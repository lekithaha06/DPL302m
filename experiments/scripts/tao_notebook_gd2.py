#!/usr/bin/env python3
"""Sinh 3 notebook giai đoạn 2 (phần Kiệt, sau khi nhận gói Đăng 03/11/2026):
  notebooks/02_baseline_B1_whisper_translate.ipynb  – kiểm gói Đăng, chạy B1 end-to-end, chấm, bootstrap
  notebooks/03_ablation_va_chon_ban_cuoi.ipynb     – kiểm toán V1–V4, ablation 1 yếu tố (rank 8/32, augmentation), chọn bản theo DEV
  notebooks/06_danh_gia_tong_hop.ipynb     – đánh giá chung B0/B1/V1–V4/ablation, prediction theo schema, Excel 3 sheet gốc, tổng 6 sheet sau khi thêm 3 seed
Ô nặng gọi script của project qua subprocess, có log; chạy lại thì bỏ qua phần đã có checkpoint/score (resume được).
Chạy: env/.venv/Scripts/python.exe scripts/tao_notebook_gd2.py   (chỉ sinh; thực thi bằng scripts/chay_notebook.py)"""
from pathlib import Path

import nbformat as nbf

T = Path(__file__).resolve().parents[1]
OUT = T / "notebooks"

SETUP = r'''
import os, sys, json, csv, subprocess, time, shutil, statistics, re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import Image, Markdown, display

# Thư mục thực nghiệm (có scripts/, data/, checkpoints/): task3/ – notebook nằm ở task3/notebooks/
T3 = next(c for c in [Path.cwd().parent, Path.cwd(), Path(r"D:\CAIDCM\teamwork\task3")] if (c / "scripts" / "mt" / "train_lora.py").exists())
os.chdir(T3); TW = T3.parent
PY = sys.executable
ENV = dict(os.environ, HF_HUB_CACHE=str(T3 / "hf_home" / "hub"), HF_HUB_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
           PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
MTREV = "ae7baa85da07dbe8e23ac26a9f5ef560c17e2138"
BO_QUA = ("Warning", "warnings.warn", "warn(", "forced_decoder_ids", "attention mask", "fget.__get__", "TypedStorage")

def chay(*lenh, log=None):
    """Chạy 1 script của project (cùng venv), in log từng dòng, ghi thêm vào file log nếu có; lỗi thì dừng ô."""
    t0 = time.time()
    p = subprocess.Popen([PY, "-X", "utf8", *map(str, lenh)], cwd=T3, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace")
    fl = open(T3 / log, "a", encoding="utf-8") if log else None
    for d in p.stdout:
        if fl: fl.write(d)
        if not any(x in d for x in BO_QUA): print(d, end="")
    p.wait(); fl and fl.close()
    print(f"--- mã thoát {p.returncode} · {time.time() - t0:.0f} s")
    if p.returncode: raise RuntimeError(f"lệnh lỗi: {lenh}")

J = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
def mt(v, s):
    p = T3 / "runs/mt" / v / s / "score.json"
    return J(p) if p.exists() else None
vn = lambda x, d=2: "–" if x is None else f"{float(x):.{d}f}".replace(".", ",")
pd.set_option("display.max_colwidth", 110); pd.set_option("display.width", 200)
plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": .3})
import torch
print("Thư mục:", T3, "| Python", sys.version.split()[0], "| torch", torch.__version__, "| GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "KHÔNG")
'''


def nb(cells):
    return nbf.v4.new_notebook(cells=[nbf.v4.new_markdown_cell(s.strip()) if k == "md" else nbf.v4.new_code_cell(s.strip()) for k, s in cells],
                               metadata={"kernelspec": {"name": "task3-dpl302m", "display_name": "Python (task3 DPL302m)", "language": "python"},
                                         "language_info": {"name": "python"}})


