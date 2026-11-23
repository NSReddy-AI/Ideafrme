#!/usr/bin/env python3
"""Isolated current-code Gate C. No downloads, shared installs or production writes.

Run with the application Python. --models explicitly enables real cached TTS and
local Qwen. Without it, dependent checks are BLOCKED, never simulated passes.
The 31 IDs preserve historical coverage; extra checks have X-prefixed IDs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
IDS = [f'A{i}' for i in range(1, 20)] + [f'B{i}' for i in range(1, 7)] + [f'C{i}' for i in range(1, 7)]
SCRIPT = 'అక్కచెల్లెమ్మలకు 31 లక్షల ఇళ్ల పట్టాలు.\nగ్రామ స్వరాజ్యం కోసం 15,000 సచివాలయాలు.\n17,805 కోట్లతో ప్రభుత్వ బడులు నాడు నేడు.'


def sha(p):
    return hashlib.file_digest(Path(p).open('rb'), 'sha256').hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--models', action='store_true')
    ap.add_argument('--historical', type=Path, help='Read-only legacy parity inputs; never executed in place')
    a = ap.parse_args()
    out = a.out.resolve()
    if out.exists() or out.is_relative_to(ROOT):
        ap.error('--out must be a NEW directory outside the source checkout')
    out.mkdir(parents=True)
    results, proc = {}, None
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1',
               TRANSFORMERS_OFFLINE='1', HF_DATASETS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1')
    for k in list(env):
        if k.endswith('_API_KEY') or k in ('HF_TOKEN', 'HUGGING_FACE_HUB_TOKEN'):
            env.pop(k)

    def record(key, name, ok=None, detail='', status=None):
        results[key] = dict(name=name, status=status or ('PASS' if ok else 'FAIL'), detail=detail)
        (out / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2))
        try:
            print(key, results[key]['status'], name, flush=True)
        except BrokenPipeError:
            pass  # A disconnected caller must not prevent evidence or cleanup.

    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    # Include this runner and pending reviewed edits, but never untracked project data.
    tracked += ['tools/m4_gate_c.py', 'tests/test_protected_preview.py', 'tests/test_tts_monitor_race.py']
    source_hashes = {n: sha(ROOT / n) for n in sorted(set(filter(None, tracked))) if (ROOT / n).is_file()}
    (out / 'source.json').write_text(json.dumps(dict(commit=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(), files=source_hashes), indent=2))
    with tempfile.TemporaryDirectory(prefix='ideaframe-m4-gatec-') as tmp:
        work = Path(tmp)
        for n in source_hashes:
            dest = work / n
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / n, dest)
        (work / 'exports').mkdir(exist_ok=True)
        env['RS_HEAVY_LOCK'] = str(work / '.heavy_model.lock')
        sandbox = ['/usr/bin/sandbox-exec', '-f', str(work / 'tools/m6_offline.sb')]

        def run(name, cmd, timeout=300):
            with (out / f'{name}.log').open('w') as log:
                log.write(json.dumps(dict(command=sandbox + cmd, cwd=str(work))) + '\n'); log.flush()
                p = subprocess.Popen(sandbox + cmd, cwd=work, env=env, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    return p.wait(timeout)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL); p.wait()
                    return 124

        def call(method, path, body=None):
            req = urllib.request.Request(base + path, method=method,
                data=json.dumps(body).encode() if body is not None else None,
                headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as e:
                return dict(_error=e.code, detail=e.read().decode())

        def job(name, action, **kw):
            j = call('POST', f'/api/projects/{name}/jobs', dict(action=action, **kw))
            deadline = time.monotonic() + 900
            while j.get('status') in ('queued', 'running'):
                if time.monotonic() > deadline:
                    call('POST', f"/api/jobs/{j['id']}/cancel")
                    raise TimeoutError(f'{action} exceeded 900 seconds')
                time.sleep(.3)
                j = call('GET', f"/api/jobs/{j['id']}")
            j['errors'] = [e.get('code') for e in j.get('events', []) if e.get('event') == 'error']
            (out / f"job-{name}-{action}-{time.time_ns()}.json").write_text(json.dumps(j, ensure_ascii=False, indent=2))
            return j

        try:
            deny = 'import socket\ns=socket.socket();s.settimeout(2)\ntry:s.connect(("1.1.1.1",443))\nexcept PermissionError:pass\nelse:raise SystemExit(1)'
            rc = run('offline', [sys.executable, '-B', '-c', deny])
            record('X1', 'OS-enforced external network denial', rc == 0)
            if rc: raise RuntimeError('Offline sandbox unavailable')
            # Legacy files are copied individually, identified by hash, never modified in place.
            if a.historical:
                expected = json.loads((ROOT / 'tests/acceptance/m4_current_20261122/execution.json').read_text())
                legacy = {}
                for n in ('common.py.preB1', 'te_numbers.py.preB1', 'frame.py.preB1', 'slides.py.preB1',
                          'qa.py.preB1', 'voice.py.preB1', 'adapter.py.preB1', 'rs.py.preB1', 'mix.py.preB1',
                          'narrate.py.preB12', 'narration_script.py.preB12', 'tts.json.preB12'):
                    src = a.historical / 'engine' / n
                    legacy[n] = sha(src)
                    if legacy[n] != expected['legacy_sha256'][n]:
                        raise RuntimeError(f'Historical parity input changed: {n}')
                    shutil.copyfile(src, work / 'engine' / n)
                (out / 'legacy-inputs.json').write_text(json.dumps(legacy, indent=2))
            suites = ['test_protected_preview', 'test_tts_monitor_race', 'test_caption_fixes', 'test_plan_checks',
                      'test_transcribe_harness', 'test_approved_content', 'test_engine_jobs',
                      'test_brand_bridge', 'test_milestone2', 'test_m6_creative']
            if a.historical: suites += ['test_narration']
            for name in suites:
                cmd = [sys.executable, '-B', f'tests/{name}.py']
                if name == 'test_narration': cmd += ['--out', str(out / 'narration')]
                rc = run(name, cmd, 600)
                record(name, name, rc == 0, f'exit={rc}; {name}.log')
            with socket.socket() as s:
                s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]
            base = f'http://127.0.0.1:{port}'
            env['RS_PORT'] = str(port)
            server_log = (out / 'server.log').open('w')
            proc = subprocess.Popen(sandbox + [sys.executable, '-B', 'app/server.py'], cwd=work,
                                    env=env, stdout=server_log, stderr=subprocess.STDOUT, start_new_session=True)
            for _ in range(100):
                try: call('GET', '/api/catalog'); break
                except OSError: time.sleep(.2)
            else: raise RuntimeError('isolated server did not start')
            baseline = '2026-11-03_reel_002_development'
            baseline_before = {str(p.relative_to(work)): sha(p) for p in (work / 'projects' / baseline).rglob('*') if p.is_file()}
            record('X2', 'Protected preview refuses writes', call('GET', f'/api/projects/{baseline}/source_frame').get('_error') == 403)
            record('X3', 'Private source files not served', call('GET', '/files/engine/tts.json').get('_error') == 404)
            n = call('POST', '/api/projects', dict(brand='jagan_for_andhra', platform='instagram', style='news_speech', slug='zz_gatec_narration'))['name']
            record('A1', 'Project created through app', n.endswith('zz_gatec_narration'))
            url = f'/api/projects/{n}'
            v = call('POST', url + '/narration', dict(mode='ai', voice='lalitha', style='news', speed=1.15))
            p = v['project']
            record('A2', 'Lalitha / News / 1.15 saved', p['narrator'] == 'lalitha' and p['narrator_style'] == 'news' and p['narration_speed'] == 1.15)
            v = call('POST', url + '/script', dict(text=SCRIPT)); lines = v['script']['lines']
            record('A3', 'Exact script and Telugu spoken numbers', [l['text'] for l in lines] == SCRIPT.splitlines() and all(not any(c.isdigit() for c in l['say']) for l in lines))
            # Use an explicitly ambiguous decimal; the historical lines no longer
            # necessarily trigger a review flag under current number handling.
            call('POST', url + '/script', dict(text=SCRIPT + '\n2.5 లక్షల పరీక్ష.'))
            record('A4', 'Unchecked flagged script refused', '_error' in call('POST', url + '/script/approve', dict(checked=False)))
            call('POST', url + '/script', dict(text=SCRIPT))
            v = call('POST', url + '/script/approve', dict(checked=True)); h = v['script']['approved_hash']
            record('A5', 'Test script approved with fingerprint', v['script']['approved'] and bool(h))
            j = job(n, 'render'); record('A6', 'Render refused before narration/edit', j['status'] == 'failed' and bool(j['errors']))
            title = dict(line1='పరీక్ష', line2='రెండు', line3='మూడు', tag_top='పరీక్ష', tag_bottom='పరీక్ష', headline=['పరీక్ష', 'పరీక్ష'])
            v = call('PUT', url + '/title', title)
            record('A7', 'Title words saved exactly', all(v['project']['hook'][k] == title[k] for k in ('line1', 'line2', 'line3')))
            models_ready = a.models
            if models_ready:
                ps = subprocess.check_output(['/bin/ps', '-axo', 'pid=,command='], text=True)
                active = [l for l in ps.splitlines() if any(x in l for x in ('engine/tts_worker.py', 'engine/asr_worker.py'))]
                if active: raise RuntimeError('Other model jobs active; refusing heavy execution')
                with urllib.request.urlopen('http://127.0.0.1:11434/api/ps', timeout=5) as r:
                    if json.load(r).get('models'): raise RuntimeError('Ollama has loaded models; do not displace another workload')
                with urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=5) as r:
                    if 'qwen3:14b' not in {m['name'] for m in json.load(r)['models']}: raise RuntimeError('Cached Qwen3 missing')
                j = job(n, 'narrate'); r = j.get('result') or {}; mem = r.get('memory') or {}
                record('A8', 'Real offline AI narration loaded model', j['status'] == 'done' and mem.get('model_loaded'), r)
                record('A9', 'Measured TTS peak below 8 GB', 0 < (mem.get('peak_rss_gb') or 0) < 8, mem)
                record('A10', 'ASR listening check CER below 0.1', r.get('cer_total', 1) < .1, r.get('cer_total'))
                b = work / 'projects' / n / 'build'
                if j['status'] == 'done':
                    tl = json.loads((b / 'narration_timeline.json').read_text()); nw = json.loads((b / 'narration_words.json').read_text())
                    config = json.loads((work / 'engine/tts.json').read_text())
                    record('A11', '1.15 speed, 10 ms fade, restart off', tl['speed'] == 1.15 and tl.get('edge_fade_ms') == 10 and config['memory']['restart_every'] == 0 and len(tl['generated']['batches']) == 1, tl)
                    record('A12', 'Captions exactly approved words', ''.join(w['w'] for w in nw).replace(' ', '') == ''.join(SCRIPT.split()))
                    shutil.copyfile(b / 'narration.wav', out / 'listen-narration.wav')
                    j = job(n, 'build'); r = j.get('result') or {}
                    record('A13', 'Approved three-slide edit built', j['status'] == 'done' and (r.get('layout') or {}).get('slides') == 3)
                    j = job(n, 'render'); outputs = (j.get('result') or {}).get('outputs', [])
                    record('A14', 'Three-platform rendering', j['status'] == 'done' and sorted(o['platform'] for o in outputs) == ['facebook', 'instagram', 'youtube'])
                    record('A15', 'QA passes every export', len(outputs) == 3 and all(o['qa_passed'] for o in outputs))
                    qa = [json.loads(Path(o['qa_report']).read_text()) for o in outputs]
                    record('A16', 'Disclosure, loudness and format QA', len(qa) == 3 and all(abs(q['loudness_lufs'] + 14) <= 1 and any(c['name'] == 'ai_disclosure' and c['passed'] for c in q['checks']) for q in qa), qa)
                    record('A17', 'AI-label flags on all outputs', len(outputs) == 3 and all(o.get('ai_label_required') for o in outputs))
                    # Worker marks done before writing post copy: wait for that observable completion.
                    posts = []
                    for _ in range(50):
                        v = call('GET', url); posts = [o['post'] for g in v['exports'] for o in g['outputs'] if o['post']]
                        if len(posts) == 3: break
                        time.sleep(.2)
                    record('A18', 'Three draft posts with AI note', len(posts) == 3 and all('AI' in (work / p).read_text() for p in posts))
                    record('A19', 'Outputs confined to disposable exports', len(outputs) == 3 and all(Path(o['path']).resolve().is_relative_to(work / 'exports') for o in outputs))
            v = call('POST', url + '/script', dict(text=SCRIPT.replace('సచివాలయాలు', 'సచివాలయాలు!')))
            record('B1', 'Script edit withdraws approval', not v['script']['approved'])
            j = job(n, 'render'); record('B2', 'Changed script blocks render', j['status'] == 'failed')
            call('POST', url + '/script', dict(text=SCRIPT))
            v = call('POST', url + '/script/approve', dict(checked=True))
            if models_ready: record('B3', 'Reapproval restores fingerprint and audio', v['script']['approved_hash'] == h and v.get('narration_ready') is True)
            record('B4', 'Baseline jobs forbidden', call('POST', f'/api/projects/{baseline}/jobs', dict(action='build')).get('_error') == 403)
            e = call('POST', '/api/projects', dict(brand='tech_ai_tools', platform='youtube', style='listicle', slug='zz_gatec_english'))['name']
            record('B5', 'English AI voice forbidden', call('POST', f'/api/projects/{e}/narration', dict(mode='ai', voice='prakash', style='news')).get('_error') == 400)
            j = job(e, 'render'); record('B6', 'Missing edit blocks render', j['status'] == 'failed' and 'EDIT_MISSING' in j['errors'])
            if models_ready:
                s = call('POST', '/api/projects', dict(brand='jagan_for_andhra', platform='instagram', style='news_speech', slug='zz_gatec_speaker'))['name']
                d = work / 'projects' / s
                words = json.loads((work / 'tests/fixtures/m4_planner/words.json').read_text())
                duration = max(w['e'] for w in words) + 1
                rc = run('synthetic-video', ['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=640x640:r=30', '-f', 'lavfi', '-i', 'sine=frequency=220:sample_rate=48000', '-t', str(duration), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(d / 'inputs/source.mp4')])
                if rc: raise RuntimeError('Synthetic source generation failed')
                call('PATCH', f'/api/projects/{s}', dict(video='inputs/source.mp4'))
                (d / 'build/transcript.json').write_text(json.dumps(dict(words=words), ensure_ascii=False))
                j = job(s, 'plan'); r = j.get('result') or {}
                record('C1', 'Real local Qwen drafts hooks and cards', j['status'] == 'done' and len(r.get('options') or {}) >= 3 and bool(r.get('cards')), r)
                j = job(s, 'build'); record('C2', 'Unapproved plan blocks build', 'PLAN_NOT_APPROVED' in j['errors'])
                j = job(s, 'approve', choice='A', checked=True); record('C3', 'Synthetic plan approval', j['status'] == 'done')
                v = call('PUT', f'/api/projects/{s}/captions', dict(fixes={'0': words[0]['w'] + '_gatec'}))
                record('C4', 'Caption fix preserves original, revokes both approvals', v['plan']['approved'] is False and v['project']['approved'] is False and v['words'][0]['w_asr'] == words[0]['w'])
                j = job(s, 'build'); record('C5', 'Caption edit blocks build until reapproved', 'PLAN_NOT_APPROVED' in j['errors'])
                job(s, 'approve', choice='A', checked=True); j = job(s, 'build')
                record('C6', 'Reapproved edit contains corrected caption', j['status'] == 'done' and any(w['w'].endswith('_gatec') for w in json.loads((d / 'build/words.json').read_text())))
            baseline_after = {str(p.relative_to(work)): sha(p) for p in (work / 'projects' / baseline).rglob('*') if p.is_file()}
            record('X4', 'Disposable baseline unchanged', baseline_before == baseline_after)
            call('PATCH', url, dict(archived=True)); call('PATCH', url, dict(archived=False))
            record('X5', 'Archive/restore retains project', call('GET', url)['project'].get('archived') is False)
            # Restart only our own server; project approval must survive disk roundtrip.
            proc.terminate(); proc.wait(15)
            proc = subprocess.Popen(sandbox + [sys.executable, '-B', 'app/server.py'], cwd=work, env=env, stdout=server_log, stderr=subprocess.STDOUT, start_new_session=True)
            for _ in range(100):
                try:
                    v = call('GET', url); break
                except OSError: time.sleep(.2)
            record('X6', 'Restart recovers script fingerprint', v['script']['approved_hash'] == h)
        except Exception as exc:
            record('runner', 'Execution interrupted', detail=f'{type(exc).__name__}: {exc}', status='BLOCKED')
        finally:
            if proc and proc.poll() is None:
                # Stop child job groups before server shutdown; no global process killing.
                try:
                    for j in call('GET', '/api/jobs'):
                        if j['status'] in ('running', 'queued'): call('POST', f"/api/jobs/{j['id']}/cancel")
                except Exception: pass
                proc.terminate()
                try: proc.wait(15)
                except subprocess.TimeoutExpired: os.killpg(proc.pid, signal.SIGKILL); proc.wait()
            for key in IDS:
                if key not in results: record(key, 'Historical Gate C check not executed', status='BLOCKED', detail='Required model run or preceding workflow unavailable')
            for p in (work / 'exports').glob('*_qa.json'):
                shutil.copyfile(p, out / p.name)
            record('X7', 'Source files unchanged by execution', all(sha(ROOT / n) == h for n, h in source_hashes.items()))
    (out / 'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(out.iterdir()) if p.is_file() and p.name != 'SHA256SUMS'))
    return 0 if all(r['status'] == 'PASS' for r in results.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
