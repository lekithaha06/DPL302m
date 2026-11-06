#!/usr/bin/env python3
"""Chấm lại theo MIỀN (đặc biệt miền Giáo dục = wikijunior) trên dự đoán ĐÃ CÓ, không chạy model lại.

ASR: cộng S/D/I/N từ runs/asr/<run>/score/per_utterance.csv theo miền của sent_id → WER/CER từng miền.
MT : corpus BLEU / chrF++ từng miền từ runs/mt/<hệ>/<tập>/hyp.jsonl.
Miền lấy từ reports/domain/fleurs_mien.csv (scripts/data/gan_mien_flores.py). Đầu ra: reports/domain/ket_qua_theo_mien.{csv,md}
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

import sacrebleu

T = Path(__file__).resolve().parents[1]
MIEN_VI = {"wikibooks": "Giáo dục (Wikibooks – sách giáo khoa mở)", "wikinews": "Tin tức (Wikinews)", "wikivoyage": "Du lịch (Wikivoyage)"}


def main():
    mien = {(r["split"], r["sent_id"]): r["domain"] for r in csv.DictReader(open(T / "reports" / "domain" / "fleurs_mien.csv", encoding="utf-8-sig"))}
    rows = []
    for d in sorted((T / "runs" / "asr").glob("kiet_t2_*_fleurs_*")):
        pu = d / "score" / "per_utterance.csv"
        if not pu.exists() or d.name.endswith("beam1"):
            continue
        sp = d.name.rsplit("_", 1)[-1]
        g = defaultdict(lambda: defaultdict(int))
        for r in csv.DictReader(open(pu, encoding="utf-8-sig")):
            m = mien.get((sp, r["sent_id"]), "khong_ghep_duoc")
            for k in ("S", "D", "I", "N", "Sc", "Dc", "Ic", "Nc"):
                g[m][k] += int(r[k])
            g[m]["n"] += 1
        for m, s in sorted(g.items()):
            rows.append({"khoi": "ASR", "he": d.name.replace("kiet_t2_", ""), "tap": f"FLEURS {sp}", "mien": MIEN_VI.get(m, m), "n_ban_thu": s["n"],
                         "WER": round(100 * (s["S"] + s["D"] + s["I"]) / s["N"], 2), "CER": round(100 * (s["Sc"] + s["Dc"] + s["Ic"]) / s["Nc"], 2),
                         "BLEU": "", "chrF++": ""})
    bleu, chrf = sacrebleu.BLEU(), sacrebleu.CHRF(word_order=2)
    for hp in sorted((T / "runs" / "mt").glob("*/fleurs_*/hyp.jsonl")):
        he, tap = hp.parent.parent.name, hp.parent.name
        sp = tap.split("_")[1]
        data = {json.loads(l)["id"]: json.loads(l) for l in open(T / "runs" / "mt_data" / f"{tap}.jsonl", encoding="utf-8")}
        g = defaultdict(list)
        for l in open(hp, encoding="utf-8"):
            r = json.loads(l)
            g[mien.get((sp, data[r["id"]]["sent_id"]), "khong_ghep_duoc")].append(r)
        for m, rs in sorted(g.items()):
            H, R = [r["hyp"] for r in rs], [[r["ref"] for r in rs]]
            rows.append({"khoi": "MT", "he": he, "tap": tap, "mien": MIEN_VI.get(m, m), "n_ban_thu": len(rs), "WER": "", "CER": "",
                         "BLEU": round(bleu.corpus_score(H, R).score, 2), "chrF++": round(chrf.corpus_score(H, R).score, 2)})
    out = T / "reports" / "domain"
    with open(out / "ket_qua_theo_mien.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    md = ["| Khối | Hệ | Tập | Miền | n | WER | CER | BLEU | chrF++ |", "|---|---|---|---|---|---|---|---|---|"]
    md += [f"| {r['khoi']} | {r['he']} | {r['tap']} | {r['mien']} | {r['n_ban_thu']} | {r['WER']} | {r['CER']} | {r['BLEU']} | {r['chrF++']} |" for r in rows]
    (out / "ket_qua_theo_mien.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
