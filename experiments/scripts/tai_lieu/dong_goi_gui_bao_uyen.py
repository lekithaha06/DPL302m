#!/usr/bin/env python3
"""Gói cho Bảo và Uyên tự viết báo cáo, slide riêng: bảng số, hình, nguồn. Không kèm báo cáo và slide của Kiệt, không checkpoint, không dữ liệu, không văn bản PhoMT."""
import sys
import zipfile
from pathlib import Path

TW = Path(__file__).resolve().parents[2]; T3 = TW / "task3"; R = TW / "repo_cuoi"; EX = R / "experiments"; N = TW / "tai_lieu_nhom_V2"
RA = TW / "GUI_BAO_UYEN_BAO_CAO_SLIDE.zip"; G = "GUI_BAO_UYEN_BAO_CAO_SLIDE/"
sys.stdout.reconfigure(encoding="utf-8")
DS = []  # (nguồn, đích)


def them(src, dst):
    src = Path(src)
    if src.is_dir():
        for p in sorted(src.rglob("*")):
            if p.is_file() and p.suffix not in (".jsonl", ".pyc") and not p.name.endswith(".per_utt.csv"):
                DS.append((p, dst + "/" + p.relative_to(src).as_posix()))
    else:
        assert src.exists(), src
        DS.append((src, dst))


them(TW / "tai_lieu_nhom_V2/DOC_TRUOC_BAO_UYEN.md", "DOC_TRUOC.md")
them(TW / "tai_lieu_nhom_V2/TAI_LIEU_KY_THUAT_BAO_UYEN.docx", "TAI_LIEU_KY_THUAT.docx")
them(TW / "tai_lieu_nhom_V2/TAI_LIEU_KY_THUAT_BAO_UYEN.pdf", "TAI_LIEU_KY_THUAT.pdf")
them(N / "4_checklist/Checklist_Nop_Bai.docx", "5_tham_khao/Checklist_Nop_Bai.docx")
them(N / "6_hinh", "2_hinh/kien_truc_va_vi_du")
them(EX / "reports/tong_hop", "2_hinh/tong_hop")
them(EX / "reports/ablation/bang_ablation.png", "2_hinh/ablation/bang_ablation.png")
them(EX / "reports/ba_seed/bieu_do_3seed.png", "2_hinh/ba_seed/bieu_do_3seed.png")
them(EX / "reports/robust/bang_robust.png", "2_hinh/do_ben/bang_robust.png")
them(EX / "reports/data/eda", "2_hinh/du_lieu/eda")
them(EX / "reports/data/can_bang", "2_hinh/du_lieu/can_bang")
for p in sorted((EX / "reports/asr").glob("tone_confusion_*.png")):
    them(p, "2_hinh/asr/" + p.name)
them(R / "reports/bang_ket_qua.xlsx", "3_bang_so/bang_ket_qua.xlsx")
for f in ("reports/ablation/bang_ablation.csv", "reports/ablation/QUY_TAC_CHON.md", "reports/ablation/chon_ban_cuoi.json", "reports/ba_seed/bang_3seed.csv", "reports/ba_seed/bang_ablation_3seed.csv", "reports/ba_seed/ket_qua_3seed.json", "reports/ba_seed/QUY_TAC_3SEED.md",
          "reports/robust/bang_robust.csv", "reports/domain/ket_qua_theo_mien.csv", "reports/he_thong_V2/ket_qua.json", "reports/he_thong_V2/bang.md", "reports/he_thong_V2/bootstrap_cu_vs_moi.json", "reports/asr/results_task2.csv", "reports/asr/paper_comparison.csv",
          "reports/asr/gap_hypotheses.csv", "reports/asr/strata.csv", "reports/asr/long_form_audit.csv", "reports/asr/error_audit.csv", "reports/mt/failure_V1_dev.md", "reports/mt/failure_V2_dev.md", "reports/data/nguon_du_lieu.md", "reports/data/kiem_chung.md", "reports/data/lam_sach_dem_tung_buoc.csv", "reports/data/lam_sach_tom_tat.json"):
    them(EX / f, "3_bang_so/" + f.replace("reports/", ""))
for p in sorted((EX / "reports/mt").glob("bootstrap_*.json")):
    them(p, "3_bang_so/mt/" + p.name)
for p in sorted((EX / "reports/toc_do/lap_V2").glob("*.json")):
    them(p, "3_bang_so/toc_do/" + p.name)
them(T3 / "tai_lieu/NGUON_SO_DA_DIEN.csv", "3_bang_so/NGUON_SO_DA_DIEN.csv")
for f in ("eda", "phan_tich_loi", "02_baseline_B1_whisper_translate", "03_ablation_va_chon_ban_cuoi", "06_danh_gia_tong_hop", "05_do_ben_khoi_nghe", "04_kiem_tra_3_seed", "00_toan_bo_code", "07_chay_san_pham_tren_gpu"):
    them(R / f"notebooks/{f}.ipynb", f"4_notebook/{f}.ipynb")
for f in ("README.md", "KIEM_THU_CUOI.md", "CHANGELOG.md", "DANH_MUC_CODE.md"):
    them(R / f, "5_tham_khao/" + f)
them(TW / "VIEC_CON_LAI.md", "5_tham_khao/VIEC_CON_LAI.md")
tmp = RA.with_suffix(".tmp")
with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
    for s, d in DS:
        if s.name == "ban_cuoi_quy_tac_cu.txt":
            continue
        if s == R / "README.md":  # bản trong gói: sửa nhãn sai, bản README của repo giữ nguyên
            z.writestr(G + d, s.read_text(encoding="utf-8").replace("# bản cuối theo quy tắc chọn trên dev", "# bản để so sánh, bản cuối là V2"))
            continue
        z.write(s, G + d)
z = zipfile.ZipFile(tmp); assert z.testzip() is None; L = z.namelist(); z.close(); tmp.replace(RA)
bad = [x for x in L if x.endswith((".safetensors", ".wav", ".jsonl"))]
nhom = {}
for x in L:
    k = x.split("/")[1]; a = nhom.setdefault(k, [0, 0]); a[0] += 1
print(RA, len(L), "file", round(RA.stat().st_size / 1e6, 1), "MB; file cấm:", bad)
for k, a in nhom.items():
    print(f"{a[0]:4d} file  {k}")
