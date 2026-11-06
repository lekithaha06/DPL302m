#!/usr/bin/env python3
"""So lần chạy lại với kết quả gốc: code, dự đoán ASR, bản dịch, điểm, trọng số adapter. Chỉ đọc, ghi báo cáo vào chính thư mục này."""
import hashlib, json, sys
from pathlib import Path
import nbformat
import torch
from safetensors.torch import load_file

W = Path(__file__).resolve().parent; T = W.parent; R = T.parent / "repo_cuoi"
sys.stdout.reconfigure(encoding="utf-8")
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
L = []


def ghi(*a):
    s = " ".join(map(str, a)); print(s); L.append(s)


ghi("# So lần chạy lại với kết quả gốc", "")
# ---- 1. code
ghi("## 1. Code", "")
BO = {"__pycache__"}
ten = sorted(p.relative_to(W / "scripts").as_posix() for p in (W / "scripts").rglob("*") if p.is_file() and not BO & set(p.parts))
khac = [f for f in ten if sha(W / "scripts" / f) != sha(T / "scripts" / f)] if all((T / "scripts" / f).exists() for f in ten) else "thiếu file"
ghi("Script chạy lại so với task3/scripts:", len(ten), "file, khác:", khac)
CHINH = ["data/viec1_tai_3_bo_du_lieu.py", "data/viec2_ghep_chia_fleurs_chong_trung.py", "data/viec2_lam_sach_du_lieu.py", "data/viec3_eda.py", "data/viec4_can_bang_du_lieu.py", "data/gan_mien_flores.py", "data/ham_dung_chung.py", "asr/make_asr_manifest.py", "asr/run_asr.py", "asr/score_asr.py", "mt/make_mt_data.py", "mt/make_balanced_data.py", "mt/translate.py", "mt/train_lora.py", "mt/bootstrap.py", "mt/do_toc_do.py", "cham_theo_mien.py"]
rep = [(f, sha(W / "scripts" / f) == sha(R / "experiments/scripts" / f)) for f in CHINH]
ghi("Script chính so với repo_cuoi:", sum(k for _, k in rep), "/", len(rep), "giống; khác:", [f for f, k in rep if not k])
n = nbformat.read(T / "notebooks/01_chay_lai_thuc_nghiem.ipynb", 4); tep = 0; dung = 0
for c in n.cells:
    if c.cell_type == "code" and c.source.startswith("%%tep"):
        a = c.source.split("\n", 1); f = a[0].split()[2]; tep += 1; dung += (W / f).read_text(encoding="utf-8").rstrip() == a[1].rstrip()
ghi("Ô %%tep trong notebook khớp file đã chạy:", dung, "/", tep, "")
for v in ("V1", "V2", "V3", "V4"):
    a, b = (json.load(open(x / f"checkpoints/{v}/config.json", encoding="utf-8")) for x in (W, T))
    kk = [k for k in a if k not in ("train", "dev", "out_dir", "resume") and a[k] != b.get(k)]
    ghi(f"Cấu hình train {v}: tham số khác:", kk, "; dữ liệu train:", [Path(x).name for x in a["train"]] == [Path(x.replace(chr(92), "/")).name for x in b["train"]])
# ---- 2. dữ liệu đầu vào
ghi("", "## 2. Dữ liệu vào khối dịch", "")
for f in sorted((T / "runs/mt_data").glob("*.jsonl")):
    g = W / "runs/mt_data" / f.name
    if g.exists():
        ghi(f.name, "giống byte" if sha(f) == sha(g) else "KHÁC")
# ---- 3. kết quả
ghi("", "## 3. Dự đoán và điểm", "")
tong = cau = khac_cau = 0
for r in sorted((W / "runs/asr").iterdir()):
    a, b = r / "predictions.jsonl", T / "runs/asr" / r.name / "predictions.jsonl"
    A = {json.loads(l)["id"]: json.loads(l)["prediction"] for l in open(a, encoding="utf-8")}; B = {json.loads(l)["id"]: json.loads(l)["prediction"] for l in open(b, encoding="utf-8")}
    k = sum(A[i] != B[i] for i in B); cau += len(B); khac_cau += k; ghi("ASR", r.name.replace("kiet_t2_", ""), len(B), "câu, khác", k)
for v in ("B0", "V1", "V2", "V3", "V4"):
    for d in sorted(p.name for p in (W / "runs/mt" / v).iterdir()):
        a, b = W / "runs/mt" / v / d, T / "runs/mt" / v / d
        if not (b / "hyp.jsonl").exists():
            ghi("MT", v, d, "không có bản gốc để so" if not b.exists() else "bản gốc không giữ hyp"); continue
        A = {json.loads(l)["id"]: json.loads(l)["hyp"] for l in open(a / "hyp.jsonl", encoding="utf-8")}; B = {json.loads(l)["id"]: json.loads(l)["hyp"] for l in open(b / "hyp.jsonl", encoding="utf-8")}
        k = sum(A[i] != B[i] for i in B); sa, sb = json.load(open(a / "score.json", encoding="utf-8")), json.load(open(b / "score.json", encoding="utf-8"))
        cau += len(B); khac_cau += k; tong += 1
        ghi("MT", v, d, len(B), "câu, khác", k, "· BLEU", sa["BLEU"], sb["BLEU"], "· chrF++", sa["chrF++"], sb["chrF++"], "" if sa["BLEU"] == sb["BLEU"] and sa["chrF++"] == sb["chrF++"] else "← LỆCH")
ghi("", f"Tổng: {cau} câu, khác {khac_cau}, tức {100 * (1 - khac_cau / cau):.4f}% giống")
# ---- 4. checkpoint
ghi("", "## 4. Trọng số adapter tốt nhất", "")
for v in ("V1", "V2", "V3", "V4"):
    a, b = W / f"checkpoints/{v}/best/adapter_model.safetensors", T / f"checkpoints/{v}/best/adapter_model.safetensors"
    A, B = load_file(a), load_file(b); ten_ = sorted(A); assert ten_ == sorted(B)
    x = torch.cat([A[k].float().flatten() for k in ten_]); y = torch.cat([B[k].float().flatten() for k in ten_]); d = (x - y).abs()
    ghi(v, "giống byte" if sha(a) == sha(b) else "khác byte", "·", x.numel(), "tham số · sai khác lớn nhất", f"{d.max():.3e}", "· tỉ lệ so với độ lớn", f"{d.norm() / y.norm():.3e}", "· tham số trùng hệt", f"{100 * (d == 0).float().mean():.2f}%")
(W / "SO_SANH_VOI_BAN_GOC.md").write_text("\n".join(L) + "\n", encoding="utf-8")
