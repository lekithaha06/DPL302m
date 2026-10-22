"""Fetch original publisher checkpoints, with revisions pinned in the saved metadata."""
import argparse
import json
import urllib.request
from pathlib import Path
REVISIONS = {"vinai/PhoWhisper-small": "a86b604c346caf7148c37512eafe783a16420adb",
             "openai/whisper-small": "973afd24965f72e36ca33b3055d56a652f456b4d"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=".work/source_models")
    args = ap.parse_args()
    for model_id in ["vinai/PhoWhisper-small", "openai/whisper-small"]:
        out = Path(args.output) / model_id.split("/")[-1]
        out.mkdir(parents=True, exist_ok=True)
        info = json.load(urllib.request.urlopen("https://huggingface.co/api/models/" + model_id + "/revision/" + REVISIONS[model_id], timeout=60))
        rev = info["sha"]
        names = {s["rfilename"] for s in info["siblings"]}
        prior = out / "source_provenance.json"
        if prior.exists() and json.loads(prior.read_text())["revision"] != rev:
            raise ValueError("Existing checkpoint folder uses a different revision")
        weight = "model.safetensors" if "model.safetensors" in names else "pytorch_model.bin"
        for name in sorted(names):
            if not (name.endswith(".json") or name in ["merges.txt", weight]):
                continue
            dest = out / name
            if dest.exists():
                continue
            print(f"Downloading {model_id} {name}", flush=True)
            with urllib.request.urlopen(f"https://huggingface.co/{model_id}/resolve/{rev}/{name}", timeout=180) as response:
                received = 0
                expected = response.headers.get("Content-Length")
                with dest.with_suffix(dest.suffix + ".partial").open("wb") as handle:
                    while block := response.read(4 * 1024 * 1024):
                        handle.write(block)
                        received += len(block)
                if expected and received != int(expected):
                    raise IOError("Incomplete checkpoint download")
            dest.with_suffix(dest.suffix + ".partial").replace(dest)
        metadata = {"source_model": model_id, "revision": rev, "source_weight_file": weight}
        (out / "source_provenance.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(json.dumps(metadata), flush=True)

if __name__ == "__main__":
    main()
