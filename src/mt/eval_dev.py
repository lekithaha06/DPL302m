"""Task 2 · chấm trên FLEURS dev (chữ máy nghe) để quyết định thay đổi ở bước suy luận (V3: chuẩn hóa số) mà không nhìn test.

Cùng cấu hình giải mã với eval_mt.py. Ghi reports/task2/mt/dev_<name>.json.
"""
import argparse, json, os, sys
import torch, sacrebleu
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True)
ap.add_argument("--adapter", default="")
ap.add_argument("--itn", action="store_true", help="apply src/text/itn_vi.py to ASR transcripts before translating")
ap.add_argument("--dev", default="data/asr/fleurs_dev_asr.jsonl")
ap.add_argument("--base", default="checkpoints/pretrained/vinai-translate-vi2en")
args = ap.parse_args()
sys.path.insert(0, "src/text")
from itn_vi import itn

rows = [json.loads(l) for l in open(args.dev, encoding="utf-8") if l.strip()]
src = [itn(r["asr"]) if args.itn else r["asr"] for r in rows]
ref = [r["en_ref"] for r in rows]
tok = AutoTokenizer.from_pretrained(args.base, src_lang="vi_VN")
en_id = tok.convert_tokens_to_ids("en_XX")
m = AutoModelForSeq2SeqLM.from_pretrained(args.base, torch_dtype=torch.float16)
if args.adapter:
    from peft import PeftModel
    m = PeftModel.from_pretrained(m, args.adapter).merge_and_unload()
m = m.to("cuda").eval()
order = sorted(range(len(src)), key=lambda i: len(src[i]))
hyp, i = [None] * len(src), 0
while i < len(order):
    L = len(src[order[i]]); bs = 16 if L < 300 else 8 if L < 600 else 4
    b = order[i:i + bs]
    enc = tok([src[j] for j in b], padding=True, truncation=True, max_length=512, return_tensors="pt").to("cuda")
    with torch.no_grad():
        g = m.generate(**enc, decoder_start_token_id=en_id, num_beams=5, early_stopping=True,
                       max_length=min(512, 2 * enc.input_ids.shape[1] + 10))
    for j, t in zip(b, tok.batch_decode(g, skip_special_tokens=True)):
        hyp[j] = t
    i += len(b)
res = {"name": args.name, "adapter": args.adapter or None, "itn": args.itn, "n": len(src),
       "itn_changed_inputs": sum(itn(r["asr"]) != r["asr"] for r in rows),
       "BLEU": round(sacrebleu.corpus_bleu(hyp, [ref]).score, 2), "chrF++": round(sacrebleu.corpus_chrf(hyp, [ref], word_order=2).score, 2)}
os.makedirs("reports/task2/mt", exist_ok=True)
json.dump(res, open(f"reports/task2/mt/dev_{args.name}.json", "w"), indent=2)
print(res, flush=True)
