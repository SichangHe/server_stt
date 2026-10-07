"""Score normalized word errors and speaker turns at reference word times, not DER."""

import argparse
import csv
import itertools
import json
import re
from pathlib import Path

from server_stt.cli import Transcript


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9']", "", text.lower())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("transcript", type=Path)
    args = parser.parse_args()
    with args.reference.open(encoding="utf-8") as source:
        reference = [
            row
            for row in csv.DictReader(source, delimiter="\t")
            if normalize(row["word"])
        ]
    transcript = Transcript.model_validate_json(
        args.transcript.read_text(encoding="utf-8")
    )
    expected = [normalize(row["word"]) for row in reference]
    observed = [
        normalize(word.text) for word in transcript.words if normalize(word.text)
    ]
    previous = list(range(len(observed) + 1))
    for i, word in enumerate(expected, start=1):
        current = [i]
        for j, hypothesis in enumerate(observed, start=1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (word != hypothesis),
                )
            )
        previous = current
    labels = sorted({turn.speaker for turn in transcript.turns})
    assignments: list[tuple[str, str | None]] = []
    for word in reference:
        start_s, end_s = float(word["start_s"]), float(word["end_s"])
        if end_s <= start_s:
            continue
        overlaps = {label: 0.0 for label in labels}
        for turn in transcript.turns:
            overlaps[turn.speaker] += max(
                0, min(end_s, turn.end_s) - max(start_s, turn.start_s)
            )
        predicted = (
            max(overlaps, key=lambda label: overlaps[label])
            if any(overlaps.values())
            else None
        )
        assignments.append((word["speaker"], predicted))
    best_correct = 0
    best_mapping: dict[str, str] = {}
    for candidate in itertools.permutations(labels, min(len(labels), 4)):
        for speakers in itertools.combinations("ABCD", len(candidate)):
            mapping = dict(zip(candidate, speakers, strict=True))
            correct = sum(
                mapping.get(predicted) == speaker if predicted is not None else False
                for speaker, predicted in assignments
            )
            if correct > best_correct:
                best_correct, best_mapping = correct, mapping
    print(
        json.dumps(
            {
                "reference_words": len(expected),
                "hypothesis_words": len(observed),
                "word_edit_errors": previous[-1],
                "word_error_fraction": previous[-1] / len(expected),
                "speaker_labels": labels,
                "best_speaker_mapping": best_mapping,
                "reference_words_with_duration": len(assignments),
                "correct_word_time_speakers": best_correct,
                "word_time_speaker_error_fraction": 1 - best_correct / len(assignments),
                "limitations": "Single 90-second crop. WER orders simultaneous speakers by onset. Speaker score uses reference word times, not ASR alignment; it is not DER.",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
