# Setup (once, about 15 minutes)

You already have Homebrew, Node.js, Python 3.12, FFmpeg, Whisper and HyperFrames from the earlier setup.

## 1. Install Claude Code
In Terminal:
```
export PATH="/opt/homebrew/bin:$PATH" && npm install -g @anthropic-ai/claude-code
```
Then `cd` into this folder and run `claude`. Sign in with your Claude account (Pro or higher).

## 2. Let Claude finish the setup
Paste this into Claude Code:
> Read CLAUDE.md and SETUP.md. Install the Python packages Reel Studio needs
> (pip install --user pillow numpy scipy opencv-python onnxruntime), make sure Homebrew's node and
> ~/.local/bin are on PATH in ~/.zshrc, run `python3 engine/rs.py check` and fix anything missing.

## 3. Optional: AI voiceover (for reels without a speaker)
Create an ElevenLabs account, copy your API key, and add it to your shell (not to any file in this folder):
```
echo 'export ELEVENLABS_API_KEY="paste-key-here"' >> ~/.zshrc
```
Without a key, those reels are made as text + music.

## 4. Fill in your channels
`channels/tech_ai_tools` and `channels/editing_freelance` still need: your handle, logo, and (optional) end card.
Tell Claude: "set up my tech_ai_tools channel: handle @…, logo is ~/Desktop/logo.png".

## Face tracking (optional, off by default)
Reel Studio's Python needs MediaPipe (Apache-2.0) and two model files (Google, Apache-2.0):
```
~/.venvs/reelstudio/bin/pip install --only-binary=:all: "mediapipe==1.2.2"
cd "Reel Studio/engine/models"
curl -fL -o blaze_face_short_range.tflite https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite
curl -fL -o pose_landmarker_lite.task https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task
```
Turn it on per project with `"face_tracking": true` in project.json. Never install Ultralytics/YOLO (AGPL).

## Speech to text (Telugu and English)
Runs in its own Python so Reel Studio's Python stays small (all free and unrestricted: transformers Apache-2.0, torch BSD-3,
faster-whisper/whisper.cpp MIT, Telugu model Apache-2.0):
```
/opt/homebrew/bin/python3.12 -m venv ~/.venvs/rs_asr
~/.venvs/rs_asr/bin/pip install --only-binary=:all: transformers torch
brew install whisper-cpp
mkdir -p ~/.cache/rs_asr && curl -fL -o ~/.cache/rs_asr/ggml-large-v3-turbo.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin
```
The Telugu model (vasista22/whisper-telugu-large-v2, about 3 GB) downloads on first use. Settings: engine/asr.json.
