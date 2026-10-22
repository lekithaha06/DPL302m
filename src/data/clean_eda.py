"""Task 2 · Giai đoạn 1 (phần dữ liệu): làm sạch, thống kê mô tả, mất cân bằng, chia tập, biểu đồ.

Mọi số in ra và ghi vào reports/task2/data/data_stats.json đều tính trực tiếp từ file đã tải:
  FLEURS vi_vn + en_us (train/dev/test .tsv và .wav), VIVOS test (manifest + dự đoán TV1 cho độ dài),
  PhoMT (đếm dòng các file detokenization nếu có --phomt).
Không sửa dữ liệu gốc; bước làm sạch tạo danh sách mẫu giữ lại và đếm số mẫu bị loại ở từng bước.
"""
import argparse, csv, hashlib, json, os, re, unicodedata
from collections import Counter
import soundfile as sf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("--fleurs", default="data/fleurs/data")
ap.add_argument("--audio", default="data/fleurs_audio")
ap.add_argument("--vivos-pred", default="reports/task1/asr/predictions_PhoWhisper-small.jsonl")
ap.add_argument("--phomt", default="")
ap.add_argument("--out", default="reports/task2/data")
args = ap.parse_args()
os.makedirs(f"{args.out}/figures", exist_ok=True)


def norm(t):  # cùng chính sách với WER/CER: NFC, viết thường, ký hiệu → khoảng trắng, giữ dấu
    t = unicodedata.normalize("NFC", t).lower()
    t = "".join(" " if unicodedata.category(c)[0] in "PS" else c for c in t)
    return " ".join(t.split())


def read_tsv(p):
    with open(p, encoding="utf-8") as f:
        return [r for r in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)]


