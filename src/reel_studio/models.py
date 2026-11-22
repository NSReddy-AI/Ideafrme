"""Versioned local project manifest and human approval state."""
from dataclasses import dataclass, field, asdict
from pathlib import Path
import json

@dataclass
class Scene:
    text: str
    start_seconds: float
    end_seconds: float
    approved: bool = False

@dataclass
class Project:
    title: str
    language: str
    source_text: str
    scenes: list[Scene] = field(default_factory=list)
    claims_approved: bool = False
    quotes_approved: bool = False
    timing_approved: bool = False
    export_approved: bool = False
    schema_version: int = 1

    def validate(self) -> None:
        if self.language not in {'en', 'te'}:
            raise ValueError('Language must be en or te')
        if not self.title.strip() or not self.source_text.strip():
            raise ValueError('Title and source text are required')
        for scene in self.scenes:
            if scene.start_seconds < 0 or scene.end_seconds <= scene.start_seconds:
                raise ValueError('Invalid scene timing')
        if any(a.end_seconds > b.start_seconds for a, b in zip(self.scenes, self.scenes[1:])):
            raise ValueError('Scenes must not overlap')

    def can_export(self) -> bool:
        return bool(self.scenes) and all((self.claims_approved, self.quotes_approved,
            self.timing_approved, self.export_approved)) and all(s.approved for s in self.scenes)

    def save(self, path: Path) -> None:
        self.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding='utf-8')

    @classmethod
    def load(cls, path: Path) -> 'Project':
        data = json.loads(path.read_text(encoding='utf-8'))
        if data.get('schema_version') != 1:
            raise ValueError('Unsupported manifest schema version')
        data['scenes'] = [Scene(**s) for s in data.get('scenes', [])]
        project = cls(**data)
        project.validate()
        return project
