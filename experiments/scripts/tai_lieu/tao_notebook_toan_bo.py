#!/usr/bin/env python3
"""Sinh notebooks/00_toan_bo_code.ipynb và DANH_MUC_CODE.md từ repo cuối.

Mã nguồn đọc trực tiếp từ file khi sinh, nên notebook luôn khớp code thật. Script tự quét mọi file code của repo,
file nào không thuộc mục nào sẽ rơi vào mục "Khác", và ô cuối notebook kiểm lại không sót file nào.
Ô mã nguồn mở đầu bằng %%script false nên Run All không chạy lại huấn luyện; ô kết quả chạy thật và lưu output.
Dùng: python scripts/tao_notebook_toan_bo.py [--chay]"""
import asyncio
import sys
from pathlib import Path

import nbformat as nbf

T3 = Path(__file__).resolve().parents[1]
R = T3.parent / "repo_cuoi"
ND = {".py", ".sh", ".yml", ".yaml", ".toml", ".ini", ".txt"}
TEN = {"Dockerfile", ".env.example", ".dockerignore", ".gitignore"}
BO = ("__pycache__", ".pytest_cache", ".ruff_cache", ".venv", "experiments/runs", "experiments/reports", "experiments/checkpoints", "experiments/logs", "checkpoints/", "reports/", "tests/bo_cau_tu_thu/audio")


def cac_file():
    F = []
    for p in sorted(R.rglob("*")):
        rel = p.relative_to(R).as_posix()
        if p.is_file() and (p.suffix in ND or p.name in TEN or p.name.startswith("Dockerfile") or (rel.startswith(("configs/", "experiments/configs/")) and p.suffix == ".json")) and not any(rel.startswith(b) or f"/{b}" in rel for b in BO):
            F.append(rel)
    return F


