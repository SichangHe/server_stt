# Validation
(authored by agents unless marked 🧑)

The English default now uses multitalker Parakeet conditioned on estimated Nemotron speaker activity. Real CLI runs with pinned Torch 2.9.1 CPU produced 31/212 speaker-attributed word errors (14.6%) on ES2004a seconds 300–390 and 27/238 (11.3%) on ES2004a seconds 600–690. No reference words or speaker labels entered inference. These are gains over Qwen's 44/212 and 46/238, but substantial errors remain. The earlier Torch 2.14 component experiment had one fewer error on the second crop; published results use the actual CLI installation.

The actual multitalker CLI on independent EN2002a seconds 300–390 produced 66/366 speaker-attributed errors (18.0%), versus Qwen's 97/366 (26.5%). Across all three crops, errors fell from 187/816 (22.9%) to 124/816 (15.2%). Chronological word-only errors were 41/212, 37/238, and 93/366; that ordering can penalize different serialization of simultaneous words, so cpWER is the primary delivered-speaker-text comparison. The earlier Torch 2.14 component run produced 61 errors on the independent crop; this is not the installed CLI result.

The Qwen comparison used generated-text alignment and Nemotron speaker probabilities on CPU. Real CLI runs used the pinned Torch 2.9.1 CPU installation on two 90-second crops from AMI ES2004a:

- seconds 300–390: 42 word edits / 212 words (19.8%); 44 speaker-attributed word edits (20.8%)
- seconds 600–690: 43 word edits / 238 words (18.1%); 46 speaker-attributed word edits (19.3%)

The previous Whisper/Sherpa pipeline had 73/212 word edits and 99/212 speaker-attributed edits on the first crop; 50/238 and 59/238 on the second. The first baseline supplied the known four-speaker count; the second estimated it. The new pipeline inferred four speakers on both. These improvements do not establish general meeting accuracy: both crops come from one meeting and simultaneous voices remain the main source of missing words. Reference transcripts are read only by evaluation, never by inference or alignment.

