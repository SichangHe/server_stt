# alternative recorded-file recognizer probes
(authored by agents unless marked 🧑)

The current multitalker file default is 58/366 on EN2002a 300–390 s and
312/2614 on whole ES2004a. Alternative recognizers were screened on the
independent crop; neither beat the current default, so neither was run on the
whole meeting or promoted.

Qwen

```sh
timeout 900s uv run --extra qwen server-stt /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/EN2002a-300-390.wav --output output/file-en2002a-qwen --language en --recognizer qwen --diarization nemotron
timeout 180s uv run --extra qwen python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/reference.tsv output/file-en2002a-qwen/transcript.json
```

```text
"word_edit_errors": 89,
"speaker_attributed_word_edit_errors": 94,
"speaker_attributed_word_error_fraction": 0.2568306010928962
```

Whisper large-v3 with Nemotron turns

```sh
timeout 900s uv run server-stt /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/EN2002a-300-390.wav --output output/file-en2002a-whisper --language en --recognizer whisper --diarization nemotron
timeout 180s uv run python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/reference.tsv output/file-en2002a-whisper/transcript.json
```

```text
"word_edit_errors": 100,
"speaker_attributed_word_edit_errors": 112,
"speaker_attributed_word_error_fraction": 0.30601092896174864
```

Both alternatives are worse than the current default, so the default remains
the pinned multitalker model with 120-second windows and 0.3 Nemotron posterior
activity masks.

whole ES2004a Qwen

```sh
/usr/bin/time -f 'elapsed_s=%e maxrss_kb=%M' timeout 1800s uv run --extra qwen server-stt /ssd1/sichangheagent/private-artifacts/server-stt/full-ES2004a/ES2004a.mp3 --output output/file-full-qwen --language en --recognizer qwen --diarization nemotron
timeout 240s uv run --extra qwen python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/full-ES2004a/reference.tsv output/file-full-qwen/transcript.json
```

```text
elapsed_s=1062.45 maxrss_kb=14215180
"word_edit_errors": 545,
"speaker_attributed_word_edit_errors": 584,
"speaker_attributed_word_error_fraction": 0.2234123947972456
```

The whole-meeting Qwen result is also worse than the current multitalker
312/2614 result.

whole ES2004a Whisper large-v3

```sh
/usr/bin/time -f 'elapsed_s=%e maxrss_kb=%M' timeout 1200s uv run server-stt /ssd1/sichangheagent/private-artifacts/server-stt/full-ES2004a/ES2004a.mp3 --output output/file-full-whisper --language en --recognizer whisper --diarization nemotron
timeout 240s uv run python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/full-ES2004a/reference.tsv output/file-full-whisper/transcript.json
```

```text
elapsed_s=662.87 maxrss_kb=6600000
"word_edit_errors": 836,
"speaker_attributed_word_edit_errors": 875,
"speaker_attributed_word_error_fraction": 0.3347352716143841
```

The whole-meeting Whisper large-v3 result is also worse than the current
multitalker 312/2614 result.

Whisper large-v3-turbo

```sh
timeout 1200s uv run server-stt /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/EN2002a-300-390.wav --output output/file-en2002a-whisper-turbo --language en --recognizer whisper --model large-v3-turbo --diarization nemotron
timeout 180s uv run python scripts/score-ami.py /ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/reference.tsv output/file-en2002a-whisper-turbo/transcript.json
```

```text
"word_edit_errors": 110,
"speaker_attributed_word_edit_errors": 117,
"speaker_attributed_word_error_fraction": 0.319672131147541
```