# ============================================================ 03 – B1
NB03 = [
    ("md", """
# 03 · Baseline B1 – Whisper Translate (end-to-end)

**B1**: audio tiếng Việt → `openai/whisper-small` (`task="translate"`) → văn bản tiếng Anh, **không** qua transcript tiếng Việt và khối dịch.
So với **B0** (cascade): PhoWhisper-small → VinAI Translate gốc. Cùng 857 bản thu FLEURS vi_vn test, cùng sacreBLEU 2.4.3.
Proposal Task 1 đã nêu "Whisper task translate làm đối chứng" → B1 là baseline đối chứng theo proposal (không phải tái lập số của paper).

Notebook: (1) kiểm gói bàn giao `DANG_BASELINE_HANDOFF`, (2) chạy thử 5 mẫu, (3) chạy đủ 857, (4) chấm BLEU/chrF++, RTF, theo miền,
(5) bootstrap so với B0. Code B1: `scripts/b1/b1_whisper_translate.py` (dựa trên code của gói bàn giao, có sửa – xem mục 1).
"""),
    ("code", SETUP),
    ("md", """
## 1. Kiểm gói bàn giao baseline

| Hạng mục checklist | Gói bàn giao | Xử lý ở notebook này |
|---|---|---|
| Dataset 857 mẫu, không trùng | Có (`check_data.py`) | Kiểm lại ô dưới |
| B0 cascade | Có số 22,69 / 49,38 (`b0_summary.json`) | Đối chiếu file kết quả ô dưới |
| B1 chạy thật với audio | **Chưa chạy** (không có GPU) | Chạy ở mục 3 |
| Output theo schema chung | Chưa (tên trường khác) | Script B1 xuất đúng schema |
| Audio > 30 s | Code gốc `processor(audio)` **cắt còn 30 s** | Sửa: long-form như B0 |
| Đọc file trên Windows | `open()` không `encoding="utf-8"`; cần `torchaudio` (venv không có) | Sửa: utf-8 + soundfile |
| Revision, seed, suppress tokens | Không ghim | Ghim `973afd24`, seed 42, suppress tokens của protocol |
| Gap analysis | Ghi "chưa có BLEU dịch sạch" – **đã có** (B0 38,27) | Số đúng ở notebook 05 |
"""),
    ("code", r'''
G = TW / "kiem_dang_baseline/goc/DANG_BASELINE_HANDOFF"
MAN = TW / "GUI_DANG_FLEURS_TEST/manifest_fleurs_test.jsonl"
m_dang = [json.loads(l) for l in open(MAN, encoding="utf-8")]
m_t3 = {json.loads(l)["id"].removesuffix(".wav"): json.loads(l) for l in open(T3 / "runs/manifests/asr_fleurs_test.jsonl", encoding="utf-8")}
print("Manifest bàn giao:", len(m_dang), "mẫu | trùng sample_id:", len(m_dang) - len({r["sample_id"] for r in m_dang}),
      "| khớp manifest thực nghiệm (id + câu Việt):", sum(r["sample_id"] in m_t3 and m_t3[r["sample_id"]]["reference"] == r["reference_vi"] for r in m_dang))
b0s = J(G / "b0_summary.json") if (G / "b0_summary.json").exists() else None
b0 = mt("B0", "fleurs_test_asr_pho")
print("B0 trong gói bàn giao:", b0s and b0s["metrics"], "| file kết quả:", {"BLEU": b0["BLEU"], "chrF++": b0["chrF++"], "n": b0["n"]})
print("→ khớp" if b0s and b0s["metrics"]["BLEU"] == b0["BLEU"] and b0s["metrics"]["chrF++"] == b0["chrF++"] else "→ KHÁC / không có gói")
print("B0 dịch transcript sạch (gói bàn giao ghi 'chưa có'):", mt("B0", "fleurs_test_clean")["BLEU"])
'''),
    ("md", "## 2. Chạy thử 5 mẫu"),
    ("code", r'''
thu = T3 / "runs/b1/smoke5.jsonl"; thu.unlink(missing_ok=True)
chay("scripts/b1/b1_whisper_translate.py", "--manifest", MAN, "--out", thu, "--limit", 5)
display(pd.read_json(thu, lines=True, dtype={"sample_id": str, "sent_id": str})[["sample_id", "audio_duration_s", "latency_s", "status", "pred_en", "reference_en"]])
'''),
    ("md", "## 3. Chạy đủ 857 bản thu (GPU, ~10–20 phút; chạy lại sẽ bỏ qua mẫu đã xong)"),
    ("code", r'''
PRED = T3 / "runs/b1/predictions_b1.jsonl"
chay("scripts/b1/b1_whisper_translate.py", "--manifest", MAN, "--out", PRED, log="logs/b1_whisper_translate.log")
b1 = pd.read_json(PRED, lines=True, dtype={"sample_id": str, "sent_id": str})
print("Số dòng:", len(b1), "| trạng thái:", b1.status.value_counts().to_dict(), "| long-form:", int(b1.long_form.sum()))
print(json.dumps(J(T3 / "runs/b1/run_metadata_b1.json"), ensure_ascii=False, indent=1)[:900])
'''),
    ("md", "## 4. Chấm BLEU / chrF++ (sacreBLEU 2.4.3, cùng cấu hình B0) – lưu `runs/mt/B1_whisper-small_translate/fleurs_test_audio/`"),
    ("code", r'''
import sacrebleu
assert len(b1) == 857 and (b1.status == "ok").all(), "chưa đủ 857 mẫu ok"
d = T3 / "runs/mt/B1_whisper-small_translate/fleurs_test_audio"; d.mkdir(parents=True, exist_ok=True)
with open(d / "hyp.jsonl", "w", encoding="utf-8") as f:   # cùng định dạng hyp.jsonl của B0/V* (id có đuôi .wav) để dùng chung bootstrap.py
    for r in b1.itertuples():
        f.write(json.dumps({"id": r.sample_id + ".wav", "sent_id": str(r.sent_id), "src": "", "ref": r.reference_en, "hyp": r.pred_en}, ensure_ascii=False) + "\n")
bl, ch = sacrebleu.BLEU(), sacrebleu.CHRF(word_order=2)
b, c = bl.corpus_score(list(b1.pred_en), [list(b1.reference_en)]), ch.corpus_score(list(b1.pred_en), [list(b1.reference_en)])
rtf = b1.latency_s.sum() / b1.audio_duration_s.sum()
sc = {"BLEU": round(b.score, 2), "chrF++": round(c.score, 2), "bleu_signature": str(bl.get_signature()), "chrf_signature": str(ch.get_signature()),
      "n": len(b1), "he": "B1 end-to-end Whisper-small translate", "model_id": b1.model_id.iloc[0], "RTF_tong": round(rtf, 3),
      "latency_p50_s": round(b1.latency_s.median(), 3), "latency_p95_s": round(b1.latency_s.quantile(.95), 3),
      "ghi_chu_RTF": "latency mỗi mẫu = chỉ bước generate (đồng bộ CUDA, đã khởi động GPU), batch 1; khác cách đo do_toc_do.py (100 mẫu, 3 lần xen kẽ)"}
(d / "score.json").write_text(json.dumps(sc, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: sc[k] for k in ("BLEU", "chrF++", "n", "RTF_tong", "latency_p50_s", "latency_p95_s")}, ensure_ascii=False))
nh = []
for ten, g in [("toàn bộ", b1)] + [(f"miền {k}", v) for k, v in b1.groupby("domain")] + [("≤ 30 s", b1[~b1.long_form]), ("> 30 s", b1[b1.long_form])]:
    nh.append({"nhóm": ten, "n": len(g), "BLEU": round(bl.corpus_score(list(g.pred_en), [list(g.reference_en)]).score, 2),
               "chrF++": round(ch.corpus_score(list(g.pred_en), [list(g.reference_en)]).score, 2)})
display(pd.DataFrame(nh))
'''),
    ("md", "## 5. So sánh với B0 – bootstrap 1000 lần theo cụm câu (`scripts/mt/bootstrap.py`)"),
    ("code", r'''
B1H = "runs/mt/B1_whisper-small_translate/fleurs_test_audio/hyp.jsonl"
for ten, a in (("B0 cascade (PhoWhisper → VinAI gốc)", "runs/mt/B0/fleurs_test_asr_pho/hyp.jsonl"),
               ("Whisper-small → VinAI gốc (cascade, khối nghe thứ hai)", "runs/mt/B0/fleurs_test_asr_wsp/hyp.jsonl")):
    o = T3 / f"reports/mt/bootstrap_{Path(a).parent.parent.name}_{Path(a).parent.name}_vs_B1.json"
    if not o.exists():
        chay("scripts/mt/bootstrap.py", "--a", a, "--b", B1H, "--data", "runs/mt_data/fleurs_test_clean.jsonl", "--out", o, "--n", 1000)
    r = J(o); print(f"{ten}: {r['BLEU_A']} → B1 {r['BLEU_B']} | Δ {r['delta']:+.2f} [{r['ci95'][0]}; {r['ci95'][1]}] | p(Δ≤0) = {r['p_one_sided_delta_le_0']}")
'''),
    ("code", r'''
A = {json.loads(l)["id"]: json.loads(l) for l in open(T3 / "runs/mt/B0/fleurs_test_asr_pho/hyp.jsonl", encoding="utf-8")}
B = {json.loads(l)["id"]: json.loads(l) for l in open(T3 / B1H, encoding="utf-8")}
cf = sacrebleu.CHRF(word_order=2)
vd = pd.DataFrame([{"id": i, "tham_chieu": A[i]["ref"], "B0_cascade": A[i]["hyp"], "B1_end_to_end": B[i]["hyp"],
                    "chrF_B0": round(cf.sentence_score(A[i]["hyp"], [A[i]["ref"]]).score, 1), "chrF_B1": round(cf.sentence_score(B[i]["hyp"], [B[i]["ref"]]).score, 1)} for i in A])
print(f"B1 tốt hơn B0 ở {(vd.chrF_B1 > vd.chrF_B0).sum()} câu, kém hơn ở {(vd.chrF_B1 < vd.chrF_B0).sum()} câu (chrF++ từng câu).")
display(vd.assign(d=vd.chrF_B1 - vd.chrF_B0).sort_values("d").iloc[[0, 1, 2, -3, -2, -1]].drop(columns="d"))
'''),
]

