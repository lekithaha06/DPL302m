#!/usr/bin/env python3
"""VIỆC 4 – Task 2, TV4 Uyên viết, Kiệt chạy.

NHIỆM VỤ: xử lý mất cân bằng cho DỮ LIỆU DẠY (chỉ tập train; dev/test giữ nguyên) và vẽ biểu đồ TRƯỚC / SAU.
  (1) V1 – FLEURS train: lấy mẫu lại theo câu (mỗi câu gốc được dạy số lần như nhau, không phụ thuộc có 1, 2 hay
      3 bản thu) và theo độ dài câu (nhóm độ dài ít mẫu được lấy thêm, có làm mềm để không lặp quá nhiều).
  (2) V2 – trộn PhoMT: chọn tỉ lệ trộn FLEURS : PhoMT thay vì gộp nguyên 3 triệu cặp PhoMT (FLEURS sẽ chỉ còn
      ~0,1%); nếu có nhãn miền cho từng dòng PhoMT thì lấy mẫu theo miền với nhiệt độ T.
Không dùng augmentation âm thanh (nhóm không train khối nghe). Script KHÔNG kết luận cải thiện: hiệu quả phải đo
bằng cách train V1 có / không cân bằng (Kiệt) trên cùng dev/test.
Chạy SAU viec2_lam_sach_du_lieu.py.

Chạy:
    python scripts/data/viec4_can_bang_du_lieu.py
Tuỳ chọn chính:
    --alpha 0.5          độ mạnh cân bằng độ dài (0 = chỉ cân bằng theo câu, 1 = cân bằng hoàn toàn theo nhóm độ dài)
    --bins 15,25,35,45   ranh giới nhóm độ dài (số âm tiết tiếng Việt)
    --ti_le_phomt 1.0    số cặp PhoMT lấy cho V2 = ti_le_phomt × số mẫu FLEURS train sau cân bằng
    --phomt_mien FILE    (tuỳ chọn) file nhãn miền, mỗi dòng 1 nhãn, cùng thứ tự với PhoMT train sạch
    --nhiet_do 5         nhiệt độ T khi lấy mẫu theo miền (p ∝ n^(1/T))
    --muc_tieu max       max: lấy thêm cho đủ, không bỏ bản thu nào (mặc định); tb: giữ nguyên tổng số mẫu
    --seed 42

Đầu ra trong --report_dir/can_bang (không có câu chữ, commit được):
    can_bang_01_theo_cau.png, can_bang_02_do_dai.png, can_bang_03_nguon_v2.png [, can_bang_04_mien_phomt.png]
    can_bang_v1_so_lan.csv     uid, sent_id, nhóm độ dài, số lần xuất hiện trong dữ liệu dạy V1
    can_bang_v2_phomt_idx.txt  chỉ số dòng PhoMT train sạch được chọn cho V2
    can_bang_tom_tat.json      số trước / sau, tham số, seed
Đầu ra trong --data_dir/can_bang (có câu chữ, KHÔNG commit):
    v1_fleurs_train_can_bang.jsonl   danh sách mẫu dạy V1 sau cân bằng (mẫu lặp lại = dòng lặp lại)
"""
import argparse
import csv
import datetime
import json
import platform
import random
from collections import Counter, defaultdict
from pathlib import Path

from ham_dung_chung import lib_versions

C_BEFORE, C_AFTER = "#9aa0a6", "#2a78d6"   # trước = xám, sau = xanh (cùng 1 phép so sánh 2 trạng thái)
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def pct(a, b):
    return round(100 * a / b, 2) if b else 0.0


def bin_label(n, edges):
    lo = None
    for e in edges:
        if n <= e:
            return f"≤{e}" if lo is None else f"{lo + 1}–{e}"
        lo = e
    return f">{edges[-1]}"


def bin_order(edges):
    return [bin_label(e, edges) for e in edges] + [f">{edges[-1]}"]


