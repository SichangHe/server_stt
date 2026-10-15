"""Decode files once, recognize words, and attribute overlapping speaker turns."""

import argparse
import math
import sys
import unicodedata
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
    probability: float | None


class Transcript(BaseModel):
    source: str
    model: str
    language: str
    language_probability: float | None
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
            token = word.text.strip()
            no_spaces = transcript.language.lower() in {
                "chinese",
                "zh",
                "japanese",
                "ja",
                "cantonese",
                "yue",
                "thai",
                "th",
            }
            punctuation = bool(token) and unicodedata.category(token[0]).startswith("P")
            separator = "" if no_spaces or punctuation else " "
            lines[-1] += separator + token
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
        help="Sherpa pyannote segmentation ONNX",
    )
    parser.add_argument("--embedding", type=Path, help="Sherpa speaker embedding ONNX")
    parser.add_argument(
        "--recognizer", choices=["whisper", "qwen", "multitalker"], default="multitalker"
    )
    parser.add_argument(
        "--diarization", choices=["sherpa", "nemotron"], default="nemotron"
    )
    parser.add_argument(
        "--diarization-model",
        type=Path,
        default=Path("models/Nemotron-3-Diarization.q8_0.gguf"),
    )
    parser.add_argument(
        "--diarization-runtime",
        type=Path,
        default=Path("models/nemo-speech-0.2.0-linux-x86_64-cpu"),
    )
    parser.add_argument("--model", default="large-v3", help="Whisper model")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--compute-type", default="int8", help="Whisper precision")
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument(
        "--speakers", type=int, default=-1, help="Known speaker count; -1 estimates it"
    )
    parser.add_argument(
        "--language",
        help="Language code; multitalker assumes English, Qwen/Whisper detect by default",
    )
    parser.add_argument(
        "--cluster-threshold",
        type=float,
        default=0.8,
        help="Automatic count threshold; larger gives fewer speakers",
    )
    parser.add_argument(
        "--activity-threshold",
        type=float,
        help="Nemotron posterior threshold for multitalker masks (default: 0.3)",
    )
    parser.add_argument("--prompt", help="Vocabulary/context hint for recognition")
    args = parser.parse_args()
    paths = [args.audio]
    if args.diarization == "sherpa":
        if args.segmentation is None or args.embedding is None:
            parser.error("Sherpa needs --segmentation and --embedding")
        paths.extend((args.segmentation, args.embedding))
    elif args.speakers != -1:
        parser.error(
            "Nemotron estimates speaker count; --speakers applies only to Sherpa"
        )
    if args.recognizer != "whisper" and args.prompt:
        parser.error("--prompt applies only to Whisper")
    if args.activity_threshold is not None and args.recognizer != "multitalker":
        parser.error("--activity-threshold applies only to multitalker")
    if args.recognizer != "whisper" and args.device != "cpu":
        parser.error("The selected backend currently supports CPU only")
    if args.recognizer == "multitalker":
        if args.diarization != "nemotron":
            parser.error("Multitalker requires Nemotron speaker activity")
        if args.language is not None and args.language.lower() not in {"en", "english"}:
            parser.error("Multitalker supports English; select Qwen for other languages")
        activity_threshold = args.activity_threshold
    else:
        activity_threshold = None
    qwen_language = None
    if args.recognizer == "qwen":
        from server_stt.recognition import language_name

        qwen_language = language_name(args.language)
        if args.language is not None and qwen_language is None:
            parser.error(
                "Unsupported Qwen language; use a supported ISO code or full name"
            )
    for path in paths:
        if not path.is_file():
            parser.error(f"File not found: {path}")
    if args.output.exists():
        parser.error(f"Output already exists: {args.output}")
    if args.threads < 1 or (args.speakers != -1 and args.speakers < 1):
        parser.error("threads and known speaker count must be positive")
    if not math.isfinite(args.cluster_threshold) or args.cluster_threshold <= 0:
        parser.error("cluster threshold must be finite and positive")
    from faster_whisper.audio import decode_audio

    print("Decoding audio", file=sys.stderr)
    audio = decode_audio(str(args.audio), sampling_rate=16000)
    assert not isinstance(audio, tuple)
    if not len(audio):
        parser.error("Audio is empty")
    print("Finding speakers", file=sys.stderr)
    native = None
    if args.diarization == "nemotron":
        from server_stt.diarization import diarize

        native = diarize(audio, args.diarization_model, args.diarization_runtime)
        if isinstance(native, str):
            parser.error(native)
        turns = [
            Turn(start_s=t.start_s, end_s=t.end_s, speaker=t.speaker)
            for t in native.turns
        ]
    else:
        import sherpa_onnx

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
        diarizer = sherpa_onnx.OfflineSpeakerDiarization(config)
        turns = [
            Turn(start_s=t.start, end_s=t.end, speaker=f"SPEAKER_{t.speaker:02d}")
            for t in diarizer.process(audio).sort_by_start_time()
        ]
    print("Recognizing words", file=sys.stderr)
    if args.recognizer == "multitalker":
        from server_stt.multitalker import recognize as recognize_multitalker

        assert native is not None
        result = recognize_multitalker(
            audio,
            native.turns,
            threads=args.threads,
            activity=native.probabilities,
            activity_frame_s=native.frame_s,
            activity_threshold=activity_threshold,
        )
        if isinstance(result, str):
            parser.error(result)
        words = [
            Word(
                start_s=w.start_s,
                end_s=w.end_s,
                text=w.text,
                probability=w.probability,
                speaker=w.speaker,
            )
            for w in result.words
        ]
        model_name, language, language_probability = result.model, result.language, None
    elif args.recognizer == "qwen":
        from server_stt.recognition import recognize

        result = recognize(
            audio,
            language=qwen_language,
            threads=args.threads,
        )
        if isinstance(result, str):
            parser.error(result)
        words = [
            Word(
                start_s=w.start_s,
                end_s=w.end_s,
                text=w.text,
                probability=w.probability,
                speaker=None,
            )
            for w in result.words
        ]
        model_name, language, language_probability = result.model, result.language, None
    else:
        from faster_whisper import WhisperModel

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
                speaker=None,
            )
            for segment in segments
            for w in segment.words or []
        ]
        model_name, language, language_probability = (
            args.model,
            info.language,
            info.language_probability,
        )
    if args.recognizer != "multitalker":
        if native is not None:
            from server_stt.diarization import speaker_for as native_speaker_for

            for word in words:
                word.speaker = native_speaker_for(word.start_s, word.end_s, native)
        else:
            for word in words:
                word.speaker = speaker_for(word.start_s, word.end_s, turns)
    transcript = Transcript(
        source=str(args.audio),
        model=model_name,
        language=language,
        language_probability=language_probability,
        duration_s=len(audio) / 16000,
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