# ============================================================ 04 – ablation
NB04 = [
    ("md", """
# 04 · Proposed: kiểm toán V1–V4, ablation một yếu tố, chọn bản cuối theo DEV

Proposed = PhoWhisper-small (giữ nguyên, không LoRA) → VinAI Translate vi2en-v2 + **LoRA** (khối dịch).
- **V1–V4** là các *phiên bản* nối tiếp (mỗi bản đổi một yếu tố so với bản trước) – giữ nguyên checkpoint/kết quả cũ, không train lại.
- **Ablation mới** (03/11/2026): so với **V2**, mỗi thí nghiệm đổi **đúng một** yếu tố: rank LoRA 8, rank LoRA 32, augmentation dữ liệu dịch.
- **Quy tắc chọn bản** chốt trước khi chạy ablation: `reports/ablation/QUY_TAC_CHON.md`. Chỉ dùng số DEV, nhưng quy tắc chốt sau khi đã có số test của V1–V4 (quy tắc đầu cho ra V3), nên không phải lựa chọn mù với test.

Mỗi lần train ~35 phút + chấm 5 tập ~17 phút (RTX 4060). Checkpoint mỗi epoch ở `checkpoints/<bản>/epoch_k` (adapter + optimizer + RNG, resume được),
bản chọn ở `checkpoints/<bản>/best`. Chạy lại notebook sẽ bỏ qua phần đã xong.
"""),
    ("code", SETUP),
    ("md", "## 1. Kiểm toán V1–V4 (đọc config, nhật ký epoch, checkpoint thật)"),
    ("code", r'''
rows = []
for v in ("V1", "V2", "V3", "V4"):
    c, e, ch_ = J(f"checkpoints/{v}/config.json"), J(f"checkpoints/{v}/epochs.json"), J(f"checkpoints/{v}/best/chon.json")
    ep = sorted(p.name for p in (T3 / "checkpoints" / v).glob("epoch_*"))
    rows.append({"bản": v, "dữ liệu train": " + ".join(Path(x).stem for x in c["train"]), "n_train": c["n_train"], "lr": c["lr"],
                 "rank/alpha": f"{c['lora_r']}/{c['lora_alpha']}", "lớp đích": c["targets"], "batch×accum": f"{c['batch_size']}×{c['grad_accum']}",
                 "epochs": c["epochs"], "seed": c["seed"], "tham số train": c["trainable_params"], "checkpoint": ", ".join(ep),
                 "epoch chọn": ch_["best_epoch"], "dev BLEU (chọn)": ch_["dev_BLEU_translate"]})
display(pd.DataFrame(rows))
print("Rò rỉ: sent_id train ∩ dev/test =", len({json.loads(l)["sent_id"] for l in open("runs/mt_data/fleurs_train_asr_pho.jsonl", encoding="utf-8")}
      & {json.loads(l)["sent_id"] for f in ("fleurs_dev_asr_pho", "fleurs_test_asr_pho") for l in open(f"runs/mt_data/{f}.jsonl", encoding="utf-8")}))
'''),
    ("md", "## 2. Quy tắc chọn bản (đã ghi file trước khi chạy ablation)"),
    ("code", r'''
display(Markdown((T3 / "reports/ablation/QUY_TAC_CHON.md").read_text(encoding="utf-8")))
print("Ghi lúc:", time.strftime("%d/%m/%Y %H:%M", time.localtime((T3 / "reports/ablation/QUY_TAC_CHON.md").stat().st_mtime)))
'''),
    ("md", "## 3. Dữ liệu augmentation (chỉ từ TRAIN) – `scripts/mt/make_aug_data.py`"),
    ("code", r'''
chay("scripts/mt/make_aug_data.py")
aug = pd.read_json("runs/mt_data/fleurs_train_clean_asrstyle.jsonl", lines=True); goc = pd.read_json("runs/mt_data/fleurs_train_asr_pho.jsonl", lines=True)
display(pd.DataFrame({"lời ASR (đã có trong V2)": goc.src.head(3).values, "transcript sạch → dạng ASR (thêm vào A_aug)": aug.src.head(3).values, "câu Anh (giữ nguyên)": aug.ref.head(3).values}))
'''),
    ("md", "## 4. Cấu hình ablation (chỉ khác V2 đúng một yếu tố)"),
    ("code", r'''
V2c = J("checkpoints/V2/config.json")
CHUNG = ["--dev", "runs/mt_data/fleurs_dev_asr_pho.jsonl", "--revision", MTREV, "--epochs", V2c["epochs"], "--lr", V2c["lr"],
         "--batch_size", V2c["batch_size"], "--grad_accum", V2c["grad_accum"], "--warmup_ratio", V2c["warmup_ratio"], "--lora_dropout", V2c["lora_dropout"],
         "--targets", V2c["targets"], "--max_len", V2c["max_len"], "--seed", V2c["seed"], "--resume"]
TRAIN_V2 = ["runs/mt_data/fleurs_train_asr_pho.jsonl", "runs/mt_data/phomt_train_mix.jsonl"]
AB = {"A_r8":  {"doi": "LoRA rank 16 → 8 (alpha 32 → 16, giữ alpha/rank = 2)", "train": TRAIN_V2, "r": 8, "alpha": 16},
      "A_r32": {"doi": "LoRA rank 16 → 32 (alpha 32 → 64)", "train": TRAIN_V2, "r": 32, "alpha": 64},
      "A_aug": {"doi": "+ 2.926 cặp transcript sạch FLEURS train dạng ASR (augmentation)", "train": TRAIN_V2 + ["runs/mt_data/fleurs_train_clean_asrstyle.jsonl"], "r": 16, "alpha": 32}}
for k, a in AB.items():
    (T3 / "configs/mt").mkdir(exist_ok=True)
    (T3 / f"configs/mt/{k}.json").write_text(json.dumps({"version": k, "base": "V2", "change_vs_V2": a["doi"], "train": a["train"], "lora_r": a["r"], "lora_alpha": a["alpha"],
        **{x: V2c[x] for x in ("epochs", "lr", "batch_size", "grad_accum", "warmup_ratio", "lora_dropout", "targets", "max_len", "seed")},
        "selection": "epoch: BLEU dev cascade qua translate.py; bản cuối: reports/ablation/QUY_TAC_CHON.md"}, ensure_ascii=False, indent=1), encoding="utf-8")
display(pd.DataFrame([{"bản": k, "thay đổi so với V2": a["doi"], "rank/alpha": f"{a['r']}/{a['alpha']}", "file train": " + ".join(Path(x).stem for x in a["train"])} for k, a in AB.items()]))
'''),
    ("md", "## 5. Huấn luyện (checkpoint mỗi epoch; có `best/` thì bỏ qua)"),
]
for k in ("A_r8", "A_r32", "A_aug"):
    NB04.append(("code", f'''
k = "{k}"
if (T3 / "checkpoints" / k / "best" / "chon.json").exists():
    print(k, "đã train xong – nạp kết quả:", J(f"checkpoints/{{k}}/best/chon.json")["best_epoch"], "epoch chọn")
else:
    chay("scripts/mt/train_lora.py", "--train", *AB[k]["train"], "--out_dir", f"checkpoints/{{k}}", "--lora_r", AB[k]["r"], "--lora_alpha", AB[k]["alpha"], *CHUNG, log=f"logs/train_{{k}}.log")
display(pd.DataFrame(J(f"checkpoints/{{k}}/epochs.json"))[["epoch", "dev_loss", "dev_BLEU_translate", "dev_chrF++_translate", "minutes"]])
display(Image(filename=str(T3 / "checkpoints" / k / "curves.png"), width=760))
'''))
NB04 += [
    ("md", "## 6. Chấm 5 tập như V1–V4 (dev cascade, dev sạch, test cascade, test sạch, PhoMT test) – `scripts/mt/translate.py`"),
    ("code", r'''
TAP = ["fleurs_dev_asr_pho", "fleurs_dev_clean", "fleurs_test_asr_pho", "fleurs_test_clean", "phomt_test"]
for k in AB:
    for s in TAP:
        if mt(k, s) is None:
            chay("scripts/mt/translate.py", "--input", f"runs/mt_data/{s}.jsonl", "--out_dir", f"runs/mt/{k}/{s}", "--revision", MTREV,
                 "--adapter", f"checkpoints/{k}/best", log=f"logs/eval_{k}.log")
print("đủ điểm:", {k: all(mt(k, s) for s in TAP) for k in AB})
'''),
    ("md", "## 7. Áp quy tắc chọn trên DEV"),
    ("code", r'''
BAN = ["V1", "V2", "V3", "V4", *AB]
dv = pd.DataFrame([{"bản": v, "dev cascade": mt(v, "fleurs_dev_asr_pho")["BLEU"], "dev sạch": mt(v, "fleurs_dev_clean")["BLEU"],
                    "tham số train": J(f"checkpoints/{v}/config.json")["trainable_params"]} for v in BAN])
M = dv["dev cascade"].max(); dv["hoà (≥ M−0,5)"] = dv["dev cascade"] >= M - 0.5
ung = dv[dv["hoà (≥ M−0,5)"]].sort_values(["dev sạch", "tham số train", "bản"], ascending=[False, True, True])
CHON = ung.iloc[0]["bản"]
display(dv)
print(f"M = {M} ({dv.loc[dv['dev cascade'].idxmax(), 'bản']}) · nhóm hoà: {list(ung['bản'])} · CHỌN theo dev sạch: {CHON}")
(T3 / "reports/ablation/chon_ban_cuoi.json").write_text(json.dumps({"quy_tac": "reports/ablation/QUY_TAC_CHON.md", "M_dev_cascade": M,
    "nhom_hoa": list(ung["bản"]), "ban_chon": CHON, "bang_dev": dv.to_dict("records"), "luc": time.strftime("%d/%m/%Y %H:%M")}, ensure_ascii=False, indent=1), encoding="utf-8")
'''),
    ("md", "## 8. Bảng ablation trên test"),
    ("code", r'''
TEN = {"B0": "B0 (VinAI gốc, không LoRA)", "V1": "V1 = B0 + LoRA (lời ASR)", "V2": "V2 = V1 + PhoMT 1:1", "V3": "V3 = V2 + cân bằng câu/độ dài",
       "V4": "V4 = V3 với lr 5e-5", "A_r8": "A_r8 = V2 với rank 8", "A_r32": "A_r32 = V2 với rank 32", "A_aug": "A_aug = V2 + augmentation"}
rows = []
for v in ["B0", *BAN]:
    r = {"bản": TEN[v]} | {s: mt(v, s)["BLEU"] for s in TAP} | {"chrF++ test cascade": mt(v, "fleurs_test_asr_pho")["chrF++"]}
    bs = T3 / f"reports/mt/bootstrap_V2_{v}_cascade_test.json"
    if v.startswith("A_"):
        if not bs.exists():
            chay("scripts/mt/bootstrap.py", "--a", "runs/mt/V2/fleurs_test_asr_pho/hyp.jsonl", "--b", f"runs/mt/{v}/fleurs_test_asr_pho/hyp.jsonl",
                 "--data", "runs/mt_data/fleurs_test_asr_pho.jsonl", "--out", bs, "--n", 1000)
        b = J(bs); r["Δ test cascade so với V2 (KTC 95%)"] = f"{b['delta']:+.2f} [{b['ci95'][0]}; {b['ci95'][1]}], p = {b['p_one_sided_delta_le_0']}"
    rows.append(r)
ab = pd.DataFrame(rows).rename(columns={"fleurs_dev_asr_pho": "dev cascade", "fleurs_dev_clean": "dev sạch", "fleurs_test_asr_pho": "test cascade",
                                        "fleurs_test_clean": "test sạch", "phomt_test": "PhoMT test"})
display(ab); ab.to_csv(T3 / "reports/ablation/bang_ablation.csv", index=False, encoding="utf-8-sig")
fig, ax = plt.subplots(figsize=(10, 3.8)); x = range(len(ab))
ax.bar([i - .2 for i in x], ab["dev cascade"], .4, label="dev cascade"); ax.bar([i + .2 for i in x], ab["test cascade"], .4, label="test cascade")
ax.set_xticks(list(x)); ax.set_xticklabels([t.split(" =")[0] for t in ab["bản"]]); ax.set_ylim(20, 29); ax.legend(); ax.set_title("BLEU cascade – phiên bản và ablation")
plt.tight_layout(); plt.savefig(T3 / "reports/ablation/bang_ablation.png", dpi=130); plt.show()
print("Bản chọn theo DEV:", J("reports/ablation/chon_ban_cuoi.json")["ban_chon"])
'''),
]

