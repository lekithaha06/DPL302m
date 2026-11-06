#!/usr/bin/env python3
"""Điền bảng mẫu của Bảo từ kết quả chạy thật (runs/asr/*), ghi ra reports/asr/ (bản mẫu gốc trong tai_lieu/bang_mau_bao giữ nguyên).

  results_task2.csv, paper_comparison.csv, strata.csv, run_metadata_<run_id>.json, long_form_audit.csv
Số đều đọc từ score/summary.json (score_asr.py của Bảo), score/per_utterance.csv, segments.jsonl, run_metadata.json.
Phân tầng tên riêng / số là HEURISTIC tự động (có chữ số → number; có từ viết hoa không đứng đầu câu → name),
ghi status AUTO_HEURISTIC_CHUA_NGHE_KIEM, chưa phải nhãn người đọc xác nhận.
"""
import csv
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

T = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(T / "scripts" / "asr"))
from score_asr import normalize  # noqa: E402

RUNS = T / "runs" / "asr"
OUT = T / "reports" / "asr"
TPL = T / "tai_lieu" / "bang_mau_bao"
DRIVER = subprocess.run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
MODELS = {"phowhisper-small": "PhoWhisper-small", "whisper-small": "whisper-small"}
DS = {"vivos": ("VIVOS", "VIVOS test", 760), "fleurs": ("FLEURS_vi_vn", "FLEURS vi_vn test", 857)}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rd_csv(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))


def wr_csv(p, rows, fields):
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)


def agg(rows):
    s = {k: sum(int(r[k]) for r in rows) for k in ("S", "D", "I", "N", "Sc", "Dc", "Ic", "Nc")}
    s["WER"] = 100 * (s["S"] + s["D"] + s["I"]) / s["N"] if s["N"] else None
    s["CER"] = 100 * (s["Sc"] + s["Dc"] + s["Ic"]) / s["Nc"] if s["Nc"] else None
    return s


