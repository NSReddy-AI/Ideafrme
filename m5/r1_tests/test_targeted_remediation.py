"""Only the two acceptance-audit regressions. Never writes prior R1 evidence."""
from copy import deepcopy
import os
from pathlib import Path
import unittest
from uuid import uuid4
from style_recipes.canonical import StyleError, digest, envelope, ref
from style_recipes.manual import edited, finding, recipe, review
from style_recipes.state import Snapshot, SnapshotView
from style_recipes.store import Store, WORKSPACE, common
from .helpers import ACTOR, NOW


def initial(number=100):
    p=finding(ACTOR,NOW,'palette.primary',dict(kind='color',rgba='#112233ff'))
    p['record_id']=p['finding_id']=f'00000000-0000-4000-8000-{number:012d}'
    return p


def correction(parent,number,color='#224466ff'):
    p=finding(ACTOR,NOW,parent['property'],dict(kind='color',rgba=color),prior=parent,reason='Explicit correction')
    p['record_id']=f'00000000-0000-4000-8000-{number:012d}'
    return p


def proposed(snapshot,additions,action='save'):
    c=common('commit',ACTOR,NOW)
    c.update(previous=snapshot.head,sequence=len(snapshot.commits)+1,action=action,
             additions=sorted([ref(p) for p in additions],key=lambda r:r['record_id']),
             roots=sorted([ref(p) for p in additions],key=lambda r:r['record_id']),recovery_from=None)
    return {**snapshot.records,**{digest(p):deepcopy(p) for p in additions},digest(c):c},ref(c)


def append(snapshot,additions,action='save'):
    return Snapshot(*proposed(snapshot,additions,action))


class FindingIntegrityTests(unittest.TestCase):
    def reject_at_validation_and_reopen(self,snapshot,additions):
        for records in (additions,list(reversed(additions))):
            with self.subTest(order=[p['record_id'] for p in records]):
                with self.assertRaises(StyleError):
                    SnapshotView(snapshot,snapshot.visible).check_additions(records,'save')
                with self.assertRaises(StyleError):
                    Snapshot(*proposed(snapshot,records))

    def test_duplicate_initial_finding_id_rejected(self):
        a=initial();b=initial(101);b['finding_id']=a['finding_id']
        self.reject_at_validation_and_reopen(Snapshot(),[a,b])

    def test_two_corrections_of_one_parent_rejected(self):
        f=initial();s=append(Snapshot(),[f])
        self.reject_at_validation_and_reopen(s,[correction(f,90),correction(f,110,'#446688ff')])

    def test_duplicate_initial_after_committed_initial_rejected(self):
        f=initial();s=append(Snapshot(),[f]);other=initial(101);other['finding_id']=f['finding_id']
        self.reject_at_validation_and_reopen(s,[other])

    def test_valid_linear_chain_is_ancestry_ordered_not_uuid_ordered(self):
        f=initial();s=append(Snapshot(),[f]);a=correction(f,90);b=correction(a,80,'#446688ff')
        for records in ([a,b],[b,a]):
            with self.subTest(order=[p['record_id'] for p in records]):
                result=append(s,records)
                self.assertEqual(result.latest('finding_id',f['finding_id']),b)
                self.assertEqual(Snapshot(result.records,result.head).latest('finding_id',f['finding_id']),b)
                self.assertEqual(result.get(ref(f)),f)

    def test_initial_and_linear_corrections_in_same_transaction(self):
        f=initial();a=correction(f,90);b=correction(a,80)
        s=append(Snapshot(),[b,a,f])
        self.assertEqual(s.latest('finding_id',f['finding_id']),b)

    def test_branch_after_in_transaction_correction_rejected(self):
        f=initial();s=append(Snapshot(),[f]);a=correction(f,90)
        self.reject_at_validation_and_reopen(s,[a,correction(a,80),correction(a,110,'#446688ff')])

    def test_stale_parent_after_later_transaction_rejected(self):
        f=initial();s=append(Snapshot(),[f]);a=correction(f,90);s=append(s,[a])
        self.reject_at_validation_and_reopen(s,[correction(f,80)])

    def test_independent_finding_chains_can_share_transaction(self):
        f=initial();g=initial(200);s=append(Snapshot(),[g,f]);a=correction(f,90);b=correction(g,190)
        result=append(s,[b,a])
        self.assertEqual(result.latest('finding_id',f['finding_id']),a)
        self.assertEqual(result.latest('finding_id',g['finding_id']),b)