stats, kept = {}, {}
for split in ("train", "dev", "test"):
    vi = read_tsv(f"{args.fleurs}/vi_vn/{split}.tsv")
    en_ids = {r[0] for r in read_tsv(f"{args.fleurs}/en_us/{split}.tsv")}
    steps = [("raw", len(vi))]
    rows = [r for r in vi if r[0] in en_ids];                        steps.append(("có câu tiếng Anh tham chiếu", len(rows)))
    rows = [r for r in rows if r[2].strip()];                       steps.append(("transcript không rỗng", len(rows)))
    good, srs, hashes, dup = [], Counter(), set(), 0
    for r in rows:
        p = f"{args.audio}/{split}/{r[1]}"
        try:
            info = sf.info(p)
        except Exception:
            continue
        if info.frames == 0:
            continue
        h = hashlib.sha1(open(p, "rb").read()).hexdigest()
        if h in hashes:
            dup += 1
            continue
        hashes.add(h); srs[info.samplerate] += 1
        good.append({"id": r[0], "file": r[1], "vi": r[2], "vi_norm": norm(r[2]), "sec": info.frames / info.samplerate,
                     "gender": r[6], "sr": info.samplerate})
    steps.append(("âm thanh đọc được, không rỗng", len(good) + dup))
    steps.append(("không trùng file âm thanh (hash)", len(good)))
    kept[split] = good
    secs = sorted(x["sec"] for x in good)
    per_sent = Counter(Counter(x["id"] for x in good).values())
    len_buckets = Counter(("<5 s" if s < 5 else "5–10 s" if s < 10 else "10–20 s" if s < 20 else "20–30 s" if s < 30 else ">30 s") for s in secs)
    stats[split] = {
        "cleaning_steps": steps, "removed_total": steps[0][1] - len(good),
        "utterances": len(good), "unique_sentences": len({x["id"] for x in good}),
        "hours": round(sum(secs) / 3600, 3), "mean_sec": round(sum(secs) / len(secs), 2),
        "median_sec": round(secs[len(secs) // 2], 2), "min_sec": round(secs[0], 2), "max_sec": round(secs[-1], 2),
        "over_30s": sum(s > 30 for s in secs), "sample_rates": dict(srs),
        "gender": dict(Counter(x["gender"] for x in good)),
        "recordings_per_sentence": {str(k): v for k, v in sorted(per_sent.items())},
        "length_buckets": {k: len_buckets.get(k, 0) for k in ["<5 s", "5–10 s", "10–20 s", "20–30 s", ">30 s"]},
        "words_mean": round(sum(len(x["vi_norm"].split()) for x in good) / len(good), 2),
    }

# leakage giữa các tập: theo ID câu và theo nội dung chuẩn hóa
leak = {}
for a, b in (("train", "dev"), ("train", "test"), ("dev", "test")):
    leak[f"{a}-{b}"] = {"id_overlap": len({x["id"] for x in kept[a]} & {x["id"] for x in kept[b]}),
                        "text_overlap": len({x["vi_norm"] for x in kept[a]} & {x["vi_norm"] for x in kept[b]})}
tot = sum(stats[s]["utterances"] for s in stats)
split_ratio = {s: round(100 * stats[s]["utterances"] / tot, 1) for s in stats}

# VIVOS test: người nói và độ dài (từ dự đoán TV1, cùng 760 câu)
viv = [json.loads(l) for l in open(args.vivos_pred, encoding="utf-8")]
viv_spk = Counter(r["speaker_id"] for r in viv)
vivos = {"utterances": len(viv), "speakers": len(viv_spk), "mean_sec": round(sum(r["duration_seconds"] for r in viv) / len(viv), 2),
         "utt_per_speaker_min": min(viv_spk.values()), "utt_per_speaker_max": max(viv_spk.values())}

phomt = {}
if args.phomt:
    for s in ("train", "dev", "test"):
        phomt[s] = sum(1 for _ in open(f"{args.phomt}/detokenization/{s}/{s}.vi", encoding="utf-8"))

# cân bằng theo câu (xử lý mất cân bằng): mỗi câu gốc có cùng trọng số = 1/số bản thu của câu đó
tr = kept["train"]
cnt = Counter(x["id"] for x in tr)
before = Counter(cnt[x["id"]] for x in tr)                   # số bản thu thuộc câu có k bản thu
after = {k: round(sum(1 / k for x in tr if cnt[x["id"]] == k), 1) for k in sorted(before)}  # tổng trọng số sau cân bằng
gender_tr = stats["train"]["gender"]

out = {"fleurs": stats, "leakage": leak, "split_ratio_percent": split_ratio, "vivos_test": vivos, "phomt_lines": phomt,
       "phomt_opensubtitles_train_share_percent": {"value": 51.4, "source": "PhoMT paper (EMNLP 2021), Table 1"},
       "sentence_balancing": {"before_utterances_by_recordings_per_sentence": {str(k): v for k, v in sorted(before.items())},
                              "after_weight_by_recordings_per_sentence": {str(k): v for k, v in after.items()}}}
json.dump(out, open(f"{args.out}/data_stats.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump({s: [x | {"sec": round(x["sec"], 3)} for x in kept[s]] for s in kept},
          open("data/processed/fleurs_clean_kept.json", "w", encoding="utf-8"), ensure_ascii=False)

# ---------------- biểu đồ
C = ["#2a5caa", "#e07b39", "#5aa469"]
fig, ax = plt.subplots(figsize=(7, 3.6))
for i, s in enumerate(("train", "dev", "test")):
    ax.hist([x["sec"] for x in kept[s]], bins=40, alpha=.55, label=f"{s} (n={len(kept[s])})", color=C[i], density=True)
ax.set_xlabel("Độ dài âm thanh (giây)"); ax.set_ylabel("Mật độ"); ax.set_title("FLEURS vi_vn: phân bố độ dài theo tập"); ax.legend()
fig.tight_layout(); fig.savefig(f"{args.out}/figures/fleurs_duration.png", dpi=160); plt.close(fig)

fig, axs = plt.subplots(1, 3, figsize=(10, 3.2))
for ax, s in zip(axs, ("train", "dev", "test")):
    g = stats[s]["gender"]; ax.bar(list(g), list(g.values()), color=C[:len(g)])
    tot_s = sum(g.values())
    for j, (k, v) in enumerate(g.items()):
        ax.text(j, v, f"{100 * v / tot_s:.1f}%", ha="center", va="bottom")
    ax.set_title(f"{s}")
fig.suptitle("FLEURS vi_vn: nhãn giới tính theo tập"); fig.tight_layout(); fig.savefig(f"{args.out}/figures/fleurs_gender.png", dpi=160); plt.close(fig)

fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
ks = [str(k) for k in sorted(before)]
ax[0].bar(ks, [before[int(k)] for k in ks], color=C[0]); ax[0].set_title("Trước: số bản thu theo nhóm câu")
ax[0].set_xlabel("Số bản thu của một câu"); ax[0].set_ylabel("Bản thu")
ax[1].bar(ks, [after[int(k)] for k in ks], color=C[2]); ax[1].set_title("Sau cân bằng theo câu: tổng trọng số")
ax[1].set_xlabel("Số bản thu của một câu")
fig.tight_layout(); fig.savefig(f"{args.out}/figures/fleurs_sentence_balance.png", dpi=160); plt.close(fig)

fig, ax = plt.subplots(figsize=(6, 3.2))
ax.bar(list(split_ratio), list(split_ratio.values()), color=C)
for i, v in enumerate(split_ratio.values()):
    ax.text(i, v, f"{v}%", ha="center", va="bottom")
ax.set_title("FLEURS vi_vn: tỉ lệ train / dev / test (bản thu)"); fig.tight_layout()
fig.savefig(f"{args.out}/figures/fleurs_split.png", dpi=160); plt.close(fig)

print(json.dumps(out, ensure_ascii=False, indent=1))
