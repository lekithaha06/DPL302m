"""Proposed Method (Task 2, TV2): LoRA fine-tuning of VinAI Translate vi2en on (ASR transcript -> English reference).

V1 idea: the cascade loses 13.62 BLEU on FLEURS because the MT model only saw clean Vietnamese text. V1 adapts it to
real PhoWhisper errors with a small LoRA adapter (base weights frozen), trained on FLEURS train transcripts and
selected on FLEURS dev. The test split is never used here.

Decoding convention follows VinAI Translate: the decoder starts with the en_XX language token, so
decoder_input_ids = [en_XX] + y and labels = y + [</s>].
Resumable: state is saved after every epoch (adapter + optimizer + scheduler + log); rerun the same command to continue.
"""
import argparse, json, math, os, random, time
import numpy as np, torch, sacrebleu
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, get_linear_schedule_with_warmup
from peft import LoraConfig, get_peft_model, PeftModel, set_peft_model_state_dict, get_peft_model_state_dict

ap = argparse.ArgumentParser()
ap.add_argument("--train", nargs="+", required=True, help="JSONL files with fields asr (or src) and en_ref")
ap.add_argument("--dev", required=True, help="JSONL with asr and en_ref (FLEURS dev transcripts)")
ap.add_argument("--src-field", default="asr")
ap.add_argument("--base", default="checkpoints/pretrained/vinai-translate-vi2en")
ap.add_argument("--out", required=True, help="run directory, e.g. checkpoints/v1")
ap.add_argument("--epochs", type=int, default=5)
ap.add_argument("--lr", type=float, default=2e-4)
ap.add_argument("--batch", type=int, default=8)
ap.add_argument("--grad-accum", type=int, default=2)
ap.add_argument("--warmup", type=float, default=0.06)
ap.add_argument("--r", type=int, default=16)
ap.add_argument("--alpha", type=int, default=32)
ap.add_argument("--lora-dropout", type=float, default=0.05)
ap.add_argument("--targets", default="q_proj,k_proj,v_proj,out_proj")
ap.add_argument("--max-len", type=int, default=256)
ap.add_argument("--seed", type=int, default=42)
ap.add_argument("--extra-train", default="", help="optional JSONL of clean pairs (src, en_ref) mixed in, e.g. PhoMT subset for V2")
ap.add_argument("--balance-sentence", action="store_true",
                help="imbalance handling (Task 2, 1.4): sample each recording of a FLEURS sentence with k recordings "
                     "with weight 1/k, so every source sentence contributes equally (sampling with replacement)")
args = ap.parse_args()


def set_seed(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s); torch.cuda.manual_seed_all(s)


def read_jsonl(path, field, with_id=False):
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    pairs = [(r[field] if field in r else r["src"], r["en_ref"]) for r in rows]
    return (pairs, [r.get("id") if field in r else None for r in rows]) if with_id else pairs


set_seed(args.seed)
os.makedirs(args.out, exist_ok=True)
dev = "cuda"
tok = AutoTokenizer.from_pretrained(args.base, src_lang="vi_VN")
en_id = tok.convert_tokens_to_ids("en_XX")
eos = tok.eos_token_id
pad = tok.pad_token_id

train_pairs, train_ids = [], []
for f in args.train:
    p, ids = read_jsonl(f, args.src_field, with_id=True)
    train_pairs += p; train_ids += ids            # id only for ASR-transcript rows (recordings of FLEURS sentences)
if args.extra_train:
    p = read_jsonl(args.extra_train, "src")
    train_pairs += p; train_ids += [None] * len(p)
dev_pairs = read_jsonl(args.dev, args.src_field)
print(f"train pairs={len(train_pairs)} dev pairs={len(dev_pairs)}", flush=True)


def encode(batch):
    src = tok([s for s, _ in batch], padding=True, truncation=True, max_length=args.max_len, return_tensors="pt")
    ys = [tok(t, add_special_tokens=False).input_ids[: args.max_len - 1] + [eos] for _, t in batch]
    L = max(len(y) for y in ys)
    dec_in = torch.full((len(ys), L), pad)
    labels = torch.full((len(ys), L), -100)
    for i, y in enumerate(ys):
        dec_in[i, : len(y)] = torch.tensor([en_id] + y[:-1])
        labels[i, : len(y)] = torch.tensor(y)
    return {"input_ids": src.input_ids, "attention_mask": src.attention_mask,
            "decoder_input_ids": dec_in, "decoder_attention_mask": (labels != -100).long(), "labels": labels}


base = AutoModelForSeq2SeqLM.from_pretrained(args.base, torch_dtype=torch.float32)
cfg = LoraConfig(r=args.r, lora_alpha=args.alpha, lora_dropout=args.lora_dropout,
                 target_modules=args.targets.split(","), bias="none", task_type="SEQ_2_SEQ_LM")
model = get_peft_model(base, cfg).to(dev)
n_train = sum(p.numel() for p in model.parameters() if p.requires_grad)
n_all = sum(p.numel() for p in model.parameters())
print(f"trainable params={n_train:,} / {n_all:,} ({100 * n_train / n_all:.2f}%)", flush=True)

