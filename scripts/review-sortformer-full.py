"""Run the pinned Sortformer activity probe on whole ES2004a."""

import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from faster_whisper.audio import decode_audio
from huggingface_hub import snapshot_download
from nemo.collections.asr.models import SortformerEncLabelModel

from server_stt.diarization import DiarizationTurn
from server_stt.multitalker import recognize

SOURCE = Path("/ssd1/sichangheagent/private-artifacts/server-stt/full-ES2004a/ES2004a.mp3")
MODEL = "nvidia/diar_streaming_sortformer_4spk-v2.1"
REVISION = "cd03eee90fbec18297ac31b8c21546e596b7f71c"


def main() -> None:
    audio = decode_audio(str(SOURCE), sampling_rate=16000)
    snapshot = Path(snapshot_download(MODEL, revision=REVISION))
    diarizer: Any = SortformerEncLabelModel.restore_from(str(snapshot / "diar_streaming_sortformer_4spk-v2.1.nemo"), map_location=torch.device("cpu"), strict=False)
    assert not isinstance(audio, tuple)
    diarizer.eval()
    segments, tensors = diarizer.diarize(audio=[str(SOURCE)], batch_size=1, include_tensor_outputs=True)
    turns = []
    for item in segments[0]:
        start, end, speaker = item.split()
        turns.append(DiarizationTurn(float(start), float(end), f"SPEAKER_{int(speaker.rsplit('_', 1)[1]) + 1:02d}"))
    activity = tensors[0].numpy().astype(np.float32).squeeze(0)
    result = recognize(audio, turns, threads=8, chunk_s=120, activity=activity, activity_frame_s=len(audio) / 16000 / activity.shape[0], activity_threshold=0.3)
    assert not isinstance(result, str), result
    transcript = {
        "source": str(SOURCE),
        "model": f"{result.model}+{MODEL}@{REVISION}",
        "language": result.language,
        "language_probability": None,
        "duration_s": len(audio) / 16000,
        "turns": [{"start_s": t.start_s, "end_s": t.end_s, "speaker": t.speaker} for t in turns],
        "words": [{"start_s": w.start_s, "end_s": w.end_s, "text": w.text, "speaker": w.speaker, "probability": w.probability} for w in result.words],
    }
    output = Path("output/file-full-sortformer21-activity03/transcript.json")
    output.unlink(missing_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(transcript, indent=2) + "\n")


if __name__ == "__main__":
    main()
