#!/usr/bin/env python3
"""Phân tích lỗi (failure cases) so sánh hai hệ thống dịch trên cùng tập (mặc định DEV để thiết kế phiên bản sau,
không nhìn test). Chia nhóm tự động theo đặc điểm câu nguồn/tham chiếu:
  so      : câu tiếng Anh tham chiếu có chữ số (ASR đọc số thành chữ)
  ten     : câu tham chiếu có từ viết hoa không đứng đầu câu (tên riêng, heuristic)
  dai     : lời ASR > 40 từ (dài / có thể ảo giác)
  asr_xau : WER câu của ASR >= 30% (nghe sai nhiều)
  con_lai : không thuộc nhóm nào ở trên
Mỗi nhóm: số câu, BLEU, chrF++ của A và B. Ví dụ: 8 câu B kém A nhiều nhất (chrF++ câu) + 4 câu B hơn A nhiều nhất.
Đầu ra: --out (markdown) + .json cùng tên.
"""
import argparse
import json
import re
from pathlib import Path

import sacrebleu


def load(p):
    return {json.loads(l)["id"]: json.loads(l) for l in open(p, encoding="utf-8") if l.strip()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True); ap.add_argument("--a_name", default="B0")
    ap.add_argument("--b", required=True); ap.add_argument("--b_name", default="V1")
    ap.add_argument("--asr_score", required=True, help="per_utterance.csv của run ASR cùng tập (để lấy WER câu)")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    import csv
    A, B = load(a.a), load(a.b)
    wer = {r["id"]: float(r["WER_percent"]) for r in csv.DictReader(open(a.asr_score, encoding="utf-8-sig"))}
    groups = {"so": [], "ten": [], "dai": [], "asr_xau": [], "con_lai": []}
    for i, r in A.items():
        g = []
        if re.search(r"\d", r["ref"]): g.append("so")
        if any(t[:1].isupper() for t in r["ref"].split()[1:] if t[:1].isalpha()): g.append("ten")
        if len(r["src"].split()) > 40: g.append("dai")
        if wer.get(i, 0) >= 30: g.append("asr_xau")
        for x in g or ["con_lai"]:
            groups[x].append(i)
    bleu, chrf = sacrebleu.BLEU(), sacrebleu.CHRF(word_order=2)

    def sc(S, ids):
        return (round(bleu.corpus_score([S[i]["hyp"] for i in ids], [[S[i]["ref"] for i in ids]]).score, 2),
                round(chrf.corpus_score([S[i]["hyp"] for i in ids], [[S[i]["ref"] for i in ids]]).score, 2))

    res = {"all": {"n": len(A), a.a_name: sc(A, list(A)), a.b_name: sc(B, list(A))}}
    for k, ids in groups.items():
        if ids:
            res[k] = {"n": len(ids), a.a_name: sc(A, ids), a.b_name: sc(B, ids)}
    diff = []
    for i in A:
        ca = chrf.sentence_score(A[i]["hyp"], [A[i]["ref"]]).score
        cb = chrf.sentence_score(B[i]["hyp"], [B[i]["ref"]]).score
        diff.append((cb - ca, i, ca, cb))
    diff.sort()
    lines = [f"# Phân tích lỗi {a.b_name} so với {a.a_name}", "", f"- A: `{a.a}`", f"- B: `{a.b}`", "",
             f"| Nhóm | n | BLEU {a.a_name} | BLEU {a.b_name} | chrF++ {a.a_name} | chrF++ {a.b_name} |", "|---|---|---|---|---|---|"]
    for k, v in res.items():
        lines.append(f"| {k} | {v['n']} | {v[a.a_name][0]} | {v[a.b_name][0]} | {v[a.a_name][1]} | {v[a.b_name][1]} |")
    for title, rows in ((f"{a.b_name} kém {a.a_name} nhiều nhất", diff[:8]), (f"{a.b_name} hơn {a.a_name} nhiều nhất", diff[-4:][::-1])):
        lines += ["", f"## {title} (chrF++ câu)", ""]
        for d, i, ca, cb in rows:
            lines += [f"**{i}** (Δ chrF++ {d:+.1f}; WER ASR {wer.get(i, 'NA')})",
                      f"- nguồn (ASR): {A[i]['src']}", f"- tham chiếu: {A[i]['ref']}",
                      f"- {a.a_name}: {A[i]['hyp']}", f"- {a.b_name}: {B[i]['hyp']}", ""]
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text("\n".join(lines), encoding="utf-8")
    a.out.with_suffix(".json").write_text(json.dumps({"groups": res, "worst": [x[1] for x in diff[:8]], "best": [x[1] for x in diff[-4:]]}, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
