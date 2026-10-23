"""Task 2 · gom kết quả: bảng ablation B0 → Vn, đường loss/BLEU theo epoch, biểu đồ tiến trình.

Đọc reports/task2/mt/eval_*.json (cùng script chấm, cùng tập test) và checkpoints/<v>/log.jsonl (log train).
Ghi reports/task2/ablation.json, reports/task2/ablation.md và hình trong reports/task2/figures/.
"""
import argparse, glob, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("--versions", default="B0,V1,V2,V3")
ap.add_argument("--ckpt", default="checkpoints")
ap.add_argument("--out", default="reports/task2")
args = ap.parse_args()
os.makedirs(f"{args.out}/figures", exist_ok=True)

rows = []
for v in args.versions.split(","):
    p = f"{args.out}/mt/eval_{v}.json"
    if not os.path.exists(p):
        continue
    e = json.load(open(p, encoding="utf-8"))
    phomt_note = None
    if v == "B0" and "phomt_test" not in e:  # B0 PhoMT: same-config rescore if it exists, else the earlier batch-32 run
        for alt, note in ((f"{args.out}/mt/eval_B0_full.json", "B0 PhoMT rescored with the same decoding config"),
                          (f"{args.out}/mt/eval_B0_batch32.json", "B0 PhoMT from the run with batch 32 / max_length 512")):
            if os.path.exists(alt):
                e["phomt_test"] = json.load(open(alt, encoding="utf-8"))["phomt_test"]; phomt_note = note
                break
    # V3 = (bản LoRA cuối) + chuẩn hóa số ở đầu vào cascade: chữ chuẩn và PhoMT không đi qua bước này,
    # nên hai cột đó lấy từ phiên bản gốc ghi trong eval_V3.json ("base_version").
    if "fleurs_clean" not in e and e.get("base_version"):
        src_e = json.load(open(f"{args.out}/mt/eval_{e['base_version']}.json", encoding="utf-8"))
        e["fleurs_clean"] = src_e["fleurs_clean"]; e.setdefault("phomt_test", src_e.get("phomt_test", {}))
        phomt_note = f"chữ chuẩn và PhoMT giống {e['base_version']} (chuẩn hóa số chỉ áp dụng cho chữ máy nghe)"
    cfg = f"{args.ckpt}/{v.lower()}/config.json"
    rows.append({"version": v,
                 "fleurs_cascade_BLEU": e["fleurs_cascade"]["BLEU"], "fleurs_cascade_chrF++": e["fleurs_cascade"]["chrF++"],
                 "fleurs_clean_BLEU": e["fleurs_clean"]["BLEU"],
                 "phomt_BLEU": e.get("phomt_test", {}).get("BLEU"), "phomt_note": phomt_note,
                 "train_pairs": json.load(open(cfg))["train_pairs"] if os.path.exists(cfg) else None})
b0 = rows[0]["fleurs_cascade_BLEU"] if rows and rows[0]["version"] == "B0" else None
for r in rows:
    r["delta_vs_B0"] = round(r["fleurs_cascade_BLEU"] - b0, 2) if b0 is not None else None
json.dump(rows, open(f"{args.out}/ablation.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

md = ["| Phiên bản | BLEU cascade | chrF++ cascade | Δ so với B0 | BLEU chữ chuẩn | BLEU PhoMT |", "|---|---|---|---|---|---|"]
for r in rows:
    md.append(f"| {r['version']} | {r['fleurs_cascade_BLEU']} | {r['fleurs_cascade_chrF++']} | {r['delta_vs_B0']:+} | {r['fleurs_clean_BLEU']} | {r['phomt_BLEU']} |")
open(f"{args.out}/ablation.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))

if rows:
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    xs = [r["version"] for r in rows]
    ax.plot(xs, [r["fleurs_cascade_BLEU"] for r in rows], "o-", label="Cascade FLEURS test (chính)", color="#2a5caa")
    ax.plot(xs, [r["fleurs_clean_BLEU"] for r in rows], "s--", label="Chữ chuẩn FLEURS test", color="#5aa469")
    if all(r["phomt_BLEU"] is not None for r in rows):
        ax.plot(xs, [r["phomt_BLEU"] for r in rows], "^:", label="PhoMT test", color="#e07b39")
    for x, r in zip(xs, rows):
        ax.annotate(f"{r['fleurs_cascade_BLEU']:.2f}", (x, r["fleurs_cascade_BLEU"]), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)
    ax.set_ylabel("BLEU"); ax.set_title("Ablation: BLEU qua từng phiên bản"); ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(f"{args.out}/figures/ablation_bleu.png", dpi=160); plt.close(fig)

for v in args.versions.split(","):
    lp = f"{args.ckpt}/{v.lower()}/log.jsonl"
    if not os.path.exists(lp):
        continue
    log = [json.loads(l) for l in open(lp, encoding="utf-8")]
    ep = [r["epoch"] for r in log]
    fig, ax1 = plt.subplots(figsize=(6.5, 3.6))
    ax1.plot([r["epoch"] for r in log if r["train_loss"] is not None], [r["train_loss"] for r in log if r["train_loss"] is not None], "o-", label="train loss", color="#2a5caa")
    ax1.plot(ep, [r["dev_loss"] for r in log], "s--", label="dev loss", color="#5aa469")
    ax1.set_xlabel("Epoch (0 = trước khi train, tức Baseline B)"); ax1.set_ylabel("Loss")
    ax2 = ax1.twinx()
    ax2.plot(ep, [r["dev_bleu"] for r in log], "^-", label="dev BLEU", color="#e07b39"); ax2.set_ylabel("dev BLEU")
    h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, fontsize=8, loc="center right"); ax1.set_title(f"{v}: loss và BLEU trên dev theo epoch")
    fig.tight_layout(); fig.savefig(f"{args.out}/figures/curves_{v}.png", dpi=160); plt.close(fig)
