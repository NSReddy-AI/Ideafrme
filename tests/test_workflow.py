from pathlib import Path
import pytest
from reel_studio.models import Project, Scene
from reel_studio.planning import propose_scenes
from reel_studio.render import render

def test_telugu_roundtrip(tmp_path: Path):
    p = Project('తెలుగు', 'te', 'నమస్కారం. ఇది పరీక్ష.')
    p.save(tmp_path / 'project.json')
    assert Project.load(tmp_path / 'project.json').source_text == p.source_text

def test_planning_requires_approval():
    p = propose_scenes(Project('Test', 'en', 'Hello world. Another scene.'))
    assert len(p.scenes) == 2
    assert not p.can_export()
    assert all(not s.approved for s in p.scenes)

def test_export_blocked_before_ffmpeg(tmp_path: Path):
    p = propose_scenes(Project('Test', 'en', 'Test scene.'))
    with pytest.raises(PermissionError):
        render(p, tmp_path / 'missing.mp4', tmp_path / 'out.mp4')

def test_export_requires_every_gate():
    p = Project('Test', 'en', 'Hello', [Scene('Hello', 0, 5, approved=True)],
        claims_approved=True, quotes_approved=True, timing_approved=True)
    assert not p.can_export()
    p.export_approved = True
    assert p.can_export()

def test_rejects_overlapping_scenes():
    p = Project('Test', 'en', 'Hello', [Scene('a', 0, 5), Scene('b', 4, 7)])
    with pytest.raises(ValueError):
        p.validate()

def test_replanning_resets_approvals():
    p = Project('Test', 'en', 'Hello', [Scene('Hello', 0, 5, True)], True, True, True, True)
    propose_scenes(p)
    assert not p.can_export()
