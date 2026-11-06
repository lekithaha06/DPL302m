#!/usr/bin/env python3
"""Rà soát nhất quán TOÀN project sau giai đoạn 2 (04/11/2026). Chỉ đọc. Số chuẩn lấy từ file kết quả task3, rồi đối chiếu với:
tài liệu của Kiệt, bản điền của Bảo, README/app/test repo cuối, notebook (output), Excel, hình kiến trúc; hash adapter, kết quả, PhoMT, dữ liệu.
Ghi kien_truc/RA_SOAT_CUOI.md."""
import csv, hashlib, json, re, statistics, sys
from pathlib import Path

import nbformat
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

TW = Path(__file__).resolve().parents[1]; T3 = TW / "task3"; R = TW / "repo_cuoi"; EX = R / "experiments"
sys.stdout.reconfigure(encoding="utf-8")
J = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
vn = lambda x, d=2: f"{float(x):.{d}f}".replace(".", ",")
sc = lambda v, s: J(T3 / f"runs/mt/{v}/{s}/score.json")
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
KQ = []


def ok(muc, dk, ghi=""):
    KQ.append((muc, bool(dk), ghi)); print(("ĐẠT " if dk else "LỖI ") + muc + (f" – {ghi}" if ghi else ""))


def txt(p):
    p = Path(p)
    if p.suffix == ".docx":
        d = Document(p); return "\n".join([x.text for x in d.paragraphs] + [c.text for t in d.tables for r in t.rows for c in r.cells])
    if p.suffix == ".pptx":
        o = []
        for s in Presentation(p).slides:
            for sh in s.shapes:
                if sh.has_text_frame: o.append(sh.text_frame.text)
                if sh.has_table: o += [c.text for r in sh.table.rows for c in r.cells]
        return "\n".join(o)
    if p.suffix == ".ipynb":
        n = nbformat.read(p, 4)
        return "\n".join(c.source + "".join(str(o.get("text", "")) + str(o.get("data", {}).get("text/plain", "")) + str(o.get("data", {}).get("text/html", "")) for o in c.get("outputs", [])) for c in n.cells)
    return p.read_text(encoding="utf-8", errors="ignore")


# ---- 1. số chuẩn từ file gốc
ch = J(T3 / "reports/ablation/chon_ban_cuoi.json"); F = ch["ban_chon"]
c, cl, ph = sc(F, "fleurs_test_asr_pho"), sc(F, "fleurs_test_clean"), sc(F, "phomt_test")
bw = J(T3 / f"reports/mt/bootstrap_B0_{F}_cascade_wsp_test.json"); bb = J(T3 / f"reports/mt/bootstrap_B0_{F}_cascade_test.json")
ht = J(T3 / "reports/he_thong_V2/ket_qua.json")["proposed"]["tat_ca"]; b1 = sc("B1_whisper-small_translate", "fleurs_test_audio")
lap = [J(p) for p in sorted((T3 / f"reports/toc_do/lap_V2").glob(f"toc_do_{F}_lan*.json"))]; rtf = statistics.median(x["RTF_total"] for x in lap)
CHUAN = {"BLEU cascade": vn(c["BLEU"]), "dịch sạch": vn(cl["BLEU"]), "PhoMT": vn(ph["BLEU"]), "Δ B0": vn(bb["delta"]), "Whisper → bản cuối": vn(sc(F, "fleurs_test_asr_wsp")["BLEU"]),
         "RTF": vn(rtf, 3), "cả hệ BLEU": vn(ht["BLEU"]), "cả hệ WER": vn(ht["WER_asr"]), "B1": vn(b1["BLEU"])}
