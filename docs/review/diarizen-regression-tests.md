# DiariZen regression tests
(authored by agents unless marked 🧑)

coverage
- `uv run python -m unittest discover -s tests`
- CLI decodes a real WAV and parses mixed logs and turns from a subprocess
  - real multitalker validation and chunk dispatch receive overlapping speaker turns
  - model loading and neural chunk inference are replaced; no accuracy claim
  - serialized transcript retains speaker labels
- chunk validation rejects durations above 90 s and nonpositive/nonfinite values before loading
- default chunk dispatch splits 181 s into 90, 90, and 1 s with recording offsets
- setup script runs twice in a temporary directory with spaces
  - local command stand-ins avoid network downloads
  - source clones once, pinned checkout and installation repeat, existing file survives