MUC = [
    ("Dữ liệu: tải, làm sạch, chống rò rỉ, EDA, cân bằng", ("experiments/scripts/data/", "data/"), "ket_du_lieu"),
    ("Khối nghe: suy luận, chấm điểm, phân tích lỗi", ("experiments/scripts/asr/run_asr", "experiments/scripts/asr/make_", "experiments/scripts/asr/score", "experiments/scripts/asr/test_", "experiments/scripts/asr/README", "experiments/scripts/asr/bootstrap", "experiments/scripts/asr/dien", "experiments/scripts/asr/error", "experiments/scripts/asr/tao_ds", "experiments/scripts/asr/tone", "experiments/scripts/asr/tong_hop", "experiments/configs/asr", "experiments/configs/common", "experiments/configs/README", "configs/"), "ket_asr"),
    ("Baseline end-to-end B1 Whisper Translate", ("experiments/scripts/baseline2/",), "ket_b1"),
    ("Khối dịch: dữ liệu, huấn luyện LoRA V1–V4, dịch, bootstrap", ("experiments/scripts/mt/", "experiments/configs/mt/"), "ket_mt"),
    ("Chọn bản cuối, ablation, đánh giá tổng hợp", ("experiments/scripts/ket_luan", "experiments/scripts/cham_theo_mien", "experiments/scripts/he_thong_bootstrap", "experiments/scripts/ve_bieu_do"), "ket_ablation"),
    ("Kiểm tra 3 seed", ("experiments/scripts/modal_3seed", "experiments/scripts/tong_hop_3seed", "experiments/scripts/tao_notebook_3seed"), "ket_3seed"),
    ("Độ bền khối nghe", ("experiments/scripts/asr/tao_audio_robust", "experiments/scripts/hang_doi_robust", "experiments/scripts/tao_notebook_robust"), "ket_robust"),
    ("Sản phẩm: pipeline, API, demo, Docker, CI", ("src/", "api/", "app/", "docker/", ".github/", "requirements", "pyproject", "pytest", ".env", ".docker", ".git"), "ket_san_pham"),
    ("Kiểm thử", ("tests/",), "ket_test"),
    ("Điều phối, môi trường, sinh notebook và tài liệu", ("experiments/",), None),
]
KET = {
    "ket_du_lieu": """xem_log("s1_viec1*", "s2a*", "s2b*", "s3a*", "s3b*", "s6_make*")
bang("experiments/reports/data/lam_sach_tom_tat.json")
for f in sorted((R / "experiments/runs/manifests").glob("*.jsonl")):
    print(f.name, sum(1 for _ in open(f, encoding="utf-8")), "dòng")""",
    "ket_asr": """xem_log("s4_asr_baseline*", "s4_make*", "h4_beam1*")
display(pd.read_csv(R / "experiments/reports/asr/results_task2.csv"))""",
    "ket_b1": """xem_log("b1_whisper_translate*")
bang("experiments/runs/mt/B1_whisper-small_translate/fleurs_test_audio/score.json")
bang("experiments/reports/mt/bootstrap_B0_fleurs_test_asr_pho_vs_B1.json")""",
    "ket_mt": """xem_log("train_V1*", "train_V2.log", "train_V3*", "train_V4*", "hang_doi_dem2*", n=12)
rows = []
for v in ("V1", "V2", "V3", "V4", "A_r8", "A_r32", "A_aug"):
    for e in json.loads((R / "experiments/checkpoints" / v / "epochs.json").read_text(encoding="utf-8")):
        rows.append({"bản": v, "epoch": e["epoch"], "dev_loss": round(e["dev_loss"], 4), "BLEU dev": e.get("dev_BLEU_translate", e["dev_BLEU"]), "phút": e["minutes"]})
display(pd.DataFrame(rows).pivot(index="bản", columns="epoch", values="BLEU dev"))
display(Image(filename=str(R / "experiments/checkpoints/V2/curves.png"), width=620))
import hashlib
dong = (R / "checkpoints/SHA256SUMS").read_text().splitlines(); sai = 0
for l in dong:
    h, f = l.split(maxsplit=1); p = R / "checkpoints" / f
    ok = hashlib.sha256(p.read_bytes()).hexdigest() == h; sai += not ok
    print(("ĐÚNG" if ok else "SAI "), f, round(p.stat().st_size / 1e6, 1), "MB", h[:16])
print(len(dong), "adapter,", sai, "sai SHA256")
bang("checkpoints/V2/best/chon.json")""",
    "ket_ablation": """print((R / "experiments/reports/ablation/QUY_TAC_CHON.md").read_text(encoding="utf-8"))
display(pd.read_csv(R / "experiments/reports/ablation/bang_ablation.csv"))
bang("experiments/reports/mt/bootstrap_B0_V2_cascade_test.json")
bang("experiments/reports/he_thong_V2/ket_qua.json")""",
    "ket_3seed": """print((R / "experiments/reports/ba_seed/QUY_TAC_3SEED.md").read_text(encoding="utf-8"))
display(pd.read_csv(R / "experiments/reports/ba_seed/bang_3seed.csv"))
display(pd.read_csv(R / "experiments/reports/ba_seed/bang_ablation_3seed.csv"))
bang("experiments/reports/ba_seed/ket_qua_3seed.json")""",
    "ket_robust": """display(pd.read_csv(R / "experiments/reports/robust/bang_robust.csv"))
display(Image(filename=str(R / "experiments/reports/robust/bang_robust.png"), width=620))""",
    "ket_san_pham": """import subprocess, torch
print("GPU:", torch.cuda.is_available())
os.chdir(R); sys.path.insert(0, str(R))
from src.pipeline import HeThong
import soundfile as sf
f = sorted((R / "experiments/nghe_kiem/audio").glob("*.wav"))[0]
he = HeThong()
a, sr = sf.read(f, dtype="float32")
kq = he.xu_ly(a, sr).dict()
print("Nạp checkpoints/V2/best, chạy thật trên", f.name)
print({k: v for k, v in kq.items() if k != 'cac_doan'})
bang("experiments/reports/he_thong_V2/thu_gradio/ket_qua_api.json")""",
    "ket_test": """r = subprocess.run([sys.executable, "-m", "pytest", "-o", "addopts=", "-q", "-p", "no:cacheprovider"], cwd=R, capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout.strip().splitlines()[-1])""",
}


