# Server score verdict, 22 Oct 2026
(authored by agents unless marked 🧑)

The four published DiariZen scores reproduce from the saved transcripts and
references. The independent review's four meeting scores and extra EN2002a
CPU score also reproduce. This checks
the scoring evidence; it does not rerun speech recognition.

Evidence paths below are relative to the private `server-stt` artifacts
directory (`../private-artifacts/server-stt` from this repository) unless
prefixed `output/`, which is relative to this repository.
The original claims are in [held-out scores](diarizen-heldout-20261015.md)
and [the independent review](reviewer-diarizen-20261017.md).

## Original scores: verdict per claim

- “ES2004a (whole, WAV) | 413 / 2614 | 15.8%”: confirmed.
  `output/dz-es/transcript.json`, scored against
  `full-ES2004a/reference.tsv`, gives 413/2614 = 15.7995%.
  The transcript records a WAV source and `"duration_s": 1049.3546875`.
- “EN2002a (300–390) | 63 / 366 | 17.2%”: confirmed.
  `output/dz-en/transcript.json` against
  `independent-EN2002a-300-390/reference.tsv` gives 63/366 = 17.2131%.
  The source filename identifies the crop; recorded duration is 90 seconds.
- “TS3003a | 398 / 2518 | 15.8%”: confirmed.
  `output/dz-ts/transcript.json` against `TS3003a/reference.tsv`
  gives 398/2518 = 15.8062%.
- “IS1009a | 340 / 1986 | 17.1%”: confirmed.
  `output/dz-is/transcript.json` against
  `review-20261012/IS1009a/reference.tsv` gives 340/1986 = 17.1198%.

## Independent review: verdict per claim

All reviewed transcripts are under `review-20261012/r6-diarizen` and use
the same meeting references listed above.

- “IS1009a, held-out: 340/1986, confirmed”: confirmed from
  `is/transcript.json`.
- “TS3003a, held-out: 398/2518, confirmed; worse than the Nemotron
  default's 377”: DiariZen confirmed from `ts/transcript.json`.
  The saved baseline score `TS3003a/score.txt` says
  `"speaker_attributed_word_edit_errors": 377` and
  `"reference_words": 2518`; the baseline is checked below.
- “EN2002a 300–390 s: 63/366, confirmed; same with the GPU hidden”:
  both `en/transcript.json` and `en-cpu/transcript.json` give 63/366.
  The latter's log records `elapsed_s=173.45 maxrss_kb=11347784`.
  The log does not record the launch environment, so GPU hiding itself
  cannot be independently established from this evidence.
- “ES2004a: claimed 413/2614, labelled ‘300–420’; that run was the
  whole meeting from WAV”: confirmed. At commit `78d21b1`, the original
  table says `ES2004a (300–420) | 413 / 2614 | 15.8%`; the source
  and duration above contradict that crop label. The current table fixes it.
- “whole meeting from MP3 gave 402/2614; the input format is the likely
  difference”: 402/2614 confirmed from `es/transcript.json`, whose source
  ends in `ES2004a.mp3` and duration is 1049.3546875 seconds.
  Format as the cause remains an inference: these records do not isolate
  format from other execution differences.
- “net over four meetings: 1203 errors against 1377 for the Nemotron
  default; the gain comes from IS1009a”: DiariZen total confirmed:
  402 + 63 + 398 + 340 = 1203. Baselines are checked below.

The saved Nemotron baseline transcripts also reproduce: 391/2614 from
`review-20261012/full/transcript.json`, 377/2518 from
`TS3003a/out3/transcript.json`, and 543/1986 from
`output/run-is/transcript.json`. The EN2002a baseline transcript
`multitalker-cli/server-multitalker-cli-independent/transcript.json`
reproduces 66/366. Its score file
`multitalker-cli/server-multitalker-cli-independent-score.json` records
`"speaker_attributed_word_edit_errors": 66` and `"reference_words": 366`.
Thus 391 + 377 + 543 + 66 = 1377. IS1009a contributes 203 fewer errors;
the other three meetings together contribute 29 more. The comparison joins
historical runs; it is not a new controlled comparison of current defaults.

## Commands and scope of verification

I ran the documented scorer separately on all nine DiariZen pairs and four
baseline pairs, using the current checkout after test commit `1ac3e54`:

```sh
uv run --extra multitalker python scripts/score-ami.py REFERENCE TRANSCRIPT
```

`scripts/score-ami.py` has no changes from `78d21b1`, the reviewed revision.

`REFERENCE` and `TRANSCRIPT` must each be one concrete path from the pairs
above. The original document's exact command,
`uv run --extra multitalker python scripts/score-ami.py REFERENCE.tsv output/dz-*/transcript.json`,
is a template, not an executable command for all four runs: the scorer accepts
exactly two positional arguments, and the glob expands to four transcripts.
Neither source document preserves complete inference commands or environment
settings. Saved transcript metadata supports input identity and duration;
it does not prove that every inference option was the default.

The review's setup failure, manual installation hypothesis, GPU memory
failure, model training/license caveats, and cleanup history are not score
claims. This score audit supplies no independent verdict on those claims.
Likewise, numerical agreement does not establish exclusion from pretraining
or general recording accuracy.
