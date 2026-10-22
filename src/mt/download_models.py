"""Download the pretrained checkpoints used by Baseline B and the cascade, pinned to the revisions used in Task 1."""
import argparse
from huggingface_hub import snapshot_download

REVISIONS = {
    "vinai/vinai-translate-vi2en": "95d9a72c9e6a319c5a9c7dd2135975092e95252b",  # AGPL-3.0, paper model (Interspeech 2022)
    "vinai/PhoWhisper-small": "a86b604c346caf7148c37512eafe783a16420adb",       # BSD-3-Clause
}
SKIP = ["*.h5", "*.msgpack", "*.ot"]  # TensorFlow/Flax weights are not needed

ap = argparse.ArgumentParser()
ap.add_argument("--output", default="checkpoints/pretrained")
args = ap.parse_args()

for repo, rev in REVISIONS.items():
    path = snapshot_download(repo, revision=rev, local_dir=f"{args.output}/{repo.split('/')[-1]}", ignore_patterns=SKIP)
    print(repo, rev, "->", path, flush=True)
