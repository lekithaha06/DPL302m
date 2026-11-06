#!/usr/bin/env python3
"""Sinh notebooks/05_do_ben_khoi_nghe.ipynb. Chỉ đọc kết quả đã chạy (scripts/hang_doi_robust.sh), ghi reports/robust/bang_robust.csv."""
from pathlib import Path

import nbformat as nbf

T = Path(__file__).resolve().parents[1]
n = nbf.v4.new_notebook()
n.metadata.kernelspec = {"name": "task3-dpl302m", "display_name": "task3-dpl302m", "language": "python"}
n.cells = [
    nbf.v4.new_markdown_cell("# Độ bền PhoWhisper-small khi audio bị nhiễu\n\nĐo trên 857 bản FLEURS test. Mỗi điều kiện đổi đúng một yếu tố so với bản gốc: nhiễu trắng theo SNR, tốc độ (resample), âm lượng.\n\nĐây chỉ là bài đo độ bền. Khối nghe **không** được fine-tune, kết quả **không** dùng để chọn mô hình. Nhiễu tất định theo id bản thu, seed 42. Chấm bằng `score_asr.py`, cùng protocol ASR.\n\nChạy lại: `bash scripts/hang_doi_robust.sh` (cần GPU và `data/`)."),
    nbf.v4.new_markdown_cell("## 1. Cách sinh audio nhiễu"),
    nbf.v4.new_code_cell('from pathlib import Path\nT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()\nprint((T / "scripts/asr/tao_audio_robust.py").read_text(encoding="utf-8"))'),
    nbf.v4.new_markdown_cell("## 2. Kết quả"),
    nbf.v4.new_code_cell('''import json
import pandas as pd
goc = json.loads((T / "runs/asr/kiet_t2_phowhisper-small_fleurs_test/score/summary.json").read_text(encoding="utf-8"))
dk = [("noise_snr20", "nhiễu trắng SNR 20 dB"), ("noise_snr10", "nhiễu trắng SNR 10 dB"), ("speed_0.9", "chậm lại 0,9 lần"), ("speed_1.1", "nhanh lên 1,1 lần"), ("vol_-12dB", "giảm âm lượng 12 dB")]
R = [dict(dieu_kien="goc", mo_ta="bản gốc", n=goc["n"], WER=goc["WER_percent"], CER=goc["CER_percent"], chenh_WER=0.0)]
for k, v in dk:
    s = json.loads((T / f"runs/robust/robust_pho_{k}/score/summary.json").read_text(encoding="utf-8"))
    R.append(dict(dieu_kien=k, mo_ta=v, n=s["n"], WER=s["WER_percent"], CER=s["CER_percent"], chenh_WER=round(s["WER_percent"] - goc["WER_percent"], 2)))
B = pd.DataFrame(R); (T / "reports/robust").mkdir(exist_ok=True); B.to_csv(T / "reports/robust/bang_robust.csv", index=False, encoding="utf-8-sig"); B'''),
    nbf.v4.new_code_cell('''import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 3.6)); ax.bar(B.mo_ta, B.WER, color="#4c72b0")
for i, v in enumerate(B.WER):
    ax.text(i, v + .3, f"{v:.2f}", ha="center", fontsize=9)
ax.set_ylabel("WER (%)"); ax.set_title("PhoWhisper-small, FLEURS test, 857 bản thu"); plt.xticks(rotation=20, ha="right"); plt.tight_layout(); fig.savefig(T / "reports/robust/bang_robust.png", dpi=150); plt.show()'''),
    nbf.v4.new_markdown_cell("## 3. Giới hạn\n\nNhiễu trắng và đổi tốc độ bằng resample không phải tiếng ồn lớp học hay micro thật. Số ở đây chỉ cho biết xu hướng. Câu hỏi hệ chạy thế nào ngoài dataset vẫn cần bộ audio tự thu (`tests/bo_cau_tu_thu/`, NOT RUN)."),
]
nbf.write(n, T / "notebooks/05_do_ben_khoi_nghe.ipynb"); print("ok")
