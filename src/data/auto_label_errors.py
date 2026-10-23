"""Task 2 · mục 1.2: gán nhãn loại lỗi TỰ ĐỘNG theo quy tắc cho 100 câu FLEURS dev (reports/task2/labeling/items.csv).

Không phải nhãn của người: mỗi nhãn do một quy tắc xác định, chạy lại cho đúng kết quả. Vì chỉ có một "người gán" (quy tắc),
không tính Cohen's Kappa (đề Task 2: Kappa chỉ cần nếu có quy trình nhiều người gán).
  sai_dau_thanh  : có ít nhất một cặp âm tiết thay thế mà bỏ dấu thanh thì giống nhau
  ten_rieng      : có tên riêng (từ viết hoa không đầu câu trong câu đúng) mà máy nghe không có
  so             : câu đúng có chữ số và (máy nghe đọc thành chữ, hoặc bản dịch thiếu chữ số có trong tham chiếu)
  thieu_thua_tu  : máy nghe có từ 2 lỗi xóa + chèn trở lên
  sai_nghia_dich : chrF++ câu của bản dịch B0 dưới 40 (chỉ là ngưỡng xấp xỉ "sai nghĩa")
Ghi auto_labels.csv và auto_labels_summary.json trong reports/task2/labeling/.
"""
import csv, json, re, unicodedata
import sacrebleu
from jiwer import process_words

D = "reports/task2/labeling"
MARK = set("̣̀́̉̃")
NUMW = {"không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín", "mười", "mươi", "trăm", "nghìn", "ngàn", "triệu", "linh", "lẻ", "chấm"}


def norm(t):
    t = unicodedata.normalize("NFC", t).lower()
    t = "".join(" " if unicodedata.category(c)[0] in "PS" else c for c in t)
    return " ".join(t.split())


def strip_tone(s):
    return unicodedata.normalize("NFC", "".join(c for c in unicodedata.normalize("NFD", s) if c not in MARK))


rows = list(csv.DictReader(open(f"{D}/items.csv", encoding="utf-8-sig")))
out, counts = [], {k: 0 for k in ("sai_dau_thanh", "ten_rieng", "so", "thieu_thua_tu", "sai_nghia_dich")}
for r in rows:
    ref, hyp = norm(r["cau_dung_vi"]), norm(r["may_nghe_vi"])
    o = process_words(ref, hyp)
    rw, hw = o.references[0], o.hypotheses[0]
    tone = any(c.type == "substitute" and any(strip_tone(rw[c.ref_start_idx + k]) == strip_tone(hw[c.hyp_start_idx + k])
                                              for k in range(c.ref_end_idx - c.ref_start_idx)) for c in o.alignments[0])
    toks = r["cau_dung_vi"].split(); hs = set(hyp.split())
    ents = [norm(t) for i, t in enumerate(toks) if t[:1].isupper() and i > 0 and toks[i - 1][-1:] not in ".?!:" and not any(ch.isdigit() for ch in t)]
    name = any(p not in hs for e in ents for p in e.split())
    digits_ref = re.findall(r"\d+", r["tham_chieu_en"])
    num = bool(re.search(r"\d", r["cau_dung_vi"])) and (any(w in NUMW for w in hyp.split()) or any(d not in r["ban_dich_B0"] for d in digits_ref))
    gap = (o.deletions + o.insertions) >= 2
    chrf = sacrebleu.sentence_chrf(r["ban_dich_B0"], [r["tham_chieu_en"]], word_order=2).score
    lab = {"sai_dau_thanh": int(tone), "ten_rieng": int(name), "so": int(num), "thieu_thua_tu": int(gap), "sai_nghia_dich": int(chrf < 40)}
    for k, v in lab.items():
        counts[k] += v
    out.append({**r, **lab, "ghi_chu": f"auto: WER {100 * o.wer:.1f}, S/D/I {o.substitutions}/{o.deletions}/{o.insertions}, chrF++ B0 {chrf:.1f}"})
with open(f"{D}/auto_labels.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
summ = {"n": len(out), "method": "gán tự động theo quy tắc (src/data/auto_label_errors.py), không phải nhãn của người",
        "counts": counts, "percent": {k: round(100 * v / len(out), 1) for k, v in counts.items()},
        "sentences_with_any_error": sum(any(x[k] for k in counts) for x in out), "kappa": "không áp dụng (một quy trình gán duy nhất)"}
json.dump(summ, open(f"{D}/auto_labels_summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(summ, ensure_ascii=False, indent=1))
