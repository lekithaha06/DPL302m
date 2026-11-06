#!/usr/bin/env python3
"""VIỆC 3 – Task 2, TV4 Uyên viết, Kiệt chạy.

NHIỆM VỤ: thống kê mô tả (EDA) trên dữ liệu ĐÃ LÀM SẠCH: tỉ lệ train/val/test, phân bố người nói, giới tính,
độ dài audio, độ dài câu, số bản thu mỗi câu, miền văn bản PhoMT. Vẽ biểu đồ PNG cho slide 6 và tự viết
NHẬN XÉT ĐỊNH LƯỢNG (có %) cho mục 1.3 của báo cáo.
Chạy SAU viec2_lam_sach_du_lieu.py.

Chạy:
    pip install matplotlib
    python scripts/data/viec3_eda.py
Tuỳ chọn: --bo_phomt (không đọc PhoMT, chỉ dùng bảng miền từ paper).

Đầu ra trong --report_dir/eda (không có câu chữ, commit được):
    eda_01_ti_le_tap.png ... eda_07_mien_phomt.png   biểu đồ
    eda_bang_*.csv                                   bảng số liệu đằng sau từng biểu đồ
    eda_nhan_xet.md                                  nhận xét định lượng tự sinh từ số đếm
    eda_tom_tat.json                                 toàn bộ số liệu
"""
import argparse
import csv
import datetime
import json
import platform
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from ham_dung_chung import ensure_phomt, lib_versions

SPLITS = ["train", "dev", "test"]
SPLIT_VI = {"train": "Train", "dev": "Val (dev)", "test": "Test"}
# Bảng miền PhoMT: Table 1 của paper PhoMT (Doan et al., EMNLP 2021, arXiv 2110.12199). File dữ liệu không có nhãn miền từng câu.
PHOMT_DOMAINS = {  # miền: (train, dev, test) số cặp câu
    "OpenSubtitles": (1529772, 9635, 9564), "WikiHow": (507379, 3212, 3246), "MediaWiki": (490505, 3024, 3270),
    "TED-Talks": (316808, 1994, 2000), "Blogspot": (92545, 597, 814), "News": (40990, 257, 257),
}
# Màu: bảng màu tham chiếu đã kiểm mù màu (3 màu đầu dùng chung được với mọi cặp)
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


# ---------------------------------------------------------------- đọc dữ liệu

def load_clean(args):
    recs = []
    for p in sorted((args.data_dir / "clean").glob("*_*.jsonl")):
        with open(p, encoding="utf-8") as f:
            recs += [json.loads(line) for line in f]
    if not recs:
        raise SystemExit(f"Không thấy {args.data_dir}/clean/*.jsonl. Chạy viec2_lam_sach_du_lieu.py trước.")
    return recs


def phomt_lengths(args):
    """Phân bố số từ mỗi câu PhoMT (đọc từng dòng). Train lấy bản đã làm sạch nếu có."""
    files = ensure_phomt(args.phomt_dir)
    clean = args.data_dir / "clean" / "phomt"
    out = {}
    for split in SPLITS:
        for lang in ("vi", "en"):
            p = clean / f"train.{lang}" if split == "train" and (clean / f"train.{lang}").exists() else files[(split, lang)]
            c = Counter()
            with open(p, encoding="utf-8") as f:
                for line in f:
                    c[len(line.split())] += 1
            out[(split, lang)] = c
    return out


# ---------------------------------------------------------------- thống kê

def pct(a, b):
    return round(100 * a / b, 2) if b else 0.0


def desc(values):
    if not values:
        return {}
    v = sorted(values)
    q = statistics.quantiles(v, n=20) if len(v) >= 2 else [v[0]] * 19
    return {"n": len(v), "mean": round(statistics.mean(v), 2), "median": round(statistics.median(v), 2),
            "min": round(v[0], 2), "p5": round(q[0], 2), "p95": round(q[18], 2), "max": round(v[-1], 2)}