# ---------------------------------------------------------------- V1: theo câu + độ dài

def balance_v1(rows, edges, alpha, seed, muc_tieu):
    """Mỗi câu gốc s được lấy c_s mẫu, kỳ vọng c_s = K × g(nhóm độ dài của s).
    K = số bản thu nhiều nhất của một câu (muc_tieu="max": chỉ lấy thêm, không bỏ bản thu nào)
      hoặc số mẫu gốc / số câu (muc_tieu="tb": giữ nguyên tổng số mẫu, câu nhiều bản thu bị bớt).
    g = (tỉ lệ câu thuộc nhóm)^(-alpha), chuẩn hoá để trung bình trên các câu = 1.
    c_s làm tròn ngẫu nhiên (phần lẻ 0,3 -> 30% lên 1) để tổng đúng kỳ vọng, không bị làm tròn xoá mất hiệu ứng.
    Các bản thu của cùng một câu được dùng xoay vòng (thứ tự xáo theo seed) nên bản thu nào cũng được dùng đều."""
    rng = random.Random(seed)
    by_sent = defaultdict(list)
    for r in rows:
        by_sent[r["group"]].append(r)
    sent_bin = {s: bin_label(len(rs[0]["text_vi_norm"].split()), edges) for s, rs in by_sent.items()}
    n_sent = len(by_sent)
    frac = {b: c / n_sent for b, c in Counter(sent_bin.values()).items()}
    g = {b: f ** (-alpha) for b, f in frac.items()}
    mean_g = sum(g[sent_bin[s]] for s in by_sent) / n_sent
    K = max(len(rs) for rs in by_sent.values()) if muc_tieu == "max" else len(rows) / n_sent
    out, so_lan = [], Counter()
    for s in sorted(by_sent):
        recs = sorted(by_sent[s], key=lambda r: r["uid"])
        rng.shuffle(recs)
        x = K * g[sent_bin[s]] / mean_g
        c = int(x) + (rng.random() < x - int(x))
        if muc_tieu == "max":
            c = max(c, len(recs))  # không bỏ bản thu nào
        c = max(c, 1)
        for i in range(c):
            r = recs[i % len(recs)]
            out.append(r)
            so_lan[r["uid"]] += 1
    rng.shuffle(out)
    return out, so_lan, sent_bin, {"K": round(K, 3), "he_so_nhom": {b: round(g[b] / mean_g, 3) for b in g}}


def dist_by_nrec(rows, by_sent_n):
    """% mẫu dạy thuộc các câu có 1 / 2 / 3 bản thu gốc."""
    c = Counter(by_sent_n[r["group"]] for r in rows)
    return {str(k): pct(c[k], len(rows)) for k in sorted(c)}


def dist_by_bin(rows, sent_bin, order):
    c = Counter(sent_bin[r["group"]] for r in rows)
    return {b: pct(c.get(b, 0), len(rows)) for b in order}


# ---------------------------------------------------------------- V2: trộn PhoMT

def count_lines(p):
    with open(p, encoding="utf-8") as f:
        return sum(1 for _ in f)


