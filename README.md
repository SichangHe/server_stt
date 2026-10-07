# Server speech to text
(authored by agents unless marked 🧑)

🧑 “have a separate repo and maybe share a submodule in some way that processes MP3 or similar files into speakers + accurate transcripts, designed to be run on the server. Agents can decide what to name it.”

`server-stt` processes audio files locally into word timestamps, anonymous speaker labels, and readable transcripts. CPU operation requires no account or GPU. MP3, WAV, and other formats supported by PyAV are decoded to mono 16 kHz. Model downloads need internet; inference uses local models after they are cached.

```sh
uv sync --locked --extra multitalker
uv run --extra multitalker server-stt-diarization-models models
uv run --extra multitalker server-stt recording.mp3 --output output/recording --language en
```

The default English pipeline uses multitalker Parakeet in independent 90-second CPU chunks, conditioned on estimated Nemotron-3 speaker activity. It recognizes each speaker separately, including overlapping voices, and returns native word timestamps. Setup requires Linux x86_64; first recognition downloads several gigabytes. Speaker count is inferred, up to eight speakers. Each output directory must be new to avoid replacing previous results. Meeting accuracy is still being improved; the measured limitations are in [validation](docs/validation.md).

Output includes `transcript.txt` and `transcript.json`. JSON preserves speaker turn intervals independently from word labels, including overlapping turns. Multitalker recognition retains the target speaker label for each word; timestamps estimate recognition frames rather than exact acoustic boundaries. Qwen/Whisper use Nemotron mean speaker probabilities or Sherpa turn overlap. Labels describe voices, not identified people. Review the audio before trusting names, numbers, technical terms, and simultaneous speech.

For other languages, install `--extra qwen` and run `uv run --extra qwen server-stt recording.mp3 --output output/recording --recognizer qwen --language zh`. Qwen uses independent 20-second CPU chunks and aligns its generated text; its models require roughly 12 GB RAM. [Recognition details](docs/qwen-recognition.md) describe the optional backend.

The previous lighter Whisper/Sherpa pipeline remains available with `--recognizer whisper --diarization sherpa`. Run `server-stt-models models` and supply `--segmentation models/sherpa-onnx-pyannote-segmentation-3-0/model.onnx --embedding models/embedding.onnx`. Whisper defaults to `large-v3` CPU INT8; `--model small.en` is faster. Its `--speakers` supplies a known count and `--prompt` supplies recognition vocabulary. Optional Whisper CUDA recognition uses `--device cuda --compute-type float16` and the [upstream runtime requirements](https://github.com/SYSTRAN/faster-whisper#gpu); GPU operation has not been validated here.

The Mac repository uses FluidAudio/CoreML; the server uses different model runtimes, so no code submodule is shared.

See [design](docs/design.md), [validation](docs/validation.md), and [model provenance](docs/models.md).
