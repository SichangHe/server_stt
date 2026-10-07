"""Download hash-pinned NVIDIA CPU runtime and Nemotron diarization model."""

import argparse
import hashlib
import platform
import shutil
import tarfile
import urllib.error
import urllib.request
from pathlib import Path

RUNTIME_NAME = "nemo-speech-0.2.0-linux-x86_64-cpu"
RUNTIME_URL = f"https://github.com/NVIDIA/NeMo-Speech.cpp/releases/download/v0.2.0/{RUNTIME_NAME}.tar.gz"
RUNTIME_SHA256 = "f396057150f1b774935c7414fd32ebc04195a795a34120d78d8c9ecefa1b7507"
MODEL_REVISION = "f667ed73aee57d40cc39428eb768b4fd87a0a29e"
MODEL_NAME = "Nemotron-3-Diarization.q8_0.gguf"
MODEL_URL = f"https://huggingface.co/nvidia/Nemotron-3-Diarization/resolve/{MODEL_REVISION}/{MODEL_NAME}"
MODEL_SHA256 = "08456d9e22cd9a323c0364d98375f3746d6e68507ebb705cd46438c534c7a3a1"
MODEL_CARD_URL = f"https://huggingface.co/nvidia/Nemotron-3-Diarization/raw/{MODEL_REVISION}/README.md"
MODEL_CARD_SHA256 = "5fe88ca4020d2ee134f806a0a02c52c19855b73047bc2e6f25b9171e1abeebfd"


def _fetch(path: Path, url: str, digest: str) -> str | None:
    """Verify existing and newly downloaded files before using them."""
    temporary = path.with_suffix(".part")
    try:
        if not path.exists():
            with (
                urllib.request.urlopen(url, timeout=120) as source,
                temporary.open("wb") as output,
            ):
                shutil.copyfileobj(source, output)
            temporary.rename(path)
        with path.open("rb") as source:
            actual = hashlib.file_digest(source, "sha256").hexdigest()
        if actual != digest:
            return f"Checksum mismatch: remove {path} and retry"
    except (OSError, urllib.error.URLError) as error:
        temporary.unlink(missing_ok=True)
        return f"Cannot fetch {path.name}: {error}"
    return None


def setup(destination: Path) -> str | None:
    """Install the optional CPU backend without changing system packages."""
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        return "Pinned native diarization runtime requires Linux x86_64"
    try:
        destination.mkdir(parents=True, exist_ok=True)
        for path, url, digest in (
            (destination / f"{RUNTIME_NAME}.tar.gz", RUNTIME_URL, RUNTIME_SHA256),
            (destination / MODEL_NAME, MODEL_URL, MODEL_SHA256),
            (
                destination / "Nemotron-3-Diarization-README.md",
                MODEL_CARD_URL,
                MODEL_CARD_SHA256,
            ),
        ):
            error = _fetch(path, url, digest)
            if error:
                return error
        with tarfile.open(destination / f"{RUNTIME_NAME}.tar.gz") as archive:
            archive.extractall(destination, filter="data")
    except (OSError, tarfile.TarError) as error:
        return f"Cannot install native diarization: {error}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    error = setup(args.destination)
    if error:
        parser.error(error)
    print(f"Model: {args.destination / MODEL_NAME}")
    print(f"Runtime: {args.destination / RUNTIME_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
