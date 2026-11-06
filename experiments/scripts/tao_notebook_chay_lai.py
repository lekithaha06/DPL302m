#!/usr/bin/env python3
"""Sinh và chạy notebooks/01_chay_lai_thuc_nghiem.ipynb: chạy lại thật toàn bộ thực nghiệm seed 42, mọi thứ ghi vào chay_lai_notebook/.
Lưu notebook sau mỗi ô. Chạy lại thì bỏ qua ô đã xong. Số trong notebook này KHÔNG ghi vào báo cáo, slide hay repo."""
import asyncio
import sys
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

T = Path(__file__).resolve().parents[1]; W = T / "chay_lai_notebook"; RA = T / "notebooks/01_chay_lai_thuc_nghiem.ipynb"
sys.stdout.reconfigure(encoding="utf-8")
SETUP = r'''
import json, os, re, subprocess, sys, time
from pathlib import Path
import pandas as pd
from IPython.core.magic import register_cell_magic
from IPython.display import Image, display
T = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
W = T / "chay_lai_notebook"; (W / "logs").mkdir(exist_ok=True)
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONUNBUFFERED="1", HF_HUB_CACHE=str(T / "hf_home/hub"), HF_HUB_DISABLE_TELEMETRY="1")
FLEURS_REV, VIVOS_REV = "70bb2e84b976b7e960aa89f1c648e09c59f894dd", "3cbfb2502e5e84776b4b778b020a09759f723f52"
PHO, WSP, MT = ("vinai/PhoWhisper-small", "a86b604c346caf7148c37512eafe783a16420adb"), ("openai/whisper-small", "973afd24965f72e36ca33b3055d56a652f456b4d"), "ae7baa85da07dbe8e23ac26a9f5ef560c17e2138"
BO = re.compile(r"Warning|warnings\.warn|forced_decoder_ids|attention mask|fget\.__get__|^\s*$|it/s\]|s/it\]")
THUA = re.compile(r"^(batch|step|bước|\s*\d+/\d+|epoch \d+ step)", re.I)


def chay(ten, *lenh, bat_buoc=True):
    """Chạy thật một lệnh python trong chay_lai_notebook/, in output ngay trong ô, log đầy đủ ở logs/."""
    t0 = time.time(); print("$ python", " ".join(map(str, lenh)), flush=True); dem = 0
    with open(W / "logs" / f"{ten}.log", "a", encoding="utf-8") as f:
        p = subprocess.Popen([sys.executable, "-u", *map(str, lenh)], cwd=W, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        for d in p.stdout:
            d = d.rstrip().split("\r")[-1]; f.write(d + "\n"); f.flush()
            if BO.search(d):
                continue
            dem += 1
            if not THUA.match(d) or dem % 40 == 0:
                print(d[:190], flush=True)
        p.wait()
    print(f"→ mã thoát {p.returncode}, {(time.time() - t0) / 60:.1f} phút", flush=True)
    if p.returncode and bat_buoc:
        raise RuntimeError(f"{ten} lỗi, xem chay_lai_notebook/logs/{ten}.log")


@register_cell_magic
def tep(dong, o):
    """Ô chứa nguyên văn script; dòng đầu là tên log, đường dẫn script và tham số. Chạy đúng file đó."""
    a = dong.split(); ten, f = a[0], a[1]
    assert (W / f).read_text(encoding="utf-8").rstrip() == o.rstrip(), "ô khác file"
    chay(ten, f, *a[2:])


def score_asr(rid, ds):
    if not (W / f"runs/asr/{rid}/score").exists():
        chay(f"cham_{rid}", "scripts/asr/score_asr.py", "--predictions", f"runs/asr/{rid}/predictions.jsonl", "--manifest", f"runs/manifests/asr_{ds}.jsonl", "--out", f"runs/asr/{rid}/score", "--run-id", rid)


def asr(m, ten, ds):
    rid = f"kiet_t2_{ten}_{ds}"
    chay(rid, "scripts/asr/run_asr.py", "--model", m[0], "--revision", m[1], "--manifest", f"runs/manifests/asr_{ds}.jsonl", "--out_dir", f"runs/asr/{rid}", "--run_id", rid); score_asr(rid, ds)


TAP = ["fleurs_dev_asr_pho", "fleurs_dev_clean", "fleurs_test_asr_pho", "fleurs_test_clean", "fleurs_test_asr_wsp", "phomt_test"]


def dich(v, ad=None):
    for d in TAP:
        l = ["scripts/mt/translate.py", "--input", f"runs/mt_data/{d}.jsonl", "--out_dir", f"runs/mt/{v}/{d}", "--revision", MT]
        chay(f"dich_{v}_{d}", *(l + (["--adapter", ad] if ad else [])))


def train(v, lr, *du_lieu):
    chay(f"train_{v}", "scripts/mt/train_lora.py", "--train", *[f"runs/mt_data/{x}.jsonl" for x in du_lieu], "--dev", "runs/mt_data/fleurs_dev_asr_pho.jsonl", "--out_dir", f"checkpoints/{v}", "--revision", MT, "--epochs", 5, "--lr", lr, "--batch_size", 4, "--grad_accum", 4, "--lora_r", 16, "--lora_alpha", 32, "--seed", 42, "--resume")
    e = json.loads((W / f"checkpoints/{v}/epochs.json").read_text(encoding="utf-8"))
    display(pd.DataFrame([{"epoch": x["epoch"], "dev_loss": round(x["dev_loss"], 4), "BLEU dev": x.get("dev_BLEU_translate", x["dev_BLEU"]), "phút": x["minutes"]} for x in e]))
    display(Image(filename=str(W / f"checkpoints/{v}/curves.png"), width=560))
    print("Checkpoint:", sorted(p.name for p in (W / f"checkpoints/{v}/best").iterdir()))
    print("Epoch chọn:", json.loads((W / f"checkpoints/{v}/best/chon.json").read_text(encoding="utf-8"))["best_epoch"])


def bs(a, b, ten):
    f = W / f"reports/mt/{ten}.json"
    if not f.exists():
        chay(ten, "scripts/mt/bootstrap.py", "--a", f"runs/mt/{a}/fleurs_test_asr_pho/hyp.jsonl", "--b", f"runs/mt/{b}/fleurs_test_asr_pho/hyp.jsonl", "--data", "runs/mt_data/fleurs_test_asr_pho.jsonl", "--out", f"reports/mt/{ten}.json")
    d = json.loads(f.read_text(encoding="utf-8")); print(ten, {k: d[k] for k in ("BLEU_A", "BLEU_B", "delta", "ci95", "p_one_sided_delta_le_0")})


print("Thư mục chạy:", W); print(subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True).stdout)
'''
S = lambda f: (W / f).read_text(encoding="utf-8").rstrip()


