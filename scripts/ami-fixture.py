"""Download a checksummed AMI crop and its independent manual word reference."""

import argparse
import csv
import hashlib
import math
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

SOURCES = {
    "ES2004a.Mix-Headset.wav": (
        "https://huggingface.co/datasets/FluidInference/ami-corpus-mirror/resolve/main/sdm/ES2004a.Mix-Headset.wav",
        "3e2560b19bee6952c7c7ce041b0f1ea8a7ea9468044c4eea79d2a2c67e24ab0f",
    ),
    "ami-manual.zip": (
        "https://groups.inf.ed.ac.uk/ami/AMICorpusAnnotations/ami_public_manual_1.6.2.zip",
        "b56e5babb2496b8795deeeda7e71178d7fbc9963f94276cf2a3f4b56ebbc9f9d",
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--start-s", type=float, default=300)
    parser.add_argument("--duration-s", type=float, default=90)
    args = parser.parse_args()
    if not math.isfinite(args.start_s) or args.start_s < 0:
        parser.error("start must be finite and nonnegative")
    if not math.isfinite(args.duration_s) or args.duration_s <= 0:
        parser.error("duration must be finite and positive")
    clip_end_s = args.start_s + args.duration_s
    stem = f"ES2004a-{args.start_s:g}-{clip_end_s:g}"
    args.directory.mkdir(parents=True, exist_ok=True)
    for name, (url, digest) in SOURCES.items():
        path = args.directory / name
        if not path.exists():
            temporary = path.with_suffix(".part")
            with (
                urllib.request.urlopen(url, timeout=120) as response,
                temporary.open("wb") as target,
            ):
                while chunk := response.read(1024 * 1024):
                    target.write(chunk)
            temporary.replace(path)
        with path.open("rb") as source:
            actual = hashlib.file_digest(source, "sha256").hexdigest()
        if actual != digest:
            parser.error(f"Checksum mismatch: remove {path} and retry")
    wav = args.directory / f"{stem}.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(args.directory / "ES2004a.Mix-Headset.wav"),
            "-ss",
            str(args.start_s),
            "-t",
            str(args.duration_s),
            "-ar",
            "16000",
            "-ac",
            "1",
            str(wav),
        ],
        check=True,
        timeout=60,
    )
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(wav),
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "3",
            str(args.directory / f"{stem}.mp3"),
        ],
        check=True,
        timeout=60,
    )
    words: list[tuple[float, float, str, str]] = []
    with zipfile.ZipFile(args.directory / "ami-manual.zip") as archive:
        for speaker in "ABCD":
            root = ET.fromstring(archive.read(f"words/ES2004a.{speaker}.words.xml"))
            for word in root.findall("w"):
                start_s, end_s = (
                    float(word.attrib["starttime"]),
                    float(word.attrib["endtime"]),
                )
                if args.start_s <= start_s < clip_end_s:
                    words.append(
                        (
                            start_s - args.start_s,
                            min(end_s, clip_end_s) - args.start_s,
                            speaker,
                            word.text or "",
                        )
                    )
    with (args.directory / "reference.tsv").open(
        "w", newline="", encoding="utf-8"
    ) as target:
        writer = csv.writer(target, delimiter="\t")
        writer.writerow(("start_s", "end_s", "speaker", "word"))
        writer.writerows(sorted(words))
    print(
        f"{len(words)} reference entries and {args.duration_s:g}-second WAV/MP3 in {args.directory}"
    )


if __name__ == "__main__":
    main()
