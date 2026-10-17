#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
uv venv --python 3.11 "$root/envs/diarizen/.venv"
uv pip install --python "$root/envs/diarizen/.venv/bin/python" --index-url https://download.pytorch.org/whl/cu121 torch==2.1.1+cu121 torchaudio==2.1.1+cu121
if [ ! -d "$root/envs/diarizen/src/.git" ]; then git -C "$root/envs/diarizen" clone https://github.com/BUTSpeechFIT/DiariZen.git src; fi
git -C "$root/envs/diarizen/src" checkout 844f555
uv pip install --python "$root/envs/diarizen/.venv/bin/python" -r "$root/envs/diarizen/src/requirements.txt"
uv pip install --python "$root/envs/diarizen/.venv/bin/python" -e "$root/envs/diarizen/src/pyannote-audio" -c "$root/envs/diarizen/src/constraints.txt"
uv pip install --python "$root/envs/diarizen/.venv/bin/python" -e "$root/envs/diarizen/src"
uv pip install --python "$root/envs/diarizen/.venv/bin/python" toml
