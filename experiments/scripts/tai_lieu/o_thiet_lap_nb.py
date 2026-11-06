# Ô thiết lập của notebook toàn bộ code. Magic %%nguon: ô chứa nguyên văn file, chạy xong in output thật của file đó.
import ast, hashlib, json, os, py_compile, subprocess, sys, tempfile
from pathlib import Path

import pandas as pd
from IPython.core.magic import register_cell_magic
from IPython.display import Image, display

R = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
E = R / "experiments"
TAM = Path(tempfile.mkdtemp(prefix="dpl302m_"))
MT_REV = "ae7baa85da07dbe8e23ac26a9f5ef560c17e2138"
ASR_REV = "a86b604c346caf7148c37512eafe783a16420adb"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONPATH=str(R))
DA_CHAY = set()


def log(*ten, n=12):
    """Log thật của lần chạy gốc, lấy trong experiments/logs."""
    for t in ten:
        f = E / "logs" / t
        d = [x.split("\r")[-1] for x in f.read_text(encoding="utf-8", errors="replace").splitlines()]
        d = [x for x in d if x.strip() and "Warning" not in x and "warnings.warn" not in x]
        print(f"--- log thật {t}: {len(d)} dòng, {min(n, len(d))} dòng cuối ---")
        print("\n".join(x[:170] for x in d[-n:]))


def chay(*lenh, cwd=E, n=14):
    """Chạy thật lệnh python, in các dòng cuối."""
    print("$ python", " ".join(str(x) for x in lenh).replace(str(TAM), "<tam>"))
    r = subprocess.run([sys.executable, *map(str, lenh)], cwd=cwd, env=ENV, capture_output=True, text=True, encoding="utf-8", errors="replace")
    d = [x.split("\r")[-1] for x in (r.stdout + "\n" + r.stderr).splitlines()]
    d = [x for x in d if x.strip() and not any(k in x for k in ("Warning", "warnings.warn", "forced_decoder_ids", "attention mask"))]
    print("\n".join(x[:170] for x in d[-n:])); print("mã thoát:", r.returncode)


def pytest_file(f):
    r = subprocess.run([sys.executable, "-m", "pytest", "-o", "addopts=", "-q", "-p", "no:cacheprovider", "--color=no", f], cwd=R, env=ENV, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("$ pytest", f, "→", r.stdout.strip().splitlines()[-1])


def json_in(p, n=900):
    print(f"--- {p} ---"); print((R / p).read_text(encoding="utf-8")[:n])


def c_train():
    d = TAM / "train_nho"; d.mkdir()
    for ten, k in (("fleurs_train_asr_pho", 40), ("fleurs_dev_asr_pho", 20)):
        (d / f"{ten}.jsonl").write_text("".join((E / f"runs/mt_data/{ten}.jsonl").open(encoding="utf-8").readlines()[:k]), encoding="utf-8")
    print("Chạy thật train ngắn để kiểm code: 40 câu, 1 epoch. Không phải số báo cáo.")
    chay("scripts/mt/train_lora.py", "--train", d / "fleurs_train_asr_pho.jsonl", "--dev", d / "fleurs_dev_asr_pho.jsonl", "--out_dir", d / "ck", "--revision", MT_REV, "--epochs", 1, "--batch_size", 4, "--grad_accum", 4, "--lora_r", 16, "--lora_alpha", 32, "--seed", 42, n=8)
    print("Checkpoint vừa lưu:", [f"{p.relative_to(d / 'ck')} {p.stat().st_size / 1e6:.1f} MB" for p in sorted((d / "ck/best").glob("adapter*"))])
    log("train_V2.log", n=8)


def c_dich():
    print("Chạy thật adapter V2 trên 30 câu dev. Số của cả tập ở score.json.")
    chay("scripts/mt/translate.py", "--input", "runs/mt_data/fleurs_dev_asr_pho.jsonl", "--out_dir", TAM / "dich", "--revision", MT_REV, "--adapter", R / "checkpoints/V2/best", "--limit", 30, n=4)
    for l in (TAM / "dich/hyp.jsonl").open(encoding="utf-8").readlines()[:2]:
        x = json.loads(l); print("VI:", x["src"][:110]); print("EN:", x["hyp"][:110])
    json_in("experiments/runs/mt/V2/fleurs_test_asr_pho/score.json", 260)


def c_asr():
    gia = {json.loads(l)["id"]: json.loads(l) for l in open(E / "runs/manifests/asr_fleurs_test.jsonl", encoding="utf-8")}
    D = []
    for f in sorted((E / "nghe_kiem/audio").glob("0[23]_fleurs_*.wav")):
        x = dict(gia[f.name.split("_", 2)[2]]); x["audio"] = str(f); D.append(x)
    m = TAM / "m.jsonl"; m.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in D), encoding="utf-8")
    print("Chạy thật PhoWhisper trên", len(D), "audio có sẵn trong gói.")
    chay("scripts/asr/run_asr.py", "--model", "vinai/PhoWhisper-small", "--revision", ASR_REV, "--manifest", m, "--out_dir", TAM / "asr", "--run_id", "kiem_notebook", n=3)
    for l in open(TAM / "asr/predictions.jsonl", encoding="utf-8"):
        print("ASR:", json.loads(l)["prediction"][:130])
    log("s4_asr_baseline.log", n=6)


