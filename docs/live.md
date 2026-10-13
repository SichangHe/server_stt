# Live transcription
(authored by agents unless marked 🧑)

🧑 "Make it also work online in the fly instead of on everything that's already recorded"

interface
- `server-stt-live` reads raw mono 16 kHz signed 16-bit PCM on stdin until it closes
- stdout carries only JSON lines
  - `{"words": [...]}`: `start_s`, `end_s`, `text`, `speaker`, `probability` (always `null`)
    - times are seconds since stream start
    - every word is delivered once and never revised
  - `{"error": "..."}` is fatal; exit status 1
- library output and one `step:` timing line per recognition step go to stderr
  - file descriptor 1 is redirected to stderr at startup; JSON uses a private copy

flow
- `live_cli.py`: input and output only
  - a reader thread forwards arriving PCM through a queue; it shares no other state
  - the main loop takes all audio that has arrived as one batch
    - audio arriving during model loading or a slow step is not lost; the next step is larger
- `live.py` `transcribe`: one step per batch, no wall-clock dependence
  - push the batch into one persistent Nemotron stream (`DiarizationStream`)
    - one stream for the whole recording keeps each speaker label on the same voice
  - labeled end: the time up to which the stream has assigned speakers
  - skip the step until `MIN_STEP_S` of new audio lies before labeled end minus `HOLD_S`
  - recognize the window from `CONTEXT_S` before the last emitted time to the labeled end
    - `multitalker.recognize_chunk`, all speakers with a turn in the new part in one batch
    - earlier audio only gives the recognizer context
  - emit words whose start lies between the last emitted time and labeled end minus `HOLD_S`
    - held-back words are recognized again next step with settled turns and lookahead
  - at end of input: finish the stream and emit everything left
- only `CONTEXT_S` plus unprocessed audio is kept
  - a backlog makes the next window longer; nothing caps it

settings, in `live_cli.py`
- `DIARIZATION_CHUNK_FRAMES = 39`, 3.1 s native chunks
  - the model default of 13 cost 0.5 s of CPU per second of audio; the stream fell behind
  - 39 cost 0.17 s per second and labels up to 3.2 s behind the audio
- `CONTEXT_S = 10`, `HOLD_S = 1`, `MIN_STEP_S = 1`
  - the recognizer attends 5.6 s back and 1.04 s ahead per layer
  - contexts 6, 10, 15 s and holds 1, 2 s gave 49–57 errors of 272 on one crop
    - differences are within run-to-run variation; shorter context and hold lower delay
  - turn stability was only tested 2 s behind the labeled end; a 1 s hold can fix a label that the stream later changes
- `--threads` defaults to 16
  - unresolved: 32 threads halved delay when run alone but stalled once beside other load; see [status](live-status.md)
  - a 14-second window with four speakers took 3.5–4.8 s at 16 threads in paced runs on a shared 64-core server, 2.8 s at 32 in a timing run
- default model paths are relative to the working directory

limits
- words arrive several seconds after they are spoken; see [validation](validation.md)
  - first words wait for model loading, about 20 s on the test server
- word boundary at the emit cut: a word whose estimated start moves across the cut between two steps can be dropped or repeated
- English only; at most eight speakers; speaker labels are stream-local
- CPU only; sustained delay depends on free cores
