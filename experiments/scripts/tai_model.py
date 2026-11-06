"""Tải mới các checkpoint vào task3/hf_home (HF_HUB_CACHE), ghi revision thật + dung lượng vào reports/models.json."""
import json, os, sys
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download
MODELS = [("vinai/PhoWhisper-small", "a86b604c346caf7148c37512eafe783a16420adb"),
          ("openai/whisper-small", "973afd24965f72e36ca33b3055d56a652f456b4d"),
          ("vinai/vinai-translate-vi2en-v2", "main")]
PAT = ["*.json", "*.txt", "*.model", "*.safetensors", "*.bin", "*.py", "*.spm", "*.tiktoken"]
IGN = ["*tf_model*", "*flax*", "*.msgpack", "*.h5", "*onnx*", "*.ot"]
out = []
for repo, rev in MODELS:
    sha = HfApi().model_info(repo, revision=rev).sha
    p = snapshot_download(repo, revision=sha, allow_patterns=PAT, ignore_patterns=IGN)
    files = {f.name: f.stat().st_size for f in Path(p).iterdir() if f.is_file()}
    # nếu có cả safetensors và bin, chỉ cần một; ghi đủ để biết
    out.append({"repo": repo, "revision_requested": rev, "sha": sha, "path": p, "files": files})
    print(repo, sha, sum(files.values()) // 2**20, "MB", flush=True)
Path(os.environ["T"], "reports").mkdir(exist_ok=True)
Path(os.environ["T"], "reports", "models.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