def c_cham():
    print("Chấm thật lại toàn bộ dự đoán FLEURS test của PhoWhisper:")
    chay("scripts/asr/score_asr.py", "--predictions", "runs/asr/kiet_t2_phowhisper-small_fleurs_test/predictions.jsonl", "--manifest", "runs/manifests/asr_fleurs_test.jsonl", "--out", TAM / "cham", "--run-id", "kiem_notebook", n=30)


def c_boot():
    print("Chạy thật bootstrap 1.000 lần, B0 so với V2:")
    chay("scripts/mt/bootstrap.py", "--a", "runs/mt/B0/fleurs_test_asr_pho/hyp.jsonl", "--b", "runs/mt/V2/fleurs_test_asr_pho/hyp.jsonl", "--data", "runs/mt_data/fleurs_test_asr_pho.jsonl", "--out", TAM / "b.json", n=3)
    print((TAM / "b.json").read_text(encoding="utf-8")[:330])


def c_infer():
    f = sorted((E / "nghe_kiem/audio").glob("02_fleurs*.wav"))[0]
    chay("src/inference.py", "--audio", f, cwd=R, n=8)


def c_eval():
    chay("src/evaluate.py", "--hyp", "experiments/runs/asr/kiet_t2_phowhisper-small_fleurs_test/predictions.jsonl", "--metric", "wer", "--truong_ref", "reference", "--truong_hyp", "prediction", "--moc", "wer_phowhisper_fleurs", cwd=R, n=6)
    pytest_file("tests/test_evaluate.py")


def c_so():
    sys.path.insert(0, str(R))
    from src.so import doi_so
    t = "hôm nay là ngày mười một tháng ba năm hai nghìn không trăm hai mươi sáu"
    print("VÀO:", t); print("RA :", doi_so(t)); pytest_file("tests/test_so.py")


def c_audio():
    import soundfile as sf
    sys.path.insert(0, str(R))
    from src.audio import chia_doan
    a, sr = sf.read(sorted((E / "nghe_kiem/audio").glob("01_*.wav"))[0], dtype="float32")
    print("Audio", round(len(a) / sr, 2), "s, chia thành:", [d.moc_thoi_gian() for d in chia_doan(a, sr)]); pytest_file("tests/test_audio.py")


