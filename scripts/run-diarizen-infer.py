"""Infer DiariZen turns as start/end/speaker lines."""
import sys
from diarizen.pipelines.inference import DiariZenPipeline

p = DiariZenPipeline.from_pretrained("BUT-FIT/diarizen-wavlm-large-s80-md")
r = p(sys.argv[1])
for t, _, s in r.itertracks(yield_label=True):
    print(t.start, t.end, s)
