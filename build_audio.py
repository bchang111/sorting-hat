#!/usr/bin/env python3
"""Record every Sorting Hat line in lines.json to audio/<id>.m4a using macOS `say`.

Run after editing lines.json:  python3 build_audio.py
Optionally pick another installed voice:  python3 build_audio.py "Jamie (Premium)"
The ids here must match audioIds() in index.html.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "audio"


def audio_ids(d):
    ids = {}
    for i, t in enumerate(d["questions"]):
        ids[f"q{i + 1:02d}"] = t
    for i, t in enumerate(d["ponder"]):
        ids[f"ponder{i + 1}"] = t
    for i, t in enumerate(d["leadIns"]):
        ids[f"lead{i + 1}"] = t
    ids["test"] = d["test"]
    for key, h in d["houses"].items():
        ids[f"house-{key}"] = h["name"] + "!"
        for i, t in enumerate(h["lines"]):
            ids[f"{key}{i + 1}"] = t
        for k in h["keys"]:
            ids["clue-" + k.replace(" ", "-")] = f"Ah. [[slnc 250]] {k.capitalize()}. [[slnc 350]] I see."
    return ids


def main():
    d = json.loads((ROOT / "lines.json").read_text())
    voice = sys.argv[1] if len(sys.argv) > 1 else d["voice"]
    rate = str(d["rate"])
    OUT.mkdir(exist_ok=True)
    ids = audio_ids(d)
    for old in OUT.glob("*.m4a"):
        if old.stem not in ids:
            old.unlink()
    # Remember what each file was recorded from, so unchanged lines are skipped next time.
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    recorded = 0
    with tempfile.TemporaryDirectory() as tmp:
        aiff = pathlib.Path(tmp) / "line.aiff"
        for n, (aid, text) in enumerate(ids.items(), 1):
            target = OUT / f"{aid}.m4a"
            source = f"{voice}|{rate}|{text}"
            if target.exists() and manifest.get(aid) == source:
                continue
            for attempt in range(3):
                try:
                    # `say` occasionally hangs; give each line a short deadline and retry.
                    subprocess.run(["say", "-v", voice, "-r", rate, "-o", str(aiff), text], check=True, timeout=20)
                    break
                except subprocess.TimeoutExpired:
                    if attempt == 2:
                        raise
            subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", "-c", "1", str(aiff), str(target)], check=True)
            manifest[aid] = source
            manifest_path.write_text(json.dumps(manifest, indent=1))
            recorded += 1
            print(f"\r{n}/{len(ids)} {aid:<28}", end="", flush=True)
    print(f"\nRecorded {recorded} new lines ({len(ids)} total) with voice {voice!r} into {OUT}")


if __name__ == "__main__":
    main()