CHAY = {
    "experiments/scripts/mt/train_lora.py": c_train, "experiments/scripts/mt/translate.py": c_dich, "experiments/scripts/asr/run_asr.py": c_asr, "experiments/scripts/asr/score_asr.py": c_cham,
    "experiments/scripts/mt/bootstrap.py": c_boot, "src/inference.py": c_infer, "src/evaluate.py": c_eval, "src/so.py": c_so, "src/audio.py": c_audio,
    "experiments/scripts/asr/test_score_asr.py": lambda: chay("scripts/asr/test_score_asr.py", n=6),
    "src/pipeline.py": lambda: pytest_file("tests/test_pipeline.py"), "src/truc_tiep.py": lambda: pytest_file("tests/test_truc_tiep.py"), "api/main.py": lambda: (pytest_file("tests/test_api.py"), json_in("experiments/reports/he_thong_V2/thu_gradio/ket_qua_api.json", 500)),
    "app/gradio_app.py": lambda: json_in("experiments/reports/he_thong_V2/thu_gradio/ket_qua_gradio.json", 700),
    "experiments/scripts/mt/do_toc_do.py": lambda: (log("do_toc_do_lap.log", n=6), json_in("experiments/reports/toc_do/lap_V2/toc_do_V2_lan1.json", 420)),
    "experiments/scripts/mt/make_aug_data.py": lambda: print("Đã sinh", sum(1 for _ in open(E / "runs/mt_data/fleurs_train_clean_asrstyle.jsonl", encoding="utf-8")), "cặp vào runs/mt_data/fleurs_train_clean_asrstyle.jsonl"),
    "experiments/scripts/mt/make_balanced_data.py": lambda: print("Đã sinh", sum(1 for _ in open(E / "runs/mt_data/fleurs_train_asr_pho_canbang.jsonl", encoding="utf-8")), "dòng vào runs/mt_data/fleurs_train_asr_pho_canbang.jsonl"),
    "experiments/scripts/mt/failure_analysis.py": lambda: print((E / "reports/mt/failure_V2_dev.md").read_text(encoding="utf-8")[:750]),
    "experiments/scripts/asr/tao_audio_robust.py": lambda: display(pd.read_csv(E / "reports/robust/bang_robust.csv")),
    "experiments/scripts/hang_doi_robust.sh": lambda: display(pd.read_csv(E / "reports/robust/bang_robust.csv")),
    "experiments/scripts/tao_notebook_robust.py": lambda: print("Sinh notebooks/05_do_ben_khoi_nghe.ipynb:", (R / "notebooks/05_do_ben_khoi_nghe.ipynb").exists()),
    "experiments/scripts/tao_notebook_3seed.py": lambda: print("Sinh notebooks/04_kiem_tra_3_seed.ipynb:", (R / "notebooks/04_kiem_tra_3_seed.ipynb").exists()),
    "experiments/scripts/tong_hop_3seed.py": lambda: display(pd.read_csv(E / "reports/ba_seed/bang_3seed.csv").head(10)),
    "experiments/scripts/modal_3seed.py": lambda: json_in("experiments/reports/ba_seed/ket_qua_3seed.json", 700),
    "experiments/scripts/ket_luan.py": lambda: print((E / "reports/tong_hop/ban_cuoi.txt").read_text(encoding="utf-8")[:300]),
    "experiments/scripts/cham_theo_mien.py": lambda: display(pd.read_csv(E / "reports/domain/ket_qua_theo_mien.csv").tail(6)),
    "experiments/scripts/ve_bieu_do.py": lambda: display(Image(filename=str(E / "reports/tong_hop/ablation.png"), width=520)),
    "experiments/scripts/baseline2/b1_whisper_translate.py": lambda: (log("b1_whisper_translate.log", n=6), json_in("experiments/runs/mt/B1_whisper-small_translate/fleurs_test_audio/score.json", 260)),
    "experiments/scripts/he_thong_bootstrap.py": lambda: json_in("experiments/reports/he_thong_V2/bootstrap_cu_vs_moi.json", 360),
}
LOG = {"viec1_tai_3_bo_du_lieu": "s1_viec1_tai_du_lieu.log", "viec2_ghep_chia_fleurs_chong_trung": "s2a_viec2_ghep_chia.log", "viec2_lam_sach_du_lieu": "s2b_viec2_lam_sach.log", "viec3_eda": "s3a_viec3_eda.log", "viec4_can_bang_du_lieu": "s3b_viec4_can_bang.log",
       "make_asr_manifest": "s4_make_manifest.log", "make_mt_data": "s6_make_mt_data.log", "tai_model": "s0_tai_model.log", "s4_asr_baseline": "s4_asr_baseline.log", "theo_doi_tai_nguyen": "tai_nguyen.csv", "chay_notebook": "chay_notebook_gd2_lan2.log"}
CHUA_CHAY = ("docker/", ".github/", ".dockerignore", ".env.example", ".gitignore")


def ket_qua(rel):
    p = R / rel; goc = p.stem
    if rel in CHAY:
        return CHAY[rel]()
    if rel.startswith("tests/test_"):
        return pytest_file(rel)
    if goc in LOG:
        return log(LOG[goc], n=10)
    if (E / "logs" / f"{goc}.log").exists():
        return log(f"{goc}.log", n=10)
    if rel.startswith(CHUA_CHAY):
        return print("File cấu hình triển khai. Docker và GitHub Actions chưa chạy thật, xem KIEM_THU_CUOI.md.")
    if p.suffix == ".json":
        d = json.loads(p.read_text(encoding="utf-8"))
        return print("JSON hợp lệ, các khoá:", list(d)[:14] if isinstance(d, dict) else len(d))
    if p.suffix == ".py":
        py_compile.compile(str(p), cfile=str(TAM / "x.pyc"), doraise=True)
        c = ast.parse(p.read_text(encoding="utf-8"))
        return print("Biên dịch đạt. Hàm/lớp:", [x.name for x in c.body if isinstance(x, (ast.FunctionDef, ast.ClassDef))][:14], "· không chạy lại vì cần dữ liệu thô, GPU dài hoặc chỉ sinh tài liệu.")
    d = p.read_text(encoding="utf-8", errors="replace").splitlines()
    print("File", p.suffix or p.name, len(d), "dòng; dùng khi cài đặt hoặc chạy.")


@register_cell_magic
def nguon(dong, o):
    rel = dong.strip(); s = (R / rel).read_text(encoding="utf-8", errors="replace").rstrip()
    khop = s == o.rstrip() or (not s and o.strip() == "# (file rỗng)")
    print(f"[{rel}] {len(s.splitlines())} dòng · khớp file trong repo: {khop}")
    DA_CHAY.add(rel); ket_qua(rel)


def bang(p):
    print(p); print((R / p).read_text(encoding="utf-8")[:1800])





def xem_log(*mau, n=14):
    for m in mau:
        for f in sorted((E / "logs").glob(m)):
            log(f.name, n=n)
print("Repo:", R.name, "· Python", sys.version.split()[0])
