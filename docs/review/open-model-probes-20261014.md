# official open-weight model probes
(authored by agents unless marked 🧑)

The current default is pinned multitalker Parakeet with Nemotron activity
masks: 58/366 on EN2002a seconds 300–390 and 312/2614 on whole ES2004a.
Official NVIDIA models were downloaded and screened on EN2002a first. Only a
crop winner was run on whole ES2004a. No model beat the whole-meeting default.

## Parakeet TDT v3

Source: `nvidia/parakeet-tdt-0.6b-v3`, revision
`541d1f99c6b0c3cd0b11a95167540bb8edefd82b` (CC-BY-4.0).

```sh
uv run python - <<'PY'
from huggingface_hub import snapshot_download
print(snapshot_download('nvidia/parakeet-tdt-0.6b-v3', allow_patterns=['README.md','*.yaml','*.json']))
PY
timeout 1200s /usr/bin/time -f 'elapsed_s=%e maxrss_kb=%M' uv run --extra multitalker python /tmp/probe_parakeet_score.py 2>&1 | tee /tmp/en2002a-parakeet-tdt.log
timeout 180s uv run python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/reference.tsv output/file-en2002a-parakeet-tdt/transcript.json
```

Output: `elapsed_s=34.79 maxrss_kb=5772352`, 102 word errors and 122
speaker-attributed errors (33.33%). It did not beat 58/366 and was not run
on the whole meeting.

## Sortformer v2.1 diarizer with multitalker

Source: `nvidia/diar_streaming_sortformer_4spk-v2.1`, revision
`cd03eee90fbec18297ac31b8c21546e596b7f71c`.

The model's posterior activity tensor was passed to the existing multitalker
recognizer. Crop commands and exact outputs:

```sh
timeout 1200s uv run --extra multitalker python - <<'PY'
from nemo.collections.asr.models import SortformerEncLabelModel
m=SortformerEncLabelModel.from_pretrained('nvidia/diar_streaming_sortformer_4spk-v2.1',map_location='cpu')
print(type(m))
PY
timeout 1800s /usr/bin/time -f 'elapsed_s=%e maxrss_kb=%M' uv run --extra multitalker python /tmp/probe_sortformer_activity.py 2>&1 | tee /tmp/en2002a-sortformer-activity.log
for t in 0.3 0.5 0.7; do timeout 180s uv run python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/reference.tsv output/file-en2002a-sortformer21-activity-$t/transcript.json; done
```

Crop outputs were 54/366 at threshold 0.3, 60/366 at 0.5, and 61/366 at
0.7. The 0.3 result beat 58/366, so it was run on whole ES2004a:

```sh
timeout 2400s /usr/bin/time -f 'elapsed_s=%e maxrss_kb=%M' uv run --extra multitalker python /tmp/probe_sortformer_full.py 2>&1 | tee /tmp/full-sortformer21-activity03.log
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
