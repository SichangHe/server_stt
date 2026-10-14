# Review status
(authored by agents unless marked 🧑)

Written by the reviewer stt_review.md at 04:10 on 13 Oct 2026, when stopped to reduce Claude usage.

where the review stands
- live tool at commit 73ba6e1, re-measured by the reviewer with real-time paced input
  - ES2004a 300–420 s: 50/272 speaker-attributed errors; file tool 67/272
  - EN2002a 300–390 s: 68/366; file tool 66/366
  - word delay median 5.7 s and 8.5 s, max 23.1 s and 28.4 s
    - the max is the first words, which wait for model loading
  - 0 non-JSON stdout lines, 0 error lines, wall time 122.3 s for 120 s and 96.1 s for 90 s
  - every gap of the earlier rounds passes on these two crops: speaker labels, model reuse, stdout, real-time latency
  - offsets after an error line are untested: errors are now fatal
- ES2004a 0–600 s was measured only on the working tree shortly before the commit, with two other runs in parallel
  - 199/1107, 604.7 s wall, median delay 5.6 s, max 171.3 s
  - whether that tree equals 73ba6e1 is unverified, and the max is inflated by the parallel load
- file tool, whole ES2004a at 09d95f0: 391/2614 (15.0%)
- Mac repository: reviewed by reading only; no change made
- the reviewer has not read the new live code for quality, only measured it

next step
- ES2004a 0–600 s was re-run alone on 73ba6e1; evidence is in [live-600-73ba6e1](review/live-600-73ba6e1.md)
- review the diff 0249312..73ba6e1 for code quality
- commands and paths: `stt_review_measurement_commands.md` and `stt_review_live_request.md` in the agents' work log directory; outputs `r4-*.txt` in the `review-20261012` artifacts directory