print("Bản cuối:", F, CHUAN)
ok("Quy tắc DEV áp lại cho ra đúng bản đã ghi", F == sorted([r for r in ch["bang_dev"] if r["dev cascade"] >= ch["M_dev_cascade"] - .5], key=lambda r: -r["dev sạch"])[0]["bản"], F)
ok("Quy tắc ghi file trước khi train ablation", (T3 / "reports/ablation/QUY_TAC_CHON.md").stat().st_mtime < (T3 / "checkpoints/A_r8/config.json").stat().st_mtime)
# ---- 2. tài liệu
DOCS = {"Báo cáo Kiệt": T3 / "tai_lieu/BaoCao_Task2_LeTuanKiet.docx", "Slide Kiệt": T3 / "tai_lieu/Slide_Task2_LeTuanKiet.pptx", "BAN_GIAO": T3 / "BAN_GIAO_KIET.md",
        "README repo": R / "README.md", "Bản điền Bảo": T3 / "tai_lieu/BaoCao_ASR_Task2_DA_DIEN.docx", "Báo cáo nhóm": TW / "tai_lieu_nhom_V2/1_bao_cao/BaoCao_Project_Nhom.docx", "Slide nhóm": TW / "tai_lieu_nhom_V2/2_slide/Slide_Project_Nhom.pptx", "Checklist nhóm": TW / "tai_lieu_nhom_V2/4_checklist/Checklist_Nop_Bai.docx", "Sơ đồ (script)": TW / "kien_truc/ve_kien_truc_du_an.py"}
T = {k: txt(v) for k, v in DOCS.items()}
for k, cac in (("Báo cáo Kiệt", list(CHUAN)), ("README repo", list(CHUAN)), ("BAN_GIAO", ["BLEU cascade", "dịch sạch", "PhoMT", "RTF", "cả hệ BLEU", "Whisper → bản cuối"]),
               ("Slide Kiệt", ["BLEU cascade", "dịch sạch", "PhoMT", "RTF", "cả hệ BLEU", "B1"]), ("Báo cáo nhóm", list(CHUAN)), ("Slide nhóm", ["BLEU cascade", "dịch sạch", "PhoMT", "RTF", "cả hệ BLEU", "B1"]), ("Bản điền Bảo", ["BLEU cascade"])):
    thieu = [x for x in cac if CHUAN[x] not in T[k]]
    ok(f"{k}: đủ số bản cuối", not thieu, f"thiếu {thieu}" if thieu else "")
CU = {"bản cuối V3/V4": r"[Bb]ản cuối\W{0,3}V[34]\b", "★ V3/V4": r"V[34] ★|★ V[34]", "BLEU sản phẩm cũ": r"27,63|chrF++ 52,48", "V4 mặc định": r"mặc định (dùng )?V4", "đề xuất V4": r"đề xuất V4|khuyến nghị.{0,20}V4", "chưa đo": r"V[24] chưa đo|chưa chạy với lời Whisper|đo trên V3"}
for k, t in T.items():
    if k == "Sơ đồ (script)": continue
    hit = {n: len(re.findall(p, t)) for n, p in CU.items() if re.search(p, t)}
    ok(f"{k}: không còn câu cũ", not hit, str(hit) if hit else "")
# ---- 3. repo khớp task3
ok("Adapter bản cuối repo = task3", sha(R / f"checkpoints/{F}/best/adapter_model.safetensors") == sha(T3 / f"checkpoints/{F}/best/adapter_model.safetensors"))
sai = [l.split()[1] for l in (R / "checkpoints/SHA256SUMS").read_text().splitlines() if sha(R / "checkpoints" / l.split()[1]) != l.split()[0]]
ok("SHA256SUMS khớp mọi adapter", not sai, str(sai) if sai else f"{len((R / 'checkpoints/SHA256SUMS').read_text().splitlines())} adapter")
khac = [str(p.relative_to(EX)) for p in (EX / "runs/mt").rglob("score.json") if (T3 / p.relative_to(EX)).exists() and p.read_bytes() != (T3 / p.relative_to(EX)).read_bytes()]
ok("score.json repo = task3", not khac, f"{len(list((EX / 'runs/mt').rglob('score.json')))} file" if not khac else str(khac[:5]))
for f in ("reports/ablation/bang_ablation.csv", "reports/ablation/chon_ban_cuoi.json", "reports/he_thong_V2/ket_qua.json", "reports/asr/results_task2.csv", "runs/b1/predictions_b1.jsonl", "reports/data/fleurs_split_ids.csv"):
    ok(f"{f} repo = task3", sha(EX / f) == sha(T3 / f))
