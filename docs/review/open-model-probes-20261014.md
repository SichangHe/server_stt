# official open-weight model probes
(authored by agents unless marked 🧑)

The current default is pinned multitalker Parakeet with Nemotron activity
masks: 58/366 on EN2002a seconds 300–390 and 312/2614 on whole ES2004a.
Official NVIDIA models were downloaded and screened on EN2002a first. Only a
crop winner was run on whole ES2004a. No model beat the whole-meeting default.
The reproducible probe scripts are committed beside this evidence.

## Parakeet TDT v3

Source: `nvidia/parakeet-tdt-0.6b-v3`, revision
`541d1f99c6b0c3cd0b11a95167540bb8edefd82b` (CC-BY-4.0).

```sh
set -e -o pipefail
uv run python - <<'PY'
from huggingface_hub import snapshot_download
print(snapshot_download('nvidia/parakeet-tdt-0.6b-v3', revision='541d1f99c6b0c3cd0b11a95167540bb8edefd82b'))
PY
timeout 1200s /usr/bin/time -f 'elapsed_s=%e maxrss_kb=%M' uv run --locked --extra multitalker python scripts/review-parakeet-tdt.py 2>&1 | tee /tmp/en2002a-parakeet-tdt.log
timeout 180s uv run python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/reference.tsv output/file-en2002a-parakeet-tdt/transcript.json
```

The download printed the pinned Hugging Face snapshot under
`~/.cache/huggingface/hub/models--nvidia--parakeet-tdt-0.6b-v3`; the inference
command printed NeMo model-load logs and completed with the timing shown below.

Output: `elapsed_s=34.79 maxrss_kb=5772352`, 102 word errors and 122
speaker-attributed errors (33.33%). It did not beat 58/366 and was not run
on the whole meeting.

## Sortformer v2.1 diarizer with multitalker

Source: `nvidia/diar_streaming_sortformer_4spk-v2.1`, revision
`cd03eee90fbec18297ac31b8c21546e596b7f71c`.

The model's posterior activity tensor was passed to the existing multitalker
recognizer. Crop commands and exact outputs:

```sh
set -e -o pipefail
timeout 1200s uv run --locked --extra multitalker python - <<'PY'
from nemo.collections.asr.models import SortformerEncLabelModel
m=SortformerEncLabelModel.from_pretrained('nvidia/diar_streaming_sortformer_4spk-v2.1',revision='cd03eee90fbec18297ac31b8c21546e596b7f71c',map_location='cpu')
print(type(m))
PY
timeout 1800s /usr/bin/time -f 'elapsed_s=%e maxrss_kb=%M' uv run --locked --extra multitalker python scripts/review-sortformer-activity.py 2>&1 | tee /tmp/en2002a-sortformer-activity.log
for t in 0.3 0.5 0.7; do timeout 180s uv run python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/reference.tsv output/file-en2002a-sortformer21-activity-$t/transcript.json; done
```

The model-load command printed
`<class 'nemo.collections.asr.models.sortformer_diar_models.SortformerEncLabelModel'>`.

Crop outputs were 54/366 at threshold 0.3, 60/366 at 0.5, and 61/366 at
0.7. The 0.3 result beat 58/366, so it was run on whole ES2004a:
The checked-in scripts were rerun after pinning; the three crop scores were
unchanged.

```sh
set -e -o pipefail
timeout 2400s /usr/bin/time -f 'elapsed_s=%e maxrss_kb=%M' uv run --locked --extra multitalker python scripts/review-sortformer-full.py 2>&1 | tee /tmp/full-sortformer21-activity03.log
timeout 360s uv run python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/full-ES2004a/reference.tsv output/file-full-sortformer21-activity03/transcript.json
```

Output: `elapsed_s=317.02 maxrss_kb=6450696`, 564 word errors and 742
speaker-attributed errors (28.39%). This is worse than 312/2614, so the
default remains unchanged.

## additional Sortformer checks

Official `nvidia/diar_sortformer_4spk-v1` revision
`2617bffbd820aa29d8f1fb6ab6f9ed7f0adbc996` with Whisper large-v3 produced
136/366 speaker-attributed errors. v2.1 binary turns with Whisper produced
64/366. Neither beat 58/366 and neither was run on whole ES2004a.

The private review fixtures are identified by these SHA-256 hashes:

```text
cb1aad210919ca0363be273b77afe1fdc2319685712efc23d80fd64a01390d5a  independent-EN2002a-300-390/EN2002a-300-390.wav
93dde0fab030a610ebc99b75d17d62d9dc6a070f786a0b18b605bf97812245d2  independent-EN2002a-300-390/reference.tsv
083746dee46bb285781233cbcd1edaf9dcdd256848d4089a0f69fde2a96974d6  full-ES2004a/ES2004a.mp3
2a6fcaef2b0403a1f4e838ffec8f36808ba3c83ef08bbb32f298fb8b91df51c6  full-ES2004a/reference.tsv
```
