#!/usr/bin/env python3
"""Ghép REPO CUỐI (03–04/11/2026, phần tích hợp của Kiệt): teamwork/repo_cuoi/
  nền   = gói sản phẩm fix.zip của Đăng (kiem_fix/goc, bản chạy GPU ổn định) – không sửa code sản phẩm ở bước này
  thêm  = B1 (code bàn giao gốc + bản đã sửa), kết quả mới (B1, ablation, đánh giá tổng hợp, số cả hệ, tốc độ V4),
          checkpoint ablation (best + nhật ký), notebook đã chạy có output, workbook 3 sheet.
Không chép: dữ liệu audio/văn bản lớn, văn bản PhoMT (giấy phép – chỉ giữ score.json), checkpoint từng epoch (ở task3/checkpoints).
Chạy lại được (ghi đè bản ghép cũ)."""
import shutil
from pathlib import Path

T3 = Path(__file__).resolve().parents[1]; TW = T3.parent
NEN, OUT = TW / "kiem_fix/goc", TW / "repo_cuoi"
EX = OUT / "experiments"
BO = shutil.ignore_patterns("__pycache__", ".pytest_cache", ".vscode", "demo.log", "*.pyc")


def cp(src, dst):
    src, dst = Path(src), Path(dst)
    if not src.exists():
        print("  (bỏ qua, chưa có)", src); return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, ignore=BO, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)


def cp_mt(v):  # bản dịch + điểm; PhoMT chỉ giữ score.json
    for d in (T3 / "runs/mt" / v).iterdir():
        if d.name == "phomt_test":
            cp(d / "score.json", EX / "runs/mt" / v / d.name / "score.json")
        else:
            cp(d, EX / "runs/mt" / v / d.name)


