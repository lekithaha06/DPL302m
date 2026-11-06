#!/usr/bin/env python3
"""Tổng hợp bảng ablation + vẽ biểu đồ cho báo cáo/slide từ kết quả đã chạy (không tính lại gì ngoài đọc score.json).

Đầu ra reports/tong_hop/:
  ablation.csv / ablation.md     B0, V1..Vn: BLEU/chrF++ dev cascade, test cascade, test sạch, dev sạch, PhoMT test
  ablation.png                   cột BLEU test cascade + đường test sạch / PhoMT
  mien_giao_duc.png              BLEU cascade test theo miền cho từng phiên bản (nếu có reports/domain/ket_qua_theo_mien.csv)
  asr_baseline.png               WER 2 baseline ASR × 2 bộ test (paper vs nhóm)
"""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

T = Path(__file__).resolve().parents[1]
OUT = T / "reports" / "tong_hop"
SETS = [("fleurs_dev_asr_pho", "dev cascade"), ("fleurs_test_asr_pho", "test cascade"), ("fleurs_test_clean", "test sạch"),
        ("fleurs_dev_clean", "dev sạch"), ("phomt_test", "PhoMT test")]


def score(v, s):
    p = T / "runs" / "mt" / v / s / "score.json"
    if not p.exists():
        return None, None
    j = json.loads(p.read_text(encoding="utf-8"))
    return j["BLEU"], j["chrF++"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    vers = ["B0"] + sorted(p.name for p in (T / "runs" / "mt").iterdir() if p.name.startswith("V") and p.is_dir())
    rows = []
    for v in vers:
        r = {"phien_ban": v}
        for s, name in SETS:
            b, c = score(v, s)
            r[f"BLEU {name}"], r[f"chrF++ {name}"] = b, c
        ch = T / "checkpoints" / v / "best" / "chon.json"
        r["epoch_chon"] = json.loads(ch.read_text(encoding="utf-8"))["best_epoch"] if ch.exists() else ""
        rows.append(r)
    with open(OUT / "ablation.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    hdr = ["Phiên bản", "epoch"] + [n for _, n in SETS]
    md = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for r in rows:
        md.append("| " + " | ".join([r["phien_ban"], str(r["epoch_chon"])] + [("" if r[f"BLEU {n}"] is None else f"{r[f'BLEU {n}']:.2f}") for _, n in SETS]) + " |")
    (OUT / "ablation.md").write_text("BLEU (sacreBLEU 2.4.3, beam 5)\n\n" + "\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))

    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = range(len(rows))
    tc = [r["BLEU test cascade"] or 0 for r in rows]
    bars = ax.bar(x, tc, color="#4C72B0", label="test cascade (ASR → MT)")
    for b, v in zip(bars, tc):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.3, f"{v:.2f}", ha="center", fontsize=9)
    ax.plot(x, [r["BLEU test sạch"] for r in rows], "o-", c="#DD8452", label="test transcript sạch")
    ax.plot(x, [r["BLEU PhoMT test"] for r in rows], "s--", c="#55A868", label="PhoMT test")
    ax.set_xticks(list(x), [r["phien_ban"] for r in rows]); ax.set_ylabel("BLEU"); ax.set_ylim(0, 45)
    ax.set_title("Ablation khối dịch: B0 → V1 → … (FLEURS test 857 bản thu, PhoMT test 19.151 câu)", fontsize=10)
    ax.legend(loc="lower right", fontsize=8); fig.tight_layout(); fig.savefig(OUT / "ablation.png", dpi=150)

    dom = T / "reports" / "domain" / "ket_qua_theo_mien.csv"
    if dom.exists():
        D = [r for r in csv.DictReader(open(dom, encoding="utf-8-sig")) if r["khoi"] == "MT" and r["tap"] == "fleurs_test_asr_pho"]
        miens = sorted({r["mien"] for r in D}, key=lambda m: (not m.startswith("Giáo dục"), m))
        hs = [v for v in vers if any(r["he"] == v for r in D)]
        fig, ax = plt.subplots(figsize=(8, 4.2)); wdt = 0.8 / max(1, len(hs))
        for i, h in enumerate(hs):
            vals = [next((float(r["BLEU"]) for r in D if r["he"] == h and r["mien"] == m), 0) for m in miens]
            ax.bar([k + i * wdt for k in range(len(miens))], vals, wdt, label=h)
        ax.set_xticks([k + wdt * (len(hs) - 1) / 2 for k in range(len(miens))], [m.split(" (")[0] for m in miens])
        ax.set_ylabel("BLEU cascade test"); ax.set_title("BLEU cascade theo miền nguồn câu (FLoRes+)", fontsize=10); ax.legend(fontsize=8)
        fig.tight_layout(); fig.savefig(OUT / "mien_giao_duc.png", dpi=150)

    # flowchart làm sạch (số từ lam_sach_dem_tung_buoc.csv của script Uyên)
    st = list(csv.DictReader(open(T / "reports" / "data" / "lam_sach_dem_tung_buoc.csv", encoding="utf-8-sig")))
    fig, ax = plt.subplots(figsize=(13, 4.2)); ax.axis("off")
    for yi, (ds, name) in enumerate((("fleurs", "FLEURS vi_vn"), ("vivos", "VIVOS"))):
        steps = {}
        for r in st:
            if r["dataset"] == ds and r["buoc"] != "KET_QUA":
                s = steps.setdefault(r["buoc"], {"ten": r["ten_buoc"], "truoc": 0, "bi_loai": 0, "sau": 0})
                for k in ("truoc", "bi_loai", "sau"):
                    s[k] += int(r[k])
        keys = sorted(steps)
        y = 0.75 - yi * 0.5
        boxes = [(f"{name} gốc\n{steps[keys[0]]['truoc']:,} mẫu".replace(",", "."))] + \
                [f"{steps[k]['ten'].split(' (')[0].replace(' + ', chr(10) + '+ ')}\n−{steps[k]['bi_loai']} → {steps[k]['sau']:,}".replace(",", ".") for k in keys]
        n = len(boxes)
        for i, b in enumerate(boxes):
            x = 0.02 + i * (0.96 / n)
            ax.text(x + 0.46 / n, y, b, ha="center", va="center", fontsize=8, wrap=True,
                    bbox=dict(boxstyle="round,pad=0.4", fc="#E8F1FA" if i else "#FCE9D9", ec="#4C72B0"))
            if i:
                ax.annotate("", xy=(x + 0.02 / n, y), xytext=(x - 0.1 / n, y), arrowprops=dict(arrowstyle="->"))
    ax.text(0.5, 0.02, "PhoMT train: 2.977.999 → bỏ 829 cặp trùng, 0 dòng rỗng, 0 dòng trùng FLEURS test → 2.977.170 cặp", ha="center", fontsize=9)
    ax.set_title("Quy trình làm sạch (số mẫu sau từng bước, cộng mọi split) – script của Uyên, Kiệt chạy 30/10/2026", fontsize=10)
    fig.tight_layout(); fig.savefig(OUT / "flowchart_lam_sach.png", dpi=150)

    pc = list(csv.DictReader(open(T / "reports" / "asr" / "paper_comparison.csv", encoding="utf-8-sig")))
    fig, ax = plt.subplots(figsize=(7, 3.8))
    lab = [f"{r['model']}\n{r['dataset'].replace(' vi_vn', '')}" for r in pc]
    ax.bar([i - 0.2 for i in range(len(pc))], [float(r["group_WER_percent"]) for r in pc], 0.4, label="nhóm (Task 2)")
    ax.bar([i + 0.2 for i in range(len(pc))], [float(r["paper_WER_percent"]) if r["paper_WER_percent"] not in ("NR", "") else 0 for r in pc], 0.4, label="paper (0 = NR, không báo cáo)")
    ax.set_xticks(range(len(pc)), lab, fontsize=8); ax.set_ylabel("WER (%)"); ax.legend(fontsize=8)
    ax.set_title("Baseline ASR: paper vs nhóm", fontsize=10); fig.tight_layout(); fig.savefig(OUT / "asr_baseline.png", dpi=150)


if __name__ == "__main__":
    main()