def is_name(ref):
    toks = [t for t in re.split(r"\s+", ref.strip()) if t]
    return any(t[:1].isupper() for t in toks[1:] if t[:1].isalpha())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    vivos_train = {normalize(json.loads(l)["text_vi"]) for l in open(T / "data" / "clean" / "vivos_train.jsonl", encoding="utf-8")}
    res_rows, paper_rows, strata_rows, lf_rows = [], [], [], []
    paper = {(r["model"], r["dataset"]): r for r in rd_csv(TPL / "paper_comparison.csv")}
    for mkey, mname in MODELS.items():
        for dkey, (dname, pname, nexp) in DS.items():
            rid = f"kiet_t2_{mkey}_{dkey}_test"
            d = RUNS / rid
            if not (d / "score" / "summary.json").exists():
                continue
            sm = json.loads((d / "score" / "summary.json").read_text(encoding="utf-8"))
            meta = json.loads((d / "run_metadata.json").read_text(encoding="utf-8"))
            segs = [json.loads(l) for l in open(d / "segments.jsonl", encoding="utf-8")]
            pu = rd_csv(d / "score" / "per_utterance.csv")
            man = {json.loads(l)["id"]: json.loads(l) for l in open(T / "runs" / "manifests" / f"asr_{dkey}_test.jsonl", encoding="utf-8")}
            el = sorted(s["elapsed_s"] for s in segs)
            dur = sum(s["duration_s"] for s in segs)
            p50 = el[len(el) // 2]
            p95 = el[min(len(el) - 1, int(round(0.95 * (len(el) - 1))))]
            peak = max(s["gpu_peak_allocated_bytes"] for s in segs)
            blobs = T / "hf_home" / "hub" / f"models--{meta['model_id'].replace('/', '--')}" / "snapshots" / meta["model_revision"]
            wfile = next((blobs / n for n in ("model.safetensors", "pytorch_model.bin") if (blobs / n).exists()), None)
            w, c = sm["word_counts"], sm["char_counts"]
            res_rows.append({"run_id": rid, "model": mname, "dataset": dname, "split": "test", "n_expected": nexp, "n_scored": sm["n"],
                             "WER_percent": round(sm["WER_percent"], 2), "CER_percent": round(sm["CER_percent"], 2),
                             "S": w["S"], "D": w["D"], "I": w["I"], "N": w["N"], "Sc": c["S"], "Dc": c["D"], "Ic": c["I"], "Nc": c["N"],
                             "rtf": round(sum(el) / dur, 4), "latency_p50_s": round(p50, 3), "latency_p95_s": round(p95, 3),
                             "gpu_peak_allocated_bytes": peak, "checkpoint_bytes": wfile.stat().st_size if wfile else "",
                             "config_sha256": meta["config_sha256"], "manifest_sha256": meta["manifest_sha256"],
                             "status": "DA_CHAY_KIET" if sm["n"] == nexp else "THIEU_MAU"})
            p = paper.get((mname, pname))
            if p:
                pw = p["paper_WER_percent"]
                gap = round(sm["WER_percent"] - float(pw), 2) if pw not in ("NR", "") else "NR"
                rel = round(100 * (sm["WER_percent"] - float(pw)) / float(pw), 1) if pw not in ("NR", "") else "NR"
                paper_rows.append({**p, "group_WER_percent": round(sm["WER_percent"], 2), "group_CER_percent": round(sm["CER_percent"], 2),
                                   "group_S": w["S"], "group_D": w["D"], "group_I": w["I"], "group_N": w["N"], "gap_pp": gap,
                                   "relative_gap_percent": rel, "status": "DA_CHAY_KIET", "run_id": rid,
                                   "manifest_sha256": meta["manifest_sha256"], "config_sha256": meta["config_sha256"]})
            # phân tầng
            groups = defaultdict(list)
            for r in pu:
                m = man[r["id"]]
                if dkey == "fleurs":
                    dd = m["duration_s"]
                    b = "<=5" if dd <= 5 else ">5_to_15" if dd <= 15 else ">15_to_30" if dd <= 30 else ">30"
                    groups[("duration_s", b)].append(r)
                    ref = m["reference"]
                    if re.search(r"\d", ref):
                        groups[("name_or_number", "number")].append(r)
                    if is_name(ref):
                        groups[("name_or_number", "name")].append(r)
                    if not re.search(r"\d", ref) and not is_name(ref):
                        groups[("name_or_number", "neither")].append(r)
                else:
                    ov = normalize(m["reference"]) in vivos_train
                    groups[("train_text_overlap", "yes" if ov else "no")].append(r)
            for (gt, gv), rs in sorted(groups.items()):
                a = agg(rs)
                strata_rows.append({"run_id": rid, "dataset": dname, "group_type": gt, "group_value": f"{gv}_{len(rs)}" if gt == "train_text_overlap" else gv,
                                    "n_recordings": len(rs), "n_reference_units": a["N"], "S": a["S"], "D": a["D"], "I": a["I"],
                                    "WER_percent": round(a["WER"], 2), "CER_percent": round(a["CER"], 2),
                                    "status": "AUTO_HEURISTIC_CHUA_NGHE_KIEM" if gt == "name_or_number" else "DA_CHAY_KIET"})
            # audit long-form
            pud = {r["id"]: r for r in pu}
            for s in segs:
                if s["long_form"]:
                    r = pud[s["id"]]
                    lf_rows.append({"run_id": rid, "id": s["id"], "duration_s": round(s["duration_s"], 2), "n_samples_input": s["n_samples_input"],
                                    "n_frames": s["n_frames"], "n_segments": len(s["segments"] or []), "coverage_end_s": s["coverage_end_s"],
                                    "hit_cap_440": s["hit_cap_440"], "n_output_tokens": s["n_output_tokens"], "has_output": bool(r["hypothesis_raw"].strip()),
                                    "S": r["S"], "D": r["D"], "I": r["I"], "N": r["N"], "WER_percent": round(float(r["WER_percent"]), 1)})
            # metadata theo mẫu
            tpl = json.loads((TPL / "run_metadata_template.json").read_text(encoding="utf-8"))
            env = meta["environment"]
            tpl.update({"status": "DA_CHAY_KIET", "run_id": rid, "model_id": meta["model_id"], "model_revision": meta["model_revision"],
                        "model_weight_sha256": sha(wfile) if wfile else None, "processor_revision": meta["model_revision"],
                        "dataset": dname, "dataset_revision": "70bb2e84b976b7e960aa89f1c648e09c59f894dd" if dkey == "fleurs" else "3cbfb2502e5e84776b4b778b020a09759f723f52",
                        "manifest_sha256": meta["manifest_sha256"], "n_expected": nexp, "n_scored": sm["n"], "scorer_sha256": sm["scorer_sha256"],
                        "resolved_generation_config": meta["resolved_config"], "config_sha256": meta["config_sha256"],
                        "gpu": env["gpu"], "cpu": env["processor"], "cuda": env["cuda"], "driver": DRIVER, "python": env["python"],
                        "packages": {"torch": env["torch"], "transformers": env["transformers"], "numpy": env["numpy"], "cudnn": env["cudnn"]},
                        "warmup_recordings": "1 (1 s im lặng, không tính)", "timing_repetitions": 1, "cuda_synchronized": True,
                        "timing_scope": "mỗi bản thu: feature extraction + generate, không gồm đọc file và decode text",
                        "long_audio_coverage_checked": all(x["has_output"] for x in lf_rows if x["run_id"] == rid),
                        "predictions_file": str((d / "predictions.jsonl").relative_to(T)), "predictions_sha256": sm["predictions_sha256"],
                        "notes": "Python 3.11.1 (protocol tham chiếu 3.11.9); các phiên bản còn lại đúng protocol."})
            (OUT / f"run_metadata_{rid}.json").write_text(json.dumps(tpl, ensure_ascii=False, indent=2), encoding="utf-8")
    wr_csv(OUT / "results_task2.csv", res_rows, list(rd_csv(TPL / "results_task2.csv")[0].keys()))
    wr_csv(OUT / "paper_comparison.csv", paper_rows, list(rd_csv(TPL / "paper_comparison.csv")[0].keys()))
    wr_csv(OUT / "strata.csv", strata_rows, list(rd_csv(TPL / "strata_template.csv")[0].keys()))
    if lf_rows:
        wr_csv(OUT / "long_form_audit.csv", lf_rows, list(lf_rows[0].keys()))
    for r in res_rows:
        print(r["run_id"], r["n_scored"], r["WER_percent"], r["CER_percent"], "RTF", r["rtf"])


if __name__ == "__main__":
    main()
