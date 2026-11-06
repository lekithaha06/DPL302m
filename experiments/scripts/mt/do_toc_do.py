#!/usr/bin/env python3
"""S9 – Đo tốc độ cascade ASR → MT trên cùng máy (RTX 4060 Laptop), batch 1, như khi dùng thật.

Lấy N bản thu FLEURS test (chọn ngẫu nhiên seed 42, cố định), mỗi bản thu: ASR (theo protocol, short/long-form) rồi dịch 1 câu.
Ghi: thời gian ASR, MT, tổng; RTF = tổng thời gian xử lý / tổng thời lượng audio; latency p50/p95 mỗi bản thu;
VRAM đỉnh (torch.cuda.max_memory_allocated); dung lượng checkpoint trên đĩa (ASR, MT, adapter).
Có 3 lần warm-up không tính. Kết quả: --out (JSON) + per_utt.csv cạnh đó.
"""
import argparse
import csv
import json
import os
import random
import statistics
import sys
import threading
import time

import psutil
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from transformers import GenerationConfig, WhisperForConditionalGeneration, WhisperProcessor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from translate import load_mt, translate_batch  # noqa: E402


def dir_bytes(p):
    return sum(f.stat().st_size for f in Path(p).rglob("*") if f.is_file())


def weight_bytes(repo, revision):
    """Dung lượng file trọng số thật sự được nạp (ưu tiên safetensors như transformers), không cộng file trùng."""
    snap = Path(os.environ["HF_HUB_CACHE"]) / f"models--{repo.replace('/', '--')}" / "snapshots" / revision
    for n in ("model.safetensors", "pytorch_model.bin"):
        if (snap / n).exists():
            return (snap / n).stat().st_size, n
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="runs/manifests/asr_fleurs_test.jsonl")
    ap.add_argument("--asr_model", default="vinai/PhoWhisper-small")
    ap.add_argument("--asr_revision", default="a86b604c346caf7148c37512eafe783a16420adb")
    ap.add_argument("--mt_revision", default="ae7baa85da07dbe8e23ac26a9f5ef560c17e2138")
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--suppress", default="configs/common_suppression_from_task1.json")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    torch.manual_seed(42)
    items = [json.loads(l) for l in open(args.manifest, encoding="utf-8") if l.strip()]
    sample = random.Random(42).sample(items, args.n)

    proc = WhisperProcessor.from_pretrained(args.asr_model, revision=args.asr_revision)
    asr = WhisperForConditionalGeneration.from_pretrained(args.asr_model, revision=args.asr_revision, torch_dtype=torch.float16).cuda().eval()
    g = GenerationConfig.from_pretrained(args.asr_model, revision=args.asr_revision)
    sup = json.load(open(args.suppress, encoding="utf-8"))
    g.suppress_tokens, g.begin_suppress_tokens = sup["suppress_tokens"], sup["begin_suppress_tokens"]
    asr.generation_config = g
    common = dict(language="vi", task="transcribe", num_beams=5, do_sample=False, max_new_tokens=440, condition_on_prev_tokens=False)
    tok, mt = load_mt(args.mt_revision, args.adapter)

    @torch.inference_mode()
    def run(a):
        long_form = len(a) / 16000 > 30
        f = proc(a, sampling_rate=16000, return_tensors="pt", truncation=False,
                 padding="longest" if long_form else "max_length", return_attention_mask=True)
        out = asr.generate(f.input_features.cuda().half(), attention_mask=f.attention_mask.cuda(), **common, return_timestamps=long_form)
        return proc.batch_decode(out if not isinstance(out, dict) else out["sequences"], skip_special_tokens=True)[0].strip()

    for it in sample[:3]:  # warm-up
        translate_batch(tok, mt, [run(sf.read(it["audio"], dtype="float32")[0])])
    torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
    proc_ps = psutil.Process()
    ram, stop = [proc_ps.memory_info().rss], threading.Event()

    def _lay_mau_ram():
        while not stop.wait(0.5):
            ram.append(proc_ps.memory_info().rss)
    th = threading.Thread(target=_lay_mau_ram, daemon=True); th.start()
    rows = []
    for it in sample:
        a = sf.read(it["audio"], dtype="float32")[0]
        torch.cuda.synchronize(); t0 = time.perf_counter()
        txt = run(a)
        torch.cuda.synchronize(); t1 = time.perf_counter()
        en = translate_batch(tok, mt, [txt])[0]
        torch.cuda.synchronize(); t2 = time.perf_counter()
        rows.append({"id": it["id"], "duration_s": len(a) / 16000, "asr_s": t1 - t0, "mt_s": t2 - t1, "total_s": t2 - t0,
                     "n_src_chars": len(txt), "n_hyp_chars": len(en)})
    dur = sum(r["duration_s"] for r in rows)
    tot = [r["total_s"] for r in rows]
    q = statistics.quantiles(tot, n=20)
    stop.set(); th.join()
    asr_b, asr_f = weight_bytes(args.asr_model, args.asr_revision)
    mt_b, mt_f = weight_bytes("vinai/vinai-translate-vi2en-v2", args.mt_revision)
    res = {"n": len(rows), "audio_s": round(dur, 1), "RTF_total": round(sum(tot) / dur, 3),
           "RTF_asr": round(sum(r["asr_s"] for r in rows) / dur, 3), "RTF_mt": round(sum(r["mt_s"] for r in rows) / dur, 3),
           "latency_p50_s": round(statistics.median(tot), 2), "latency_p95_s": round(q[18], 2),
           "latency_mean_s": round(statistics.mean(tot), 2), "asr_mean_s": round(statistics.mean(r["asr_s"] for r in rows), 2),
           "mt_mean_s": round(statistics.mean(r["mt_s"] for r in rows), 2),
           "gpu_peak_allocated_bytes": torch.cuda.max_memory_allocated(),
           "ram_rss_peak_bytes": max(ram), "ram_sampling": "RSS tiến trình Python, lấy mẫu mỗi 0,5 s trong lúc đo",
           "asr_checkpoint_bytes": asr_b, "asr_weight_file": asr_f, "mt_checkpoint_bytes": mt_b, "mt_weight_file": mt_f,
           "adapter_bytes": sum(f.stat().st_size for f in Path(args.adapter).glob("adapter_model.*")) if args.adapter else 0,
           "adapter": args.adapter,
           "gpu": torch.cuda.get_device_name(0), "torch": torch.__version__, "batch_size": 1,
           "note": "ASR fp16 beam 5 theo protocol; MT fp16 beam 5; adapter LoRA được merge vào trọng số trước khi đo"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(res, indent=2), encoding="utf-8")
    with open(args.out.with_suffix(".per_utt.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(json.dumps(res))


if __name__ == "__main__":
    main()
