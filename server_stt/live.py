"""Low-latency PCM framing for online speech processing.

The reader accepts mono 16 kHz signed 16-bit little-endian PCM on stdin and
passes bounded float32 chunks to a caller supplied processor.  A processor can
keep model state between calls and emit partial results as JSON or another
protocol.
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Iterable

import numpy as np


def pcm_chunks(stream, chunk_s: float = 1.0, sample_rate: int = 16000) -> Iterable[np.ndarray]:
    """Yield finite float32 mono chunks from a raw PCM byte stream."""
    if sample_rate < 1 or not 0 < chunk_s <= 60:
        raise ValueError("sample_rate must be positive and chunk_s must be in (0, 60]")
    frame_bytes = max(2, round(chunk_s * sample_rate) * 2)
    carry = b""
    while True:
        data = stream.read(frame_bytes)
        if not data:
            break
        carry += data
        usable = len(carry) - len(carry) % 2
        if usable:
            samples = np.frombuffer(carry[:usable], dtype="<i2").astype(np.float32) / 32768
            yield samples
            carry = carry[usable:]
    if carry:
        raise ValueError("input ends with an incomplete PCM sample")


def run(process: Callable[[np.ndarray], object], stream=None, chunk_s: float = 1.0) -> None:
    """Process stdin PCM chunks, writing one repr per processor result."""
    for chunk in pcm_chunks(stream or sys.stdin.buffer, chunk_s):
        result = process(chunk)
        if result is not None:
            print(result, flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunk-s", type=float, default=1.0)
    parser.parse_args()
    parser.error("a model processor is required; import server_stt.live.run")


if __name__ == "__main__":
    main()
