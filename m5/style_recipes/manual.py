"""Manual typed authoring; all edits create new immutable revisions."""
from copy import deepcopy
from .canonical import ref, require
from .schema import validate, FORMATS
from .store import common


def finding(actor,now,prop,value,evidence=(),prior=None,reason=None):
    p=common('finding',actor,now)
    p.update(finding_id=prior['finding_id'] if prior else p['record_id'],
             supersedes=ref(prior) if prior else None,property=prop,value=deepcopy(value),
             origin='user-entered',confidence='not-assessed',explanation='Manually entered; not measured.',
             evidence=deepcopy(list(evidence)),source=None,method=None,region=None,interval=None,
             correction_reason=reason if prior else None)
    validate(p);return p


def recipe(actor,now,name,findings=(),dependencies=(),brand=None,prior=None,protections=()):
    p=common('recipe',actor,now)
    p.update(schema_version=1,recipe_id=prior['recipe_id'] if prior else p['record_id'],
             revision_id=p['record_id'],parent=ref(prior) if prior else None,name=name,
             dependencies=sorted([ref(d) for d in dependencies],key=lambda r:next(d['dependency_id'] for d in dependencies if d['record_id']==r['record_id'])),
             brand=ref(brand) if brand else None,
             findings=[ref(f) for f in sorted(findings,key=lambda f:f['finding_id'])],
             protections=deepcopy(list(protections)),
             properties=sorted([dict(property=f['property'],value=deepcopy(f['value']),finding=ref(f)) for f in findings],key=lambda v:v['property']),
             outputs=['poster'],required_capabilities=[])
    validate(p);return p


def edited(snapshot,old,actor,now,name=None,prop=None,value=None,reason=None):
    require(old['format']==FORMATS['recipe'],'schema','$','recipe required')
    p=deepcopy(old)
    p.update(common('recipe',actor,now))
    p.update(revision_id=p['record_id'],parent=ref(old))
    if name is not None:
        p['name']=name
    fs=[snapshot.get(r,'finding') for r in old['findings']]
    additions=[]
    if prop is not None:
        selected=next((v for v in old['properties'] if v['property']==prop),None)
        prior=snapshot.get(selected['finding'],'finding') if selected else next((f for f in fs if f['property']==prop),None)
        require(reason is not None,'schema','$','explicit edit reason required')
        f=finding(actor,now,prop,value,evidence=prior['evidence'] if prior else (),prior=prior,reason=reason)
        fs=[q for q in fs if prior is None or ref(q)!=ref(prior)]+[f]
        p['findings']=[ref(q) for q in sorted(fs,key=lambda q:q['finding_id'])]
        p['properties']=sorted([v for v in p['properties'] if v['property']!=prop]+
                               [dict(property=prop,value=deepcopy(value),finding=ref(f))],key=lambda v:v['property'])
        additions.append(f)
    validate(p)
    additions.append(p)
    return additions,p


def review(snapshot,subject,actor,now,decision,authority,reason):
    from .state import kind
    p=snapshot.get(subject);k=kind(p)
    scope={'finding':'finding','recipe':'recipe-definition','rights-decision':'rights-decision'}[k]
    previous=snapshot.event(subject,scope)[1]
    deps=p['dependencies'] if k=='recipe' else sorted({r['sha256']:r for r in snapshot.dependencies(p)}.values(),key=lambda r:r['record_id']) if k=='finding' else []
    event=common('review',actor,now)
    event.update(subject=subject,scope=scope,decision=decision,previous=ref(previous) if previous else None,
                 reason=reason,authority=authority,reviewed_dependencies=deps)
    validate(event);return event


def availability(snapshot,subject,actor,now,state,reason):
    previous=snapshot.event(subject)[1]
    p=common('dependency-event',actor,now)
    p.update(subject=subject,previous=ref(previous) if previous else None,state=state,reason=reason)
    validate(p);return p


def association(snapshot,recipe_ref,actor,now,project_id,creative,prior=None,library=False):
    """Dependency intent for a synthetic project only; never applies to creative layers."""
    p=common('project-association',actor,now);q=snapshot.get(recipe_ref,'recipe')
    p.update(association_id=prior['association_id'] if prior else p['record_id'],parent=ref(prior) if prior else None,
             project_id=project_id,creative=deepcopy(creative),recipe=recipe_ref,recipe_id=q['recipe_id'],
             revision_id=q['revision_id'],dependencies=q['dependencies'],library_recipe=recipe_ref if library else None,snapshot=recipe_ref)
    validate(p);return p
