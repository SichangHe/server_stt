# discarded recorded-file probes
(authored by agents unless marked 🧑)

These probes used the promoted 120-second windows and 0.3 posterior threshold.
They were measured on the independent EN2002a 300–390 s crop before any
whole-meeting rerun; none was promoted.

posterior threshold 0.2

```sh
timeout 360s uv run --extra multitalker server-stt /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/EN2002a-300-390.wav --output output/file-en2002a-th02 --language en --activity-threshold 0.2
timeout 120s uv run --extra multitalker python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/reference.tsv output/file-en2002a-th02/transcript.json
```

```text
"word_edit_errors": 90,
"speaker_attributed_word_edit_errors": 59,
"speaker_attributed_word_error_fraction": 0.16120218579234974
```

posterior threshold 0.4

```sh
timeout 360s uv run --extra multitalker server-stt /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/EN2002a-300-390.wav --output output/file-en2002a-th04 --language en --activity-threshold 0.4
timeout 120s uv run --extra multitalker python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/reference.tsv output/file-en2002a-th04/transcript.json
```

```text
"word_edit_errors": 89,
"speaker_attributed_word_edit_errors": 61,
"speaker_attributed_word_error_fraction": 0.16666666666666666
```

recognition windows of 60 seconds

```sh
timeout 360s uv run --extra multitalker server-stt /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/EN2002a-300-390.wav --output output/file-en2002a-th03-ch60 --language en --activity-threshold 0.3 --recognition-chunk-s 60
timeout 120s uv run --extra multitalker python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/reference.tsv output/file-en2002a-th03-ch60/transcript.json
```

```text
"word_edit_errors": 94,
"speaker_attributed_word_edit_errors": 68,
"speaker_attributed_word_error_fraction": 0.18579234972677597
```

The temporary `--recognition-chunk-s` option was removed after this probe; the
production interface remains the fixed 120-second bound.

0.3 posterior masks with 90-second windows

The temporary default was changed to 90 seconds for this probe, then restored
to 120 seconds without committing the temporary change.

```sh
timeout 360s uv run --extra multitalker server-stt /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/EN2002a-300-390.wav --output output/file-en2002a-th03-ch90 --language en --activity-threshold 0.3
timeout 120s uv run --extra multitalker python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/reference.tsv output/file-en2002a-th03-ch90/transcript.json
```

```text
"word_edit_errors": 86,
"speaker_attributed_word_edit_errors": 58,
"speaker_attributed_word_error_fraction": 0.15846994535519127
```

It tied 120-second windows on cpWER, so the 120-second default remains.

target-only lower threshold

A temporary variant used a 0.2 target threshold and 0.3 competing-speaker
threshold. It was measured with:

```sh
timeout 360s uv run --extra multitalker server-stt /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/EN2002a-300-390.wav --output output/file-en2002a-target02 --language en
timeout 120s uv run --extra multitalker python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/reference.tsv output/file-en2002a-target02/transcript.json
```

```text
"word_edit_errors": 90,
"speaker_attributed_word_edit_errors": 59,
"speaker_attributed_word_error_fraction": 0.16120218579234974
```

It regressed the promoted 0.3/0.3 masks and was reverted without a
whole-meeting run.

one-frame posterior-mask dilation

The temporary implementation dilated each binary posterior mask by one frame
on both sides. Its exact command was:

```sh
timeout 360s uv run --extra multitalker server-stt /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/EN2002a-300-390.wav --output output/file-en2002a-th03-dil --language en --activity-threshold 0.3
timeout 120s uv run --extra multitalker python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/reference.tsv output/file-en2002a-th03-dil/transcript.json
```

```text
"word_edit_errors": 87,
"speaker_attributed_word_edit_errors": 58,
"speaker_attributed_word_error_fraction": 0.15846994535519127
```

It tied the promoted threshold on cpWER and changed the lexical score, so the
temporary code was reverted without a whole-meeting run.
