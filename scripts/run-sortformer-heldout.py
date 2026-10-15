"""Run Sortformer threshold probes and held-out scores."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = Path('/ssd1/sichangheagent/private-artifacts/server-stt')
OUT = ART / 'sortformer-heldout-results'
OUT.mkdir(parents=True, exist_ok=True)

def run(source: str, script: str, output: str, thresholds: tuple[float, ...]) -> None:
    template = (ROOT / 'scripts' / script).read_text()
    for threshold in thresholds:
        text = template.replace('SOURCE = Path("/ssd1/sichangheagent/private-artifacts/server-stt/independent-EN2002a-300-390/EN2002a-300-390.wav")', f'SOURCE = Path("{source}")')
        text = text.replace('SOURCE = Path("/ssd1/sichangheagent/private-artifacts/server-stt/full-ES2004a/ES2004a.mp3")', f'SOURCE = Path("{source}")')
        text = text.replace('for threshold in (0.3, 0.5, 0.7):', f'for threshold in ({threshold},):')
        text = text.replace('chunk_s=120', 'chunk_s=90').replace('output/file-en2002a-sortformer21-activity-', f'output/{output}-')
        generated = OUT / f'{output}-{threshold}.py'
        generated.write_text(text)
        subprocess.run(['uv', 'run', '--extra', 'multitalker', 'python', str(generated)], cwd=ROOT, check=True)
        transcript = ROOT / f'output/{output}-{threshold}/transcript.json'
        reference = ART / ('review-20261012/reference-300-420.tsv' if 'es' in output else 'TS3003a/reference.tsv' if 'ts' in output else 'review-20261012/IS1009a/reference.tsv')
        score = subprocess.check_output(['uv', 'run', '--extra', 'multitalker', 'python', 'scripts/score-ami.py', str(reference), str(transcript)], cwd=ROOT, text=True)
        (OUT / f'{output}-{threshold}.score').write_text(score)

run(str(ART / 'full-ES2004a/ES2004a.mp3'), 'review-sortformer-activity.py', 'es-sortformer', (0.3, 0.5, 0.7))
run(str(ART / 'TS3003a/TS3003a.Mix-Headset.wav'), 'review-sortformer-full.py', 'ts-sortformer', (0.3,))
run(str(ART / 'review-20261012/IS1009a/IS1009a.Mix-Headset.wav'), 'review-sortformer-full.py', 'is-sortformer', (0.3,))
