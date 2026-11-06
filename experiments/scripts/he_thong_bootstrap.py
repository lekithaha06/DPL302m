#!/usr/bin/env python3
"""Bootstrap BLEU cả hệ: cách xử lý cũ (truoc_0411) so với bản cuối (proposed) của sản phẩm fix.zip.
Chỉ đọc dự đoán đã chạy (reports/he_thong/du_doan_*.jsonl), không chạy model. Cùng cách với scripts/mt/bootstrap.py:
1000 lần, theo cụm sent_id (manifest FLEURS test), seed 42. Ghi reports/he_thong/bootstrap_cu_vs_moi.json."""
import json
import random
from pathlib import Path

import sacrebleu

T = Path(__file__).resolve().parents[1]
import sys
H = T / "reports" / (sys.argv[1] if len(sys.argv) > 1 else "he_thong")  # [04/11] thư mục kết quả: he_thong (V4, 03/11) hoặc he_thong_V2


def doc(f):
    return {(r := json.loads(l))["id"]: r for l in open(H / f, encoding="utf-8") if l.strip()}


A, B = doc("du_doan_truoc_0411.jsonl"), doc("du_doan_proposed.jsonl")
ids = sorted(A)
assert sorted(B) == ids and len(ids) == 857
sent = {json.loads(l)["id"]: json.loads(l)["sent_id"] for l in open(T / "runs/manifests/asr_fleurs_test.jsonl", encoding="utf-8")}
bleu = lambda S, ii: sacrebleu.corpus_bleu([S[i]["en"] for i in ii], [[S[i]["ref_en"] for i in ii]]).score
cum = {}
for i in ids:
    cum.setdefault(sent[i], []).append(i)
ks = sorted(cum)
random.seed(42)
d = []
for _ in range(1000):
    ii = [i for c in random.choices(ks, k=len(ks)) for i in cum[c]]
    d.append(bleu(B, ii) - bleu(A, ii))
d.sort()
co_so = [i for i in ids if any(ch.isdigit() for ch in A[i]["ref_vi"])]
out = {"A": "truoc_0411", "B": "proposed", "BLEU_A": round(bleu(A, ids), 2), "BLEU_B": round(bleu(B, ids), 2),
       "delta": round(bleu(B, ids) - bleu(A, ids), 2), "ci95": [round(d[25], 2), round(d[974], 2)],
       "p_one_sided_delta_le_0": sum(x <= 0 for x in d) / 1000, "n_resamples": 1000, "n_clusters": len(ks), "n_items": len(ids),
       "cluster": "sent_id", "seed": 42, "so_ban_dich_khac": sum(A[i]["en"] != B[i]["en"] for i in ids),
       "so_loi_asr_khac": sum(A[i]["vi_goc"] != B[i]["vi_goc"] for i in ids),
       "cau_co_chu_so": {"n": len(co_so), "BLEU_A": round(bleu(A, co_so), 2), "BLEU_B": round(bleu(B, co_so), 2)}}
(H / "bootstrap_cu_vs_moi.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False))
