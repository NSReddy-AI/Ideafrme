#!/bin/bash
# Milestone 2 acceptance checkpoint (dev copy only). Uses Reel Studio's own Python.
cd "$(dirname "$0")"
PY="$HOME/.venvs/reelstudio/bin/python"
P=2026-11-03_reel_002_development
echo "== 1. environment";       "$PY" engine/adapter.py check | "$PY" -c "import sys,json;r=json.load(sys.stdin);print('check ok' if r['ok'] else 'CHECK FAILED', '| telugu layout:', r['telugu_layout'])"
echo "== 2. self-test";         "$PY" tests/test_milestone2.py | tail -1
cp "projects/$P/project.json" /tmp/rs_pj_before.json
echo "== 3. baseline (instagram, adapter)"; START=$(date +%s)
"$PY" engine/adapter.py render "$P" --platform instagram --baseline tests/baseline_reel_002.json > exports/_checkpoint_baseline.jsonl
tail -1 exports/_checkpoint_baseline.jsonl | "$PY" -c "import sys,json;d=json.load(sys.stdin);print('render ok:',d['ok'],'| QA passed:',d['qa_passed'])"
echo "   time: $(( $(date +%s) - START )) s"
grep '"event": "qa"' exports/_checkpoint_baseline.jsonl | "$PY" -c "
import sys,json
for l in sys.stdin:
    r=json.load(open(json.loads(l)['report']))
    for c in r['checks']: print('  ', 'PASS' if c['passed'] else 'FAIL', c['name'], c['value'])
    print('   frames', r['frames'], '| size', r['file_size'], '| loudness', r['loudness_lufs'], '| peak', r['true_peak_db'], '| warnings', len(r['warnings']))"
echo "== 4. all platforms (one storyboard, three exports)"; START=$(date +%s)
"$PY" engine/adapter.py render "$P" --all-platforms > exports/_checkpoint_all.jsonl
tail -1 exports/_checkpoint_all.jsonl | "$PY" -c "
import sys,json;d=json.load(sys.stdin);print('render ok:',d['ok'],'| QA passed:',d['qa_passed'])
for o in d['outputs']: print('  ', o['platform'], 'QA', 'PASS' if o['qa_passed'] else 'FAIL', o['path'].split('/')[-1])"
echo "   time: $(( $(date +%s) - START )) s"
echo "== 5. project.json unchanged (apart from history)"
"$PY" -c "
import json;a=json.load(open('/tmp/rs_pj_before.json'));b=json.load(open('projects/$P/project.json'));a.pop('history');b.pop('history');print('unchanged' if a==b else 'CHANGED!')"
echo "CHECKPOINT DONE"
