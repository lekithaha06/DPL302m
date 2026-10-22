"""Task 2 · đo tốc độ, bộ nhớ và dung lượng (phần Đăng, Kiệt chạy khi GPU không làm việc khác).

1. Câu ngắn: N bản thu FLEURS test đầu tiên (sắp theo tên file), từng câu một, không VAD:
   thời gian ASR, MT, tổng; RTF = thời gian xử lý / độ dài âm thanh; độ trễ trung vị và p95.
2. Âm thanh dài: ghép K bản thu test liên tiếp (chèn 0,5 s im lặng), chạy có VAD và không VAD.
3. Dung lượng: số tham số và kích thước file trọng số (PhoWhisper, VinAI Translate, adapter LoRA nếu có); VRAM đỉnh.
"""
import argparse, json, os, statistics, time, platform
import numpy as np, torch
from cascade import Cascade, load_audio, SR

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True)
ap.add_argument("--asr", default="checkpoints/pretrained/PhoWhisper-small")
ap.add_argument("--mt", default="checkpoints/pretrained/vinai-translate-vi2en")
ap.add_argument("--adapter", default="")
ap.add_argument("--test", default="data/processed/fleurs_vi_en_test.json")
ap.add_argument("--n", type=int, default=100)
ap.add_argument("--k-long", type=int, default=20)
ap.add_argument("--out", default="reports/task2/system")
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
torch.manual_seed(42)


def dir_mb(d, exts=(".bin", ".safetensors")):
    return round(sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d) if f.endswith(exts)) / 2**20, 1)


cas = Cascade(args.asr, args.mt, args.adapter)
rows = sorted(json.load(open(args.test, encoding="utf-8")), key=lambda r: os.path.basename(r["audio"]))[: args.n]
warm = load_audio(rows[0]["audio"])
for _ in range(2):
    cas.run(warm, use_vad=False)
torch.cuda.reset_peak_memory_stats()

per = []
for r in rows:
    a = load_audio(r["audio"])
    t0 = time.perf_counter()
    _, t = cas.run(a, use_vad=False)
    per.append({"sec": len(a) / SR, "asr": t["asr"], "mt": t["mt"], "total": time.perf_counter() - t0})
tot_audio = sum(p["sec"] for p in per)
short = {"n": len(per), "audio_seconds": round(tot_audio, 1),
         "rtf_total": round(sum(p["total"] for p in per) / tot_audio, 3),
         "rtf_asr": round(sum(p["asr"] for p in per) / tot_audio, 3), "rtf_mt": round(sum(p["mt"] for p in per) / tot_audio, 3),
         "latency_median_s": round(statistics.median(p["total"] for p in per), 3),
         "latency_p95_s": round(float(np.percentile([p["total"] for p in per], 95)), 3),
         "mean_utt_seconds": round(tot_audio / len(per), 2)}

gap = np.zeros(SR // 2, dtype="float32")
long_audio = np.concatenate([x for r in rows[: args.k_long] for x in (load_audio(r["audio"]), gap)])
longr = {"audio_seconds": round(len(long_audio) / SR, 1)}
for use_vad in (True, False):
    t0 = time.perf_counter()
    segs, t = cas.run(long_audio, use_vad=use_vad)
    el = time.perf_counter() - t0
    longr["vad" if use_vad else "no_vad"] = {"segments": len(segs), "seconds": round(el, 2), "rtf": round(el / (len(long_audio) / SR), 3),
                                             "vad_s": round(t["vad"], 2), "asr_s": round(t["asr"], 2), "mt_s": round(t["mt"], 2)}

size = {"asr_params": sum(p.numel() for p in cas.asr.model.parameters()), "asr_weights_mb": dir_mb(args.asr),
        "mt_params": sum(p.numel() for p in cas.mt.parameters()), "mt_weights_mb": dir_mb(args.mt),
        "adapter_mb": dir_mb(args.adapter) if args.adapter else 0.0,
        "gpu_peak_allocated_mb": round(torch.cuda.max_memory_allocated() / 2**20, 1)}
res = {"name": args.name, "adapter": args.adapter or None, "gpu": torch.cuda.get_device_name(0), "torch": torch.__version__,
       "python": platform.python_version(), "precision": "fp16", "short_utterances": short, "long_audio": longr, "size": size}
json.dump(res, open(f"{args.out}/speed_{args.name}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(res, ensure_ascii=False, indent=1))