def main():
    OUT.mkdir(exist_ok=True)
    for x in OUT.iterdir():  # xoá nội dung cũ (không xoá chính thư mục – có thể đang được ứng dụng khác mở)
        shutil.rmtree(x) if x.is_dir() else x.unlink()
    shutil.copytree(NEN, OUT, ignore=BO, dirs_exist_ok=True)
    for x in ("danh_gia", "nghiem_thu", "CHAY_TREN_GPU.ipynb"):  # bằng chứng V4 03/11 nằm ở experiments/reports/he_thong; notebook chạy GPU sinh lại bên dưới
        y = OUT / x; shutil.rmtree(y) if y.is_dir() else y.unlink(missing_ok=True)
    # --- B1: code bàn giao gốc (giữ nguyên) + bản sửa dùng để chạy
    cp(TW / "kiem_dang_baseline/goc/DANG_BASELINE_HANDOFF", EX / "scripts/baseline2/ban_giao_goc")
    cp(T3 / "scripts/b1/b1_whisper_translate.py", EX / "scripts/baseline2/b1_whisper_translate.py")
    cp(T3 / "runs/b1/predictions_b1.jsonl", EX / "runs/b1/predictions_b1.jsonl")
    cp(T3 / "runs/b1/run_metadata_b1.json", EX / "runs/b1/run_metadata_b1.json")
    cp(T3 / "runs/mt/B1_whisper-small_translate", EX / "runs/mt/B1_whisper-small_translate")
    # --- ablation: dữ liệu aug, config, checkpoint best + nhật ký, bản dịch, bảng
    cp(T3 / "runs/mt_data/fleurs_train_clean_asrstyle.jsonl", EX / "runs/mt_data/fleurs_train_clean_asrstyle.jsonl")
    for k in ("A_r8", "A_r32", "A_aug"):
        cp(T3 / f"configs/mt/{k}.json", EX / f"configs/mt/{k}.json")
        for f in ("config.json", "epochs.json", "train_log.jsonl", "curves.png"):
            cp(T3 / f"checkpoints/{k}/{f}", EX / f"checkpoints/{k}/{f}")
        cp(T3 / f"checkpoints/{k}/best", OUT / f"checkpoints/{k}/best")       # adapter chọn – dùng được như V3/V4
        if (T3 / "runs/mt" / k).exists():
            cp_mt(k)
    for d in ("ablation", "danh_gia", "he_thong", "he_thong_V2", "toc_do/lap_V4", "toc_do/lap_V2"):
        cp(T3 / "reports" / d, EX / "reports" / d)
    for f in (T3 / "reports/mt").glob("bootstrap_*"):
        cp(f, EX / "reports/mt" / f.name)
    cp(T3 / "reports/tong_hop/ban_cuoi.txt", EX / "reports/tong_hop/ban_cuoi.txt")
    cp(T3 / "reports/tong_hop/ban_cuoi_quy_tac_cu.txt", EX / "reports/tong_hop/ban_cuoi_quy_tac_cu.txt")
    # --- đo độ bền khối nghe (audio nhiễu sinh lại được nên không đóng gói wav)
    cp(T3 / "reports/robust", EX / "reports/robust")
    for f in (T3 / "runs/robust").glob("robust_pho_*"):
        cp(f, EX / "runs/robust" / f.name)
    cp(T3 / "nghe_kiem", EX / "nghe_kiem")
    for f in ("asr/tao_audio_robust.py", "hang_doi_robust.sh", "tao_notebook_robust.py"):
        cp(T3 / "scripts" / f, EX / "scripts" / f)
    # --- script sinh tài liệu (chép để đối chiếu) và src/train.py theo cấu trúc đề bài
    for f in ("tao_bao_cao.py", "tao_slide.py", "tao_ban_giao.py", "tao_checklist.py", "dien_tai_lieu_bao.py", "tao_notebook_toan_bo.py", "o_thiet_lap_nb.py", "dong_zip_nop.py"):
        cp(T3 / "scripts" / f, EX / "scripts/tai_lieu" / f)
    cp(TW / "tai_lieu_nhom_V2/_script", EX / "scripts/tai_lieu/nhom")
    cp(TW / "kien_truc/ve_kien_truc_du_an.py", EX / "scripts/tai_lieu/ve_kien_truc_du_an.py")
    cp(TW / "kien_truc/ra_soat_cuoi.py", EX / "scripts/tai_lieu/ra_soat_cuoi.py")
    (OUT / "src/train.py").write_text('''"""Huấn luyện LoRA cho khối dịch. Code thật ở experiments/scripts/mt/train_lora.py, lệnh đầy đủ ở experiments/chay_lai.sh."""

import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "experiments/scripts/mt/train_lora.py"), run_name="__main__")
''', encoding="utf-8")
    # --- 3 seed: adapter tốt nhất + nhật ký + bản dịch; V1 seed 42; đủ log
    MS = T3 / "runs/ba_seed/modal"
    for p in sorted((MS / "checkpoints").iterdir()):
        cp(p / "best", OUT / f"checkpoints/{p.name}/best")
        for f in ("config.json", "epochs.json", "train_log.jsonl", "curves.png"):
            cp(p / f, EX / f"checkpoints/{p.name}/{f}")
    cp(MS / "runs/mt", EX / "runs/ba_seed/mt")
    cp(T3 / "reports/ba_seed", EX / "reports/ba_seed")
    cp(T3 / "reports/nb07_chay_05-11", EX / "reports/nb07_chay_05-11")
    cp(T3 / "scripts/chay_nb07.py", EX / "scripts/chay_nb07.py")
    cp(T3 / "checkpoints/V1/best", OUT / "checkpoints/V1/best")
    for f in ("modal_3seed.py", "tong_hop_3seed.py", "tao_notebook_3seed.py"):
        cp(T3 / "scripts" / f, EX / "scripts" / f)
    for f in sorted((T3 / "logs").iterdir()):
        if f.is_file() and f.suffix in (".log", ".csv"):
            cp(f, EX / "logs" / f.name)
    y = OUT / "notebooks/CHAY_TREN_GPU.ipynb"; y.unlink(missing_ok=True)
    # --- chạy lại toàn bộ thực nghiệm seed 42 trong notebook
    W = T3 / "chay_lai_notebook"
    for f in ("so_sanh_voi_ban_goc.py", "SO_SANH_VOI_BAN_GOC.md"):
        cp(W / f, EX / "chay_lai_notebook" / f)
    for f in sorted((W / "logs").iterdir()):
        if f.is_file() and f.suffix == ".log":
            cp(f, EX / "chay_lai_notebook/logs" / f.name)
    cp(T3 / "scripts/tao_notebook_chay_lai.py", EX / "scripts/tao_notebook_chay_lai.py")
    cp(T3 / "scripts/tao_notebook_3seed.py", EX / "scripts/tao_notebook_3seed.py")
    cp(T3 / "scripts/asr/chay_baseline_asr.sh", EX / "scripts/asr/chay_baseline_asr.sh")
    cp(T3 / "scripts/dong_goi_gui_bao_uyen.py", EX / "scripts/tai_lieu/dong_goi_gui_bao_uyen.py")
    # --- script mới của giai đoạn 2
    for f in ("mt/make_aug_data.py", "he_thong_bootstrap.py", "tao_notebook_eda_loi.py", "tao_notebook_gd2.py", "chay_notebook.py",
              "dong_goi_repo_cuoi.py", "hang_doi_do_V4.sh", "hang_doi_do_V2.sh", "hang_doi_he_thong_V2.sh", "ket_luan.py"):
        cp(T3 / "scripts" / f, EX / "scripts" / f)
    for f in ("b1_whisper_translate.log", "hang_doi_do_V4.log", "hang_doi_do_V2.log", "hang_doi_he_thong_V2.log", "chay_notebook_gd2.log", "chay_notebook_gd2_lan2.log", "train_A_r8.log", "train_A_r32.log", "train_A_aug.log",
              "eval_A_r8.log", "eval_A_r32.log", "eval_A_aug.log"):
        cp(T3 / "logs" / f, EX / "logs" / f)
    # --- notebook đã chạy (có output)
    for f in ("eda.ipynb", "phan_tich_loi.ipynb", "02_baseline_B1_whisper_translate.ipynb", "03_ablation_va_chon_ban_cuoi.ipynb", "01_chay_lai_thuc_nghiem.ipynb", "06_danh_gia_tong_hop.ipynb", "05_do_ben_khoi_nghe.ipynb", "04_kiem_tra_3_seed.ipynb"):
        cp(T3 / "notebooks" / f, OUT / "notebooks" / f)
    cp(T3 / "reports/danh_gia/bang_ket_qua.xlsx", OUT / "reports/bang_ket_qua.xlsx")
    tich_hop_v2()
    readme_ket_qua()
    sua_gioi_han()
    ghi_chu_repo()
    for d in (T3 / "runs/asr").glob("kiet_t2_*"):  # kết quả chấm: notebook và tài liệu đọc từ đây
        for f in ("summary.json", "per_utterance.csv"):
            cp(d / "score" / f, EX / "runs/asr" / d.name / "score" / f)
    r = OUT / "README.md"; t = r.read_text(encoding="utf-8")
    t = t.replace("# bản cuối theo quy tắc chọn trên dev", "# bản để so sánh, bản cuối là V2")
    t = t.replace("chạy bốn job: lint bằng ruff, test trên Python 3.10 và 3.11,", "chạy năm job: lint bằng ruff, test trên Python 3.10 và 3.11, cài sạch `requirements.txt`,")
    r.write_text(t, encoding="utf-8")
    r = EX / "chay_lai.sh"; t = r.read_text(encoding="utf-8")
    if "--with_test_audio" not in t:
        t = t.replace("--revision $FLEURS_REV ${LIM}", "--revision $FLEURS_REV --with_test_audio ${LIM}")
    assert "--with_test_audio" in t
    r.write_text(t, encoding="utf-8", newline="\n")
    r = EX / "README.md"; t = r.read_text(encoding="utf-8")
    t = t.replace("| Adapter | V3, V4: `../checkpoints/V*/best` (có SHA256). V1, V2: trong gói `task3.zip` của Kiệt |", "| Adapter | V1–V4 và ablation, đủ 3 seed: `../checkpoints/*/best` (có SHA256) |")
    r.write_text(t, encoding="utf-8")
    if "## Chạy lại 3 seed" not in t:
        t = t.rstrip() + """

## Chạy lại 3 seed và đo độ bền

Seed 42 chạy theo `chay_lai.sh`. Seed 1 và 2 của V1–V4, ablation chạy bằng `scripts/modal_3seed.py` (cần `pip install modal` và tài khoản Modal; đưa file trong `runs/mt_data/` lên Volume `dpl302m-3seed`, riêng `phomt_train_mix.jsonl` phải tự tạo lại vì không phân phối). Train trên RTX PRO 6000 với torch 2.7.1, dịch và chấm trên T4 với torch 2.0.1. Tổng hợp: `scripts/tong_hop_3seed.py`, kết quả ở `reports/ba_seed/` và `runs/ba_seed/mt/`.

Đo độ bền khối nghe: `bash scripts/hang_doi_robust.sh` (cần GPU và `data/`), kết quả ở `reports/robust/`, `runs/robust/`.

Toàn bộ log của các lần chạy thật ở `logs/`.
"""
        r.write_text(t, encoding="utf-8")
    import subprocess  # Ruff (cùng phiên bản CI 0.5.7) – sửa lỗi tự động + format, để job Lint của CI đạt
    ruff = TW / "kiem_repo_asr/.venv/Scripts/ruff.exe"
    for lenh in (["check", "--fix", "--no-cache"], ["format", "--no-cache"], ["check", "--no-cache"], ["format", "--check", "--no-cache"]):
        r = subprocess.run([str(ruff), *lenh, "src", "api", "app", "tests"], cwd=OUT, capture_output=True, text=True)
        print("  ruff", " ".join(lenh[:2]), "→", (r.stdout or r.stderr).strip().splitlines()[-1])
    n = sum(1 for p in OUT.rglob("*") if p.is_file()); mb = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file()) / 2**20
    print(f"{OUT}: {n} file, {mb:.0f} MB")


