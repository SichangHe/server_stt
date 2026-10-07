# Native diarization
(authored by agents unless marked 🧑)

implementation
- optional CPU backend in `server_stt/diarization.py`
- load versioned C ABI through `ctypes`
  - declare every pointer and return type before calling
  - return expected loading and inference errors as strings
  - close stream before destroying model
- infer overlapping speaker turns and eight-channel probabilities
  - speaker channels have recording-local identity
  - native segment labels start at one; probability columns start at zero
- assign each ASR word the greatest mean speaker probability over its duration
  - ASR already supplies speech evidence; do not apply a second speech threshold
  - timestamps outside the recording stay unknown
  - keep simultaneous speaker intervals in the turn output

inference limits
- full attention for recordings up to 390 seconds
  - NVIDIA's [CLI guide](https://github.com/NVIDIA/NeMo-Speech.cpp/blob/v0.2.0/docs/cli.md) says "The model's positional table limits that path to about 6.6 minutes"
  - 390 seconds leaves six seconds below that approximate limit
- longer recordings use published `v3-offline` streaming geometry
  - the guide says "selects larger streaming chunks and caches; it does not enable full attention"
- feed streaming audio in 30-second blocks and copy new probabilities after each block
  - engineering choice: comfortably shorter than native posterior compaction
  - NVIDIA's [ABI header](https://github.com/NVIDIA/NeMo-Speech.cpp/blob/v0.2.0/include/nemo_speech/diar.h) says "long-lived streams bound their memory by converting older probabilities into final segments"
  - header identifies the compaction horizon as "~20 min"
  - copied probabilities remain in Python memory for later word attribution
- native default segmentation remains unchanged
  - onset 0.641, offset 0.561, edge pads 0.229/0.079 seconds, minimum speech 0.511 seconds, minimum gap 0.296 seconds
  - [native configuration](https://github.com/NVIDIA/NeMo-Speech.cpp/blob/v0.2.0/src/asr/diar/diar_pipeline.h), `DiarSegmentationCfg`

distribution
- `server_stt/diarization_models.py` downloads runtime and model separately
  - Linux x86_64 CPU release `nemo-speech-0.2.0-linux-x86_64-cpu.tar.gz`
  - [NVIDIA release](https://github.com/NVIDIA/NeMo-Speech.cpp/releases/tag/v0.2.0), Apache-2.0 runtime
  - archive includes runtime license, notice, and third-party notices under `share/licenses/nemo-speech`
- [Nemotron-3-Diarization](https://huggingface.co/nvidia/Nemotron-3-Diarization/tree/f667ed73aee57d40cc39428eb768b4fd87a0a29e)
  - revision `f667ed73aee57d40cc39428eb768b4fd87a0a29e`
  - `Nemotron-3-Diarization.q8_0.gguf`, NVIDIA OpenMDW-1.1 model license
  - model card describes "up to eight speakers"
  - setup saves the pinned model card beside the weights, retaining its license identifier and usage information
- SHA-256 values pinned in setup module
  - runtime compared with NVIDIA's published release checksum
  - model compared with Hugging Face's revision-specific LFS object hash
  - verify existing files too; safely extract runtime with bundled notices
- downloaded files stay outside Git

measurement
- preserve overlapping turns for overlap-inclusive diarization error rate
- do not infer delivered transcript quality from reference-word-time speaker errors
  - those scores can penalize correct simultaneous speakers through tie breaking
- compare delivered words and assigned speakers with permutation-invariant word errors
  - reference speaker names are used only for scoring
