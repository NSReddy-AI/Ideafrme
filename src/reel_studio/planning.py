"""Deterministic offline baseline planner; local model adapter to follow."""
import re
from .models import Project, Scene

def propose_scenes(project: Project, seconds_per_scene: float = 5.0) -> Project:
    if seconds_per_scene <= 0:
        raise ValueError('seconds_per_scene must be positive')
    segments = [s.strip() for s in re.split(r'(?<=[.!?।])\s+|\n+', project.source_text) if s.strip()]
    project.scenes = [Scene(text=s, start_seconds=i * seconds_per_scene,
        end_seconds=(i + 1) * seconds_per_scene) for i, s in enumerate(segments)]
    project.claims_approved = False
    project.quotes_approved = False
    project.timing_approved = False
    project.export_approved = False
    project.validate()
    return project
