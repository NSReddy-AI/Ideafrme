"""Check acceptance exit status using controlled transcripts, without loading models."""
import contextlib
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = json.loads((ROOT / "tests/asr_reference_what_jagan_said.json").read_text())


class AcceptanceVerdict(unittest.TestCase):
    def run_case(self, bad_telugu=False, failed_english=False):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "result"

            def fake_run(command, **kwargs):
                if command[0] == "ffmpeg":
                    return subprocess.CompletedProcess(command, 0)
                lang = command[command.index("--lang") + 1]
                if lang == "en" and failed_english:
                    return subprocess.CompletedProcess(command, 1, "", "controlled English failure")
                words = [dict(word, review=[]) for word in REFERENCE["words"]]
                if bad_telugu and lang == "te":
                    words = [dict(w="unrelated", s=0, e=1, review=[])]
                target = Path(command[command.index("--out") + 1])
                target.write_text(json.dumps(dict(words=words, model="controlled-test", review_count=0)))
                return subprocess.CompletedProcess(command, 0, "controlled transcript", "")

            args = ["test_transcribe.py", "--source", str(Path(tmp) / "source.mov"), "--out", str(out)]
            with patch.object(sys, "argv", args), patch("subprocess.run", side_effect=fake_run), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as exit_result:
                    runpy.run_path(str(ROOT / "tests/test_transcribe.py"), run_name="__main__")
            return exit_result.exception.code, json.loads((out / "transcribe_report.json").read_text())

    def test_matching_transcript_succeeds(self):
        code, report = self.run_case()
        self.assertEqual(code, 0)
        self.assertEqual(report["te"]["cer"], 0)

    def test_inaccurate_telugu_fails(self):
        code, _ = self.run_case(bad_telugu=True)
        self.assertEqual(code, 1)

    def test_failed_english_fails(self):
        code, _ = self.run_case(failed_english=True)
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
