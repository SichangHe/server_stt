"""Exercise DiariZen plumbing without downloading or running neural models."""

import os
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

import numpy as np

from server_stt import cli, multitalker
from server_stt.diarization import DiarizationTurn

ROOT = Path(__file__).resolve().parents[1]


# 🧑 "tests in server_stt for bugs already hit on the DiariZen path"
class DiarizenRegressionTests(unittest.TestCase):
    def test_cli_ignores_logs_and_hands_turns_to_recognizer(self):
        """Decode a WAV and pass real subprocess output through the CLI."""
        output = """Loading model
INFO loading checkpoint
0.0 0.75 00
Downloading weights: 100% complete
0.5 1.0 01
"""
        check_output = subprocess.check_output

        def diarizen_output(command, **kwargs):
            self.assertEqual(
                command,
                [
                    str(ROOT / "envs/diarizen/.venv/bin/python"),
                    str(ROOT / "scripts/diarizen-turns.py"),
                    str(audio_path),
                ],
            )
            return check_output(
                [sys.executable, "-c", f"print({output!r})"], timeout=10, **kwargs
            )

        def recognize_chunk(model, audio, offset_s, turns, since_s, *activity):
            self.assertEqual(
                [(t.start_s, t.end_s, t.speaker) for t in turns],
                [(0.0, 0.75, "SPEAKER_00"), (0.5, 1.0, "SPEAKER_01")],
            )
            self.assertEqual((audio.size, offset_s, since_s), (16000, 0, 0))
            self.assertEqual(activity, (None, None, None))
            return [multitalker.SpeakerWord(0.6, 0.8, "hello", "SPEAKER_01")]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio_path = root / "input.wav"
            with wave.open(str(audio_path), "wb") as audio:
                audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
                audio.writeframes(bytes(32000))
            destination = root / "output"
            with (
                patch.object(
                    sys,
                    "argv",
                    ["server-stt", str(audio_path), "--output", str(destination)],
                ),
                patch("subprocess.check_output", side_effect=diarizen_output),
                patch.object(multitalker, "load", return_value=object()),
                patch.object(
                    multitalker, "recognize_chunk", side_effect=recognize_chunk
                ) as chunk,
            ):
                self.assertEqual(cli.main(), 0)
            chunk.assert_called_once()
            transcript = cli.Transcript.model_validate_json(
                (destination / "transcript.json").read_text()
            )
            self.assertEqual(len(transcript.turns), 2)
            self.assertEqual(transcript.words[0].speaker, "SPEAKER_01")
            self.assertEqual(
                (destination / "transcript.txt").read_text(),
                "[0.60s] SPEAKER_01: hello\n",
            )

    def test_chunk_duration_rejected_before_model_loading(self):
        audio = np.zeros(16000, dtype=np.float32)
        turns = [DiarizationTurn(0, 1, "SPEAKER_00")]
        with patch.object(multitalker, "load") as load:
            for chunk_s in (90.0001, 91, 0, -1, float("inf"), float("nan")):
                with self.subTest(chunk_s=chunk_s):
                    self.assertEqual(
                        multitalker.recognize(audio, turns, chunk_s=chunk_s),
                        "Multitalker chunk duration must be in (0, 90] seconds",
                    )
            load.assert_not_called()

    def test_default_chunks_stop_at_90_seconds_and_keep_remainder(self):
        audio = np.zeros(181 * 16000, dtype=np.float32)
        turns = [DiarizationTurn(0, 181, "SPEAKER_00")]
        with (
            patch.object(multitalker, "load", return_value=object()),
            patch.object(multitalker, "recognize_chunk", return_value=[]) as chunk,
        ):
            result = multitalker.recognize(audio, turns)
        self.assertIsInstance(result, multitalker.MultitalkerResult)
        self.assertEqual(
            [
                (call.args[1].size, call.args[2], call.args[4])
                for call in chunk.call_args_list
            ],
            [(90 * 16000, 0, 0), (90 * 16000, 90, 90), (16000, 180, 180)],
        )
        self.assertTrue(all(call.args[3] is turns for call in chunk.call_args_list))

    def test_setup_rerun_keeps_existing_source(self):
        """Run the shell script twice with local stand-ins for network tools."""
        with tempfile.TemporaryDirectory(prefix="diarizen setup ") as directory:
            root = Path(directory)
            scripts = root / "scripts"
            scripts.mkdir()
            script = scripts / "setup-diarizen.sh"
            script.write_bytes((ROOT / "scripts/setup-diarizen.sh").read_bytes())
            tools = root / "bin"
            tools.mkdir()
            tool_source = f"""#!{sys.executable}
import os
import sys
from pathlib import Path
with open(os.environ['TEST_COMMAND_LOG'], 'a') as log:
    log.write(repr([Path(sys.argv[0]).name, *sys.argv[1:]]) + '\\n')
if sys.argv[1] == 'venv':
    Path(sys.argv[-1]).mkdir(parents=True, exist_ok=True)
if 'clone' in sys.argv:
    source = Path(sys.argv[2]) / 'src'
    source.mkdir()
    (source / '.git').mkdir()
"""
            for name in ("uv", "git"):
                tool = tools / name
                tool.write_text(tool_source)
                tool.chmod(0o755)
            log = root / "commands.log"
            env = dict(
                os.environ,
                PATH=f"{tools}:{os.environ['PATH']}",
                TEST_COMMAND_LOG=str(log),
            )
            marker = root / "envs/diarizen/src/preserve-me"
            for run in range(2):
                subprocess.run(
                    ["sh", str(script)],
                    env=env,
                    check=True,
                    capture_output=True,
                    timeout=10,
                )
                if run == 0:
                    marker.write_text("existing checkout")
            commands = log.read_text().splitlines()
            self.assertEqual(sum("'clone'" in line for line in commands), 1)
            self.assertEqual(
                sum("'checkout', '844f555'" in line for line in commands), 2
            )
            self.assertEqual(sum("'pip', 'install'" in line for line in commands), 10)
            self.assertEqual(marker.read_text(), "existing checkout")


if __name__ == "__main__":
    unittest.main()
