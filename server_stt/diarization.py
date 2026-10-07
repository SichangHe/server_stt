"""Optional CPU Nemotron diarization through NVIDIA's versioned native ABI."""

import ctypes as c
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


@dataclass
class DiarizationTurn:
    start_s: float
    end_s: float
    speaker: str


@dataclass
class DiarizationResult:
    turns: list[DiarizationTurn]
    probabilities: NDArray[np.float32]
    frame_s: float


class _ModelConfig(c.Structure):
    _fields_ = [
        ("size", c.c_size_t),
        ("model_path", c.c_char_p),
        ("gpu", c.c_int32),
        ("preset", c.c_char_p),
        ("chunk_frames", c.c_int32),
        ("right_context_frames", c.c_int32),
        ("left_context_frames", c.c_int32),
        ("fifo_frames", c.c_int32),
        ("spkcache_frames", c.c_int32),
        ("update_period_frames", c.c_int32),
    ]


class _Segment(c.Structure):
    _fields_ = [
        ("start_s", c.c_double),
        ("end_s", c.c_double),
        ("speaker", c.c_int32),
    ]


def _load(runtime_path: Path) -> c.CDLL | str:
    """Declare the pinned v0.2.0 ABI before passing pointers to native code."""
    library = runtime_path / "lib" / "libnemo_speech_asr_c.so"
    try:
        lib = c.CDLL(str(library))
    except OSError as error:
        return f"Cannot load Nemotron runtime {library}: {error}"
    pointer = c.c_void_p
    float_pointer = c.POINTER(c.c_float)
    signatures = {
        "create": ([c.POINTER(_ModelConfig), c.POINTER(pointer)], c.c_int),
        "destroy": ([pointer], None),
        "num_speakers": ([pointer], c.c_int32),
        "seconds_per_frame": ([pointer], c.c_double),
        "offline_f32": (
            [pointer, float_pointer, c.c_size_t, c.c_int32, c.POINTER(pointer)],
            c.c_int,
        ),
        "stream_open": ([pointer, c.POINTER(pointer)], c.c_int),
        "stream_push_f32": ([pointer, float_pointer, c.c_size_t, c.c_int32], c.c_int),
        "stream_finish": ([pointer], c.c_int),
        "stream_close": ([pointer], None),
        "frame_count": ([pointer], c.c_int64),
        "frame_probs_start": ([pointer], c.c_int64),
        "frame_probs": ([pointer, float_pointer, c.c_size_t], c.c_int),
        "segments": (
            [pointer, pointer, c.POINTER(_Segment), c.c_size_t, c.POINTER(c.c_size_t)],
            c.c_int,
        ),
    }
    try:
        for name, (arguments, result) in signatures.items():
            function = getattr(lib, f"nemo_speech_diar_{name}")
            function.argtypes = arguments
            function.restype = result
        lib.nemo_speech_asr_last_error.argtypes = []
        lib.nemo_speech_asr_last_error.restype = c.c_char_p
    except AttributeError as error:
        return f"Incompatible Nemotron runtime: {error}"
    return lib


def _error(lib: c.CDLL, operation: str) -> str:
    raw = lib.nemo_speech_asr_last_error()
    return f"Nemotron {operation} failed: {raw.decode(errors='replace') if raw else 'unknown native error'}"