The independent Qwen check on AMI EN2002a Mix-Headset seconds 300–390 produced 313 words against 366 normalized reference words: 87 word edits (23.77%) and 97 speaker-attributed edits (26.50%), with four inferred speakers. No reference transcript or known speaker count was supplied to inference. [Source audio](https://huggingface.co/datasets/FluidInference/ami-corpus-mirror/resolve/main/sdm/EN2002a.Mix-Headset.wav) SHA-256: `a15017d0d3c871866971ee178052a0ce3a7e44d6fbf89fc23dcab326511b65f5`; annotations use the same official archive as the ES2004a fixture.

Reproduce the English default:

```sh
uv sync --locked --extra multitalker
uv run --extra multitalker server-stt-diarization-models models
uv run --extra multitalker python scripts/ami-fixture.py output/fixture
uv run --extra multitalker server-stt output/fixture/ES2004a-300-390.mp3 \
  --output output/current --language en
uv run --extra multitalker python scripts/score-ami.py output/fixture/reference.tsv \
  output/current/transcript.json
```

For the second crop, use a new fixture directory and `--start-s 600`. The scorer's `speaker_attributed_word_error_fraction` is MeetEval's concatenated minimum-permutation word error rate (cpWER): recognized words are grouped by predicted speaker and globally matched to reference speakers. It measures word and speaker errors jointly, including omitted words. [MeetEval's README](https://github.com/fgnt/meeteval) lists “Concatenated minimum-Permutation Word Error Rate (cpWER)”. The older word-time speaker score is retained for historical comparisons, but arbitrary overlap tie-breaking can penalize correctly detected simultaneous speakers; it does not judge the delivered words.

The clean JFK MP3 passed through both Qwen and multitalker actual CLIs with one speaker and the expected phrases. Qwen and multitalker word confidence and language confidence are absent and remain `null`; alignment never invents confidence.

A CPU experiment with Microsoft VibeVoice-ASR tested joint text and speaker generation on the same two clips. It produced 46/212 and 40/238 word edits, and 48/212 and 42/238 speaker-attributed edits. Across both clips, its 90 speaker-attributed edits matched Qwen; its 86 word edits exceeded Qwen's 85. Inference took 939 and 905 seconds per 90-second clip. This gave no aggregate accuracy gain and was not adopted. Code revision: `1541f590c7099820f10ea012f48d2399282df69f`; model revision: `d0c9efdb8d614685062c04425d91e01b6f37d944`. Settings were CPU float32, SDPA, 16 threads, greedy generation with 2048 maximum new tokens; no reference text or speaker labels were supplied.

Actual CPU inference processed WAV and MP3 on 2026-10-06. The initial official Sherpa Mandarin fixture produced four distinct labels with the supplied known count. No manual transcript reference was available for that fixture.

The English reference is AMI meeting ES2004a, Mix-Headset seconds 300–390, four participants. `scripts/ami-fixture.py` downloads checksummed AMI audio from a FluidInference mirror and manual word annotations from the official AMI server; generates the 90-second WAV/MP3 and reference timestamps. Credit: AMI Consortium. The [AMI download page](https://groups.inf.ed.ac.uk/ami/download/) states “license altered to CC BY 4.0”; see the [corpus license](https://groups.inf.ed.ac.uk/ami/corpus/license.shtml). Exact URLs and hashes are in the script's `SOURCES`. Audio and generated results are excluded from Git.

The fixture-generation script requires a system `ffmpeg` executable; the transcription CLI itself uses bundled PyAV decoding.

```sh
uv run python scripts/ami-fixture.py output/fixture
uv run server-stt-models models
uv run server-stt output/fixture/ES2004a-300-390.mp3 \
  --output output/validation --language en --recognizer whisper --diarization sherpa \
  --segmentation models/sherpa-onnx-pyannote-segmentation-3-0/model.onnx \
  --embedding models/embedding.onnx
uv run python scripts/score-ami.py output/fixture/reference.tsv \
  output/validation/transcript.json
```

The scorer removes punctuation and lowercases each word, then counts insertion/deletion/substitution edits against 212 reference words. Simultaneous voices are ordered by word onset, which penalizes recognition of only one voice and may penalize a different ordering. The speaker metric assigns each reference word interval the most overlapping predicted speaker and selects the best one-to-one label mapping; this measures speaker mistakes at reference word times, not diarization error rate (DER).

Historical Whisper/Sherpa comparisons on MP3, with CPU int8 recognition:

- `small.en`: 85 word edits (40.1%); `large-v3`: 73 (34.4%)
- initial Mandarin ERes2Net embedding, threshold 0.5: 11 speaker labels, 60 speaker mistakes (28.3%)
- English WeSpeaker embedding, threshold 0.5: 7 labels, 53 mistakes (25.0%)
- English WeSpeaker embedding, threshold 0.8: 5 labels, 44 mistakes (20.8%)

The legacy Sherpa setup selects the English embedding and automatic threshold 0.8 from these comparisons. This is tuning on one short meeting, not independent evidence of general accuracy. Automatic count still overestimates four participants. For Sherpa, prefer a known `--speakers` count; review overlapping speech and transcript omissions. The implementation works end to end, but these measured errors do not support calling its transcripts reliably accurate.

The historical default combination (`large-v3`, English embedding, threshold 0.8) was rerun on MP3: 73 word edits, 44 speaker mistakes, five labels, matching the component comparisons above.

Supplying the known `--speakers 4` with the final models produced four labels and 42 speaker mistakes (19.8%); recognition stayed at 73 word edits. Giving the count fixes overestimation but leaves substantial speaker errors in this meeting.

A focused comparison disabled faster-whisper voice activity filtering while holding the audio, recognition model, CPU precision, language, beam size, and speaker turns constant. It produced 78 word edits (36.8%), worse than the default's 73 (34.4%). Filtering remains enabled; disabling it did not recover missing words in this crop.

A second, clean MP3 check used [OpenAI Whisper's JFK fixture](https://github.com/openai/whisper/blob/main/tests/jfk.flac), source SHA-256 `63a4b1e4c1dc655ac70961ffbf518acd249df237e5a0152faae9a4a836949715`. The final default pipeline returned one speaker and recognized the [upstream test](https://github.com/openai/whisper/blob/main/tests/test_transcribe.py)'s expected phrases “my fellow americans”, “your country”, and “do for you”. This short single-voice case supports basic recognition functionality, not meeting accuracy.

GPU recognition, very long recordings, and non-English use of the English embedding remain unvalidated.
