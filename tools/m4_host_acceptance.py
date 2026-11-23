#!/usr/bin/env python3
"""Run remaining M4 host checks in a disposable copy; never release or install anything."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import zipfile


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--historical', type=Path, default=Path('/Users/Nadish/projects/AI Video Editor./Reel Studio_dev'))
    ap.add_argument('--media', type=Path, default=Path('/Users/Nadish/projects/AI Video Editor./raw footage/What jagan said.mov'))
    ap.add_argument('--reports', type=Path, default=Path.home() / 'projects/agents/m4-host-reports')
    ap.add_argument('--preflight-only', action='store_true', help='check host permissions without staging or running tests')
    args = ap.parse_args()
    source = args.source.resolve()
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    reports = args.reports.expanduser().resolve()
    # Output belongs outside every source/protected project.
    protected = [source, args.historical.resolve(), args.historical.resolve().parent / 'Reel Studio']
    for p in protected:
        if reports == p or reports.is_relative_to(p):
            ap.error('--reports must be outside source, historical and production roots')
    reports.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix=stamp + '_', dir=reports))
    results = []
    workspace = None
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1',
               TRANSFORMERS_OFFLINE='1', HF_DATASETS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1')
    for key in ['ANTHROPIC_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEY', 'ELEVENLABS_API_KEY', 'HF_TOKEN', 'HUGGING_FACE_HUB_TOKEN']:
        env.pop(key, None)
    py = Path.home() / '.venvs/reelstudio/bin/python'
    before = {}

    def record(name, status, detail=''):
        results.append(dict(name=name, status=status, detail=detail))
        (out / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2))
        print(f'[{status}] {name}: {str(detail)[:180]}', flush=True)

    def run(name, cmd, timeout=1200, offline=False, cwd=None):
        log = out / (name + '.log')
        command = (['/usr/bin/sandbox-exec', '-f', str(workspace / 'tools/m6_offline.sb')] if offline else []) + [str(c) for c in cmd]
        start = time.time()
        with log.open('w') as f:
            f.write(json.dumps({'command': command, 'cwd': str(cwd or workspace)}, ensure_ascii=False) + '\n')
            f.flush()
            proc = subprocess.Popen(command, cwd=cwd or workspace or source, env=env,
                                    stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = proc.wait(timeout=timeout)
            except (subprocess.TimeoutExpired, KeyboardInterrupt):
                import signal
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                if sys.exc_info()[0] is KeyboardInterrupt:
                    raise
                record(name, 'FAIL', 'Timed out; process group stopped')
                return False
        record(name, 'PASS' if code == 0 else 'FAIL', dict(exit=code, seconds=round(time.time()-start, 1), log=log.name))
        return code == 0

    def fingerprints():
        paths = [source / 'projects/2026-11-03_reel_002_development/project.json',
                 args.historical / 'projects/2026-11-03_reel_002_development/project.json',
                 args.historical / 'projects/2026-11-03_reel_002_development/build/words.json']
        production = args.historical.parent / 'Reel Studio'
        if production.is_dir():
            paths += [p for p in production.rglob('*') if p.is_file() and not p.is_symlink()]
        return {str(p): sha(p) for p in paths if p.is_file()}

    try:
        if not py.is_file():
            raise RuntimeError('reelstudio Python is missing; no installation will be attempted')
        # No real model work until monitoring and process inventory are available.
        probe = subprocess.run(['/usr/bin/top', '-l', '1', '-pid', str(os.getpid()), '-stats', 'mem'], capture_output=True, text=True)
        if probe.returncode or not re.search(r'\bMEM\b', probe.stdout):
            raise RuntimeError('macOS memory monitoring unavailable; use a normal VS Code Terminal')
        rss = subprocess.run(['/bin/ps', '-o', 'rss=', '-p', str(os.getpid())], capture_output=True, text=True)
        if rss.returncode or not rss.stdout.strip().isdigit() or int(rss.stdout.strip()) <= 0:
            raise RuntimeError('Narration RSS watchdog cannot read process memory')
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0))
        sandbox = subprocess.run(['/usr/bin/sandbox-exec', '-f', str(source / 'tools/m6_offline.sb'), '/usr/bin/true'], capture_output=True, text=True)
        if sandbox.returncode:
            raise RuntimeError('Offline sandbox unavailable: ' + sandbox.stderr.strip())
        ps = subprocess.run(['/bin/ps', '-axo', 'pid=,command='], capture_output=True, text=True)
        if ps.returncode:
            raise RuntimeError('Cannot inspect running jobs')
        active = [line for line in ps.stdout.splitlines() if re.search(r'engine/(asr_worker|tts_worker|narrate|adapter|build|transcribe)\.py|app/server\.py', line)]
        if active:
            raise RuntimeError('Close existing Reel Studio apps/jobs before running: ' + '\n'.join(active))
        for lock in [source / '.heavy_model.lock', source / 'engine/.heavy_model.lock', args.historical.parent / 'Reel Studio/.heavy_model.lock']:
            if lock.exists():
                raise RuntimeError(f'Existing lock needs owner inspection; this runner will not remove it: {lock}')
        record('host_preflight', 'PASS', 'memory monitor, loopback, sandbox and process checks available')
        if args.preflight_only:
            return 0
        if not args.media.is_file():
            raise RuntimeError(f'ASR reference media missing: {args.media}')
        before = fingerprints()
        (out / 'protected_before.json').write_text(json.dumps(before, indent=2))
        workspace = Path(tempfile.mkdtemp(prefix='m4-host-workspace-'))
        tracked = subprocess.check_output(['git', '-C', str(source), 'ls-files', '-z']).decode().split('\0')
        for name in filter(None, tracked):
            p = source / name
            if p.is_file():
                dest = workspace / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, dest)
        if not (workspace / 'tests/fixtures/m4_planner/words.json').is_file():
            raise RuntimeError('Use the isolated release-gates checkout containing the fixture fix')
        legacy = {}
        for name in ['common.py.preB1','te_numbers.py.preB1','frame.py.preB1','slides.py.preB1','qa.py.preB1','voice.py.preB1','adapter.py.preB1','rs.py.preB1','mix.py.preB1','narrate.py.preB12','narration_script.py.preB12','tts.json.preB12']:
            src = args.historical / 'engine' / name
            if not src.is_file():
                raise RuntimeError(f'Legacy comparison input missing: {src}')
            legacy[name] = sha(src)
            shutil.copyfile(src, workspace / 'engine' / name)
        fixture = workspace / 'tests/fixtures/m4_planner/words.json'
        if sha(fixture) != '94fb7a37a64a82cbd6156715ce5034738ffdf1bdb883d9a692ba22dd8e7ccd7e':
            raise RuntimeError('Planner fixture checksum mismatch')
        target = workspace / 'projects/2026-11-03_reel_002_development/build/words.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(fixture, target)
        (out / 'source.json').write_text(json.dumps(dict(source=str(source), commit=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD']).decode().strip(), workspace=str(workspace), legacy_sha256=legacy), indent=2))
        env['RS_HEAVY_LOCK'] = str(workspace / '.heavy_model.lock')
        record('staging', 'PASS', 'fresh disposable copy; historical comparison files hash-recorded')
        denial_code = "import socket,sys\ns=socket.socket();s.settimeout(3)\ntry:s.connect(('1.1.1.1',443))\nexcept PermissionError:sys.exit(0)\nexcept OSError:sys.exit(2)\nelse:sys.exit(1)"
        offline_ok = run('offline_external_block', [py,'-B','-c',denial_code], offline=True, timeout=20)
        if not offline_ok:
            raise RuntimeError('Cannot establish external-connection enforcement; no model tests started')
        run('planner_safety', [py,'-B','tests/test_plan_checks.py'], offline=True)
        narration_ok = run('narration_contracts', [py,'-B','tests/test_narration.py','--out',out/'narration'], offline=True)
        run('app_routes', [py,'-B','tests/test_m6_creative.py'], offline=True)
        run('asr_harness', [py,'-B','tests/test_transcribe_harness.py'], offline=True)
        if not narration_ok:
            record('real_models', 'BLOCKED', 'Narration contracts must pass before heavy model work')
            return 1
        # Require local cached planner, never pull a model or start a service.
        import urllib.request
        try:
            tags = json.load(urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=5))
            loaded = json.load(urllib.request.urlopen('http://127.0.0.1:11434/api/ps', timeout=5))
            if loaded.get('models'):
                raise RuntimeError('Ollama currently holds models; stop other model use and unload them before rerunning')
            names = {m['name'] for m in tags.get('models', [])}
            if 'qwen3:14b' not in names:
                raise RuntimeError('Cached qwen3:14b missing; no download will be attempted')
        except Exception as exc:
            raise RuntimeError('Local Ollama readiness: ' + str(exc))
        run('real_asr', [py,'-B','tests/test_transcribe.py','--source',args.media.resolve(),'--out',out/'asr'], offline=True, timeout=1800)
        run('real_planner', [py,'-B','tests/test_planner.py','--models','qwen3:14b','--provider','local'], offline=True, timeout=1800)
        # Synthetic approval is confined to this unique throwaway test project.
        name = 'zz_host_narration'
        d = workspace / 'projects' / name
        (d/'inputs').mkdir(parents=True)
        (d/'build').mkdir()
        base = json.loads((workspace/'projects/2026-11-03_reel_002_development/project.json').read_text())
        base.update(status='test',history=[],approved=False,video=None,title_person=None,title_bg=None,style='documentary',narration='ai',narrator='lalitha',narrator_style='news',narration_speed=1.15)
        (d/'project.json').write_text(json.dumps(base,ensure_ascii=False,indent=2))
        script = d/'inputs/script.txt'
        script.write_text('అక్కచెల్లెమ్మలకు 31 లక్షల ఇళ్ల పట్టాలు ఇచ్చారు.\nసొంతింటి కల నెరవేర్చేలా 17,000 జగనన్న కాలనీలు.\nపేదవాడి ఆరోగ్యానికి 10,000 విలేజ్ క్లినిక్‌లు.\n')
        setup = run('test_script_prepare',[py,'-B','engine/rs.py','script',str(d),str(script)],offline=True)
        setup = setup and run('test_script_approve',[py,'-B','engine/rs.py','script-approve',str(d),'--checked'],offline=True)
        voiced = setup and run('real_narration',[py,'-B','engine/adapter.py','narrate',str(d)],offline=True,timeout=2400)
        if voiced:
            timeline = json.loads((d/'build/narration_timeline.json').read_text())
            (out/'real_narration_timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2))
            if (d/'build/narration.wav').exists():
                shutil.copyfile(d/'build/narration.wav',out/'listen_narration.wav')
            listening = json.loads((d/'build/narration_check.json').read_text())
            peak = timeline.get('memory', {}).get('peak_rss_gb')
            metrics_ok = (timeline.get('memory', {}).get('model_loaded') is True
                          and isinstance(peak, (int,float)) and 0 < peak < 8
                          and listening.get('cer_total', 1) < 0.1)
            record('real_narration_metrics', 'PASS' if metrics_ok else 'FAIL',
                   dict(peak_gb=peak, cer=listening.get('cer_total')))
            cached = run('narration_cache',[py,'-B','engine/adapter.py','narrate',str(d)],offline=True,timeout=1200)
            if cached:
                cache_timeline = json.loads((d/'build/narration_timeline.json').read_text())
                generated = cache_timeline.get('generated', {})
                record('cache_reuse', 'PASS' if generated.get('spoken') == 0 and generated.get('cached') == 3 else 'FAIL', generated)
            built = run('fresh_build',[py,'-B','engine/adapter.py','build',str(d)],offline=True)
            if built:
                run('fresh_three_platform_render',[py,'-B','engine/adapter.py','render',str(d),'--all-platforms'],offline=True,timeout=1800)
        # Retain small structured reports; large generated videos stay in the disposable workspace.
        for folder in [workspace/'tests/out', d/'build', workspace/'exports']:
            if folder.exists():
                for file in folder.rglob('*'):
                    if file.is_file() and file.suffix in ['.json','.md','.txt'] and file.stat().st_size < 5_000_000:
                        dest = out/'details'/file.relative_to(workspace)
                        dest.parent.mkdir(parents=True,exist_ok=True)
                        shutil.copyfile(file,dest)
        return 0 if all(v['status']=='PASS' for v in results) else 1
    except KeyboardInterrupt:
        record('interrupted','BLOCKED','Stopped by user; report preserved')
        return 1
    except Exception as exc:
        record('runner','BLOCKED',f'{type(exc).__name__}: {exc}')
        return 1
    finally:
        if before:
            try:
                after = fingerprints()
                (out/'protected_after.json').write_text(json.dumps(after,indent=2))
                record('protected_files_unchanged','PASS' if before==after else 'FAIL','SHA-256 comparison of watched files')
            except Exception as exc:
                record('protection_verification','FAIL',str(exc))
        blocked = any(v['status']!='PASS' for v in results)
        text = '# M4 host acceptance report\n\nCheck verdict: '+('INCOMPLETE / REVIEW REQUIRED' if blocked else 'EXECUTED CHECKS PASSED')+'\n\n'
        text += 'This runner does not qualify the entire release, grade narration/hooks, verify every package licence, adapt the historical 31-check M4 harness, rehearse recovery, or authorise Gate D.\n\n'
        text += '| Check | Status | Detail |\n|---|---|---|\n'
        for v in results:
            detail=str(v['detail']).replace('|','/').replace('\n',' ')
            text+=f"| {v['name']} | {v['status']} | {detail} |\n"
        text += f'\nDisposable workspace retained for diagnosis: `{workspace}`. No production or main release performed.\n'
        (out/'REPORT.md').write_text(text)
        manifest = {str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='SHA256SUMS'}
        (out/'SHA256SUMS').write_text(''.join(f'{v}  {k}\n' for k,v in sorted(manifest.items())))
        archive = out.with_suffix('.zip')
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for p in out.rglob('*'):
                if p.is_file():z.write(p,p.relative_to(out))
        print(f'\nREPORT: {out / "REPORT.md"}\nSEND BACK: {archive}',flush=True)
        if any(v['status'] != 'PASS' for v in results):
            return 1


if __name__ == '__main__':
    raise SystemExit(main())
