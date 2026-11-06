#!/usr/bin/env python3
"""Huấn luyện LoRA cho VinAI Translate vi2en (Proposed Method V1..Vn).

Dữ liệu dạy: một hoặc nhiều file JSONL (id, src, ref). src là câu tiếng Việt đưa vào MT (V1: lời ASR của FLEURS train),
ref là câu tiếng Anh. Dữ liệu dev dùng để chọn epoch (BLEU dev, cùng cấu hình decode với scripts/mt/translate.py).

Checkpoint mỗi epoch ở --out_dir/epoch_{k}/: adapter LoRA + optimizer + scheduler + GradScaler + trạng thái RNG.
Dừng giữa chừng → chạy lại cùng lệnh với --resume để tiếp từ epoch đã lưu gần nhất (thứ tự dữ liệu mỗi epoch
sinh từ seed + số epoch nên không phụ thuộc vào việc dừng). Bản tốt nhất theo BLEU dev chép ra --out_dir/best/.
Log: train_log.jsonl (loss theo bước), epochs.json (loss dev, BLEU dev mỗi epoch), curves.png.
"""
import argparse
import json
import math
import random
import shutil
import time
from pathlib import Path

import subprocess

import numpy as np
import psutil
import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, get_linear_schedule_with_warmup

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from translate import DECODE, MT_MODEL, score  # noqa: E402


def set_seed(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s); torch.cuda.manual_seed_all(s)


