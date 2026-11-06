"""Nghiem thu voi MODEL THAT (can GPU + mang lan dau). Khong chay trong pytest/CI.

Chay tai goc repo:
    python tests/nghiem_thu_that.py --audio a.wav b.wav c.wav            # T01, T03-T08 + T09 (1 phan)
    python tests/nghiem_thu_that.py --audio a.wav --hoi_quy 857           # them F09: chay lai FLEURS test
    python tests/nghiem_thu_that.py --audio a.wav --api http://localhost:8000   # them T06/T09 qua API

--audio: 3-5 file tieng Viet CHUA dung trong test (tu thu, 10-20 s). Script tu tao them file
dai 1/3/5 phut (ghep cac file nay), file im lang, giong nho, cac dinh dang, file hong.
Ket qua: nghiem_thu/<ngay_gio>/bang.md + ket_qua.json + log tung muc. Mo bang.md de dien checklist.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
import wave
from pathlib import Path

import numpy as np

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

from src.audio import SR, chuan_hoa, doc_audio_bytes  # noqa: E402

KQ: list[dict] = []


def ghi(ma, ten, dat, chi_tiet):
    KQ.append({"ma": ma, "ten": ten, "dat": dat, "chi_tiet": chi_tiet})
    print(f"[{'DAT ' if dat else 'TRUOT'}] {ma} {ten}: {chi_tiet}", flush=True)


def muc(ma, ten):
    def boc(f):
        def chay(*a, **k):
            try:
                f(*a, **k)
            except Exception as e:
                ghi(ma, ten, False, f"{type(e).__name__}: {e}")
                traceback.print_exc()

        return chay

    return boc


def wav_bytes(x, sr=SR):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
    return buf.getvalue()


def doc(p: Path):
    s, sr = doc_audio_bytes(p.read_bytes())
    return chuan_hoa(s, sr)


CHU_GIA = ("[gia]", "[mock]")


# ---------------------------------------------------------------- cac muc
@muc("T01/F01", "Audio that -> transcript + ban dich, backend=that")
def t01(he, files):
    dong = []
    ok = True
    for f in files:
        kq = he.xu_ly(doc(f), SR)
        gia = any(c in kq.transcript_vi + kq.ban_dich_en for c in CHU_GIA)
        ok &= (
            kq.backend == "that"
            and not gia
            and bool(kq.transcript_vi.strip())
            and bool(kq.ban_dich_en.strip())
        )
        dong.append(
            f"{f.name}: VI='{kq.transcript_vi[:80]}' | EN='{kq.ban_dich_en[:80]}' | RTF {kq.rtf:.3f}"
        )
    ghi(
        "T01/F01",
        "Audio that",
        ok,
        f"{he.backend.mo_hinh}\n    "
        + "\n    ".join(dong)
        + "\n    -> NGUOI KIEM phai doc lai: noi dung VI/EN co dung voi audio khong",
    )


@muc("T03/F03", "Audio 1/3/5 phut: doan <30 s, moc thoi gian dung, khong mat doan")
def t03(he, files):
    goc = np.concatenate([doc(f) for f in files])
    dong, ok = [], True
    for phut in (1, 3, 5):
        n = phut * 60 * SR
        x = np.tile(goc, int(np.ceil(n / goc.size)))[:n]
        t = time.perf_counter()
        kq = he.xu_ly(x, SR)
        d = kq.cac_doan
        dai_nhat = max(z.ket_thuc_s - z.bat_dau_s for z in d)
        lien = all(abs(a.ket_thuc_s - b.bat_dau_s) < 0.05 for a, b in zip(d, d[1:], strict=False))
        het = abs(d[-1].ket_thuc_s - phut * 60) < 0.5
        rong = sum(not z.transcript_vi.strip() for z in d)
        ok &= dai_nhat < 30 and lien and het
        dong.append(
            f"{phut} phut: {len(d)} doan, dai nhat {dai_nhat:.1f} s, lien nhau={lien}, "
            f"phu het={het}, doan rong={rong}, xu ly {time.perf_counter() - t:.1f} s"
        )
    ghi(
        "T03/F03",
        "Audio dai",
        ok,
        "\n    ".join(dong) + "\n    -> NGUOI KIEM nghe cho noi 2 doan: co lap/mat chu khong",
    )


@muc("T04/F05", "Im lang khong sinh chu; giong nho khong bi loc")
def t04(he, files):
    kq_il = he.xu_ly(np.zeros(3 * SR, np.float32), SR)
    x = doc(files[0])
    nho = x / (np.sqrt(np.mean(x**2)) + 1e-9) * 10 ** (-50 / 20)  # RMS -50 dBFS
    kq_nho = he.xu_ly(nho, SR)
    ok = kq_il.cac_doan == [] and kq_il.transcript_vi == "" and bool(kq_nho.transcript_vi.strip())
    ghi(
        "T04/F05",
        "Im lang / giong nho",
        ok,
        f"im lang 3 s -> {len(kq_il.cac_doan)} doan, '{kq_il.transcript_vi}'; "
        f"giong nho -50 dBFS -> '{kq_nho.transcript_vi[:80]}'",
    )


@muc("T05/F08", "WAV, MP3, FLAC, OGG, M4A, WEBM; 8/44,1/48 kHz; stereo")
def t05(he, files, thu_muc):
    if shutil.which("ffmpeg") is None:
        ghi("T05/F08", "Dinh dang", False, "khong co ffmpeg trong PATH: m4a/webm se khong doc duoc")
        return
    nguon = thu_muc / "nguon.wav"
    nguon.write_bytes(wav_bytes(doc(files[0])))
    goc = he.xu_ly(doc(files[0]), SR).transcript_vi
    dong, ok = [], True
    for duoi, them in (
        ("mp3", []),
        ("flac", []),
        ("ogg", ["-c:a", "libvorbis"]),
        ("m4a", ["-c:a", "aac"]),
        ("webm", ["-c:a", "libopus", "-ar", "48000"]),
        ("8k.wav", ["-ar", "8000"]),
        ("44k_stereo.wav", ["-ar", "44100", "-ac", "2"]),
    ):
        ra = thu_muc / f"thu.{duoi}"
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-i", str(nguon), *them, str(ra)], check=True
        )
        s, sr = doc_audio_bytes(ra.read_bytes())
        kq = he.xu_ly(s, sr)
        giong = kq.transcript_vi.strip() != ""
        ok &= giong
        dong.append(
            f"{duoi}: sr={sr}, '{kq.transcript_vi[:50]}'{'' if kq.transcript_vi == goc else ' (khac wav goc)'}"
        )
    ghi("T05/F08", "Dinh dang", ok, "\n    ".join(dong))


@muc("T07", "Nap model that bai -> bao loi, khong chuyen sang gia")
def t07():
    os.environ["ADAPTER_PATH"] = "khong_ton_tai/V9"
    from src.pipeline import tao_backend

    try:
        b = tao_backend()
        ghi("T07", "Nap loi", False, f"khong bao loi, backend={b.ten}")
    except Exception as e:
        ghi("T07", "Nap loi", True, f"{type(e).__name__}: {str(e)[:120]}")
    finally:
        os.environ.pop("ADAPTER_PATH", None)


@muc("T08/F06", "V2 (mac dinh), V4, B0 nap dung checkpoint")
def t08(files):
    from src.pipeline import HeThong

    x = doc(files[0])
    dong, ok, ban = [], True, {}
    for ten, gt in (("V2 mac dinh", None), ("V4", "checkpoints/V4/best"), ("B0", "none")):
        if gt is None:
            os.environ.pop("ADAPTER_PATH", None)
        else:
            os.environ["ADAPTER_PATH"] = gt
        he = HeThong()
        kq = he.xu_ly(x, SR)
        ban[ten] = kq.ban_dich_en
        mong = {"V2 mac dinh": "V2/best", "V4": "V4/best", "B0": "khong (B0)"}[ten]
        ok &= mong in he.backend.mo_hinh
        dong.append(f"{ten}: {he.backend.mo_hinh}\n      EN='{kq.ban_dich_en[:90]}'")
        del he
        _don_gpu()
    os.environ.pop("ADAPTER_PATH", None)
    ghi(
        "T08/F06",
        "Doi phien ban",
        ok,
        "\n    ".join(dong)
        + f"\n    ban dich 3 ban giong nhau het: {len(set(ban.values())) == 1} (giong het thi nghi adapter khong duoc nap)",
    )


@muc("T09/F10", "10 luot lien tiep khong lan ket qua")
def t09(he, files):
    x = [doc(f) for f in files]
    lan1 = [he.xu_ly(s, SR).transcript_vi for s in x]
    ok = True
    for k in range(10):
        i = k % len(x)
        ok &= he.xu_ly(x[i], SR).transcript_vi == lan1[i]
    ghi("T09/F10", "10 luot", ok, f"{len(x)} file x 10 luot, ket qua lap lai giong lan dau = {ok}")


@muc("T06/F10", "API: rong / hong / qua dung luong / 10 request")
def t06_api(url, files, key):
    import httpx

    h = {"X-API-Key": key} if key else {}
    r = httpx.get(f"{url}/health", timeout=10).json()
    dong = [f"health: {r}"]
    ok = r.get("backend") == "that"
    for ten, du_lieu, mong in (
        ("rong.wav", b"", 400),
        ("hong.wav", b"\x00rac" * 100, 400),
        ("x.txt", b"abc", 400),
    ):
        c = httpx.post(
            f"{url}/dich", files={"file": (ten, du_lieu)}, headers=h, timeout=60
        ).status_code
        ok &= c == mong
        dong.append(f"{ten} -> {c} (mong {mong})")
    lon = int(os.environ.get("MAX_UPLOAD_MB", "50")) * 1024 * 1024 + 10
    c = httpx.post(
        f"{url}/dich", files={"file": ("lon.wav", b"\0" * lon)}, headers=h, timeout=120
    ).status_code
    ok &= c == 413
    dong.append(f"file qua gioi han -> {c} (mong 413)")
    raw = files[0].read_bytes()
    kq = [
        httpx.post(
            f"{url}/dich", files={"file": (files[0].name, raw)}, headers=h, timeout=300
        ).json()
        for _ in range(10)
    ]
    giong = len({k["transcript_vi"] for k in kq}) == 1
    ok &= giong and all(k["backend"] == "that" for k in kq)
    dong.append(f"10 request lien tiep: ket qua giong nhau={giong}, mo_hinh={kq[0].get('mo_hinh')}")
    ghi("T06/F10", "API", ok, "\n    ".join(dong))


@muc("F09", "Hoi quy FLEURS test: WER/BLEU so voi so da bao cao")
def f09(he, n, thu_muc):
    import sacrebleu

    from src.evaluate import tinh_wer

    man = GOC / "experiments" / "runs" / "manifests" / "asr_fleurs_test.jsonl"
    dong = [json.loads(x) for x in man.read_text(encoding="utf-8").splitlines() if x.strip()][:n]
    goc_audio = os.environ.get("FLEURS_AUDIO_DIR")
    ra = thu_muc / "hoi_quy.jsonl"
    with ra.open("w", encoding="utf-8") as f:
        for k, m in enumerate(dong):
            p = (
                Path(goc_audio) / Path(m["audio"].replace("\\", "/")).name
                if goc_audio
                else Path(m["audio"])
            )
            kq = he.xu_ly(doc(p), SR)
            f.write(
                json.dumps(
                    {
                        "id": m["id"],
                        "reference": m["reference"],
                        "prediction": kq.transcript_vi,
                        "ref": m["text_en"],
                        "hyp": kq.ban_dich_en,
                        "dur": m["duration_s"],
                        "t": kq.thoi_gian_tong_s,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            if k % 100 == 0:
                print(f"  hoi quy {k}/{len(dong)}", flush=True)
    R = [json.loads(x) for x in ra.read_text(encoding="utf-8").splitlines()]
    w = tinh_wer([(r["reference"], r["prediction"]) for r in R])["gia_tri"]
    b = sacrebleu.BLEU().corpus_score([r["hyp"] for r in R], [[r["ref"] for r in R]]).score
    c = (
        sacrebleu.CHRF(word_order=2)
        .corpus_score([r["hyp"] for r in R], [[r["ref"] for r in R]])
        .score
    )
    rtf = sum(r["t"] for r in R) / sum(r["dur"] for r in R)
    # moc 04/11 (857 ban, V2 + tien/hau xu ly, experiments/reports/he_thong_V2): WER 12.26 BLEU 28.15
    ok = n < 857 or (abs(w - 12.26) < 1.0 and abs(b - 28.15) < 1.0)
    ghi(
        "F09",
        "Hoi quy",
        ok,
        f"{len(R)} ban: WER {w:.2f}%, BLEU {b:.2f}, chrF++ {c:.2f}, RTF {rtf:.3f}; "
        f"moc 04/11 (V2): WER 12,26 BLEU 28,15 (sai so cho phep 1,0). {he.backend.mo_hinh}. Du doan: {ra}",
    )


def _don_gpu():
    try:
        import gc

        import torch

        gc.collect()
        torch.cuda.empty_cache()
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--audio", nargs="+", type=Path, required=True)
    ap.add_argument(
        "--api", help="URL service API da chay voi model that, vd http://localhost:8000"
    )
    ap.add_argument("--api_key", default=os.environ.get("API_KEY", ""))
    ap.add_argument(
        "--hoi_quy", type=int, default=0, help="so ban FLEURS test chay lai (857 = toan bo)"
    )
    a = ap.parse_args()

    os.environ["ASR_BACKEND"] = "that"
    thu_muc = GOC / "nghiem_thu" / time.strftime("%Y%m%d_%H%M%S")
    thu_muc.mkdir(parents=True)
    for f in a.audio:
        if not f.exists():
            raise SystemExit(f"khong co file {f}")

    t07()
    from src.pipeline import HeThong

    print("nap model that (lan dau tai ~2,7 GB) ...", flush=True)
    he = HeThong()
    print("da nap:", he.backend.mo_hinh, flush=True)
    t01(he, a.audio)
    t03(he, a.audio)
    t04(he, a.audio)
    t05(he, a.audio, thu_muc)
    t09(he, a.audio)
    if a.hoi_quy:
        f09(he, a.hoi_quy, thu_muc)
    del he
    _don_gpu()
    t08(a.audio)
    if a.api:
        t06_api(a.api.rstrip("/"), a.audio, a.api_key)

    import platform

    moi_truong = {"python": platform.python_version(), "may": platform.platform()}
    try:
        import gradio
        import torch
        import transformers

        moi_truong |= {
            "torch": torch.__version__,
            "cuda": torch.cuda.is_available(),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "-",
            "transformers": transformers.__version__,
            "gradio": gradio.__version__,
        }
    except Exception as e:
        moi_truong["loi"] = str(e)

    (thu_muc / "ket_qua.json").write_text(
        json.dumps({"moi_truong": moi_truong, "ket_qua": KQ}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    bang = [
        "# Nghiem thu model that",
        "",
        f"Ngay {time.strftime('%d/%m/%Y %H:%M')} · {moi_truong}",
        "",
        "| Ma | Bai kiem tra | Ket qua |",
        "|---|---|---|",
    ]
    bang += [f"| {k['ma']} | {k['ten']} | {'DAT' if k['dat'] else '**TRUOT**'} |" for k in KQ]
    bang += [
        "",
        "Chua tu dong: T02 (micro 45-60 s tren trinh duyet) va T09 phan 2 tab GUI, T10 (pytest + ruff "
        "+ docker). Kiem bang tay theo README muc Nghiem thu.",
        "",
        "## Chi tiet",
        "",
    ]
    bang += [f"### {k['ma']} {k['ten']}\n\n```\n{k['chi_tiet']}\n```\n" for k in KQ]
    (thu_muc / "bang.md").write_text("\n".join(bang), encoding="utf-8")
    so_dat = sum(k["dat"] for k in KQ)
    print(f"\n{so_dat}/{len(KQ)} muc DAT. Bang: {thu_muc / 'bang.md'}")
    return 0 if so_dat == len(KQ) else 1


if __name__ == "__main__":
    sys.exit(main())
