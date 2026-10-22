"""Evaluate both original small ASR checkpoints on the same frozen VIVOS test split."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import random
import statistics
import time
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from jiwer import process_words, process_characters
from faster_whisper import WhisperModel, BatchedInferencePipeline
from faster_whisper.audio import pad_or_trim
from faster_whisper.tokenizer import Tokenizer

def normalize(text):
    # Vietnamese diacritics are retained; CER excludes spaces, after this step.
    text = unicodedata.normalize("NFC", text).lower()
    text = "".join(" " if unicodedata.category(ch)[0] in "PS" else ch for ch in text)
    return " ".join(text.split())

def metrics(rows):
    refs = [r["reference_normalized"] for r in rows]
    hyps = [r["prediction_normalized"] for r in rows]
    words = process_words(refs, hyps)
    chars = process_characters([s.replace(" ", "") for s in refs], [s.replace(" ", "") for s in hyps])
    return {"n": len(rows), "wer_percent": 100 * words.wer, "cer_percent": 100 * chars.cer,
            "word_counts": {"substitutions": words.substitutions, "deletions": words.deletions,
                            "insertions": words.insertions, "hits": words.hits,
                            "reference_units": words.hits + words.substitutions + words.deletions},
            "character_counts": {"substitutions": chars.substitutions, "deletions": chars.deletions,
                                 "insertions": chars.insertions, "hits": chars.hits,
                                 "reference_units": chars.hits + chars.substitutions + chars.deletions}}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="data/vivos_test/manifest.jsonl")
    ap.add_argument("--models-dir", default=".work/models")
    ap.add_argument("--output", default="reports/baseline_asr.json")
    ap.add_argument("--limit", type=int, default=0, help="0 means full test; positive means sorted first N")
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--beam-size", type=int, default=5)
    ap.add_argument("--batch-size", type=int, default=8)
    args = ap.parse_args()
    random.seed(42)
    np.random.seed(42)
    manifest_path = Path(args.manifest)
    items = [json.loads(s) for s in manifest_path.read_text(encoding="utf-8").splitlines()]
    if args.limit:
        items = items[:args.limit]
    ids = [r["id"] for r in items]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate test IDs")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    config = {"device": "cpu", "compute_type": "int8", "cpu_threads": args.threads,
              "beam_size": args.beam_size, "temperature": 0.0, "language": "vi", "task": "transcribe",
              "condition_on_previous_text": False, "vad_filter": False, "without_timestamps": True,
              "compression_ratio_threshold": None, "log_prob_threshold": None, "no_speech_threshold": None,
              "seed": 42, "batch_size": args.batch_size,
              "decoding_api": "faster-whisper 1.1.1 BatchedInferencePipeline.generate_segment_batched"}
    report = {"status": "running", "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "dataset": json.loads((manifest_path.parent / "provenance.json").read_text()),
              "selection": {"n": len(items), "policy": "all official test" if not args.limit else "first N sorted IDs",
                            "ids": ids},
              "normalization": {"name": "NFC lowercase punctuation_symbols_to_spaces collapse_whitespace",
                                "preserve_diacritics": True, "cer_whitespace": "removed",
                                "wer_unit": "whitespace-delimited Vietnamese syllable-like token",
                                "aggregation": "corpus micro sum(S+D+I)/sum(N)"},
              "configuration": config, "environment": {"python": platform.python_version(), "os": platform.platform(),
                            "cpu_logical_count": os.cpu_count(), "processor": platform.processor(),
                            "packages": {p: importlib.metadata.version(p) for p in
                                         ["torch", "transformers", "faster-whisper", "ctranslate2", "jiwer", "numpy", "soundfile", "scipy", "huggingface-hub"]}},
              "paper_comparison": {"PhoWhisper-small": {"vivos_wer_percent": 6.33, "vivos_cer_percent": None,
                 "source": "https://arxiv.org/pdf/2406.02555", "location": "Table 2 page 2"},
                 "whisper-small": {"vivos_wer_percent": None, "vivos_cer_percent": None,
                    "reason": "VIVOS is not reported in the Whisper paper"}},
              "comparability": "Publisher weights converted to CTranslate2 int8; paper decoding and text normalization are not fully specified. This is a rerun with disclosed settings, not exact protocol reproduction.",
              "models": {}}
    def save():
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    save()
    for name in ["PhoWhisper-small", "whisper-small"]:
        model_dir = Path(args.models_dir) / name
        provenance = json.loads((model_dir / "provenance.json").read_text())
        model_size = (model_dir / "model.bin").stat().st_size
        fingerprint = hashlib.sha256(json.dumps({"ids": ids, "config": config, "model": provenance,
                         "manifest_sha256": report["dataset"]["manifest_sha256"], "normalization": report["normalization"]}, sort_keys=True).encode()).hexdigest()
        prediction_path = output.parent / f"predictions_{name}.jsonl"
        rows = []
        if prediction_path.exists():
            rows = [json.loads(s) for s in prediction_path.read_text(encoding="utf-8").splitlines()]
            if any(r["run_fingerprint"] != fingerprint for r in rows):
                raise ValueError(f"Existing predictions use another configuration: {prediction_path}")
        done = {r["id"] for r in rows}
        print(f"Loading {name}; completed {len(done)}/{len(items)}", flush=True)
        model = WhisperModel(str(model_dir), device="cpu", compute_type="int8", cpu_threads=args.threads, num_workers=1)
        # Excluded warm-up uses silence, not a test utterance.
        warm, info = model.transcribe(np.zeros(16000, dtype=np.float32), language="vi", task="transcribe",
                   beam_size=args.beam_size, temperature=0.0, condition_on_previous_text=False,
                   vad_filter=False, without_timestamps=True, compression_ratio_threshold=None,
                   log_prob_threshold=None, no_speech_threshold=None)
        list(warm)
        pipeline = BatchedInferencePipeline(model)
        tokenizer = Tokenizer(model.hf_tokenizer, model.model.is_multilingual, task="transcribe", language="vi")
        pending = [item for item in items if item["id"] not in done]
        with prediction_path.open("a", encoding="utf-8") as handle:
            for offset in range(0, len(pending), args.batch_size):
                batch = pending[offset:offset + args.batch_size]
                audios, durations = [], []
                for item in batch:
                    audio_path = Path(item["audio"])
                    if hashlib.sha256(audio_path.read_bytes()).hexdigest() != item["audio_sha256"]:
                        raise ValueError("Audio content changed")
                    audio, sr = sf.read(audio_path, dtype="float32", always_2d=True)
                    duration = len(audio) / sr
                    if duration > 30:
                        raise ValueError("Batched short-utterance evaluation supports <=30 seconds only")
                    audio = audio.mean(axis=1)
                    if sr != 16000:
                        import math
                        g = math.gcd(sr, 16000)
                        audio = resample_poly(audio, 16000 // g, sr // g).astype(np.float32)
                    audios.append(audio)
                    durations.append(duration)
                started = time.perf_counter()
                features = np.stack([pad_or_trim(model.feature_extractor(audio), 3000) for audio in audios])
                _, generated = pipeline.generate_segment_batched(features, tokenizer, info.transcription_options)
                predictions = [tokenizer.decode(result["tokens"]).strip() for result in generated]
                elapsed = time.perf_counter() - started
                for item, prediction, duration in zip(batch, predictions, durations):
                    row = {"id": item["id"], "speaker_id": item["speaker_id"], "reference": item["reference"],
                           "prediction": prediction, "reference_normalized": normalize(item["reference"]),
                           "prediction_normalized": normalize(prediction), "duration_seconds": duration,
                           "inference_seconds": elapsed / len(batch), "batch_inference_seconds": elapsed,
                           "batch_id": batch[0]["id"], "batch_size_actual": len(batch), "run_fingerprint": fingerprint}
                    row["utterance_wer_percent"] = metrics([row])["wer_percent"]
                    rows.append(row)
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                handle.flush()
                if len(rows) % 40 == 0 or len(rows) == len(items):
                    print(f"{name} {len(rows)}/{len(items)}; elapsed inference {sum(r['inference_seconds'] for r in rows):.1f}s", flush=True)
        del pipeline, model
        if {r["id"] for r in rows} != set(ids):
            raise ValueError("Incomplete or extra predictions")
        rows.sort(key=lambda r: r["id"])
        m = metrics(rows)
        groups = defaultdict(list)
        for row in rows:
            groups[row["speaker_id"]].append(row)
        audio_total = sum(r["duration_seconds"] for r in rows)
        inference_total = sum(r["inference_seconds"] for r in rows)
        report["models"][name] = {"status": "completed", "source": provenance, "metrics": m,
             "timing": {"total_audio_seconds": audio_total, "total_inference_seconds": inference_total,
                        "rtf": inference_total / audio_total, "amortized_seconds_per_utterance_median": statistics.median(r["inference_seconds"] for r in rows),
                        "batch_latency_median_seconds": statistics.median(r["batch_inference_seconds"] for r in rows[::args.batch_size]),
                        "batch_latency_p95_seconds": float(np.percentile([r["batch_inference_seconds"] for r in rows[::args.batch_size]],95)),
                        "scope": "batched feature extraction and decode; excludes file IO, loading, warmup, queue wait and MT. RTF is throughput, not streaming latency."},
             "converted_weight_bytes": model_size, "speaker_metrics": {sp: metrics(rs) for sp,rs in groups.items()},
             "worst_examples": sorted(rows, key=lambda r: r["utterance_wer_percent"], reverse=True)[:10],
             "predictions_file": prediction_path.name, "predictions_sha256": hashlib.sha256(prediction_path.read_bytes()).hexdigest()}
        save()
        print(f"COMPLETED {name}: WER {m['wer_percent']:.4f}% CER {m['cer_percent']:.4f}% RTF {inference_total/audio_total:.3f}", flush=True)
    report["status"] = "completed"
    report["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["comparison"] = {"relative_wer_reduction_percent": 100 * (report["models"]["whisper-small"]["metrics"]["wer_percent"] - report["models"]["PhoWhisper-small"]["metrics"]["wer_percent"]) / report["models"]["whisper-small"]["metrics"]["wer_percent"]}
    save()

if __name__ == "__main__":
    main()
