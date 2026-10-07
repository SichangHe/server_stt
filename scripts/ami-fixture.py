"""Download a checksummed AMI crop and its independent manual word reference."""

import argparse
import csv
import hashlib
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
    args = parser.parse_args()
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
    wav = args.directory / "ES2004a-300-390.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(args.directory / "ES2004a.Mix-Headset.wav"),
            "-ss",
            "300",
            "-t",
            "90",
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
            str(args.directory / "ES2004a-300-390.mp3"),
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
                if 300 <= start_s < 390:
                    words.append(
                        (start_s - 300, min(end_s, 390) - 300, speaker, word.text or "")
                    )
    with (args.directory / "reference.tsv").open(
        "w", newline="", encoding="utf-8"
    ) as target:
        writer = csv.writer(target, delimiter="\t")
        writer.writerow(("start_s", "end_s", "speaker", "word"))
        writer.writerows(sorted(words))
    print(f"{len(words)} reference entries and 90-second WAV/MP3 in {args.directory}")


if __name__ == "__main__":
    main()
