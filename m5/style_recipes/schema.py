"""Closed manual-R1 record grammar. All semantic relationships checked by state.py."""
from datetime import datetime
from decimal import Decimal
import re
from .canonical import canonical, require, StyleError

PREFIX = 'ai-reel-studio/style-'
KINDS = ('dependency', 'brand', 'rights-decision', 'finding', 'recipe', 'review',
         'dependency-event', 'project-association', 'commit')
FORMATS = {k: PREFIX + k + '@1' for k in KINDS}
ID = r'(?!00000000-0000-0000-0000-000000000000$)[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}'
HASH = r'[0-9a-f]{64}'
DECIMAL = r'(?:0|-?[1-9][0-9]*|-?(?:0|[1-9][0-9]*)\.[0-9]*[1-9])'
KEY = r'[a-z][a-z0-9_.-]{0,63}'
STATES = ('available', 'missing', 'stale', 'unsupported', 'failed', 'revoked', 'expired')
COMMON = 'format record_id created_at created_by'
FIELDS = {
 'dependency': 'dependency_id kind name version content_sha256 license_expression notice_sha256 rights_record parameters required',
 'brand': 'brand_id parent name hard_rules guided_rules protections',
 'rights-decision': 'rights_id supersedes resource_sha256 decision grantor basis evidence_sha256 permitted_uses project_ids outputs valid_from expires_at obligations',
 'finding': 'finding_id supersedes property value origin confidence explanation evidence source method region interval correction_reason',
 'recipe': 'schema_version recipe_id revision_id parent name dependencies brand findings protections properties outputs required_capabilities',
 'review': 'subject scope decision previous reason authority reviewed_dependencies',
 'dependency-event': 'subject previous state reason',
 'project-association': 'association_id parent project_id creative recipe recipe_id revision_id dependencies library_recipe snapshot',
 'commit': 'previous sequence action additions roots recovery_from',
}


def shape(x, fields, path='$'):
    require(type(x) is dict and set(x) == set(fields.split()), 'schema', path, 'exact fields required')


def match(x, pattern, path='$'):
    require(type(x) is str and re.fullmatch(pattern, x) is not None, 'schema', path, 'invalid scalar')


def text(x, path='$', minimum=0, maximum=4096):
    require(type(x) is str and minimum <= len(x) <= maximum, 'schema', path, 'invalid text length')


def enum(x, choices, path='$'):
    require(type(x) is str and x in choices, 'schema', path, 'unsupported choice')


def array(x, path='$', maximum=4096):
    require(type(x) is list and len(x) <= maximum, 'schema', path, 'array bound')


def ordered(x, key=lambda x: x, path='$'):
    values = [key(v) for v in x]
    require(values == sorted(values) and len(set(values)) == len(values),
            'schema', path, 'unique sorted values required')


