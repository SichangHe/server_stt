# Reviewer re-check of c765026 (file) and 73ba6e1 (live)
(authored by agents unless marked 🧑)

stt_review.md, 14 Oct 2026, re-measuring stt_file_acc.md's claims in `file-final-c765026.md` and `live-600-73ba6e1.md`. Outputs: `review-20261012/r5*` in the server-stt private artifacts directory.

live, ES2004a 0–600 s, exact 73ba6e1 code, real-time paced, run alone: pass
- 201/1107 speaker-attributed errors (18.2%), same as claimed
- wall 604.3 s; word delay median 4.5 s, max 11.3 s (claimed 3.7 s, 10.0 s)
- 0 non-JSON lines, 0 error lines, four labels
- HEAD changed `multitalker.recognize_chunk` after 73ba6e1, so HEAD's live path is not this measurement

file, HEAD (file code identical to c765026): numbers reproduce exactly; the gain does not hold on a held-out meeting
- whole ES2004a: 312/2614 (11.9%); 444 word errors
- EN2002a 300–390 s: 58/366 (15.8%)
- held-out IS1009a, whole 839 s, AMI evaluation set, never used in tuning
  - c765026: 587/1986 (29.6%)
  - 73ba6e1: 543/1986 (27.3%)
  - the change adds 44 errors here
- inference: the 0.3 posterior threshold and 120 s windows were chosen on ES2004a and EN2002a, the same meetings used to report the gain; IS1009a suggests this is overfitting, though one meeting cannot settle it
- held-out fixture: `review-20261012/IS1009a`, reference built by `heldout_ref.py` there from the AMI manual annotations; source SHA-256 `6eb5a0ede0d9e72794f976ce7bea5b78133eae969f99b4c5418b43c2468d25b1`

next step
- decide file defaults on meetings not used for tuning, e.g. compare 73ba6e1 and c765026 on more AMI evaluation meetings (TS3003a)
