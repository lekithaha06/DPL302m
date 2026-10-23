"""Task 2 · Visual Results (phần Đăng): ví dụ đầu ra tiêu biểu của bản cuối (tham số, mặc định V2) so với B0 trên FLEURS test.

Chọn tự động, không chọn tay: mỗi câu gốc chỉ lấy một bản thu; lấy 3 câu bản cuối tốt lên nhiều nhất (chrF++ câu),
1 câu có số, và 2 câu bản cuối vẫn sai. Ghi reports/task2/system/visual_results.md và .json.
"""
import json, re, sys
import sacrebleu
NEW = sys.argv[1] if len(sys.argv) > 1 else "V2"   # bản cuối

B = {r["audio"]: r for r in json.load(open("reports/task2/mt/predictions_B0.json", encoding="utf-8"))}
V = {r["audio"]: r for r in json.load(open(f"reports/task2/mt/predictions_{NEW}.json", encoding="utf-8"))}
src = {r["audio"]: r for r in json.load(open("reports/task1/mt/predictions_fleurs_test.json", encoding="utf-8"))}
rows = []
for a, s in src.items():
    c0 = sacrebleu.sentence_chrf(B[a]["cascade"], [s["en_ref"]], word_order=2).score
    c2 = sacrebleu.sentence_chrf(V[a]["cascade"], [s["en_ref"]], word_order=2).score
    rows.append({"audio": a, "id": s["id"], "vi_ref": s["vi_raw"], "asr": s["asr"], "en_ref": s["en_ref"],
                 "B0": B[a]["cascade"], "final": V[a]["cascade"], "version": NEW, "chrf_B0": round(c0, 1), "chrf_final": round(c2, 1),
                 "has_digits": bool(re.search(r"\d", s["vi_raw"]))})


def pick(cands, k, used):
    out = []
    for r in cands:
        if r["id"] not in used and len(r["vi_ref"]) < 170:
            out.append(r); used.add(r["id"])
        if len(out) == k:
            break
    return out


used = set()
gain = sorted(rows, key=lambda r: r["chrf_final"] - r["chrf_B0"], reverse=True)
sel = {"tốt lên": pick(gain, 3, used),
       "Câu có số": pick([r for r in gain if r["has_digits"]], 1, used),
       "vẫn sai": pick(sorted(rows, key=lambda r: r["chrf_final"]), 2, used)}
json.dump(sel, open("reports/task2/system/visual_results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
md = [f"# Visual Results: B0 so với {NEW} (FLEURS test, chọn tự động theo chrF++ từng câu)", ""]
for group, rs in sel.items():
    md += [f"## {group}", ""]
    for r in rs:
        md += [f"- **Câu đúng (vi):** {r['vi_ref']}", f"  - **Máy nghe (PhoWhisper):** {r['asr']}", f"  - **Tham chiếu (en):** {r['en_ref']}",
               f"  - **B0:** {r['B0']} *(chrF++ {r['chrf_B0']})*", f"  - **{NEW}:** {r['final']} *(chrF++ {r['chrf_final']})*", ""]
open("reports/task2/system/visual_results.md", "w", encoding="utf-8").write("\n".join(md))
print("\n".join(md))
