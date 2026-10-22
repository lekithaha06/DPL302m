"""Reproduce paper Table 1: VinAI Translate VI-EN BLEU on the PhoMT test set (paper 40.42, Task 1 rerun 40.25).

PhoMT is gated (research/education only, no redistribution): download PhoMT.zip yourself from
https://huggingface.co/datasets/vinai/PhoMT and extract it to --phomt. Hypotheses on the PhoMT test set are written
outside Git (data/ is ignored) because they are derived from the restricted data.
Length-adaptive batches (long sentences -> small batches) and resumable checkpoints.
"""
import argparse, json, os, time, torch, sacrebleu
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

ap = argparse.ArgumentParser()
ap.add_argument("split", nargs="?", default="test")
ap.add_argument("--phomt", default="data/phomt/PhoMT")
ap.add_argument("--models-dir", default="checkpoints/pretrained")
ap.add_argument("--models", default="vinai-translate-vi2en")
ap.add_argument("--hyp-dir", default="data/phomt_hyp")
ap.add_argument("--out", default="reports/task1/mt")
args = ap.parse_args()

torch.manual_seed(42)
D = f"{args.phomt}/detokenization/{args.split}/{args.split}"
src = [l.rstrip("\n") for l in open(D + ".vi", encoding="utf-8")]
ref = [l.rstrip("\n") for l in open(D + ".en", encoding="utf-8")]
assert len(src) == len(ref)
os.makedirs(args.hyp_dir, exist_ok=True)
os.makedirs(args.out, exist_ok=True)
print(args.split, "sentences:", len(src), flush=True)


def batches(order, texts):
    i = 0
    while i < len(order):
        L = len(texts[order[i]])
        bs = 32 if L < 300 else 12 if L < 600 else 4
        j = i
        while j < len(order) and j - i < bs and len(texts[order[j]]) < (300 if bs == 32 else 600 if bs == 12 else 10**9):
            j += 1
        j = max(j, i + 1)
        yield order[i:j]
        i = j


res = {"split": args.split, "n": len(src)}
for name in args.models.split(","):
    md = f"{args.models_dir}/{name}"
    ck = f"{args.hyp_dir}/phomt_{args.split}_{name}_hyp.json"
    hyp = json.load(open(ck, encoding="utf-8")) if os.path.exists(ck) else [None] * len(src)
    tok = AutoTokenizer.from_pretrained(md, src_lang="vi_VN")
    model = AutoModelForSeq2SeqLM.from_pretrained(md, torch_dtype=torch.float16).to("cuda").eval()
    en_id = tok.convert_tokens_to_ids("en_XX")
    order = [i for i in sorted(range(len(src)), key=lambda i: len(src[i])) if hyp[i] is None]
    t0, n = time.time(), 0
    for idx in batches(order, src):
        enc = tok([src[i] for i in idx], padding=True, truncation=True, max_length=512, return_tensors="pt").to("cuda")
        with torch.no_grad():
            g = model.generate(**enc, decoder_start_token_id=en_id, num_beams=5, early_stopping=True, max_length=512)
        for i, t in zip(idx, tok.batch_decode(g, skip_special_tokens=True)):
            hyp[i] = t
        n += 1
        if n % 40 == 0:
            json.dump(hyp, open(ck, "w", encoding="utf-8"), ensure_ascii=False)
            print(name, sum(h is not None for h in hyp), "/", len(src), round(time.time() - t0), "s", flush=True)
    json.dump(hyp, open(ck, "w", encoding="utf-8"), ensure_ascii=False)
    bm = sacrebleu.metrics.BLEU(); cm = sacrebleu.metrics.CHRF(word_order=2)
    b, c = bm.corpus_score(hyp, [ref]), cm.corpus_score(hyp, [ref])
    res[name] = {"BLEU": round(b.score, 2), "chrF++": round(c.score, 2), "seconds": round(time.time() - t0, 1),
                 "BLEU_signature": str(bm.get_signature())}
    print(name, res[name], flush=True)
    del model; torch.cuda.empty_cache()
    json.dump(res, open(f"{args.out}/baseline_phomt_{args.split}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved")
