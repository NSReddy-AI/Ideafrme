import base64,copy,json,os,sqlite3,unittest,uuid
from pathlib import Path
from visual_poster_studio.brands import Store,ROOT,rights
from studio_manual_ui.service import UIError

UNKNOWN={'status':'unknown','authority':'','evidence':'','scopes':[],'destinations':[],'expires':None}
GRANT={'status':'granted','authority':'Synthetic owner','evidence':'Synthetic fixture rights','scopes':['internal_preview'],'destinations':['library_metadata'],'expires':'2099-01-01T00:00:00Z'}
P={'name':'తెలుగు Brand','colors':['#112233','#FFFFFF'],'typography':{'english':'Inter Bold','telugu':'Noto Sans Telugu'},'mandatory_rules':['Preserve logo geometry'],'preferences':['Calm spacing'],'inspiration':['Editorial'],'notes':'','asset_ids':[]}
class BrandTests(unittest.TestCase):
 def setUp(self):self.root=Path(os.environ['VISUAL_TEST_ROOT'])/('library-'+uuid.uuid4().hex);self.s=Store(self.root)
 def save(self,p=None,brand=None):return self.s.command({'action':'save','brand_id':brand['record']['brand_id'] if brand else None,'expected_head':brand['hash'] if brand else None,'payload':copy.deepcopy(P if p is None else p)})
 def asset(self,kind='logo',r=None):return self.s.command({'action':'register_asset','name':'synthetic.bin','kind':kind,'provenance':{'owner':'Synthetic','source':'Test fixture','license':'First-party test'},'data_base64':base64.b64encode(b'OPAQUE NOT AN IMAGE').decode(),'rights':copy.deepcopy(UNKNOWN if r is None else r)})
 def approve(self,b):return self.s.command({'action':'approve','brand_id':b['record']['brand_id'],'expected_head':b['hash'],'reviewer':'Synthetic reviewer','acknowledge':True})
 def decision(self,a,r):return self.s.command({'action':'rights','asset_id':a['asset_id'],'expected_rights':a['rights_hash'],'rights':r})
 def test_absent_read_does_not_initialize(self):self.assertEqual(self.s.list()['brands'],[]);self.assertFalse(self.root.exists())
 def test_multiple_brands_reopen_exact(self):
  a=self.save();b=self.save(dict(P,name='Second'));reopened=Store(self.root).list();self.assertEqual(len(reopened['brands']),2);self.assertIn(a,reopened['brands']);self.assertIn(b,reopened['brands'])
 def test_immutable_approval_revision_history(self):
  a=self.save();approved=self.approve(a);new=self.save(dict(P,name='New name'),approved);history=self.s.command({'action':'history','brand_id':a['record']['brand_id']})['versions'];self.assertEqual(history,[new,approved,a]);self.assertEqual(approved['record']['payload']['name'],P['name'])
 def test_stale_brand_update_rejected(self):
  a=self.save();self.save(P,a)
  with self.assertRaises(UIError):self.save(P,a)
 def test_unknown_rights_blocks_approval(self):
  a=self.asset();b=self.save(dict(P,asset_ids=[a['asset_id']]))
  with self.assertRaises(UIError):self.approve(b)
 def test_expired_and_scope_deny(self):
  for grant in [dict(GRANT,expires='2000-01-01T00:00:00Z'),dict(GRANT,scopes=['commercial_design']),dict(GRANT,destinations=['poster'])]:
   a=self.asset(r=grant);b=self.save(dict(P,asset_ids=[a['asset_id']]))
   with self.assertRaises(UIError):self.approve(b)
 def test_revocation_regrant_no_approval_resurrection(self):
  a=self.asset(r=GRANT);b=self.approve(self.save(dict(P,asset_ids=[a['asset_id']])));frozen=copy.deepcopy(b['record']);revoked=self.decision(a,dict(UNKNOWN,status='denied',authority='Owner',evidence='Withdrawn'));a['rights_hash']=revoked['rights_hash'];self.assertFalse(self.s.list()['brands'][0]['approval_current']);self.decision(a,GRANT);current=self.s.list()['brands'][0];self.assertFalse(current['approval_current']);self.assertEqual(current['record'],frozen)
 def test_all_declared_asset_kinds_opaque_identity(self):
  for kind in ['logo','image','font','template']:self.asset(kind)
  assets=self.s.list()['assets'];self.assertEqual(len(assets),4);self.assertEqual(len({a['record']['sha256'] for a in assets}),1);self.assertTrue(all(not a['decoding_enabled'] for a in assets))
 def test_invalid_rights_and_expiry(self):
  for r in [dict(GRANT,authority=''),dict(GRANT,expires=None),dict(GRANT,expires='2099-02-31T00:00:00Z'),dict(GRANT,scopes=['unknown']),dict(UNKNOWN,scopes=['internal_preview'])]:
   with self.assertRaises(UIError):rights(r)
 def test_asset_paths_and_malformed_bytes_refused(self):
  for name,data in [('../outside','YQ=='),('ok','!invalid!')]:
   with self.assertRaises(UIError):self.s.command({'action':'register_asset','name':name,'kind':'logo','provenance':{'owner':'','source':'','license':''},'data_base64':data,'rights':UNKNOWN})
  self.assertEqual(self.s.list()['assets'],[])
 def test_missing_reference_refused(self):
  with self.assertRaises(UIError):self.save(dict(P,asset_ids=[str(uuid.uuid4())]))
 def test_approval_ack_and_current_draft(self):
  b=self.save()
  with self.assertRaises(UIError):self.s.command({'action':'approve','brand_id':b['record']['brand_id'],'expected_head':b['hash'],'reviewer':'R','acknowledge':False})
  b=self.approve(b)
  with self.assertRaises(UIError):self.approve(b)
 def test_database_immutability_and_unknown_version(self):
  b=self.save()
  with self.s.transaction() as c:
   with self.assertRaises(sqlite3.DatabaseError):c.execute('DELETE FROM records')
  con=sqlite3.connect(self.root/'library.sqlite3');con.execute('PRAGMA user_version=99');con.close()
  with self.assertRaises(UIError):self.s.list()
 def test_corrupt_record_hash_refused(self):
  self.save();con=sqlite3.connect(self.root/'library.sqlite3');con.execute('DROP TRIGGER records_update');con.execute("UPDATE records SET payload=?",(b'{}',));con.commit();con.close()
  with self.assertRaises(UIError):self.s.list()
 def test_transaction_rollback_registration(self):
  with self.assertRaises(UIError):self.asset(r=dict(GRANT,authority=''))
  self.assertEqual(self.s.list()['assets'],[])
 def test_rights_stale_decision_refused(self):
  a=self.asset();self.decision(a,GRANT)
  with self.assertRaises(UIError):self.decision(a,GRANT)
 def test_writer_lock_refuses_competing_operation(self):
  self.save()
  with self.s.transaction():
   with self.assertRaises(UIError):Store(self.root).list()
 def test_symlink_store_refused(self):
  alias=self.root.parent/('alias-'+uuid.uuid4().hex);self.save();alias.symlink_to(self.root,target_is_directory=True)
  with self.assertRaises(UIError):Store(alias)
 def test_opaque_blob_corruption_refused(self):
  self.asset();con=sqlite3.connect(self.root/'library.sqlite3');con.execute('DROP TRIGGER blobs_update');con.execute('UPDATE blobs SET data=?',(b'changed',));con.commit();con.close()
  with self.assertRaises(UIError):self.s.list()
