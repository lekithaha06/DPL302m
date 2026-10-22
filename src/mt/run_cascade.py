"""Baseline B (VinAI Translate vi->en) on FLEURS vi_vn test: clean transcripts and cascade with PhoWhisper-small.

Task 1 result (RTX 4060 Laptop 8 GB, fp16, beam 5): clean BLEU 37.89, cascade BLEU 24.27, ASR WER 12.21%.
Only `vinai-translate-vi2en` (the paper model) is the baseline. `vinai-translate-vi2en-v2` was run on FLEURS for
reference only: its extra training data (mTet-v2) overlaps the PhoMT test set, so it is excluded (leakage L2).
"""
import argparse, json, os, re, time, unicodedata
import torch, soundfile as sf, librosa, jiwer, sacrebleu
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

ap = argparse.ArgumentParser()
ap.add_argument("--eval-set", default="data/processed/fleurs_vi_en_test.json")
ap.add_argument("--models-dir", default="checkpoints/pretrained")
ap.add_argument("--mt-models", default="vinai-translate-vi2en", help="comma-separated folder names under --models-dir")
ap.add_argument("--asr-model", default="PhoWhisper-small")
ap.add_argument("--out", default="reports/task1/mt")
ap.add_argument("--limit", type=int, default=0)
args = ap.parse_args()

dev = "cuda"
torch.manual_seed(42)
rows = json.load(open(args.eval_set, encoding="utf-8"))
if args.limit:
    rows = rows[:args.limit]
os.makedirs(args.out, exist_ok=True)
mt_models = args.mt_models.split(",")
print("utterances:", len(rows), flush=True)


def norm_vi(s):  # for WER: lowercase, strip punctuation
    s = unicodedata.normalize("NFC", s.lower())
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def translate(model_dir, texts, bs=16, beams=5):
    tok = AutoTokenizer.from_pretrained(model_dir, src_lang="vi_VN")
    model = AutoModelForSeq2SeqLM.from_pretrained(model_dir, torch_dtype=torch.float16).to(dev).eval()
    en_id = tok.convert_tokens_to_ids("en_XX")
    t0 = time.time()
    order = sorted(range(len(texts)), key=lambda i: len(texts[i]))  # length-sorted batching
    res = [None] * len(texts)
    for s in range(0, len(order), bs):
        idx = order[s:s + bs]
        enc = tok([texts[i] for i in idx], padding=True, truncation=True, max_length=512, return_tensors="pt").to(dev)
        with torch.no_grad():
            g = model.generate(**enc, decoder_start_token_id=en_id, num_beams=beams, early_stopping=True, max_length=512)
        for i, t in zip(idx, tok.batch_decode(g, skip_special_tokens=True)):
            res[i] = t
    el = time.time() - t0
    del model; torch.cuda.empty_cache()
    return res, el


def score(hyp, ref):
    bm, cm = sacrebleu.metrics.BLEU(), sacrebleu.metrics.CHRF(word_order=2)  # chrF++
    b, c = bm.corpus_score(hyp, [ref]), cm.corpus_score(hyp, [ref])
    return {"BLEU": round(b.score, 2), "chrF++": round(c.score, 2),
            "BLEU_signature": str(bm.get_signature()), "chrF++_signature": str(cm.get_signature())}


refs = [r["en_ref"] for r in rows]
result = {"n_utterances": len(rows), "n_unique_sentences": len({r["id"] for r in rows}),
          "torch": torch.__version__, "gpu": torch.cuda.get_device_name(0)}

# ---- 1. MT on clean transcripts (upper bound for the MT block)
clean = [r["vi_raw"] for r in rows]
hyps = {}
for name in mt_models:
    h, el = translate(f"{args.models_dir}/{name}", clean)
    hyps[f"clean__{name}"] = h
    result[f"clean__{name}"] = {**score(h, refs), "seconds": round(el, 1)}
    print(name, "clean", result[f"clean__{name}"], flush=True)

# ---- 2. ASR: PhoWhisper-small (resumable)
asr = pipeline("automatic-speech-recognition", model=f"{args.models_dir}/{args.asr_model}", device=0, torch_dtype=torch.float16)
ASR_CK = f"{args.out}/asr_checkpoint.json"  # {"out": [...], "dur": seconds_of_audio_done, "sec": decode_seconds_done}
ck = json.load(open(ASR_CK, encoding="utf-8")) if os.path.exists(ASR_CK) else {"out": [], "dur": 0.0, "sec": 0.0}
asr_out, dur, prev_sec = ck["out"][:len(rows)], ck["dur"], ck["sec"]
if asr_out: print("resuming ASR from", len(asr_out), flush=True)
t0 = time.time()
for i in range(len(asr_out), len(rows)):
    a, sr = sf.read(rows[i]["audio"])
    if a.ndim > 1: a = a.mean(1)
    if sr != 16000: a = librosa.resample(a, orig_sr=sr, target_sr=16000)
    dur += len(a) / 16000
    asr_out.append(asr({"raw": a.astype("float32"), "sampling_rate": 16000}, generate_kwargs={"language": "vi", "task": "transcribe"}, chunk_length_s=30)["text"].strip())
    if i % 50 == 0:
        json.dump({"out": asr_out, "dur": dur, "sec": prev_sec + time.time() - t0}, open(ASR_CK, "w", encoding="utf-8"), ensure_ascii=False)
        print("asr", i, flush=True)
json.dump({"out": asr_out, "dur": dur, "sec": prev_sec + time.time() - t0}, open(ASR_CK, "w", encoding="utf-8"), ensure_ascii=False)
asr_sec = prev_sec + time.time() - t0
del asr; torch.cuda.empty_cache()
ref_n = [norm_vi(r["vi_raw"]) for r in rows]
hyp_n = [norm_vi(t) for t in asr_out]
# CER here counts spaces; the official Task 1 CER (8.58%, spaces removed) comes from src/eval/recompute_metrics.py.
# RTF here is NOT reliable (GPU was shared during the Task 1 run) and is not quoted anywhere.
result["asr_" + args.asr_model] = {"WER": round(jiwer.wer(ref_n, hyp_n) * 100, 2), "CER": round(jiwer.cer(ref_n, hyp_n) * 100, 2),
                                   "seconds": round(asr_sec, 1), "audio_seconds": round(dur, 1), "RTF": round(asr_sec / dur, 3)}
print(result["asr_" + args.asr_model], flush=True)

# ---- 3. Cascade: PhoWhisper -> VinAI Translate
for name in mt_models:
    h, el = translate(f"{args.models_dir}/{name}", asr_out)
    hyps[f"cascade__{name}"] = h
    result[f"cascade__{name}"] = {**score(h, refs), "seconds": round(el, 1)}
    print(name, "cascade", result[f"cascade__{name}"], flush=True)

json.dump(result, open(f"{args.out}/baseline_cascade.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump([{**r, "audio": os.path.basename(r["audio"]), "asr": asr_out[i], **{k: v[i] for k, v in hyps.items()}} for i, r in enumerate(rows)],
          open(f"{args.out}/predictions_fleurs_test.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved")
