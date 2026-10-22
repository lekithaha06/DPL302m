"""Task 2 · kiểm định cải thiện có thật hay do may: paired bootstrap resampling (Koehn, 2004) trên cascade FLEURS test.

Lấy mẫu lại có hoàn lại N câu (cùng chỉ số cho cả hai hệ), tính BLEU và chrF++ của từng hệ trên mẫu đó, lặp B lần.
p-value = tỉ lệ lần lấy mẫu mà hệ mới KHÔNG tốt hơn hệ gốc; khoảng tin cậy 95% của chênh lệch BLEU.
Lưu ý: 857 bản thu chỉ có 347 câu gốc; ngoài lấy mẫu theo bản thu, script lấy mẫu theo câu gốc (cả cụm bản thu) cho chặt hơn.
"""
import argparse, json, random
from collections import defaultdict
import numpy as np, sacrebleu

ap = argparse.ArgumentParser()
ap.add_argument("--base", default="B0")
ap.add_argument("--new", required=True)
ap.add_argument("--dir", default="reports/task2/mt")
ap.add_argument("--b", type=int, default=1000)
args = ap.parse_args()

A = json.load(open(f"{args.dir}/predictions_{args.base}.json", encoding="utf-8"))
B = json.load(open(f"{args.dir}/predictions_{args.new}.json", encoding="utf-8"))
refs = [r["en_ref"] for r in A]
ha, hb = [r["cascade"] for r in A], [r["cascade"] for r in B]
groups = defaultdict(list)
for i, r in enumerate(A):
    groups[r["id"]].append(i)
gkeys = sorted(groups)


# Sufficient statistics per sentence are computed once; a corpus score on any resample is the score of the summed
# statistics (identical to sacrebleu.corpus_bleu / corpus_chrf on that resample, but thousands of times faster).
bleu, chrf = sacrebleu.metrics.BLEU(), sacrebleu.metrics.CHRF(word_order=2)
S = {k: np.array(m._extract_corpus_statistics(h, [refs]), dtype=np.int64)
     for k, m, h in (("bA", bleu, ha), ("bB", bleu, hb), ("cA", chrf, ha), ("cB", chrf, hb))}


def stats(idx):
    idx = np.asarray(list(idx))
    return (bleu._compute_score_from_stats(S["bA"][idx].sum(0).tolist()).score,
            bleu._compute_score_from_stats(S["bB"][idx].sum(0).tolist()).score,
            chrf._compute_score_from_stats(S["cA"][idx].sum(0).tolist()).score,
            chrf._compute_score_from_stats(S["cB"][idx].sum(0).tolist()).score)


res = {"base": args.base, "new": args.new, "B": args.b}
full = stats(range(len(refs)))
res["full"] = {"BLEU_base": round(full[0], 2), "BLEU_new": round(full[1], 2), "chrF_base": round(full[2], 2), "chrF_new": round(full[3], 2)}
for mode in ("utterance", "sentence_cluster"):
    rng = random.Random(42)
    d_bleu, d_chrf = [], []
    for _ in range(args.b):
        if mode == "utterance":
            idx = [rng.randrange(len(refs)) for _ in refs]
        else:
            idx = [i for _ in gkeys for i in groups[gkeys[rng.randrange(len(gkeys))]]]
        s = stats(idx)
        d_bleu.append(s[1] - s[0]); d_chrf.append(s[3] - s[2])
    d_bleu, d_chrf = np.array(d_bleu), np.array(d_chrf)
    res[mode] = {"delta_BLEU_mean": round(float(d_bleu.mean()), 2),
                 "delta_BLEU_CI95": [round(float(np.percentile(d_bleu, 2.5)), 2), round(float(np.percentile(d_bleu, 97.5)), 2)],
                 "p_value_BLEU": round(float((d_bleu <= 0).mean()), 4),
                 "delta_chrF_mean": round(float(d_chrf.mean()), 2),
                 "delta_chrF_CI95": [round(float(np.percentile(d_chrf, 2.5)), 2), round(float(np.percentile(d_chrf, 97.5)), 2)],
                 "p_value_chrF": round(float((d_chrf <= 0).mean()), 4)}
json.dump(res, open(f"{args.dir}/significance_{args.new}_vs_{args.base}.json", "w"), indent=2)
print(json.dumps(res, indent=1))
