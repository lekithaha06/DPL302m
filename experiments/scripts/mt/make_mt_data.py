#!/usr/bin/env python3
"""Tạo dữ liệu MT (JSONL: id, src, ref, sent_id) cho B0 / cascade / LoRA. Manifest cascade tách riêng manifest ASR.

  phomt_test.jsonl, phomt_dev.jsonl       PhoMT bản detokenization (src=vi, ref=en)
  fleurs_{split}_clean.jsonl              src = transcript tiếng Việt gốc (raw) – đo khối dịch khi nghe đúng 100%
  fleurs_{split}_asr_{tag}.jsonl          src = lời ASR (predictions.jsonl của run ASR) – đầu vào cascade / dữ liệu dạy V1
Mỗi bản thu FLEURS là một mục (id = file_name); BLEU tính trên toàn bộ bản thu (857 ở test) cho cả sạch và cascade.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from ham_dung_chung import find_phomt_file  # noqa: E402


def write(p, rows):
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(p.name, len(rows), hashlib.sha256(p.read_bytes()).hexdigest()[:16])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest_dir", type=Path, default=Path("runs/manifests"))
    ap.add_argument("--phomt_dir", type=Path, default=Path("data/phomt"))
    ap.add_argument("--out_dir", type=Path, default=Path("runs/mt_data"))
    ap.add_argument("--asr", nargs="*", default=[], help="split:tag:predictions.jsonl")
    ap.add_argument("--phomt", action="store_true")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.phomt:
        for sp in ("test", "dev"):
            vi = find_phomt_file(args.phomt_dir, sp, "vi").read_text(encoding="utf-8").split("\n")
            en = find_phomt_file(args.phomt_dir, sp, "en").read_text(encoding="utf-8").split("\n")
            if vi and vi[-1] == "" and en[-1] == "":
                vi, en = vi[:-1], en[:-1]
            assert len(vi) == len(en), (sp, len(vi), len(en))
            write(args.out_dir / f"phomt_{sp}.jsonl", [{"id": f"phomt_{sp}_{i}", "src": a.strip(), "ref": b.strip()} for i, (a, b) in enumerate(zip(vi, en))])
    for sp in ("test", "dev", "train"):
        man = [json.loads(l) for l in open(args.manifest_dir / f"asr_fleurs_{sp}.jsonl", encoding="utf-8") if l.strip()]
        assert all(m["text_en"] for m in man), f"fleurs {sp}: thiếu câu tiếng Anh"
        write(args.out_dir / f"fleurs_{sp}_clean.jsonl", [{"id": m["id"], "sent_id": m["sent_id"], "src": m["reference"], "ref": m["text_en"]} for m in man])
    for spec in args.asr:
        sp, tag, pred = spec.split(":", 2)
        man = {json.loads(l)["id"]: json.loads(l) for l in open(args.manifest_dir / f"asr_fleurs_{sp}.jsonl", encoding="utf-8") if l.strip()}
        pr = {json.loads(l)["id"]: json.loads(l) for l in open(pred, encoding="utf-8") if l.strip()}
        assert pr.keys() == man.keys(), f"{spec}: id ASR không khớp manifest ({len(pr)} vs {len(man)})"
        write(args.out_dir / f"fleurs_{sp}_asr_{tag}.jsonl",
              [{"id": i, "sent_id": m["sent_id"], "src": pr[i]["prediction"], "ref": m["text_en"]} for i, m in man.items()])


if __name__ == "__main__":
    main()
