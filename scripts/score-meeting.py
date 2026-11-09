"""Score server-stt transcript.json against AMI ref.tsv: WER (speaker-blind), cpWER, DER (collar 0.25)."""
import csv, json, re, sys
import meeteval
from meeteval.der import md_eval_22
from meeteval.io import SegLST

FILL = {"uh","um","mm","hmm","mmhmm","uhhuh","huh","erm","ah","oh","eh","mhm"}
norm = lambda t: re.sub(r"[^a-z0-9']", "", t.lower())
if "--no-fillers" in sys.argv:
    sys.argv.remove("--no-fillers"); _n = norm; norm = lambda t: "" if _n(t) in FILL else _n(t)
ref_rows = [r for r in csv.DictReader(open(sys.argv[1]), delimiter="\t") if norm(r["word"])]
hyp = json.load(open(sys.argv[2]))
ref = SegLST([{"session_id": "m", "speaker": r["speaker"], "words": norm(r["word"]),
               "start_time": float(r["start_s"]), "end_time": float(r["end_s"])} for r in ref_rows])
hw = [w for w in hyp["words"] if norm(w["text"])]
hypo = SegLST([{"session_id": "m", "speaker": w["speaker"], "words": norm(w["text"]),
                "start_time": w["start_s"], "end_time": w["end_s"]} for w in hw])
c = meeteval.wer.cpwer(ref, hypo)["m"]
# speaker-blind WER, words in time order
order = lambda L, k: [x["words"] for x in sorted(L, key=lambda x: x[k])]
single = lambda L: SegLST([{**x, "speaker": "A"} for x in L])
wer = meeteval.wer.cpwer(single(ref), single(hypo))["m"]
print(f"ref_words {c.length}  cpWER {c.error_rate:.4f} ({c.errors} err)  speaker-blind WER {wer.error_rate:.4f} ({wer.errors} err)")
# DER from reference word intervals (merged per speaker, gaps <0.5s bridged) vs hyp turns
def merge(iv, gap=0.5):
    out = []
    for s, e in sorted(iv):
        if out and s - out[-1][1] <= gap: out[-1][1] = max(out[-1][1], e)
        else: out.append([s, e])
    return out
rs = {}
for r in ref_rows: rs.setdefault(r["speaker"], []).append((float(r["start_s"]), float(r["end_s"])))
rseg = SegLST([{"session_id": "m", "speaker": k, "start_time": s, "end_time": e} for k, v in rs.items() for s, e in merge(v)])
hseg = SegLST([{"session_id": "m", "speaker": t["speaker"], "start_time": t["start_s"], "end_time": t["end_s"]} for t in hyp["turns"]])
try:
    d = md_eval_22(rseg, hseg, collar=0.25)["m"]
    print(f"DER (collar 0.25, ref=word intervals bridged 0.5s) {d.error_rate:.4f}")
except Exception as ex:
    print("DER unavailable:", type(ex).__name__, str(ex)[:200])
