# Design
(authored by agents unless marked 🧑)

flow
- validate input paths and new output directory
- decode mono 16 kHz once with PyAV
- identify speech turns and cluster speaker embeddings with Sherpa ONNX
- recognize words with faster-whisper
  - beam search and voice activity filtering
  - word times are model estimates
- assign each word the speaker with greatest overlapping time
  - no overlapping turn means unknown
  - simultaneous voices remain in separate turn intervals
- write Pydantic JSON and grouped text

resources
- full decoded recording stays in memory
  - roughly 230 MB float32 audio per hour
- CPU threads default to four
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
- overlapping words cannot carry multiple recognized voices
- transcription accuracy requires reference evaluation
