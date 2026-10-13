# Request to mac_stt_cx.md: the live tool does not yet meet the human's request
(authored by agents unless marked 🧑)

🧑 "First make the tool that converts an audio file to separated speakers and transcripts reliably, and then Make it also work online in the fly instead of on everything that's already recorded. After that we can consider Mac."

## Goal

Make `server-stt-live` in /ssd1/sichangheagent/server_stt deliver separated speakers and transcripts online, with measured evidence.

## Facts measured by the reviewer on 12 Oct at commit 09d95f0

Recorded in `docs/validation.md` (two 🤖 paragraphs); artifacts in /ssd1/sichangheagent/private-artifacts/server-stt/review-20261012.

- file tool, step 1: whole ES2004a (1049 s) gives 391/2614 speaker-attributed errors (15.0%); this step holds on one full meeting
- live tool, step 2, ES2004a seconds 300–420 (`live120.pcm`, reference `reference-300-420.tsv`):
  - 208/272 speaker-attributed errors (76.5%); file CLI on the same audio: 67/272 (24.6%)
  - 92/272 errors when speaker labels are ignored
  - every 20-second chunk restarts labels at `SPEAKER_01`, so a label does not mean the same voice across chunks
  - `recognize` restores the model from the checkpoint on every chunk (six restores for six chunks)
  - NeMo logs go to stdout among the JSON lines
  - `live_cli.py` skips `offset += ...` when a chunk errors, so later `offset_s` values are wrong
  - `live.py` `run` and `main` are unused; `main` only errors
  - no live measurement existed in `docs/validation.md` before this review
  - latency under real-time paced input is unmeasured

## How the reviewer re-measures each fix

`review-20261012/remeasure.py` in the artifacts directory feeds PCM at real time and prints stdout purity, error lines, cpWER, and word latency (arrival time minus word end time). Run it as `uv run --extra multitalker python remeasure.py AUDIO.wav reference.tsv START_S DURATION_S`. It expects JSON lines holding `words` with `start_s`, `end_s`, `text`, `speaker`, plus an optional per-line `offset_s`; say so if the output format changes.

Baseline at 0249312 with real-time pacing:

- ES2004a 300–420: 208/272, median word latency 31.4 s, max 42.1 s, 816 non-JSON stdout lines
- EN2002a 300–390: 278/366 (file CLI: 66/366), median word latency 35.8 s, max 46.9 s, 680 non-JSON stdout lines

## Review round 1: uncommitted rework in server_stt at 00:35 on 13 Oct

Measured with `remeasure.py` (it now reads word times as absolute stream times); outputs are `r1-es.txt` and `r1-en.txt` in the artifacts directory.

- confirmed, stdout: 0 non-JSON lines on both meetings
- confirmed, model reuse: 120 s of audio finished in 124.7 s wall at real-time pace; median word latency fell from 31.4 s to 21.1 s (ES2004a) and from 35.8 s to 22.7 s (EN2002a); max is still 41.3 s and 48.7 s
- confirmed by reading only, offsets: `offset` now advances on error lines; no error occurred in either run
- rejected, speaker labels: errors are unchanged, 208/272 on ES2004a and 278/366 on EN2002a
  - fact: `canonical` in `live_cli.py` is keyed by the chunk-local label string, so chunk-local `SPEAKER_01` always maps to the same output label whichever voice it is; nothing compares voices between chunks
  - the new README sentence "It keeps canonical labels ... across a process" claims more than this does
- 🧑 development rule "Pass explicit resources instead of global sharing": `_MODEL_CACHE` is a mutable module global
- nothing is committed yet

## Review round 2: uncommitted rework at 00:45 on 13 Oct (re-diarizes the whole history per chunk)

Outputs are `r2-es.txt`, `r2-en.txt`, `r2-es600.txt` in the artifacts directory. `ref600` is `scripts/ami-fixture.py --start-s 0 --duration-s 600`.

- pass, stdout: 0 non-JSON lines in all three runs
- pass, model reuse: still one restore per process (120 s of audio in 125.8 s wall)
- fail, speaker labels and accuracy: ES2004a 300–420 208/272; EN2002a 300–390 232/366 (file CLI 66/366); ES2004a 0–600 886/1107
- fail, new regression: 4 of 6, 3 of 5, and 14 of 30 chunks print `{"error": "Multitalker speaker turns must have finite valid recording times"}` and lose all their words
  - fact: `live_cli.py` shifts history turns by `-offset` without clipping them to the chunk, and `recognize` rejects turns outside `0 <= start_s < end_s <= duration_s + 0.1`
- pass by reading, offsets: `offset` advances on those error lines; later word times stayed plausible
- fail, real-time latency: the 600 s stream took 691.5 s, so it falls behind real time; max word latency 97.3 s, median 29.1 s; history and diarization cost grow with stream length without bound
- nothing is committed yet

## Mac, step 3 (facts from reading mac_stt at 43b89bd and its GitHub runs; nothing was built here)

- GitHub Actions run 37576954140, cited by the evaluator, is the `test` workflow: `sh -n` on four scripts plus `swift test`
- the `macOS feature evidence` run for 43b89bd (37576954114) was cancelled; the last green one, 37575815438, ran on the previous commit with file input on a hosted Mac and warned "ANE power sampling is unsupported; hard acceleration acceptance remains open"
- correction on 13 Oct: an earlier version of this file said `docs/hardware-evidence.md` overclaims; it does not, it defines claim levels, and README already says "File input is not microphone evidence"
- `Package.swift` needs Swift tools 6.0 and macOS 14; the human's toolchain and compile error text are unknown
- untracked `PLAN-mac-stt-acceptance.md` and `state.lock` sit in the working tree

## Wanted result

- live output whose speaker labels stay consistent for the whole stream
- live speaker-attributed error on the audio above, and on EN2002a, reported next to the file CLI's on the same audio, in `docs/validation.md`
- latency measured with input paced at real time
- stdout carries only the result lines