def tao():
    F = cac_file(); da = set(); C = []
    md = lambda s: C.append(nbf.v4.new_markdown_cell(s))
    code = lambda s: C.append(nbf.v4.new_code_cell(s))
    nhom = []
    for ten, tien_to, ket in MUC:
        ds = [f for f in F if f not in da and f.startswith(tien_to)]
        da |= set(ds); nhom.append((ten, ds, ket))
    khac = [f for f in F if f not in da]
    if khac:
        nhom.append(("Khác", khac, None))
    md("# DPL302m – Đề tài 1: toàn bộ code của project\n\nNhận dạng giọng nói tiếng Việt và dịch sang văn bản tiếng Anh, miền Giáo dục.\n\n"
       "Cascade: **PhoWhisper-small** → **VinAI Translate vi2en-v2 + LoRA V2**. LoRA chỉ ở khối dịch, khối nghe không fine-tune.\n\n"
       f"Notebook này gom nguyên văn **{len(F)} file code và cấu hình** của repo, xếp theo thứ tự chạy, kèm output kết quả thật.\n\n"
       "**Cách đọc:** mỗi ô chứa nguyên văn một file (dòng đầu `%%nguon <đường dẫn>`), ngay dưới là output của file đó. File chạy được trong notebook thì chạy thật: train ngắn và lưu checkpoint, dịch, nhận dạng, chấm điểm, bootstrap, test. File cần dữ liệu thô hoặc GPU nhiều giờ thì hiện log thật của lần chạy gốc. Output nói rõ từng trường hợp.\n\n"
       "Muốn chạy lại thật: xem `experiments/README.md` và `experiments/chay_lai.sh`.\n\n**Mục lục**\n\n" + "\n".join(f"{i}. {t} ({len(d)} file)" for i, (t, d, _) in enumerate(nhom, 1)))
    md("## Thiết lập")
    code((T3 / "scripts/o_thiet_lap_nb.py").read_text(encoding="utf-8"))
    for i, (ten, ds, ket) in enumerate(nhom, 1):
        md(f"## {i}. {ten}")
        for f in ds:
            s = (R / f).read_text(encoding="utf-8", errors="replace").rstrip()
            code(f"%%nguon {f}\n{s or '# (file rỗng)'}")
        if ket:
            md(f"### Output thật mục {i}")
            code(KET[ket])
    md("## Kiểm tra độ đầy đủ\n\nĐối chiếu danh sách file trong notebook với file code thực tế của repo.")
    code(f"ds = {F!r}\nthieu = [f for f in ds if f not in DA_CHAY]\nprint(len(ds), 'file code, đã chạy ô output', len(DA_CHAY), ', thiếu', len(thieu))\nassert not thieu")
    n = nbf.v4.new_notebook(cells=C); n.metadata.kernelspec = {"name": "san-pham-gpu", "display_name": "san-pham-gpu", "language": "python"}
    L = ["# Danh mục toàn bộ code", "", f"{len(F)} file code và cấu hình. Bản gom nguyên văn kèm output: `notebooks/00_toan_bo_code.ipynb`.", ""]
    for t, d, _ in nhom:
        L += [f"## {t} ({len(d)} file)", ""] + [f"- `{f}`" for f in d] + [""]
    (R / "DANH_MUC_CODE.md").write_text("\n".join(L), encoding="utf-8")
    return n, len(F)


if __name__ == "__main__":
    n, k = tao(); ra = R / "notebooks/00_toan_bo_code.ipynb"; nbf.write(n, ra); print(k, "file code,", len(n.cells), "ô")
    if "--chay" in sys.argv:
        from nbclient import NotebookClient
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        import os
        os.environ.update(HF_HUB_CACHE=str(T3 / "hf_home/hub"), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", PYTHONIOENCODING="utf-8", PYTHONUTF8="1", HF_HUB_DISABLE_TELEMETRY="1")
        NotebookClient(n, timeout=None, kernel_name="san-pham-gpu", allow_errors=True, resources={"metadata": {"path": str(R / "notebooks")}}).execute()
        for c in n.cells:
            if c.cell_type == "code":
                c.outputs = [o for o in c.outputs if not (o.get("output_type") == "stream" and o.get("name") == "stderr")]
        nbf.write(n, ra)
        loi = [o for c in n.cells if c.cell_type == "code" for o in c.outputs if o.get("output_type") == "error"]
        print("LỖI:", len(loi)); [print(o["ename"], o["evalue"][:300]) for o in loi]
