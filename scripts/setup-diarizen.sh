#!/bin/sh
set -eu
python3.11 -m venv /tmp/dzvenv
/tmp/dzvenv/bin/pip install torch==2.1.1 torchaudio==2.1.1
/tmp/dzvenv/bin/pip install /tmp/DiariZen
