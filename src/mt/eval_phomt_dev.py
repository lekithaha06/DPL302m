"""Task 2 · chọn phiên bản cuối trên VALIDATION (không dùng test): BLEU trên N câu PhoMT dev lấy ngẫu nhiên (seed 42).

Tiêu chí chọn bản cuối (đặt trước khi đo, xem 04_he_thong_kha_thi.md): BLEU cascade trên FLEURS dev cao nhất
trong các phiên bản mà BLEU PhoMT dev không giảm quá 1 điểm so với B0. Cùng cấu hình giải mã với eval_mt.py.
"""
import argparse, json, os, random
import torch, sacrebleu
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

ap = argparse.ArgumentParser()
ap.add_argument("--phomt", required=True)
ap.add_argument("--n", type=int, default=2000)
ap.add_argument("--base", default="checkpoints/pretrained/vinai-translate-vi2en")
ap.add_argument("--versions", default="B0,V1,V2")
ap.add_argument("--out", default="reports/task2/mt/phomt_dev_selection.json")
args = ap.parse_args()

d = f"{args.phomt}/detokenization/dev/dev"
vi = open(d + ".vi", encoding="utf-8").read().split("\n")
en = open(d + ".en", encoding="utf-8").read().split("\n")
idx = [i for i in range(min(len(vi), len(en))) if vi[i].strip()]
random.Random(42).shuffle(idx)
idx = idx[: args.n]
src, ref = [vi[i] for i in idx], [en[i] for i in idx]
tok = AutoTokenizer.from_pretrained(args.base, src_lang="vi_VN")
en_id = tok.convert_tokens_to_ids("en_XX")
res = {"n": len(src), "seed": 42, "split": "PhoMT dev"}
for v in args.versions.split(","):
    m = AutoModelForSeq2SeqLM.from_pretrained(args.base, torch_dtype=torch.float16)
    if v != "B0":
        from peft import PeftModel
        m = PeftModel.from_pretrained(m, f"checkpoints/{v.lower()}/best_adapter").merge_and_unload()
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
    res[v] = {"BLEU": round(sacrebleu.corpus_bleu(hyp, [ref]).score, 2),
              "chrF++": round(sacrebleu.corpus_chrf(hyp, [ref], word_order=2).score, 2)}
    print(v, res[v], flush=True)
    del m; torch.cuda.empty_cache()
fl = {v: json.load(open(f"checkpoints/{v.lower()}/best.json"))["dev_bleu"] for v in args.versions.split(",") if v != "B0"}
ok = [v for v in fl if res[v]["BLEU"] >= res["B0"]["BLEU"] - 1.0]
res["fleurs_dev_bleu"] = fl
res["eligible_(phomt_dev_drop<=1)"] = ok
res["final"] = max(ok, key=fl.get) if ok else max(fl, key=fl.get)
json.dump(res, open(args.out, "w", encoding="utf-8"), indent=2)
print("FINAL", res["final"], flush=True)
