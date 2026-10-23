"""Manifest FLEURS test cho src/asr/evaluate_asr_gpu.py (Baseline A trên FLEURS, cùng script và cấu hình với VIVOS).

FLEURS không có mã người nói; trường speaker_id ở đây là ID câu FLoRes (một câu có 1–3 bản thu), nên
"speaker_metrics" trong báo cáo kết quả thực chất là chỉ số theo câu.
"""
import argparse, hashlib, json, os

ap = argparse.ArgumentParser()
ap.add_argument("--eval-set", default="data/processed/fleurs_vi_en_test.json")
ap.add_argument("--out", default="data/fleurs_test_asr")
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
rows = json.load(open(args.eval_set, encoding="utf-8"))
items = []
for r in sorted(rows, key=lambda r: os.path.basename(r["audio"])):
    a = os.path.abspath(r["audio"])
    items.append({"id": os.path.splitext(os.path.basename(a))[0], "speaker_id": f"sent{r['id']}", "audio": a,
                  "reference": r["vi_raw"], "audio_sha256": hashlib.sha256(open(a, "rb").read()).hexdigest()})
text = "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in items)
open(f"{args.out}/manifest.jsonl", "w", encoding="utf-8").write(text)
prov = {"repo": "google/fleurs", "config": "vi_vn", "split": "test", "n": len(items), "license": "CC-BY-4.0",
        "speaker_id_note": "FLoRes sentence id (FLEURS has no speaker id)",
        "manifest_sha256": hashlib.sha256(text.encode()).hexdigest()}
json.dump(prov, open(f"{args.out}/provenance.json", "w", encoding="utf-8"), indent=2)
print(prov)