class SelectionPreservationTests(unittest.TestCase):
    def fixture(self):
        inactive=initial(100);active=initial(200)
        s=append(Snapshot(),[inactive,active])
        exclude=review(s,ref(inactive),ACTOR,NOW,'exclude','A','Retained but intentionally inactive')
        s=append(s,[exclude],'review')
        r=recipe(ACTOR,NOW,'Original',[active])
        r['findings']=sorted([ref(inactive),ref(active)],key=lambda r:r['record_id'])
        return append(s,[r]),r,inactive,active

    def test_rename_preserves_empty_selection(self):
        f=initial();s=append(Snapshot(),[f]);r=recipe(ACTOR,NOW,'Original',[f]);r['properties']=[]
        s=append(s,[r]);adds,new=edited(s,r,ACTOR,NOW,name='Rename only')
        self.assertEqual(new['properties'],[]);self.assertEqual(new['findings'],r['findings'])
        self.assertEqual(len(adds),1);append(s,adds)

    def test_rename_preserves_inactive_excluded_findings_and_all_other_fields(self):
        s,r,inactive,active=self.fixture();before=envelope(r)
        adds,new=edited(s,r,ACTOR,NOW,name='Rename only')
        allowed={'record_id','revision_id','parent','created_at','created_by','name'}
        for key in r:
            if key not in allowed:self.assertEqual(new[key],r[key],key)
        reopened=append(s,adds)
        self.assertEqual(reopened.event(ref(inactive),'finding')[1]['decision'],'exclude')
        self.assertEqual(envelope(reopened.get(ref(r))),before)
        self.assertEqual(reopened.get(ref(new))['properties'],r['properties'])
        self.assertFalse(reopened.eligible(ref(new),NOW)['eligible'])

    def test_targeted_edit_preserves_inactive_same_property_observation(self):
        s,r,inactive,active=self.fixture()
        adds,new=edited(s,r,ACTOR,NOW,prop='palette.primary',value=dict(kind='color',rgba='#abcdefFF'.lower()),reason='Chosen active value only')
        self.assertEqual(adds[0]['supersedes'],ref(active))
        self.assertIn(ref(inactive),new['findings'])
        self.assertEqual(len(new['properties']),1)
        self.assertEqual(new['properties'][0]['finding'],ref(adds[0]))
        append(s,adds)

    def test_targeted_edit_preserves_other_active_and_inactive_properties(self):
        a=initial(100);b=finding(ACTOR,NOW,'layout.alignment',dict(kind='choice',value='center'))
        c=finding(ACTOR,NOW,'description.texture',dict(kind='text',value='Inactive note'))
        s=append(Snapshot(),[a,b,c]);r=recipe(ACTOR,NOW,'Original',[a,b]);r['findings']=sorted([ref(a),ref(b),ref(c)],key=lambda r:next(p['finding_id'] for p in (a,b,c) if ref(p)==r))
        s=append(s,[r]);adds,new=edited(s,r,ACTOR,NOW,prop='palette.primary',value=dict(kind='color',rgba='#abcdefFF'.lower()),reason='One property')
        self.assertEqual(next(v for v in new['properties'] if v['property']==b['property']),next(v for v in r['properties'] if v['property']==b['property']))
        self.assertNotIn(c['property'],[v['property'] for v in new['properties']])
        self.assertIn(ref(c),new['findings']);append(s,adds)

    def test_edited_record_is_a_deep_copy(self):
        s,r,_,_=self.fixture();before=envelope(r)
        _,new=edited(s,r,ACTOR,NOW,name='Copy')
        new['properties'][0]['value']['rgba']='#000000ff'
        self.assertEqual(envelope(r),before)


class IsolatedStoreTests(unittest.TestCase):
    def setUp(self):
        evidence=Path(os.environ['R1_REMEDIATION_EVIDENCE']).absolute()
        self.assertTrue(evidence.is_relative_to(WORKSPACE/'.runtime/r1'))
        self.assertTrue(evidence.name.startswith('remediation-'))
        self.store=Store.create(evidence/'stores'/str(uuid4()))

    def test_rejected_fork_does_not_publish_or_change_originals(self):
        f=initial();self.store.commit([f],None,ACTOR,NOW)
        head=(self.store.path/'HEAD').read_bytes();before={p.name:p.read_bytes() for p in (self.store.path/'records').iterdir()}
        with self.assertRaises(StyleError):
            self.store.commit([correction(f,90),correction(f,110)],self.store.read().head,ACTOR,NOW)
        self.assertEqual((self.store.path/'HEAD').read_bytes(),head)
        self.assertEqual({p.name:p.read_bytes() for p in (self.store.path/'records').iterdir()},before)

    def test_store_reopen_uses_linear_ancestry(self):
        f=initial();self.store.commit([f],None,ACTOR,NOW);a=correction(f,90);b=correction(a,80)
        self.store.commit([b,a],self.store.read().head,ACTOR,NOW)
        reopened=Store(self.store.path).read()
        self.assertEqual(reopened.latest('finding_id',f['finding_id']),b)

    def test_store_reopen_rejects_legacy_fork(self):
        f=initial();self.store.commit([f],None,ACTOR,NOW)
        records,head=proposed(self.store.read(),[correction(f,90),correction(f,110)])
        # Deliberately malformed synthetic store confined to this fresh evidence run.
        for p in records.values():
            path=self.store.path/'records'/(digest(p)+'.json')
            if not path.exists():path.write_bytes(envelope(p))
        from style_recipes.canonical import canonical
        (self.store.path/'HEAD').write_bytes(canonical(head))
        with self.assertRaises(StyleError):Store(self.store.path).read()

    def test_store_save_and_reopen_rename_keeps_selection(self):
        f=initial();r=recipe(ACTOR,NOW,'Inactive',[f]);r['properties']=[]
        self.store.commit([r,f],None,ACTOR,NOW)
        adds,new=edited(self.store.read(),r,ACTOR,NOW,name='Renamed')
        self.store.commit(adds,self.store.read().head,ACTOR,NOW)
        self.assertEqual(Store(self.store.path).read().get(ref(new))['properties'],[])