ok("ban_chot.json = bản cuối", J(R / "configs/ban_chot.json")["ban_chot"] == F)
ok("Mặc định code = bản cuối", f'"checkpoints" / "{F}" / "best"' in (R / "src/pipeline.py").read_text(encoding="utf-8"))
for f in (".env.example", "docker/docker-compose.yml"):
    ok(f"{f} = bản cuối", f"checkpoints/{F}/best" in (R / f).read_text(encoding="utf-8"))
ok("Không có văn bản PhoMT", not [p for p in EX.rglob("*") if p.is_file() and "phomt" in str(p).lower() and p.suffix == ".jsonl"])
ok("Trong repo không có email cá nhân", not any("kietle" in p.read_text(encoding="utf-8", errors="ignore") for p in R.rglob("*.md")))
# ---- 4. notebook
for f in ("eda", "phan_tich_loi", "02_baseline_B1_whisper_translate", "03_ablation_va_chon_ban_cuoi", "01_chay_lai_thuc_nghiem", "06_danh_gia_tong_hop", "05_do_ben_khoi_nghe", "04_kiem_tra_3_seed", "07_chay_san_pham_tren_gpu"):
    p = R / f"notebooks/{f}.ipynb"; n = nbformat.read(p, 4); cd = [x for x in n.cells if x.cell_type == "code"]
    ok(f"Notebook {f}: chạy đủ, có output, không lỗi", all(x.outputs for x in cd) and not any(o.get("output_type") == "error" for x in cd for o in x.outputs) and [x.execution_count for x in cd] == list(range(1, len(cd) + 1)), f"{len(cd)} ô")
    ok(f"Notebook {f}: repo = task3", p.read_bytes() == (T3 / f"notebooks/{f}.ipynb").read_bytes())
