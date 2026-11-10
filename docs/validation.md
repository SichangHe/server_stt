# Validation
(authored by agents unless marked 🧑)

Current default (DiariZen turns, 90-second hard-turn masks), measured on 17 Oct 2026 from a fresh clone after `uv sync --locked --extra multitalker` and `sh scripts/setup-diarizen.sh`, with the normal `server-stt` command and `scripts/score-ami.py`. Speaker-attributed errors, previous Nemotron default in parentheses:

- IS1009a, whole: 340/1986 (543)
- TS3003a, whole: 398/2518 (377)
- ES2004a, whole MP3: 402/2614 (391)
- EN2002a 300–390 s: 63/366 (66); the same with the GPU hidden, 173 s wall

IS1009a and TS3003a were not used to choose settings in this repository. DiariZen's model card says its training data includes AMI, the corpus of all four meetings; whether these meetings were excluded is unverified. DiariZen used the GPU in these runs; four runs at once ran out of GPU memory.

GPU execution, 9 Nov 2026 (real CLI, default DiariZen + multitalker, whole-meeting MP3, `--device auto` resolving to cuda on one RTX A6000 shared with other jobs; scorer `scripts/score-meeting.py`, reference from `scripts/ami-meeting.py`):

- ES2004a (1049 s): cpWER 0.1538 (402/2614), speaker-blind WER 0.1756, DER 0.2128; 182.1 s wall, 3.9 GB peak RSS. Equals the earlier CPU figure (402/2614); not rerun on CPU.
- IS1009a (839 s): cpWER 0.2145 (426/1986), DER 0.1466; 92.2 s wall. CPU rerun the same day, `--device cpu --threads 16`, on a loaded server (load average about 70): identical cpWER 0.2145 and DER 0.1466, 1233.7 s wall, 12.8 GB peak RSS (13x slower). The 340/1986 above is an earlier figure that the same-day rerun did not reproduce; the cause is unknown (scorer normalisation or crop handling differ).
- EN2002a (2143 s, heavy overlap): cpWER 0.2598 (1953/7516), DER 0.2920; 190.0 s wall. No earlier whole-meeting CPU figure; not rerun on CPU.

DER is approximate: the reference is word intervals bridged over gaps under 0.5 s, collar 0.25 s, not official AMI RTTM. AMI is in DiariZen's training data, so these are not held-out. A prototype (DiariZen + per-speaker Parakeet-TDT, since deleted) scored cpWER 0.2104, 0.2442 and 0.3417 on the same three meetings; multitalker is better on all three.

Open-license diarizer comparison, 10 Nov 2026 (whole-meeting MP3, GPU multitalker, same scorer `scripts/score-meeting.py`, reference from `scripts/ami-meeting.py`; one run each; DER approximate as described below). cpWER / DER. DiariZen is the figure above; Nemotron is the default CLI with `--activity-threshold 0.3` (hard turns in parentheses); Sortformer from `scripts/sortformer-meeting.py` with the same two mask modes.

- DiariZen (weights CC BY-NC 4.0, not commercial): ES2004a 0.1538 / 0.2128; IS1009a 0.2145 / 0.1466; EN2002a 0.2598 / 0.2920
- Nemotron-3 Diarization (OpenMDW-1.1, commercial use allowed): ES2004a 0.1201 (0.1484) / 0.1359; IS1009a 0.2175 (0.2613) / 0.1122; EN2002a 0.2181 (0.2319) / 0.1886
- Sortformer 4spk v2.1 (NVIDIA Open Model License): ES2004a 0.2995 (0.2930) / 0.3616; IS1009a 0.3359 (0.3026) / 0.1920; EN2002a 0.2251 (0.2328) / 0.2929
- Sortformer 4spk v2 (CC-BY-4.0): ES2004a 0.1423 (0.1503) / 0.2243; IS1009a 0.3656 (0.3510) / 0.3132; EN2002a 0.2319 (0.2350) / 0.2666

