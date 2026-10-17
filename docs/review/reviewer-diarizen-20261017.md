# Reviewer re-check of the DiariZen default
(authored by agents unless marked 🧑)

stt_review.md, 17 Oct 2026, re-measuring `diarizen-heldout-20261015.md` at 78d21b1 from a fresh clone, as a new user would. Outputs: `review-20261012/r6-diarizen` in the server-stt private artifacts directory.

setup as documented: failed, now fixed
- `scripts/setup-diarizen.sh` skipped DiariZen's own step “cd pyannote-audio && pip install -e .[dev,testing] -c ../constraints.txt”
- the default command then failed with `ModuleNotFoundError: No module named 'pyannote'`
- the worker's own environment had it, apparently installed by hand
- the script now installs it; after that the fresh clone ran end to end

claims, speaker-attributed errors
- IS1009a, held-out: 340/1986, confirmed
- TS3003a, held-out: 398/2518, confirmed; worse than the Nemotron default's 377
- EN2002a 300–390 s: 63/366, confirmed; same with the GPU hidden
- ES2004a: claimed 413/2614, labelled “300–420”; that run was the whole meeting from WAV
  - whole meeting from MP3 gave 402/2614; the input format is the likely difference
- net over four meetings: 1203 errors against 1377 for the Nemotron default; the gain comes from IS1009a

caveats
- DiariZen's model card lists AMI among its training data, and all four meetings are AMI; “held-out” means only that this repository did not tune on them
- weights are CC BY-NC 4.0, non-commercial only
- DiariZen silently uses a visible GPU; four concurrent runs ran out of GPU memory

cleanup in the same commit
- the CLI found `scripts/diarizen-turns.py` relative to the working directory; it now resolves it from the package
- removed unreferenced experiment scripts, the unused `envs/diarizen/pyproject.toml`, and the `envs/diarizen/src` gitlink that had no `.gitmodules` (setup clones it)
- the `--activity-threshold` help text named a 0.3 default the code no longer uses
- docs now describe DiariZen as the default
- left as is: basedpyright reports `list[Turn]` passed as `list[DiarizationTurn]` in `cli.py`; this predates this review
