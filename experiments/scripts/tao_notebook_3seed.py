#!/usr/bin/env python3
"""Sinh notebooks/04_kiem_tra_3_seed.ipynb: tổng hợp 3 seed cho V1–V4 và ablation, ghi thêm sheet vào workbook."""
from pathlib import Path

import nbformat as nbf

T = Path(__file__).resolve().parents[1]
n = nbf.v4.new_notebook()
n.metadata.kernelspec = {"name": "task3-dpl302m", "display_name": "task3-dpl302m", "language": "python"}
md = nbf.v4.new_markdown_cell; co = nbf.v4.new_code_cell
n.cells = [
    md("# Kiểm tra 3 seed: V1–V4 và ablation\n\nSeed 42 chạy trên máy nhóm (RTX 4060, torch 2.0.1). Seed 1 và 2 train trên Modal (RTX PRO 6000, torch 2.7.1), rồi dịch và chấm bằng torch 2.0.1 trên T4, đúng môi trường của seed 42. Code: `scripts/modal_3seed.py`, `scripts/tong_hop_3seed.py`."),
    md("## 1. Quy tắc ghi trước khi train seed mới"),
    co('from pathlib import Path\nimport json, shutil, statistics as st\nimport pandas as pd\nimport matplotlib.pyplot as plt\nT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()\nR = T / "reports/ba_seed"\nprint((R / "QUY_TAC_3SEED.md").read_text(encoding="utf-8"))'),
    md("## 2. Kiểm tra phép chấm và đối chứng môi trường\n\nCùng adapter V2 seed 42 trên tập dev: T4 + torch 2.0.1 cho BLEU 26,45, khớp máy nhóm; RTX PRO 6000 + torch 2.7.1 cho 26,24. Vì vậy mọi số dưới đây đều chấm bằng torch 2.0.1.\n\nBảng dưới so V2 seed 42 train trên máy nhóm với V2 seed 42 train lại trên Modal. Job đối chứng này không tính vào trung bình. Chênh lệch ở đây cho biết riêng môi trường train đã làm số đổi bao nhiêu."),
    co('kq = json.loads((R / "ket_qua_3seed.json").read_text(encoding="utf-8"))\ndc = pd.DataFrame(kq["doi_chung_phan_cung_V2_s42"]).T\ndc["chênh"] = (dc.iloc[:, 1] - dc.iloc[:, 0]).round(2)\ndc'),
    md("## 3. V1–V4 theo từng seed\n\n`n` là số seed có dữ liệu. V1 seed 42 chưa chạy Whisper → dịch nên mục đó chỉ có 2 seed."),
    co('B = pd.read_csv(R / "bang_3seed.csv")\nB'),
    co('dat = B.pivot(index="bản", columns="chỉ số", values="trung bình")[["dev cascade", "dev sạch", "test cascade", "test sạch", "Whisper → dịch"]]\nsd = B.pivot(index="bản", columns="chỉ số", values="độ lệch chuẩn")[dat.columns]\n(dat.round(2).astype(str) + " ± " + sd.round(2).astype(str))'),
    md("## 4. Áp lại quy tắc DEV trên trung bình 3 seed"),
    co('print("Đỉnh dev cascade trung bình:", kq["M_dev_cascade_tb"])\nprint("Nhóm hoà (cách đỉnh ≤ 0,5):", kq["nhom_hoa"])\nprint("Quy tắc trên trung bình ra:", kq["quy_tac_tren_trung_binh_ra"], "· bản cuối giữ:", kq["ban_cuoi_giu_nguyen"])\nprint("Epoch tốt nhất:", kq["epoch_tot_nhat"])'),
    md("## 5. So với B0, tính riêng từng seed"),
    co('''J = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
b0c, b0s = J(T / "runs/mt/B0/fleurs_test_asr_pho/score.json")["BLEU"], J(T / "runs/mt/B0/fleurs_test_clean/score.json")["BLEU"]
v2 = B[B["bản"] == "V2"].set_index("chỉ số")
d = {s: round(v2.loc["test cascade", s] - b0c, 2) for s in ("seed 42", "seed 1", "seed 2")}
print("Δ test cascade V2 so với B0:", d, "· trung bình", round(st.mean(d.values()), 2), "· độ lệch chuẩn", round(st.stdev(d.values()), 2))
c = {s: round(v2.loc["test sạch", s] - b0s, 2) for s in ("seed 42", "seed 1", "seed 2")}
print("Δ test sạch V2 so với B0 (ngưỡng ≥ 38,27):", c, "· trung bình", round(st.mean(c.values()), 2))
print("Số seed đạt ngưỡng dịch sạch:", sum(x >= 0 for x in c.values()), "/ 3")'''),
    md("## 6. Ablation một yếu tố, 3 seed\n\nCột cuối so với V2 theo từng cặp cùng seed. Mục Whisper → dịch của ablation chỉ có 2 seed."),
    co('A = pd.read_csv(R / "bang_ablation_3seed.csv").fillna("")\nA'),
    co('''x = B[B["chỉ số"] == "test cascade"]; y = A[(A["chỉ số"] == "test cascade") & (A["bản"] != "V2")]
ten = list(x["bản"]) + list(y["bản"]); tb = list(x["trung bình"]) + list(y["trung bình"]); sd_ = list(x["độ lệch chuẩn"]) + list(y["độ lệch chuẩn"])
fig, ax = plt.subplots(figsize=(8, 3.8)); ax.bar(ten, tb, yerr=sd_, capsize=4, color=["#4c72b0"] * 4 + ["#8fa8cf"] * 3)
ax.axhline(b0c, color="#dd8452", ls="--", label=f"B0 {b0c}"); ax.set_ylabel("BLEU test cascade"); ax.set_ylim(20, 30); ax.legend(); ax.set_title("Trung bình 3 seed, thanh sai là độ lệch chuẩn"); plt.tight_layout(); fig.savefig(R / "bieu_do_3seed.png", dpi=150); plt.show()'''),
    md("## 7. Ghi thêm vào workbook"),
    co('''from openpyxl import load_workbook
X = T / "reports/danh_gia/bang_ket_qua.xlsx"
with pd.ExcelWriter(X, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
    B.to_excel(w, sheet_name="3 seed V1-V4", index=False); A.to_excel(w, sheet_name="3 seed ablation", index=False)
print(load_workbook(X).sheetnames)'''),
]
nbf.write(n, T / "notebooks/04_kiem_tra_3_seed.ipynb"); print("ok")
