#!/usr/bin/env python3
"""Dữ liệu dạy theo thiết kế cân bằng của Uyên (reports/data/can_bang/), nhưng src là LỜI ASR như V1:

  fleurs_train_asr_pho_canbang.jsonl  mỗi bản thu lặp đúng so_lan_trong_du_lieu_day lần (can_bang_v1_so_lan.csv) → 4468 mẫu
  phomt_train_mix.jsonl               các dòng PhoMT train sạch theo can_bang_v2_phomt_idx.txt (4468 cặp, chống quên miền PhoMT)
Id lặp được thêm hậu tố #k để phân biệt; nội dung giữ nguyên.
"""
import csv
import hashlib
import json
from pathlib import Path

T = Path(__file__).resolve().parents[2]
CB = T / "reports" / "data" / "can_bang"
OUT = T / "runs" / "mt_data"


def write(p, rows):
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(p.name, len(rows), hashlib.sha256(p.read_bytes()).hexdigest()[:16])


def main():
    asr = {json.loads(l)["id"]: json.loads(l) for l in open(OUT / "fleurs_train_asr_pho.jsonl", encoding="utf-8")}
    rows = []
    for r in csv.DictReader(open(CB / "can_bang_v1_so_lan.csv", encoding="utf-8-sig")):
        it = asr[f"{r['uid']}.wav"]
        for k in range(int(r["so_lan_trong_du_lieu_day"])):
            rows.append({**it, "id": f"{it['id']}#{k}"})
    write(OUT / "fleurs_train_asr_pho_canbang.jsonl", rows)
    idx = [int(x) for x in (CB / "can_bang_v2_phomt_idx.txt").read_text().split()]
    want = set(idx)
    vi, en = {}, {}
    for name, store in (("train.vi", vi), ("train.en", en)):
        with open(T / "data" / "clean" / "phomt" / name, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i in want:
                    store[i] = line.rstrip("\n")
    write(OUT / "phomt_train_mix.jsonl", [{"id": f"phomt_train_{i}", "src": vi[i].strip(), "ref": en[i].strip()} for i in idx])


if __name__ == "__main__":
    main()