def desc_counter(c):
    """Thống kê từ Counter {giá_trị: số_lần} mà không bung ra danh sách (PhoMT 3 triệu câu)."""
    n = sum(c.values())
    if not n:
        return {}
    items = sorted(c.items())
    mean = sum(k * m for k, m in items) / n

    def q(p):
        acc = 0
        for k, m in items:
            acc += m
            if acc >= p * n:
                return k
        return items[-1][0]
    return {"n": n, "mean": round(mean, 2), "median": q(0.5), "min": items[0][0], "p5": q(0.05), "p95": q(0.95),
            "max": items[-1][0]}


def compute(recs, plen):
    S = {}
    by = defaultdict(list)
    for r in recs:
        by[(r["dataset"], r["split"])].append(r)
    datasets = sorted({r["dataset"] for r in recs})

    # 1. Tỉ lệ tập
    S["ti_le_tap"] = []
    for ds in datasets:
        tot_n = sum(len(by[(ds, s)]) for s in SPLITS)
        tot_h = sum(r["dur"] for s in SPLITS for r in by[(ds, s)]) / 3600
        for s in SPLITS:
            rs = by[(ds, s)]
            if not rs:
                continue
            h = sum(r["dur"] for r in rs) / 3600
            S["ti_le_tap"].append({"dataset": ds, "split": s, "so_mau": len(rs), "pct_mau": pct(len(rs), tot_n),
                                   "gio": round(h, 3), "pct_gio": pct(h, tot_h),
                                   "so_cau_goc": len({r["group"] for r in rs}),
                                   "so_nguoi_noi": len({r["speaker"] for r in rs if r["speaker"]}) or None})
    if plen:
        tot = sum(sum(plen[(s, "vi")].values()) for s in SPLITS)
        for s in SPLITS:
            n = sum(plen[(s, "vi")].values())
            S["ti_le_tap"].append({"dataset": "phomt", "split": s, "so_mau": n, "pct_mau": pct(n, tot), "gio": None,
                                   "pct_gio": None, "so_cau_goc": n, "so_nguoi_noi": None})

    # 2. Người nói (chỉ VIVOS có ID người nói)
    S["nguoi_noi"] = {}
    for s in ("train", "test"):
        c = Counter(r["speaker"] for r in by[("vivos", s)])
        if c:
            vals = list(c.values())
            S["nguoi_noi"][s] = {"so_nguoi_noi": len(c), "cau_moi_nguoi": desc(vals),
                                 "ti_le_max_min": round(max(vals) / min(vals), 2),
                                 "pct_cau_cua_5_nguoi_nhieu_nhat": pct(sum(sorted(vals)[-5:]), sum(vals)),
                                 "dem": dict(sorted(c.items(), key=lambda kv: -kv[1]))}

    # 3. Giới tính
    S["gioi_tinh"] = []
    for ds in datasets:
        for s in SPLITS:
            rs = by[(ds, s)]
            if not rs:
                continue
            c = Counter(gender_vi(r["gender"]) for r in rs)
            row = {"dataset": ds, "split": s, "don_vi": "mẫu", **{k: c.get(k, 0) for k in ("Nam", "Nữ", "Không rõ")}}
            row.update({f"pct_{k}": pct(row[k], len(rs)) for k in ("Nam", "Nữ", "Không rõ")})
            S["gioi_tinh"].append(row)
            if ds == "vivos":
                spk = {r["speaker"]: gender_vi(r["gender"]) for r in rs}
                c2 = Counter(spk.values())
                row = {"dataset": ds, "split": s, "don_vi": "người nói", **{k: c2.get(k, 0) for k in ("Nam", "Nữ", "Không rõ")}}
                row.update({f"pct_{k}": pct(row[k], len(spk)) for k in ("Nam", "Nữ", "Không rõ")})
                S["gioi_tinh"].append(row)

    # 4. Độ dài audio
    S["thoi_luong"] = {}
    for ds in datasets:
        for s in SPLITS:
            d = [r["dur"] for r in by[(ds, s)]]
            if d:
                S["thoi_luong"][f"{ds}_{s}"] = {**desc(d), "pct_tren_30s": pct(sum(x > 30 for x in d), len(d)),
                                                "so_tren_30s": sum(x > 30 for x in d)}

    # 5. Số bản thu mỗi câu (FLEURS)
    S["ban_thu_moi_cau"] = {}
    for s in SPLITS:
        c = Counter(r["group"] for r in by[("fleurs", s)])
        if c:
            dist = Counter(c.values())
            S["ban_thu_moi_cau"][s] = {"so_cau": len(c), "phan_bo": {str(k): dist[k] for k in sorted(dist)},
                                       "pct": {str(k): pct(dist[k], len(c)) for k in sorted(dist)},
                                       "trung_binh": round(sum(c.values()) / len(c), 2)}

    # 6. Độ dài câu (số từ)
    S["do_dai_cau"] = {}
    for ds in datasets:
        for s in SPLITS:
            rs = by[(ds, s)]
            if rs:
                S["do_dai_cau"][f"{ds}_{s}_vi"] = desc([len(r["text_vi_norm"].split()) for r in rs])
                if ds == "fleurs":
                    S["do_dai_cau"][f"{ds}_{s}_en"] = desc([len((r["text_en"] or "").split()) for r in rs])
    if plen:
        for (s, lang), c in plen.items():
            S["do_dai_cau"][f"phomt_{s}_{lang}"] = desc_counter(c)

    # 7. Miền PhoMT (theo paper)
    S["mien_phomt"] = []
    for i, s in enumerate(SPLITS):
        tot = sum(v[i] for v in PHOMT_DOMAINS.values())
        for dom, v in PHOMT_DOMAINS.items():
            S["mien_phomt"].append({"split": s, "mien": dom, "so_cap": v[i], "pct": pct(v[i], tot)})
    tr = [v[0] for v in PHOMT_DOMAINS.values()]
    S["mien_phomt_ti_le_max_min_train"] = round(max(tr) / min(tr), 1)
    return S, by


