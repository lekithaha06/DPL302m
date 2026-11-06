#!/usr/bin/env python3
"""Gắn MIỀN (nguồn) cho từng câu FLEURS bằng metadata của FLoRes+ (openlanguagedata/flores_plus, gated – cần bấm đồng ý trên web).

FLEURS lấy câu từ FLoRes; FLoRes+ ghi cho mỗi câu: domain (wikinews / wikijunior / wikivoyage), topic, url.
Ghép bằng câu tiếng Anh: câu Anh của FLEURS (en_us, đã có trong manifest) so với câu eng_Latn của FLoRes+ sau chuẩn hoá
(NFC, viết thường, bỏ dấu câu, gộp khoảng trắng). Câu không ghép được → domain "khong_ghep_duoc" (không đoán).
Chủ đề Giáo dục của nhóm = câu domain "wikibooks" (sách giáo khoa mở; gồm cả Wikijunior – sách cho thiếu nhi). Đối chiếu 30/10: 633 câu wikibooks, 247 có URL Wikijunior.

Đầu ra: reports/domain/fleurs_mien.csv (split, sent_id, domain, topic, url, cach_ghep), reports/domain/mien_tom_tat.json
"""
import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

T = Path(__file__).resolve().parents[2]
REPO = "openlanguagedata/flores_plus"


def norm(s):
    s = unicodedata.normalize("NFC", s).lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return " ".join(s.split())


def main():
    rev = HfApi().dataset_info(REPO).sha
    flores = {}
    files = {}
    for sp in ("dev", "devtest"):
        p = hf_hub_download(REPO, f"{sp}/eng_Latn.jsonl", repo_type="dataset", revision=rev, local_dir=T / "data" / "flores_plus")
        files[sp] = str(p)
        for l in open(p, encoding="utf-8"):
            r = json.loads(l)
            flores.setdefault(norm(r["text"]), []).append({**{k: r.get(k) for k in ("id", "domain", "topic", "url")}, "flores_split": sp})
    out, stat = [], {}
    for sp in ("train", "dev", "test"):
        seen = {}
        for l in open(T / "runs" / "manifests" / f"asr_fleurs_{sp}.jsonl", encoding="utf-8"):
            m = json.loads(l)
            seen.setdefault(m["sent_id"], m["text_en"])
        c = Counter()
        for sid, en in sorted(seen.items(), key=lambda x: int(x[0])):
            hits = flores.get(norm(en or ""), [])
            doms = {h["domain"] for h in hits}
            if len(doms) == 1:
                h = hits[0]; how = "khop_chinh_xac"
            else:
                h = {"domain": "khong_ghep_duoc" if not hits else "nhieu_mien", "topic": "", "url": "", "id": ""}; how = "khong" if not hits else "mo_ho"
            out.append({"split": sp, "sent_id": sid, "domain": h["domain"], "topic": h.get("topic") or "", "url": h.get("url") or "",
                        "flores_id": h.get("id") or "", "cach_ghep": how})
            c[h["domain"]] += 1
        stat[sp] = dict(c)
    d = T / "reports" / "domain"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "fleurs_mien.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    (d / "mien_tom_tat.json").write_text(json.dumps({"flores_plus_revision": rev, "files": files, "so_cau_theo_mien": stat},
                                                    ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stat, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