def o(ten, f, args=""):
    return f"%%tep {ten} {f} {args}\n{S(f)}"


def tao():
    md, co = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
    C = [md("# Chạy lại toàn bộ thực nghiệm, seed 42\n\nNotebook chạy thật từ dữ liệu gốc đã tải: làm sạch, 4 baseline ASR, B0, train V1–V4 đủ 5 epoch, đánh giá, bootstrap, tốc độ. Mọi kết quả ghi vào `chay_lai_notebook/`, không đụng `runs/`, `checkpoints/`, `reports/` đã báo cáo.\n\nÔ bắt đầu bằng `%%tep` chứa nguyên văn script và chạy đúng script đó. Số ở đây có thể lệch nhẹ so với số đã báo cáo, và **chưa đưa vào tài liệu**."), co(SETUP.strip())]
    C += [md("## 1. Môi trường"), co(o("check_env", "env/check_env.py")),
          md("## 2. Dữ liệu"),
          co(o("viec1", "scripts/data/viec1_tai_3_bo_du_lieu.py", "--data_dir data --report_dir reports/data --fleurs_revision 70bb2e84b976b7e960aa89f1c648e09c59f894dd --vivos_revision 3cbfb2502e5e84776b4b778b020a09759f723f52")),
          co(o("viec2a", "scripts/data/viec2_ghep_chia_fleurs_chong_trung.py", "--data_dir data --report_dir reports/data --revision 70bb2e84b976b7e960aa89f1c648e09c59f894dd --with_test_audio")),
          co(o("viec2b", "scripts/data/viec2_lam_sach_du_lieu.py", "--data_dir data --report_dir reports/data")),
          co(o("viec3", "scripts/data/viec3_eda.py", "--data_dir data --report_dir reports/data")),
          co(o("viec4", "scripts/data/viec4_can_bang_du_lieu.py", "--data_dir data --report_dir reports/data --seed 42")),
          co(o("manifest", "scripts/asr/make_asr_manifest.py", "--clean_dir data/clean --out_dir runs/manifests")),
          co(o("mien", "scripts/data/gan_mien_flores.py")),
          md("## 3. Khối nghe: 4 baseline và lời ASR cho khối dịch"),
          co(o("kiet_t2_phowhisper-small_vivos_test", "scripts/asr/run_asr.py", "--model vinai/PhoWhisper-small --revision a86b604c346caf7148c37512eafe783a16420adb --manifest runs/manifests/asr_vivos_test.jsonl --out_dir runs/asr/kiet_t2_phowhisper-small_vivos_test --run_id kiet_t2_phowhisper-small_vivos_test")),
          co(S("scripts/asr/score_asr.py").join(['%%tep cham_pho_vivos scripts/asr/score_asr.py --predictions runs/asr/kiet_t2_phowhisper-small_vivos_test/predictions.jsonl --manifest runs/manifests/asr_vivos_test.jsonl --out runs/asr/kiet_t2_phowhisper-small_vivos_test/score --run-id kiet_t2_phowhisper-small_vivos_test\n', ''])),
          co('asr(PHO, "phowhisper-small", "fleurs_test")'), co('asr(WSP, "whisper-small", "vivos_test")'), co('asr(WSP, "whisper-small", "fleurs_test")'),
          co('asr(PHO, "phowhisper-small", "fleurs_dev")'), co('asr(PHO, "phowhisper-small", "fleurs_train")'),
          co('''d = []
for r in ("phowhisper-small_vivos_test", "phowhisper-small_fleurs_test", "whisper-small_vivos_test", "whisper-small_fleurs_test", "phowhisper-small_fleurs_dev", "phowhisper-small_fleurs_train"):
    s = json.loads((W / f"runs/asr/kiet_t2_{r}/score/summary.json").read_text(encoding="utf-8")); d.append({"run": r, "n": s["n"], "WER": round(s["WER_percent"], 2), "CER": round(s["CER_percent"], 2), **{k: s["word_counts"][k] for k in "SDIN"}})
pd.DataFrame(d)'''),
          md("## 4. Khối dịch: dữ liệu"),
          co(o("mt_data", "scripts/mt/make_mt_data.py", "--phomt --asr test:pho:runs/asr/kiet_t2_phowhisper-small_fleurs_test/predictions.jsonl dev:pho:runs/asr/kiet_t2_phowhisper-small_fleurs_dev/predictions.jsonl train:pho:runs/asr/kiet_t2_phowhisper-small_fleurs_train/predictions.jsonl test:wsp:runs/asr/kiet_t2_whisper-small_fleurs_test/predictions.jsonl")),
          co(o("mt_can_bang", "scripts/mt/make_balanced_data.py")),
          md("## 5. Baseline B0: VinAI Translate gốc"),
          co(o("dich_B0_mau", "scripts/mt/translate.py", f"--input runs/mt_data/fleurs_dev_asr_pho.jsonl --out_dir runs/mt/B0/fleurs_dev_asr_pho --revision ae7baa85da07dbe8e23ac26a9f5ef560c17e2138")),
          co('dich("B0")'),
          md("## 6. Train LoRA V1–V4, đủ 5 epoch, seed 42"),
          co(o("train_V1", "scripts/mt/train_lora.py", "--train runs/mt_data/fleurs_train_asr_pho.jsonl --dev runs/mt_data/fleurs_dev_asr_pho.jsonl --out_dir checkpoints/V1 --revision ae7baa85da07dbe8e23ac26a9f5ef560c17e2138 --epochs 5 --lr 2e-4 --batch_size 4 --grad_accum 4 --lora_r 16 --lora_alpha 32 --seed 42 --resume")),
          co('train("V1", 2e-4, "fleurs_train_asr_pho")'), co('dich("V1", "checkpoints/V1/best")'),
          co('train("V2", 2e-4, "fleurs_train_asr_pho", "phomt_train_mix")'), co('dich("V2", "checkpoints/V2/best")'),
          co('train("V3", 2e-4, "fleurs_train_asr_pho_canbang", "phomt_train_mix")'), co('dich("V3", "checkpoints/V3/best")'),
          co('train("V4", 5e-5, "fleurs_train_asr_pho_canbang", "phomt_train_mix")'), co('dich("V4", "checkpoints/V4/best")'),
          md("## 7. Đánh giá"),
          co(o("bs_mau", "scripts/mt/bootstrap.py", "--a runs/mt/B0/fleurs_test_asr_pho/hyp.jsonl --b runs/mt/V2/fleurs_test_asr_pho/hyp.jsonl --data runs/mt_data/fleurs_test_asr_pho.jsonl --out reports/mt/bootstrap_B0_V2_mau.json")),
          co('(W / "reports/mt").mkdir(parents=True, exist_ok=True)\nfor v in ("V1", "V2", "V3", "V4"):\n    bs("B0", v, f"bootstrap_B0_{v}_cascade_test")\nbs("V1", "V2", "bootstrap_V1_V2_cascade_test"); bs("V2", "V3", "bootstrap_V2_V3_cascade_test"); bs("V3", "V4", "bootstrap_V3_V4_cascade_test")'),
          co(o("toc_do", "scripts/mt/do_toc_do.py", "--n 100 --out reports/toc_do/toc_do_V2.json --adapter checkpoints/V2/best")),
          co('chay("mien_ket_qua", "scripts/cham_theo_mien.py", bat_buoc=False)\nf = W / "reports/domain/ket_qua_theo_mien.csv"\nif f.exists():\n    display(pd.read_csv(f).tail(12))'),
          co('''H = {"B0": "B0", "V1": "V1", "V2": "V2", "V3": "V3", "V4": "V4"}
d = []
for v in H:
    r = {"bản": v}
    for k, t in (("dev cascade", "fleurs_dev_asr_pho"), ("dev sạch", "fleurs_dev_clean"), ("test cascade", "fleurs_test_asr_pho"), ("test sạch", "fleurs_test_clean"), ("Whisper → dịch", "fleurs_test_asr_wsp"), ("PhoMT", "phomt_test")):
        s = json.loads((W / f"runs/mt/{v}/{t}/score.json").read_text(encoding="utf-8")); r[k] = s["BLEU"]
    d.append(r)
B = pd.DataFrame(d); display(B)
M = B[B["bản"] != "B0"]["dev cascade"].max(); hoa = B[(B["bản"] != "B0") & (B["dev cascade"] >= M - .5)]
print("Áp quy tắc DEV trên lần chạy này: nhóm hoà", list(hoa["bản"]), "→ chọn", hoa.sort_values("dev sạch", ascending=False).iloc[0]["bản"])'''),
          co('''# So với số đã báo cáo, chỉ để xem, không ghi vào đâu
c = []
for v in H:
    for k, t in (("test cascade", "fleurs_test_asr_pho"), ("test sạch", "fleurs_test_clean")):
        a = json.loads((T / f"runs/mt/{v}/{t}/score.json").read_text(encoding="utf-8"))["BLEU"]; b = json.loads((W / f"runs/mt/{v}/{t}/score.json").read_text(encoding="utf-8"))["BLEU"]
        c.append({"bản": v, "chỉ số": k, "đã báo cáo": a, "lần chạy này": b, "chênh": round(b - a, 2)})
pd.DataFrame(c)''')]
    n = nbf.v4.new_notebook(cells=C); n.metadata.kernelspec = {"name": "task3-dpl302m", "display_name": "task3-dpl302m", "language": "python"}
    return n


def main():
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    n = nbf.read(RA, 4) if RA.exists() else tao()
    if not RA.exists():
        nbf.write(n, RA)
    k = NotebookClient(n, timeout=None, kernel_name="task3-dpl302m", resources={"metadata": {"path": str(RA.parent)}})
    with k.setup_kernel():
        for i, c in enumerate(n.cells):
            if c.cell_type != "code":
                continue
            xong = c.get("execution_count") and not any(o.get("output_type") == "error" for o in c.outputs)
            if xong and i > 1:
                continue
            print(f"{__import__('time').strftime('%H:%M:%S')} Ô {i}/{len(n.cells)}: {c.source[:70]!r}", flush=True)
            try:
                k.execute_cell(c, i)
            except CellExecutionError as e:
                nbf.write(n, RA); print("DỪNG VÌ LỖI ô", i, str(e)[-900:], flush=True); sys.exit(1)
            nbf.write(n, RA)
    print("TAT_CA_XONG", flush=True)


if __name__ == "__main__":
    main()
