"""Recompute the Task 1 derived numbers from the committed prediction files (no GPU, no audio needed).

- FLEURS ASR WER/CER with the same normalization as the VIVOS run (CER without spaces) -> 12.21 / 8.58
- WER/CER split into substitutions, deletions, insertions (required by the course for ASR)
- VIVOS per-speaker WER range and mean utterance duration
- Whisper-small VIVOS WER with and without the looping utterance VIVOSDEV03_R193
"""
import argparse, json, statistics, sys, unicodedata
from collections import defaultdict
from jiwer import process_words, process_characters

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--reports", default="reports/task1")
ap.add_argument("--output", default="reports/task1/recomputed_metrics.json")
args = ap.parse_args()


def normalize(text):  # identical to src/asr/evaluate_asr.py
    text = unicodedata.normalize("NFC", text).lower()
    text = "".join(" " if unicodedata.category(ch)[0] in "PS" else ch for ch in text)
    return " ".join(text.split())


def wer_cer(refs, hyps):
    w = process_words(refs, hyps)
    c = process_characters([s.replace(" ", "") for s in refs], [s.replace(" ", "") for s in hyps])
    return {"n": len(refs), "WER": round(100 * w.wer, 2), "CER": round(100 * c.cer, 2),
            "word_S": w.substitutions, "word_D": w.deletions, "word_I": w.insertions,
            "word_ref": w.hits + w.substitutions + w.deletions}


out = {}

# FLEURS test (857 utterances): PhoWhisper-small output from the cascade run
fl = json.load(open(f"{args.reports}/mt/predictions_fleurs_test.json", encoding="utf-8"))
out["fleurs_PhoWhisper-small"] = wer_cer([normalize(r["vi_raw"]) for r in fl], [normalize(r["asr"]) for r in fl])

# VIVOS test (760 utterances, 19 speakers)
for name in ["PhoWhisper-small", "whisper-small"]:
    rows = [json.loads(s) for s in open(f"{args.reports}/asr/predictions_{name}.jsonl", encoding="utf-8")]
    m = wer_cer([r["reference_normalized"] for r in rows], [r["prediction_normalized"] for r in rows])
    by_spk = defaultdict(list)
    for r in rows:
        by_spk[r["speaker_id"]].append(r)
    spk = {s: wer_cer([r["reference_normalized"] for r in rs], [r["prediction_normalized"] for r in rs])["WER"] for s, rs in by_spk.items()}
    m["speakers"] = len(spk)
    m["speaker_WER_min"] = min(spk.items(), key=lambda kv: kv[1])
    m["speaker_WER_max"] = max(spk.items(), key=lambda kv: kv[1])
    m["mean_duration_s"] = round(statistics.mean(r["duration_seconds"] for r in rows), 2)
    if name == "whisper-small":
        keep = [r for r in rows if r["id"] != "VIVOSDEV03_R193"]
        m["WER_without_R193"] = wer_cer([r["reference_normalized"] for r in keep], [r["prediction_normalized"] for r in keep])["WER"]
    out[f"vivos_{name}"] = m

json.dump(out, open(args.output, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(out, ensure_ascii=False, indent=2))
