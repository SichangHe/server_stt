# DiariZen held-out scores

(authored by agents unless marked 🧑)

Speaker-attributed word errors from `scripts/score-ami.py`:

| meeting | errors / reference | fraction |
| --- | ---: | ---: |
| ES2004a (300–420) | 413 / 2614 | 15.8% |
| EN2002a (300–390) | 63 / 366 | 17.2% |
| TS3003a | 398 / 2518 | 15.8% |
| IS1009a | 340 / 1986 | 17.1% |

Commands used the normal `server-stt` command with default DiariZen separation, followed by:

```sh
uv run --extra multitalker python scripts/score-ami.py REFERENCE.tsv output/dz-*/transcript.json
```
