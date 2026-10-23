"""Task 2 · mục 1.2: bộ gán nhãn loại lỗi cho 100 câu FLEURS dev (phần Đăng, Uyên gán độc lập để tính Cohen's Kappa).

Chọn câu: mỗi câu gốc lấy một bản thu (bản có bản dịch B0 kém nhất theo chrF++); chỉ lấy câu mà B0 nghe sai (WER > 0)
hoặc dịch kém (chrF++ < 50); lấy ngẫu nhiên 100 câu với seed 42. Không dùng tập test.
Ghi vào reports/task2/labeling/: items.csv, annotator_Dang.csv, annotator_Uyen.csv, label_studio_tasks.json,
label_studio_config.xml. Tiêu chí gán nhãn: reports/task2/labeling/TIEU_CHI_GAN_NHAN.md.
"""
import csv, json, os, random, unicodedata
import sacrebleu
from jiwer import process_words

OUT = "reports/task2/labeling"
CATS = [("sai_dau_thanh", "Sai dấu thanh"), ("ten_rieng", "Tên riêng sai"), ("so", "Số sai / đọc thành chữ"),
        ("thieu_thua_tu", "Thiếu hoặc thừa từ"), ("sai_nghia_dich", "Bản dịch sai nghĩa")]


def norm(t):
    t = unicodedata.normalize("NFC", t).lower()
    t = "".join(" " if unicodedata.category(c)[0] in "PS" else c for c in t)
    return " ".join(t.split())


rows = json.load(open("reports/task2/mt/dev_predictions_B0.json", encoding="utf-8"))
best = {}
for r in rows:
    r["asr_wer"] = round(100 * process_words(norm(r["vi_raw"]), norm(r["asr"])).wer, 1)
    r["chrf"] = round(sacrebleu.sentence_chrf(r["hyp"], [r["en_ref"]], word_order=2).score, 1)
    if r["asr_wer"] > 0 or r["chrf"] < 50:
        if r["id"] not in best or r["chrf"] < best[r["id"]]["chrf"]:
            best[r["id"]] = r
cands = sorted(best.values(), key=lambda r: r["audio"])
random.Random(42).shuffle(cands)
sel = cands[:100]
os.makedirs(OUT, exist_ok=True)
head = ["stt", "audio", "id_cau", "cau_dung_vi", "may_nghe_vi", "tham_chieu_en", "ban_dich_B0"] + [k for k, _ in CATS] + ["ghi_chu"]
items = [[i + 1, r["audio"], r["id"], r["vi_raw"], r["asr"], r["en_ref"], r["hyp"]] for i, r in enumerate(sel)]
for name in ("items", "annotator_Dang", "annotator_Uyen"):
    with open(f"{OUT}/{name}.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(head)
        for it in items:
            w.writerow(it + [""] * (len(CATS) + 1))
json.dump([{"data": {"stt": it[0], "audio": it[1], "cau_dung_vi": it[3], "may_nghe_vi": it[4], "tham_chieu_en": it[5], "ban_dich_B0": it[6]}}
           for it in items], open(f"{OUT}/label_studio_tasks.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
choices = "\n".join(f'    <Choice value="{k}" alias="{k}" hint="{v}"/>' for k, v in CATS)
open(f"{OUT}/label_studio_config.xml", "w", encoding="utf-8").write(f"""<View>
  <Header value="Câu số $stt"/>
  <Text name="ref" value="Câu đúng (vi): $cau_dung_vi"/>
  <Text name="asr" value="Máy nghe (vi): $may_nghe_vi"/>
  <Text name="enref" value="Tham chiếu (en): $tham_chieu_en"/>
  <Text name="mt" value="Bản dịch B0 (en): $ban_dich_B0"/>
  <Choices name="loai_loi" toName="asr" choice="multiple" showInLine="false">
{choices}
  </Choices>
</View>
""")
stats = {"n": len(sel), "pool": len(cands), "dev_recordings": len(rows), "seed": 42,
         "mean_asr_wer": round(sum(r["asr_wer"] for r in sel) / len(sel), 2), "mean_chrf_B0": round(sum(r["chrf"] for r in sel) / len(sel), 2)}
json.dump(stats, open(f"{OUT}/selection.json", "w"), indent=2)
print(stats)
