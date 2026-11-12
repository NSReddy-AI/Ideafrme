"""Bounded strict JSON and the G1 style-only canonical encoding. No creative@1 changes."""
import hashlib
import json


class StyleError(ValueError):
    def __init__(self, category, path, message):
        self.category, self.path = category, path
        super().__init__(f"{category} {path}: {message}")


def require(condition, category, path, message):
    if not condition:
        raise StyleError(category, path, message)


def bounds(value):
    members = items = 0

    def visit(x, depth):
        nonlocal members, items
        if isinstance(x, (dict, list)):
            require(depth <= 32, 'limit', '$', 'nesting exceeds 32')
        if isinstance(x, dict):
            members += len(x)
            require(members <= 500, 'limit', '$', 'too many object members')
            for k, v in x.items():
                require(type(k) is str, 'schema', '$', 'keys must be strings')
                visit(k, depth + 1)
                visit(v, depth + 1)
        elif isinstance(x, list):
            items += len(x)
            require(items <= 4096, 'limit', '$', 'too many array items')
            for v in x:
                visit(v, depth + 1)
        elif isinstance(x, str):
            require(len(x) <= 4096 and not any(0xd800 <= ord(c) <= 0xdfff for c in x),
                    'encoding', '$', 'oversized string or lone surrogate')
        elif type(x) is int:
            require(-(2**63) <= x < 2**63, 'schema', '$', 'integer outside signed64')
        else:
            require(x is None or type(x) is bool, 'schema', '$', 'unsupported JSON value')
    visit(value, 1)


def _preflight(text):
    """Bound container allocations before stdlib parsing; stdlib checks JSON grammar."""
    stack, string, escaped, members, items = [], False, False, 0, 0
    for c in text:
        if string:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == '"':
                string = False
            continue
        if c in ' \t\r\n':
            continue
        if stack and stack[-1][0] == '[' and stack[-1][1] and c != ']':
            if c != ',':
                items += 1
                stack[-1][1] = False
        if c == '"':
            string = True
        elif c in '[{':
            stack.append([c, c == '['])
            require(len(stack) <= 32, 'limit', '$', 'nesting exceeds 32')
        elif c in ']}':
            if stack:
                stack.pop()
        elif c == ':':
            members += 1
        elif c == ',' and stack and stack[-1][0] == '[':
            stack[-1][1] = True
        require(members <= 500 and items <= 4096, 'limit', '$', 'aggregate JSON bound')


def loads(raw, maximum=1048576):
    require(type(raw) is bytes and len(raw) <= maximum, 'limit', '$', 'input byte bound')
    try:
        text = raw.decode('utf-8', errors='strict')
    except UnicodeError as e:
        raise StyleError('encoding', '$', 'invalid UTF-8') from e
    require(not text.startswith('\ufeff'), 'encoding', '$', 'BOM forbidden')
    _preflight(text)

    def pairs(values):
        result = {}
        for k, v in values:
            require(k not in result, 'syntax', '$', 'duplicate decoded key')
            result[k] = v
        return result

    def integer(token):
        require(token != '-0' and len(token) <= 20, 'schema', '$', 'invalid integer')
        return int(token)

    def forbidden(token):
        raise StyleError('syntax', '$', 'non-integer numeric token forbidden')
    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_int=integer,
                           parse_float=forbidden, parse_constant=forbidden)
    except (json.JSONDecodeError, RecursionError) as e:
        raise StyleError('syntax', '$', 'invalid JSON') from e
    bounds(value)
    return value


def canonical(value):
    bounds(value)
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':'), allow_nan=False).encode('utf-8')
    require(len(encoded) <= 1048576, 'limit', '$', 'encoded byte bound')
    return encoded


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def ref(payload):
    return dict(format=payload['format'], record_id=payload['record_id'], sha256=digest(payload))


def envelope(payload):
    return canonical(dict(payload=payload, sha256=digest(payload)))
