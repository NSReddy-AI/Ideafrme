"""FFmpeg video export with approval gating and safe subprocess invocation."""
from pathlib import Path
import subprocess
from .models import Project

PROFILES = {
    'reels': (1080, 1920, 30),
    'shorts': (1080, 1920, 30),
    'facebook': (1080, 1920, 30),
}

def render(project: Project, input_video: Path, output_video: Path, profile: str = 'reels') -> Path:
    project.validate()
    if not project.can_export():
        raise PermissionError('Human approval gates are incomplete; export blocked')
    if profile not in PROFILES:
        raise ValueError('Unknown export profile')
    if not input_video.is_file():
        raise FileNotFoundError(input_video)
    if input_video.resolve() == output_video.resolve():
        raise ValueError('Input and output must differ')
    width, height, fps = PROFILES[profile]
    output_video.parent.mkdir(parents=True, exist_ok=True)
    filtergraph = f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}'
    subprocess.run(['ffmpeg', '-hide_banner', '-nostdin', '-y', '-i', str(input_video),
        '-vf', filtergraph, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20',
        '-preset', 'medium', '-c:a', 'aac', '-movflags', '+faststart', str(output_video)],
        check=True)
    return output_video