# ============================================================ 05 – tổng hợp
NB05 = [
    ("md", """
# 05 · Đánh giá tổng hợp B0 / B1 / Proposed + Excel 3 sheet gốc, tổng 6 sheet sau khi thêm 3 seed

Cùng 857 bản thu FLEURS test, cùng sacreBLEU 2.4.3. WER/CER chỉ cho hệ có transcript tiếng Việt (cascade); B1 không có.
Xuất prediction theo schema chung (`reports/danh_gia/predictions_<model>.jsonl` + 1 file CSV gộp) và workbook
`reports/danh_gia/bang_ket_qua.xlsx` (Baseline · Proposed & Ablation · Error & Feasibility). Mục nào chưa chạy ghi **NOT RUN**.
"""),
    ("code", SETUP),
    ("md", "## 1. Prediction theo schema chung (chuyển từ kết quả đã chạy, không chạy lại model)"),
    ("code", r'''
OUTD = T3 / "reports/danh_gia"; OUTD.mkdir(parents=True, exist_ok=True)
man = {json.loads(l)["id"]: json.loads(l) for l in open("runs/manifests/asr_fleurs_test.jsonl", encoding="utf-8")}
en = {json.loads(l)["id"]: json.loads(l)["ref"] for l in open("runs/mt_data/fleurs_test_clean.jsonl", encoding="utf-8")}
asr = {s: {json.loads(l)["id"]: json.loads(l)["prediction"] for l in open(f"runs/asr/kiet_t2_{s}_fleurs_test/predictions.jsonl", encoding="utf-8")}
       for s in ("phowhisper-small", "whisper-small")}
chon = J("reports/ablation/chon_ban_cuoi.json")["ban_chon"]
HE = {"B0": ("B0_cascade_PhoWhisper+VinAI", "B0", "fleurs_test_asr_pho", "phowhisper-small"),
      "B0_wsp": ("cascade_WhisperSmall+VinAI", "B0", "fleurs_test_asr_wsp", "whisper-small"),
      **{v: (f"Proposed_PhoWhisper+VinAI+LoRA_{v}", v, "fleurs_test_asr_pho", "phowhisper-small") for v in ("V1", "V2", "V3", "V4", "A_r8", "A_r32", "A_aug")}}
b1 = {r["sample_id"] + ".wav": r for r in (json.loads(l) for l in open("runs/b1/predictions_b1.jsonl", encoding="utf-8"))}
tat = []
for k, (mid, v, s, a) in HE.items():
    hyp = {json.loads(l)["id"]: json.loads(l)["hyp"] for l in open(f"runs/mt/{v}/{s}/hyp.jsonl", encoding="utf-8")}
    R = [{"sample_id": i.removesuffix(".wav"), "split": "test", "model_id": mid, "reference_vi": man[i]["reference"], "reference_en": en[i], "pred_vi": asr[a][i],
          "pred_en": hyp[i], "latency_s": None, "audio_duration_s": man[i]["duration_s"], "status": "ok"} for i in man]
    tat += R
    with open(OUTD / f"predictions_{k}.jsonl", "w", encoding="utf-8") as f:
        for r in R: f.write(json.dumps(r, ensure_ascii=False) + "\n")
R = [{k_: b1[i][k_] for k_ in ("sample_id", "split", "model_id", "reference_vi", "reference_en", "pred_vi", "pred_en", "latency_s", "audio_duration_s", "status")} for i in man]
tat += R
with open(OUTD / "predictions_B1.jsonl", "w", encoding="utf-8") as f:
    for r in R: f.write(json.dumps(r, ensure_ascii=False) + "\n")
df = pd.DataFrame(tat); df.to_csv(OUTD / "predictions_tat_ca.csv", index=False, encoding="utf-8-sig")
print(df.groupby("model_id").size().to_string()); print("latency_s mỗi mẫu: chỉ B1 đo khi chạy; cascade đo tốc độ riêng (reports/toc_do/lap_V4) → NULL trong file này")
'''),
    ("md", "## 2. Bảng so sánh chung trên test"),
    ("code", r'''
import statistics as st
rs = {r["run_id"]: r for r in csv.DictReader(open("reports/asr/results_task2.csv", encoding="utf-8-sig"))}
PHIEN = next(d for d in ("lap_V2", "lap_V4") if (T3 / "reports/toc_do" / d / "toc_do_V2_lan3.json").exists() or d == "lap_V4")  # cùng 1 phiên cho mọi hệ
lap = lambda v: [J(p) for p in sorted((T3 / "reports/toc_do" / PHIEN).glob(f"toc_do_{v}_lan*.json"))]
print("Phiên đo tốc độ:", PHIEN)
def td(v):
    L = lap(v); return (st.median(x["RTF_total"] for x in L), st.median(x["latency_p95_s"] for x in L), max(x["gpu_peak_allocated_bytes"] for x in L) / 2**30) if L else (None, None, None)
b1s = mt("B1_whisper-small_translate", "fleurs_test_audio")
siz = lambda p: sum(f.stat().st_size for f in Path(p).rglob("*") if f.is_file())
hf = T3 / "hf_home/hub"
SZ = {"pho": siz(hf / "models--vinai--PhoWhisper-small/blobs"), "wsp": siz(hf / "models--openai--whisper-small/blobs"), "mt": siz(hf / "models--vinai--vinai-translate-vi2en-v2/blobs")}
rows = [{"hệ": "B0 · PhoWhisper → VinAI gốc", "WER FLEURS (%)": rs["kiet_t2_phowhisper-small_fleurs_test"]["WER_percent"], "BLEU test": mt("B0", "fleurs_test_asr_pho")["BLEU"],
         "chrF++": mt("B0", "fleurs_test_asr_pho")["chrF++"], "BLEU dịch sạch": mt("B0", "fleurs_test_clean")["BLEU"], "RTF": td("B0")[0], "p95 (s)": td("B0")[1]},
        {"hệ": "Whisper-small → VinAI gốc (cascade)", "WER FLEURS (%)": rs["kiet_t2_whisper-small_fleurs_test"]["WER_percent"], "BLEU test": mt("B0", "fleurs_test_asr_wsp")["BLEU"],
         "chrF++": mt("B0", "fleurs_test_asr_wsp")["chrF++"], "BLEU dịch sạch": "–", "RTF": "NOT RUN", "p95 (s)": "NOT RUN"},
        {"hệ": "B1 · Whisper-small translate (end-to-end)", "WER FLEURS (%)": "không áp dụng", "BLEU test": b1s["BLEU"], "chrF++": b1s["chrF++"], "BLEU dịch sạch": "không áp dụng",
         "RTF": f"{b1s['RTF_tong']} (cách đo khác)", "p95 (s)": b1s["latency_p95_s"]}]
for v in ("V1", "V2", "V3", "V4", "A_r8", "A_r32", "A_aug"):
    rows.append({"hệ": f"Proposed {v}" + (" ★ chọn theo dev" if v == chon else ""), "WER FLEURS (%)": rs["kiet_t2_phowhisper-small_fleurs_test"]["WER_percent"],
                 "BLEU test": mt(v, "fleurs_test_asr_pho")["BLEU"], "chrF++": mt(v, "fleurs_test_asr_pho")["chrF++"], "BLEU dịch sạch": mt(v, "fleurs_test_clean")["BLEU"],
                 "RTF": td(v)[0] if td(v)[0] else "NOT RUN", "p95 (s)": td(v)[1] if td(v)[1] else "NOT RUN"})
TONG = pd.DataFrame(rows); display(TONG)
print("Kích thước checkpoint (GB): PhoWhisper", round(SZ["pho"] / 1e9, 2), "· Whisper-small", round(SZ["wsp"] / 1e9, 2), "· VinAI", round(SZ["mt"] / 1e9, 2), "· adapter 0,035")
'''),
    ("md", "## 3. Workbook 3 sheet – `reports/danh_gia/bang_ket_qua.xlsx`"),
    ("code", r'''
pc = pd.read_csv("reports/asr/paper_comparison.csv", encoding="utf-8-sig")
S1 = pd.DataFrame([
  {"baseline": "PhoWhisper-small (ASR)", "dataset": "VIVOS test (760)", "metric": "WER %", "paper": 6.33, "nhóm": float(rs["kiet_t2_phowhisper-small_vivos_test"]["WER_percent"]),
   "ghi chú": "cùng dataset; paper PhoWhisper Table 2", "nguồn": "reports/asr/results_task2.csv"},
  {"baseline": "Whisper-small (ASR)", "dataset": "FLEURS vi_vn test (857)", "metric": "WER %", "paper": 21.2, "nhóm": float(rs["kiet_t2_whisper-small_fleurs_test"]["WER_percent"]),
   "ghi chú": "cùng dataset; paper Whisper Table 11", "nguồn": "reports/asr/results_task2.csv"},
  {"baseline": "VinAI Translate vi2en (MT gốc)", "dataset": "PhoMT test (19.151)", "metric": "BLEU", "paper": 40.42, "nhóm": mt("B0", "phomt_test")["BLEU"],
   "ghi chú": "cùng dataset; paper Interspeech 2022 Table 1", "nguồn": "runs/mt/B0/phomt_test/score.json"},
  {"baseline": "B0 cascade PhoWhisper → VinAI", "dataset": "FLEURS vi_vn test (857)", "metric": "BLEU", "paper": "NR", "nhóm": mt("B0", "fleurs_test_asr_pho")["BLEU"],
   "ghi chú": "paper không báo cascade; dịch sạch cùng tập: " + str(mt("B0", "fleurs_test_clean")["BLEU"]), "nguồn": "runs/mt/B0/fleurs_test_asr_pho/score.json"},
  {"baseline": "B1 Whisper-small translate (end-to-end)", "dataset": "FLEURS vi_vn test (857)", "metric": "BLEU", "paper": "NOT RUN (chưa tra bảng dịch FLEURS của paper Whisper)", "nhóm": b1s["BLEU"],
   "ghi chú": "baseline đối chứng theo proposal Task 1; không nhận là tái lập paper", "nguồn": "runs/mt/B1_whisper-small_translate/fleurs_test_audio/score.json"}])
S2 = pd.read_csv("reports/ablation/bang_ablation.csv", encoding="utf-8-sig").assign(nguồn="runs/mt/<bản>/<tập>/score.json; reports/mt/bootstrap_V2_*.json; chọn: reports/ablation/chon_ban_cuoi.json")
grp = {"all": "tất cả", "so": "có chữ số", "ten": "có tên riêng", "dai": "lời ASR > 40 từ", "asr_xau": "ASR sai nhiều", "con_lai": "còn lại"}
e3 = []
for r in csv.DictReader(open("reports/asr/strata.csv", encoding="utf-8-sig")):
    if r["run_id"] == "kiet_t2_phowhisper-small_fleurs_test":
        e3.append({"loại": "WER ASR theo nhóm (test)", "nhóm": f"{r['group_type']}={r['group_value']}", "n": r["n_recordings"], "giá trị": r["WER_percent"], "đơn vị": "WER %", "nguồn": "reports/asr/strata.csv"})
fv = chon if (T3 / f"reports/mt/failure_{chon}_dev.json").exists() else "V4"
g = J(f"reports/mt/failure_{fv}_dev.json")["groups"]
for k, t in grp.items():
    e3.append({"loại": f"BLEU dev theo nhóm câu: B0 → {fv}", "nhóm": t, "n": g[k]["n"], "giá trị": f"{g[k]['B0'][0]} → {g[k][fv][0]}", "đơn vị": "BLEU", "nguồn": f"reports/mt/failure_{fv}_dev.json"})
for v in ("B0", "V2", "V3", "V4"):
    rtf, p95, vr = td(v)
    if rtf is not None:
        e3.append({"loại": "Tốc độ (3 lần đo xen kẽ, 100 bản thu)", "nhóm": v, "n": 100, "giá trị": f"RTF {rtf} · p95 {p95} s · VRAM {vr:.2f} GiB", "đơn vị": "", "nguồn": f"reports/toc_do/{PHIEN}/"})
e3.append({"loại": "Tốc độ B1", "nhóm": "B1", "n": 857, "giá trị": f"RTF {b1s['RTF_tong']} · p95 {b1s['latency_p95_s']} s", "đơn vị": "", "nguồn": "runs/mt/B1_whisper-small_translate/fleurs_test_audio/score.json"})
he = next((T3 / f"reports/{d}/ket_qua.json" for d in ("he_thong_V2", "he_thong") if (T3 / f"reports/{d}/ket_qua.json").exists()), T3 / "x")
if he.exists():
    k_ = J(he)
    for c_ in ("truoc_0411", "proposed"):
        q = k_[c_]["tat_ca"]; e3.append({"loại": f"Cả hệ sản phẩm ({k_['mo_hinh'].split('LoRA ')[-1]} + tiền/hậu xử lý)", "nhóm": c_, "n": q["n"], "giá trị": f"WER {q['WER_asr']} · BLEU {q['BLEU']} · chrF++ {q['chrF++']} · RTF {q['RTF']}", "đơn vị": "", "nguồn": str(he.relative_to(T3))})
e3.append({"loại": "Kích thước", "nhóm": "PhoWhisper + VinAI + adapter", "n": "", "giá trị": round((SZ["pho"] + SZ["mt"]) / 1e9 + 0.035, 2), "đơn vị": "GB", "nguồn": "hf_home/hub"})
S3 = pd.DataFrame(e3)
X = OUTD / "bang_ket_qua.xlsx"
with pd.ExcelWriter(X, engine="openpyxl") as w:
    S1.to_excel(w, sheet_name="Baseline Comparison", index=False); S2.to_excel(w, sheet_name="Proposed & Ablation", index=False); S3.to_excel(w, sheet_name="Error & Feasibility", index=False)
    TONG.to_excel(w, sheet_name="So sanh chung (test)", index=False)
from openpyxl import load_workbook
wb = load_workbook(X)
for ws in wb.worksheets:
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = min(60, max(10, max(len(str(c.value or "")) for c in col) + 2))
wb.save(X)
print(X, "| sheet:", wb.sheetnames); display(S1); display(S3.head(12))
'''),
]


def main():
    # Chỉ sinh notebook được chỉ định (vd: 05) – sinh lại sẽ XOÁ output đã chạy của notebook đó
    import sys
    OUT.mkdir(exist_ok=True)
    chon = set(sys.argv[1:]) or {"03", "04", "05"}
    for ten, c in (("02_baseline_B1_whisper_translate.ipynb", NB03), ("03_ablation_va_chon_ban_cuoi.ipynb", NB04), ("06_danh_gia_tong_hop.ipynb", NB05)):
        if ten[:2] in chon:
            nbf.write(nb(c), OUT / ten); print("sinh", OUT / ten)


if __name__ == "__main__":
    main()
