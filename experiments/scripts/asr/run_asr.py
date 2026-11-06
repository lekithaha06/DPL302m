#!/usr/bin/env python3
"""Suy luận ASR theo protocol bao_asr_v1_20261027 (Bảo thiết kế, Kiệt viết code và chạy).

- Audio <= 30 s: short-form, padding=max_length, return_timestamps=False.
- Audio  > 30 s: long-form tuần tự của Transformers, padding=longest, không cắt 30 s, return_timestamps=True,
  condition_on_prev_tokens=False; ghép text các segment theo thứ tự, lưu segment thô vào log.
- fp16, beam 5, batch 1, seed 42, max_new_tokens 440, language vi, task transcribe,
  suppress_tokens / begin_suppress_tokens lấy từ configs/common_suppression_from_task1.json cho cả hai model.

Manifest đầu vào (JSONL): id, audio (đường dẫn wav 16 kHz mono), reference (nhãn raw), sent_id, speaker_id, duration_s.
Đầu ra trong --out_dir:
  predictions.jsonl  ghi từng dòng ngay khi xong (chạy lại sẽ bỏ qua id đã có → chia buổi không đổi kết quả)
  segments.jsonl     log chi tiết: n_samples, n_frames, số token, chạm cap, segment thô (long-form), thời gian
  run_metadata.json  môi trường, revision, generation config đã resolve + SHA256, hash manifest
"""
import argparse
import hashlib
import json
import platform
import random
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import transformers
from transformers import GenerationConfig, WhisperForConditionalGeneration, WhisperProcessor

