"""Immutable graph validation and current eligibility, separate from historical identity."""
from copy import deepcopy
from decimal import Decimal
from .canonical import require, digest, ref, canonical, StyleError
from .schema import FORMATS, validate, timestamp, CATALOG


def kind(p):
    return next(k for k, f in FORMATS.items() if p['format'] == f)


def refs(value):
    if type(value) is dict:
        if set(value) == {'format','record_id','sha256'}:
            yield value
        else:
            for v in value.values():
                yield from refs(v)
    elif type(value) is list:
        for v in value:
            yield from refs(v)


class Snapshot:
    def __init__(self, records=None, head=None):
        self.records = deepcopy(records or {})
        self.head = deepcopy(head)
        self.events = []
        self.sequence = {}
        self.roots = []
        self.recovery_sequence = 0
        self.last_time = None
        self.commits = []
        if head:
            self._graph(head, set(), set(), 1)
            chain, r = [], head
            while r:
                p = self.get(r, 'commit')
                chain.append(p)
                r = p['previous']
            previous = None
            seen = {}
            for c in reversed(chain):
                require(c['previous'] == previous and c['sequence'] == len(self.commits)+1,
                        'reference','$','commit ancestry/sequence')
                additions = [self.get(r) for r in c['additions']]
                prior = SnapshotView(self, seen)
                ordered_additions = prior.check_additions(additions, c['action'])
                for p in additions:
                    if kind(p)=='review' and p['decision']=='approve':
                        check=prior.eligible(p['subject'],c['created_at'],prerequisites=True,
                                             supported=('manual-style-authoring',))
                        require(check['eligible'],'authority','$','invalid historical approval prerequisites')
                for p in ordered_additions:
                    h = digest(p)
                    require(h not in seen, 'conflict','$','addition already committed')
                    seen[h] = p
                    self.sequence[h] = c['sequence']
                    self.events.append((c['sequence'], p))
                for r in c['roots']:
                    require(r['sha256'] in seen, 'reference','$','root not committed')
                    self.get(r)
                if c['action'] == 'recover':
                    require(c['roots'] == self.roots, 'reference','$','recovery roots changed')
                    self.recovery_sequence = c['sequence']
                self.roots = c['roots']
                self.commits.append(c)
                self.last_time = max(self.last_time or c['created_at'], c['created_at'])
                previous = ref(c)
        self.visible = {h:p for h,p in self.records.items() if h in self.sequence}

    def _graph(self, r, active, done, depth):
        require(depth <= 64, 'limit','$','reference depth exceeds 64')
        h = r['sha256']
        require(h not in active, 'reference','$','cycle')
        if h in done:
            self.get(r)
            return
        require(len(done)+len(active) < 4096, 'limit','$','graph record bound')
        p = self.get(r)
        active.add(h)
        for child in refs(p):
            self._graph(child, active, done, depth+1)
        active.remove(h); done.add(h)

    def get(self, r, expected=None):
        p = self.records.get(r['sha256'])
        require(p is not None and ref(p)==r, 'reference','$','missing or mismatched reference')
        validate(p)
        require(expected is None or kind(p)==expected, 'reference','$','wrong reference type')
        return p

    def latest(self, logical_field, ident):
        return next((p for _,p in reversed(self.events) if p.get(logical_field)==ident), None)

    def event(self, subject, scope=None):
        typ = 'review' if scope else 'dependency-event'
        return next(((seq,p) for seq,p in reversed(self.events) if kind(p)==typ and
                     p['subject']==subject and (not scope or p['scope']==scope)), (0,None))

    def dependencies(self, p):
        k = kind(p)
        if k=='recipe':
            used = list(p['dependencies']) + list(p['findings'])
            if p['brand']:
                used.append(p['brand'])
            return used
        if k=='finding':
            return p['evidence'] + [p[x] for x in ('source','method') if p[x]]
        if k=='dependency':
            return [p['rights_record']] if p['rights_record'] else []
        return []

    def adverse(self, p):
        subjects = {}
        def visit(p):
            h=digest(p)
            if h in subjects:
                return
            subjects[h]=p
            for r in self.dependencies(p):
                visit(self.get(r))
        visit(p)
        watermark = self.recovery_sequence
        for seq,event in self.events:
            k=kind(event)
            if k=='dependency-event' and event['subject']['sha256'] in subjects and event['state']!='available':
                watermark=max(watermark,seq)
            elif k=='review' and event['subject']['sha256'] in subjects and event['decision']!='approve':
                watermark=max(watermark,seq)
            elif k=='finding' and event['supersedes'] and event['supersedes']['sha256'] in subjects:
                watermark=max(watermark,seq)
            elif k=='rights-decision' and any(kind(s)=='rights-decision' and s['rights_id']==event['rights_id']
                    and digest(s)!=digest(event) for s in subjects.values()):
                watermark=max(watermark,seq)
        return watermark

    def eligible(self, r, now, project_id=None, prerequisites=False, supported=()):
        """Returns safe structured reasons. Only manual-style-authoring/poster is implemented."""
        try:
            timestamp(now)
            require(self.last_time is None or now >= self.last_time, 'dependency','$','clock moved backwards')
            self._eligible(self.get(r), now, project_id, prerequisites, set(supported), set())
            return {'eligible':True, 'reasons':[], 'head':self.head, 'evaluated_at':now}
        except StyleError as e:
            return {'eligible':False, 'reasons':[str(e)], 'head':self.head, 'evaluated_at':now}

    def _eligible(self,p,now,project,prereq,supported,active):
        h=digest(p); k=kind(p); r=ref(p)
        require(h not in active,'reference','$','eligibility cycle')
        active=active|{h}
        if k=='rights-decision':
            require(p['decision']=='grant' and self.latest('rights_id',p['rights_id'])==p,
                    'dependency','$','rights denied/revoked/superseded')
            require(p['valid_from']<=now and (p['expires_at'] is None or now<p['expires_at']),
                    'dependency','$','rights not current')
            require('manual-style-authoring' in p['permitted_uses'] and 'poster' in p['outputs'] and
                    (prereq or p['project_ids'] is None or project in p['project_ids']), 'dependency','$','rights scope')
            # R1 has no publishing/bundling: unknown obligation satisfaction cannot authorize use.
            require(not p['obligations'], 'dependency','$','obligation fulfillment not implemented in R1')
        elif k in ('dependency','finding'):
            _, availability=self.event(r)
            require(availability is not None and availability['state']=='available', 'dependency','$','resource/finding unavailable')
            if k=='dependency':
                require(p['rights_record'] is not None, 'dependency','$','rights unknown')
                self._eligible(self.get(p['rights_record'],'rights-decision'),now,project,False,supported,active)
                if p['kind']=='capability':
                    require(p['name'] in supported, 'dependency','$','unsupported capability')
                return
            require(self.latest('finding_id',p['finding_id'])==p, 'dependency','$','superseded finding')
            for d in self.dependencies(p):
                self._eligible(self.get(d,'dependency'),now,project,False,supported,active)
        elif k=='recipe':
            active_refs={v['finding']['sha256'] for v in p['properties']}
            evidence=set()
            for f in p['findings']:
                if f['sha256'] in active_refs:
                    fp=self.get(f,'finding')
                    self._eligible(fp,now,project,False,supported,active)
                    evidence.update(d['sha256'] for d in self.dependencies(fp))
            for d in p['dependencies']:
                dp=self.get(d,'dependency')
                if dp['required'] or d['sha256'] in evidence or dp['kind']=='brand' or (
                        dp['kind']=='font' and any(v['value'].get('value')==dp['dependency_id'] for v in p['properties'])):
                    self._eligible(dp,now,project,False,supported,active)
            require(set(p['required_capabilities'])<=supported,'dependency','$','unsupported capability')
            self.check_rules(p)
        elif k=='project-association':
            self._eligible(self.get(p['recipe'],'recipe'),now,p['project_id'],False,supported,active)
            return
        else:
            require(False,'schema','$','not an approvable subject')
        if not prereq:
            scope={'finding':'finding','recipe':'recipe-definition','rights-decision':'rights-decision'}[k]
            seq,review=self.event(r,scope)
            require(review is not None and review['decision']=='approve' and seq>self.adverse(p),
                    'authority','$','fresh subject approval required')
            if k=='recipe':
                for f in p['findings']:
                    if f['sha256'] in {v['finding']['sha256'] for v in p['properties']}:
                        require(seq>self.event(f,'finding')[0], 'authority','$','recipe approval predates finding review')
                for d in p['dependencies']:
                    right=self.get(d)['rights_record']
                    if right:
                        require(seq>self.event(right,'rights-decision')[0], 'authority','$','recipe approval predates rights review')

    def check_rules(self,p):
        brand=self.get(p['brand'],'brand') if p['brand'] else None
        protections=p['protections']+(brand['protections'] if brand else [])
        require(not(p['properties'] and any(t['target'] is None and t['mode']=='locked' for t in protections)),
                'protection','$','global locked scope conflicts with style changes')
        if not brand:
            return
        # Conservative manual intent: all declared hard/guided constraints must hold.
        for group in ('hard_rules','guided_rules'):
            for rule in brand[group]:
                for v in p['properties']:
                    if v['property']==rule['property']:
                        require(allows(rule,v['value']), 'protection','$','brand rule conflict')


