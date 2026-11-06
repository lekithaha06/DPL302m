"""Danh gia Proposed Method (can GPU): cung PhoWhisper-small pretrained + VinAI Translate + LoRA (mac dinh V2, doi bang ADAPTER_PATH),
chi khac tien/hau xu ly. So 2 cau hinh tren CUNG tap, CUNG chuan hoa:

  truoc_0411 : cat dung giua, khong bo lap cho noi, khong doi so    (cach xu ly cu)
  proposed   : cat tai cho lang +-3 s, bo lap cho noi, doi so truoc khi dich

Chay tai goc repo:
    set FLEURS_AUDIO_DIR=D:\\...\\audio_16k\\fleurs\\test     (Windows)
    python tests/danh_gia_proposed.py --tap test            # 857 ban FLEURS test
    python tests/danh_gia_proposed.py --tap test --n 50     # chay thu
    python tests/danh_gia_proposed.py --tu_thu thu_muc/      # bo cau tu thu (wav + cau.jsonl)

Ghi danh_gia/<ngay_gio>/: du_doan_<cau_hinh>.jsonl (tung mau), bang.md, ket_qua.json.
Bang tach 3 tang de khong nham module: ASR (WER/CER tren loi nguyen ban), ASR sau doi so
(chi de tham khao vi tham chieu FLEURS viet chu so), va cascade (BLEU/chrF++ cuoi pipeline).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

from src.audio import SR, chuan_hoa, doc_audio_bytes  # noqa: E402
from src.evaluate import tinh_bleu, tinh_wer  # noqa: E402

CAU_HINH = {
    "truoc_0411": {"cat_tai_lang": False, "bo_lap": False, "doi_so": False},
    "proposed": {"cat_tai_lang": True, "bo_lap": True, "doi_so": True},
}


def doc_mau(a):
    """Tra list {id, audio, ref_vi, ref_en}."""
    if a.tu_thu:
        d = Path(a.tu_thu)
        mau = [
            json.loads(x)
            for x in (d / "cau.jsonl").read_text(encoding="utf-8").splitlines()
            if x.strip()
        ]
        return [
            {
                "id": m["file"],
                "audio": d / m["file"],
                "ref_vi": m["vi"],
                "ref_en": m.get("en", ""),
                "nhom": m.get("nhom", ""),
            }
            for m in mau
        ]
    man = GOC / "experiments" / "runs" / "manifests" / f"asr_fleurs_{a.tap}.jsonl"
    goc_audio = os.environ.get("FLEURS_AUDIO_DIR")
    ra = []
    for x in man.read_text(encoding="utf-8").splitlines()[: a.n or None]:
        m = json.loads(x)
        p = Path(m["audio"].replace("\\", "/"))
        ra.append(
            {
                "id": m["id"],
                "audio": Path(goc_audio) / p.name if goc_audio else p,
                "ref_vi": m["reference"],
                "ref_en": m["text_en"],
                "nhom": "dai" if m["duration_s"] > 28 else "",
            }
        )
    return ra


def cham(R, nhom=None):
    R = [r for r in R if nhom is None or r["nhom"] == nhom]
    if not R:
        return {}
    kq = {
        "n": len(R),
        "WER_asr": tinh_wer([(r["ref_vi"], r["vi_goc"]) for r in R])["gia_tri"],
        "CER_asr": tinh_wer([(r["ref_vi"], r["vi_goc"]) for r in R], muc_ky_tu=True)["gia_tri"],
        "WER_sau_doi_so": tinh_wer([(r["ref_vi"], r["vi"]) for r in R])["gia_tri"],
        "RTF": round(sum(r["t"] for r in R) / max(1e-9, sum(r["dur"] for r in R)), 4),
    }
    if all(r["ref_en"] for r in R):
        b = tinh_bleu([(r["ref_en"], r["en"]) for r in R])
        kq |= {"BLEU": b["gia_tri"], "chrF++": b["chrF++"], "bleu_signature": b["bleu_signature"]}
    return kq


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--tap", default="test", choices=["test", "dev"])
    ap.add_argument("--n", type=int, default=0, help="chi lay n mau dau (0 = het)")
    ap.add_argument("--tu_thu", help="thu muc co cac wav + cau.jsonl {file, vi, en, nhom}")
    a = ap.parse_args()

    os.environ.setdefault("ASR_BACKEND", "that")
    from src.pipeline import HeThong, tao_backend

    backend = tao_backend()  # nap 1 lan, 2 cau hinh dung chung trong so
    mau = doc_mau(a)
    ra_dir = GOC / "danh_gia" / time.strftime("%Y%m%d_%H%M%S")
    ra_dir.mkdir(parents=True)
    tong = {"mo_hinh": backend.mo_hinh, "tap": a.tu_thu or f"fleurs_{a.tap}", "cau_hinh": CAU_HINH}

    for ten, ch in CAU_HINH.items():
        he = HeThong(backend=backend, **ch)
        R = []
        with (ra_dir / f"du_doan_{ten}.jsonl").open("w", encoding="utf-8") as f:
            for k, m in enumerate(mau):
                s, sr = doc_audio_bytes(Path(m["audio"]).read_bytes())
                x = chuan_hoa(s, sr)
                kq = he.xu_ly(x, SR)
                r = {
                    **{q: m[q] for q in ("id", "ref_vi", "ref_en", "nhom")},
                    "vi_goc": kq.transcript_vi_goc,
                    "vi": kq.transcript_vi,
                    "en": kq.ban_dich_en,
                    "dur": x.size / SR,
                    "t": kq.thoi_gian_tong_s,
                    "doan": [[d.bat_dau_s, d.ket_thuc_s] for d in kq.cac_doan],
                }
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                R.append(r)
                if k % 100 == 0:
                    print(f"{ten}: {k}/{len(mau)}", flush=True)
        tong[ten] = {"tat_ca": cham(R)}
        for nh in sorted({r["nhom"] for r in R} - {""}):
            tong[ten][nh] = cham(R, nh)

    (ra_dir / "ket_qua.json").write_text(
        json.dumps(tong, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    cot = ["n", "WER_asr", "CER_asr", "WER_sau_doi_so", "BLEU", "chrF++", "RTF"]
    bang = [
        f"# Danh gia Proposed Method · {tong['tap']}",
        "",
        f"`{backend.mo_hinh}`",
        "",
        "| Cau hinh | Nhom | " + " | ".join(cot) + " |",
        "|---|---|" + "---|" * len(cot),
    ]
    for ten in CAU_HINH:
        for nh, kq in tong[ten].items():
            bang.append(f"| {ten} | {nh} | " + " | ".join(str(kq.get(c, "-")) for c in cot) + " |")
    bang += [
        "",
        "WER_asr: loi PhoWhisper nguyen ban (so voi Task 2: FLEURS test 13,68 khi chay tung file).",
        "WER_sau_doi_so: tham khao, tham chieu FLEURS viet chu so nen doi so lam WER giam.",
        "BLEU/chrF++: sacreBLEU 2.4.3, cuoi pipeline (cascade).",
    ]
    (ra_dir / "bang.md").write_text("\n".join(bang), encoding="utf-8")
    print("\n".join(bang))
    print(f"\nDa ghi {ra_dir}")


if __name__ == "__main__":
    main()
