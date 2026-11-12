#!/bin/bash
# Fetches the two open fonts the graphics use (Anton, Six Caps - SIL Open Font Licence) into engine/fonts, then runs the test.
set -e
cd "$(dirname "$0")/.."
F=engine/fonts; mkdir -p "$F/licences"
get() { [ -s "$2" ] || curl -fsSL -o "$2" "https://raw.githubusercontent.com/google/fonts/main/$1"; ls -l "$2" | awk '{print $5, $9}'; }
get ofl/anton/Anton-Regular.ttf "$F/Anton-Regular.ttf"
get ofl/anton/OFL.txt "$F/licences/Anton-OFL.txt"
get ofl/sixcaps/SixCaps.ttf "$F/SixCaps.ttf"
get ofl/sixcaps/OFL.txt "$F/licences/SixCaps-OFL.txt"
"$HOME/.venvs/reelstudio/bin/python" tests/test_motion.py
