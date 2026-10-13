"""CPU target-speaker recognition conditioned on estimated overlapping turns."""

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from server_stt.diarization import DiarizationTurn

MODEL = "nvidia/multitalker-parakeet-streaming-0.6b-v1"
REVISION = "8749fc71fd6e2d88ef230159bbf2aea69b524ee1"
CHECKPOINT = "multitalker-parakeet-streaming-0.6b-v1.nemo"


@dataclass
class SpeakerWord:
    start_s: float
    end_s: float
    text: str
    speaker: str
    probability: float | None = None


@dataclass
class MultitalkerResult:
    words: list[SpeakerWord]
    language: str = "English"
    model: str = f"{MODEL}@{REVISION}"


# 🧑 "speakers + accurate transcripts"
def recognize(
    audio: NDArray[np.float32],
    turns: list[DiarizationTurn],
    threads: int = 8,
    chunk_s: float = 90,
) -> MultitalkerResult | str:
    """Recognize each speaker using target and competing-speaker activity.

    Audio is mono float32 at 16 kHz. Independent chunks bound encoder memory.
    Word times are RNNT emission-frame estimates, not forced alignments.
    Overlapping turns activate both target and background masks. No enrollment
    audio, reference text, or reference speaker activity enters recognition.
    """
    if audio.ndim != 1 or audio.dtype != np.float32 or not np.isfinite(audio).all():
        return "Multitalker needs finite mono float32 audio at 16 kHz"
    if not audio.size or threads < 1:
        return "Multitalker needs nonempty audio and positive thread count"
    if not math.isfinite(chunk_s) or not 0 < chunk_s <= 90:
        return "Multitalker chunk duration must be in (0, 90] seconds"
    duration_s = audio.size / 16000
    if any(
        not turn.speaker
        or not math.isfinite(turn.start_s)
        or not math.isfinite(turn.end_s)
        or not 0 <= turn.start_s < turn.end_s <= duration_s + 0.1
        for turn in turns
    ):
        return "Multitalker speaker turns must have finite valid recording times"
    if not turns:
        return MultitalkerResult([])
    try:
        import torch
        from huggingface_hub import hf_hub_download
        from nemo.collections.asr.models import ASRModel
        from nemo.collections.asr.models.multitalker_asr_models import (
            EncDecMultiTalkerRNNTBPEModel,
        )
        from nemo.collections.asr.modules.audio_preprocessing import (
            AudioToMelSpectrogramPreprocessor,
        )
        from nemo.collections.asr.modules.conformer_encoder import ConformerEncoder
        from nemo.collections.asr.parts.utils.rnnt_utils import Hypothesis
        from omegaconf import OmegaConf
    except ImportError as error:
        return f"Multitalker dependencies unavailable; install the multitalker extra: {error}"
    torch.set_num_threads(threads)
    try:
        checkpoint = hf_hub_download(MODEL, CHECKPOINT, revision=REVISION)
        restored = ASRModel.restore_from(checkpoint, map_location=torch.device("cpu"))
        if not isinstance(restored, EncDecMultiTalkerRNNTBPEModel):
            return "Multitalker checkpoint has an unexpected model architecture"
        model = restored.to("cpu").eval()
        model.change_decoding_strategy(
            OmegaConf.create(
                {
                    "strategy": "greedy_batch",
                    "greedy": {"use_cuda_graph_decoder": False},
                    "preserve_alignments": True,
                    "compute_timestamps": True,
                }
            )
        )
        encoder = model.encoder
        preprocessor = model.preprocessor
        if not isinstance(encoder, ConformerEncoder) or not isinstance(
            preprocessor, AudioToMelSpectrogramPreprocessor
        ):
            return "Multitalker checkpoint has an unexpected audio encoder"
        subsampling_factor = int(encoder.subsampling_factor)
        frame_s = float(model.cfg.preprocessor.window_stride) * subsampling_factor
        chunk_samples = max(1, round(chunk_s * 16000))
        words: list[SpeakerWord] = []
        with torch.inference_mode():
            for offset in range(0, audio.size, chunk_samples):
                offset_s = offset / 16000
                chunk = audio[offset : offset + chunk_samples]
                end_s = (offset + chunk.size) / 16000
                active_turns = [
                    turn
                    for turn in turns
                    if turn.start_s < end_s and turn.end_s > offset_s
                ]
                labels = sorted({turn.speaker for turn in active_turns})
                if not labels:
                    continue
                signal = torch.from_numpy(chunk).unsqueeze(0)
                length = torch.tensor([chunk.size])
                _, processed_length = preprocessor(input_signal=signal, length=length)
                n_frames = math.ceil(int(processed_length[0]) / subsampling_factor)
                activity = torch.zeros((len(labels), n_frames), dtype=torch.float32)
                frame_times = torch.arange(n_frames) * frame_s + offset_s
                for index, label in enumerate(labels):
                    for turn in active_turns:
                        if turn.speaker == label:
                            activity[
                                index,
                                (frame_times >= turn.start_s)
                                & (frame_times < turn.end_s),
                            ] = 1
                for index, label in enumerate(labels):
                    other_indices = [j for j in range(len(labels)) if j != index]
                    background = (
                        activity[other_indices].amax(dim=0)
                        if other_indices
                        else torch.zeros(n_frames)
                    )
                    model.set_speaker_targets(
                        activity[index].unsqueeze(0), background.unsqueeze(0)
                    )
                    encoded, encoded_length = model.forward(
                        input_signal=signal, input_signal_length=length
                    )
                    hypotheses = model.decoding.rnnt_decoder_predictions_tensor(
                        encoded, encoded_length, return_hypotheses=True
                    )
                    hypothesis = hypotheses[0]
                    if not isinstance(hypothesis, Hypothesis):
                        return "Multitalker decoder returned an unexpected hypothesis"
                    if not isinstance(hypothesis.timestamp, dict):
                        return "Multitalker did not return native word timestamps"
                    timestamp_words = hypothesis.timestamp.get("word", [])
                    if (
                        hypothesis.text
                        and hypothesis.text.strip()
                        and not timestamp_words
                    ):
                        return (
                            "Multitalker produced speech without native word timestamps"
                        )
                    for word in timestamp_words:
                        start_frame = float(word["start_offset"])
                        end_frame = float(word["end_offset"])
                        n_encoded_frames = int(encoded_length[0])
                        if not (
                            0 <= start_frame <= n_encoded_frames
                            and start_frame <= end_frame <= n_encoded_frames + 1
                        ):
                            return (
                                f"Multitalker invalid timestamps for {label} in chunk "
                                f"{offset_s:g}–{end_s:g}s: frames {start_frame:g}–{end_frame:g}"
                            )
                        start_s = offset_s + start_frame * frame_s
                        word_end_s = offset_s + end_frame * frame_s
                        words.append(
                            SpeakerWord(
                                min(start_s, end_s),
                                min(word_end_s, end_s),
                                word["word"],
                                label,
                            )
                        )
    except (OSError, RuntimeError, ValueError) as error:
        return f"Multitalker recognition failed: {error}"
    return MultitalkerResult(
        sorted(words, key=lambda word: (word.start_s, word.end_s, word.speaker))
    )
