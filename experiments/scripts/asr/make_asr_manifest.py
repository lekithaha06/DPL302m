#!/usr/bin/env python3
"""Tạo manifest ASR (JSONL) từ dữ liệu sạch của Uyên (data/clean/{dataset}_{split}.jsonl) + SHA256.

Mỗi dòng: id, audio, reference (nhãn raw gốc), sent_id, speaker_id, duration_s, flags.
- FLEURS: id = file_name (vd 1234567890.wav) vì nhiều bản thu dùng chung sent_id; sent_id = ID câu FLoRes.
- VIVOS: id = mã câu (vd VIVOSDEV01_R086), sent_id = id.
Manifest ASR tách riêng với manifest cascade (cascade cần thêm câu tiếng Anh, tạo ở scripts/mt/make_mt_data.py).
Kiểm số lượng mong đợi theo protocol (VIVOS test 760, FLEURS test 857, dev 361); lệch thì dừng.
"""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED = {("vivos", "test"): 760, ("fleurs", "test"): 857, ("fleurs", "dev"): 361}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean_dir", type=Path, default=Path("data/clean"))
    ap.add_argument("--out_dir", type=Path, default=Path("runs/manifests"))
    ap.add_argument("--sets", default="vivos:test,fleurs:test,fleurs:dev,fleurs:train")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    info = {}
    for s in args.sets.split(","):
        ds, sp = s.split(":")
        rows = [json.loads(l) for l in open(args.clean_dir / f"{ds}_{sp}.jsonl", encoding="utf-8") if l.strip()]
        out = []
        for r in rows:
            rid = f"{r['uid']}.wav" if ds == "fleurs" else r["uid"]
            out.append({"id": rid, "audio": str(Path(r["audio_16k"]).resolve()), "reference": r["text_vi"],
                        "sent_id": r["group"], "speaker_id": r.get("speaker"), "gender": r.get("gender"),
                        "duration_s": r["dur"], "flags": r.get("flags", []), "text_en": r.get("text_en")})
        ids = [o["id"] for o in out]
        assert len(ids) == len(set(ids)), f"{ds}_{sp}: trùng id"
        exp = EXPECTED.get((ds, sp))
        if exp is not None and len(out) != exp:
            raise SystemExit(f"{ds}_{sp}: {len(out)} bản thu, protocol cần {exp}")
        p = args.out_dir / f"asr_{ds}_{sp}.jsonl"
        p.write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in out), encoding="utf-8")
        info[p.name] = {"n": len(out), "n_gt_30s": sum(o["duration_s"] > 30 for o in out),
                        "n_sent_id": len({o["sent_id"] for o in out}), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        print(p.name, info[p.name])
    (args.out_dir / "manifests_sha256.json").write_text(json.dumps(info, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
