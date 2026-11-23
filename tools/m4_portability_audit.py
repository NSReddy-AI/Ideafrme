#!/usr/bin/env python3
"""Offline dependency, SBOM and restore evidence; writes only a new report and temp dirs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); out = a.out.resolve()
    if out.exists() or out.is_relative_to(ROOT): ap.error('Use a new external report directory')
    out.mkdir(parents=True)
    results = {}

    def run(key, cmd, cwd=ROOT, timeout=300):
        p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PIP_NO_INDEX='1', PIP_DISABLE_PIP_VERSION_CHECK='1'))
        (out / f'{key}.log').write_text(json.dumps(dict(command=cmd, cwd=str(cwd))) + '\n' + p.stdout + p.stderr)
        results[key] = dict(status='PASS' if p.returncode == 0 else 'FAIL', exit=p.returncode)
        return p

    def digest(p):
        with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

    bom = json.loads((ROOT / 'docs/SBOM.json').read_text())
    norm = lambda n: re.sub(r'[-_.]+', '-', n.lower())
    known = {(norm(c['name']), c.get('version')) for c in bom['components']}
    scan = '''import json,importlib.metadata as m
print(json.dumps([dict(name=d.metadata['Name'],version=d.version,license=d.metadata.get('License-Expression') or d.metadata.get('License'),classifiers=d.metadata.get_all('Classifier') or [],requires=d.requires or []) for d in m.distributions()]))'''
    environments = {}
    for name in ('reelstudio', 'rs_asr', 'rs_tts'):
        py = str(Path.home() / '.venvs' / name / 'bin/python')
        p = run(name + '-metadata', [py, '-I', '-c', scan])
        packages = json.loads(p.stdout)
        environments[name] = dict(packages=packages, absent_from_sbom=[p for p in packages if (norm(p['name']), p['version']) not in known])
        run(name + '-pip-check', [py, '-m', 'pip', 'check'])
        frozen = run(name + '-freeze', [py, '-m', 'pip', 'freeze', '--all']).stdout
        (out / f'{name}-requirements.txt').write_text(frozen)
    lock = json.loads((ROOT / 'app/web/package-lock.json').read_text())
    npm = [dict(name=p.get('name') or n.split('node_modules/')[-1], version=p.get('version'), license=p.get('license'))
           for n, p in lock['packages'].items() if n]
    (out / 'dependency-reconciliation.json').write_text(json.dumps(dict(python=environments, npm=npm,
        npm_absent_from_sbom=[p for p in npm if (norm(p['name']), p['version']) not in known]), indent=2))
    run('ffmpeg-build', ['ffmpeg', '-buildconf'])
    run('ffmpeg-license', ['ffmpeg', '-L'])
    run('hardcoded-paths', ['rg', '-n', '/Users/|/opt/homebrew|~/.venvs|~/.cache', 'app', 'engine', 'tools', 'Start Reel Studio.command'])
    # rg exit 0 means findings, not a portability pass.
    results['hardcoded-paths']['status'] = 'REVIEW'
    with tempfile.TemporaryDirectory(prefix='ideaframe-m4-portability-') as tmp:
        tmp = Path(tmp); fresh = tmp / 'checkout'
        run('fresh-checkout', ['git', 'clone', '--no-hardlinks', '--no-checkout', str(ROOT), str(fresh)])
        run('checkout-source', ['git', 'checkout', '--detach', 'HEAD'], fresh)
        source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=fresh).decode().strip()
        results['source'] = dict(commit=source, status='PASS', note='Fresh clone, same Mac; not independent clean-Mac certification')
        envpath = tmp / 'venv'
        run('fresh-venv', [sys.executable, '-m', 'venv', str(envpath)])
        # No indexes, no shared site-packages, no changes to the shared environment.
        wheels = tmp / 'empty-wheelhouse'; wheels.mkdir()
        req = out / 'reelstudio-requirements.txt'
        p = run('fresh-python-install', [str(envpath / 'bin/python'), '-m', 'pip', 'install', '--no-index', '--find-links', str(wheels), '-r', str(req)])
        if p.returncode: results['fresh-python-install']['status'] = 'BLOCKED'
        run('web-offline-install', ['npm', 'ci', '--offline', '--ignore-scripts', '--no-audit', '--no-fund'], fresh / 'app/web')
        if results['web-offline-install']['exit'] == 0:
            run('web-build', ['npm', 'run', 'build'], fresh / 'app/web')
            run('web-tests', ['node', '--test'] + [str(p) for p in sorted((fresh / 'tests/web').glob('test_*.mjs'))], fresh)
        # Restore only tracked source. Never archive model caches or original project directories.
        archive = tmp / 'source.tar'
        run('source-archive', ['git', 'archive', '--format=tar', '-o', str(archive), 'HEAD'], fresh)
        restore = tmp / 'restore'; restore.mkdir()
        run('source-restore', ['tar', '-xf', str(archive), '-C', str(restore)])
        names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=fresh).decode().split('\0')
        mismatch = [n for n in names if n and (fresh / n).is_file() and digest(fresh / n) != digest(restore / n)]
        results['restore-parity'] = dict(status='PASS' if not mismatch else 'FAIL', mismatches=mismatch,
            note='Tracked source only; not model/environment disaster recovery')
    results['independent-clean-mac'] = dict(status='BLOCKED', detail='No independent clean Mac available')
    results['redistribution'] = dict(status='BLOCKED', detail='Candidate closure, model terms, complete notices and GPL compliance need review; not legal approval')
    (out / 'results.json').write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    (out / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.name}\n' for p in sorted(out.iterdir()) if p.is_file() and p.name != 'SHA256SUMS'))


if __name__ == '__main__': main()