def balance_v2(args, n_fleurs, rng):
    tr = args.data_dir / "clean" / "phomt" / "train.vi"
    if not tr.exists():
        return None
    n_phomt = count_lines(tr)
    want = min(n_phomt, round(args.ti_le_phomt * n_fleurs))
    res = {"phomt_train_sach": n_phomt, "fleurs_train_v1": n_fleurs, "phomt_lay": want,
           "truoc_pct_fleurs": pct(n_fleurs, n_fleurs + n_phomt), "sau_pct_fleurs": pct(n_fleurs, n_fleurs + want)}
    if args.phomt_mien:
        labels = Path(args.phomt_mien).read_text(encoding="utf-8").split("\n")[:n_phomt]
        if len(labels) != n_phomt:
            raise SystemExit(f"--phomt_mien có {len(labels)} dòng, PhoMT train sạch có {n_phomt} dòng.")
        by_dom = defaultdict(list)
        for i, d in enumerate(labels):
            by_dom[d.strip()].append(i)
        # Lấy mẫu theo nhiệt độ: p_d ∝ n_d^(1/T). T = 1 giữ nguyên tỉ lệ, T lớn -> gần đều giữa các miền.
        w = {d: len(ix) ** (1 / args.nhiet_do) for d, ix in by_dom.items()}
        tot = sum(w.values())
        idx = []
        for d, ix in by_dom.items():
            k = min(len(ix), round(want * w[d] / tot))
            idx += rng.sample(ix, k)
        res["mien_truoc_pct"] = {d: pct(len(ix), n_phomt) for d, ix in by_dom.items()}
        res["mien_sau_pct"] = {d: pct(sum(1 for i in idx if labels[i].strip() == d), len(idx)) for d in by_dom}
        res["nhiet_do"] = args.nhiet_do
    else:
        idx = rng.sample(range(n_phomt), want)  # ngẫu nhiên đều: giữ nguyên tỉ lệ miền gốc của PhoMT
        res["mien_ghi_chu"] = ("Không có nhãn miền từng dòng -> lấy ngẫu nhiên đều, tỉ lệ miền giữ như PhoMT gốc "
                               "(OpenSubtitles ~51,4% theo paper). Có nhãn thì thêm --phomt_mien để cân bằng theo miền.")
    res["idx"] = sorted(idx)
    return res


# ---------------------------------------------------------------- vẽ

