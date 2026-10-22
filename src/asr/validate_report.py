"""Check evidence completeness and recompute corpus WER/CER independently of jiwer."""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

def distance(a, b):
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        current = [i]
        for j, y in enumerate(b, 1):
            current.append(min(current[-1]+1, previous[j]+1, previous[j-1]+(x != y)))
        previous = current
    return previous[-1]

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="reports/task1/asr/baseline_asr.json")
    ap.add_argument("--source-dir", default=".work/source_models")
    args = ap.parse_args()
    path = Path(args.report)
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["status"] == "completed"
    assert report["selection"]["n"] == 760
    expected = set(report["selection"]["ids"])
    checks = {"status": "passed", "n": 760, "independent_metric_implementation": "Python dynamic-programming Levenshtein", "models": {}}
    rows_by_model = {}
    for name, model in report["models"].items():
        predpath = path.parent / model["predictions_file"]
        assert sha256(predpath) == model["predictions_sha256"]
        rows = [json.loads(s) for s in predpath.read_text(encoding="utf-8").splitlines()]
        assert len(rows) == model["metrics"]["n"] == 760
        assert {r["id"] for r in rows} == expected
        assert len({r["speaker_id"] for r in rows}) == 19
        assert len({r["run_fingerprint"] for r in rows}) == 1
        word_errors = sum(distance(r["reference_normalized"].split(), r["prediction_normalized"].split()) for r in rows)
        word_total = sum(len(r["reference_normalized"].split()) for r in rows)
        char_errors = sum(distance(r["reference_normalized"].replace(" ",""), r["prediction_normalized"].replace(" ","")) for r in rows)
        char_total = sum(len(r["reference_normalized"].replace(" ","")) for r in rows)
        assert math.isclose(100*word_errors/word_total, model["metrics"]["wer_percent"], abs_tol=1e-10)
        assert math.isclose(100*char_errors/char_total, model["metrics"]["cer_percent"], abs_tol=1e-10)
        assert math.isclose(sum(r["duration_seconds"] for r in rows), model["timing"]["total_audio_seconds"], abs_tol=1e-8)
        assert math.isclose(sum(r["inference_seconds"] for r in rows), model["timing"]["total_inference_seconds"], abs_tol=1e-8)
        source = Path(args.source_dir) / name / model["source"]["source_weight_file"]
        model["original_checkpoint_sha256"] = sha256(source)
        checks["models"][name] = {"n": len(rows), "word_errors": word_errors, "reference_tokens": word_total,
            "character_errors": char_errors, "reference_characters": char_total,
            "wer_percent": 100*word_errors/word_total, "cer_percent": 100*char_errors/char_total,
            "checksum_verified": True, "no_duplicate_or_missing_ids": True}
        rows_by_model[name] = {r["id"]: r for r in rows}
    for uid in expected:
        a = rows_by_model["PhoWhisper-small"][uid]
        b = rows_by_model["whisper-small"][uid]
        assert a["reference_normalized"] == b["reference_normalized"]
        assert a["duration_seconds"] == b["duration_seconds"]
    report["verification"] = {"complete_official_test": True, "same_test_and_references": True,
                              "independent_wer_cer_check": True, "prediction_checksums_verified": True}
    if report["configuration"]["device"] == "cuda":
        try:
            driver = subprocess.check_output(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"], text=True).strip().splitlines()[0]
            report["environment"]["nvidia_driver_version_at_validation"] = driver
        except (OSError, subprocess.CalledProcessError):
            pass
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    checks["final_report_sha256"] = sha256(path)
    (path.parent / "validation_asr.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(checks, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
