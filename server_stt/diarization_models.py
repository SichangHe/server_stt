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
MODEL_REPO = "nvidia/Nemotron-3-Diarization"
MODEL_SHA256 = "08456d9e22cd9a323c0364d98375f3746d6e68507ebb705cd46438c534c7a3a1"


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


def model_path() -> Path | str:
    """Fetch the pinned model through the Hugging Face cache (`HF_HUB_CACHE`, `HF_HOME`) and verify it."""
    from huggingface_hub import hf_hub_download

    try:
        path = Path(hf_hub_download(MODEL_REPO, MODEL_NAME, revision=MODEL_REVISION))
        with path.open("rb") as source:
            actual = hashlib.file_digest(source, "sha256").hexdigest()
    except Exception as error:
        return f"Cannot fetch {MODEL_NAME}: {error}"
    return path if actual == MODEL_SHA256 else f"Checksum mismatch: remove {path} and retry"


def setup(destination: Path) -> str | None:
    """Install the optional CPU runtime without changing system packages; the model goes to the Hugging Face cache."""
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        return "Pinned native diarization runtime requires Linux x86_64"
    try:
        destination.mkdir(parents=True, exist_ok=True)
        for path, url, digest in (
            (destination / f"{RUNTIME_NAME}.tar.gz", RUNTIME_URL, RUNTIME_SHA256),
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
    model = model_path()
    if error or isinstance(model, str):
        parser.error(error or str(model))
    print(f"Model: {model}")
    print(f"Runtime: {args.destination / RUNTIME_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
