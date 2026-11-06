"""Cham diem: WER/CER cho khoi nghe, BLEU/chrF++ cho khoi dich.

Dung de kiem hoi quy: chay lai tap test va so voi so da bao cao o Task 2.
Nguong hoi quy mac dinh lay tu bao cao (runs/mt/V3/fleurs_test_asr_pho/score.json).

Vi du:
    python src/evaluate.py --hyp runs/mt/V3/.../hyp.jsonl --metric bleu
    python src/evaluate.py --hyp ra.jsonl --metric wer --nguong 13.68 --sai_so 0.5
"""

from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path

# Cac moc da bao cao o Task 2, dung lam nguong kiem hoi quy.
# Nguon: reports/asr/results_task2.csv va runs/mt/*/score.json
MOC_TASK2 = {
    "wer_phowhisper_vivos": 6.24,
    "cer_phowhisper_vivos": 3.25,
    "wer_phowhisper_fleurs": 13.68,
    "cer_phowhisper_fleurs": 9.88,
    "bleu_b0_cascade": 22.69,
    "bleu_v3_cascade": 27.33,
    "bleu_v4_cascade": 27.37,
    "bleu_b0_sach": 38.27,
}


def chuan_hoa_vi(s: str) -> str:
    """Chuan hoa doi xung cho ca tham chieu va du doan.

    Dung protocol vi_nfc_ps_space_v1 cua Bao: NFC -> chu thuong -> moi ky tu loai
    Unicode P hoac S thanh khoang trang -> gop khoang trang.
    Giu dau thanh, khong tach tu, khong doi chu so sang chu.
    """
    s = unicodedata.normalize("NFC", s).lower()
    ra = []
    for ch in s:
        ra.append(" " if unicodedata.category(ch)[0] in ("P", "S") else ch)
    return " ".join("".join(ra).split())


def _edit_counts(ref: list[str], hyp: list[str]) -> tuple[int, int, int]:
    """Levenshtein, tra ve (S, D, I). Uu tien khop > thay > xoa > them khi dong hang."""
    n, m = len(ref), len(hyp)
    # d[i][j] = (chi_phi, so_thay, so_xoa, so_them)
    truoc = [(j, 0, 0, j) for j in range(m + 1)]
    for i in range(1, n + 1):
        hien = [(i, 0, i, 0)] + [(0, 0, 0, 0)] * m
        for j in range(1, m + 1):
            if ref[i - 1] == hyp[j - 1]:
                hien[j] = truoc[j - 1]
                continue
            thay = truoc[j - 1]
            xoa = truoc[j]
            them = hien[j - 1]
            ung_vien = [
                (thay[0] + 1, thay[1] + 1, thay[2], thay[3]),
                (xoa[0] + 1, xoa[1], xoa[2] + 1, xoa[3]),
                (them[0] + 1, them[1], them[2], them[3] + 1),
            ]
            hien[j] = min(ung_vien, key=lambda x: x[0])
        truoc = hien
    _, s, d, i = truoc[m]
    return s, d, i


def tinh_wer(cap: list[tuple[str, str]], muc_ky_tu: bool = False) -> dict:
    """WER hoac CER tren toan corpus: cong S/D/I va N roi moi chia.

    Khong lay trung binh WER tung cau: cau ngan co the co WER rat lon va khong
    nen cung trong so voi cau dai.
    """
    tS = tD = tI = tN = 0
    for ref, hyp in cap:
        r, h = chuan_hoa_vi(ref), chuan_hoa_vi(hyp)
        if muc_ky_tu:
            rt, ht = list(r.replace(" ", "")), list(h.replace(" ", ""))
        else:
            rt, ht = r.split(), h.split()
        if not rt:
            raise ValueError(f"tham chiếu rỗng sau chuẩn hoá: {ref!r}")
        s, d, i = _edit_counts(rt, ht)
        tS, tD, tI, tN = tS + s, tD + d, tI + i, tN + len(rt)
    return {
        "metric": "CER" if muc_ky_tu else "WER",
        "gia_tri": round(100 * (tS + tD + tI) / tN, 2),
        "S": tS,
        "D": tD,
        "I": tI,
        "N": tN,
        "n_cau": len(cap),
    }


