import base64,copy,errno,io,json,os,sqlite3,unittest,uuid,zipfile
from pathlib import Path
from visual_poster_studio.brands import Store,canonical
from visual_poster_studio.brand_portability import build_package,parse,preview,restore,snapshot,fingerprint,save_backup
from studio_manual_ui.service import UIError
from test_brands import P,UNKNOWN,GRANT

class PortabilityTests(unittest.TestCase):
 def setUp(self):
  parent=Path(os.environ['VISUAL_TEST_ROOT']);self.s=Store(parent/('source-'+uuid.uuid4().hex));self.t=Store(parent/('target-'+uuid.uuid4().hex));self.asset=self.s.command({'action':'register_asset','name':'synthetic.bin','kind':'logo','provenance':{'owner':'Fixture','source':'Synthetic bytes','license':'Test-only first-party'},'data_base64':base64.b64encode(b'OPAQUE PORTABILITY FIXTURE').decode(),'rights':dict(GRANT,scopes=['internal_preview','redistribute'])});self.b=self.save(self.s,dict(P,asset_ids=[self.asset['asset_id']]));self.b=self.s.command({'action':'approve','brand_id':self.b['record']['brand_id'],'expected_head':self.b['hash'],'reviewer':'Fixture reviewer','acknowledge':True})
 def save(self,s,p,b=None):return s.command({'action':'save','brand_id':b['record']['brand_id'] if b else None,'expected_head':b['hash'] if b else None,'payload':p})
 def state(self,s):
  if not s.root.exists():return None
  with s.transaction() as c:return snapshot(s,c)
 def apply(self,raw,target=None,fault=None):
  target=target or self.t;p=preview(target,raw);return restore(target,raw,p['destination_fingerprint'],p['package_sha256'],True,fault)
 def rights(self,record):
  saved=self.s.command({'action':'rights','asset_id':self.asset['asset_id'],'expected_rights':self.asset['rights_hash'],'rights':record});self.asset['rights_hash']=saved['rights_hash']
 def rewritten(self,raw,change):
  with zipfile.ZipFile(io.BytesIO(raw)) as z:files={n:z.read(n) for n in z.namelist()}
  change(files);out=io.BytesIO()
  with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_STORED) as z:
   for n,v in sorted(files.items()):z.writestr(n,v)
  return out.getvalue()
 def test_deterministic_manifest_backup(self):
  a=build_package(self.s);b=build_package(self.s);self.assertEqual(a,b);parsed=parse(a);self.assertEqual(parsed['omissions'],{});self.assertEqual(len(parsed['state']['blobs']),1)
 def test_preview_no_initialization(self):
  p=preview(self.t,build_package(self.s));self.assertTrue(p['can_restore']);self.assertEqual(p['brands'],1);self.assertEqual(p['versions'],2);self.assertFalse(self.t.root.exists());self.assertEqual(p['rights_quarantined'],[self.asset['asset_id']])
 def test_restore_records_bytes_quarantine(self):
  original=self.state(self.s);self.apply(build_package(self.s));target=self.state(self.t)
  for h,raw in original['records'].items():self.assertEqual(target['records'][h],raw)
  self.assertEqual(target['blobs'],original['blobs']);entry=self.t.list()['brands'][0];self.assertEqual(entry['record'],self.b['record']);self.assertFalse(entry['approval_current']);self.assertFalse(entry['creative_use_enabled']);self.assertEqual(self.t.list()['assets'][0]['rights']['status'],'unknown')
 def test_duplicates_noop(self):
  raw=build_package(self.s);self.apply(raw);before=self.state(self.t);p=preview(self.t,raw);self.assertTrue(p['is_noop']);self.apply(raw);self.assertEqual(before,self.state(self.t))
 def test_old_backup_does_not_undo_local_revocation(self):
  raw=build_package(self.s);self.rights(dict(UNKNOWN,status='denied',authority='Owner',evidence='Revoked'));before=self.state(self.s);self.apply(raw,self.s);self.assertEqual(before,self.state(self.s));self.assertFalse(self.s.list()['brands'][0]['approval_current'])
 def test_expired_copy_rights_omitted(self):
  self.rights(dict(GRANT,scopes=['internal_preview','redistribute'],expires='2000-01-01T00:00:00Z'));raw=build_package(self.s);p=preview(self.t,raw);self.assertFalse(p['can_restore']);self.assertEqual(len(p['missing_dependencies']),1)
 def test_unknown_copy_rights_missing_refuses_mutation(self):
  self.rights(UNKNOWN);raw=build_package(self.s);p=preview(self.t,raw)
  with self.assertRaises(UIError):restore(self.t,raw,p['destination_fingerprint'],p['package_sha256'],True)
  self.assertFalse(self.t.root.exists());self.assertEqual(len(p['omitted_assets']),1)
 def test_existing_bytes_satisfy_declared_omission(self):
  raw=build_package(self.s);blob=next(iter(parse(raw)['state']['blobs'].values()));self.t.command({'action':'register_asset','name':'Already-local.bin','kind':'logo','provenance':{'owner':'Fixture','source':'Existing local bytes','license':'Fixture'},'data_base64':base64.b64encode(blob).decode(),'rights':UNKNOWN});self.rights(dict(UNKNOWN,status='denied'));new=build_package(self.s);p=preview(self.t,new);self.assertTrue(p['can_restore']);self.assertEqual(p['missing_dependencies'],[]);self.apply(new);self.assertTrue(all(a['rights']['status'] in ('unknown','denied') for a in self.t.list()['assets']))
 def test_divergent_brand_history_refused(self):
  raw=build_package(self.s);self.apply(raw);self.save(self.s,dict(P,name='Left',asset_ids=[self.asset['asset_id']]),self.b)
  target=self.t.list()['brands'][0];self.save(self.t,dict(P,name='Right',asset_ids=[self.asset['asset_id']]),target);before=self.state(self.t);p=preview(self.t,build_package(self.s));self.assertFalse(p['can_restore']);self.assertTrue(p['conflicts']);self.assertEqual(before,self.state(self.t))
 def test_stale_preview_refused(self):
  raw=build_package(self.s);p=preview(self.t,raw);self.save(self.t,P);before=self.state(self.t)
  with self.assertRaises(UIError):restore(self.t,raw,p['destination_fingerprint'],p['package_sha256'],True)
  self.assertEqual(before,self.state(self.t))
 def test_failed_restore_rolls_back_existing(self):
  self.save(self.t,P);before=self.state(self.t);raw=build_package(self.s)
  def fail(phase):raise OSError('injected interruption')
  with self.assertRaises(OSError):self.apply(raw,fault=fail)
  self.assertEqual(before,self.state(self.t))
 def test_package_hash_and_ack_refusal(self):
  raw=build_package(self.s);p=preview(self.t,raw)
  for h,ack in [('0'*64,True),(p['package_sha256'],False)]:
   with self.assertRaises(UIError):restore(self.t,raw,p['destination_fingerprint'],h,ack)
  self.assertFalse(self.t.root.exists())
 def test_corrupted_record_rejected(self):
  raw=build_package(self.s)
  def corrupt(files):files[next(n for n in files if n.startswith('records/'))]=b'{}'
  with self.assertRaises(UIError):preview(self.t,self.rewritten(raw,corrupt))
  self.assertFalse(self.t.root.exists())
 def test_missing_member_rejected(self):
  with self.assertRaises(UIError):parse(self.rewritten(build_package(self.s),lambda f:f.pop(next(n for n in f if n.startswith('blobs/')))))
 def test_unsupported_version(self):
  def unsupported(f):m=json.loads(f['manifest.json']);m['version']=99;f['manifest.json']=canonical(m)
  with self.assertRaises(UIError):parse(self.rewritten(build_package(self.s),unsupported))
 def test_traversal_unknown_entry_refused(self):
  for name in ['../outside','/absolute','records/../../x','arbitrary.txt']:
   with self.assertRaises(UIError):parse(self.rewritten(build_package(self.s),lambda f:f.update({name:b'x'})))
 def test_truncated_and_compressed_refused(self):
  raw=build_package(self.s)
  with self.assertRaises(UIError):parse(raw[:-10])
  out=io.BytesIO()
  with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('manifest.json',b'{}')
  with self.assertRaises(UIError):parse(out.getvalue())
 def test_backup_exclusive_and_readback(self):
  a=save_backup(self.s);b=save_backup(self.s);self.assertEqual(a,b);self.assertTrue(Path(a['path']).is_file());self.assertEqual(parse(Path(a['path']).read_bytes())['package_sha256'],a['package_sha256'])
 def test_new_library_interruption_empty_recoverable(self):
  raw=build_package(self.s)
  def fail(phase):
   if phase=='before-commit':raise OSError(errno.ENOSPC,'Synthetic precommit disk-full signal')
  with self.assertRaises(OSError):self.apply(raw,fault=fail)
  self.assertEqual(self.t.list()['brands'],[]);self.assertEqual(self.t.list()['assets'],[]);self.apply(raw);self.assertEqual(len(self.t.list()['brands']),1)
 def test_divergent_rights_quarantine_and_revocation_block(self):
  raw=build_package(self.s);self.apply(raw);self.rights(dict(UNKNOWN,status='denied'));before=self.state(self.t);p=preview(self.t,build_package(self.s));self.assertFalse(p['can_restore']);self.assertTrue(any('rights_heads' in x for x in p['conflicts']));self.assertEqual(before,self.state(self.t))
 def test_shared_blob_unknown_alias_cannot_launder_copy(self):
  self.s.command({'action':'register_asset','name':'Unknown alias','kind':'template','provenance':{'owner':'','source':'','license':''},'data_base64':base64.b64encode(b'OPAQUE PORTABILITY FIXTURE').decode(),'rights':UNKNOWN});p=parse(build_package(self.s));self.assertEqual(len(p['state']['blobs']),0);self.assertEqual(len(p['omissions']),1)
 def test_duplicate_zip_members_refused(self):
  import warnings
  raw=build_package(self.s);out=io.BytesIO()
  with zipfile.ZipFile(io.BytesIO(raw)) as source,zipfile.ZipFile(out,'w') as target:
   for name in source.namelist():target.writestr(name,source.read(name))
   with warnings.catch_warnings():warnings.simplefilter('ignore');target.writestr('manifest.json',source.read('manifest.json'))
  with self.assertRaises(UIError):parse(out.getvalue())
 def test_symlink_archive_entry_refused(self):
  raw=build_package(self.s);out=io.BytesIO()
  with zipfile.ZipFile(io.BytesIO(raw)) as source,zipfile.ZipFile(out,'w') as target:
   for n in source.namelist():
    info=zipfile.ZipInfo(n);info.external_attr=(0o120777 if n=='manifest.json' else 0o100644)<<16;target.writestr(info,source.read(n))
  with self.assertRaises(UIError):parse(out.getvalue())
 def test_sqlite_full_rollback_preserves_existing(self):
  from contextlib import contextmanager
  from unittest.mock import patch
  self.save(self.t,P);before=self.state(self.t)
  self.s.command({'action':'register_asset','name':'Bounded full test.bin','kind':'template','provenance':{'owner':'Fixture','source':'Bounded synthetic bytes','license':'First-party fixture'},'data_base64':base64.b64encode(b'X'*65536).decode(),'rights':dict(GRANT,scopes=['internal_preview','redistribute'])})
  raw=build_package(self.s);original=self.t.transaction
  @contextmanager
  def limited(*args,**kwargs):
   with original(*args,**kwargs) as c:
    pages=c.execute('PRAGMA page_count').fetchone()[0];c.execute('PRAGMA max_page_count='+str(pages));yield c
  with patch.object(self.t,'transaction',limited):
   with self.assertRaises(UIError) as caught:self.apply(raw)
   self.assertEqual(caught.exception.__cause__.sqlite_errorcode,sqlite3.SQLITE_FULL)
  self.assertEqual(before,self.state(self.t))
 def test_restore_after_grant_expiry_never_activates(self):
  from unittest.mock import patch
  raw=build_package(self.s)
  with patch('visual_poster_studio.brands.now',return_value='2100-01-01T00:00:00Z'):
   self.apply(raw);self.assertFalse(self.t.list()['assets'][0]['eligibility']['eligible']);self.assertFalse(self.t.list()['brands'][0]['approval_current'])