def sua(p, cap):
    """Thay chuỗi trong file của repo cuối; mỗi cặp phải khớp đúng 1 lần (không khớp thì dừng để khỏi sửa sai)."""
    p = OUT / p; s = p.read_text(encoding="utf-8")
    for a, b in cap:
        assert s.count(a) == 1, f"{p}: không khớp đúng 1 lần: {a[:60]}"
        s = s.replace(a, b)
    p.write_text(s, encoding="utf-8")


def tich_hop_v2():
    """Quy tắc DEV (experiments/reports/ablation/QUY_TAC_CHON.md, chốt trước ablation) chọn V2 → V2 là mặc định."""
    import hashlib, json
    J = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
    d = OUT / "checkpoints/V2/best"
    for f in ("adapter_config.json", "adapter_model.safetensors", "chon.json"):
        cp(T3 / "checkpoints/V2/best" / f, d / f)
    cp(T3 / "checkpoints/V2/best/dev_translate/score.json", d / "dev_translate/score.json")
    cp(T3 / "runs/mt/V2/fleurs_dev_clean/score.json", d / "dev_clean/score.json")
    for k in ("A_r8", "A_r32", "A_aug"):
        if (T3 / "runs/mt" / k / "fleurs_dev_clean/score.json").exists():
            cp(T3 / "runs/mt" / k / "fleurs_dev_clean/score.json", OUT / f"checkpoints/{k}/best/dev_clean/score.json")
    ds = sorted((OUT / "checkpoints").glob("*/best/adapter_model.safetensors"))
    (OUT / "checkpoints/SHA256SUMS").write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(OUT / 'checkpoints').as_posix()}\n" for p in ds),
                                                encoding="utf-8", newline="\n")
    c = J(T3 / "reports/ablation/chon_ban_cuoi.json"); dv = {r["bản"]: r for r in c["bang_dev"]}
    v = c["ban_chon"]; assert v == "V2", v
    (OUT / "configs/ban_chot.json").write_text(json.dumps({
        "ban_chot": v, "adapter": f"checkpoints/{v}/best", "nguoi_quyet": "nhóm (04/11/2026), áp quy tắc DEV chốt trước khi chạy ablation",
        "quy_tac": "experiments/reports/ablation/QUY_TAC_CHON.md: M = BLEU dev cascade cao nhất; nhóm hoà = các bản ≥ M − 0,5; trong nhóm hoà chọn BLEU dev dịch sạch cao nhất",
        "ap_dung": {"M": c["M_dev_cascade"], "nhom_hoa": c["nhom_hoa"], "dev_cascade": {k: r["dev cascade"] for k, r in dv.items()},
                    "dev_sach": {k: r["dev sạch"] for k, r in dv.items()}},
        "ket_qua": f"{v}: dev sạch {dv[v]['dev sạch']} cao nhất trong nhóm hoà; ablation A_r8/A_r32/A_aug đều < M − 0,5 trên dev cascade",
        "lich_su": "03/11 nhóm tạm chốt V4 (lý do dev sạch so với V3); 04/11 áp quy tắc đầy đủ cho V1–V4 + ablation → V2",
        "khong_dung_diem_test_de_chon": True, "nguon_so": "experiments/reports/ablation/chon_ban_cuoi.json; checkpoints/<bản>/best/dev_*/score.json"},
        ensure_ascii=False, indent=2), encoding="utf-8")
    sua("src/pipeline.py", [
        ("          -> VinAI Translate + adapter LoRA V4 -> cau tieng Anh", "          -> VinAI Translate + adapter LoRA V2 -> cau tieng Anh"),
        ("# Nhom chot V4 (03/11/2026), ly do va nguon so o configs/ban_chot.json.\n# Quy tac cu (BLEU dev cascade cao nhat) chon V3: 26,71 so voi V4 26,33. Doi sang V4 vi\n"
         "# tren dev sach V4 giam it hon so voi B0 (36,75 so voi V3 36,37; B0 37,57), con dev\n# cascade chi chenh 0,38. Khong dung diem test de chon.\n"
         'ADAPTER_MAC_DINH = GOC / "checkpoints" / "V4" / "best"',
         "# Ban chot V2 theo quy tac DEV chot truoc ablation (configs/ban_chot.json):\n"
         "# V1-V4 hoa tren dev cascade (cach V3 26,71 <= 0,5) -> chon dev sach cao nhat = V2 (36,93).\n"
         "# Ablation rank 8/32, augmentation deu thap hon tren dev. Khong dung diem test de chon.\n"
         'ADAPTER_MAC_DINH = GOC / "checkpoints" / "V2" / "best"'),
        ("-> checkpoints/V4/best (ban chot).", "-> checkpoints/V2/best (ban chot).")])
    sua(".env.example", [("De trong thi mac dinh V4 (ban nhom chot, xem configs/ban_chot.json);\n# checkpoints/V3/best de so sanh;",
                          "De trong thi mac dinh V2 (ban chot theo quy tac DEV, xem configs/ban_chot.json);\n# checkpoints/V3/best, V4/best de so sanh;"),
                         ("ADAPTER_PATH=checkpoints/V4/best", "ADAPTER_PATH=checkpoints/V2/best")])
    sua("docker/docker-compose.yml", [("${ADAPTER_PATH:-/models/checkpoints/V4/best}   # V3: /models/checkpoints/V3/best, B0: none",
                                       "${ADAPTER_PATH:-/models/checkpoints/V2/best}   # V3/V4: /models/checkpoints/V3|V4/best, B0: none")])
    sua("src/inference.py", [("--adapter checkpoints/V4/best --json", "--adapter checkpoints/V2/best --json"),
                             ("(mặc định checkpoints/V4/best;", "(mặc định checkpoints/V2/best;")])
    sua("src/models/__init__.py", [("Adapter da train: checkpoints/V3, V4.", "Adapter da train: checkpoints/V2 (ban chot), V3, V4, ablation A_r8/A_r32/A_aug.")])
    sua("tests/test_adapter.py", [
        ('def test_co_san_adapter_v3_v4():\n    for v in ("V3", "V4"):', 'def test_co_san_adapter_v2_v3_v4():\n    for v in ("V2", "V3", "V4"):'),
        ("def test_mac_dinh_la_v4(monkeypatch):", "def test_mac_dinh_la_v2(monkeypatch):"),
        ('def test_ly_do_chot_v4_dung_so_dev():\n    """So trong ly do chot phai khop file score.json tren dev."""',
         'def test_ly_do_chot_v2_dung_so_dev():\n    """So trong ly do chot (quy tac DEV) phai khop file score.json tren dev."""'),
        ('    assert bleu("V4/best/dev_clean/score.json") > bleu("V3/best/dev_clean/score.json")',
         '    assert bleu("V2/best/dev_translate/score.json") == 26.45\n'
         '    assert 26.71 - bleu("V2/best/dev_translate/score.json") <= 0.5          # V2 trong nhom hoa\n'
         '    assert bleu("V2/best/dev_clean/score.json") == 36.93\n'
         '    for v in ("V3", "V4"):\n'
         '        assert bleu("V2/best/dev_clean/score.json") > bleu(f"{v}/best/dev_clean/score.json")\n'
         '    chot = json.loads((pl.GOC / "configs" / "ban_chot.json").read_text(encoding="utf-8"))\n'
         '    assert chot["ban_chot"] == "V2" and pl.ADAPTER_MAC_DINH.parent.name == "V2"')])
    sua("tests/nghiem_thu_that.py", [('@muc("T08/F06", "V4 (mac dinh), V3, B0 nap dung checkpoint")', '@muc("T08/F06", "V2 (mac dinh), V4, B0 nap dung checkpoint")'),
                                     ('for ten, gt in (("V4 mac dinh", None), ("V3", "checkpoints/V3/best"), ("B0", "none")):',
                                      'for ten, gt in (("V2 mac dinh", None), ("V4", "checkpoints/V4/best"), ("B0", "none")):'),
                                     ('mong = {"V4 mac dinh": "V4/best", "V3": "V3/best", "B0": "khong (B0)"}[ten]',
                                      'mong = {"V2 mac dinh": "V2/best", "V4": "V4/best", "B0": "khong (B0)"}[ten]')])
    sua("tests/danh_gia_proposed.py", [("+ VinAI Translate + LoRA V4,", "+ VinAI Translate + LoRA (mac dinh V2, doi bang ADAPTER_PATH),")])


