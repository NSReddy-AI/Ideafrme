import errno
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
from style_recipes.store import Store,WORKSPACE
from style_recipes.canonical import StyleError,ref,digest
from style_recipes.manual import recipe
from .helpers import *

WORKER=WORKSPACE/'r1_tests/fault_worker.py'
FAILURES=[]


def worker(mode,s,config):
    return subprocess.run([sys.executable,'-B',str(WORKER),mode,str(s.path),json.dumps(config)],
                          cwd=WORKSPACE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)


class PersistenceTests(unittest.TestCase):
    def setUp(self):self.s=new_store()

    def test_real_local_filesystem_primitives(self):
        report=self.s.qualify()
        self.assertTrue(report['F_FULLFSYNC'] and report['directory_fsync'] and report['exclusive_lock_probe'])
        self.assertFalse(report['power_loss_certified'])
        (WORKSPACE/'.runtime/r1/filesystem-qualification.json').write_text(json.dumps(report,indent=2)+'\n')

    def test_normal_stale_generation(self):
        _,r=manual(self.s);old=self.s.read().head
        save(self.s,[recipe(ACTOR,NOW,'second')])
        with self.assertRaises(StyleError):self.s.commit([recipe(ACTOR,NOW,'stale')],old,ACTOR,NOW)

    def test_actual_process_lock_contention(self):
        manual(self.s);before=self.s.read().head
        with self.s.opened(write=True):
            p=worker('race',self.s,dict(expected=before))
            self.assertEqual(p.returncode,2,p.stderr)
            self.assertIn(b'busy',p.stdout)
        self.assertEqual(self.s.read().head,before)
        p=worker('race',self.s,dict(expected=before));self.assertEqual(p.returncode,0,p.stdout+p.stderr)

    def test_two_actual_writer_processes_only_one_commits(self):
        manual(self.s);head=self.s.read().head;cmd=[sys.executable,'-B',str(WORKER),'race',str(self.s.path),json.dumps(dict(expected=head))]
        a=subprocess.Popen(cmd,cwd=WORKSPACE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        b=subprocess.Popen(cmd,cwd=WORKSPACE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        ao=a.communicate(timeout=20);bo=b.communicate(timeout=20)
        self.assertEqual(sorted([a.returncode,b.returncode]),[0,2],(ao,bo))
        self.assertEqual(len(self.s.read().commits),2)

    def test_os_sandbox_denies_network_and_writes_outside_r1(self):
        p=worker('isolation',self.s,{})
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        evidence=json.loads(p.stdout)
        self.assertTrue(evidence['network_denied'] and evidence['write_outside_r1_denied'])
        (WORKSPACE/'.runtime/r1/isolation-results.json').write_text(json.dumps(evidence,indent=2)+'\n')

    def test_sigkill_releases_lock_and_stale_metadata_is_not_authority(self):
        manual(self.s);old=self.s.read().head
        (self.s.path/'.writer.info.json').write_text('{"pid":1,"age":"stale"}')
        p=subprocess.Popen([sys.executable,'-B',str(WORKER),'signal-kill',str(self.s.path),'{}'],
                           cwd=WORKSPACE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            deadline=time.monotonic()+10
            while not (self.s.path/'staging'/'kill-ready').exists() and p.poll() is None and time.monotonic()<deadline:
                time.sleep(0.01)
            self.assertTrue((self.s.path/'staging'/'kill-ready').exists())
            p.kill();p.communicate(timeout=10);self.assertEqual(p.returncode,-9)
            self.assertEqual(self.s.read().head,old)
            save(self.s,[recipe(ACTOR,NOW,'Writer after crash')])
        finally:
            if p.poll() is None:p.kill();p.communicate(timeout=10)

    def test_unsupported_filesystem_and_sync_fail_closed(self):
        s=Store(self.s.path)
        with patch('style_recipes.store.sys.platform','unsupported'):
            with self.assertRaises(StyleError):s.qualify()
        self.assertFalse(s.qualified)
        with patch('style_recipes.store.os.fsync',side_effect=OSError(errno.EINVAL,'unsupported sync')):
            with self.assertRaises(OSError):s.qualify()
        self.assertFalse(s.qualified)

    def test_real_os_file_size_failure_keeps_head(self):
        manual(self.s);head=self.s.read().head
        result=worker('file-limit',self.s,{})
        self.assertEqual(result.returncode,2,result.stderr)
        self.assertIn(b'not published',result.stdout)
        self.assertEqual(self.s.read().head,head)

    def stages(self,recovery=False):
        s=new_store();manual(s)
        stages=[]
        if recovery:
            save(s,[recipe(ACTOR,NOW,'second commit establishes PREVIOUS')])
            (s.path/'HEAD').write_bytes(b'broken')
            gen=s.recovery_generation();s.fault=stages.append;s.recover(gen,ACTOR,NOW,confirmed=True)
        else:
            s.fault=stages.append;save(s,[recipe(ACTOR,NOW,'stage enumeration')])
        return list(dict.fromkeys(stages))

    def test_crash_every_normal_commit_stage(self):
        for stage in self.stages():
            with self.subTest(stage=stage):
                s=new_store();f,r=approved(s);old=s.read().head
                before=(s.path/'records'/(digest(r)+'.json')).read_bytes()
                proc=worker('crash',s,dict(stage=stage))
                self.assertEqual(proc.returncode,77,proc.stdout+proc.stderr)
                after=s.read()
                self.assertIn(len(after.commits),(len(self.s.read().commits)+4,len(self.s.read().commits)+5))
                self.assertTrue(after.eligible(ref(r),NOW)['eligible'])
                self.assertEqual((s.path/'records'/(digest(r)+'.json')).read_bytes(),before)
                FAILURES.append(dict(mode='process-crash',stage=stage,exit=77,head_unchanged=after.head==old,
                                     historical_recipe_unchanged=True,valid_reopen=True))

    def test_disk_full_every_normal_commit_stage(self):
        for stage in self.stages():
            with self.subTest(stage=stage):
                s=new_store();manual(s);old=s.read().head
                def fault(actual):
                    if actual==stage:raise OSError(errno.ENOSPC,'injected disk full')
                s.fault=fault
                with self.assertRaises(StyleError) as raised:save(s,[recipe(ACTOR,NOW,'disk full')])
                result=s.read()
                if result.head!=old:self.assertIn('UNCERTAIN',str(raised.exception))
                FAILURES.append(dict(mode='ENOSPC-injection',stage=stage,head_unchanged=result.head==old,
                                     valid_reopen=True,message=str(raised.exception)))

    def test_partial_record_crash_never_publishes(self):
        manual(self.s);old=self.s.read().head
        p=worker('crash',self.s,dict(stage='after:record:write',occurrence=1))
        self.assertEqual(p.returncode,77,p.stderr)
        self.assertEqual(self.s.read().head,old)

    def test_crash_every_recovery_stage_preserves_previous(self):
        for stage in self.stages(recovery=True):
            with self.subTest(stage=stage):
                s=new_store();approved(s);save(s,[recipe(ACTOR,NOW,'extra draft')])
                (s.path/'HEAD').write_bytes(b'broken');prev=(s.path/'PREVIOUS').read_bytes()
                gen=s.recovery_generation();proc=worker('recovery-crash',s,dict(stage=stage,generation=gen))
                self.assertEqual(proc.returncode,77,proc.stdout+proc.stderr)
                self.assertEqual((s.path/'PREVIOUS').read_bytes(),prev)
                if (s.path/'HEAD').read_bytes()!=b'broken':
                    snap=s.read();self.assertGreater(snap.recovery_sequence,0)
                else:
                    with self.assertRaises(StyleError):s.read()
                FAILURES.append(dict(mode='recovery-process-crash',stage=stage,exit=77,previous_unchanged=True))

    def test_disk_full_recovery_preserves_previous(self):
        for stage in self.stages(recovery=True):
            with self.subTest(stage=stage):
                s=new_store();manual(s);save(s,[recipe(ACTOR,NOW,'extra')])
                (s.path/'HEAD').write_bytes(b'broken');prev=(s.path/'PREVIOUS').read_bytes();gen=s.recovery_generation()
                def fault(actual):
                    if actual==stage:raise OSError(errno.ENOSPC,'injected recovery disk full')
                s.fault=fault
                with self.assertRaises(StyleError):s.recover(gen,ACTOR,NOW,confirmed=True)
                self.assertEqual((s.path/'PREVIOUS').read_bytes(),prev)
                FAILURES.append(dict(mode='recovery-ENOSPC-injection',stage=stage,previous_unchanged=True))

    def test_recovery_exact_consent_and_invalidated_approvals(self):
        f,r=approved(self.s);save(self.s,[recipe(ACTOR,NOW,'extra')])
        (self.s.path/'HEAD').write_bytes(b'broken');prev=(self.s.path/'PREVIOUS').read_bytes();gen=self.s.recovery_generation()
        with self.assertRaises(StyleError):self.s.recover(gen,ACTOR,NOW)
        self.s.recover(gen,ACTOR,NOW,confirmed=True)
        self.assertEqual((self.s.path/'PREVIOUS').read_bytes(),prev)
        self.assertFalse(self.s.read().eligible(ref(r),NOW)['eligible'])
        with self.assertRaises(StyleError):self.s.recover(gen,ACTOR,NOW,confirmed=True)
        approve(self.s,f);approve(self.s,r)
        self.assertTrue(self.s.read().eligible(ref(r),NOW)['eligible'])
        evidence=[json.loads(p.read_text()) for p in (self.s.path/'quarantine').iterdir()]
        self.assertEqual(evidence[0]['head_hex'],b'broken'.hex())

    def test_corrupt_payload_and_missing_head_never_auto_repair(self):
        f,r=manual(self.s);file=self.s.path/'records'/(digest(r)+'.json');file.write_bytes(b'corrupt')
        with self.assertRaises(StyleError):self.s.read()
        self.assertEqual(file.read_bytes(),b'corrupt')
        (self.s.path/'HEAD').unlink()
        with self.assertRaises(StyleError):self.s.read()

    def test_link_device_and_boundary_guards(self):
        with self.assertRaises(StyleError):Store(WORKSPACE/'creative_core')
        with self.assertRaises(StyleError):Store(WORKSPACE.parent/'other')
        manual(self.s);file=self.s.path/'HEAD';target=self.s.path/'unchanged-head';file.rename(target);file.symlink_to(target)
        with self.assertRaises((StyleError,OSError)):self.s.read()
        file.unlink();os.link(target,file)
        with self.assertRaises(StyleError):self.s.read()
        file.unlink();os.mkfifo(file)
        with self.assertRaises(StyleError):self.s.read()

    def test_store_is_not_reinitialized(self):
        with self.assertRaises(StyleError):Store.create(self.s.path)

    @classmethod
    def tearDownClass(cls):
        (WORKSPACE/'.runtime/r1/persistence-fault-results.json').write_text(json.dumps(FAILURES,indent=2)+'\n')
