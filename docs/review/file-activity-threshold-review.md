# review of posterior-mask change
(authored by agents unless marked 🧑)

The review of `c375469..d2002df` found and fixed two correctness issues before
the posterior-mask change was treated as current:

- a parser default of `0.3` made Qwen and Whisper reject every invocation before
  processing; the default is now applied only after selecting multitalker
- posterior validation now rejects nonpositive frame geometry, empty or
  out-of-range arrays, missing speaker columns, and non-`SPEAKER_NN` labels
  before model loading

commands and outputs

```sh
uv run server-stt /tmp/does-not-exist.mp3 --output /tmp/no-output --recognizer qwen
uv run python - <<'PY'
import numpy as np
from server_stt.multitalker import recognize
from server_stt.diarization import DiarizationTurn
a=np.zeros(16000,dtype=np.float32)
turn=[DiarizationTurn(0,1,'SPEAKER_01')]
for probs,frame in [(np.zeros((0,1),dtype=np.float32),.01),(np.ones((2,1),dtype=np.float32)*2,.01),(np.ones((2,1),dtype=np.float32),0)]:
 print(recognize(a,turn,activity=probs,activity_frame_s=frame,activity_threshold=.3))
print(recognize(a,[DiarizationTurn(0,1,'bad')],activity=np.ones((2,1),dtype=np.float32),activity_frame_s=.01,activity_threshold=.3))
PY
uv run ruff check server_stt scripts
uv run basedpyright server_stt
```

```text
server-stt: error: File not found: /tmp/does-not-exist.mp3
Multitalker activity threshold needs finite posterior probabilities and a threshold in (0, 1]
Multitalker activity threshold needs finite posterior probabilities and a threshold in (0, 1]
Multitalker activity threshold needs finite posterior probabilities and a threshold in (0, 1]
Multitalker posterior masks need SPEAKER_NN labels
All checks passed!
0 errors, 0 warnings, 0 notes
```
