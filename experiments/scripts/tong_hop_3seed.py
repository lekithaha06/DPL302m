#!/usr/bin/env python3
"""Tổng hợp 3 seed theo reports/ba_seed/QUY_TAC_3SEED.md. Seed 42 lấy ở runs/mt/<V>, seed 1 và 2 ở runs/ba_seed/modal/runs/mt/<V>_s<seed>."""
import csv
import json
import statistics as st
import sys
from pathlib import Path

T = Path(__file__).resolve().parents[1]; M = T / "runs/ba_seed/modal/runs/mt"; R = T / "reports/ba_seed"
sys.stdout.reconfigure(encoding="utf-8")
TAP = {"dev cascade": "fleurs_dev_asr_pho", "dev sạch": "fleurs_dev_clean", "test cascade": "fleurs_test_asr_pho", "test sạch": "fleurs_test_clean", "Whisper → dịch": "fleurs_test_asr_wsp"}
J = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))


def sc(v, s, t):
    p = (T / f"runs/mt/{v}/{t}/score.json") if s == 42 else (M / f"{v}_s{s}/{t}/score.json")
    return J(p) if p.exists() else None  # V1 seed 42 chưa chạy Whisper → dịch


rows, tb = [], {}
for v in ("V1", "V2", "V3", "V4"):
    for k, t in TAP.items():
        kq_ = [sc(v, s, t) for s in (42, 1, 2)]; x = [q["BLEU"] if q else None for q in kq_]; c = [q["chrF++"] for q in kq_ if q]; y = [q for q in x if q is not None]
        m, d = round(st.mean(y), 2), round(st.stdev(y), 2); tb[v, k] = m
        rows.append({"bản": v, "chỉ số": k, "seed 42": x[0], "seed 1": x[1], "seed 2": x[2], "trung bình": m, "độ lệch chuẩn": d, "chrF++ trung bình": round(st.mean(c), 2), "n": len(y)})
R.mkdir(parents=True, exist_ok=True)
with open(R / "bang_3seed.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows:
    print(r["bản"], f"{r['chỉ số']:15}", r["seed 42"], r["seed 1"], r["seed 2"], "→", r["trung bình"], "±", r["độ lệch chuẩn"])
b0 = {k: J(T / f"runs/mt/B0/{t}/score.json")["BLEU"] for k, t in TAP.items()}
print("B0", b0)
M_ = max(tb[v, "dev cascade"] for v in ("V1", "V2", "V3", "V4")); hoa = [v for v in ("V1", "V2", "V3", "V4") if tb[v, "dev cascade"] >= M_ - .5]
chon = max(hoa, key=lambda v: tb[v, "dev sạch"])
dk = {"dev cascade": {}, "dev sạch": {}, "test cascade": {}, "test sạch": {}, "Whisper → dịch": {}}
for k, t in TAP.items():
    dk[k] = {"seed 42 máy nhóm (torch 2.0.1)": J(T / f"runs/mt/V2/{t}/score.json")["BLEU"], "seed 42 Modal (train torch 2.7.1)": J(M / f"V2_s42/{t}/score.json")["BLEU"]}
kq = {"M_dev_cascade_tb": M_, "nhom_hoa": hoa, "quy_tac_tren_trung_binh_ra": chon, "ban_cuoi_giu_nguyen": "V2", "doi_chung_phan_cung_V2_s42": dk, "epoch_tot_nhat": {f"{v}_s{s}": J(T / f"runs/ba_seed/modal/checkpoints/{v}_s{s}/best/chon.json")["best_epoch"] for v in ("V1", "V2", "V3", "V4") for s in (1, 2)}}
(R / "ket_qua_3seed.json").write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(kq, ensure_ascii=False, indent=1))
