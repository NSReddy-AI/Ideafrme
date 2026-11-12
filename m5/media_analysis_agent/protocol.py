"""Small closed control protocol, NOT a persisted R2 format or media report."""
import json
import uuid

from .policy import AgentError, FRAME_BYTES, VALUE_BYTES


def identifier(value):
    try:
        return type(value) is str and str(uuid.UUID(value)) == value and uuid.UUID(value).int != 0
    except (ValueError, AttributeError):
        return False


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AgentError("protocol", "duplicate key")
        result[key] = value
    return result


def decode(raw):
    if type(raw) is not bytes or not raw.endswith(b"\n") or len(raw) > FRAME_BYTES:
        raise AgentError("protocol", "invalid frame size or delimiter")
    # Refuse nested containers BEFORE json parsing: this protocol is flat.
    text = raw.decode("utf-8", errors="strict")
    quoted = escaped = False
    depth = 0
    for c in text:
        if quoted:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                quoted = False
        elif c == '"':
            quoted = True
        elif c in "{[":
            depth += 1
            if c == "[" or depth > 1:
                raise AgentError("protocol", "nested data forbidden")
        elif c in "}]":
            depth -= 1
    def forbidden(_):
        raise AgentError("protocol", "noninteger token")
    try:
        value = json.loads(text, object_pairs_hook=_pairs, parse_float=forbidden,
                           parse_constant=forbidden)
    except (ValueError, RecursionError) as exc:
        raise AgentError("protocol", "invalid JSON") from exc
    if type(value) is not dict or len(value) > 8:
        raise AgentError("protocol", "expected bounded object")
    for item in value.values():
        if type(item) not in (str, int, bool, type(None)):
            raise AgentError("protocol", "invalid field type")
        if type(item) is int and not -(2**63) <= item < 2**63:
            raise AgentError("protocol", "integer range")
        if type(item) is str:
            try:
                encoded = item.encode("utf-8")
            except UnicodeError as exc:
                raise AgentError("protocol", "invalid Unicode") from exc
            if len(encoded) > VALUE_BYTES:
                raise AgentError("protocol", "string size")
    return value


def encode(value):
    try:
        raw = json.dumps(value, ensure_ascii=False, allow_nan=False,
                         separators=(",", ":")).encode("utf-8") + b"\n"
    except (ValueError, UnicodeError, TypeError) as exc:
        raise AgentError("protocol", "unencodable message") from exc
    decode(raw)
    return raw


def ready(value, session):
    if (set(value) != {"v", "type", "session", "backend"}
            or type(value["v"]) is not int or value["v"] != 1
            or value["type"] != "ready" or value["session"] != session
            or value["backend"] != "synthetic"):
        raise AgentError("protocol", "invalid capability handshake")


def result(value, session, job_id):
    if (set(value) != {"v", "type", "session", "job_id", "value"}
            or type(value["v"]) is not int or value["v"] != 1
            or value["type"] != "result" or value["session"] != session
            or value["job_id"] != job_id or type(value["value"]) is not str):
        raise AgentError("protocol", "invalid result binding or fields")


def request(value, session, scenarios):
    if (set(value) != {"v", "type", "session", "job_id", "value", "scenario"}
            or type(value["v"]) is not int or value["v"] != 1
            or value["type"] != "job" or value["session"] != session
            or not identifier(value["job_id"]) or type(value["value"]) is not str
            or value["scenario"] not in scenarios):
        raise AgentError("protocol", "invalid request")
