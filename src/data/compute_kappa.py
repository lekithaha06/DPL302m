"""Task 2 · mục 1.2: Cohen's Kappa giữa hai người gán nhãn loại lỗi (Đăng, Uyên) trên cùng 100 câu FLEURS dev.

Đọc hai file CSV đã gán (cột nhãn ghi 1 nếu có lỗi loại đó, để trống hoặc 0 nếu không), hoặc file export JSON của
Label Studio. Mỗi loại lỗi là một nhãn nhị phân → một Kappa; báo thêm Kappa trung bình và tỉ lệ đồng ý thô.
Ghi reports/task2/labeling/kappa.json (slide 5 tự đọc file này).
Chạy: python src/data/compute_kappa.py reports/task2/labeling/annotator_Dang.csv reports/task2/labeling/annotator_Uyen.csv
"""
import csv, json, sys

CATS = ["sai_dau_thanh", "ten_rieng", "so", "thieu_thua_tu", "sai_nghia_dich"]


def load(path):
    if path.endswith(".json"):                                    # Label Studio export (JSON)
        out = {}
        for t in json.load(open(path, encoding="utf-8")):
            ch = set()
            for a in t.get("annotations", [])[:1]:
                for r in a.get("result", []):
                    ch |= set(r.get("value", {}).get("choices", []))
            out[int(t["data"]["stt"])] = {c: int(c in ch) for c in CATS}
        return out
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            vals = {c: 1 if str(r.get(c, "")).strip() in ("1", "x", "X", "có") else 0 for c in CATS}
            filled = any(str(r.get(c, "")).strip() for c in CATS)
            out[int(r["stt"])] = vals if filled else None
    return out


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else (po - pe) / (1 - pe), po


A, B = load(sys.argv[1]), load(sys.argv[2])
keys = sorted(k for k in A if A.get(k) is not None and B.get(k) is not None)
if len(keys) < len(A):
    print(f"cảnh báo: {len(A) - len(keys)} câu chưa được cả hai người gán, bị bỏ qua")
res = {"n_sentences": len(keys), "per_category": {}}
for c in CATS:
    k, po = kappa([A[i][c] for i in keys], [B[i][c] for i in keys])
    res["per_category"][c] = {"kappa": None if k is None else round(k, 3), "agreement": round(po, 3),
                              "count_A": sum(A[i][c] for i in keys), "count_B": sum(B[i][c] for i in keys)}
ks = [v["kappa"] for v in res["per_category"].values() if v["kappa"] is not None]
res["mean_kappa"] = round(sum(ks) / len(ks), 3) if ks else None
res["exact_set_agreement"] = round(sum(A[i] == B[i] for i in keys) / len(keys), 3)
res["interpretation"] = "Landis & Koch 1977: <0,2 thấp · 0,21–0,4 khá · 0,41–0,6 trung bình · 0,61–0,8 tốt · >0,8 rất tốt"
json.dump(res, open("reports/task2/labeling/kappa.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(res, ensure_ascii=False, indent=1))
