"""Score an MT model (Baseline B or a LoRA version) on the fixed Task 2 test sets (TV2 area).

Test sets (never used for training or model selection):
  fleurs_cascade : PhoWhisper-small transcripts of FLEURS test (Task 1 run on the same RTX 4060 / same env) -> en
  fleurs_clean   : FLEURS test reference Vietnamese -> en
  phomt          : PhoMT test (19,151 pairs), only if --phomt is given; hypotheses stay in data/ (license)
Same decoding as Task 1 (fp16, beam 5, max_length 512) and sacreBLEU 2.6.0 (BLEU 13a, chrF++).
"""
import argparse, json, os, time
import torch, sacrebleu
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True, help="B0, V1, V2, ...")
ap.add_argument("--base", default="checkpoints/pretrained/vinai-translate-vi2en")
ap.add_argument("--adapter", default="", help="LoRA adapter dir; empty = Baseline B")
ap.add_argument("--fleurs", default="reports/task1/mt/predictions_fleurs_test.json")
ap.add_argument("--phomt", default="", help="PhoMT root (…/PhoMT) to also score PhoMT test")
ap.add_argument("--out", default="reports/task2/mt")
args = ap.parse_args()

torch.manual_seed(42)
tok = AutoTokenizer.from_pretrained(args.base, src_lang="vi_VN")
model = AutoModelForSeq2SeqLM.from_pretrained(args.base, torch_dtype=torch.float16)
if args.adapter:
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, args.adapter).merge_and_unload()
model = model.to("cuda").eval()
en_id = tok.convert_tokens_to_ids("en_XX")


def translate(texts):
    order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
    res, i = [None] * len(texts), 0
    t0 = time.time()
    while i < len(order):
        L = len(texts[order[i]])
        # batch 16/8/4: one looping hypothesis (512 tokens x 5 beams) in a batch of 32 overflowed 8 GB VRAM (V1, Task 2)
        bs = 16 if L < 300 else 8 if L < 600 else 4
        idx = order[i:i + bs]
        enc = tok([texts[j] for j in idx], padding=True, truncation=True, max_length=512, return_tensors="pt").to("cuda")
        # output cap = 2 x source tokens + 10 (<= 512): never reached by a normal translation, but stops a looping
        # hypothesis from filling 8 GB VRAM. Applied identically to every version, B0 included.
        cap = min(512, 2 * enc.input_ids.shape[1] + 10)
        with torch.no_grad():
            g = model.generate(**enc, decoder_start_token_id=en_id, num_beams=5, early_stopping=True, max_length=cap)
        for j, t in zip(idx, tok.batch_decode(g, skip_special_tokens=True)):
            res[j] = t
        i += len(idx)
    return res, time.time() - t0


def score(h, r):
    b = sacrebleu.metrics.BLEU(); c = sacrebleu.metrics.CHRF(word_order=2)
    return {"BLEU": round(b.corpus_score(h, [r]).score, 2), "chrF++": round(c.corpus_score(h, [r]).score, 2),
            "BLEU_signature": str(b.get_signature())}


os.makedirs(args.out, exist_ok=True)
rows = json.load(open(args.fleurs, encoding="utf-8"))
refs = [r["en_ref"] for r in rows]
result = {"name": args.name, "adapter": args.adapter or None, "gpu": torch.cuda.get_device_name(0), "torch": torch.__version__,
          "decoding": "fp16, beam 5, max_length min(512, 2*src_tokens+10), length-sorted batches 16/8/4 (<300/<600/longer chars)"}
preds = {}
for key, src in (("fleurs_cascade", [r["asr"] for r in rows]), ("fleurs_clean", [r["vi_raw"] for r in rows])):
    h, sec = translate(src)
    preds[key] = h
    result[key] = {**score(h, refs), "n": len(h), "seconds": round(sec, 1)}
    print(args.name, key, result[key], flush=True)

if args.phomt:
    d = f"{args.phomt}/detokenization/test/test"
    src = [l.rstrip("\n") for l in open(d + ".vi", encoding="utf-8")]
    ref = [l.rstrip("\n") for l in open(d + ".en", encoding="utf-8")]
    h, sec = translate(src)
    os.makedirs("data/phomt_hyp", exist_ok=True)  # derived from PhoMT: not committed
    json.dump(h, open(f"data/phomt_hyp/phomt_test_{args.name}.json", "w", encoding="utf-8"), ensure_ascii=False)
    result["phomt_test"] = {**score(h, ref), "n": len(h), "seconds": round(sec, 1)}
    print(args.name, "phomt_test", result["phomt_test"], flush=True)

json.dump(result, open(f"{args.out}/eval_{args.name}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump([{"id": r["id"], "audio": r["audio"], "asr": r["asr"], "en_ref": r["en_ref"],
            "cascade": preds["fleurs_cascade"][i], "clean": preds["fleurs_clean"][i]} for i, r in enumerate(rows)],
          open(f"{args.out}/predictions_{args.name}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved", flush=True)