def tinh_bleu(cap: list[tuple[str, str]]) -> dict:
    """BLEU va chrF++ bang sacreBLEU 2.4.3 - cung phien ban da dung o bao cao."""
    try:
        import sacrebleu
    except ImportError:
        raise SystemExit("Cần sacrebleu: pip install sacrebleu==2.4.3") from None
    # Dung doi tuong BLEU()/CHRF() giong translate.py cua Task 2. Ban cu goi
    # get_signature() tren ket qua corpus_bleu nen crash (BLEUScore khong co ham nay).
    refs, hyps = [[r for r, _ in cap]], [h for _, h in cap]
    bleu = sacrebleu.BLEU()
    chrf = sacrebleu.CHRF(word_order=2)
    b = bleu.corpus_score(hyps, refs)
    c = chrf.corpus_score(hyps, refs)
    return {
        "metric": "BLEU",
        "gia_tri": round(b.score, 2),
        "chrF++": round(c.score, 2),
        "bleu_signature": str(bleu.get_signature()),
        "chrf_signature": str(chrf.get_signature()),
        "n_cau": len(cap),
    }


def doc_cap(duong_dan: Path, truong_ref: str, truong_hyp: str) -> list[tuple[str, str]]:
    cap = []
    with duong_dan.open(encoding="utf-8") as f:
        for so_dong, dong in enumerate(f, 1):
            if not dong.strip():
                continue
            d = json.loads(dong)
            if truong_ref not in d or truong_hyp not in d:
                raise SystemExit(
                    f"{duong_dan}:{so_dong} thiếu trường "
                    f"{truong_ref!r} hoặc {truong_hyp!r}. "
                    f"Các trường có: {list(d)}"
                )
            cap.append((d[truong_ref], d[truong_hyp]))
    if not cap:
        raise SystemExit(f"{duong_dan} không có dòng nào")
    return cap


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--hyp", type=Path, required=True, help="File JSONL có trường tham chiếu và dự đoán"
    )
    p.add_argument("--metric", choices=["wer", "cer", "bleu"], required=True)
    p.add_argument("--truong_ref", default="ref")
    p.add_argument("--truong_hyp", default="hyp")
    p.add_argument("--nguong", type=float, help="Giá trị đã báo cáo, để kiểm hồi quy")
    p.add_argument("--moc", choices=sorted(MOC_TASK2), help="Lấy ngưỡng từ mốc đã báo cáo ở Task 2")
    p.add_argument(
        "--sai_so", type=float, default=0.5, help="Sai số cho phép khi kiểm hồi quy (mặc định 0,5)"
    )
    p.add_argument("--json", type=Path, help="Ghi kết quả ra JSON")
    a = p.parse_args()

    cap = doc_cap(a.hyp, a.truong_ref, a.truong_hyp)
    kq = tinh_bleu(cap) if a.metric == "bleu" else tinh_wer(cap, muc_ky_tu=(a.metric == "cer"))

    print(json.dumps(kq, ensure_ascii=False, indent=1))

    nguong = a.nguong if a.nguong is not None else (MOC_TASK2[a.moc] if a.moc else None)
    ma_thoat = 0
    if nguong is not None:
        lech = kq["gia_tri"] - nguong
        dat = abs(lech) <= a.sai_so
        print(
            f"\nKiểm hồi quy: {kq['gia_tri']} so với mốc {nguong} "
            f"(lệch {lech:+.2f}, cho phép ±{a.sai_so}) → {'ĐẠT' if dat else 'KHÔNG ĐẠT'}"
        )
        ma_thoat = 0 if dat else 1

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(
            json.dumps({**kq, "nguong": nguong}, ensure_ascii=False, indent=1), encoding="utf-8"
        )
    return ma_thoat


if __name__ == "__main__":
    raise SystemExit(main())
