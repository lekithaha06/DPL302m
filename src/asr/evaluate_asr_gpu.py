"""Run original publisher Whisper/PhoWhisper weights through Transformers on CUDA FP16."""
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import random
import statistics
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import soundfile as sf
import torch
from scipy.signal import resample_poly
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from evaluate_asr import normalize, metrics

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="data/vivos_test/manifest.jsonl")
    ap.add_argument("--source-dir", default=".work/source_models")
    ap.add_argument("--output", default="reports/baseline_asr.json")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable; use evaluate_asr.py for the separate CPU INT8 configuration")
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    torch.set_num_threads(4)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    path = Path(args.manifest)
    items = [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines()]
    if args.limit:
        items = items[:args.limit]
    ids = [r["id"] for r in items]
    assert len(ids) == len(set(ids))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    common_generation = json.loads((Path(args.source_dir) / "whisper-small" / "generation_config.json").read_text())
    config = {"backend": "transformers", "device": "cuda", "precision": "float16", "batch_size": 1,
              "beam_size": 5, "do_sample": False, "language": "vi", "task": "transcribe",
              "return_timestamps": False, "condition_on_previous_text": False, "vad_filter": False,
              "return_attention_mask": True,
              "max_new_tokens": 440, "seed": 42, "cpu_threads": 4,
              "suppress_tokens": common_generation["suppress_tokens"],
              "begin_suppress_tokens": common_generation["begin_suppress_tokens"]}
    report = {"status": "running", "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "dataset": json.loads((path.parent / "provenance.json").read_text()),
              "selection": {"n": len(items), "policy": "all official test" if not args.limit else "first N sorted IDs", "ids": ids},
              "configuration": config,
              "normalization": {"name": "NFC lowercase punctuation_symbols_to_spaces collapse_whitespace", "preserve_diacritics": True,
                  "cer_whitespace": "removed", "wer_unit": "whitespace-delimited Vietnamese syllable-like token",
                  "aggregation": "corpus micro sum(S+D+I)/sum(N)"},
              "environment": {"python": platform.python_version(), "os": platform.platform(),
                  "processor": platform.processor(), "cpu_logical_count": os.cpu_count(),
                  "gpu": torch.cuda.get_device_name(0), "gpu_total_bytes": torch.cuda.get_device_properties(0).total_memory,
                  "cuda_build": torch.version.cuda, "cudnn": torch.backends.cudnn.version(),
                  "packages": {p: importlib.metadata.version(p) for p in
                      ["torch", "transformers", "faster-whisper", "ctranslate2", "jiwer", "numpy", "soundfile", "scipy", "huggingface-hub"]}},
              "paper_comparison": {"PhoWhisper-small": {"vivos_wer_percent": 6.33, "vivos_cer_percent": None,
                 "source": "https://arxiv.org/pdf/2406.02555", "location": "Table 2 page 2"},
                 "whisper-small": {"vivos_wer_percent": None, "vivos_cer_percent": None,
                    "reason": "VIVOS is not reported in the Whisper paper"}},
              "comparability": "Original publisher checkpoints loaded directly in Transformers, CUDA FP16. Paper decoding and normalization are not fully specified; this is a rerun with disclosed settings, not exact protocol reproduction.",
              "models": {}}
    def save():
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    save()
    for name in ["PhoWhisper-small", "whisper-small"]:
        source = Path(args.source_dir) / name
        provenance = json.loads((source / "source_provenance.json").read_text())
        fingerprint = hashlib.sha256(json.dumps({"ids": ids, "config": config, "model": provenance,
            "manifest_sha256": report["dataset"]["manifest_sha256"], "normalization": report["normalization"]}, sort_keys=True).encode()).hexdigest()
        predpath = out.parent / f"predictions_{name}.jsonl"
        rows = [json.loads(s) for s in predpath.read_text(encoding="utf-8").splitlines()] if predpath.exists() else []
        if any(r["run_fingerprint"] != fingerprint for r in rows):
            raise ValueError("Prediction file configuration mismatch")
        done = {r["id"] for r in rows}
        processor = WhisperProcessor.from_pretrained(source)
        model = WhisperForConditionalGeneration.from_pretrained(source, torch_dtype=torch.float16, attn_implementation="eager").to("cuda").eval()
        # Task 2: same environment as Baseline B (transformers 5.x), where forced_decoder_ids is no longer accepted;
        # language/task select the same <|vi|><|transcribe|><|notimestamps|> prompt.
        genargs = {"language": "vi", "task": "transcribe", "num_beams": 5, "do_sample": False, "max_new_tokens": 440,
                   "return_timestamps": False, "suppress_tokens": config["suppress_tokens"],
                   "begin_suppress_tokens": config["begin_suppress_tokens"]}
        def decode(audio):
            inputs = processor(audio, sampling_rate=16000, return_tensors="pt", return_attention_mask=True)
            feats = inputs.input_features.to("cuda", dtype=torch.float16)
            with torch.inference_mode():
                generated = model.generate(feats, attention_mask=inputs.attention_mask.to("cuda"), **genargs)
            return processor.batch_decode(generated, skip_special_tokens=True)[0].strip()
        print(f"CUDA loading {name}, remaining {len(items)-len(done)}", flush=True)
        decode(np.zeros(16000, dtype=np.float32))
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        with predpath.open("a", encoding="utf-8") as handle:
            for item in items:
                if item["id"] in done:
                    continue
                audiofile = Path(item["audio"])
                if hashlib.sha256(audiofile.read_bytes()).hexdigest() != item["audio_sha256"]:
                    raise ValueError("Audio changed")
                audio, sr = sf.read(audiofile, dtype="float32", always_2d=True)
                duration = len(audio) / sr
                audio = audio.mean(axis=1)
                if sr != 16000:
                    g = math.gcd(sr, 16000)
                    audio = resample_poly(audio, 16000//g, sr//g).astype(np.float32)
                torch.cuda.synchronize()
                started = time.perf_counter()
                prediction = decode(audio)
                torch.cuda.synchronize()
                elapsed = time.perf_counter() - started
                row = {"id": item["id"], "speaker_id": item["speaker_id"], "reference": item["reference"],
                    "prediction": prediction, "reference_normalized": normalize(item["reference"]),
                    "prediction_normalized": normalize(prediction), "duration_seconds": duration,
                    "inference_seconds": elapsed, "run_fingerprint": fingerprint}
                row["utterance_wer_percent"] = metrics([row])["wer_percent"]
                rows.append(row)
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                handle.flush()
                if len(rows) % 50 == 0 or len(rows) == len(items):
                    print(f"{name} {len(rows)}/{len(items)}; inference {sum(r['inference_seconds'] for r in rows):.1f}s", flush=True)
        peak_alloc, peak_reserved = torch.cuda.max_memory_allocated(), torch.cuda.max_memory_reserved()
        del model
        torch.cuda.empty_cache()
        if {r["id"] for r in rows} != set(ids):
            raise ValueError("Incomplete or extra predictions")
        rows.sort(key=lambda r: r["id"])
        groups = defaultdict(list)
        for row in rows:
            groups[row["speaker_id"]].append(row)
        duration = sum(r["duration_seconds"] for r in rows)
        elapsed = sum(r["inference_seconds"] for r in rows)
        m = metrics(rows)
        report["models"][name] = {"status": "completed", "source": provenance, "metrics": m,
            "timing": {"total_audio_seconds": duration, "total_inference_seconds": elapsed, "rtf": elapsed / duration,
                 "latency_median_seconds": statistics.median(r["inference_seconds"] for r in rows),
                 "latency_p95_seconds": float(np.percentile([r["inference_seconds"] for r in rows],95)),
                 "scope": "single-utterance feature extraction, host-to-device transfer, generation and text decoding; excludes file IO, model load, warmup, queue wait and MT"},
            "original_checkpoint_bytes": (source / provenance["source_weight_file"]).stat().st_size,
            "gpu_peak_allocated_bytes": peak_alloc, "gpu_peak_reserved_bytes": peak_reserved,
            "speaker_metrics": {sp: metrics(rs) for sp,rs in groups.items()},
            "worst_examples": sorted(rows,key=lambda r: r["utterance_wer_percent"],reverse=True)[:10],
            "predictions_file": predpath.name, "predictions_sha256": hashlib.sha256(predpath.read_bytes()).hexdigest()}
        save()
        print(f"COMPLETED {name} WER {m['wer_percent']:.4f}% CER {m['cer_percent']:.4f}% RTF {elapsed/duration:.3f}", flush=True)
    report["status"] = "completed"
    report["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["comparison"] = {"relative_wer_reduction_percent": 100 * (report["models"]["whisper-small"]["metrics"]["wer_percent"] - report["models"]["PhoWhisper-small"]["metrics"]["wer_percent"]) / report["models"]["whisper-small"]["metrics"]["wer_percent"]}
    save()

if __name__ == "__main__":
    main()