g = torch.Generator(); g.manual_seed(args.seed)
if args.balance_sentence:
    from collections import Counter
    from torch.utils.data import WeightedRandomSampler
    k = Counter(i for i in train_ids if i is not None)
    weights = [1.0 / k[i] if i is not None else 1.0 for i in train_ids]
    sampler = WeightedRandomSampler(weights, num_samples=len(train_pairs), replacement=True, generator=g)
    loader = DataLoader(train_pairs, batch_size=args.batch, sampler=sampler, collate_fn=encode)
    print(f"sentence balancing: {len(k)} FLEURS sentences, recordings per sentence {dict(sorted(Counter(k.values()).items()))}", flush=True)
else:
    loader = DataLoader(train_pairs, batch_size=args.batch, shuffle=True, collate_fn=encode, generator=g)
steps_total = math.ceil(len(loader) / args.grad_accum) * args.epochs
opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr, weight_decay=0.0)
sched = get_linear_schedule_with_warmup(opt, int(args.warmup * steps_total), steps_total)

state_path = os.path.join(args.out, "state.pt")
log_path = os.path.join(args.out, "log.jsonl")
start_epoch, best = 0, {"dev_bleu": -1}
if os.path.exists(state_path):
    st = torch.load(state_path, map_location="cpu", weights_only=False)
    set_peft_model_state_dict(model, st["adapter"])
    opt.load_state_dict(st["opt"]); sched.load_state_dict(st["sched"])
    start_epoch, best = st["epoch"], st["best"]
    torch.set_rng_state(st["rng_cpu"]); torch.cuda.set_rng_state(st["rng_cuda"]); g.set_state(st["rng_loader"])
    print(f"resumed after epoch {start_epoch}, best dev BLEU {best['dev_bleu']}", flush=True)
json.dump(vars(args) | {"trainable_params": n_train, "total_params": n_all, "train_pairs": len(train_pairs),
                        "dev_pairs": len(dev_pairs), "gpu": torch.cuda.get_device_name(0), "torch": torch.__version__},
          open(os.path.join(args.out, "config.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)


@torch.no_grad()
def evaluate():
    model.eval()
    losses = []
    for i in range(0, len(dev_pairs), 16):
        b = {k: v.to(dev) for k, v in encode(dev_pairs[i:i + 16]).items()}
        with torch.autocast("cuda", dtype=torch.bfloat16):
            losses.append(model(**b).loss.item())
    hyps = []
    for i in range(0, len(dev_pairs), 16):
        src = tok([s for s, _ in dev_pairs[i:i + 16]], padding=True, truncation=True, max_length=args.max_len, return_tensors="pt").to(dev)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            out = model.generate(**src, decoder_start_token_id=en_id, num_beams=5, early_stopping=True, max_length=args.max_len)
        hyps += tok.batch_decode(out, skip_special_tokens=True)
    refs = [t for _, t in dev_pairs]
    model.train()
    return (float(np.mean(losses)), sacrebleu.corpus_bleu(hyps, [refs]).score,
            sacrebleu.corpus_chrf(hyps, [refs], word_order=2).score)


if start_epoch == 0 and not os.path.exists(log_path):
    l0, b0, c0 = evaluate()  # epoch 0 = base model with untrained (zero-initialised) LoRA, i.e. Baseline B
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"epoch": 0, "train_loss": None, "dev_loss": l0, "dev_bleu": b0, "dev_chrf++": c0, "seconds": 0}) + "\n")
    print(f"epoch 0 (baseline) dev loss {l0:.4f} BLEU {b0:.2f} chrF++ {c0:.2f}", flush=True)

model.train()
for epoch in range(start_epoch + 1, args.epochs + 1):
    t0, tl, n = time.time(), 0.0, 0
    for step, b in enumerate(loader, 1):
        b = {k: v.to(dev) for k, v in b.items()}
        with torch.autocast("cuda", dtype=torch.bfloat16):
            loss = model(**b).loss / args.grad_accum
        loss.backward()
        tl += loss.item() * args.grad_accum; n += 1
        if step % args.grad_accum == 0 or step == len(loader):
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sched.step(); opt.zero_grad(set_to_none=True)
        if step % 50 == 0:
            print(f"epoch {epoch} step {step}/{len(loader)} loss {tl / n:.4f}", flush=True)
    dl, db, dc = evaluate()
    rec = {"epoch": epoch, "train_loss": tl / n, "dev_loss": dl, "dev_bleu": db, "dev_chrf++": dc, "seconds": round(time.time() - t0, 1)}
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print(rec, flush=True)
    if db > best["dev_bleu"]:
        best = rec
        model.save_pretrained(os.path.join(args.out, "best_adapter"))
    torch.save({"adapter": get_peft_model_state_dict(model), "opt": opt.state_dict(), "sched": sched.state_dict(),
                "epoch": epoch, "best": best, "rng_cpu": torch.get_rng_state(), "rng_cuda": torch.cuda.get_rng_state(),
                "rng_loader": g.get_state()}, state_path)
json.dump(best, open(os.path.join(args.out, "best.json"), "w"), indent=2)
print("best", best, flush=True)
