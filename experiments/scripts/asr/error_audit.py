#!/usr/bin/env python3
"""Trích mẫu lỗi ASR theo error_audit_template.csv của Bảo → reports/asr/error_audit.csv.

Mỗi run test chọn tự động (không chọn tay): 10 bản thu WER cao nhất + tối đa 5 bản thu cho mỗi nhãn
(tone_only, omission, number, proper_name, repetition), ưu tiên WER cao, không trùng.
Nhãn là gợi ý tự động: tone_only = có substitution chỉ khác dấu thanh; omission = D >= 2; number = tham chiếu có chữ số;
proper_name = có từ viết hoa không đứng đầu câu; repetition = giả thuyết có 3-gram lặp >= 3 lần.
audio_checked = CHUA_NGHE (chưa ai nghe audio); reviewer để trống. Không dùng để kết luận khi chưa nghe kiểm.
"""
import csv
import json
import re
from collections import Counter
from pathlib import Path

T = Path(__file__).resolve().parents[2]
TPL = T / "tai_lieu" / "bang_mau_bao" / "error_audit_template.csv"


def rep(h):
    w = h.split()
    c = Counter(tuple(w[i:i + 3]) for i in range(len(w) - 2))
    return bool(c) and max(c.values()) >= 3


def main():
    fields = list(csv.DictReader(open(TPL, encoding="utf-8-sig")).fieldnames)
    out = []
    for d in sorted((T / "runs" / "asr").glob("kiet_t2_*_test")):
        if not (d / "score" / "per_utterance.csv").exists():
            continue
        ds = "VIVOS" if "_vivos_" in d.name else "FLEURS_vi_vn"
        man = {json.loads(l)["id"]: json.loads(l) for l in open(T / "runs" / "manifests" / f"asr_{'vivos' if ds == 'VIVOS' else 'fleurs'}_test.jsonl", encoding="utf-8")}
        rows = list(csv.DictReader(open(d / "score" / "per_utterance.csv", encoding="utf-8-sig")))
        al = {json.loads(l)["id"]: json.loads(l) for l in open(d / "score" / "alignments.jsonl", encoding="utf-8")}
        for r in rows:
            m = man[r["id"]]
            ref = m["reference"]
            r["_lab"] = {"tone_only": int(r["tone_only_substitutions"]) > 0, "omission": int(r["D"]) >= 2,
                         "number": bool(re.search(r"\d", ref)),
                         "proper_name": any(t[:1].isupper() for t in ref.split()[1:] if t[:1].isalpha()),
                         "repetition": rep(r["hypothesis_norm"])}
            r["_w"] = float(r["WER_percent"])
        rows.sort(key=lambda r: (-r["_w"], r["id"]))
        pick, seen = [], set()
        for r in rows[:10]:
            pick.append(r); seen.add(r["id"])
        for lab in ("tone_only", "omission", "number", "proper_name", "repetition"):
            k = 0
            for r in rows:
                if k >= 5:
                    break
                if r["_lab"][lab] and r["id"] not in seen:
                    pick.append(r); seen.add(r["id"]); k += 1
        for r in pick:
            m = man[r["id"]]
            ops = " ".join(o["op"] for o in al[r["id"]]["word_alignment"])
            out.append({"run_id": d.name, "dataset": ds, "recording_id": r["id"], "sent_id": m["sent_id"], "speaker_id": m.get("speaker_id") or "",
                        "duration_s": round(m["duration_s"], 2), "reference_raw": r["reference_raw"], "hypothesis_raw": r["hypothesis_raw"],
                        "reference_norm": r["reference_norm"], "hypothesis_norm": r["hypothesis_norm"], "word_ops": ops,
                        **{k: r[k] for k in ("S", "D", "I", "N", "Sc", "Dc", "Ic", "Nc", "WER_percent", "CER_percent")},
                        **{k: int(v) for k, v in r["_lab"].items()}, "audio_checked": "CHUA_NGHE", "reference_issue": "",
                        "reviewer": "", "comment": "chọn tự động (WER cao nhất / theo nhãn gợi ý)"})
    p = T / "reports" / "asr" / "error_audit.csv"
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(out)
    print(p, len(out))


if __name__ == "__main__":
    main()
