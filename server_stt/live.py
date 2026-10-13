"""Online speaker-attributed recognition over a growing recording."""

import math
import sys
import time
from collections.abc import Iterable, Iterator
from itertools import chain
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from server_stt.diarization import DiarizationStream
from server_stt.multitalker import SpeakerWord, recognize_chunk

if TYPE_CHECKING:
    from nemo.collections.asr.models.multitalker_asr_models import (
        EncDecMultiTalkerRNNTBPEModel,
    )


# 🧑 "Make it also work online in the fly instead of on everything that's already recorded"
def transcribe(
    batches: Iterable[NDArray[np.float32]],
    diarization: DiarizationStream,
    model: "EncDecMultiTalkerRNNTBPEModel",
    context_s: float,
    hold_s: float,
    min_step_s: float,
) -> Iterator[list[SpeakerWord] | str]:
    """Yield each word once, in recording time, as mono 16 kHz audio arrives.

    Each batch is all audio that arrived since the previous one, so a slow
    step is followed by a larger one and the stream catches up. A step
    recognizes the unemitted audio after `context_s` of earlier audio and
    emits words starting before the labeled end minus `hold_s`; later words
    wait for settled speaker turns and recognizer lookahead. A string is a
    fatal error and ends the stream.
    """
    buffer = np.empty(0, dtype=np.float32)
    buffer_start = 0
    emitted_s = 0.0
    empty = np.empty(0, dtype=np.float32)
    for batch, final in chain(((b, False) for b in batches), [(empty, True)]):
        buffer = np.concatenate((buffer, batch))
        t0 = time.monotonic()
        error = diarization.finish() if final else diarization.push(batch)
        if error is not None:
            yield error
            return
        received_s = (buffer_start + len(buffer)) / 16000
        end_s = received_s if final else min(received_s, diarization.done_s())
        if end_s <= emitted_s or not final and end_s - hold_s - emitted_s < min_step_s:
            continue
        t1 = time.monotonic()
        turns = diarization.turns()
        if isinstance(turns, str):
            yield turns
            return
        start = max(buffer_start, round((emitted_s - context_s) * 16000))
        buffer = buffer[start - buffer_start :]
        buffer_start = start
        words = recognize_chunk(
            model,
            buffer[: round(end_s * 16000) - buffer_start],
            buffer_start / 16000,
            turns,
            emitted_s,
        )
        if isinstance(words, str):
            yield words
            return
        print(
            f"step: end {end_s:.1f}s window {end_s - buffer_start / 16000:.1f}s diarization {t1 - t0:.1f}s recognition {time.monotonic() - t1:.1f}s",
            file=sys.stderr,
        )
        cut_s = math.inf if final else end_s - hold_s
        yield sorted(
            (w for w in words if emitted_s <= w.start_s < cut_s),
            key=lambda w: (w.start_s, w.end_s, w.speaker),
        )
        emitted_s = cut_s
