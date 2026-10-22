"""Transcribe a FLEURS split with PhoWhisper-small (Task 2, TV1 area).

The output is the training/validation data for Proposed Method V1: pairs (ASR transcript with real recognition errors
-> English reference). Decoding is identical to the Task 1 cascade (src/mt/run_cascade.py): transformers pipeline,
fp16, language=vi, task=transcribe, chunk_length_s=30, default generation config. Resumable: rows already in the
output JSONL are skipped, so the run can be stopped (machine shut down) and restarted.
"""
import argparse, json, os, platform, time
import torch, soundfile as sf, librosa
from transformers import pipeline

ap = argparse.ArgumentParser()
ap.add_argument("--eval-set", required=True, help="data/processed/fleurs_vi_en_<split>.json from data/build_fleurs_eval.py")
ap.add_argument("--model", default="checkpoints/pretrained/PhoWhisper-small")
ap.add_argument("--output", required=True, help="JSONL, one utterance per line")
args = ap.parse_args()

torch.manual_seed(42)
rows = json.load(open(args.eval_set, encoding="utf-8"))
done = set()
if os.path.exists(args.output):
    with open(args.output, encoding="utf-8") as f:
        done = {json.loads(l)["audio"] for l in f if l.strip()}
todo = [r for r in rows if os.path.basename(r["audio"]) not in done]
print(f"utterances={len(rows)} done={len(done)} todo={len(todo)} gpu={torch.cuda.get_device_name(0)}", flush=True)

asr = pipeline("automatic-speech-recognition", model=args.model, device=0, torch_dtype=torch.float16)
meta = {"gpu": torch.cuda.get_device_name(0), "torch": torch.__version__, "python": platform.python_version()}
os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
t_all = time.time()
with open(args.output, "a", encoding="utf-8") as out:
    for i, r in enumerate(todo):
        a, sr = sf.read(r["audio"])
        if a.ndim > 1: a = a.mean(1)
        if sr != 16000: a = librosa.resample(a, orig_sr=sr, target_sr=16000)
        t0 = time.time()
        text = asr({"raw": a.astype("float32"), "sampling_rate": 16000},
                   generate_kwargs={"language": "vi", "task": "transcribe"}, chunk_length_s=30)["text"].strip()
        out.write(json.dumps({"id": r["id"], "audio": os.path.basename(r["audio"]), "vi_raw": r["vi_raw"], "en_ref": r["en_ref"],
                              "asr": text, "duration_s": round(len(a) / 16000, 3), "decode_s": round(time.time() - t0, 3), **meta},
                             ensure_ascii=False) + "\n")
        if i % 25 == 0:
            out.flush()
            print(f"{len(done) + i + 1}/{len(rows)}  {time.time() - t_all:.0f}s", flush=True)
print("finished", args.output, flush=True)
