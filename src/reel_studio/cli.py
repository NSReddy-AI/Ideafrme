"""Local command-line entry point. No network calls."""
import argparse
from pathlib import Path
from .models import Project
from .planning import propose_scenes
from .render import render

def main() -> None:
    parser = argparse.ArgumentParser(prog='ideaframe')
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init', help='Create a local project from UTF-8 script')
    init.add_argument('script', type=Path)
    init.add_argument('manifest', type=Path)
    init.add_argument('--title', required=True)
    init.add_argument('--language', choices=['en', 'te'], default='en')
    plan = sub.add_parser('plan', help='Propose unapproved timed scenes')
    plan.add_argument('manifest', type=Path)
    export = sub.add_parser('export', help='Export only an approved project')
    export.add_argument('manifest', type=Path)
    export.add_argument('input_video', type=Path)
    export.add_argument('output_video', type=Path)
    export.add_argument('--profile', choices=['reels', 'shorts', 'facebook'], default='reels')
    args = parser.parse_args()
    if args.command == 'init':
        Project(title=args.title, language=args.language,
            source_text=args.script.read_text(encoding='utf-8')).save(args.manifest)
        print(f'Created {args.manifest}')
    elif args.command == 'plan':
        project = propose_scenes(Project.load(args.manifest))
        project.save(args.manifest)
        print(f'Proposed {len(project.scenes)} unapproved scenes in {args.manifest}')
    elif args.command == 'export':
        print(render(Project.load(args.manifest), args.input_video,
            args.output_video, args.profile))

if __name__ == '__main__':
    main()
