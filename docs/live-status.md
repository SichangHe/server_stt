# Live transcription status
(authored by agents unless marked 🧑)

Written 13 Oct 2026 by stt_live_fix.md when paused to reduce Claude usage. Delete this file when the open points are closed.

done
- `server-stt-live` rewritten; design in [live](live.md), numbers in [validation](validation.md)
- one context-free code review done; its four findings fixed
- after those fixes: one paced run scored 52/272, file tool 67/272; empty, 1-second, odd-byte, and missing-model inputs behave

open
- independent confirmation by stt_review.md has not been requested yet
  - next step: ask it through the manager to rerun its three `remeasure.py` commands on this commit
- thread default is unresolved
  - 16 threads: no stall in two parallel runs (four processes each); delay medians 5–13 s
  - 32 threads alone: delay medians 5–6 s
  - 32 threads beside the file tool: one recognition step took 67 s instead of about 2.5 s; the 120-second stream finished 100 s late
    - cause unknown; another agent's `remeasure.py` may have been running in this directory at the time
  - an interrupted test compared 16, 32, and 32 with `OMP_WAIT_POLICY=passive`, each beside the file tool; 16 threads had no stall through 72 s when stopped
  - next step: rerun that comparison when the server is otherwise idle of our own runs
- `state.lock` in the repository root is untracked, empty, created 13 Oct 00:09, before this work; no code here or in the installed packages names it; left in place
