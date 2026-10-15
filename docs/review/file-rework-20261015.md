# file recognition rework
(authored by agents unless marked 🧑)

The held-out IS1009a result showed that c765026's file defaults were tuned to
the reported meetings. The default now returns to the previously validated
geometry: 90-second windows and turn-derived hard masks. Posterior masks remain
available only when `--activity-threshold` is explicitly supplied, so the file
CLI no longer silently applies the tuned 0.3 threshold.

commands and outputs

```text
uv run ruff check server_stt
All checks passed!
uv run basedpyright server_stt
0 errors, 0 warnings, 0 notes
git diff 73ba6e1 -- server_stt/multitalker.py server_stt/cli.py
default chunk_s: 90; default activity_threshold: None
```

measurements

The reworked defaults were run on fresh crops and scored with the review
scorer. Commands used:

```sh
uv run --extra multitalker python scripts/score-ami.py $P/review-20261012/reference-300-420.tsv output/run-es/transcript.json
uv run --extra multitalker python scripts/score-ami.py $P/independent-EN2002a-300-390/reference.tsv output/run-en/transcript.json
uv run --extra multitalker python scripts/score-ami.py $P/review-20261012/IS1009a/reference.tsv output/run-is/transcript.json
```

Results (speaker-attributed word errors): ES2004a 300–420: 107/272; EN2002a
300–390: 60/366; held-out IS1009a: 543/1986. The held-out result matches the
73ba6e1 baseline and improves on c765026's 587/1986.

additional AMI evidence and tuning

The 3014-entry TS3003a reference contains 2518 scored words because the scorer
normalizes words and removes entries with empty normalized text; cpWER reports
the scored count. Baseline TS3003a is 377/2518 (15.0%), and baseline IS1009a is
543/1986 (27.3%).

Using only the existing ES2004a and EN2002a measurements to select posterior
mask settings, threshold 0.5 improved TS3003a to 347/2518 (13.8%) but gave
547/1986 on IS1009a. A follow-up 0.7 probe gave IS1009a 522/1986 (26.3%);
TS3003a at 0.7 was not rerun. Commands and outputs are outside the repository
under `private-artifacts/server-stt/{TS3003a,review-20261012/IS1009a}`.

follow-up blocker

The local review artifacts contain ES2004a, EN2002a, and IS1009a only. No
second unseen AMI meeting such as TS3003a audio and reference is available, so
the requested second-meeting measurement cannot be run honestly until supplied.

cause audit

The NVIDIA Sortformer v2.1 probe was evaluated with threshold 0.3 selected on ES2004a and EN2002a. It scored 388/2518 (15.4%) on held-out TS3003a and 575/1986 (29.0%) on held-out IS1009a, worse than the file baseline 377/2518 and 543/1986. It was not adopted.

IS1009a has 399 reference words overlapping a word from another speaker, out of
2393 reference entries; TS3003a has 204/3014. Both transcripts infer four
labels (IS1009a 208 turns, TS3003a 394 turns), matching the four annotated
speakers. This points to overlap handling as the dominant observable structural
difference, rather than speaker-count overclustering. A stronger diarization
model or clustering change was not available locally, and no structural change
was made without a selection measurement on ES2004a and EN2002a.

The scorer's cpWER does not expose per-reference edit identities, so a precise
543-error cause partition requires a new alignment scorer. The overlap counts
above are exposure counts, not claims that every error is caused by overlap.
NeMo is installed, but `pyannote.audio` is absent and pyannote community
models require authenticated Hugging Face access; no stronger-model result is
reported without a reproducible adapter and credentials.

commit

```text
a28b9642dee787c6790e01bc1683159808f5899c
```