SR = 16000
PROTOCOL_ID = "bao_asr_v1_20261027"


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha_obj(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def set_seed(s):
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


def load_audio(path):
    a, sr = sf.read(path, dtype="float32", always_2d=False)
    if sr != SR:
        raise ValueError(f"{path}: sample rate {sr} != {SR} (phải dùng audio đã chuẩn hoá ở bước làm sạch)")
    if a.ndim != 1:
        raise ValueError(f"{path}: không phải mono")
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--revision", required=True)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--out_dir", required=True, type=Path)
    ap.add_argument("--run_id", required=True)
    ap.add_argument("--suppress", type=Path, default=Path(__file__).resolve().parents[2] / "configs" / "common_suppression_from_task1.json")
    ap.add_argument("--limit", type=int, default=0, help="smoke test: chỉ N mẫu đầu")
    ap.add_argument("--num_beams", type=int, default=5)
    args = ap.parse_args()

    torch.set_num_threads(4)
    set_seed(42)
    dev = "cuda"
    items = [json.loads(l) for l in open(args.manifest, encoding="utf-8") if l.strip()]
    if args.limit:
        items = items[: args.limit]
    args.out_dir.mkdir(parents=True, exist_ok=True)

    processor = WhisperProcessor.from_pretrained(args.model, revision=args.revision)
    model = WhisperForConditionalGeneration.from_pretrained(args.model, revision=args.revision, torch_dtype=torch.float16).to(dev).eval()
    gen_cfg = GenerationConfig.from_pretrained(args.model, revision=args.revision)
    sup = json.loads(args.suppress.read_text(encoding="utf-8"))
    gen_cfg.suppress_tokens = sup["suppress_tokens"]
    gen_cfg.begin_suppress_tokens = sup["begin_suppress_tokens"]
    model.generation_config = gen_cfg

    common = dict(language="vi", task="transcribe", num_beams=args.num_beams, do_sample=False, max_new_tokens=440,
                  length_penalty=1.0, repetition_penalty=1.0, no_repeat_ngram_size=0, temperature=None,
                  logprob_threshold=None, compression_ratio_threshold=None, no_speech_threshold=None,
                  condition_on_prev_tokens=False, use_cache=True)
    resolved = {"protocol_id": PROTOCOL_ID, "generate_kwargs_common": common,
                "short_form": {"processor": {"truncation": False, "padding": "max_length", "return_attention_mask": True},
                               "return_timestamps": False},
                "long_form": {"processor": {"truncation": False, "padding": "longest", "return_attention_mask": True},
                              "return_timestamps": True, "return_segments": True},
                "generation_config_after_override": gen_cfg.to_dict(),
                "suppress_file_sha256": sha_file(args.suppress), "dtype": "float16", "batch_size": 1, "seed": 42}
    cfg_sha = sha_obj(resolved)
    manifest_sha = sha_file(args.manifest)
    fingerprint = sha_obj({"model": args.model, "revision": args.revision, "config_sha256": cfg_sha,
                           "manifest_sha256": manifest_sha, "run_id": args.run_id, "limit": args.limit})

    pred_path = args.out_dir / "predictions.jsonl"
    done = set()
    if pred_path.exists():
        for l in open(pred_path, encoding="utf-8"):
            if l.strip():
                r = json.loads(l)
                if r["run_fingerprint"] != fingerprint:
                    sys.exit("predictions.jsonl có fingerprint khác (config/manifest đổi) → dùng out_dir mới")
                done.add(r["id"])
    meta = {"run_id": args.run_id, "protocol_id": PROTOCOL_ID, "model_id": args.model, "model_revision": args.revision,
            "manifest": str(args.manifest), "manifest_sha256": manifest_sha, "n_manifest": len(items),
            "config_sha256": cfg_sha, "run_fingerprint": fingerprint, "resolved_config": resolved,
            "environment": {"python": sys.version.split()[0], "torch": torch.__version__, "cuda": torch.version.cuda,
                            "cudnn": torch.backends.cudnn.version(), "transformers": transformers.__version__,
                            "numpy": np.__version__, "gpu": torch.cuda.get_device_name(0), "platform": platform.platform(),
                            "processor": platform.processor(),
                            "driver": subprocess.run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()},
            "started": time.strftime("%Y-%m-%d %H:%M:%S"), "resumed_skip": len(done)}
    (args.out_dir / "run_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # warm-up 1 lần (không ghi), để thời gian mẫu đầu không tính khởi tạo CUDA
    with torch.inference_mode():
        f = processor(np.zeros(SR, dtype=np.float32), sampling_rate=SR, return_tensors="pt", truncation=False,
                      padding="max_length", return_attention_mask=True)
        model.generate(f.input_features.to(dev, torch.float16), attention_mask=f.attention_mask.to(dev), **common, return_timestamps=False)
    torch.cuda.reset_peak_memory_stats()

    fp = open(pred_path, "a", encoding="utf-8")
    fs = open(args.out_dir / "segments.jsonl", "a", encoding="utf-8")
    n_new = 0
    for it in items:
        if it["id"] in done:
            continue
        audio = load_audio(it["audio"])
        dur = len(audio) / SR
        long_form = dur > 30.0
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        with torch.inference_mode():
            if not long_form:
                f = processor(audio, sampling_rate=SR, return_tensors="pt", truncation=False, padding="max_length", return_attention_mask=True)
                out = model.generate(f.input_features.to(dev, torch.float16), attention_mask=f.attention_mask.to(dev),
                                     **common, return_timestamps=False)
                seqs = out
                segs_log = None
            else:
                f = processor(audio, sampling_rate=SR, return_tensors="pt", truncation=False, padding="longest", return_attention_mask=True)
                out = model.generate(f.input_features.to(dev, torch.float16), attention_mask=f.attention_mask.to(dev),
                                     **common, return_timestamps=True, return_segments=True)
                seqs = out["sequences"]
                segs_log = [{"start": float(s["start"]), "end": float(s["end"]), "n_tokens": int(len(s["tokens"])),
                             "text": processor.tokenizer.decode(s["tokens"], skip_special_tokens=True)}
                            for s in out["segments"][0]]
        torch.cuda.synchronize()
        el = time.perf_counter() - t0
        text = processor.batch_decode(seqs, skip_special_tokens=True)[0].strip()
        n_tok = int(seqs.shape[-1])
        hit_cap = any(s["n_tokens"] >= 440 for s in segs_log) if segs_log else n_tok >= 440
        rec = {"id": it["id"], "reference": it["reference"], "prediction": text, "sent_id": it.get("sent_id"),
               "speaker_id": it.get("speaker_id"), "duration_s": dur, "long_form": long_form,
               "run_fingerprint": fingerprint}
        fp.write(json.dumps(rec, ensure_ascii=False) + "\n"); fp.flush()
        fs.write(json.dumps({"id": it["id"], "n_samples_input": len(audio), "n_frames": int(f.input_features.shape[-1]),
                             "duration_s": dur, "long_form": long_form, "n_output_tokens": n_tok, "hit_cap_440": hit_cap,
                             "segments": segs_log, "elapsed_s": el,
                             "coverage_end_s": (segs_log[-1]["end"] if segs_log else None),
                             "gpu_peak_allocated_bytes": torch.cuda.max_memory_allocated()}, ensure_ascii=False) + "\n"); fs.flush()
        n_new += 1
        if n_new % 50 == 0:
            print(f"[{args.run_id}] {len(done) + n_new}/{len(items)}", flush=True)
    fp.close(); fs.close()
    meta["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    meta["gpu_peak_allocated_bytes_this_session"] = torch.cuda.max_memory_allocated()
    (args.out_dir / "run_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{args.run_id}] xong: {len(done) + n_new}/{len(items)} (mới {n_new})")


if __name__ == "__main__":
    main()
