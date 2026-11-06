"""Suy luan tu dong lenh: audio tieng Viet -> transcript + ban dich.

Vi du:
    python src/inference.py --audio bai_giang.wav
    python src/inference.py --audio a.wav --adapter checkpoints/V2/best --json ra.json
    python src/inference.py --thu_muc audio/ --json ket_qua.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.audio import doc_audio_bytes  # noqa: E402
from src.pipeline import HeThong  # noqa: E402

log = logging.getLogger(__name__)
DUOI = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".webm"}


def doc_file(duong_dan: Path) -> tuple[np.ndarray, int]:
    return doc_audio_bytes(duong_dan.read_bytes())


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--audio", type=Path, help="Một file audio")
    g.add_argument("--thu_muc", type=Path, help="Thư mục chứa nhiều file audio")
    p.add_argument(
        "--adapter",
        help="Adapter LoRA (mặc định checkpoints/V2/best; none = không dùng adapter, chạy B0)",
    )
    p.add_argument(
        "--max_doan_s",
        type=float,
        default=28.0,
        help="Độ dài tối đa mỗi đoạn, giây (mặc định 28, phải dưới 30)",
    )
    p.add_argument(
        "--vad",
        action="store_true",
        help="Audio dài: cắt tại khoảng lặng thay vì chia đều (chưa đo với model thật)",
    )
    p.add_argument("--json", type=Path, help="Ghi kết quả ra file JSON hoặc JSONL")
    p.add_argument("-v", "--verbose", action="store_true")
    a = p.parse_args()

    logging.basicConfig(
        level=logging.INFO if a.verbose else logging.WARNING, format="%(levelname)s %(message)s"
    )

    if a.max_doan_s > 30:
        p.error("--max_doan_s phải ≤ 30: khối nghe giải mã sai phần sau 30 giây")

    files = (
        [a.audio]
        if a.audio
        else sorted(f for f in a.thu_muc.rglob("*") if f.suffix.lower() in DUOI)
    )
    if not files:
        raise SystemExit("Không tìm thấy file audio nào")
    for f in files:
        if not f.exists():
            raise SystemExit(f"Không có file {f}")

    he = HeThong(adapter=a.adapter, max_doan_s=a.max_doan_s, dung_vad=a.vad)
    if he.backend.ten == "gia":
        print("CẢNH BÁO: ASR_BACKEND=gia, kết quả không có nghĩa.\n", file=sys.stderr)

    ket_qua = []
    for f in files:
        song, sr = doc_file(f)
        kq = he.xu_ly(song, sr)
        ket_qua.append({"file": str(f), **kq.dict()})

        print(f"\n=== {f.name} ===")
        print(
            f"{kq.thoi_luong_audio_s:.1f} s · {len(kq.cac_doan)} đoạn · "
            f"RTF {kq.rtf:.3f} · nghe {kq.thoi_gian_nghe_s:.2f} s + "
            f"dịch {kq.thoi_gian_dich_s:.2f} s"
        )
        for d in kq.cac_doan:
            print(f"  [{d.moc_thoi_gian}] {d.transcript_vi}")
            print(f"  {' ' * (len(d.moc_thoi_gian) + 3)}→ {d.ban_dich_en}")

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        if a.json.suffix == ".jsonl":
            with a.json.open("w", encoding="utf-8") as fh:
                for r in ket_qua:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        else:
            noi_dung = ket_qua[0] if len(ket_qua) == 1 else ket_qua
            a.json.write_text(json.dumps(noi_dung, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nĐã ghi {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