def readme_ket_qua():
    """Thay mục '## Kết quả chính' của README bằng bảng sinh từ file kết quả (không gõ tay số)."""
    import json, statistics
    J = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
    mt = lambda v, s: J(T3 / f"runs/mt/{v}/{s}/score.json")
    vn = lambda x, d=2: f"{float(x):.{d}f}".replace(".", ",")
    rs = {r.split(",")[0]: r.split(",") for r in (T3 / "reports/asr/results_task2.csv").read_text(encoding="utf-8-sig").splitlines()[1:]}
    wer = lambda k: rs[k][6]
    bs = lambda f: J(T3 / "reports/mt" / f)
    lap = lambda v: [J(p) for p in sorted((T3 / "reports/toc_do/lap_V2").glob(f"toc_do_{v}_lan*.json"))]
    td = lambda v: (statistics.median(x["RTF_total"] for x in lap(v)), statistics.median(x["latency_p95_s"] for x in lap(v)))
    ch = J(T3 / "reports/ablation/chon_ban_cuoi.json"); dv = {r["bản"]: r for r in ch["bang_dev"]}
    b1 = mt("B1_whisper-small_translate", "fleurs_test_audio")
    ht = J(T3 / "reports/he_thong_V2/ket_qua.json"); hb = J(T3 / "reports/he_thong_V2/bootstrap_cu_vs_moi.json")
    b02, b0v2w = bs("bootstrap_B0_V2_cascade_test.json"), bs("bootstrap_B0_V2_cascade_wsp_test.json")
    bb1 = bs("bootstrap_B0_fleurs_test_asr_pho_vs_B1.json")
    L = ["## Kết quả chính", "",
         "*[Cập nhật 04/11/2026 – sinh từ file kết quả bằng `experiments/scripts/dong_goi_repo_cuoi.py`; mỗi số có nguồn ở cột cuối.]*", "",
         "**Hệ cuối** = PhoWhisper-small pretrained (khối nghe, không fine-tune) → VinAI Translate vi2en + **adapter LoRA V2** (khối dịch) + tiền/hậu xử lý "
         "(chia đoạn tại chỗ ngắt nghỉ, bỏ lặp ở chỗ nối, đổi số đọc bằng chữ). **V2 được chọn theo quy tắc DEV chốt trước khi chạy ablation** "
         f"(`experiments/reports/ablation/QUY_TAC_CHON.md`): bản có BLEU dev cascade cao nhất là {max(dv, key=lambda v: dv[v]['dev cascade'])} ({vn(ch['M_dev_cascade'])}); "
         f"các bản cách ≤ 0,5 coi là hoà ({', '.join(ch['nhom_hoa'])}); trong nhóm hoà chọn BLEU dev dịch sạch cao nhất → **{ch['ban_chon']}** ({vn(dv[ch['ban_chon']]['dev sạch'])}). "
         "Quy tắc này chốt sau khi đã có số test của V1–V4 (quy tắc đầu, lấy dev cascade cao nhất, cho ra V3), nên không phải lựa chọn mù với test; chỉ ba bản ablation chạy sau khi có quy tắc.", "",
         "**Kiểm tra 3 seed** (seed 42, 1, 2; `experiments/reports/ba_seed/`, `notebooks/04_kiem_tra_3_seed.ipynb`): V2 test cascade 27,34 ± 0,12, test sạch 37,80 ± 0,26, hơn B0 +4,65 ± 0,12. Áp quy tắc trên trung bình dev vẫn ra V2. Seed 1 và 2 train trên Modal bằng torch 2.7.1, dịch và chấm bằng torch 2.0.1 như seed 42. Các bảng dưới là số seed 42, đúng adapter chạy trong sản phẩm.", "",
         "### Baseline (FLEURS vi_vn test, 857 bản thu)", "",
         "| Hệ | WER khối nghe | BLEU | chrF++ | Nguồn |", "|---|---|---|---|---|",
         f"| B0 cascade: PhoWhisper-small → VinAI gốc | {vn(wer('kiet_t2_phowhisper-small_fleurs_test'))}% | {vn(mt('B0', 'fleurs_test_asr_pho')['BLEU'])} | {vn(mt('B0', 'fleurs_test_asr_pho')['chrF++'])} | `experiments/runs/mt/B0/fleurs_test_asr_pho/score.json` |",
         f"| Cascade khối nghe thứ hai: Whisper-small → VinAI gốc | {vn(wer('kiet_t2_whisper-small_fleurs_test'))}% | {vn(mt('B0', 'fleurs_test_asr_wsp')['BLEU'])} | {vn(mt('B0', 'fleurs_test_asr_wsp')['chrF++'])} | `experiments/runs/mt/B0/fleurs_test_asr_wsp/score.json` |",
         f"| B1 end-to-end: Whisper-small `task=translate` | không có transcript Việt | {vn(b1['BLEU'])} | {vn(b1['chrF++'])} | `experiments/runs/mt/B1_whisper-small_translate/fleurs_test_audio/score.json` |", "",
         f"B1 kém B0 {vn(-bb1['delta'])} BLEU (KTC 95% [{vn(bb1['ci95'][0])}; {vn(bb1['ci95'][1])}]): Whisper-small dịch tiếng Việt yếu, nhiều câu lặp vòng khi giải mã "
         "(`notebooks/02_baseline_B1_whisper_translate.ipynb`, `notebooks/phan_tich_loi.ipynb` mục 12). Paper đối chiếu cùng dataset: PhoWhisper VIVOS 6,33 (nhóm "
         f"{vn(wer('kiet_t2_phowhisper-small_vivos_test'))}), Whisper-small FLEURS 21,2 (nhóm {vn(wer('kiet_t2_whisper-small_fleurs_test'))}), VinAI PhoMT 40,42 (nhóm {vn(mt('B0', 'phomt_test')['BLEU'])}).", "",
         "### Proposed: LoRA khối dịch – phiên bản và ablation (BLEU)", "",
         "| Bản | Thay đổi | Dev cascade | Dev sạch | Test cascade | Test sạch | PhoMT |", "|---|---|---|---|---|---|---|"]
    doi = {"B0": "VinAI gốc", "V1": "+ LoRA trên lời ASR", "V2": "V1 + PhoMT 1:1", "V3": "V2 + cân bằng câu/độ dài", "V4": "V3, lr 5e-5",
           "A_r8": "V2, rank 8", "A_r32": "V2, rank 32", "A_aug": "V2 + augmentation transcript sạch"}
    for v, t in doi.items():
        L.append(f"| {v}{' ★' if v == ch['ban_chon'] else ''} | {t} | {vn(mt(v, 'fleurs_dev_asr_pho')['BLEU'])} | {vn(mt(v, 'fleurs_dev_clean')['BLEU'])} | "
                 f"{vn(mt(v, 'fleurs_test_asr_pho')['BLEU'])} | {vn(mt(v, 'fleurs_test_clean')['BLEU'])} | {vn(mt(v, 'phomt_test')['BLEU'])} |")
    L += ["", f"V2 so với B0 trên test cascade: +{vn(b02['delta'])} (KTC 95% [{vn(b02['ci95'][0])}; {vn(b02['ci95'][1])}]); với khối nghe Whisper-small: "
          f"{vn(mt('B0', 'fleurs_test_asr_wsp')['BLEU'])} → {vn(mt('V2', 'fleurs_test_asr_wsp')['BLEU'])} (+{vn(b0v2w['delta'])} [{vn(b0v2w['ci95'][0])}; {vn(b0v2w['ci95'][1])}]). "
          "Giữa V1–V4 và ablation rank, chênh lệch test nằm trong khoảng tin cậy. Nguồn: `experiments/reports/ablation/bang_ablation.csv`, `experiments/reports/mt/bootstrap_*.json`.", "",
          "### Cả hệ sản phẩm và tính khả thi", "",
          "| Chỉ số | Giá trị | Nguồn |", "|---|---|---|"]
    p, o = ht["proposed"]["tat_ca"], ht["truoc_0411"]["tat_ca"]
    L += [f"| Cả hệ (V2 + tiền/hậu xử lý), 857 bản | WER {vn(p['WER_asr'])}% · BLEU {vn(p['BLEU'])} · chrF++ {vn(p['chrF++'])} | `experiments/reports/he_thong_V2/ket_qua.json` |",
          f"| So với cách xử lý cũ (cắt giữa, không đổi số) | BLEU {vn(o['BLEU'])} → {vn(p['BLEU'])}, Δ {vn(hb['delta'])} [{vn(hb['ci95'][0])}; {vn(hb['ci95'][1])}] | `experiments/reports/he_thong_V2/bootstrap_cu_vs_moi.json` |"]
    for v in ("B0", "V2"):
        r, p95 = td(v)
        L.append(f"| Tốc độ {v} (100 bản, 3 lần xen kẽ, trung vị) | RTF {vn(r, 3)} · p95 {vn(p95)} s | `experiments/reports/toc_do/lap_V2/` |")
    L += ["| VRAM đỉnh khi suy luận · kích thước | 1,57 GiB · 2,69 GB (adapter 34,7 MB) | `experiments/reports/toc_do/lap_V2/` |", "",
          "Notebook có output: `notebooks/eda.ipynb`, `phan_tich_loi.ipynb`, `02_baseline_B1_whisper_translate.ipynb`, `03_ablation_va_chon_ban_cuoi.ipynb`, `06_danh_gia_tong_hop.ipynb`, `05_do_ben_khoi_nghe.ipynb`, `04_kiem_tra_3_seed.ipynb`. Toàn bộ code kèm output và phần checkpoint: `notebooks/00_toan_bo_code.ipynb`. "
          "Workbook 6 sheet: `reports/bang_ket_qua.xlsx`. Bảng PASS / FAIL / NOT RUN: `KIEM_THU_CUOI.md`.", ""]
    rp = OUT / "README.md"; s = rp.read_text(encoding="utf-8")
    i, j = s.index("## Kết quả chính"), s.index("## Cài đặt")
    rp.write_text(s[:i] + "\n".join(L) + "\n" + s[j:], encoding="utf-8")


