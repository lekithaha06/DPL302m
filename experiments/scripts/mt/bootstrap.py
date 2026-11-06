#!/usr/bin/env python3
"""Bootstrap theo cụm sent_id (FLEURS có nhiều bản thu cùng một câu) cho BLEU, so sánh cặp hai hệ thống.

python scripts/mt/bootstrap.py --a runs/mt/B0/fleurs_test_asr_pho/hyp.jsonl --b runs/mt/V1/fleurs_test_asr_pho/hyp.jsonl \
       --data runs/mt_data/fleurs_test_asr_pho.jsonl --out reports/mt/bootstrap_B0_V1.json
Mỗi lần lấy mẫu: rút có hoàn lại các sent_id, lấy mọi bản thu của câu được rút, tính corpus BLEU cho A và B trên cùng mẫu.
Báo cáo: BLEU A, B, delta, khoảng tin cậy 95% của delta, p (một phía: tỉ lệ lần delta <= 0).
"""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

import sacrebleu


def load(p):
    return {json.loads(l)["id"]: json.loads(l) for l in open(p, encoding="utf-8") if l.strip()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True); ap.add_argument("--b", required=True)
    ap.add_argument("--data", required=True, help="JSONL có id, sent_id (để gom cụm)")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--n", type=int, default=1000); ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    A, B, D = load(args.a), load(args.b), load(args.data)
    assert A.keys() == B.keys() == D.keys(), "id không khớp giữa hai hệ thống / dữ liệu"
    clusters = defaultdict(list)
    for i, d in D.items():
        clusters[d.get("sent_id") or i].append(i)
    keys = sorted(clusters)
    bleu = sacrebleu.BLEU()

    def corp(S, ids):
        return bleu.corpus_score([S[i]["hyp"] for i in ids], [[S[i]["ref"] for i in ids]]).score

    ids_all = sorted(D)
    a0, b0 = corp(A, ids_all), corp(B, ids_all)
    rng = random.Random(args.seed)
    deltas = []
    for _ in range(args.n):
        ids = [i for k in rng.choices(keys, k=len(keys)) for i in clusters[k]]
        deltas.append(corp(B, ids) - corp(A, ids))
    deltas.sort()
    res = {"A": args.a, "B": args.b, "BLEU_A": round(a0, 2), "BLEU_B": round(b0, 2), "delta": round(b0 - a0, 2),
           "ci95": [round(deltas[int(0.025 * args.n)], 2), round(deltas[int(0.975 * args.n) - 1], 2)],
           "p_one_sided_delta_le_0": sum(d <= 0 for d in deltas) / args.n, "n_resamples": args.n,
           "n_clusters": len(keys), "n_items": len(ids_all), "cluster": "sent_id", "seed": args.seed}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res))


if __name__ == "__main__":
    main()
