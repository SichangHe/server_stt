"""Decode files once, recognize words, and attribute overlapping speaker turns."""

import argparse
import math
import sys
from pathlib import Path

from pydantic import BaseModel


class Turn(BaseModel):
    start_s: float
    end_s: float
    speaker: str


class Word(BaseModel):
    start_s: float
    end_s: float
    text: str
    speaker: str | None
    probability: float


class Transcript(BaseModel):
    source: str
    model: str
    language: str
    language_probability: float
    duration_s: float
    turns: list[Turn]
    words: list[Word]


def speaker_for(start_s: float, end_s: float, turns: list[Turn]) -> str | None:
    """Use greatest temporal overlap; preserve unknown when no turn overlaps."""
    overlaps: dict[str, float] = {}
    for turn in turns:
        overlap_s = max(0.0, min(end_s, turn.end_s) - max(start_s, turn.start_s))
        overlaps[turn.speaker] = overlaps.get(turn.speaker, 0.0) + overlap_s
    return (
        max(overlaps, key=lambda speaker: overlaps[speaker])
        if any(overlaps.values())
        else None
    )


def render(transcript: Transcript) -> str:
    """Group adjacent words with identical speaker labels for readable output."""
    lines: list[str] = []
    previous: str | None = None
    for word in transcript.words:
        speaker = word.speaker or "UNKNOWN"
        if speaker != previous:
            lines.append(f"[{word.start_s:.2f}s] {speaker}: {word.text.strip()}")
        else:
            lines[-1] += word.text
        previous = speaker
    return "\n".join(lines) + "\n"


# 🧑 "processes MP3 or similar files into speakers + accurate transcripts, designed to be run on the server"
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument(
        "--output", type=Path, required=True, help="New output directory"
    )
    parser.add_argument(
        "--segmentation",
        type=Path,
        required=True,
        help="Sherpa pyannote segmentation ONNX",
    )
    parser.add_argument(
        "--embedding", type=Path, required=True, help="Sherpa speaker embedding ONNX"
    )
    parser.add_argument("--model", default="large-v3")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument(
        "--speakers", type=int, default=-1, help="Known speaker count; -1 estimates it"
    )
    parser.add_argument("--language", help="Language code; default detects it")
    parser.add_argument(
        "--cluster-threshold",
        type=float,
        default=0.8,
        help="Automatic count threshold; larger gives fewer speakers",
    )
    parser.add_argument("--prompt", help="Vocabulary/context hint for recognition")
    args = parser.parse_args()
    for path in (args.audio, args.segmentation, args.embedding):
        if not path.is_file():
            parser.error(f"File not found: {path}")
    if args.output.exists():
        parser.error(f"Output already exists: {args.output}")
    if args.threads < 1 or (args.speakers != -1 and args.speakers < 1):
        parser.error("threads and known speaker count must be positive")
    if not math.isfinite(args.cluster_threshold) or args.cluster_threshold <= 0:
        parser.error("cluster threshold must be finite and positive")
    import sherpa_onnx
    from faster_whisper import WhisperModel
    from faster_whisper.audio import decode_audio

    print("Decoding audio", file=sys.stderr)
    audio = decode_audio(str(args.audio), sampling_rate=16000)
    assert not isinstance(audio, tuple)
    if not len(audio):
        parser.error("Audio is empty")
    config = sherpa_onnx.OfflineSpeakerDiarizationConfig(
        segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
            pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(
                model=str(args.segmentation)
            ),
            num_threads=args.threads,
        ),
        embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(
            model=str(args.embedding), num_threads=args.threads
        ),
        clustering=sherpa_onnx.FastClusteringConfig(
            num_clusters=args.speakers, threshold=args.cluster_threshold
        ),
        min_duration_on=0.3,
        min_duration_off=0.5,
    )
    if not config.validate():
        parser.error("Invalid speaker model configuration")
    print("Finding speakers", file=sys.stderr)
    diarizer = sherpa_onnx.OfflineSpeakerDiarization(config)
    turns = [
        Turn(start_s=t.start, end_s=t.end, speaker=f"SPEAKER_{t.speaker:02d}")
        for t in diarizer.process(audio).sort_by_start_time()
    ]
    print("Recognizing words", file=sys.stderr)
    model = WhisperModel(
        args.model,
        device=args.device,
        compute_type=args.compute_type,
        cpu_threads=args.threads,
    )
    segments, info = model.transcribe(
        audio,
        language=args.language,
        initial_prompt=args.prompt,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
    )
    words = [
        Word(
            start_s=w.start,
            end_s=w.end,
            text=w.word,
            probability=w.probability,
            speaker=speaker_for(w.start, w.end, turns),
        )
        for segment in segments
        for w in segment.words or []
    ]
    transcript = Transcript(
        source=str(args.audio),
        model=args.model,
        language=info.language,
        language_probability=info.language_probability,
        duration_s=info.duration,
        turns=turns,
        words=words,
    )
    args.output.mkdir(parents=True)
    (args.output / "transcript.json").write_text(
        transcript.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    (args.output / "transcript.txt").write_text(render(transcript), encoding="utf-8")
    print(f"Wrote {args.output}", file=sys.stderr)
    return 0
