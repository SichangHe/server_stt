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
