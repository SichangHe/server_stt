# Measuring `server-stt-live`: paths and exact commands
(authored by agents unless marked 🧑)

For stt_live_fix.md, from stt_review.md. Findings and both failed rework rounds are in `stt_review_live_request.md` beside this file.

Run everything from /ssd1/sichangheagent/server_stt. Below, `P=/ssd1/sichangheagent/private-artifacts/server-stt` and `D=$P/review-20261012`.

## Paths

- script: `$D/remeasure.py`
- ES2004a audio: `$P/full-ES2004a/ES2004a.Mix-Headset.wav` (1049 s), MP3 beside it
- EN2002a audio: `$P/independent-EN2002a-300-390/EN2002a.Mix-Headset.wav`
- references, word times relative to the crop start:
  - `$D/reference-300-420.tsv` (ES2004a 300–420 s, 272 scored words)
  - `$D/reference-0-600.tsv` (ES2004a 0–600 s, 1107 scored words)
  - `$D/reference-full.tsv` (whole ES2004a, 2614 scored words)
  - `$P/independent-EN2002a-300-390/reference.tsv` (EN2002a 300–390 s, 366 scored words)
- past outputs: `$D/base-*.txt` (commit 0249312), `$D/r1-*.txt`, `$D/r2-*.txt`

## Fixture generation

`scripts/ami-fixture.py` only knows ES2004a. Seed a new directory with the downloaded sources so nothing is fetched, then crop:

```sh
mkdir -p output/ref && ln -sf $P/full-ES2004a/ES2004a.Mix-Headset.wav $P/full-ES2004a/ami-manual.zip output/ref/
uv run --extra multitalker python scripts/ami-fixture.py output/ref --start-s 300 --duration-s 120
```

It writes `output/ref/reference.tsv` plus the cropped WAV and MP3. The EN2002a reference was made by `$P/independent-EN2002a-300-390/fixture.py`.

## Real-time pacing, scoring, and lateness: one command per run

```sh
uv run --extra multitalker python $D/remeasure.py $P/full-ES2004a/ES2004a.Mix-Headset.wav $D/reference-300-420.tsv 300 120
uv run --extra multitalker python $D/remeasure.py $P/independent-EN2002a-300-390/EN2002a.Mix-Headset.wav $P/independent-EN2002a-300-390/reference.tsv 300 90
uv run --extra multitalker python $D/remeasure.py $P/full-ES2004a/ES2004a.Mix-Headset.wav $D/reference-0-600.tsv 0 600
```

Arguments are `AUDIO.wav reference.tsv START_S DURATION_S [server-stt-live arguments...]`. The three runs can go in parallel; each lasts about its audio duration.

What the script does:

- pacing: `ffmpeg` crops to mono 16 kHz s16le; a thread writes 0.1 s of PCM every 0.1 s of wall time to `server-stt-live` stdin, then closes it
- stdout purity: counts stdout lines that are not JSON
- error lines: counts JSON lines holding `error`
- scoring: MeetEval cpWER (speaker-attributed word errors) of all words against the reference, with the normalizer of `scripts/score-ami.py`
- lateness: per word, arrival time of its line since the first PCM byte minus the word's `end_s`; prints median, max, min; `wall_s` above the audio duration means the stream fell behind

Format it expects: JSON lines holding `words`, each with `start_s`, `end_s`, `text`, `speaker`; `start_s` and `end_s` are seconds since stream start, not since chunk start.

## File CLI on the same audio, for comparison

```sh
uv run --extra multitalker server-stt output/ref/ES2004a-300-420.mp3 --output output/file-300-420 --language en
uv run --extra multitalker python scripts/score-ami.py output/ref/reference.tsv output/file-300-420/transcript.json
```

Read `speaker_attributed_word_edit_errors`. Measured: 67/272 (ES2004a 300–420), 66/366 (EN2002a 300–390), 391/2614 (whole ES2004a).

## Numbers so far (speaker-attributed errors)

- commit 0249312: 208/272 and 278/366; median word lateness 31.4 s and 35.8 s
- round 2 working tree: 208/272, 232/366, 886/1107; about half the chunks are error lines; the 600 s stream took 691.5 s

## State of /ssd1/sichangheagent/server_stt at 01:03 on 13 Oct

- HEAD is 0249312; the Codex worker's round-2 edits to `README.md`, `docs/validation.md`, `server_stt/live_cli.py`, `server_stt/multitalker.py` are uncommitted in the working tree, with an untracked `state.lock`
- mac_stt_cx.md's task file still said `status: running` at 01:05; the reviewer cannot see whether its process has stopped
