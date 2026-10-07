# Multitalker recognition
(authored by agents unless marked 🧑)

estimated speaker activity
- native Nemotron turns define target and competing-speaker masks at encoder frame times
- overlapping turns activate both masks
- recognize each estimated speaker separately from the same mono recording
  - no enrollment audio, reference text, or reference speaker activity enters inference
- no detected turns returns an empty transcript

bounded CPU recognition
- independent chunks up to 90 seconds bound encoder memory
- native RNNT emission offsets produce word times at 80 ms resolution
  - estimates are not exact acoustic boundaries or forced alignments
- preserve the target speaker on every recognized word
- sort delivered words by start time for readable output
- absent confidence remains `null`
- English only; Qwen remains available for other languages
- duplicated 180-second audio tests chunk offsets and label preservation
  - this does not establish accuracy on continuous long meetings

installation and provenance
- `uv sync --locked --extra multitalker`
- pinned NeMo source archive avoids its Git-source Torch index settings
- explicit Torch CPU wheels prevent installation of the CUDA Torch runtime
- [model card](https://huggingface.co/nvidia/multitalker-parakeet-streaming-0.6b-v1/blob/8749fc71fd6e2d88ef230159bbf2aea69b524ee1/README.md) declares `license_name: nvidia-open-model-license`
  - [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/)
- model revision and checkpoint filename are pinned in `multitalker.py`
- measured accuracy and reproduction commands are in [validation](validation.md)