def allows(rule,v):
    if rule['allowed'] and v not in rule['allowed']:
        return False
    if v['kind']=='decimal':
        d=Decimal(v['value'])
        return (rule['minimum'] is None or d>=Decimal(rule['minimum'])) and (rule['maximum'] is None or d<=Decimal(rule['maximum']))
    return True


class SnapshotView(Snapshot):
    """Earlier committed state during deterministic history validation."""
    def __init__(self, base, visible):
        self.__dict__=base.__dict__.copy()
        self.visible=visible.copy()

    def check_additions(self, additions, action):
        for p in additions:
            validate(p)
        require(len({p['record_id'] for p in additions})==len(additions), 'conflict','$','duplicate addition identity')
        all_records={**self.visible}
        finding_heads={}
        for _,p in self.events:
            if kind(p)=='finding':
                finding_heads[p['finding_id']]=p
        special={'review':'review','project-association':'associate','dependency-event':'dependency-event','rights-decision':'rights-decision'}
        counted=[]
        pending=list(additions)
        ordered_additions=[]
        available=set(all_records)
        while pending:
            ready=[p for p in pending if all(r['sha256'] in available for r in refs(p))]
            require(bool(ready),'reference','$','cycle or absent addition reference')
            for p in ready:
                pending.remove(p); ordered_additions.append(p); available.add(digest(p))
        for p in ordered_additions:
            k=validate(p)
            require(not any(q['record_id']==p['record_id'] for q in all_records.values()), 'conflict','$','immutable identity reused')
            for r in refs(p):
                require(r['sha256'] in all_records and ref(all_records[r['sha256']])==r, 'reference','$','reference not earlier/committed')
            # Arrays are sorted in commit, so dependency order is handled below, not input order.
            all_records[digest(p)]=p
            if k in special:
                counted.append(special[k])
            require(k!='commit','schema','$','cannot import a commit as an addition')
            self._relationships(p,all_records,finding_heads)
            if k=='finding':
                finding_heads[p['finding_id']]=p
        require((not counted and action in ('save','recover')) or counted==[action], 'schema','$','action/event mismatch')
        if action=='recover':
            require(not additions,'schema','$','recovery additions forbidden')
        return ordered_additions

    def _relationships(self,p,records,finding_heads):
        k=kind(p)
        def get(r,typ):
            q=records[r['sha256']]
            require(kind(q)==typ,'reference','$','wrong target type')
            return q
        for f, logical, typ in [('parent','recipe_id','recipe'),('parent','brand_id','brand'),
                                ('parent','association_id','project-association'),('supersedes','finding_id','finding'),
                                ('supersedes','rights_id','rights-decision')]:
            if k!=typ:
                continue
            prior=finding_heads.get(p[logical]) if k=='finding' else self.latest(logical,p[logical])
            # Recipes can explicitly fork a retained parent; findings/rights cannot branch.
            if p[f]:
                q=get(p[f],typ)
                require(q[logical]==p[logical], 'reference','$','parent logical identity')
                if k in ('finding','rights-decision'):
                    require(prior is not None and ref(prior)==p[f], 'conflict','$','stale logical revision')
            else:
                require(prior is None,'conflict','$','logical identity already exists')
        if k=='dependency' and p['rights_record']:
            q=get(p['rights_record'],'rights-decision')
            require(q['resource_sha256']==p['content_sha256'], 'reference','$','rights resource mismatch')
        elif k=='finding':
            for r in p['evidence']:
                get(r,'dependency')
            if p['supersedes']:
                q=get(p['supersedes'],'finding')
                require(all(p[f]==q[f] for f in ('finding_id','property','origin','evidence','source','method')),
                        'reference','$','correction changed provenance')
        elif k=='rights-decision':
            peers=[q for q in records.values() if kind(q)=='rights-decision' and q['resource_sha256']==p['resource_sha256']]
            require(all(q['rights_id']==p['rights_id'] for q in peers), 'conflict','$','competing resource rights chains')
            if p['supersedes']:
                require(get(p['supersedes'],'rights-decision')['resource_sha256']==p['resource_sha256'], 'reference','$','rights changed resource')
        elif k=='brand':
            for a in p['hard_rules']:
                for b in p['guided_rules']:
                    if a['property']==b['property']:
                        vals=a['allowed'] or b['allowed']
                        if vals:
                            require(any(allows(a,v) and allows(b,v) for v in vals),'protection','$','empty hard/guided intersection')
                        else:
                            low=max(Decimal(x['minimum'] or CATALOG[a['property']][2]) for x in (a,b))
                            high=min(Decimal(x['maximum'] or CATALOG[a['property']][3]) for x in (a,b))
                            require(low<=high,'protection','$','empty rule ranges')
        elif k=='recipe':
            deps=[get(r,'dependency') for r in p['dependencies']]
            fs=[get(r,'finding') for r in p['findings']]
            require([q['dependency_id'] for q in deps]==sorted({q['dependency_id'] for q in deps}), 'schema','$','dependency order/identity')
            require([q['finding_id'] for q in fs]==sorted({q['finding_id'] for q in fs}), 'schema','$','finding order/identity')
            for v in p['properties']:
                f=get(v['finding'],'finding')
                require(v['finding'] in p['findings'] and v['property']==f['property'] and v['value']==f['value'], 'reference','$','property/finding mismatch')
                if v['property'].endswith('.font'):
                    require(any(d['kind']=='font' and d['dependency_id']==v['value']['value'] for d in deps),'reference','$','font not pinned')
            for f in fs:
                require(all(r in p['dependencies'] for r in self.dependencies(f)), 'reference','$','finding dependency not pinned')
            if p['brand']:
                b=get(p['brand'],'brand')
                require(any(d['kind']=='brand' and d['content_sha256']==digest(b) for d in deps), 'reference','$','brand dependency not pinned')
            for cap in p['required_capabilities']:
                require(any(d['kind']=='capability' and d['name']==cap for d in deps), 'reference','$','capability not pinned')
        elif k in ('review','dependency-event'):
            subject=get(p['subject'], {'finding':'finding','recipe-definition':'recipe','rights-decision':'rights-decision'}[p['scope']]) if k=='review' else records[p['subject']['sha256']]
            require(p['subject']['sha256'] in self.visible,'reference','$','events require previously committed subject')
            if k=='dependency-event':
                require(kind(subject) in ('dependency','finding'), 'reference','$','availability target')
            prior=self.event(p['subject'],p['scope'] if k=='review' else None)[1]
            require(p['previous']==(ref(prior) if prior else None), 'conflict','$','stale event predecessor')
            if k=='review':
                expected=subject['dependencies'] if kind(subject)=='recipe' else sorted({r['sha256']:r for r in self.dependencies(subject)}.values(), key=lambda r:r['record_id']) if kind(subject)=='finding' else []
                require(p['reviewed_dependencies']==expected,'reference','$','reviewed dependencies mismatch')
        elif k=='project-association':
            q=get(p['recipe'],'recipe')
            require(p['creative']['id'].startswith('synthetic-'),'schema','$','R1 associations are synthetic-only')
            require(p['recipe_id']==q['recipe_id'] and p['revision_id']==q['revision_id'] and p['dependencies']==q['dependencies'], 'reference','$','association pin mismatch')
            require(p['library_recipe'] is None or p['library_recipe']==p['recipe'], 'reference','$','library snapshot mismatch')
            if p['parent']:
                require(get(p['parent'],'project-association')['project_id']==p['project_id'],'reference','$','association project changed')
