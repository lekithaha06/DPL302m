#!/usr/bin/env python3
"""Sinh audio nhiễu để đo độ bền PhoWhisper trên FLEURS test (chỉ benchmark, KHÔNG fine-tune ASR, không dùng để chọn model).

Mỗi điều kiện thay đúng một yếu tố so với bản gốc: thêm nhiễu trắng theo SNR, đổi tốc độ (resample, cao độ đổi theo), đổi âm lượng.
Nhiễu tất định theo id (seed = SHA256 của "42:điều_kiện:id"). Ghi runs/robust/audio/<điều_kiện>/*.wav và runs/robust/manifests/<điều_kiện>.jsonl.
Chạy: $P scripts/asr/tao_audio_robust.py <điều_kiện>   (không đối số: tất cả)
"""
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

T = Path(__file__).resolve().parents[2]
SR = 16000
DIEU_KIEN = {"noise_snr20": ("noise", 20), "noise_snr10": ("noise", 10), "speed_0.9": ("speed", 0.9), "speed_1.1": ("speed", 1.1), "vol_-12dB": ("gain", -12)}


def bien_doi(a, kieu, gt, rid):
    if kieu == "noise":
        rng = np.random.default_rng(int(hashlib.sha256(rid.encode()).hexdigest()[:16], 16))
        n = rng.standard_normal(len(a)).astype(np.float32)
        ps = float(np.mean(a**2)); return a + n * np.sqrt(ps / 10 ** (gt / 10))
    if kieu == "speed":
        f = Fraction(gt).limit_denominator(100)  # chạy nhanh gấp f lần: còn 1/f số mẫu
        return resample_poly(a, f.denominator, f.numerator).astype(np.float32)
    return a * 10 ** (gt / 20)


def main():
    rows = [json.loads(l) for l in open(T / "runs/manifests/asr_fleurs_test.jsonl", encoding="utf-8")]
    (T / "runs/robust/manifests").mkdir(parents=True, exist_ok=True)
    for dk in sys.argv[1:] or DIEU_KIEN:
        kieu, gt = DIEU_KIEN[dk]; out = T / "runs/robust/audio" / dk; out.mkdir(parents=True, exist_ok=True); m = []
        for r in rows:
            a, sr = sf.read(r["audio"], dtype="float32"); assert sr == SR and a.ndim == 1
            b = np.clip(bien_doi(a, kieu, gt, f"42:{dk}:{r['id']}"), -1, 1); p = out / r["id"]
            sf.write(p, b, SR, subtype="PCM_16")
            m.append({**r, "audio": str(p), "duration_s": round(len(b) / SR, 3)})
        (T / f"runs/robust/manifests/{dk}.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in m), encoding="utf-8")
        print("XONG", dk, len(m), flush=True)


if __name__ == "__main__":
    main()
