"""Task 2 · phân tích lỗi dịch (failure cases) của Vn so với B0 trên cascade FLEURS test.

Chia câu theo nhóm và so BLEU/chrF++ của B0 và Vn trong từng nhóm:
  - mức lỗi nghe của câu đầu vào (WER của PhoWhisper trên câu đó)
  - câu có số viết bằng chữ số trong câu đúng (ASR thường đọc ra thành chữ: "802" → "tám trăm linh hai")
Trích ví dụ: câu Vn tốt lên nhiều nhất, kém đi nhiều nhất, và câu cả hai đều sai nặng.
"""
import argparse, json, re, unicodedata
import sacrebleu
from jiwer import process_words

ap = argparse.ArgumentParser()
ap.add_argument("--base", default="B0")
ap.add_argument("--new", required=True)
ap.add_argument("--dir", default="reports/task2/mt")
ap.add_argument("--k", type=int, default=8)
args = ap.parse_args()


def norm(t):
    t = unicodedata.normalize("NFC", t).lower()
    t = "".join(" " if unicodedata.category(c)[0] in "PS" else c for c in t)
    return " ".join(t.split())


A = json.load(open(f"{args.dir}/predictions_{args.base}.json", encoding="utf-8"))
B = json.load(open(f"{args.dir}/predictions_{args.new}.json", encoding="utf-8"))
src = json.load(open("reports/task1/mt/predictions_fleurs_test.json", encoding="utf-8"))
assert len(A) == len(B) == len(src)

rows = []
for a, b, s in zip(A, B, src):
    w = process_words(norm(s["vi_raw"]), norm(s["asr"])).wer
    rows.append({"id": s["id"], "vi_ref": s["vi_raw"], "asr": s["asr"], "en_ref": s["en_ref"], "base": a["cascade"], "new": b["cascade"],
                 "asr_wer": round(100 * w, 1), "has_digits": bool(re.search(r"\d", s["vi_raw"])),
                 "chrf_base": sacrebleu.sentence_chrf(a["cascade"], [s["en_ref"]], word_order=2).score,
                 "chrf_new": sacrebleu.sentence_chrf(b["cascade"], [s["en_ref"]], word_order=2).score})


def grp(rs):
    if not rs:
        return None
    refs = [r["en_ref"] for r in rs]
    return {"n": len(rs),
            f"BLEU_{args.base}": round(sacrebleu.corpus_bleu([r["base"] for r in rs], [refs]).score, 2),
            f"BLEU_{args.new}": round(sacrebleu.corpus_bleu([r["new"] for r in rs], [refs]).score, 2),
            f"chrF++_{args.base}": round(sacrebleu.corpus_chrf([r["base"] for r in rs], [refs], word_order=2).score, 2),
            f"chrF++_{args.new}": round(sacrebleu.corpus_chrf([r["new"] for r in rs], [refs], word_order=2).score, 2)}


bucket = lambda w: "WER 0" if w == 0 else "WER 0–10" if w <= 10 else "WER 10–30" if w <= 30 else "WER >30"
report = {"by_asr_wer": {k: grp([r for r in rows if bucket(r["asr_wer"]) == k]) for k in ["WER 0", "WER 0–10", "WER 10–30", "WER >30"]},
          "by_digits": {"có số": grp([r for r in rows if r["has_digits"]]), "không có số": grp([r for r in rows if not r["has_digits"]])},
          "sentences_better": sum(r["chrf_new"] > r["chrf_base"] + 1 for r in rows),
          "sentences_worse": sum(r["chrf_new"] < r["chrf_base"] - 1 for r in rows),
          "sentences_same": sum(abs(r["chrf_new"] - r["chrf_base"]) <= 1 for r in rows)}
d = sorted(rows, key=lambda r: r["chrf_new"] - r["chrf_base"])
keep = ("id", "vi_ref", "asr", "en_ref", "base", "new", "asr_wer", "chrf_base", "chrf_new")
report["examples_most_improved"] = [{k: r[k] for k in keep} for r in d[::-1][: args.k]]
report["examples_most_worse"] = [{k: r[k] for k in keep} for r in d[: args.k]]
report["examples_both_bad"] = [{k: r[k] for k in keep} for r in sorted(rows, key=lambda r: r["chrf_new"])[: args.k]]
json.dump(report, open(f"{args.dir}/mt_errors_{args.new}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps({k: report[k] for k in ("by_asr_wer", "by_digits", "sentences_better", "sentences_worse", "sentences_same")},
                 ensure_ascii=False, indent=1))