# 🧑 "speakers + accurate transcripts"
def diarize(
    audio: NDArray[np.float32], model_path: Path, runtime_path: Path
) -> DiarizationResult | str:
    """Infer overlapping turns and posterior scores from mono 16 kHz samples.

    Recordings up to 390 seconds use full attention. Longer recordings use
    NVIDIA's v3-offline streaming preset. Streaming input is fed in 30-second
    chunks to avoid the native runtime's 20-minute posterior compaction.
    """
    if audio.ndim != 1 or not len(audio) or not np.isfinite(audio).all():
        return "Nemotron needs nonempty finite mono 16 kHz audio"
    if not model_path.is_file():
        return f"Nemotron model not found: {model_path}"
    lib = _load(runtime_path)
    if isinstance(lib, str):
        return lib
    config = _ModelConfig(
        c.sizeof(_ModelConfig),
        str(model_path).encode(),
        -1,
        b"v3-offline",
        0,
        0,
        -1,
        0,
        0,
        0,
    )
    model, stream = c.c_void_p(), c.c_void_p()
    if lib.nemo_speech_diar_create(c.byref(config), c.byref(model)):
        return _error(lib, "model loading")
    try:
        samples = np.ascontiguousarray(audio, dtype=np.float32)
        float_pointer = samples.ctypes.data_as(c.POINTER(c.c_float))
        if len(samples) <= 390 * 16000:
            status = lib.nemo_speech_diar_offline_f32(
                model, float_pointer, len(samples), 16000, c.byref(stream)
            )
            probabilities = None
        else:
            status = lib.nemo_speech_diar_stream_open(model, c.byref(stream))
            posterior_chunks = []
            copied_frames = 0
            n_speakers = lib.nemo_speech_diar_num_speakers(model)
            for start in range(0, len(samples), 30 * 16000):
                if status:
                    break
                chunk = samples[start : start + 30 * 16000]
                status = lib.nemo_speech_diar_stream_push_f32(
                    stream,
                    chunk.ctypes.data_as(c.POINTER(c.c_float)),
                    len(chunk),
                    16000,
                )
                if start + len(chunk) == len(samples) and not status:
                    status = lib.nemo_speech_diar_stream_finish(stream)
                if status:
                    break
                first_frame = lib.nemo_speech_diar_frame_probs_start(stream)
                n_frames = lib.nemo_speech_diar_frame_count(stream)
                if first_frame > copied_frames:
                    return "Nemotron discarded posterior frames before retrieval"
                retained = np.empty(
                    (n_frames - first_frame, n_speakers), dtype=np.float32
                )
                status = lib.nemo_speech_diar_frame_probs(
                    stream, retained.ctypes.data_as(c.POINTER(c.c_float)), retained.size
                )
                posterior_chunks.append(retained[copied_frames - first_frame :].copy())
                copied_frames = n_frames
            if not status:
                probabilities = np.concatenate(posterior_chunks)
            else:
                probabilities = None
        if status:
            return _error(lib, "inference")
        n_frames = lib.nemo_speech_diar_frame_count(stream)
        n_speakers = lib.nemo_speech_diar_num_speakers(model)
        frame_s = lib.nemo_speech_diar_seconds_per_frame(model)
        if probabilities is None:
            probabilities = np.empty((n_frames, n_speakers), dtype=np.float32)
            status = lib.nemo_speech_diar_frame_probs(
                stream,
                probabilities.ctypes.data_as(c.POINTER(c.c_float)),
                probabilities.size,
            )
            if status:
                return _error(lib, "posterior retrieval")
        count = c.c_size_t()
        if lib.nemo_speech_diar_segments(stream, None, None, 0, c.byref(count)):
            return _error(lib, "turn counting")
        segments = (_Segment * count.value)()
        if lib.nemo_speech_diar_segments(
            stream, None, segments, count.value, c.byref(count)
        ):
            return _error(lib, "turn retrieval")
        return DiarizationResult(
            [
                DiarizationTurn(s.start_s, s.end_s, f"SPEAKER_{s.speaker:02d}")
                for s in segments
            ],
            probabilities,
            frame_s,
        )
    finally:
        if stream:
            lib.nemo_speech_diar_stream_close(stream)
        lib.nemo_speech_diar_destroy(model)


def speaker_for(start_s: float, end_s: float, result: DiarizationResult) -> str | None:
    """Choose the greatest mean speaker posterior during an ASR word.

    ASR provides independent evidence of speech, so no speech threshold is
    applied again. Overlapping turns remain intact; this selects one label
    for each recognized word. Out-of-range timestamps remain unknown.
    """
    start = max(0, math.floor(start_s / result.frame_s))
    end = min(
        len(result.probabilities), max(start + 1, math.ceil(end_s / result.frame_s))
    )
    if start >= end:
        return None
    scores = result.probabilities[start:end].mean(axis=0)
    speaker = int(scores.argmax())
    return f"SPEAKER_{speaker + 1:02d}"
