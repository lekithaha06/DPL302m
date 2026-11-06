#!/usr/bin/env python3
"""B1 – baseline end-to-end Whisper Translate: audio tiếng Việt → văn bản tiếng Anh (không qua transcript tiếng Việt).

Dựa trên code bàn giao của Đăng (DANG_BASELINE_HANDOFF/b1_whisper_translate/inference.py + run_fleurs_test.py).
để chạy đúng và so công bằng với B0 (protocol bao_asr_v1_20261027):
  - ghim revision whisper-small @973afd24 (cùng checkpoint Baseline 2 ASR của Task 2);
  - audio > 30 s KHÔNG bị cắt: long-form tuần tự của Transformers (truncation=False, return_timestamps=True) như B0;
    bản gốc gọi processor(audio) mặc định → chỉ giữ 30 s đầu (mất nội dung 7 bản dài);
  - cùng suppress tokens (configs/common_suppression_from_task1.json), fp16, beam 5, seed 42, max_new_tokens 440 như protocol;
  - đọc manifest/audio bằng utf-8 + soundfile (bản gốc dùng open() mặc định → lỗi tiếng Việt trên Windows; torchaudio không có trong venv);
  - xuất đúng schema chung của nhóm, ghi từng dòng (chạy lại bỏ qua mẫu đã xong).
Schema: sample_id, split, model_id, reference_vi, reference_en, pred_vi (NULL – B1 không có transcript Việt), pred_en,
        latency_s, audio_duration_s, status (+ sent_id, domain, long_form để gom cụm/phân tích).

Chạy:  $P scripts/b1/b1_whisper_translate.py --manifest <manifest_fleurs_test.jsonl> --out runs/b1/predictions_b1.jsonl [--limit 5]
"""
import argparse
import hashlib
import json
import random
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor

T = Path(__file__).resolve().parents[2]
MODEL, REV, SR = "openai/whisper-small", "973afd24965f72e36ca33b3055d56a652f456b4d", 16000
MODEL_ID = f"B1_whisper-small_translate@{REV[:8]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, type=Path, help="JSONL: sample_id, audio_path (tương đối với manifest), reference_vi, reference_en")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--suppress", type=Path, default=T / "configs/common_suppression_from_task1.json")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    random.seed(42); np.random.seed(42); torch.manual_seed(42); torch.cuda.manual_seed_all(42)
    rows = [json.loads(l) for l in open(a.manifest, encoding="utf-8") if l.strip()]
    rows = rows[: a.limit] if a.limit else rows
    a.out.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["sample_id"] for l in open(a.out, encoding="utf-8")} if a.out.exists() else set()
    dev = "cuda"
    proc = WhisperProcessor.from_pretrained(MODEL, revision=REV)
    model = WhisperForConditionalGeneration.from_pretrained(MODEL, revision=REV, torch_dtype=torch.float16).to(dev).eval()
    sup = json.loads(a.suppress.read_text(encoding="utf-8"))
    model.generation_config.suppress_tokens = sup["suppress_tokens"]
    model.generation_config.begin_suppress_tokens = sup["begin_suppress_tokens"]
    gen = dict(language="vi", task="translate", num_beams=5, do_sample=False, max_new_tokens=440)
    meta = {"model_id": MODEL_ID, "model": MODEL, "revision": REV, "generate": gen, "dtype": "float16", "seed": 42,
            "suppress_sha256": hashlib.sha256(a.suppress.read_bytes()).hexdigest(), "manifest": str(a.manifest),
            "manifest_sha256": hashlib.sha256(a.manifest.read_bytes()).hexdigest(), "gpu": torch.cuda.get_device_name(0),
            "torch": torch.__version__, "long_form": "> 30 s: truncation=False, padding=longest, return_timestamps=True (như B0)"}
    (a.out.parent / "run_metadata_b1.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    with torch.inference_mode():  # khởi động GPU, không tính vào latency
        f = proc(np.zeros(SR, dtype=np.float32), sampling_rate=SR, return_tensors="pt")
        model.generate(f.input_features.to(dev, torch.float16), **gen)
    base = a.manifest.parent
    with open(a.out, "a", encoding="utf-8") as fo:
        for k, r in enumerate(rows):
            if r["sample_id"] in done:
                continue
            out = {"sample_id": r["sample_id"], "split": r.get("split", "test"), "model_id": MODEL_ID, "reference_vi": r["reference_vi"],
                   "reference_en": r["reference_en"], "pred_vi": None, "pred_en": "", "latency_s": None, "audio_duration_s": r.get("audio_duration_s"),
                   "status": "ok", "sent_id": r.get("sent_id"), "domain": r.get("domain"), "long_form": None}
            try:
                audio, sr = sf.read(base / r["audio_path"], dtype="float32", always_2d=False)
                if audio.ndim > 1:
                    audio = audio.mean(axis=1)
                assert sr == SR, f"sample rate {sr} != {SR}"
                dur = len(audio) / SR; lf = dur > 30.0
                torch.cuda.synchronize(); t0 = time.perf_counter()
                with torch.inference_mode():
                    if not lf:
                        f = proc(audio, sampling_rate=SR, return_tensors="pt")
                        ids = model.generate(f.input_features.to(dev, torch.float16), **gen, return_timestamps=False)
                    else:
                        f = proc(audio, sampling_rate=SR, return_tensors="pt", truncation=False, padding="longest", return_attention_mask=True)
                        ids = model.generate(f.input_features.to(dev, torch.float16), attention_mask=f.attention_mask.to(dev), **gen, return_timestamps=True)
                torch.cuda.synchronize()
                out.update(pred_en=proc.batch_decode(ids, skip_special_tokens=True)[0].strip(), latency_s=round(time.perf_counter() - t0, 3),
                           audio_duration_s=round(dur, 2), long_form=lf)
            except Exception as e:  # ghi lỗi, không bỏ mẫu
                out.update(status=f"error: {type(e).__name__}: {e}"[:300])
            fo.write(json.dumps(out, ensure_ascii=False) + "\n"); fo.flush()
            if k % 100 == 0:
                print(f"  B1 {k}/{len(rows)}", flush=True)
    print("B1_XONG", a.out)


if __name__ == "__main__":
    main()
