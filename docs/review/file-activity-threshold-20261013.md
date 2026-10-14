# recorded-file accuracy with posterior activity threshold
(authored by agents unless marked 🧑)

The file CLI now defaults to a 0.3 threshold on Nemotron speaker posterior
activity when building Parakeet target and background masks. The live path is
unchanged and still uses its settled hard turns.

commit

The implementation commit is `d2002df` (`feat: condition file recognition on posterior activity`).

commands

```sh
timeout 360s uv run --extra multitalker server-stt /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/EN2002a-300-390.wav --output output/file-en2002a-th03-crop --language en --activity-threshold 0.3
timeout 120s uv run --extra multitalker python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/reference.tsv output/file-en2002a-th03-crop/transcript.json
/usr/bin/time -f 'elapsed_s=%e maxrss_kb=%M' timeout 1200s uv run --extra multitalker server-stt /ssd1/sichangheagent/private-artifacts/server-stt/full-ES2004a/ES2004a.mp3 --output output/file-full-120-th03 --language en --activity-threshold 0.3
timeout 180s uv run --extra multitalker python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/full-ES2004a/reference.tsv output/file-full-120-th03/transcript.json
```

outputs

EN2002a 300–390 s:

```text
"reference_words": 366,
"hypothesis_words": 356,
"word_edit_errors": 86,
"speaker_attributed_word_edit_errors": 58,
"speaker_attributed_word_error_fraction": 0.15846994535519127
```

Whole ES2004a:

```text
Wrote output/file-full-120-th03
elapsed_s=246.56 maxrss_kb=6124232
"reference_words": 2614,
"hypothesis_words": 2530,
"word_edit_errors": 444,
"speaker_attributed_word_edit_errors": 312,
"speaker_attributed_word_error_fraction": 0.11935730680948738
```

The previous file default at commit `c375469` scored 352/2614 on whole
ES2004a and the earlier 90-second baseline scored 66/366 on EN2002a. The
threshold therefore reduced errors by 40 on ES2004a and 8 on EN2002a in these
runs.

An initial command accidentally used the untrimmed 2142.7-second EN2002a source
with the 300–390-second reference; its 6794/366 score is invalid and was not
used. The crop command above is the valid EN2002a measurement.
