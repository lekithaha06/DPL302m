#!/usr/bin/env python3
"""H3: bootstrap ghép cặp (cùng ID) cho chênh WER whisper-small − PhoWhisper-small, theo cụm sent_id (FLEURS) / id (VIVOS), 1000 lần, seed 42."""
import csv, json, random
from collections import defaultdict
from pathlib import Path
T = Path(__file__).resolve().parents[2]
out = {}
for ds in ("vivos", "fleurs"):
    A = {r["id"]: r for r in csv.DictReader(open(T / f"runs/asr/kiet_t2_phowhisper-small_{ds}_test/score/per_utterance.csv", encoding="utf-8-sig"))}
    B = {r["id"]: r for r in csv.DictReader(open(T / f"runs/asr/kiet_t2_whisper-small_{ds}_test/score/per_utterance.csv", encoding="utf-8-sig"))}
    assert A.keys() == B.keys()
    cl = defaultdict(list)
    for i, r in A.items():
        cl[r["sent_id"] or i].append(i)
    keys = sorted(cl)
    w = lambda S, ids: 100 * sum(int(S[i]["S"]) + int(S[i]["D"]) + int(S[i]["I"]) for i in ids) / sum(int(S[i]["N"]) for i in ids)
    rng = random.Random(42); d = []
    for _ in range(1000):
        ids = [i for k in rng.choices(keys, k=len(keys)) for i in cl[k]]
        d.append(w(B, ids) - w(A, ids))
    d.sort(); allids = list(A)
    out[ds] = {"WER_pho": round(w(A, allids), 2), "WER_whisper": round(w(B, allids), 2), "delta_whisper_minus_pho": round(w(B, allids) - w(A, allids), 2),
               "ci95": [round(d[25], 2), round(d[974], 2)], "n_clusters": len(keys)}
(T / "reports/asr/bootstrap_wer_H3.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out))
