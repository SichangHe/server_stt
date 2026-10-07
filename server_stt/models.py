"""Fetch public speaker models and preserve their bundled license."""

import argparse
import hashlib
import shutil
import tarfile
import urllib.request
from pathlib import Path

BASE = "https://github.com/k2-fsa/sherpa-onnx/releases/download"
FILES = {
    "segmentation.tar.bz2": (
        f"{BASE}/speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2",
        "24615ee884c897d9d2ba09bb4d30da6bb1b15e685065962db5b02e76e4996488",
    ),
    "embedding.onnx": (
        f"{BASE}/speaker-recongition-models/wespeaker_en_voxceleb_resnet34.onnx",
        "5ef208a9da1453335308a6b6f4e6dfbd7e183a38b604de0a57664f45d257fe94",
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    for name, (url, digest) in FILES.items():
        path = args.destination / name
        if not path.exists():
            temporary = path.with_suffix(".part")
            with (
                urllib.request.urlopen(url, timeout=120) as response,
                temporary.open("wb") as output,
            ):
                shutil.copyfileobj(response, output)
            temporary.rename(path)
        with path.open("rb") as source:
            actual = hashlib.file_digest(source, "sha256").hexdigest()
        if actual != digest:
            parser.error(f"Checksum mismatch: remove {path} and retry")
    with tarfile.open(args.destination / "segmentation.tar.bz2") as archive:
        archive.extractall(args.destination, filter="data")
    print(args.destination)
    return 0
