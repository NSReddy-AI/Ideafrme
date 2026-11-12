import json
import re
import subprocess
from copy import deepcopy
import unittest
from style_recipes.canonical import loads,canonical,digest,ref,envelope,StyleError
from style_recipes.schema import validate,FORMATS
from style_recipes.state import Snapshot
from style_recipes.store import common,WORKSPACE
from style_recipes.manual import edited,association,finding,recipe,review
from .helpers import *


class CanonicalTests(unittest.TestCase):
    def test_frozen_complete_record_fixtures(self):
        for case in json.loads((WORKSPACE/'r1_tests/fixtures/records.json').read_text()):
            with self.subTest(kind=case['kind']):
                self.assertEqual(validate(case['payload']),case['kind'])
                self.assertEqual(digest(case['payload']),case['sha256'])

    def test_cross_language_frozen_vectors_and_rejections(self):
        fixture=json.loads((WORKSPACE/'r1_tests/fixtures/canonical.json').read_text())
        lines=[];expected=[]
        for v in fixture:
            lines.append(json.dumps(dict(id=v['id'],raw=v['raw'])))
            try:
                obj=loads(v['raw'].encode());py=canonical(obj)
                result=dict(hex=py.hex(),sha256=digest(obj))
                self.assertNotIn('reject',v,v['id'])
                if 'sha256' in v:self.assertEqual(result['sha256'],v['sha256'],v['id'])
                if 'bytes' in v:self.assertEqual(len(py),v['bytes'],v['id'])
            except StyleError:
                self.assertTrue(v.get('reject'),v['id']);result=dict(rejected=True)
            expected.append(result)
        proc=subprocess.run(['node',str(WORKSPACE/'tools/r1_canonical.mjs')],input=('\n'.join(lines)+'\n').encode(),
                            stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=WORKSPACE,timeout=20,check=True)
        actual=[json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual(len(actual),len(expected))
        for a,e in zip(actual,expected):
            ident=a['id'];self.assertEqual({k:v for k,v in a.items() if k!='id'},e,ident)
        (WORKSPACE/'.runtime/r1/cross-language-results.json').write_text(json.dumps(dict(
            cases=len(actual),languages=['Python','JavaScript/Node'],results=actual),indent=2)+'\n')

    def test_bounds_before_parsing(self):
        for raw in (b'['*33+b']'*33, ('{"x":'+('"x"'*1048576)+'}').encode(),
                    ('{'+','.join('"k%d":0'%i for i in range(501))+'}').encode(),
                    ('['+','.join('0' for _ in range(4097))+']').encode()):
            with self.assertRaises(StyleError):loads(raw)

    def test_unknown_missing_fields_and_numeric_types(self):
        p=rights()
        for change in ({'unknown':0},{'created_by':True},{'created_at':'2026-02-30T00:00:00Z'},
                       {'format':FORMATS['rights-decision'].replace('@1','@2')}):
            with self.subTest(change=change),self.assertRaises(StyleError):validate(dict(p,**change))
        q=deepcopy(p);del q['expires_at']
        with self.assertRaises(StyleError):validate(q)

    def test_decimal_units_and_catalog(self):
        for val in ('00','01','-0','-0.0','1.0','0.650','+1','1e-2','.5','1.',' 0.65'):
            with self.subTest(val=val),self.assertRaises(StyleError):
                finding(ACTOR,NOW,'layout.margin',dict(kind='decimal',value=val,unit='ratio'))
        for val in ('0.46','-0.1'):
            with self.assertRaises(StyleError):finding(ACTOR,NOW,'layout.margin',dict(kind='decimal',value=val,unit='ratio'))
        with self.assertRaises(StyleError):finding(ACTOR,NOW,'layout.margin',dict(kind='decimal',value='0.1',unit='px'))
        with self.assertRaises(StyleError):finding(ACTOR,NOW,'motion.duration',dict(kind='decimal',value='1',unit='px'))


class LifecycleTests(unittest.TestCase):
    def setUp(self):self.s=new_store()

    def test_manual_save_reopen_edit_immutable(self):
        f,r=approved(self.s);before=(self.s.path/'records'/ (digest(r)+'.json')).read_bytes()
        additions,new=edited(self.s.read(),r,ACTOR,NOW,prop='palette.primary',value=dict(kind='color',rgba='#112233ff'),reason='Manual revision')
        save(self.s,additions)
        self.assertNotEqual(ref(new),ref(r));self.assertEqual(new['parent'],ref(r))
        self.assertEqual((self.s.path/'records'/(digest(r)+'.json')).read_bytes(),before)
        self.assertFalse(self.s.read().eligible(ref(new),NOW)['eligible'])
        self.assertFalse(self.s.read().eligible(ref(r),NOW)['eligible']) # correction invalidates old finding pin
        self.assertEqual(self.s.read().get(ref(r)),r)

    def test_revocation_transitive_and_fresh_ordered_reviews(self):
        f,r=approved(self.s);self.assertTrue(self.s.read().eligible(ref(r),NOW)['eligible'])
        approve(self.s,f,'revoke');self.assertFalse(self.s.read().eligible(ref(r),NOW)['eligible'])
        approve(self.s,f);self.assertFalse(self.s.read().eligible(ref(r),NOW)['eligible'])
        approve(self.s,r);self.assertTrue(self.s.read().eligible(ref(r),NOW)['eligible'])

    def test_availability_restore_does_not_restore_approval(self):
        f,r=approved(self.s);available(self.s,f,'missing');available(self.s,f)
        self.assertFalse(self.s.read().eligible(ref(f),NOW)['eligible'])
        with self.assertRaises(StyleError):approve(self.s,r)
        approve(self.s,f);approve(self.s,r)
        self.assertTrue(self.s.read().eligible(ref(r),NOW)['eligible'])

    def test_explicit_confirmation_and_exact_predecessor(self):
        f,r=manual(self.s);available(self.s,f)
        e=review(self.s.read(),ref(f),ACTOR,NOW,'approve','A','Review')
        with self.assertRaises(StyleError):save(self.s,[e],'review')
        approve(self.s,f)
        with self.assertRaises(StyleError):save(self.s,[e],'review',confirmed=True)

    def test_immutable_identity_reuse_is_rejected(self):
        f,r=manual(self.s);changed=dict(r,name='Overwritten')
        with self.assertRaises(StyleError):save(self.s,[changed])

    def test_manual_only_and_poster_only(self):
        f,r=manual(self.s)
        for changes in ({'origin':'measured'},{'origin':'inferred'},{'region':dict(x='0',y='0',width='1',height='1')}, {'method':ref(f)}):
            with self.subTest(changes=changes),self.assertRaises(StyleError):validate(dict(f,**changes))
        with self.assertRaises(StyleError):validate(dict(r,outputs=['reel']))

    def test_global_lock_and_brand_rule_conflict(self):
        f,r=manual(self.s);available(self.s,f);approve(self.s,f)
        r2=recipe(ACTOR,NOW,'locked',[f],prior=r,protections=[dict(target=None,mode='locked',protected_aspects=['content'])])
        save(self.s,[r2])
        with self.assertRaises(StyleError):approve(self.s,r2)

    def test_brand_versions_benign_and_adverse_dependency_invalidation(self):
        b=common('brand',ACTOR,NOW)
        b.update(brand_id=b['record_id'],parent=None,name='Fixture brand',hard_rules=[],guided_rules=[],protections=[])
        save(self.s,[b])
        rd=rights(resource=digest(b));save(self.s,[rd],'rights-decision',confirmed=True)
        approve(self.s,rd,authority='B',verified_evidence=rd['evidence_sha256'])
        d=dependency(rd,kind='brand',name='Fixture brand');save(self.s,[d]);available(self.s,d)
        f=finding(ACTOR,NOW,'palette.primary',dict(kind='color',rgba='#3366ffff'))
        r=recipe(ACTOR,NOW,'Pinned brand recipe',[f],[d],brand=b)
        save(self.s,[f,r]);available(self.s,f);approve(self.s,f);approve(self.s,r)
        self.assertTrue(self.s.read().eligible(ref(r),NOW)['eligible'])
        b2=dict(b,record_id=str(uuid4()),parent=ref(b),name='Optional new variant')
        with self.assertRaises(StyleError):save(self.s,[b2])
        save(self.s,[b2],brand_classification='benign',confirmed=True)
        self.assertTrue(self.s.read().eligible(ref(r),NOW)['eligible'])
        b3=dict(b2,record_id=str(uuid4()),parent=ref(b2),name='Mandatory protection change')
        # Adverse changes to an existing pin first require dependency invalidation.
        with self.assertRaises(StyleError):save(self.s,[dict(b3,parent=ref(b))],brand_classification='adverse',confirmed=True)
        available(self.s,d,'stale')
        save(self.s,[dict(b3,parent=ref(b))],brand_classification='adverse',confirmed=True)
        self.assertFalse(self.s.read().eligible(ref(r),NOW)['eligible'])
        self.assertEqual(self.s.read().get(ref(r))['brand'],ref(b))
        self.assertTrue(list((self.s.path/'quarantine').glob('brand-review-*.json')))

    def test_brand_constraints_reject_conflicting_recipe(self):
        b=common('brand',ACTOR,NOW)
        b.update(brand_id=b['record_id'],parent=None,name='Constrained',hard_rules=[dict(property='palette.primary',
            allowed=[dict(kind='color',rgba='#000000ff')],minimum=None,maximum=None,unit=None)],guided_rules=[],protections=[])
        d=dependency(kind='brand',content_sha256=digest(b));f=finding(ACTOR,NOW,'palette.primary',dict(kind='color',rgba='#ffffffff'))
        r=recipe(ACTOR,NOW,'Conflict',[f],[d],brand=b);save(self.s,[b,d,f,r]);available(self.s,f);approve(self.s,f)
        self.assertFalse(self.s.read().eligible(ref(r),NOW,prerequisites=True)['eligible'])

    def test_malformed_nested_types_fail_as_schema_errors(self):
        for p in (dict(rights(),permitted_uses=[{}]),dict(rights(),project_ids=[{}]),
                  dict(recipe(ACTOR,NOW,'x'),protections=[dict(target=None,mode='free',protected_aspects=[{}])])):
            with self.subTest(payload=p),self.assertRaises(StyleError):validate(p)

    def test_unknown_required_capability_blocks_approval(self):
        f,r=manual(self.s);available(self.s,f);approve(self.s,f)
        d=dependency(kind='capability',name='unknown-capability')
        r2=recipe(ACTOR,NOW,'caps',[f],[d],prior=r);r2['required_capabilities']=['unknown-capability']
        save(self.s,[d,r2])
        with self.assertRaises(StyleError):approve(self.s,r2)

    def test_missing_reference_and_hash_mismatch(self):
        f,r=manual(self.s);r2=deepcopy(r);r2.update(record_id=str(uuid4()),revision_id=None,parent=ref(r))
        r2['revision_id']=r2['record_id'];r2['findings'][0]['sha256']='f'*64
        with self.assertRaises(StyleError):save(self.s,[r2])

    def test_project_snapshot_and_creative_compatibility(self):
        from creative_core.document import new_document,fingerprint
        from creative_core.validation import validate as creative_validate
        creative=new_document();before=canonical(creative);creative_validate(creative,WORKSPACE)
        f,r=approved(self.s)
        a=association(self.s.read(),ref(r),ACTOR,NOW,PROJECT,
                      dict(format=creative['format'],id=creative['id'],fingerprint=fingerprint(creative)),library=True)
        save(self.s,[a],'associate')
        adds,r2=edited(self.s.read(),r,ACTOR,NOW,name='Library revision');save(self.s,adds)
        self.assertEqual(self.s.read().get(ref(a))['snapshot'],ref(r))
        self.assertEqual(canonical(creative),before);creative_validate(creative,WORKSPACE)
        self.assertTrue(self.s.read().eligible(ref(a),NOW)['eligible'])


class RightsTests(unittest.TestCase):
    def setUp(self):self.s=new_store()

    def fixture(self,rd=None):
        rd=rd or rights();save(self.s,[rd],'rights-decision',confirmed=True)
        approve(self.s,rd,authority='B',verified_evidence=rd['evidence_sha256'])
        d=dependency(rd);save(self.s,[d]);available(self.s,d)
        f=finding(ACTOR,NOW,'palette.primary',dict(kind='color',rgba='#112233ff'),evidence=[ref(d)])
        r=recipe(ACTOR,NOW,'Rights-bound',[f],[d]);save(self.s,[f,r]);available(self.s,f);approve(self.s,f);approve(self.s,r)
        return rd,d,f,r

    def test_rights_valid_and_expired_and_scope(self):
        rd,d,f,r=self.fixture(rights(expires_at='2027-01-01T00:00:00Z'))
        self.assertTrue(self.s.read().eligible(ref(r),NOW)['eligible'])
        self.assertFalse(self.s.read().eligible(ref(r),'2027-01-01T00:00:00Z')['eligible'])
        self.assertFalse(self.s.read().eligible(ref(r),'2025-01-01T00:00:00Z')['eligible'])

    def test_revoked_rights_immediately_block_without_review(self):
        rd,d,f,r=self.fixture()
        rev=rights(resource=rd['resource_sha256'],rights_id=rd['rights_id'],supersedes=ref(rd),decision='revoke',permitted_uses=[],outputs=[])
        save(self.s,[rev],'rights-decision',confirmed=True)
        self.assertFalse(self.s.read().eligible(ref(r),NOW)['eligible'])
        self.assertEqual(self.s.read().get(ref(rd)),rd)

    def test_missing_unreviewed_or_out_of_scope_rights(self):
        d=dependency();save(self.s,[d]);available(self.s,d)
        self.assertFalse(self.s.read().eligible(ref(d),NOW)['eligible'])
        rd=rights(project_ids=[PROJECT]);save(self.s,[rd],'rights-decision',confirmed=True)
        approve(self.s,rd,authority='B',verified_evidence=rd['evidence_sha256'])
        d2=dependency(rd);save(self.s,[d2]);available(self.s,d2)
        self.assertFalse(self.s.read().eligible(ref(d2),NOW)['eligible'])
        self.assertTrue(self.s.read().eligible(ref(d2),NOW,PROJECT)['eligible'])

    def test_rights_evidence_authority_and_obligations(self):
        rd=rights();save(self.s,[rd],'rights-decision',confirmed=True)
        with self.assertRaises(StyleError):approve(self.s,rd,authority='A',verified_evidence=rd['evidence_sha256'])
        with self.assertRaises(StyleError):approve(self.s,rd,authority='B',verified_evidence='c'*64)
        approve(self.s,rd,authority='B',verified_evidence=rd['evidence_sha256'])
        self.assertTrue(self.s.read().eligible(ref(rd),NOW)['eligible'])

    def test_unknown_obligation_blocks_clearance(self):
        rd=rights(obligations=[dict(kind='notice',text='Required notice; satisfaction not established')])
        save(self.s,[rd],'rights-decision',confirmed=True)
        with self.assertRaises(StyleError):approve(self.s,rd,authority='B',verified_evidence=rd['evidence_sha256'])

    def test_restored_rights_never_reactivate_old_pin(self):
        rd,d,f,r=self.fixture()
        denied=rights(resource=rd['resource_sha256'],rights_id=rd['rights_id'],supersedes=ref(rd),decision='deny',permitted_uses=[],outputs=[])
        save(self.s,[denied],'rights-decision',confirmed=True)
        restored=rights(resource=rd['resource_sha256'],rights_id=rd['rights_id'],supersedes=ref(denied))
        save(self.s,[restored],'rights-decision',confirmed=True)
        approve(self.s,restored,authority='B',verified_evidence=restored['evidence_sha256'])
        self.assertFalse(self.s.read().eligible(ref(r),NOW)['eligible'])

    def test_competing_rights_chain_and_resource_mismatch(self):
        rd=rights();save(self.s,[rd],'rights-decision',confirmed=True)
        with self.assertRaises(StyleError):save(self.s,[rights()],'rights-decision',confirmed=True)
        with self.assertRaises(StyleError):save(self.s,[dependency(rd,content_sha256='d'*64)])
