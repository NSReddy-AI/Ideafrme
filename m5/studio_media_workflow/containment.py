"""Fail-closed processing admission. No decoder, worker, sandbox shortcut or launch API."""
import importlib.util,platform,shutil
from pathlib import Path
from studio_manual_ui.service import UIError
LIMITS={'aggregate_memory_bytes':1073741824,'aggregate_scratch_bytes':134217728,'worker_seconds':15,'job_seconds':60,'concurrent_jobs':1,'worker_processes':4,'compute_threads':1,'result_bytes':1048576}
MISSING=(
 'No qualified hard aggregate job-memory mechanism, including descendants/shared and attributable host buffers.',
 'No qualified confinement/quota over every writable sink, including memory-backed and open-deleted storage.',
 'No qualified process/thread admission and whole-job cancellation boundary against a compromised worker.',
 'No qualified combined filesystem/network isolation and crash-safe supervisor lifecycle.',
)
def status():
 return {'qualified':False,'live_placement_enabled':False,'supported_new_formats':[],
         'candidate_formats_disabled':['png','svg','ttf','otf'],'limits':dict(LIMITS),'missing':list(MISSING),
         'local_inventory':{'system':platform.system(),'release':platform.release(),'machine':platform.machine(),
          'linux_cgroup_present':Path('/sys/fs/cgroup/cgroup.controllers').exists(),
          'tools':{n:shutil.which(n) for n in ('sandbox-exec','swift','clang','qemu-system-aarch64','limactl','colima','docker','wasmtime','bwrap','prlimit')},
          'python_candidates':{n:importlib.util.find_spec(n) is not None for n in ('PIL','png','wasmtime')}},
         'evidence':'Read-only inventory and existing decisions; no enforcement experiment or media decoding.',
         'note':'Installed tools, signatures, polling/RSS, per-file limits or process groups cannot be substituted for the missing guarantees.'}
def require_qualified():
 # Deliberately no user-editable qualification flag, JSON attestation or forced-enable option.
 raise UIError('media-boundary-unqualified','Live processing/placement disabled. '+ ' '.join(MISSING),409)
