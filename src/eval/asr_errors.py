"""Task 2 · phân tích lỗi ASR (thiết kế phần Bảo, chạy phần Kiệt).

Từ file dự đoán (ref, hyp đã chuẩn hóa) tính:
  - WER tách thay thế / xóa / chèn (S/D/I)
  - ma trận nhầm dấu thanh 6x6 trên các cặp âm tiết được căn chỉnh (thay cho Confusion Matrix của bài phân loại)
  - tỉ lệ lỗi thay thế chỉ sai dấu thanh (cùng âm tiết khi bỏ dấu thanh)
  - WER theo nhóm độ dài câu và theo người nói (nếu có speaker_id)
"""
import argparse, json, unicodedata
from collections import Counter, defaultdict
import numpy as np
from jiwer import process_words
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TONES = ["ngang", "huyền", "sắc", "hỏi", "ngã", "nặng"]
MARK = {"̀": "huyền", "́": "sắc", "̉": "hỏi", "̃": "ngã", "̣": "nặng"}


def tone(syl):
    for ch in unicodedata.normalize("NFD", syl):
        if ch in MARK:
            return MARK[ch]
    return "ngang"


def strip_tone(syl):
    return unicodedata.normalize("NFC", "".join(c for c in unicodedata.normalize("NFD", syl) if c not in MARK))


def norm(t):  # same policy as src/asr/evaluate_asr.py
    t = unicodedata.normalize("NFC", t).lower()
    t = "".join(" " if unicodedata.category(c)[0] in "PS" else c for c in t)
    return " ".join(t.split())


ap = argparse.ArgumentParser()
ap.add_argument("--vivos", default="reports/task2/asr/predictions_PhoWhisper-small.jsonl")
ap.add_argument("--fleurs", default="reports/task1/mt/predictions_fleurs_test.json")
ap.add_argument("--out", default="reports/task2/asr")
args = ap.parse_args()

sets = {}
viv = [json.loads(l) for l in open(args.vivos, encoding="utf-8")]
sets["VIVOS"] = [{"ref": r["reference_normalized"], "hyp": r["prediction_normalized"], "spk": r["speaker_id"], "sec": r["duration_seconds"]} for r in viv]
fl = json.load(open(args.fleurs, encoding="utf-8"))
sets["FLEURS"] = [{"ref": norm(r["vi_raw"]), "hyp": norm(r["asr"]), "spk": None, "sec": None} for r in fl]

report = {}
for name, rows in sets.items():
    refs, hyps = [r["ref"] for r in rows], [r["hyp"] for r in rows]
    out = process_words(refs, hyps)
    cm = np.zeros((6, 6), dtype=int)
    tone_only = other_sub = 0
    examples = []
    for i, al in enumerate(out.alignments):
        rw, hw = out.references[i], out.hypotheses[i]
        for ch in al:
            if ch.type in ("equal", "substitute"):
                for k in range(ch.ref_end_idx - ch.ref_start_idx):
                    r, h = rw[ch.ref_start_idx + k], hw[ch.hyp_start_idx + k]
                    cm[TONES.index(tone(r)), TONES.index(tone(h))] += 1
                    if ch.type == "substitute":
                        if strip_tone(r) == strip_tone(h):
                            tone_only += 1
                            if len(examples) < 15:
                                examples.append({"ref": r, "hyp": h, "sentence_ref": refs[i]})
                        else:
                            other_sub += 1
    rep = {"n": len(rows), "WER": round(100 * out.wer, 2), "substitutions": out.substitutions, "deletions": out.deletions,
           "insertions": out.insertions, "ref_words": out.hits + out.substitutions + out.deletions,
           "tone_only_substitutions": tone_only, "other_substitutions": other_sub,
           "tone_only_share_of_substitutions_percent": round(100 * tone_only / max(1, tone_only + other_sub), 1),
           "tone_confusion": {"labels": TONES, "matrix_ref_rows_hyp_cols": cm.tolist()}, "tone_only_examples": examples}
    if rows[0]["sec"] is not None:
        buckets = defaultdict(list)
        for r in rows:
            buckets["<3 s" if r["sec"] < 3 else "3–5 s" if r["sec"] < 5 else "≥5 s"].append(r)
        rep["wer_by_length"] = {k: {"n": len(v), "WER": round(100 * process_words([x["ref"] for x in v], [x["hyp"] for x in v]).wer, 2)}
                                for k, v in sorted(buckets.items())}
    report[name] = rep

    off = cm.copy(); np.fill_diagonal(off, 0)
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    im = ax.imshow(off, cmap="Oranges")
    ax.set_xticks(range(6), TONES); ax.set_yticks(range(6), TONES)
    ax.set_xlabel("Máy nghe ra (hyp)"); ax.set_ylabel("Đúng (ref)")
    for a in range(6):
        for b in range(6):
            ax.text(b, a, cm[a, b] if a != b else "", ha="center", va="center", fontsize=8)
    ax.set_title(f"{name}: nhầm dấu thanh (bỏ đường chéo)")
    fig.colorbar(im, fraction=.046); fig.tight_layout()
    fig.savefig(f"{args.out}/tone_confusion_{name}.png", dpi=160); plt.close(fig)

json.dump(report, open(f"{args.out}/asr_errors.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
for k, v in report.items():
    print(k, {x: v[x] for x in ("WER", "substitutions", "deletions", "insertions", "tone_only_substitutions", "tone_only_share_of_substitutions_percent")})
