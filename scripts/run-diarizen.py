"""Recognize an audio file using precomputed DiariZen turns."""
import json
import re
import sys
from pathlib import Path

from faster_whisper.audio import decode_audio

from server_stt.diarization import DiarizationTurn
from server_stt.multitalker import recognize


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: run-diarizen.py AUDIO TURNS OUTPUT")
    audio_path, turns_path, output_path = map(Path, sys.argv[1:])
    audio = decode_audio(str(audio_path), sampling_rate=16000)
    turns = []
    for line in turns_path.read_text().splitlines():
        fields = line.split()
        if len(fields) == 3 and re.fullmatch(r"[0-9.eE+-]+", fields[0]):
            turns.append(DiarizationTurn(float(fields[0]), float(fields[1]), f"SPEAKER_{int(fields[2]):02d}"))
    result = recognize(audio, turns, threads=8, chunk_s=90)
    if isinstance(result, str):
        raise RuntimeError(result)
    transcript = {"source": str(audio_path), "model": result.model, "language": result.language,
                  "language_probability": None, "duration_s": len(audio) / 16000,
                  "turns": [t.__dict__ for t in turns],
                  "words": [w.__dict__ for w in result.words]}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(transcript, indent=2) + "\n")


if __name__ == "__main__":
    main()