def plot(out, S, order):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.color": GRID, "axes.axisbelow": True, "axes.titlesize": 13,
                         "axes.titleweight": "bold", "axes.titlecolor": INK})

    def paired(name, title, cats, before, after, xlabel, note, ref=None, ref_label=None):
        fig, ax = plt.subplots(figsize=(10, 4.8))
        x = range(len(cats))
        w = 0.38
        b1 = ax.bar([i - w / 2 for i in x], [before[c] for c in cats], w * 0.94, color=C_BEFORE, label="Trước")
        b2 = ax.bar([i + w / 2 for i in x], [after[c] for c in cats], w * 0.94, color=C_AFTER, label="Sau")
        for bars in (b1, b2):
            for bar in bars:
                h = bar.get_height()
                inside = h > 6  # số nằm trong đầu cột để không đè lên đường tham chiếu
                ax.text(bar.get_x() + bar.get_width() / 2, h - 0.8 if inside else h + 0.8, f"{h:.1f}%", ha="center",
                        va="top" if inside else "bottom", fontsize=8.5, color="white" if inside else INK2,
                        fontweight="bold" if inside else "normal")
        if ref:
            for i, c in enumerate(cats):
                ax.plot([i - w, i + w], [ref[c]] * 2, color=INK, linewidth=1.2, linestyle="--",
                        label=ref_label if i == 0 else None)
        ax.set_xticks(list(x), cats)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("% số mẫu dạy")
        ax.grid(axis="x", visible=False)
        ax.legend(frameon=False, ncols=3, loc="lower center", bbox_to_anchor=(0.5, 1.0))
        ax.set_title(title, pad=30)
        fig.text(0.01, 0.01, note, fontsize=8.5, color=INK2)
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        fig.savefig(out / name, dpi=200, facecolor="white")
        plt.close(fig)

    v = S["v1"]
    cats = sorted(v["theo_cau_truoc"], key=int)
    paired("can_bang_01_theo_cau.png", "V1 – FLEURS train: tỉ lệ mẫu dạy theo số bản thu gốc của câu",
           cats, v["theo_cau_truoc"], {c: v["theo_cau_sau"].get(c, 0) for c in cats},
           "Câu gốc có … bản thu", "Đường đứt = % số câu gốc trong nhóm (mức 'mỗi câu được dạy như nhau'). Sau cân bằng, cột xanh gần đường đứt.",
           ref=v["ti_le_cau_theo_nhom"], ref_label="% số câu gốc")
    paired("can_bang_02_do_dai.png", f"V1 – FLEURS train: tỉ lệ mẫu dạy theo độ dài câu (alpha = {S['tham_so']['alpha']})",
           order, v["do_dai_truoc"], v["do_dai_sau"], "Độ dài câu (số âm tiết tiếng Việt)",
           "Nhóm ít mẫu được lấy lặp thêm; alpha < 1 để không lặp quá nhiều vài câu hiếm. Dev/test không đổi.")
    v2 = S.get("v2")
    if v2:
        cats = ["FLEURS", "PhoMT"]
        before = {"FLEURS": v2["truoc_pct_fleurs"], "PhoMT": round(100 - v2["truoc_pct_fleurs"], 2)}
        after = {"FLEURS": v2["sau_pct_fleurs"], "PhoMT": round(100 - v2["sau_pct_fleurs"], 2)}
        paired("can_bang_03_nguon_v2.png", "V2 – trộn dữ liệu dịch: tỉ lệ FLEURS : PhoMT", cats, before, after, "Nguồn",
               f"Trước = gộp nguyên {v2['phomt_train_sach']:,} cặp PhoMT; sau = lấy {v2['phomt_lay']:,} cặp (ti_le_phomt = {S['tham_so']['ti_le_phomt']}).".replace(",", "."))
        if "mien_truoc_pct" in v2:
            doms = sorted(v2["mien_truoc_pct"], key=lambda d: -v2["mien_truoc_pct"][d])
            paired("can_bang_04_mien_phomt.png", f"V2 – PhoMT theo miền (nhiệt độ T = {v2['nhiet_do']})", doms,
                   v2["mien_truoc_pct"], v2["mien_sau_pct"], "Miền", "p(miền) ∝ n^(1/T).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data_dir", type=Path, default=Path("data"))
    ap.add_argument("--report_dir", type=Path, default=Path("reports/task2/data"))
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--bins", default="15,25,35,45")
    ap.add_argument("--ti_le_phomt", type=float, default=1.0)
    ap.add_argument("--phomt_mien", default=None)
    ap.add_argument("--nhiet_do", type=float, default=5.0)
    ap.add_argument("--muc_tieu", choices=["max", "tb"], default="max",
                    help="max: mỗi câu lấy lên bằng câu nhiều bản thu nhất (không bỏ dữ liệu); tb: giữ nguyên tổng số mẫu")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    edges = [int(x) for x in args.bins.split(",")]
    order = bin_order(edges)
    out = args.report_dir / "can_bang"
    out.mkdir(parents=True, exist_ok=True)
    dout = args.data_dir / "can_bang"
    dout.mkdir(parents=True, exist_ok=True)

    src = args.data_dir / "clean" / "fleurs_train.jsonl"
    if not src.exists():
        raise SystemExit(f"Không thấy {src}. Chạy viec2_lam_sach_du_lieu.py trước.")
    with open(src, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]
    n_rec = Counter(r["group"] for r in rows)
    after, so_lan, sent_bin, info = balance_v1(rows, edges, args.alpha, args.seed, args.muc_tieu)
    nrec_of = {s: n for s, n in n_rec.items()}
    sent_by_n = Counter(nrec_of.values())
    S = {"tham_so": {"alpha": args.alpha, "bins": edges, "ti_le_phomt": args.ti_le_phomt, "seed": args.seed,
                     "phomt_mien": args.phomt_mien, "nhiet_do": args.nhiet_do, "muc_tieu": args.muc_tieu},
         "v1": {"so_mau_truoc": len(rows), "so_mau_sau": len(after), "so_cau": len(n_rec), **info,
                "ti_le_cau_theo_nhom": {str(k): pct(sent_by_n[k], len(n_rec)) for k in sorted(sent_by_n)},
                "theo_cau_truoc": dist_by_nrec(rows, nrec_of), "theo_cau_sau": dist_by_nrec(after, nrec_of),
                "do_dai_truoc": dist_by_bin(rows, sent_bin, order), "do_dai_sau": dist_by_bin(after, sent_bin, order),
                "ti_le_cau_theo_do_dai": {b: pct(c, len(n_rec)) for b, c in Counter(sent_bin.values()).items()},
                "so_ban_thu_khong_dung": sum(1 for r in rows if so_lan[r["uid"]] == 0),
                "so_lan_lap_toi_da_1_ban_thu": max(so_lan.values()) if so_lan else 0}}
    # Số lần mỗi câu được dạy, so trong CÙNG nhóm độ dài (khác nhóm thì cố ý khác nhau do cân bằng độ dài)
    for name, rs in (("truoc", Counter(r["group"] for r in rows)), ("sau", Counter(r["group"] for r in after))):
        per_bin = defaultdict(list)
        for sid, n in rs.items():
            per_bin[sent_bin[sid]].append(n)
        S["v1"][f"lan_day_moi_cau_{name}"] = {b: {"min": min(v), "max": max(v), "tb": round(sum(v) / len(v), 2)}
                                              for b, v in per_bin.items()}
        S["v1"][f"ti_le_max_min_trong_nhom_{name}"] = round(max(max(v) / min(v) for v in per_bin.values()), 2)

    with open(dout / "v1_fleurs_train_can_bang.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in after)
    with open(out / "can_bang_v1_so_lan.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["uid", "sent_id", "nhom_do_dai", "so_ban_thu_cua_cau", "so_lan_trong_du_lieu_day"])
        w.writerows([r["uid"], r["group"], sent_bin[r["group"]], n_rec[r["group"]], so_lan[r["uid"]]] for r in rows)

    v2 = balance_v2(args, len(after), random.Random(args.seed))
    if v2:
        (out / "can_bang_v2_phomt_idx.txt").write_text("".join(f"{i}\n" for i in v2.pop("idx")))
        S["v2"] = v2
    else:
        print("[V2] không thấy data/clean/phomt/train.vi -> bỏ qua phần trộn PhoMT.")

    plot(out, S, order)
    S["meta"] = {"script": "viec4_can_bang_du_lieu.py", "time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                 "versions": lib_versions(), "platform": platform.platform()}
    (out / "can_bang_tom_tat.json").write_text(json.dumps(S, ensure_ascii=False, indent=2), encoding="utf-8")

    v = S["v1"]
    print(f"V1: {v['so_mau_truoc']} mẫu -> {v['so_mau_sau']} mẫu, {v['so_cau']} câu gốc, K = {v['K']}")
    print(f"  % mẫu theo số bản thu của câu: trước {v['theo_cau_truoc']} -> sau {v['theo_cau_sau']} (mức đều: {v['ti_le_cau_theo_nhom']})")
    print(f"  chênh lệch số lần dạy giữa các câu cùng nhóm độ dài (max/min): trước {v['ti_le_max_min_trong_nhom_truoc']}× "
          f"-> sau {v['ti_le_max_min_trong_nhom_sau']}×")
    print(f"  % mẫu theo độ dài: trước {v['do_dai_truoc']} -> sau {v['do_dai_sau']}")
    print(f"  bản thu không được dùng: {v['so_ban_thu_khong_dung']}; một bản thu lặp tối đa {v['so_lan_lap_toi_da_1_ban_thu']} lần")
    if v2:
        print(f"V2: FLEURS chiếm {v2['truoc_pct_fleurs']}% nếu gộp nguyên PhoMT -> {v2['sau_pct_fleurs']}% sau khi lấy {v2['phomt_lay']} cặp PhoMT")
    print(f"\nBiểu đồ + bảng (commit được): {out}/  |  Dữ liệu dạy V1 (không commit): {dout}/")


if __name__ == "__main__":
    main()
