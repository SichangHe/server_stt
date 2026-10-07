"""Optional Qwen recognition and generated-text alignment on mono 16 kHz audio."""

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

ASR_MODEL = "Qwen/Qwen3-ASR-1.7B"
ASR_REVISION = "7278e1e70fe206f11671096ffdd38061171dd6e5"
ALIGNER_MODEL = "Qwen/Qwen3-ForcedAligner-0.6B"
ALIGNER_REVISION = "c7cbfc2048c462b0d63a45797104fc9db3ad62b7"
LANGUAGES = {
    "zh": "Chinese",
    "en": "English",
    "yue": "Cantonese",
    "ar": "Arabic",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "pt": "Portuguese",
    "id": "Indonesian",
    "it": "Italian",
    "ko": "Korean",
    "ru": "Russian",
    "th": "Thai",
    "vi": "Vietnamese",
    "ja": "Japanese",
    "tr": "Turkish",
    "hi": "Hindi",
    "ms": "Malay",
    "nl": "Dutch",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "pl": "Polish",
    "cs": "Czech",
    "tl": "Filipino",
    "fil": "Filipino",
    "fa": "Persian",
    "el": "Greek",
    "ro": "Romanian",
    "hu": "Hungarian",
    "mk": "Macedonian",
}


def language_name(value: str | None) -> str | None:
    """Accept ISO language codes or Qwen's canonical full names."""
    if value is None:
        return None
    value = value.strip().lower()
    return LANGUAGES.get(value.split("-")[0]) or next(
        (name for name in LANGUAGES.values() if name.lower() == value), None
    )


@dataclass
class RecognitionWord:
    start_s: float
    end_s: float
    text: str
    probability: float | None


@dataclass
class RecognitionResult:
    words: list[RecognitionWord]
    language: str
    model: str


# 🧑 "speakers + accurate transcripts"
def recognize(
    audio: NDArray[np.float32],
    language: str | None = None,
    threads: int = 8,
    chunk_s: float = 20,
) -> RecognitionResult | str:
    """Align only recognized text, preserving unknown word confidence.

    Input samples must be mono 16 kHz float32. Language uses Qwen's full
    language names. Fixed chunks bound CPU memory and inference context.
    """
    if audio.ndim != 1 or audio.dtype != np.float32 or not np.isfinite(audio).all():
        return "Qwen requires finite mono float32 samples at 16 kHz"
    if threads < 1 or not math.isfinite(chunk_s) or not 0 < chunk_s <= 300:
        return "Qwen threads must be positive and chunk duration in (0, 300] seconds"
    if not audio.size:
        return "Qwen cannot recognize empty audio"
    try:
        import torch
        from huggingface_hub import snapshot_download
        from qwen_asr import Qwen3ASRModel
    except ImportError as error:
        return f"Qwen dependencies unavailable; install the qwen extra: {error}"
    torch.set_num_threads(threads)
    try:
        model_path = snapshot_download(ASR_MODEL, revision=ASR_REVISION)
        aligner_path = snapshot_download(ALIGNER_MODEL, revision=ALIGNER_REVISION)
        model = Qwen3ASRModel.from_pretrained(
            model_path,
            dtype=torch.float32,
            device_map="cpu",
            max_inference_batch_size=1,
            max_new_tokens=1024,
            forced_aligner=aligner_path,
            forced_aligner_kwargs={"dtype": torch.float32, "device_map": "cpu"},
        )
        words: list[RecognitionWord] = []
        detected_languages: list[str] = []
        chunk_samples = max(1, round(chunk_s * 16000))
        for offset in range(0, audio.size, chunk_samples):
            result = model.transcribe(
                audio=(audio[offset : offset + chunk_samples], 16000),
                language=language,
                return_time_stamps=True,
            )[0]
            detected_languages.append(result.language)
            if result.time_stamps is None:
                if result.text.strip():
                    return "Qwen produced text without required word timestamps"
                continue
            for item in result.time_stamps.items:
                start_s = offset / 16000 + float(item.start_time)
                end_s = offset / 16000 + float(item.end_time)
                if not 0 <= start_s <= end_s <= audio.size / 16000 + 0.1:
                    return "Qwen produced invalid word timestamps"
                words.append(RecognitionWord(start_s, end_s, item.text, None))
    except (OSError, RuntimeError, ValueError) as error:
        return f"Qwen recognition failed: {error}"
    detected = ", ".join(dict.fromkeys(detected_languages))
    return RecognitionResult(words, detected, f"{ASR_MODEL}@{ASR_REVISION}")
