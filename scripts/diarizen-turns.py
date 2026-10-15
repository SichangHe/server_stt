"""Run the pinned DiariZen environment and print normalized turns."""
import sys
from diarizen.pipelines.inference import DiariZenPipeline

pipeline = DiariZenPipeline.from_pretrained("BUT-FIT/diarizen-wavlm-large-s80-md")
for segment, _, speaker in pipeline(sys.argv[1]).itertracks(yield_label=True):
    print(segment.start, segment.end, speaker)
