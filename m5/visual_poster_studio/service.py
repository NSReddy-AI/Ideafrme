"""Composition over accepted manual APIs; separate fresh session and derived scenes."""
from studio_manual_ui.service import Studio, UIError, exact
from .fonts import Fonts
from .scene import build_scene
from .exports import Exports
from .session import marker,initialize,root_path,sync_directory
from .recovery import Journal
from studio_manual_ui.service import safe,project_id,manual_subset,decode,read
import creative_core as core

class VisualStudio:
    def __init__(self,root,*,resume=False):
        root=root_path(root)
        if resume:marker(root)  # ownership only; no project reads before the writer lock
        self.manual=Studio(root,resume=resume)
        self.root=root
        try:
            if not resume:initialize(root)
            else:sync_directory(root)
            self.journal=Journal(root,resume=resume)
            self.exports=Exports(root,resume=resume)
            self.project_errors={}
            if resume:
                for directory in self.manual.projects.iterdir():
                    safe(directory);identity=project_id(directory.name)
                    if not directory.is_dir():raise UIError('session','Invalid project directory.')
                    state=self.journal.inspect(identity)
                    if state['state']!='clean':self.project_errors[identity]=state;continue
                    if (directory/'creative.json').exists():
                        try:self.manual.reopen(identity)
                        except (UIError,OSError):self.project_errors[identity]={'state':'invalid-document','detail':'Document/history validation failed.'}
        except Exception:
            self.manual.close();raise
        try:
            from .project_bindings import Pairs
            self.pairs=Pairs(root,self.journal);self.journal.extra_usage=self.pairs.usage
            self.pairs.scan(self.manual);self.project_errors.update(self.pairs.errors)
        except Exception:
            self.manual.close();raise
        self.fonts=None;self.font_error=None
        try:self.fonts=Fonts()
        except UIError as exc:self.font_error=exc.detail
    def close(self):self.manual.close()
    def status(self):
        return {'ownership':'visual-session@1','durability':'application-crash-recovery; physical-power-loss-unverified',
                'recovery':{**self.project_errors,**self.pairs.errors},'exports':self.exports.status,'recovery_bytes':self.journal.usage()}
    def analysis(self):
        result=self.manual.analysis();result['session_status']=self.status();return result
    def _ready(self,identity):
        project_id(identity)
        if identity in self.project_errors or identity in self.pairs.errors or self.journal.states.get(identity,{}).get('state','clean')!='clean':
            raise UIError('recovery-required','Project requires explicit recovery; original files preserved.',409)
    def list_projects(self):
        result=[]
        for path in sorted(self.manual.projects.iterdir()):
            safe(path);identity=project_id(path.name)
            if identity in self.project_errors:continue
            if identity not in self.manual._working and not (path/'creative.json').exists():continue
            value=self.manual.view(identity);result.append({k:value[k] for k in ('project_id','name','dirty','saved')})
        return result
    def _decorate(self,value):
        value['history_version']=self.manual.document(value['project_id'])['history'].get('version',1)
        from .binding_workflow import binding_state
        value['binding']=binding_state(self,value['project_id'])
        from .brand_application import status
        value['brand_application']=status(self,value['project_id'])
        return value
    def view(self,identity):
        self._ready(identity);return self._decorate(self.manual.view(identity))
    def create(self,request):
        if type(request)==dict and type(request.get('text'))==str and len(request['text'].split('\n'))>64:raise UIError('limit','64 explicit lines maximum.')
        return self._decorate(self.manual.create(request))
    def action(self,request):
        if type(request)!=dict:raise UIError('request','Object required.')
        from .brand_application import action
        return action(self,request,self._action)
    def _action(self,request):
        if type(request)!=dict:raise UIError('request','Object required.')
        if request.get('action')=='save' and request.get('project_id') in self.pairs.bindings:
            from .binding_workflow import save
            self._ready(request['project_id'])
            with self.manual.lock:return save(self,request)
        if request.get('action')=='geometry':
            exact(request,{'project_id','expected_revision','action','view_id','targets','acknowledge_upgrade'})
            identity=project_id(request['project_id']);self._ready(identity)
            with self.manual.lock:
                doc=self.manual.document(identity)
                if type(request['expected_revision'])!=int or request['expected_revision']!=doc['revision']:raise UIError('conflict','Stale geometry revision.',409)
                if type(request['acknowledge_upgrade'])!=bool:raise UIError('request','Explicit upgrade acknowledgement must be boolean.')
                operation={k:request[k] for k in ('expected_revision','view_id','targets')};operation['op']='geometry'
                if doc['history'].get('version',1)<3:
                    if not request['acknowledge_upgrade']:raise UIError('upgrade-required','Explicit history v3 acknowledgement required.',409)
                    operation.update(acknowledge_upgrade=True,legacy_checkpoint_sha256=self.context_checkpoint(identity,doc))
                try:candidate=core.apply(doc,operation,self.manual.projects/identity)
                except core.CreativeError as exc:raise UIError('geometry',str(exc)) from exc
                manual_subset(candidate);self.manual._working[identity]=candidate
                return self._decorate(self.manual.view(identity))
        if request.get('action')=='remove':
            exact(request,{'project_id','expected_revision','action','element_id'})
            identity=project_id(request['project_id']);self._ready(identity)
            with self.manual.lock:
                doc=self.manual.document(identity)
                if type(request['expected_revision'])!=int or request['expected_revision']!=doc['revision']:raise UIError('conflict','Stale layer removal revision.',409)
                try:candidate=core.apply(doc,{'op':'remove','element_id':request['element_id']},self.manual.projects/identity)
                except core.CreativeError as exc:raise UIError('remove',str(exc)) from exc
                manual_subset(candidate);self.manual._working[identity]=candidate
                return self._decorate(self.manual.view(identity))
        if request.get('action')=='reorder':
            exact(request,{'project_id','expected_revision','action','view_id','ordered_element_ids','acknowledge_upgrade'})
            identity=project_id(request['project_id']);self._ready(identity)
            with self.manual.lock:
                doc=self.manual.document(identity)
                if type(request['expected_revision'])!=int or request['expected_revision']!=doc['revision']:raise UIError('conflict','Stale reorder revision.',409)
                if type(request['acknowledge_upgrade'])!=bool:raise UIError('request','Explicit upgrade acknowledgement must be boolean.')
                operation={k:request[k] for k in ('expected_revision','view_id','ordered_element_ids')};operation['op']='reorder'
                if doc['history'].get('version',1)==1:
                    if not request['acknowledge_upgrade']:raise UIError('upgrade-required','Explicit history upgrade acknowledgement required.',409)
                    operation.update(acknowledge_upgrade=True,legacy_checkpoint_sha256=self.context_checkpoint(identity,doc))
                try:candidate=core.apply(doc,operation,self.manual.projects/identity)
                except core.CreativeError as exc:raise UIError('reorder',str(exc)) from exc
                manual_subset(candidate)
                self.manual._working[identity]=candidate
                return self._decorate(self.manual.view(identity))
        if request.get('project_id') is not None:self._ready(request['project_id'])
        if request.get('action')=='save':
            exact(request,{'project_id','expected_revision','action'})
            with self.manual.lock:
                try:return self._decorate(self.journal.save(self.manual,request))
                except (UIError,OSError) as exc:
                    state=self.journal.inspect(request['project_id'])
                    if state['state']=='clean' and getattr(exc,'code',None)=='recovery-required':state={'state':'durability-unconfirmed','detail':'Save completion synchronization failed; project blocked in this process.'}
                    if state['state']!='clean':self.project_errors[request['project_id']]=state
                    if isinstance(exc,OSError):raise UIError('save-failed','Save could not start or finish; original files were not automatically repaired.') from exc
                    raise
        # Check render text capacity before asking the accepted API to commit.
        if type(request)==dict and request.get('action') in {'edit_text','add_text'}:
            with self.manual.lock:
                doc=self.manual.document(request.get('project_id'))
                texts={c['id']:c['text'] for c in doc['content']}
                total=sum(len(texts[e['content_id']]) for e in doc['elements'] if e['type']=='text')
                if request['action']=='edit_text' and type(request.get('text'))==str:
                    e=next((e for e in doc['elements'] if e['id']==request.get('element_id') and e['type']=='text'),None)
                    if e:total+=len(request['text'])-len(texts[e['content_id']])
                    if len(request['text'].split('\n'))>64:raise UIError('limit','64 explicit lines maximum.')
                elif request['action']=='add_text':
                    used={e.get('content_id') for e in doc['elements']}
                    slot=next((c for c in doc['content'] if c['language']==request.get('language') and c['id'] not in used),None)
                    total+=len(slot['text']) if slot else 0
                if total>20000:raise UIError('limit','20,000 active Unicode code points maximum.')
                return self._decorate(self.manual.action(request))
        return self._decorate(self.manual.action(request))
    def context_checkpoint(self,identity,doc):
        digest=self.journal.checkpoint(identity,doc)
        if identity in self.pairs.bindings:self.pairs.commit(identity,doc,self.pairs.bindings[identity],self.pairs.heads[identity],publish=False)
        return digest
    def reopen(self,identity,expected_revision=None):
        self._ready(identity)
        if identity in self.pairs.bindings:
            with self.manual.lock:
                if expected_revision is not None:self.manual._expected(identity,expected_revision)
                doc=self.pairs.load(identity);self.pairs.install(self.manual,identity,doc)
                return self._decorate(self.manual.view(identity))
        return self._decorate(self.manual.reopen(identity,expected_revision))
    def scene(self,identity,revision):
        self._ready(identity)
        with self.manual.lock:
            doc=self.manual.document(identity)
            if type(revision)!=int or doc['revision']!=revision:raise UIError('conflict','Project revision changed.',409)
            if self.fonts is None:raise UIError('font',self.font_error)
            from .binding_workflow import bound_scene
            return bound_scene(self,identity,build_scene(doc,self.fonts))
    def begin(self,request):
        exact(request,{'project_id','expected_revision'})
        with self.manual.lock:
            return self.exports.begin(request['project_id'],self.scene(request['project_id'],request['expected_revision']))
    def navigation(self):
        # Explicit refresh, fixed owned root only. No downloads, path arguments or repairs.
        self.exports.status=self.exports.audit()
        receipts=[]
        for directory in sorted(self.exports.root.iterdir()):
            safe(directory)
            if not directory.is_dir():continue
            item={'id':directory.name,'state':'partial','revision':None,'svg_sha256':None,'png_sha256':None,'directory':str(directory)}
            if directory.name in self.exports.status['errors']:item['state']='review-required'
            elif (directory/'manifest.json').exists():
                value=decode(read(directory/'manifest.json',65536))
                if type(value.get('revision')) is not int or value['revision']<0:
                    item['state']='review-required';self.exports.status['errors'].append(directory.name);self.exports.status['blocked']=True
                else:item.update(state='draft',revision=value['revision'],svg_sha256=value['svg_sha256'],png_sha256=value['png_sha256'])
            receipts.append(item)
        return {'runtime_root':str(self.root),'projects':self.list_projects(),'exports':receipts,'export_status':self.exports.status,
                'recovery':{**self.project_errors,**self.pairs.errors},'recovery_bytes':self.journal.usage(),'analysis':'OFF','history_support':[1,2,3]}
    def finish(self,request):
        exact(request,{'token','revision','png','qa'})
        with self.manual.lock:
            p=self.exports.pending
            if not p:raise UIError('export','No export in flight.',409)
            current=self.manual.document(p['identity'])['revision']
            if p['identity'] in self.pairs.bindings:
                scene=self.scene(p['identity'],current)
                if scene.get('binding_identity')!=p['scene'].get('binding_identity'):raise UIError('stale','Bound export identity changed.',409)
            return self.exports.finish(request['token'],request['revision'],request['png'],request['qa'],current)