Decision: Nemotron with threshold 0.3 is the default. It beats DiariZen on ES2004a and EN2002a and is 0.003 worse on IS1009a. pyannote community-1 and 3.1 were not measured: their gated terms are not accepted on the Hugging Face account. Not measured, not claimed: held-out status (AMI is in some models' training data).

Recognizer comparison, same meetings, Nemotron turns, threshold-free Qwen word-to-turn speaker assignment on the GPU (`--recognizer qwen --device cuda`), cpWER vs multitalker Parakeet: ES2004a 0.2223 vs 0.1201; IS1009a 0.2905 vs 0.2175; EN2002a 0.3528 vs 0.2181. Qwen3-ASR-1.7B is clearly worse here, so multitalker Parakeet stays the default. Qwen wall time 238 s, 141 s, 487 s.

Earlier defaults, kept as history:

The English default now uses multitalker Parakeet conditioned on estimated Nemotron speaker activity. Real CLI runs with pinned Torch 2.9.1 CPU produced 31/212 speaker-attributed word errors (14.6%) on ES2004a seconds 300–390 and 27/238 (11.3%) on ES2004a seconds 600–690. No reference words or speaker labels entered inference. These are gains over Qwen's 44/212 and 46/238, but substantial errors remain. The earlier Torch 2.14 component experiment had one fewer error on the second crop; published results use the actual CLI installation.

The actual multitalker CLI on independent EN2002a seconds 300–390 produced 66/366 speaker-attributed errors (18.0%), versus Qwen's 97/366 (26.5%). Across all three crops, errors fell from 187/816 (22.9%) to 124/816 (15.2%). Chronological word-only errors were 41/212, 37/238, and 93/366; that ordering can penalize different serialization of simultaneous words, so cpWER is the primary delivered-speaker-text comparison. The earlier Torch 2.14 component run produced 61 errors on the independent crop; this is not the installed CLI result.

🤖 Review on 12 Oct 2026 at commit 09d95f0 ran the installed CLI on the whole 1049-second ES2004a MP3: 391/2614 speaker-attributed errors (15.0%), 512/2614 chronological word errors, 8 min 48 s wall time and 5.7 GB peak memory on a shared 128-core CPU server. The reference came from `scripts/ami-fixture.py --start-s 0 --duration-s 3600`. This is one meeting; other recordings are unmeasured.

The file CLI now recognizes independent 120-second windows, within the model's 120-second batched-row bound. On the same whole ES2004a MP3 and reference, commit `c375469` produced 352/2614 speaker-attributed errors (13.5%), 479 chronological word errors, 246.1 s wall time, and 5.5 GB peak resident memory. A 0.3 Nemotron posterior activity threshold then reduced this to 312/2614 (11.9%), retained by the validation-fixed commit `c765026`; the final rerun used 234.32 s wall time and 5.5 GB peak resident memory. Exact commands and outputs are in [file-final-c765026](review/file-final-c765026.md). This remains one-meeting evidence.

🤖 The same review piped ES2004a seconds 300–420 as PCM into `server-stt-live` with defaults: 208/272 speaker-attributed errors (76.5%), against 67/272 (24.6%) for the file CLI on the same 120 seconds. Ignoring speaker labels, live had 92/272 errors. Each 20-second chunk restarted labels at `SPEAKER_01`, restored the model again (six restores), and wrote NeMo logs to stdout among the JSON lines. Input came from a file without real-time pacing, so latency is unmeasured; the run took 137 seconds for 120 seconds of audio including startup.

🤖 After the live rewrite (one persistent speaker stream, sliding recognition window; [live design](live.md)), the same reviewer script `remeasure.py`, which feeds PCM at real time, gave these developer-run results on 13 Oct 2026 with 16 threads, three streams and one file-tool run in parallel on the shared server. No stdout line was non-JSON and no line was an error. The independent reviewer has not yet confirmed them.

- ES2004a 300–420 s: 51/272 speaker-attributed errors (18.8%); word delay median 8.2 s, max 20.4 s
- EN2002a 300–390 s: 65/366 (17.8%); delay median 12.5 s, max 28.4 s
- ES2004a 0–600 s: 201/1107 (18.2%); delay median 5.4 s, max 14.1 s; 608 s wall time

Word delay is arrival time since the first PCM byte minus the word's end time. The maximum is the first words, which wait about 20 s for model loading. The file tool scored 67/272 on the first crop before and after the recognizer refactor.

Controlled Torch 2.14 component comparisons retained the default hard speaker activity and greedy decoding. Across the same 816 reference words, hard turns gave 118 errors; continuous probabilities gave 152, binary probability thresholds 0.5 and 0.3 gave 119 and 117. The one-edit aggregate gain at 0.3 worsened the first clip by two errors, so it was not promoted. Beam size four gave 120 errors versus greedy's 118 with the same decoder thread count. These exploratory comparisons do not replace the installed CLI measurements above.

Independent 30-second recognition chunks gave 33/212, 24/238, and 70/366 errors, totaling 127/816 versus 118/816 with 90-second chunks in the same component environment. The shorter context was not adopted. This test exposed rounding at the allowed one-frame timestamp boundary (`30.080000000000002` versus `30.08`); a one-nanosecond numerical tolerance now prevents rejection without expanding the meaningful timing range. Real reruns confirmed ordered, bounded output times.

The actual CLI residual audit counted 45 deletions, 62 substitutions, and 17 insertions. An approximate greedy utterance-assignment score gave 120 errors versus cpWER's 124, suggesting predominantly lexical errors; this is not an exact speaker-error decomposition. Fifteen deleted/substituted reference words had no inferred target activity, mostly far from turn boundaries. Small boundary padding therefore does not address the dominant observed failures. Reference annotations diagnose these errors only during evaluation. Precise acoustic word boundaries remain unvalidated; native emission times can trail speech and span pauses.

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

The [official AMI Full-corpus-ASR partition](https://groups.inf.ed.ac.uk/ami/corpus/datasets.shtml) lists “SC (UNSEEN DATA FOR EVALUATION): ES2004, IS1009, TS3003, EN2002”. Both tested meetings belong to that recommended evaluation partition. NVIDIA's [pinned model card](https://huggingface.co/nvidia/multitalker-parakeet-streaming-0.6b-v1/blob/8749fc71fd6e2d88ef230159bbf2aea69b524ee1/README.md) lists “AMI Corpus” under “Training Datasets (Real conversations)” without specifying excluded meeting IDs. The independent meeting was held out from our tuning; exclusion from pretrained training is unverified.

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
