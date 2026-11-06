#!/usr/bin/env python3
"""Augmentation dữ liệu dạy khối dịch (ablation A_aug, 03/11/2026).

Lấy 2.926 cặp transcript SẠCH của FLEURS TRAIN (runs/mt_data/fleurs_train_clean.jsonl) và đổi câu nguồn sang dạng giống lời ASR
của PhoWhisper: chữ thường, bỏ dấu câu bên trong câu, giữ dấu chấm cuối (PhoWhisper thường in dấu chấm cuối, không in dấu phẩy).
Câu đích tiếng Anh giữ nguyên → không đổi nghĩa. Chỉ dùng TRAIN; dev/test không đụng tới. Chữ số giữ nguyên (không đoán cách đọc).
Ghi runs/mt_data/fleurs_train_clean_asrstyle.jsonl (id thêm hậu tố '#sach' để không trùng id với bản lời ASR).
"""
import json
import re
import unicodedata
from pathlib import Path

T = Path(__file__).resolve().parents[2]
SRC = T / "runs/mt_data/fleurs_train_clean.jsonl"
OUT = T / "runs/mt_data/fleurs_train_clean_asrstyle.jsonl"
DEV_TEST = [T / f"runs/mt_data/{n}.jsonl" for n in ("fleurs_dev_clean", "fleurs_test_clean")]


def kieu_asr(s):
    s = unicodedata.normalize("NFC", s).lower().strip()
    s = re.sub(r"[\"“”‘’'«»()\[\]{}:;,!?…–—/\\]", " ", s)     # bỏ dấu câu
    s = re.sub(r"(?<=\D)-(?=\D)", " ", s)                       # gạch nối giữa chữ → khoảng trắng
    s = re.sub(r"\.(?=\s|$)", " ", s)                          # bỏ chấm giữa câu (giữ số thập phân 2.4)
    s = re.sub(r"\s+", " ", s).strip()
    return s + "." if s else s


def main():
    rows = [json.loads(l) for l in open(SRC, encoding="utf-8") if l.strip()]
    cam = {json.loads(l)["sent_id"] for f in DEV_TEST for l in open(f, encoding="utf-8") if l.strip()}
    assert not ({r["sent_id"] for r in rows} & cam), "rò rỉ: câu train trùng dev/test"
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({"id": r["id"] + "#sach", "sent_id": r["sent_id"], "src": kieu_asr(r["src"]), "ref": r["ref"]}, ensure_ascii=False) + "\n")
    print(f"{OUT} | {len(rows)} cặp | 0 câu trùng dev/test | ví dụ:", rows[0]["src"], "→", kieu_asr(rows[0]["src"]))


if __name__ == "__main__":
    main()
