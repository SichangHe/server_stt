"""Transcribe raw mono 16 kHz signed 16-bit PCM from stdin as it arrives.

Stdout carries only JSON lines: `{"words": [...]}` with recording-time
`start_s`, `end_s`, `text`, `speaker`, or a final `{"error": "..."}`.
"""

import argparse
import json
import os
import queue
import sys
import threading
from collections.abc import Iterator
from dataclasses import asdict
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

# Measured trade-offs are in docs/live.md.
DIARIZATION_CHUNK_FRAMES = 39
CONTEXT_S = 10.0
HOLD_S = 1.0
MIN_STEP_S = 1.0


def _read(source_fd: int, arrived: queue.Queue[NDArray[np.float32] | None]) -> None:
    """Forward PCM as float samples the moment it arrives; `None` marks the end."""
    carry = b""
    try:
        while data := os.read(source_fd, 1 << 16):
            carry += data
            usable = len(carry) - len(carry) % 2
            arrived.put(
                np.frombuffer(carry[:usable], dtype="<i2").astype(np.float32)
                / np.float32(32768)
            )
            carry = carry[usable:]
    finally:
        arrived.put(None)


def _batches(
    arrived: queue.Queue[NDArray[np.float32] | None],
) -> Iterator[NDArray[np.float32]]:
    """Wait for audio, then yield everything that has arrived."""
    ended = False
    while not ended:
        blocks = [arrived.get()]
        while blocks[-1] is not None and not arrived.empty():
            blocks.append(arrived.get())
        ended = blocks[-1] is None
        samples = [block for block in blocks if block is not None]
        if samples:
            yield np.concatenate(samples)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--diarization-model",
        type=Path,
        default=Path("models/Nemotron-3-Diarization.q8_0.gguf"),
    )
    p.add_argument(
        "--diarization-runtime",
        type=Path,
        default=Path("models/nemo-speech-0.2.0-linux-x86_64-cpu"),
    )
    p.add_argument("--threads", type=int, default=16)
    a = p.parse_args()
    # Libraries print to file descriptor 1; keep it for JSON lines only.
    out = os.fdopen(os.dup(1), "w")
    os.dup2(2, 1)
    arrived: queue.Queue[NDArray[np.float32] | None] = queue.Queue()
    threading.Thread(
        target=_read, args=(sys.stdin.fileno(), arrived), daemon=True
    ).start()
    from server_stt.diarization import DiarizationStream
    from server_stt.live import transcribe
    from server_stt.multitalker import load

    def fail(error: str) -> int:
        print(json.dumps({"error": error}), file=out, flush=True)
        return 1

    model = load(a.threads)
    if isinstance(model, str):
        return fail(model)
    diarization = DiarizationStream.open(
        a.diarization_model, a.diarization_runtime, DIARIZATION_CHUNK_FRAMES
    )
    if isinstance(diarization, str):
        return fail(diarization)
    try:
        for words in transcribe(
            _batches(arrived), diarization, model, CONTEXT_S, HOLD_S, MIN_STEP_S
        ):
            if isinstance(words, str):
                return fail(words)
            if words:
                print(
                    json.dumps({"words": [asdict(w) for w in words]}),
                    file=out,
                    flush=True,
                )
    finally:
        diarization.close()
    return 0
