"""Process raw microphone PCM chunks online with the existing CPU models."""
import argparse, json, sys
from pathlib import Path
from server_stt.live import pcm_chunks

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--chunk-s',type=float,default=20.0)
    p.add_argument('--diarization-model',type=Path,default=Path('models/Nemotron-3-Diarization.q8_0.gguf'))
    p.add_argument('--diarization-runtime',type=Path,default=Path('models/nemo-speech-0.2.0-linux-x86_64-cpu'))
    a=p.parse_args()
    from server_stt.diarization import diarize
    from server_stt.multitalker import recognize
    offset=0.0
    for audio in pcm_chunks(sys.stdin.buffer,a.chunk_s):
        d=diarize(audio,a.diarization_model,a.diarization_runtime)
        if isinstance(d,str): print(json.dumps({'error':d}),flush=True); continue
        r=recognize(audio,d.turns)
        if isinstance(r,str): print(json.dumps({'error':r}),flush=True); continue
        print(json.dumps({'offset_s':offset,'words':[w.__dict__ for w in r.words]}),flush=True)
        offset += len(audio)/16000
    return 0
