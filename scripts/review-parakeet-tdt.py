"""Run the pinned Parakeet TDT crop probe and write a scored transcript."""

import json
from pathlib import Path
from typing import Any

import torch
from faster_whisper.audio import decode_audio
from huggingface_hub import snapshot_download
from nemo.collections.asr.models import ASRModel

from server_stt.cli import Turn, speaker_for
from server_stt.diarization import diarize

SOURCE = Path("/ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/EN2002a-300-390.wav")
MODEL = "nvidia/parakeet-tdt-0.6b-v3"
REVISION = "541d1f99c6b0c3cd0b11a95167540bb8edefd82b"


def main() -> None:
    audio = decode_audio(str(SOURCE), sampling_rate=16000)
    assert not isinstance(audio, tuple)
    native = diarize(
        audio,
        Path("models/Nemotron-3-Diarization.q8_0.gguf"),
        Path("models/nemo-speech-0.2.0-linux-x86_64-cpu"),
    )
    assert not isinstance(native, str), native
    turns = [Turn(start_s=t.start_s, end_s=t.end_s, speaker=t.speaker) for t in native.turns]
    snapshot = Path(snapshot_download(MODEL, revision=REVISION))
    model: Any = ASRModel.restore_from(str(snapshot / "parakeet-tdt-0.6b-v3.nemo"), map_location=torch.device("cpu"))
    model.eval()
    hypothesis = model.transcribe([str(SOURCE)], timestamps=True, return_hypotheses=True)[0]
    words = [
        {
            "start_s": float(item["start"]),
            "end_s": float(item["end"]),
            "text": item["word"],
            "speaker": speaker_for(float(item["start"]), float(item["end"]), turns),
            "probability": None,
        }
        for item in hypothesis.timestamp["word"]
    ]
    transcript = {
        "source": str(SOURCE),
        "model": f"{MODEL}@{REVISION}",
        "language": "English",
        "language_probability": None,
        "duration_s": len(audio) / 16000,
        "turns": [t.model_dump() for t in turns],
        "words": words,
    }
    output = Path("output/file-en2002a-parakeet-tdt/transcript.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(transcript, indent=2) + "\n")


if __name__ == "__main__":
    main()
