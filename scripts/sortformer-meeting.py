"""Sortformer turns and activity + multitalker on a whole meeting, one output per threshold.

Usage: sortformer-meeting.py AUDIO OUT_DIR MODEL REVISION [--thresholds hard,0.3]. `hard` uses turns only.
Writes OUT_DIR/<threshold>/transcript.json (new directories only). Runs on CUDA when visible.
"""
import argparse, json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from faster_whisper.audio import decode_audio
from huggingface_hub import snapshot_download
from nemo.collections.asr.models import SortformerEncLabelModel

from server_stt.diarization import DiarizationTurn
from server_stt.multitalker import recognize


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("audio", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("model")
    p.add_argument("revision")
    p.add_argument("--thresholds", default="hard,0.3")
    a = p.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    audio = decode_audio(str(a.audio), sampling_rate=16000)
    assert not isinstance(audio, tuple)
    snapshot = Path(snapshot_download(a.model, revision=a.revision))
    nemo_file = next(snapshot.glob("*.nemo"))
    diarizer: Any = SortformerEncLabelModel.restore_from(str(nemo_file), map_location=torch.device(device), strict=False)
    diarizer.eval()
    segments, tensors = diarizer.diarize(audio=[str(a.audio)], batch_size=1, include_tensor_outputs=True)
    turns = []
    for item in segments[0]:
        start, end, speaker = item.split()
        turns.append(DiarizationTurn(float(start), float(end), f"SPEAKER_{int(speaker.rsplit('_', 1)[1]) + 1:02d}"))
    activity = tensors[0].detach().cpu().numpy().astype(np.float32).squeeze(0)
    frame_s = len(audio) / 16000 / activity.shape[0]
    for name in a.thresholds.split(","):
        threshold = None if name == "hard" else float(name)
        result = recognize(audio, turns, threads=8, activity=None if threshold is None else activity,
                           activity_frame_s=None if threshold is None else frame_s,
                           activity_threshold=threshold, device=device)
        assert not isinstance(result, str), result
        transcript = {
            "source": str(a.audio),
            "model": f"{result.model}+{a.model}@{a.revision}",
            "language": result.language,
            "language_probability": None,
            "duration_s": len(audio) / 16000,
            "turns": [{"start_s": t.start_s, "end_s": t.end_s, "speaker": t.speaker} for t in turns],
            "words": [{"start_s": w.start_s, "end_s": w.end_s, "text": w.text, "speaker": w.speaker, "probability": w.probability} for w in result.words],
        }
        output = a.out / name / "transcript.json"
        output.parent.mkdir(parents=True, exist_ok=False)
        output.write_text(json.dumps(transcript, indent=2) + "\n")


if __name__ == "__main__":
    main()