def timestamp(x, path='$'):
    match(x, r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z', path)
    try:
        datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        require(False, 'schema', path, 'invalid UTC time')


def reference(x, path='$', nullable=False):
    if x is None and nullable:
        return
    shape(x, 'format record_id sha256', path)
    enum(x['format'], FORMATS.values(), path)
    match(x['record_id'], ID, path)
    match(x['sha256'], HASH, path)


def references(xs, path='$', maximum=32):
    array(xs, path, maximum)
    for x in xs:
        reference(x, path)


def decimal(x, path='$'):
    match(x, DECIMAL, path)
    require(len(x) <= 32, 'schema', path, 'decimal too long')
    return Decimal(x)


def value(x, path='$'):
    require(type(x) is dict and 'kind' in x, 'schema', path, 'typed value required')
    kind = x['kind']
    enum(kind, ('color', 'decimal', 'text', 'choice'), path)
    shape(x, 'kind rgba' if kind == 'color' else 'kind value unit' if kind == 'decimal' else 'kind value', path)
    if kind == 'color':
        match(x['rgba'], r'#[0-9a-f]{8}', path)
    elif kind == 'decimal':
        decimal(x['value'], path)
        enum(x['unit'], ('px', 'ratio', 'em'), path)
    else:
        text(x['value'], path)


CATALOG = {f'palette.{p}': ('color', None, None, None) for p in ('primary', 'secondary', 'accent', 'background')}
for role in ('heading', 'body'):
    for field, kind, unit, low, high in [('font','choice',None,None,None), ('size','decimal','px','1','512'),
             ('line_height','decimal','ratio','0.5','3'), ('tracking','decimal','em','-0.2','1')]:
        CATALOG[f'typography.{role}.{field}'] = (kind, unit, low, high)
CATALOG.update({'layout.margin': ('decimal','ratio','0','0.45'), 'layout.alignment': ('choice',None,None,None),
                'description.lighting': ('text',None,None,None), 'description.texture': ('text',None,None,None)})


def property_value(prop, val, path='$'):
    enum(prop, CATALOG, path)
    value(val, path)
    kind, unit, low, high = CATALOG[prop]
    require(val['kind'] == kind, 'schema', path, 'property type mismatch')
    if unit:
        require(val['unit'] == unit and Decimal(low) <= decimal(val['value']) <= Decimal(high),
                'schema', path, 'property unit/range')
    elif prop.endswith('.font'):
        match(val['value'], ID, path)
    elif prop == 'layout.alignment':
        enum(val['value'], ('start', 'center', 'end'), path)


def rules(xs):
    array(xs)
    seen = set()
    for r in xs:
        shape(r, 'property allowed minimum maximum unit')
        p = r['property']
        enum(p, CATALOG)
        require(p not in seen, 'schema', '$.rules', 'duplicate property')
        seen.add(p)
        array(r['allowed'])
        require(len({canonical(v) for v in r['allowed']}) == len(r['allowed']), 'schema', '$', 'duplicate rule value')
        for v in r['allowed']:
            property_value(p, v)
        _, unit, low, high = CATALOG[p]
        if unit:
            require(r['unit'] == unit, 'schema', '$', 'rule unit')
            a = decimal(r['minimum']) if r['minimum'] is not None else Decimal(low)
            b = decimal(r['maximum']) if r['maximum'] is not None else Decimal(high)
            require(Decimal(low) <= a <= b <= Decimal(high), 'schema', '$', 'empty or invalid rule range')
            require(not r['allowed'] or any(a <= Decimal(v['value']) <= b for v in r['allowed']),
                    'protection', '$', 'empty allowed intersection')
        else:
            require(r['minimum'] is r['maximum'] is r['unit'] is None and bool(r['allowed']),
                    'schema', '$', 'nondecimal rule needs allowed values only')


def protections(xs):
    array(xs, maximum=32)
    targets = set()
    for p in xs:
        shape(p, 'target mode protected_aspects')
        if p['target'] is not None:
            match(p['target'], ID)
        require(p['target'] not in targets, 'schema', '$', 'duplicate target')
        targets.add(p['target'])
        enum(p['mode'], ('locked','guided','free'))
        array(p['protected_aspects'])
        require(len(set(p['protected_aspects'])) == len(p['protected_aspects']), 'schema', '$', 'duplicate aspect')
        for a in p['protected_aspects']:
            enum(a, ('identity','content','logo','portrait','rights'))


def _validate(p):
    canonical(p)  # includes scalar/aggregate bounds; envelope overhead checked by loader/writer
    require(type(p) is dict, 'schema', '$', 'record required')
    kind = next((k for k, f in FORMATS.items() if p.get('format') == f), None)
    require(kind is not None, 'schema', '$.format', 'unsupported format/version')
    shape(p, COMMON + ' ' + FIELDS[kind])
    for key in ('record_id', 'created_by'):
        match(p[key], ID, '$.'+key)
    timestamp(p['created_at'])
    for key in ('dependency_id','brand_id','rights_id','finding_id','recipe_id','revision_id','association_id','project_id'):
        if key in p:
            match(p[key], ID, '$.'+key)
    for key in ('parent','supersedes','rights_record','brand','source','method','library_recipe','previous'):
        if key in p:
            reference(p[key], '$.'+key, True)
    for key in ('subject','recipe','snapshot'):
        if key in p:
            reference(p[key], '$.'+key)
    for key in ('dependencies','findings','evidence','reviewed_dependencies','additions','roots'):
        if key in p:
            references(p[key], '$.'+key, 4096 if key == 'additions' else 32)
    if 'name' in p:
        text(p['name'], minimum=1, maximum=256)
    if 'reason' in p:
        text(p['reason'], minimum=1)
    if kind == 'dependency':
        enum(p['kind'], ('brand','reference','font','extractor','capability','render-profile','renderer','rights'))
        for k in ('version','license_expression'):
            if p[k] is not None:
                text(p[k])
        match(p['content_sha256'], HASH)
        if p['notice_sha256'] is not None:
            match(p['notice_sha256'], HASH)
        require(type(p['required']) is bool, 'schema', '$', 'required boolean')
        array(p['parameters'])
        for v in p['parameters']:
            shape(v, 'key value'); match(v['key'], KEY); value(v['value'])
        ordered(p['parameters'], lambda v: v['key'])
    elif kind == 'brand':
        rules(p['hard_rules']); rules(p['guided_rules']); protections(p['protections'])
    elif kind == 'rights-decision':
        enum(p['decision'], ('grant','deny','revoke'))
        text(p['grantor'], minimum=1)
        enum(p['basis'], ('owned','license','permission'))
        for k in ('resource_sha256','evidence_sha256'):
            match(p[k], HASH)
        for k in ('permitted_uses','outputs'):
            array(p[k]); ordered(p[k])
        for u in p['permitted_uses']:
            enum(u, ('manual-style-authoring','reference-analysis','style-application','publication','redistribution'))
        for o in p['outputs']:
            enum(o, ('poster','reel'))
        require(bool(p['permitted_uses']) == (p['decision'] == 'grant') and bool(p['outputs']) == (p['decision'] == 'grant'),
                'schema', '$', 'grant/deny scopes')
        if p['project_ids'] is not None:
            array(p['project_ids']); ordered(p['project_ids'])
            for ident in p['project_ids']:
                match(ident, ID)
        timestamp(p['valid_from'])
        if p['expires_at'] is not None:
            timestamp(p['expires_at'])
            require(p['valid_from'] < p['expires_at'], 'schema', '$', 'expiry order')
        array(p['obligations'])
        for o in p['obligations']:
            shape(o,'kind text'); enum(o['kind'], ('notice','attribution','no-redistribution')); text(o['text'],minimum=1)
            require(not(o['kind']=='no-redistribution' and 'redistribution' in p['permitted_uses']), 'schema','$','rights conflict')
        ordered(p['obligations'], lambda o: (o['kind'],o['text']))
    elif kind == 'finding':
        property_value(p['property'],p['value'])
        require(p['origin'] == 'user-entered' and p['source'] is p['method'] is p['region'] is p['interval'] is None,
                'schema','$','R1 is manual only')
        enum(p['confidence'], ('high','medium','low','not-assessed')); text(p['explanation'])
        require((p['supersedes'] is None) == (p['correction_reason'] is None), 'schema','$','correction reason required')
        if p['correction_reason'] is not None:
            text(p['correction_reason'], minimum=1)
    elif kind == 'recipe':
        require(type(p['schema_version']) is int and p['schema_version']==1 and p['record_id']==p['revision_id'], 'schema','$','recipe version/identity')
        protections(p['protections']); array(p['properties'], maximum=32)
        for v in p['properties']:
            shape(v,'property value finding'); property_value(v['property'],v['value']); reference(v['finding'])
        ordered(p['properties'], lambda v:v['property'])
        require(p['outputs']==['poster'], 'schema','$','R1 poster only')
        array(p['required_capabilities'], maximum=32); ordered(p['required_capabilities'])
        for c in p['required_capabilities']:
            match(c,KEY)
    elif kind == 'review':
        enum(p['scope'], ('finding','recipe-definition','rights-decision'))
        enum(p['decision'], ('approve','exclude','reject','revoke'))
        enum(p['authority'], ('A','B','C'))
        require(p['scope']=='finding' or p['decision']!='exclude', 'schema','$','exclude finding only')
        require(p['scope']!='rights-decision' or p['authority']=='B', 'authority','$','rights need B')
    elif kind == 'dependency-event':
        enum(p['state'], STATES)
    elif kind == 'project-association':
        shape(p['creative'],'format id fingerprint')
        require(p['creative']['format']=='ai-reel-studio/creative@1','schema','$','creative format')
        text(p['creative']['id'], minimum=1); match(p['creative']['fingerprint'],r'sha256:'+HASH)
        require(p['snapshot']==p['recipe'], 'reference','$','snapshot must equal recipe')
    elif kind == 'commit':
        require(type(p['sequence']) is int and p['sequence']>0, 'schema','$','positive sequence')
        enum(p['action'], ('save','review','associate','dependency-event','rights-decision','recover'))
        ordered(p['additions'],lambda r:r['record_id']); ordered(p['roots'],lambda r:r['record_id'])
        r=p['recovery_from']
        require((r is not None)==(p['action']=='recover'), 'schema','$','recovery evidence required')
        if r is not None:
            shape(r,'head_present head_bytes_sha256 previous')
            require(type(r['head_present']) is bool,'schema','$','presence boolean')
            match(r['head_bytes_sha256'],HASH); reference(r['previous'])
            require(r['previous']==p['previous'] and p['additions']==[], 'schema','$','recovery base/additions')
    return kind


def validate(p):
    try:
        return _validate(p)
    except StyleError:
        raise
    except (TypeError,ValueError,KeyError,AttributeError) as e:
        raise StyleError('schema','$','invalid field type or value') from e
