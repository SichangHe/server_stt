# Qwen recognition
(authored by agents unless marked 🧑)

CPU recognition
- `recognition.recognize` accepts decoded mono float32 samples at 16 kHz
- Qwen3-ASR-1.7B recognizes independent 20-second chunks
  - no preceding transcript or reference text is supplied
- Qwen3-ForcedAligner-0.6B aligns each generated transcript against its own chunk
  - offsets restore full-file times
  - equal start/end times are retained for downstream point attribution
- word confidence is absent in the SDK; `probability` remains `None`
- model snapshots pin weights, configuration, and tokenizer together
  - SDK model-loading revision arguments do not pin processor loading
- expected dependency, download, and inference failures return error strings

installation
- `uv sync --locked --extra qwen`
- Torch 2.9.1 CPU wheels are resolved from the explicit upstream CPU index
- CPU float32 runs require roughly 12 GB RAM for loaded models and inference
- optional SDK dependencies remain separate from the Whisper installation

measurement
- 20-second chunks improved two 90-second AMI meeting crops over whole-crop recognition
  - actual CLI results and reproduction commands are in [validation](validation.md)
- both crops come from one meeting; they do not establish general accuracy
- evaluation reads reference transcripts only after recognition
