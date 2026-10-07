# Models and provenance
(authored by agents unless marked 🧑)

The default CPU pipeline is described in [Qwen recognition](qwen-recognition.md) and [native diarization](native-diarization.md). The Whisper/Sherpa models below are the optional legacy pipeline.

The [official Sherpa Python example](https://github.com/k2-fsa/sherpa-onnx/blob/master/python-api-examples/offline-speaker-diarization.py) says “Step 1: Download a speaker segmentation model” and names `sherpa-onnx-pyannote-segmentation-3-0.tar.bz2`. Setup uses that archive and the same project's public `wespeaker_en_voxceleb_resnet34.onnx` release. `server-stt-models` verifies hashes recorded in `server_stt/models.py`.

The segmentation archive includes an MIT license, beginning “Copyright (c) 2022 CNRS”. Setup preserves it beside the model. WeSpeaker's [official pretrained-model documentation](https://github.com/wenet-e2e/wespeaker/blob/master/docs/pretrained.md) lists VoxCeleb ResNet34 language “EN” and says pretrained VoxCeleb models follow “Creative Commons Attribution 4.0 International License.” Attribution: WeSpeaker contributors, VoxCeleb ResNet34 pretrained model, converted release published by Sherpa ONNX contributors. Preserve these notices when redistributing models. The setup default changed from Mandarin ERes2Net after the English model improved the measured speaker result on AMI; that single example does not establish general accuracy.

Whisper recognition weights are downloaded through faster-whisper from Hugging Face, unless `--model` names a local converted model directory. Defaults favor recognition quality; the small-model validation is a functional check, not evidence that large-v3 has achieved an accuracy target.

The [faster-whisper README](https://github.com/SYSTRAN/faster-whisper#requirements) states “The audio is decoded with the Python library PyAV”; its CUDA section requires “cuBLAS for CUDA 12” and “cuDNN 9 for CUDA 12”.
