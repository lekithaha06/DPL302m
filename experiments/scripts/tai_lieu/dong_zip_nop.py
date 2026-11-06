#!/usr/bin/env python3
"""Đóng zip nộp cuối: repo cuối + tài liệu của Kiệt + tài liệu nhóm. Không đưa dữ liệu thô, văn bản PhoMT, checkpoint từng epoch."""
import sys
import zipfile
from pathlib import Path

TW = Path(__file__).resolve().parents[2]; T3 = TW / "task3"; R = TW / "repo_cuoi"; RA = TW / "BAN_NOP_CUOI/repo_asr_vi_en_cuoi.zip"
sys.stdout.reconfigure(encoding="utf-8")
BO = {"__pycache__", ".pytest_cache", ".ruff_cache", ".venv"}
KIET = [T3 / "tai_lieu" / f for f in ("BaoCao_Task2_LeTuanKiet.docx", "BaoCao_Task2_LeTuanKiet.pdf", "Slide_Task2_LeTuanKiet.pptx", "BaoCao_ASR_Task2_DA_DIEN.docx", "Slide_ASR_Task2_DA_DIEN.pptx", "NGUON_SO_DA_DIEN.csv")]
KIET += [T3 / "README_BAN_NOP.md", T3 / "BAN_GIAO_KIET.md", T3 / "CHECKLIST_YEU_CAU.md", T3 / "NHAT_KY.md", TW / "kien_truc/RA_SOAT_CUOI.md"]
NHOM = ["1_bao_cao/BaoCao_Project_Nhom.docx", "1_bao_cao/BaoCao_Project_Nhom.pdf", "2_slide/Slide_Project_Nhom.pptx", "2_slide/Slide_Project_Nhom.pdf",
        "3_paper/Paper_Springer_LNCS.docx", "3_paper/Paper_Springer_LNCS.pdf", "4_checklist/Checklist_Nop_Bai.docx", "4_checklist/Checklist_Nop_Bai.pdf"]
tmp = RA.with_suffix(".tmp"); n = 0
with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, allowZip64=True, compresslevel=6) as z:
    for p in sorted(R.rglob("*")):
        if p.is_file() and not BO & set(p.parts):
            z.write(p, "repo_asr_vi_en/" + p.relative_to(R).as_posix()); n += 1
    for p in KIET:
        if p.exists():
            z.write(p, "repo_asr_vi_en/tai_lieu_Kiet/" + p.name); n += 1
        else:
            print("THIẾU", p)
    for f in NHOM:
        z.write(TW / "tai_lieu_nhom_V2" / f, "repo_asr_vi_en/tai_lieu_nhom/" + f); n += 1
    for f in ("TAI_LIEU_KY_THUAT_BAO_UYEN.docx", "TAI_LIEU_KY_THUAT_BAO_UYEN.pdf"):
        z.write(TW / "tai_lieu_nhom_V2" / f, "repo_asr_vi_en/tai_lieu_nhom/" + f); n += 1
    for p in sorted((TW / "tai_lieu_nhom_V2/6_hinh").iterdir()):
        z.write(p, "repo_asr_vi_en/tai_lieu_nhom/6_hinh/" + p.name); n += 1
z = zipfile.ZipFile(tmp); bad = z.testzip(); z.close()
assert bad is None, bad
tmp.replace(RA); print(RA, n, "file", round(RA.stat().st_size / 1e6), "MB, testzip OK")
