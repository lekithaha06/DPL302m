"""Task 2 · nhật ký bằng chứng: dòng thời gian chạy, mã hash của dữ liệu đã xử lý, checkpoint và file kết quả.

Ghi reports/task2/evidence/manifest.json và reports/task2/NHAT_KY_THUC_NGHIEM.md. Mã SHA-256 cho phép chứng minh
file kết quả/checkpoint không bị sửa sau khi chạy (đối chiếu lại bằng cùng script).
"""
import glob, hashlib, json, os, sys
sys.stdout.reconfigure(encoding="utf-8")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


groups = {
    "data_processed": sorted(glob.glob("data/processed/*.json")) + sorted(glob.glob("data/asr/*.jsonl")) + sorted(glob.glob("data/mt/*.jsonl")),
    "checkpoints": sorted(glob.glob("checkpoints/v*/best_adapter/*")) + sorted(glob.glob("checkpoints/v*/*.json*")),
    "results": sorted(p for p in glob.glob("reports/task2/**/*", recursive=True) if os.path.isfile(p) and "evidence" not in p),
}
man = {g: [{"path": p.replace("\\", "/"), "bytes": os.path.getsize(p), "sha256": sha(p)} for p in ps] for g, ps in groups.items()}
os.makedirs("reports/task2/evidence", exist_ok=True)
json.dump(man, open("reports/task2/evidence/manifest.json", "w", encoding="utf-8"), indent=1)

log = open("reports/task2/logs/queue.log", encoding="utf-8").read().strip().splitlines()
md = ["# Nhật ký thực nghiệm Task 2", "",
      "Máy: xem `evidence/gpu.txt`; thư viện: `evidence/pip_freeze.txt`; mã hash mọi file: `evidence/manifest.json`.", "",
      "## Dòng thời gian (trích `logs/queue.log`)", "", "```"] + log + ["```", "",
      "## Kết quả train từng phiên bản", ""]
for v in ("v1", "v2"):
    lp = f"checkpoints/{v}/log.jsonl"
    if os.path.exists(lp):
        md += [f"### {v.upper()}", "", "| Epoch | Train loss | Dev loss | Dev BLEU | Dev chrF++ | Giây |", "|---|---|---|---|---|---|"]
        for l in open(lp, encoding="utf-8"):
            r = json.loads(l)
            tl = "–" if r["train_loss"] is None else f"{r['train_loss']:.4f}"
            md.append(f"| {r['epoch']} | {tl} | {r['dev_loss']:.4f} | {r['dev_bleu']:.2f} | {r['dev_chrf++']:.2f} | {r['seconds']} |")
        md.append("")
md += ["## Mã hash checkpoint (adapter LoRA)", ""]
md += [f"- `{x['path']}`: `{x['sha256'][:16]}…` ({x['bytes']:,} byte)" for x in man["checkpoints"] if "adapter_model" in x["path"]]
open("reports/task2/NHAT_KY_THUC_NGHIEM.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("files hashed:", {g: len(v) for g, v in man.items()})