def gender_vi(g):
    g = (g or "").strip().lower()
    return "Nam" if g in ("m", "male") else "Nữ" if g in ("f", "female") else "Không rõ"


# ---------------------------------------------------------------- vẽ

def style(plt):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
                         "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlecolor": INK, "figure.dpi": 100})


def save(fig, out, name, note):
    fig.text(0.01, 0.01, note, fontsize=8.5, color=INK2, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(out / name, dpi=200, facecolor="white")


def plot_all(S, by, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    style(plt)
    colors = {"train": C1, "dev": C2, "test": C3}

    # 01 Tỉ lệ train/val/test: thanh 100% chồng, mỗi bộ dữ liệu 1 hàng
    rows = S["ti_le_tap"]
    dss = [d for d in ("vivos", "fleurs", "phomt") if any(r["dataset"] == d for r in rows)]
    fig, ax = plt.subplots(figsize=(10, 1.4 + 0.9 * len(dss)))
    for y, ds in enumerate(dss):
        left = 0
        for s in SPLITS:
            r = next((r for r in rows if r["dataset"] == ds and r["split"] == s), None)
            if not r:
                continue
            ax.barh(y, r["pct_mau"], left=left, color=colors[s], height=0.55, edgecolor="white", linewidth=2)
            if r["pct_mau"] >= 4:
                ax.text(left + r["pct_mau"] / 2, y, f"{r['pct_mau']:.1f}%\n{r['so_mau']:,}".replace(",", "."),
                        ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
            left += r["pct_mau"]
    ax.set_yticks(range(len(dss)), [d.upper() for d in dss])
    ax.set_xlim(0, 100)
    ax.set_xlabel("% số mẫu (bản thu / cặp câu)")
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.legend([plt.Rectangle((0, 0), 1, 1, color=colors[s]) for s in SPLITS], [SPLIT_VI[s] for s in SPLITS],
              ncols=3, loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False)
    ax.set_title("Tỉ lệ Train / Val / Test (giữ split gốc)", pad=28)
    save(fig, out, "eda_01_ti_le_tap.png", "Nguồn: dữ liệu sau làm sạch (viec2_lam_sach_du_lieu.py). VIVOS không có tập dev chính thức.")
    plt.close(fig)

    # 02 Số câu mỗi người nói VIVOS
    nn = S["nguoi_noi"]
    if nn:
        fig, axes = plt.subplots(1, len(nn), figsize=(12, 4.6), gridspec_kw={"width_ratios": [nn[s]["so_nguoi_noi"] for s in nn]})
        axes = axes if len(nn) > 1 else [axes]
        for ax, s in zip(axes, nn):
            dem = nn[s]["dem"]
            ax.bar(range(len(dem)), list(dem.values()), color=colors[s], width=0.8)
            m = nn[s]["cau_moi_nguoi"]["mean"]
            ax.axhline(m, color=INK2, linewidth=1, linestyle="--")
            ax.text(len(dem) - 0.5, m, f"TB {m:.0f}", ha="right", va="bottom", color=INK2, fontsize=9)
            ax.set_xticks([])
            ax.set_xlabel(f"{nn[s]['so_nguoi_noi']} người nói (xếp giảm dần)")
            ax.set_title(f"VIVOS {SPLIT_VI[s]} (max/min = {nn[s]['ti_le_max_min']}×)", fontsize=11.5)
            ax.grid(axis="x", visible=False)
        axes[0].set_ylabel("Số câu mỗi người nói")
        save(fig, out, "eda_02_vivos_nguoi_noi.png", "FLEURS không có ID người nói nên không vẽ được biểu đồ này cho FLEURS.")
        plt.close(fig)

    # 03 Giới tính
    g = S["gioi_tinh"]
    labels = [f"{r['dataset'].upper()} {SPLIT_VI[r['split']]}" + (" (theo người nói)" if r["don_vi"] == "người nói" else "")
              for r in g]
    fig, ax = plt.subplots(figsize=(10, 1.2 + 0.5 * len(g)))
    gcol = {"Nam": C1, "Nữ": C2, "Không rõ": "#b5b4ad"}
    for y, r in enumerate(g):
        left = 0
        for k in ("Nam", "Nữ", "Không rõ"):
            v = r[f"pct_{k}"]
            if v:
                ax.barh(y, v, left=left, color=gcol[k], height=0.6, edgecolor="white", linewidth=2)
                if v >= 6:
                    ax.text(left + v / 2, y, f"{v:.0f}%", ha="center", va="center", color="white", fontsize=9, fontweight="bold")
                left += v
    handles = [plt.Rectangle((0, 0), 1, 1, color=gcol[k]) for k in gcol]
    ax.legend(handles, list(gcol), ncols=3, loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False)
    ax.set_yticks(range(len(g)), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("%")
    ax.grid(axis="y", visible=False)
    ax.set_title("Phân bố giới tính (theo nhãn có sẵn của dataset)", pad=28)
    save(fig, out, "eda_03_gioi_tinh.png", "Giới tính lấy từ nhãn gốc (FLEURS: cột gender; VIVOS: genders.txt). Nhóm chưa nghe kiểm lại.")
    plt.close(fig)

    # 04 Độ dài audio: histogram nhỏ cho từng bộ (cùng trục x để so)
    dss = [d for d in ("vivos", "fleurs") if any(k.startswith(d) for k in S["thoi_luong"])]
    if dss:
        allmax = max(S["thoi_luong"][k]["max"] for k in S["thoi_luong"])
        fig, axes = plt.subplots(len(dss), 1, figsize=(10, 2.8 * len(dss)), sharex=True)
        axes = axes if len(dss) > 1 else [axes]
        bins = [i * 0.5 for i in range(int(allmax / 0.5) + 2)]
        for ax, ds in zip(axes, dss):
            d = [r["dur"] for s in SPLITS for r in by[(ds, s)]]
            ax.hist(d, bins=bins, color=C1 if ds == "vivos" else C2, edgecolor="white", linewidth=0.6)
            st = desc(d)
            top = ax.get_ylim()[1]
            ax.set_ylim(0, top * 1.12)
            ax.axvline(st["median"], color=INK, linewidth=1)
            ax.text(st["median"], top * 1.04, f" trung vị {st['median']} s", color=INK, fontsize=9)
            ax.axvline(30, color=INK2, linewidth=1, linestyle="--")
            ax.text(29.7, top * 1.04, "30 s (Whisper cắt đoạn) ", color=INK2, fontsize=9, ha="right")
            ax.set_ylabel("Số bản thu")
            ax.set_title(f"{ds.upper()}: TB {st['mean']} s, p95 {st['p95']} s, dài nhất {st['max']} s", fontsize=11.5, loc="left")
        axes[-1].set_xlabel("Độ dài audio (giây)")
        save(fig, out, "eda_04_thoi_luong.png", "Gộp các tập của mỗi bộ; số theo từng tập xem eda_bang_thoi_luong.csv.")
        plt.close(fig)

    # 05 Số bản thu mỗi câu FLEURS
    b = S["ban_thu_moi_cau"]
    if b:
        ks = sorted({k for s in b for k in b[s]["pct"]}, key=int)
        fig, ax = plt.subplots(figsize=(9, 4.6))
        w = 0.8 / len(b)
        for i, s in enumerate(b):
            xs = [j + (i - (len(b) - 1) / 2) * w for j in range(len(ks))]
            vals = [b[s]["pct"].get(k, 0) for k in ks]
            ax.bar(xs, vals, width=w * 0.92, color=colors[s], label=f"{SPLIT_VI[s]} ({b[s]['so_cau']} câu, TB {b[s]['trung_binh']})")
            for x, v in zip(xs, vals):
                if v:
                    ax.text(x, v + 1, f"{v:.0f}%", ha="center", fontsize=8.5, color=INK2)
        ax.set_xticks(range(len(ks)), [f"{k} bản thu" for k in ks])
        ax.set_ylabel("% số câu gốc")
        ax.grid(axis="x", visible=False)
        ax.legend(frameon=False)
        ax.set_title("FLEURS: số bản thu cho mỗi câu gốc")
        save(fig, out, "eda_05_ban_thu_moi_cau.png", "Câu có nhiều bản thu được 'nhìn thấy' nhiều lần khi dạy → mất cân bằng theo câu (xử lý ở việc 4).")
        plt.close(fig)

    # 06 Độ dài câu (số từ): mỗi bộ 1 hộp p5–p95 + trung vị
    dd = S["do_dai_cau"]
    keys = [k for k in dd if k.endswith("_vi") or k.startswith("fleurs") or k.startswith("phomt")]
    if keys:
        fig, ax = plt.subplots(figsize=(10, 0.9 + 0.38 * len(keys)))
        for y, k in enumerate(keys):
            st = dd[k]
            ds, s, lang = k.split("_")
            col = {"vivos": C1, "fleurs": C2, "phomt": C3}[ds]
            ax.plot([st["p5"], st["p95"]], [y, y], color=col, linewidth=6, solid_capstyle="round", alpha=0.45)
            ax.plot([st["median"]], [y], "o", color=col, markersize=8, markeredgecolor="white", markeredgewidth=2)
            ax.text(st["p95"] + 0.6, y, f"TB {st['mean']}", va="center", fontsize=8.5, color=INK2)
        ax.set_yticks(range(len(keys)), [f"{k.split('_')[0].upper()} {SPLIT_VI[k.split('_')[1]]} ({k.split('_')[2]})" for k in keys])
        ax.invert_yaxis()
        ax.set_xlabel("Số từ mỗi câu (chấm = trung vị, thanh = khoảng 5%–95%)")
        ax.grid(axis="y", visible=False)
        ax.set_title("Độ dài câu theo bộ dữ liệu")
        save(fig, out, "eda_06_do_dai_cau.png", "Tiếng Việt đếm theo âm tiết (tách bằng khoảng trắng) sau chuẩn hoá; tiếng Anh đếm theo từ.")
        plt.close(fig)

    # 07 Miền PhoMT (train) – cột ngang, có %
    tr = [r for r in S["mien_phomt"] if r["split"] == "train"]
    tr.sort(key=lambda r: r["pct"])
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.barh([r["mien"] for r in tr], [r["pct"] for r in tr], color=C3, height=0.6)
    for i, r in enumerate(tr):
        ax.text(r["pct"] + 0.6, i, f"{r['pct']:.1f}%  ({r['so_cap']:,} cặp)".replace(",", "."), va="center", fontsize=9.5, color=INK)
    ax.set_xlim(0, max(r["pct"] for r in tr) * 1.35)
    ax.set_xlabel("% số cặp câu PhoMT train")
    ax.grid(axis="y", visible=False)
    ax.set_title(f"PhoMT train theo miền (lớn nhất / nhỏ nhất = {S['mien_phomt_ti_le_max_min_train']}×)")
    save(fig, out, "eda_07_mien_phomt.png", "Nguồn: Table 1, Doan et al. (EMNLP 2021), arXiv 2110.12199. Dữ liệu PhoMT không có nhãn miền từng câu.")
    plt.close(fig)


# ---------------------------------------------------------------- nhận xét định lượng

def comments(S):
    c = []
    t = {(r["dataset"], r["split"]): r for r in S["ti_le_tap"]}
    for ds in ("vivos", "fleurs", "phomt"):
        parts = [f"{SPLIT_VI[s]} {t[(ds, s)]['pct_mau']}% ({t[(ds, s)]['so_mau']:,} mẫu)".replace(",", ".")
                 for s in SPLITS if (ds, s) in t]
        if parts:
            c.append(f"**Tỉ lệ tập {ds.upper()}** (theo số mẫu): " + ", ".join(parts) + ". Giữ split gốc, không chia lại 80/10/10.")
    for s, v in S["nguoi_noi"].items():
        d = v["cau_moi_nguoi"]
        c.append(f"**VIVOS {SPLIT_VI[s]}**: {v['so_nguoi_noi']} người nói, mỗi người {d['min']}–{d['max']} câu (TB {d['mean']}); "
                 f"người nhiều nhất gấp {v['ti_le_max_min']} lần người ít nhất; 5 người nhiều nhất chiếm "
                 f"{v['pct_cau_cua_5_nguoi_nhieu_nhat']}% số câu.")
    for r in S["gioi_tinh"]:
        c.append(f"**Giới tính {r['dataset'].upper()} {SPLIT_VI[r['split']]}** (theo {r['don_vi']}): Nam {r['pct_Nam']}%, "
                 f"Nữ {r['pct_Nữ']}%" + (f", không rõ {r['pct_Không rõ']}%" if r["pct_Không rõ"] else "") + ".")
    tl = S["thoi_luong"]
    for k, v in tl.items():
        ds, s = k.split("_")
        c.append(f"**Độ dài audio {ds.upper()} {SPLIT_VI[s]}**: TB {v['mean']} s, trung vị {v['median']} s, "
                 f"5%–95% trong khoảng {v['p5']}–{v['p95']} s; {v['so_tren_30s']} bản thu ({v['pct_tren_30s']}%) dài hơn 30 s.")
    if "vivos_test" in tl and "fleurs_test" in tl:
        c.append(f"Bản thu FLEURS test dài gấp {round(tl['fleurs_test']['mean'] / tl['vivos_test']['mean'], 1)} lần VIVOS test "
                 f"(TB {tl['fleurs_test']['mean']} s so với {tl['vivos_test']['mean']} s) → kết quả trên VIVOS không đại diện audio dài.")
    for s, v in S["ban_thu_moi_cau"].items():
        c.append(f"**FLEURS {SPLIT_VI[s]}**: {v['so_cau']} câu gốc, TB {v['trung_binh']} bản thu/câu; phân bố "
                 + ", ".join(f"{k} bản thu: {p}%" for k, p in v["pct"].items()) + ".")
    tr = sorted([r for r in S["mien_phomt"] if r["split"] == "train"], key=lambda r: -r["pct"])
    te = {r["mien"]: r["pct"] for r in S["mien_phomt"] if r["split"] == "test"}
    c.append(f"**Miền PhoMT train** (theo paper): {tr[0]['mien']} {tr[0]['pct']}%, nhỏ nhất {tr[-1]['mien']} {tr[-1]['pct']}% "
             f"(chênh {S['mien_phomt_ti_le_max_min_train']} lần); ở test, {tr[0]['mien']} chiếm {te[tr[0]['mien']]}%. "
             "→ Mô hình dịch nghiêng về văn nói kiểu phụ đề; FLEURS là câu kiểu Wikipedia (khác miền).")
    dd = S["do_dai_cau"]
    if "fleurs_test_vi" in dd and "vivos_test_vi" in dd:
        c.append(f"**Độ dài câu**: FLEURS test TB {dd['fleurs_test_vi']['mean']} âm tiết/câu, VIVOS test "
                 f"{dd['vivos_test_vi']['mean']}" + (f", PhoMT test {dd['phomt_test_vi']['mean']}" if "phomt_test_vi" in dd else "") + ".")
    return c


def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data_dir", type=Path, default=Path("data"))
    ap.add_argument("--report_dir", type=Path, default=Path("reports/task2/data"))
    ap.add_argument("--phomt_dir", type=Path, default=None, help="mặc định <data_dir>/phomt")
    ap.add_argument("--bo_phomt", action="store_true")
    args = ap.parse_args()
    args.phomt_dir = args.phomt_dir or args.data_dir / "phomt"
    out = args.report_dir / "eda"
    out.mkdir(parents=True, exist_ok=True)

    recs = load_clean(args)
    plen = None if args.bo_phomt else phomt_lengths(args)
    S, by = compute(recs, plen)
    plot_all(S, by, out)
    cm = comments(S)

    write_csv(out / "eda_bang_ti_le_tap.csv", S["ti_le_tap"])
    write_csv(out / "eda_bang_gioi_tinh.csv", S["gioi_tinh"])
    write_csv(out / "eda_bang_thoi_luong.csv", [{"bo_tap": k, **v} for k, v in S["thoi_luong"].items()])
    write_csv(out / "eda_bang_do_dai_cau.csv", [{"bo_tap_ngon_ngu": k, **v} for k, v in S["do_dai_cau"].items()])
    write_csv(out / "eda_bang_mien_phomt.csv", S["mien_phomt"])
    write_csv(out / "eda_bang_nguoi_noi_vivos.csv",
              [{"split": s, "speaker": k, "so_cau": n} for s, v in S["nguoi_noi"].items() for k, n in v["dem"].items()])
    write_csv(out / "eda_bang_ban_thu_moi_cau.csv",
              [{"split": s, "so_ban_thu": k, "so_cau": v["phan_bo"][k], "pct": v["pct"][k]} for s, v in S["ban_thu_moi_cau"].items() for k in v["phan_bo"]])
    (out / "eda_nhan_xet.md").write_text("# Nhận xét định lượng (tự sinh từ số đếm, mục 1.3 / slide 6)\n\n"
                                         + "\n".join(f"- {x}" for x in cm) + "\n", encoding="utf-8")
    S["meta"] = {"script": "viec3_eda.py", "time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                 "versions": {**lib_versions(), "matplotlib": __import__("matplotlib").__version__}, "platform": platform.platform()}
    (out / "eda_tom_tat.json").write_text(json.dumps(S, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n".join(f"- {x}" for x in cm))
    print(f"\nBiểu đồ + bảng (commit được): {out}/")


if __name__ == "__main__":
    main()
