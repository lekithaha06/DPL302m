#!/usr/bin/env python3
"""Dịch vi→en bằng VinAI Translate vi2en (B0) hoặc B0 + LoRA adapter (V1..Vn), rồi chấm BLEU/chrF++ bằng sacrebleu.

Đầu vào: JSONL có các trường id, src (câu tiếng Việt đưa vào MT: transcript sạch hoặc lời ASR), ref (câu tiếng Anh).
Đầu ra trong --out_dir:
  hyp.jsonl      id, src, ref, hyp  (ghi dần, chạy lại bỏ qua id đã có → chia buổi không đổi kết quả)
  score.json     BLEU, chrF++, signature sacrebleu, số câu, thời gian, cấu hình decode, adapter
Cấu hình decode cố định cho mọi phiên bản: beam 5, max_new_tokens 256, fp16, batch theo độ dài (chỉ ảnh hưởng tốc độ).
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import sacrebleu
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

MT_MODEL = "vinai/vinai-translate-vi2en-v2"
DECODE = {"num_beams": 5, "max_new_tokens": 256, "early_stopping": True, "do_sample": False}


def load_mt(revision, adapter=None, dtype=torch.float16):
    """Nạp base fp32, merge LoRA ở fp32 (chính xác hơn merge ở fp16), rồi mới đổi sang fp16 để suy luận.
    Với B0 (không adapter) kết quả giống hệt nạp thẳng fp16 vì chỉ là một lần ép kiểu."""
    tok = AutoTokenizer.from_pretrained(MT_MODEL, revision=revision, src_lang="vi_VN")
    model = AutoModelForSeq2SeqLM.from_pretrained(MT_MODEL, revision=revision, torch_dtype=torch.float32)
    if adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter)
        model = model.merge_and_unload()
    return tok, model.to(dtype).to("cuda").eval()


N_OOM_SPLIT = 0


@torch.inference_mode()
def translate_batch(tok, model, srcs):
    """Dịch một batch. Nếu hết VRAM (vd adapter overfit sinh câu rất dài) thì chia đôi batch đó và dịch lại;
    batch không lỗi giữ nguyên thành phần → kết quả các run trước (không lỗi) không đổi. Số lần chia ghi vào score.json."""
    global N_OOM_SPLIT
    try:
        enc = tok(srcs, padding=True, truncation=True, max_length=256, return_tensors="pt").to("cuda")
        out = model.generate(**enc, decoder_start_token_id=tok.lang_code_to_id["en_XX"], **DECODE)
        return [s.strip() for s in tok.batch_decode(out, skip_special_tokens=True)]
    except torch.cuda.OutOfMemoryError:
        if len(srcs) == 1:
            raise
        N_OOM_SPLIT += 1
        torch.cuda.empty_cache()
        h = len(srcs) // 2
        return translate_batch(tok, model, srcs[:h]) + translate_batch(tok, model, srcs[h:])


def score(hyps, refs):
    bleu = sacrebleu.BLEU()
    chrf = sacrebleu.CHRF(word_order=2)
    b = bleu.corpus_score(hyps, [refs])
    c = chrf.corpus_score(hyps, [refs])
    return {"BLEU": round(b.score, 2), "chrF++": round(c.score, 2), "bleu_signature": str(bleu.get_signature()),
            "chrf_signature": str(chrf.get_signature()), "n": len(hyps)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out_dir", required=True, type=Path)
    ap.add_argument("--revision", required=True, help="commit của vinai-translate-vi2en-v2 (reports/models.json)")
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--batch_size", type=int, default=16)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    torch.manual_seed(42)
    items = [json.loads(l) for l in open(args.input, encoding="utf-8") if l.strip()]
    if args.limit:
        items = items[: args.limit]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    hp = args.out_dir / "hyp.jsonl"
    done = {}
    if hp.exists():
        for l in open(hp, encoding="utf-8"):
            if l.strip():
                r = json.loads(l); done[r["id"]] = r
    tok, model = load_mt(args.revision, args.adapter)
    # Chia batch trên TOÀN BỘ danh sách (cố định theo độ dài + id) rồi mới bỏ batch đã xong,
    # để chạy liền hay chạy tiếp sau khi dừng đều cho cùng thành phần batch → cùng kết quả.
    order = sorted(items, key=lambda r: (len(r["src"]), r["id"]))
    batches = [order[i:i + args.batch_size] for i in range(0, len(order), args.batch_size)]
    todo = [it for it in items if it["id"] not in done]
    t0 = time.perf_counter()
    with open(hp, "a", encoding="utf-8") as f:
        for bi, chunk in enumerate(batches):
            if all(c["id"] in done for c in chunk):
                continue
            for it, h in zip(chunk, translate_batch(tok, model, [c["src"] for c in chunk])):
                if it["id"] in done:
                    continue
                r = {"id": it["id"], "src": it["src"], "ref": it["ref"], "hyp": h}
                f.write(json.dumps(r, ensure_ascii=False) + "\n"); done[it["id"]] = r
            f.flush()
            if bi % 50 == 0:
                print(f"batch {bi + 1}/{len(batches)}", flush=True)
    el = time.perf_counter() - t0
    rows = [done[it["id"]] for it in items]
    s = score([r["hyp"] for r in rows], [r["ref"] for r in rows])
    s.update({"input": str(args.input), "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
              "model": MT_MODEL, "revision": args.revision, "adapter": args.adapter, "decode": DECODE,
              "dtype": "float16 (adapter merge ở fp32)", "batch_size": args.batch_size, "n_oom_split": N_OOM_SPLIT, "elapsed_s_this_session": round(el, 1), "n_new_this_session": len(todo),
              "finished": time.strftime("%Y-%m-%d %H:%M:%S")})
    (args.out_dir / "score.json").write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: s[k] for k in ("BLEU", "chrF++", "n")}))


if __name__ == "__main__":
    main()
