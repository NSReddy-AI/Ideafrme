"""New quarantined envelope; embedded creative/binding records keep their original versions."""
import re
import creative_core as core
from creative_core.document import canonical
from studio_manual_ui.service import UIError,exact,project_id
from visual_poster_studio.project_bindings import validate as binding_validate
from visual_poster_studio.brands import validate_record
FORMAT='studio-media-workflow@1'
MAX_ENVELOPE=10*1024*1024
CANDIDATES={'png':{'logo','image'},'svg':{'logo','image'},'ttf':{'font'},'otf':{'font'}}
def require(ok,message):
 if not ok:raise UIError('media-contract',message,409)
def commit_name(v):return type(v)==str and re.fullmatch(r'[0-9]{8}-[0-9a-f]{32}',v) is not None
def digest(v):return type(v)==str and re.fullmatch(r'[0-9a-f]{64}',v) is not None
def validate(value,root,session_id):
 exact(value,{'format','version','session_id','generation','parent','document','binding','admissions','state','recovered_from'})
 require(value['format']==FORMAT and type(value['version'])==int and value['version']==1,'Unsupported media workflow version.')
 require(value['session_id']==session_id,'Foreign media session.')
 require(type(value['generation'])==int and 1<=value['generation']<=200,'Invalid workflow generation.')
 require(value['parent'] is None or commit_name(value['parent']),'Invalid workflow ancestry.')
 require(value['state']=='quarantined','Only quarantined foundation state is implemented; no qualified outputs accepted.')
 doc=value['document'];require(type(doc)==dict and doc.get('assets')==[],'Foundation cannot publish active asset references before containment qualifies.')
 # No asset reads: assets are empty before core validation (including historical snapshots).
 history=doc.get('history');require(type(history)==dict and type(history.get('transactions'))==list and all(type(t)==dict for t in history['transactions']),'Invalid history structure.');require(type(doc.get('versions'))==list and all(type(v)==dict for v in doc['versions']),'Invalid named snapshots.')
 states=[doc]+[s for tx in doc.get('history',{}).get('transactions',[]) for s in (tx.get('before',{}),tx.get('after',{}))]+[v.get('snapshot',{}) for v in doc.get('versions',[])]
 require(all(type(s)==dict and s.get('assets')==[] for s in states),'No historical active assets admitted by this foundation.')
 require(len(canonical(doc))<=8*1024*1024,'Creative payload exceeds 8 MiB.');core.validate(doc,root);project_id(doc['id']);binding_validate(value['binding'],session_id,doc['id'])
 require(type(value['admissions'])==list and len(value['admissions'])<=64,'Maximum 64 quarantined asset admissions.')
 seen=set()
 for a in value['admissions']:
  exact(a,{'asset_id','asset_record_hash','asset','rights_hash','declared_format','state'})
  project_id(a['asset_id']);require(a['asset_id'] not in seen,'Duplicate asset admission.');seen.add(a['asset_id']);validate_record(a['asset'])
  require(a['asset']['type']=='asset' and a['asset']['id']==a['asset_id'],'Admission identity mismatch.')
  require(digest(a['asset_record_hash']) and digest(a['rights_hash']),'Invalid admission hashes.')
  import hashlib
  require(hashlib.sha256(canonical(a['asset'])).hexdigest()==a['asset_record_hash'],'Asset record hash mismatch.')
  require(type(a['declared_format'])==str and a['declared_format'] in CANDIDATES and a['asset']['kind'] in CANDIDATES[a['declared_format']],'Unsupported candidate format/kind.')
  require(a['state']=='quarantined-unparsed','Admission is not format validation or clearance to decode.')
  pin=value['binding']['brand'];require(pin is not None and a['asset_id'] in pin['record']['payload']['asset_ids'],'Asset is not in pinned approved brand.')
  matches=[b for b in pin['record']['bindings'] if b['asset_id']==a['asset_id']]
  require(len(matches)==1 and matches[0]['rights_hash']==a['rights_hash'] and matches[0]['sha256']==a['asset']['sha256'],'Admission does not match approved asset/rights binding.')
 if value['recovered_from'] is not None:
  r=value['recovered_from'];exact(r,{'session_id','commit','envelope_sha256'});project_id(r['session_id']);require(commit_name(r['commit']) and digest(r['envelope_sha256']),'Invalid recovery source.')
 require(len(canonical(value))<=MAX_ENVELOPE,'Workflow envelope exceeds 10 MiB.');return value
