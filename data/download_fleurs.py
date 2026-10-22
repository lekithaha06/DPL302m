"""Download FLEURS vi_vn (audio + transcripts) and en_us (transcripts only) from the official Hugging Face repo.

Task 2 (TV4 area): train/dev are new downloads; test is kept for evaluation only.
License: CC BY 4.0 (google/fleurs).
"""
import argparse, os, tarfile
from huggingface_hub import hf_hub_download

REPO = "google/fleurs"

ap = argparse.ArgumentParser()
ap.add_argument("--splits", default="train,dev,test")
ap.add_argument("--out", default="data/fleurs")
ap.add_argument("--audio-out", default="data/fleurs_audio")
args = ap.parse_args()

for split in args.splits.split(","):
    for lang in ("vi_vn", "en_us"):
        p = hf_hub_download(REPO, f"data/{lang}/{split}.tsv", repo_type="dataset", local_dir=args.out)
        print("tsv", p, flush=True)
    tar = hf_hub_download(REPO, f"data/vi_vn/audio/{split}.tar.gz", repo_type="dataset", local_dir=args.out)
    dest = os.path.join(args.audio_out, split)
    if not os.path.isdir(dest) or not os.listdir(dest):
        os.makedirs(dest, exist_ok=True)
        with tarfile.open(tar) as t:
            members = [m for m in t.getmembers() if m.isfile() and m.name.endswith(".wav")]
            for m in members:
                m.name = os.path.basename(m.name)  # flatten; also blocks path traversal
                t.extract(m, dest)
        print("audio", split, len(members), "files ->", dest, flush=True)
