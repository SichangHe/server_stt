# final recorded-file measurement after validation fixes
(authored by agents unless marked 🧑)

These reruns use commit `c765026`, which fixes the posterior-mask CLI default
and validates malformed posterior inputs. The valid recognition behavior and
accuracy remain unchanged from `d2002df`.

EN2002a 300–390 s

```sh
timeout 360s uv run --extra multitalker server-stt /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/EN2002a-300-390.wav --output output/file-en2002a-final --language en
timeout 120s uv run --extra multitalker python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/reference.tsv output/file-en2002a-final/transcript.json
```

```text
"reference_words": 366,
"hypothesis_words": 356,
"word_edit_errors": 86,
"speaker_attributed_word_edit_errors": 58,
"speaker_attributed_word_error_fraction": 0.15846994535519127
```

whole ES2004a

```sh
/usr/bin/time -f 'elapsed_s=%e maxrss_kb=%M' timeout 1200s uv run --extra multitalker server-stt /ssd1/sichangheagent/private-artifacts/server-stt/full-ES2004a/ES2004a.mp3 --output output/file-full-final --language en
timeout 180s uv run --extra multitalker python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/full-ES2004a/reference.tsv output/file-full-final/transcript.json
```

```text
Wrote output/file-full-final
elapsed_s=234.32 maxrss_kb=5738484
"reference_words": 2614,
"hypothesis_words": 2530,
"word_edit_errors": 444,
"speaker_attributed_word_edit_errors": 312,
"speaker_attributed_word_error_fraction": 0.11935730680948738,
"speaker_labels": ["SPEAKER_01", "SPEAKER_02", "SPEAKER_03", "SPEAKER_04"]
```
