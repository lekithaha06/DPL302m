"""Download only the official VIVOS test files, without executing a dataset loader."""
import argparse
import gzip
import hashlib
import json
import tarfile
import urllib.request
from pathlib import Path

REPO = "AILAB-VNUHCM/vivos"
REVISION = "3cbfb2502e5e84776b4b778b020a09759f723f52"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="data/vivos_test")
    args = ap.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    info = json.load(urllib.request.urlopen(f"https://huggingface.co/api/datasets/{REPO}/revision/{REVISION}", timeout=60))
    revision = info["sha"]
    base = f"https://huggingface.co/datasets/{REPO}/resolve/{revision}/data/"
    prompt_bytes = urllib.request.urlopen(base + "prompts-test.txt.gz", timeout=60).read()
    prompts = {}
    for line in gzip.decompress(prompt_bytes).decode("utf-8").splitlines():
        utterance_id, transcript = line.strip().split(" ", 1)
        if utterance_id in prompts:
            raise ValueError("Duplicate utterance id")
        prompts[utterance_id] = transcript
    if len(prompts) != 760:
        raise ValueError(f"Expected 760 test items, found {len(prompts)}")
    missing = {uid for uid in prompts if not (out / (uid + ".wav")).exists()}
    if missing:
        print(f"Downloading official archive stream; extracting {len(missing)} test files", flush=True)
        with urllib.request.urlopen(base + "vivos.tar.gz", timeout=180) as stream:
            with tarfile.open(fileobj=stream, mode="r|gz") as archive:
                for member in archive:
                    if not member.isfile() or "/test/waves/" not in member.name:
                        continue
                    uid = Path(member.name).stem
                    if uid not in missing:
                        continue
                    with archive.extractfile(member) as source:
                        (out / (uid + ".wav")).write_bytes(source.read())
                    missing.remove(uid)
                    if len(missing) % 100 == 0:
                        print(f"Remaining {len(missing)}", flush=True)
                    if not missing:
                        break
        if missing:
            raise ValueError(f"Archive missing {len(missing)} test recordings")
    manifest = []
    for uid in sorted(prompts):
        audio = out / (uid + ".wav")
        manifest.append({"id": uid, "speaker_id": uid.split("_")[0], "audio": str(audio.resolve()),
                         "reference": prompts[uid], "audio_sha256": hashlib.sha256(audio.read_bytes()).hexdigest()})
    manifest_text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in manifest)
    (out / "manifest.jsonl").write_text(manifest_text, encoding="utf-8")
    provenance = {"repo": REPO, "revision": revision, "split": "test", "n": len(manifest),
                  "license": "CC-BY-NC-SA-4.0", "source": base + "vivos.tar.gz",
                  "prompts_sha256": hashlib.sha256(prompt_bytes).hexdigest(),
                  "ordered_audio_ids_sha256": hashlib.sha256("\n".join(sorted(prompts)).encode()).hexdigest(),
                  "manifest_sha256": hashlib.sha256(manifest_text.encode()).hexdigest()}
    (out / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(provenance, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
