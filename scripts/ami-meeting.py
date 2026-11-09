"""Download an AMI meeting (headset mix) and its manual word reference; write MP3 + reference.tsv.

Usage: ami-fixture.py DIR MEETING_ID [--start-s S --duration-s D]. Credit: AMI Consortium, CC BY 4.0.
"""
import argparse, csv, subprocess, urllib.request, xml.etree.ElementTree as ET, zipfile
from pathlib import Path

AUDIO = "https://huggingface.co/datasets/FluidInference/ami-corpus-mirror/resolve/main/sdm/{m}.Mix-Headset.wav"
MANUAL = "https://groups.inf.ed.ac.uk/ami/AMICorpusAnnotations/ami_public_manual_1.6.2.zip"


def fetch(url: Path | str, path: Path) -> None:
    if not path.exists():
        urllib.request.urlretrieve(url, path.with_suffix(".part"))
        path.with_suffix(".part").replace(path)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("directory", type=Path)
    p.add_argument("meeting")
    p.add_argument("--start-s", type=float, default=0)
    p.add_argument("--duration-s", type=float, default=3600)
    a = p.parse_args()
    a.directory.mkdir(parents=True, exist_ok=True)
    wav, zp = a.directory / f"{a.meeting}.wav", a.directory / "ami-manual.zip"
    fetch(AUDIO.format(m=a.meeting), wav)
    fetch(MANUAL, zp)
    end = a.start_s + a.duration_s
    mp3 = a.directory / f"{a.meeting}.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a.start_s), "-t", str(a.duration_s), "-i", str(wav),
                    "-ac", "1", "-ar", "16000", "-codec:a", "libmp3lame", "-q:a", "3", str(mp3)], check=True)
    rows = []
    with zipfile.ZipFile(zp) as z:
        for name in z.namelist():
            if name.startswith(f"words/{a.meeting}.") and name.endswith(".words.xml"):
                spk = name.split(".")[-3]
                for w in ET.fromstring(z.read(name)).findall("w"):
                    s, e = float(w.attrib["starttime"]), float(w.attrib["endtime"])
                    if a.start_s <= s < end and w.text:
                        rows.append((s - a.start_s, min(e, end) - a.start_s, spk, w.text))
    with (a.directory / f"{a.meeting}.ref.tsv").open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(("start_s", "end_s", "speaker", "word"))
        w.writerows(sorted(rows))
    print(f"{len(rows)} reference words -> {mp3}")


main()
