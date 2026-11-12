from pathlib import Path
from uuid import uuid4
from style_recipes.store import Store,common,WORKSPACE
from style_recipes.canonical import ref,digest
from style_recipes.manual import finding,recipe,review,availability

ACTOR='00000000-0000-4000-8000-000000000002'
NOW='2026-11-10T23:00:00Z'
PROJECT='00000000-0000-4000-8000-000000000003'


def new_store():
    root=WORKSPACE/'.runtime/r1/tests'
    root.mkdir(exist_ok=True)
    return Store.create(root/str(uuid4()))


def save(s,records,action='save',**kwargs):
    return s.commit(records,s.read().head,ACTOR,NOW,action=action,**kwargs)


def manual(s):
    f=finding(ACTOR,NOW,'palette.primary',dict(kind='color',rgba='#3366ffff'))
    r=recipe(ACTOR,NOW,'తెలుగు / English manual recipe',[f])
    save(s,[f,r]);return f,r


def available(s,p,state='available'):
    e=availability(s.read(),ref(p),ACTOR,NOW,state,'Explicit synthetic fixture availability.')
    save(s,[e],'dependency-event',confirmed=True);return e


def approve(s,p,decision='approve',authority='A',**kwargs):
    e=review(s.read(),ref(p),ACTOR,NOW,decision,authority,'Synthetic fixture human-role confirmation.')
    save(s,[e],'review',confirmed=True,**kwargs);return e


def approved(s):
    f,r=manual(s);available(s,f);approve(s,f);approve(s,r);return f,r


def rights(resource='a'*64,**changes):
    p=common('rights-decision',ACTOR,NOW)
    p.update(rights_id=p['record_id'],supersedes=None,resource_sha256=resource,decision='grant',
             grantor='Synthetic fixture owner',basis='owned',evidence_sha256='b'*64,
             permitted_uses=['manual-style-authoring'],project_ids=None,outputs=['poster'],
             valid_from='2026-01-01T00:00:00Z',expires_at=None,obligations=[])
    p.update(changes);return p


def dependency(rd=None,**changes):
    p=common('dependency',ACTOR,NOW)
    p.update(dependency_id=p['record_id'],kind='font',name='Synthetic pinned font',version='1',
             content_sha256=rd['resource_sha256'] if rd else 'a'*64,license_expression=None,
             notice_sha256=None,rights_record=ref(rd) if rd else None,parameters=[],required=True)
    p.update(changes);return p
