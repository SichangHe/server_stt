# Design
(authored by agents unless marked 🧑)

flow
- validate input paths and new output directory
- decode mono 16 kHz once with PyAV
- infer overlapping turns with DiariZen in its own environment
  - `--diarization nemotron` uses native Nemotron turns instead
- recognize each speaker with multitalker Parakeet conditioned on estimated activity
  - preserve target labels and native recognition-frame word times
  - independent 90-second chunks bound recognition memory
- optional Qwen recognizes chunks then aligns generated text
- optional Whisper/Sherpa retains beam search and temporal attribution
- preserve simultaneous voices in separate turn intervals and word streams
- write Pydantic JSON and grouped text

resources
- full decoded recording stays in memory
  - roughly 230 MB float32 audio per hour
- CPU threads default to eight
- recognition device is explicit
- segmentation and embeddings run on CPU

model setup
- download public releases
- verify SHA-256 before extracting
- safe tar extraction preserves bundled license
- pin Sherpa core and Python package together
  - newer tested wheel lacked loadable ONNX runtime library
- constrain PyAV below 17
  - installed version 19 rejects faster-whisper's decoding argument

limitations
- anonymous speaker labels have recording-local meaning
- English-trained embeddings require measurement for other languages
- estimated speaker count can overcluster
- chronological text can interleave overlapping voices
- transcription accuracy requires reference evaluation

backend details
- [live transcription](live.md)
  - streaming input, stable labels, delay
- [multitalker recognition](multitalker.md)
- [Qwen recognition](qwen-recognition.md)
- [native diarization](native-diarization.md)
  - CPU runtime, posterior word attribution, distribution, and limits