ptl = txt(R / "notebooks/phan_tich_loi.ipynb")
ok("phan_tich_loi: có B1, ablation, bản cuối", all(x in ptl for x in (vn(b1["BLEU"], 1).replace(",", "."), "CHỌN: " + F, "Bản cuối: " + F)))
# ---- 4b. notebook toàn bộ, 3 seed, độ bền, checkpoint
n0 = nbformat.read(R / "notebooks/00_toan_bo_code.ipynb", 4); ch0 = [x for x in n0.cells if x.cell_type == "code"]
ok("Notebook 00: mọi ô output chạy không lỗi", not any(o.get("output_type") == "error" for x in ch0 for o in x.outputs), f"{len(ch0)} ô code")
ok("Notebook 00: có đủ output và kiểm SHA256", any("0 sai SHA256" in str(o.get("text", "")) for x in ch0 for o in x.outputs))
ok("Notebook 00: mọi ô code đều có output", all(x.outputs for x in ch0), f"{sum(bool(x.outputs) for x in ch0)}/{len(ch0)} ô")
ok("Notebook 00: mọi file khớp nguyên văn", not any("khớp file trong repo: False" in str(o.get("text", "")) for x in ch0 for o in x.outputs))
ds_code = [p for p in list(R.rglob("*.py")) + list(R.rglob("*.sh")) if "__pycache__" not in p.parts]
ng = "\n".join(x.source for x in ch0)
sot = [p.relative_to(R).as_posix() for p in ds_code if f"%%nguon {p.relative_to(R).as_posix()}\n" not in ng]
ok("Notebook 00: chứa toàn bộ file code", not sot, f"{len(ds_code)} file" if not sot else str(sot[:5]))
ad = sorted(p.parent.parent.name for p in (R / "checkpoints").glob("*/best/adapter_model.safetensors"))
can = {f"{v}" for v in ("V1", "V2", "V3", "V4", "A_r8", "A_r32", "A_aug")} | {f"{v}_s{s}" for v in ("V1", "V2", "V3", "V4", "A_r8", "A_r32", "A_aug") for s in (1, 2)}
ok("Checkpoint đủ 7 bản × 3 seed", can <= set(ad), f"{len(ad)} adapter" if can <= set(ad) else str(sorted(can - set(ad))))
b3 = list(csv.DictReader(open(EX / "reports/ba_seed/bang_3seed.csv", encoding="utf-8-sig")))
v2 = next(r for r in b3 if r["bản"] == "V2" and r["chỉ số"] == "test cascade"); ok("Số 3 seed V2 khớp tính lại", round(statistics.mean(float(v2[f"seed {s}"]) for s in (42, 1, 2)), 2) == float(v2["trung bình"]), v2["trung bình"])
ok("Báo cáo và slide nhóm có số 3 seed", all(vn(v2["trung bình"]) in T[k] for k in ("Báo cáo nhóm", "Slide nhóm")))
ok("README có số 3 seed", vn(v2["trung bình"]) in T["README repo"])
rb = list(csv.DictReader(open(EX / "reports/robust/bang_robust.csv", encoding="utf-8-sig"))); ok("Độ bền đủ 6 dòng, 857 bản", len(rb) == 6 and all(r["n"] == "857" for r in rb))
ok("Báo cáo nhóm không còn NOT RUN ở mục độ bền", all(vn(r["WER"]) in T["Báo cáo nhóm"] for r in rb))
ok("Checklist không còn ô chờ", "@" not in T["Checklist nhóm"].replace("@fpt", ""))
# ---- 5. Excel
wb = load_workbook(R / "reports/bang_ket_qua.xlsx", data_only=True); ok("Excel ≥ 3 sheet", len(wb.sheetnames) >= 3, str(wb.sheetnames))
gt = " ".join(str(c_.value) for ws in wb.worksheets for r_ in ws.iter_rows() for c_ in r_)
ok("Excel có số bản cuối + B1 + cả hệ", all(str(x) in gt for x in (c["BLEU"], b1["BLEU"], ht["BLEU"])))
ok("Excel đánh dấu ★ đúng bản", f"Proposed {F} ★" in gt)
ok("Excel: tốc độ bản cuối đã đo", str(round(rtf, 3)) in gt)
# ---- 6. dữ liệu
sid = {json.loads(l)["sample_id"] for l in open(TW / "GUI_DANG_FLEURS_TEST/manifest_fleurs_test.jsonl", encoding="utf-8")}
b1id = {json.loads(l)["sample_id"] for l in open(EX / "runs/b1/predictions_b1.jsonl", encoding="utf-8")}
hyp = {json.loads(l)["id"].removesuffix(".wav") for l in open(EX / f"runs/mt/{F}/fleurs_test_asr_pho/hyp.jsonl", encoding="utf-8")}
ok("B1 và bản cuối cùng 857 sample_id", sid == b1id == hyp and len(sid) == 857)
tr = {json.loads(l)["sent_id"] for f in ("fleurs_train_asr_pho", "fleurs_train_clean_asrstyle") for l in open(T3 / f"runs/mt_data/{f}.jsonl", encoding="utf-8")}
te = {json.loads(l)["sent_id"] for f in ("fleurs_dev_clean", "fleurs_test_clean") for l in open(T3 / f"runs/mt_data/{f}.jsonl", encoding="utf-8")}
ok("Không rò rỉ: câu train (cả augmentation) ∩ dev/test = 0", not tr & te)
n_ok = sum(k[1] for k in KQ)
L = [f"# Rà soát nhất quán toàn project – 04/11/2026 (bản cuối {F})", "", f"**{n_ok}/{len(KQ)} mục đạt.** Script: `kien_truc/ra_soat_cuoi.py` (chỉ đọc).", "",
     "Số chuẩn: " + " · ".join(f"{k} {v}" for k, v in CHUAN.items()), "", "| Mục | Kết quả | Ghi chú |", "|---|---|---|"]
L += [f"| {m} | {'ĐẠT' if d else '**LỖI**'} | {g.replace('|', '/')} |" for m, d, g in KQ]
(TW / "kien_truc/RA_SOAT_CUOI.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print(f"\n{n_ok}/{len(KQ)} đạt")
