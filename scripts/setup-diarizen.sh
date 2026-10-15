#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
uv venv --python 3.11 "$root/envs/diarizen/.venv"
uv pip install --python "$root/envs/diarizen/.venv/bin/python" --index-url https://download.pytorch.org/whl/cu121 torch==2.1.1 torchaudio==2.1.1
git -C "$root/envs/diarizen" clone https://github.com/BUTSpeechFIT/DiariZen.git src
git -C "$root/envs/diarizen/src" checkout 844f555
uv pip install --python "$root/envs/diarizen/.venv/bin/python" -e "$root/envs/diarizen/src"
