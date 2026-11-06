#!/usr/bin/env python3
"""Ma trận nhầm lẫn dấu thanh (6 thanh tiếng Việt) từ các cặp substitution chỉ khác dấu thanh trong alignments.jsonl.

Dùng cho mục "Confusion Matrix" (bài toán ASR/MT không có lớp; ma trận thanh điệu là dạng confusion hợp lý nhất).
Đầu ra: reports/asr/tone_confusion_<run_id>.csv + .png. Hàng = thanh trong tham chiếu, cột = thanh trong giả thuyết.
"""
import argparse
import csv
import json
import unicodedata
from pathlib import Path

TONES = {"̀": "huyền", "́": "sắc", "̃": "ngã", "̉": "hỏi", "̣": "nặng"}
ORDER = ["ngang", "huyền", "sắc", "hỏi", "ngã", "nặng"]


def tone(w):
    d = unicodedata.normalize("NFD", w)
    t = [TONES[c] for c in d if c in TONES]
    return t[0] if t else "ngang"


def strip_tone(w):
    d = unicodedata.normalize("NFD", w)
    return unicodedata.normalize("NFC", "".join(c for c in d if c not in TONES))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--out_dir", type=Path, default=Path("reports/asr"))
    a = ap.parse_args()
    M = {r: {c: 0 for c in ORDER} for r in ORDER}
    n = 0
    for l in open(a.run / "score" / "alignments.jsonl", encoding="utf-8"):
        for o in json.loads(l)["word_alignment"]:
            if o["op"] == "S" and o["ref"] != o["hyp"] and strip_tone(o["ref"]) == strip_tone(o["hyp"]):
                M[tone(o["ref"])][tone(o["hyp"])] += 1; n += 1
    a.out_dir.mkdir(parents=True, exist_ok=True)
    name = a.run.name
    with open(a.out_dir / f"tone_confusion_{name}.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(["ref\\hyp"] + ORDER)
        for r in ORDER:
            w.writerow([r] + [M[r][c] for c in ORDER])
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    X = np.array([[M[r][c] for c in ORDER] for r in ORDER])
    fig, ax = plt.subplots(figsize=(5.5, 4.6))
    im = ax.imshow(X, cmap="Blues")
    ax.set_xticks(range(6), ORDER); ax.set_yticks(range(6), ORDER)
    ax.set_xlabel("thanh trong giả thuyết ASR"); ax.set_ylabel("thanh trong tham chiếu")
    for i in range(6):
        for j in range(6):
            ax.text(j, i, X[i, j], ha="center", va="center", color="white" if X[i, j] > X.max() / 2 else "black", fontsize=9)
    ax.set_title(f"Nhầm dấu thanh ({n} cặp)\n{name}", fontsize=9)
    fig.colorbar(im); fig.tight_layout(); fig.savefig(a.out_dir / f"tone_confusion_{name}.png", dpi=150)
    print(name, "tone-only substitutions:", n)


if __name__ == "__main__":
    main()
