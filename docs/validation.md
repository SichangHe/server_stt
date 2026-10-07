# Validation
(authored by agents unless marked 🧑)

Actual CPU inference processed WAV and MP3 on 2026-10-06. The initial official Sherpa Mandarin fixture produced four distinct labels with the supplied known count. No manual transcript reference was available for that fixture.

The English reference is AMI meeting ES2004a, Mix-Headset seconds 300–390, four participants. `scripts/ami-fixture.py` downloads checksummed AMI audio from a FluidInference mirror and manual word annotations from the official AMI server; generates the 90-second WAV/MP3 and reference timestamps. Credit: AMI Consortium. The [AMI download page](https://groups.inf.ed.ac.uk/ami/download/) states “license altered to CC BY 4.0”; see the [corpus license](https://groups.inf.ed.ac.uk/ami/corpus/license.shtml). Exact URLs and hashes are in the script's `SOURCES`. Audio and generated results are excluded from Git.

The fixture-generation script requires a system `ffmpeg` executable; the transcription CLI itself uses bundled PyAV decoding.

```sh
uv run python scripts/ami-fixture.py output/fixture
uv run server-stt-models models
uv run server-stt output/fixture/ES2004a-300-390.mp3 \
  --output output/validation --language en \
  --segmentation models/sherpa-onnx-pyannote-segmentation-3-0/model.onnx \
  --embedding models/embedding.onnx
uv run python scripts/score-ami.py output/fixture/reference.tsv \
  output/validation/transcript.json
```

The scorer removes punctuation and lowercases each word, then counts insertion/deletion/substitution edits against 212 reference words. Simultaneous voices are ordered by word onset, which penalizes recognition of only one voice and may penalize a different ordering. The speaker metric assigns each reference word interval the most overlapping predicted speaker and selects the best one-to-one label mapping; this measures speaker mistakes at reference word times, not diarization error rate (DER).

Measured comparisons on MP3, with CPU int8 recognition:

- `small.en`: 85 word edits (40.1%); `large-v3`: 73 (34.4%)
- initial Mandarin ERes2Net embedding, threshold 0.5: 11 speaker labels, 60 speaker mistakes (28.3%)
- English WeSpeaker embedding, threshold 0.5: 7 labels, 53 mistakes (25.0%)
- English WeSpeaker embedding, threshold 0.8: 5 labels, 44 mistakes (20.8%)

Setup selects the English embedding and automatic threshold 0.8 from these comparisons. This is tuning on one short meeting, not independent evidence of general accuracy. Automatic count still overestimates four participants. Prefer a known `--speakers` count; review overlapping speech and transcript omissions. The implementation works end to end, but these measured errors do not support calling its transcripts reliably accurate.

The final default combination (`large-v3`, English embedding, threshold 0.8) was rerun on MP3: 73 word edits, 44 speaker mistakes, five labels, matching the component comparisons above.

Supplying the known `--speakers 4` with the final models produced four labels and 42 speaker mistakes (19.8%); recognition stayed at 73 word edits. Giving the count fixes overestimation but leaves substantial speaker errors in this meeting.

A second, clean MP3 check used [OpenAI Whisper's JFK fixture](https://github.com/openai/whisper/blob/main/tests/jfk.flac), source SHA-256 `63a4b1e4c1dc655ac70961ffbf518acd249df237e5a0152faae9a4a836949715`. The final default pipeline returned one speaker and recognized the [upstream test](https://github.com/openai/whisper/blob/main/tests/test_transcribe.py)'s expected phrases “my fellow americans”, “your country”, and “do for you”. This short single-voice case supports basic recognition functionality, not meeting accuracy.

GPU recognition, very long recordings, and non-English use of the English embedding remain unvalidated.