def ghi_chu_repo():
    """CHANGELOG, README notebooks, hình kiến trúc, notebook chạy GPU cho repo cuối."""
    import json
    cp(TW / "kien_truc/kien_truc_toan_bo_du_an.png", OUT / "reports/kien_truc_toan_bo_du_an.png")
    cp(T3 / "reports/KIEM_THU_CUOI.md", OUT / "KIEM_THU_CUOI.md")
    (OUT / "notebooks/README.md").write_text("""# Notebook (đã chạy, có output)

| Notebook | Nội dung |
|---|---|
| `eda.ipynb` | Thống kê mô tả dữ liệu: split, giới tính, số bản thu mỗi câu, độ dài audio/câu, miền, cân bằng |
| `phan_tich_loi.ipynb` | Phân tích lỗi: nhầm dấu thanh, WER theo nhóm, BLEU theo nhóm/miền, ca lỗi có ID, lan truyền ASR → MT, B1, ablation |
| `02_baseline_B1_whisper_translate.ipynb` | Kiểm gói baseline, chạy B1 Whisper Translate (857 bản), chấm, bootstrap với B0 |
| `03_ablation_va_chon_ban_cuoi.ipynb` | Kiểm toán V1–V4, ablation một yếu tố (rank 8/32, augmentation), áp quy tắc chọn trên DEV |
| `06_danh_gia_tong_hop.ipynb` | Prediction theo schema chung, bảng so sánh, workbook 3 sheet gốc; `04_kiem_tra_3_seed.ipynb` thêm 2 sheet, tổng 6 sheet |
| `05_do_ben_khoi_nghe.ipynb` | Độ bền PhoWhisper-small khi thêm nhiễu, đổi tốc độ, đổi âm lượng (chỉ đo, không fine-tune) |
| `04_kiem_tra_3_seed.ipynb` | Kiểm tra 3 seed cho V1–V4 và ablation, đối chứng môi trường |
| `00_toan_bo_code.ipynb` | Toàn bộ code của project, log và output thật, phần checkpoint, chạy thử model thật |
| `01_chay_lai_thuc_nghiem.ipynb` | Chạy lại thật seed 42: dữ liệu, 4 baseline ASR, B0, train V1–V4 đủ 5 epoch, đánh giá, tốc độ. So sánh với kết quả gốc ở `experiments/chay_lai_notebook/SO_SANH_VOI_BAN_GOC.md` |
| `07_chay_san_pham_tren_gpu.ipynb` | Chạy thật sản phẩm V2 trên GPU: kiểm adapter, test, đánh giá cũ/mới 857 bản, nghiệm thu, demo |

`eda` và `phan_tich_loi` chỉ đọc `experiments/`, chạy được không cần GPU. 03–05 gọi script thực nghiệm và cần thư mục làm việc có `data/` (không đẩy lên Git, xem `data/README.md`);
output đã lưu trong file, mở ra đọc được ngay. Phần đã có checkpoint/score sẽ tự bỏ qua khi chạy lại.
""", encoding="utf-8")
    nbp = NEN / "CHAY_TREN_GPU.ipynb"
    if nbp.exists():
        s = nbp.read_text(encoding="utf-8").replace("gói `fix.zip` của Đăng", "repo cuối").replace("kiem_fix\\\\goc", "repo_cuoi").replace("(model thật, V4)", "(model thật, V2)")
        cp(T3 / "notebooks/07_chay_san_pham_tren_gpu.ipynb", OUT / "notebooks/07_chay_san_pham_tren_gpu.ipynb")  # bản đã chạy, có output
    sua("README.md", [
        ("**Adapter LoRA có sẵn trong repo** (`checkpoints/V3/best`, `checkpoints/V4/best`, mỗi bản 34,7 MB, r=16, α=32). App, API và CLI **mặc định dùng V4**",
         "**Adapter LoRA có sẵn trong repo** (`checkpoints/V2/best` là bản chốt; `V3`, `V4`, ablation `A_r8`, `A_r32`, `A_aug` để so sánh; r=16, α=32 trừ bản rank). App, API và CLI **mặc định dùng V2**"),
        ('$env:ADAPTER_PATH="checkpoints/V4/best"; python app/gradio_app.py', '$env:ADAPTER_PATH="checkpoints/V2/best"; python app/gradio_app.py'),
        ("python src/inference.py --audio a.wav --adapter checkpoints/V4/best --json ra.json", "python src/inference.py --audio a.wav --adapter checkpoints/V2/best --json ra.json"),
        ("| T08/F06 | V4 (mặc định), V3, B0 nạp đúng adapter", "| T08/F06 | V2 (mặc định), V4, B0 nạp đúng adapter"),
        ("mount sẵn, mặc định dùng V4)", "mount sẵn, mặc định dùng V2)"),
        ("adapter LoRA V3, V4 (34,7 MB mỗi bản) + SHA256SUMS", "adapter LoRA V2 (chốt), V3, V4, ablation A_* + SHA256SUMS"),
        ("Siêu tham số của bản cuối: LoRA r=16", "Siêu tham số của bản cuối V2: LoRA r=16"),
        ("lr 2e-4 (V4 dùng 5e-5)", "lr 2e-4"),
        ("train LoRA V1–V4, chọn checkpoint", "train LoRA V1–V4 + ablation, B1, chọn checkpoint")])
    c = OUT / "CHANGELOG.md"; s = c.read_text(encoding="utf-8")
    s = s.replace("## 04/11/2026 — sửa theo demo", "## 03/11/2026 — sửa theo demo", 1)
    moi = """# Thay đổi

## 04/11/2026 — tích hợp cuối (Kiệt)

| # | Thay đổi | Ở đâu |
|---|---|---|
| 35 | Chốt quy tắc chọn bản trên DEV trước khi chạy ablation; áp cho V1–V4 + ablation → **V2** là bản cuối, mặc định của app/API/CLI/Docker | `configs/ban_chot.json`, `src/pipeline.py`, `experiments/reports/ablation/` |
| 36 | B1 Whisper Translate end-to-end: code bàn giao gốc (giữ nguyên) + bản sửa (không cắt audio > 30 s, ghim revision, seed, suppress tokens, utf-8, schema chung), chạy đủ 857 bản | `experiments/scripts/baseline2/`, `experiments/runs/b1/` |
| 37 | Ablation một yếu tố so với V2: rank 8, rank 32, augmentation; có checkpoint, log, bảng | `checkpoints/A_*`, `experiments/checkpoints/A_*`, `notebooks/03_ablation_va_chon_ban_cuoi.ipynb` |
| 38 | Đánh giá chung, prediction theo schema, workbook 3 sheet | `notebooks/06_danh_gia_tong_hop.ipynb`, `reports/bang_ket_qua.xlsx` |
| 39 | Đo lại cả hệ, tốc độ và nghiệm thu với V2 | `experiments/reports/he_thong_V2/`, `experiments/reports/toc_do/lap_V2/` |
| 40 | Ruff check + format toàn bộ `src api app tests`; README, giới hạn trong app, mốc F09 theo số V2 | README, `app/gradio_app.py`, `tests/nghiem_thu_that.py` |
| 41 | Kiểm tra 3 seed V1–V4 và ablation, đo độ bền khối nghe, notebook toàn bộ code, `src/train.py`, thêm adapter V1 và các seed | `experiments/reports/ba_seed/`, `experiments/reports/robust/`, `notebooks/00_toan_bo_code.ipynb` |
"""
    i = s.index("\n") + 1
    s = moi + s[i:]
    s = s.replace("Số đo với model thật sau khi sửa 1–3 (trước khi sửa 4–5): toàn bộ 857 bản FLEURS test, adapter V4, WER 12,27%, BLEU 27,63. Cần chạy lại một lần sau khi sửa 4–5.",
                  "Số đo 01/11 sau khi sửa 1–3: WER 12,27%, BLEU 27,63 (V4). Đã đo lại sau các sửa đổi: xem `experiments/reports/he_thong_V2/`.")
    s = s.replace("Chưa làm được trong máy sửa (không có GPU, không có mạng để cài ruff/pytest): chạy model thật, đo lại WER/BLEU sau thay đổi, thử micro thật, `pip install` sạch, `ruff`. Các bước này đã có lệnh trong README.",
                  "Máy sửa khi đó không có GPU; các bước đo lại đã làm ở mục 04/11 (trừ micro thật, xem `KIEM_THU_CUOI.md`).")
    c.write_text(s, encoding="utf-8")


