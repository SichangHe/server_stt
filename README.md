# Server speech to text
(authored by agents unless marked 🧑)

🧑 “have a separate repo and maybe share a submodule in some way that processes MP3 or similar files into speakers + accurate transcripts, designed to be run on the server. Agents can decide what to name it.”

`server-stt` processes audio files locally into word timestamps, anonymous speaker labels, and readable transcripts. CPU operation requires no account or GPU. MP3, WAV, and other formats supported by PyAV are decoded to mono 16 kHz. Model downloads need internet; inference uses local models after they are cached.

```sh
uv sync --locked
uv run server-stt-models models
uv run server-stt recording.mp3 --output output/recording \
  --segmentation models/sherpa-onnx-pyannote-segmentation-3-0/model.onnx \
  --embedding models/embedding.onnx
```

The default recognition model is `large-v3` with CPU `int8`; its first run downloads several gigabytes. For a faster initial check, add `--model small.en --language en`. Use `--speakers 4` when the count is known; otherwise clustering estimates it. `--prompt 'technical vocabulary'` supplies recognition context. Each output directory must be new to avoid replacing previous results.

Output includes `transcript.txt` and `transcript.json`. JSON preserves speaker turn intervals independently from word labels, including overlapping turns. Words receive the speaker with greatest overlap; words without overlap have `null` speaker. Labels describe voices, not identified people. Review the audio before trusting names, numbers, technical terms, and simultaneous speech.

CUDA recognition: add `--device cuda --compute-type float16`; install the CUDA 12/cuDNN 9 runtime described in [faster-whisper's requirements](https://github.com/SYSTRAN/faster-whisper#gpu). Speaker processing remains on CPU. GPU operation has not been validated here.

The server implementation uses faster-whisper/CTranslate2 and Sherpa ONNX. The Mac repository uses FluidAudio/CoreML, so no code submodule is shared. Both implementations consume audio, but their model runtimes differ.

See [design](docs/design.md), [validation](docs/validation.md), and [model provenance](docs/models.md).