def read_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", nargs="+", required=True, type=Path)
    ap.add_argument("--dev", required=True, type=Path)
    ap.add_argument("--out_dir", required=True, type=Path)
    ap.add_argument("--revision", required=True)
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--lr", type=float, default=2e-4)
    # 4 × 4 = batch hiệu dụng 16 (như 8 × 2) nhưng không tràn VRAM 8 GB khi có câu PhoMT dài (đêm 1: 8 × 2 đỉnh 9,3 GB)
    ap.add_argument("--batch_size", type=int, default=4)
    ap.add_argument("--grad_accum", type=int, default=4)
    ap.add_argument("--warmup_ratio", type=float, default=0.06)
    ap.add_argument("--weight_decay", type=float, default=0.0)
    ap.add_argument("--lora_r", type=int, default=16)
    ap.add_argument("--lora_alpha", type=int, default=32)
    ap.add_argument("--lora_dropout", type=float, default=0.05)
    ap.add_argument("--targets", default="q_proj,k_proj,v_proj,out_proj,fc1,fc2")
    ap.add_argument("--max_len", type=int, default=256)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    cfg = {k: (str(v) if isinstance(v, Path) else [str(x) for x in v] if isinstance(v, list) else v) for k, v in vars(args).items()}
    cfg.update({"model": MT_MODEL, "optimizer": "AdamW (torch)", "scheduler": "linear warmup/decay", "precision": "fp32 weights + fp16 autocast",
                "decode_dev": DECODE, "selection": "BLEU dev cao nhất"})
    set_seed(args.seed)
    tok = AutoTokenizer.from_pretrained(MT_MODEL, revision=args.revision, src_lang="vi_VN", tgt_lang="en_XX")
    base = AutoModelForSeq2SeqLM.from_pretrained(MT_MODEL, revision=args.revision, torch_dtype=torch.float32)
    lcfg = LoraConfig(r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=args.lora_dropout,
                      target_modules=args.targets.split(","), task_type="SEQ_2_SEQ_LM")
    model = get_peft_model(base, lcfg).to("cuda")
    n_train_p = sum(p.numel() for p in model.parameters() if p.requires_grad)
    n_all = sum(p.numel() for p in model.parameters())
    cfg.update({"trainable_params": n_train_p, "all_params": n_all})

    train = [r for p in args.train for r in read_jsonl(p)]
    dev = read_jsonl(args.dev)
    cfg.update({"n_train": len(train), "n_dev": len(dev)})
    (out / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    bos_en = tok.lang_code_to_id["en_XX"]

    steps_per_epoch = math.ceil(len(train) / args.batch_size / args.grad_accum)
    total = steps_per_epoch * args.epochs
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr, weight_decay=args.weight_decay)
    sch = get_linear_schedule_with_warmup(opt, int(args.warmup_ratio * total), total)
    scaler = torch.cuda.amp.GradScaler()

    start_ep = 1
    epochs_log = []
    if args.resume:
        done = sorted([int(p.name.split("_")[1]) for p in out.glob("epoch_*") if (p / "state.pt").exists()])
        if done:
            k = done[-1]
            st = torch.load(out / f"epoch_{k}" / "state.pt", map_location="cpu")
            from peft import set_peft_model_state_dict
            from safetensors.torch import load_file
            set_peft_model_state_dict(model, load_file(str(out / f"epoch_{k}" / "adapter_model.safetensors")))
            opt.load_state_dict(st["opt"]); sch.load_state_dict(st["sch"]); scaler.load_state_dict(st["scaler"])
            random.setstate(st["py_rng"]); np.random.set_state(st["np_rng"]); torch.set_rng_state(st["torch_rng"])
            torch.cuda.set_rng_state_all(st["cuda_rng"])
            epochs_log = json.loads((out / "epochs.json").read_text(encoding="utf-8"))[:k]
            start_ep = k + 1
            tl_path = out / "train_log.jsonl"  # bỏ các bước của epoch dở dang (sẽ chạy lại)
            keep = [l for l in open(tl_path, encoding="utf-8") if l.strip() and json.loads(l)["epoch"] <= k]
            tl_path.write_text("".join(keep), encoding="utf-8")
            print(f"resume từ epoch {k}", flush=True)

    def collate(rows):
        enc = tok([r["src"] for r in rows], text_target=[r["ref"] for r in rows], padding=True, truncation=True,
                  max_length=args.max_len, return_tensors="pt")
        enc["labels"][enc["labels"] == tok.pad_token_id] = -100
        return {k: v.to("cuda") for k, v in enc.items()}

    @torch.inference_mode()
    def evaluate():
        model.eval()
        losses, hyps = [], []
        order = sorted(range(len(dev)), key=lambda i: (len(dev[i]["src"]), dev[i]["id"]))
        res = [None] * len(dev)
        for i in range(0, len(order), 16):
            idx = order[i:i + 16]
            rows = [dev[j] for j in idx]
            b = collate(rows)
            with torch.autocast("cuda", dtype=torch.float16):
                losses.append(model(**b).loss.item() * len(rows))
                enc = tok([r["src"] for r in rows], padding=True, truncation=True, max_length=args.max_len, return_tensors="pt").to("cuda")
                g = model.generate(**enc, decoder_start_token_id=bos_en, **DECODE)
            for j, h in zip(idx, tok.batch_decode(g, skip_special_tokens=True)):
                res[j] = h.strip()
        model.train()
        s = score(res, [r["ref"] for r in dev])
        return sum(losses) / len(dev), s, res

    log_f = open(out / "train_log.jsonl", "a", encoding="utf-8")
    model.train()
    for ep in range(start_ep, args.epochs + 1):
        t0 = time.time()
        g = random.Random(args.seed * 1000 + ep)
        order = list(range(len(train))); g.shuffle(order)
        batches = [order[i:i + args.batch_size] for i in range(0, len(order), args.batch_size)]
        run_loss, nb = 0.0, 0
        for bi, idx in enumerate(batches):
            b = collate([train[i] for i in idx])
            with torch.autocast("cuda", dtype=torch.float16):
                loss = model(**b).loss / args.grad_accum
            scaler.scale(loss).backward()
            run_loss += loss.item() * args.grad_accum; nb += 1
            if (bi + 1) % args.grad_accum == 0 or bi + 1 == len(batches):
                scaler.unscale_(opt)
                torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
                scaler.step(opt); scaler.update(); opt.zero_grad(set_to_none=True); sch.step()
                step = (ep - 1) * steps_per_epoch + (bi // args.grad_accum) + 1
                if step % 10 == 0:
                    log_f.write(json.dumps({"epoch": ep, "step": step, "train_loss": run_loss / nb, "lr": sch.get_last_lr()[0]}) + "\n"); log_f.flush()
                    run_loss, nb = 0.0, 0
        dev_loss, s, hyps = evaluate()
        ed = out / f"epoch_{ep}"
        model.save_pretrained(ed)
        torch.save({"opt": opt.state_dict(), "sch": sch.state_dict(), "scaler": scaler.state_dict(),
                    "py_rng": random.getstate(), "np_rng": np.random.get_state(), "torch_rng": torch.get_rng_state(),
                    "cuda_rng": torch.cuda.get_rng_state_all()}, ed / "state.pt")
        with open(ed / "dev_hyp.jsonl", "w", encoding="utf-8") as f:
            for r, h in zip(dev, hyps):
                f.write(json.dumps({"id": r["id"], "src": r["src"], "ref": r["ref"], "hyp": h}, ensure_ascii=False) + "\n")
        epochs_log.append({"epoch": ep, "dev_loss": dev_loss, "dev_BLEU": s["BLEU"], "dev_chrF++": s["chrF++"],
                           "minutes": round((time.time() - t0) / 60, 2), "peak_vram_bytes": torch.cuda.max_memory_allocated(),
                           "ram_rss_bytes": psutil.Process().memory_info().rss})
        (out / "epochs.json").write_text(json.dumps(epochs_log, indent=2), encoding="utf-8")
        print(json.dumps(epochs_log[-1]), flush=True)
    log_f.close()

    # Chọn epoch bằng ĐÚNG đường suy luận dùng để báo cáo (translate.py: base fp32 + merge LoRA → fp16, batch cố định),
    # vì BLEU đo trong lúc train (fp32 + autocast, chưa merge) lệch vài phần mười điểm (đêm 1: V1 25,96 vs 25,61).
    del model, base, opt
    torch.cuda.empty_cache()
    tr = Path(__file__).resolve().parent / "translate.py"
    for e in epochs_log:
        d = out / f"epoch_{e['epoch']}" / "dev_translate"
        if not (d / "score.json").exists():
            subprocess.run([sys.executable, str(tr), "--input", str(args.dev), "--out_dir", str(d), "--revision", args.revision,
                            "--adapter", str(out / f"epoch_{e['epoch']}")], check=True)
        sj = json.loads((d / "score.json").read_text(encoding="utf-8"))
        e["dev_BLEU_translate"], e["dev_chrF++_translate"] = sj["BLEU"], sj["chrF++"]
    (out / "epochs.json").write_text(json.dumps(epochs_log, indent=2), encoding="utf-8")
    best = max(epochs_log, key=lambda e: (e["dev_BLEU_translate"], -e["epoch"]))
    if (out / "best").exists():
        shutil.rmtree(out / "best")
    shutil.copytree(out / f"epoch_{best['epoch']}", out / "best", ignore=shutil.ignore_patterns("state.pt"))
    (out / "best" / "chon.json").write_text(json.dumps({"best_epoch": best["epoch"], "rule": "BLEU dev cao nhất qua translate.py (hoà thì lấy epoch sớm hơn)", **best}, indent=2), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    tl = [json.loads(l) for l in open(out / "train_log.jsonl", encoding="utf-8") if l.strip()]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot([r["step"] for r in tl], [r["train_loss"] for r in tl], label="train loss")
    ax[0].plot([e["epoch"] * steps_per_epoch for e in epochs_log], [e["dev_loss"] for e in epochs_log], "o-", label="dev loss")
    ax[0].set_xlabel("step"); ax[0].legend(); ax[0].set_title("Loss")
    ax[1].plot([e["epoch"] for e in epochs_log], [e["dev_BLEU"] for e in epochs_log], "o-", label="lúc train (fp32+autocast)")
    ax[1].plot([e["epoch"] for e in epochs_log], [e["dev_BLEU_translate"] for e in epochs_log], "s-", label="translate.py (dùng để chọn)")
    ax[1].set_xlabel("epoch"); ax[1].set_title("BLEU dev"); ax[1].axvline(best["epoch"], ls="--", c="gray"); ax[1].legend()
    fig.tight_layout(); fig.savefig(out / "curves.png", dpi=150)
    print("best", best)


if __name__ == "__main__":
    main()