def sua_gioi_han():
    """Câu 'giới hạn đã biết' (app + README) và mốc hồi quy F09 dùng số của bản cuối (V2), tính từ file."""
    import csv as _csv, json, re
    J = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
    vn = lambda x, d=2: f"{float(x):.{d}f}".replace(".", ",")
    v = J(T3 / "reports/ablation/chon_ban_cuoi.json")["ban_chon"]
    dm = {(r["khoi"], r["he"], r["tap"], r["mien"].split(" (")[0]): r for r in _csv.DictReader(open(T3 / "reports/domain/ket_qua_theo_mien.csv", encoding="utf-8-sig"))}
    bm = {m: float(dm[("MT", v, "fleurs_test_asr_pho", m)]["BLEU"]) for m in ("Giáo dục", "Tin tức", "Du lịch")}
    wm = {m: dm[("ASR", "phowhisper-small_fleurs_test", "FLEURS test", m)]["WER"] for m in bm}
    tot, xau = max(bm, key=bm.get), min(bm, key=bm.get)
    hy = [json.loads(l) for l in open(T3 / f"runs/mt/{v}/fleurs_dev_asr_pho/hyp.jsonl", encoding="utf-8")]
    ngan = sum(len(r["hyp"].split()) < 0.7 * len(r["ref"].split()) for r in hy)
    ht = J(T3 / "reports/he_thong_V2/ket_qua.json"); p, d = ht["proposed"]["tat_ca"], ht["proposed"]["dai"]
    mien = (f"(BLEU {vn(bm[tot])}, WER khối nghe {vn(wm[tot])}%) và kém nhất ở miền {xau} (BLEU {vn(bm[xau])}, WER {vn(wm[xau])}%)")
    cau_ngan = f"{ngan} trên {len(hy)} câu dev có bản dịch ngắn hơn 0,7 lần tham chiếu ({v})."
    he = f"WER {vn(p['WER_asr'])}%, BLEU {vn(p['BLEU'])}, chrF++ {vn(p['chrF++'])} (adapter {v}, đo 04/11/2026, `experiments/reports/he_thong_V2/`)"
    dai = f"{d['n']} bản thu dài hơn 28 s của FLEURS test: WER {vn(d['WER_asr'])}%, BLEU {vn(d['BLEU'])} (đưa thẳng audio > 30 s vào khối nghe thì WER lên tới 94,70%)"
    for f in ("app/gradio_app.py", "README.md"):
        fp = OUT / f; s = fp.read_text(encoding="utf-8")
        s = re.sub(r"\(BLEU 30,92, WER( khối nghe)? 10,76%\) và kém nhất ở miền Tin tức \(BLEU 23,17, WER 19,18%\)", mien, s)
        s = s.replace("8 trên 361 câu dev có bản dịch ngắn hơn 0,7 lần tham chiếu.", cau_ngan)
        s = s.replace("Chưa đo lại WER với model thật.", f"Đo lại 04/11 với {v}: {dai}.")
        s = re.sub(r"\*\*WER 12,27%, BLEU 27,63\*\* \(adapter V4, đo ngày 01/11[^)]*\)", "**" + he + "**", s)
        s = re.sub(r"đo trên 7 bản thu dài của FLEURS test còn WER 16,31%[^.]*\.", "đo trên " + dai + ".", s)
        s = re.sub(r"chia đoạn thì còn 16,31% \(đo trên 7 bản thu dài của FLEURS test\)", "chia đoạn: " + dai, s)
        s = s.replace("so với mốc 01/11 (WER 12,27, BLEU 27,63, sai số 1,0)", f"so với mốc 04/11 – bản {v} (WER {vn(p['WER_asr'])}, BLEU {vn(p['BLEU'])}, sai số 1,0)")
        fp.write_text(s, encoding="utf-8")
    sua("tests/nghiem_thu_that.py", [
        ("    # moc 01/11 (857 ban, V4, truoc khi sua gop LoRA fp32 + suppress): WER 12,27 BLEU 27,63\n    ok = n < 857 or (abs(w - 12.27) < 1.0 and abs(b - 27.63) < 1.0)",
         f"    # moc 04/11 (857 ban, {v} + tien/hau xu ly, experiments/reports/he_thong_V2): WER {p['WER_asr']} BLEU {p['BLEU']}\n"
         f"    ok = n < 857 or (abs(w - {p['WER_asr']}) < 1.0 and abs(b - {p['BLEU']}) < 1.0)"),
        ('f"moc 01/11: WER 12,27 BLEU 27,63 (sai so cho phep 1,0).', f'f"moc 04/11 ({v}): WER {vn(p["WER_asr"])} BLEU {vn(p["BLEU"])} (sai so cho phep 1,0).')])
    con = [f for f in ("app/gradio_app.py", "README.md", "tests/nghiem_thu_that.py") if re.search(r"27,63|27\.63|30,92|8 trên 361", (OUT / f).read_text(encoding="utf-8"))]
    print("  số cũ còn sót:", con or "không")


if __name__ == "__main__":
    main()
