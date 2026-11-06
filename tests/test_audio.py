"""Test phan tien xu ly audio va chia doan. Khong can GPU, khong nap model."""

import shutil
import subprocess

import numpy as np
import pytest

from src.audio import (
    MAX_DOAN_S,
    SR,
    bo_lap_cho_noi,
    chia_doan,
    chuan_hoa,
    doc_audio_bytes,
    doc_tep,
    ghep_loi,
    tim_vung_noi,
)


def tao_tieng(thoi_luong_s, sr=SR, bien_do=0.3, tan_so=220.0):
    """Tao song sin coi nhu 'co tieng noi'."""
    t = np.arange(int(thoi_luong_s * sr)) / sr
    return (bien_do * np.sin(2 * np.pi * tan_so * t)).astype(np.float32)


def tao_im_lang(thoi_luong_s, sr=SR):
    return np.zeros(int(thoi_luong_s * sr), dtype=np.float32)


# ---------------- chuan hoa ----------------
def test_chuan_hoa_doi_sample_rate():
    song = tao_tieng(1.0, sr=44100)
    ra = chuan_hoa(song, 44100, SR)
    # cho phep lech vai mau do lam tron cua bo resample
    assert abs(ra.size - SR) <= 10, f"ky vong ~{SR} mau, nhan {ra.size}"
    assert ra.dtype == np.float32


def test_chuan_hoa_stereo_thanh_mono():
    stereo = np.stack([tao_tieng(0.5), tao_tieng(0.5)], axis=1)
    ra = chuan_hoa(stereo, SR, SR)
    assert ra.ndim == 1


def test_chuan_hoa_int16_ve_khoang_mot():
    song = (tao_tieng(0.5) * 32767).astype(np.int16)
    ra = chuan_hoa(song, SR, SR)
    assert np.abs(ra).max() <= 1.01, "int16 phai duoc chia 32768"


def test_chuan_hoa_giu_nguyen_khi_dung_sr():
    song = tao_tieng(1.0)
    ra = chuan_hoa(song, SR, SR)
    assert ra.size == song.size


def test_chuan_hoa_int16_bien_do_nho():
    """Ban cu kiem kieu int SAU khi da doi sang float nen int16 nho tieng khong duoc chia 32768."""
    song = (tao_tieng(0.5, bien_do=0.001) * 32767).astype(np.int16)  # max ~33, < 1,5 cu
    ra = chuan_hoa(song, SR, SR)
    assert np.abs(ra).max() < 0.01


def test_chuan_hoa_audio_rong():
    assert chuan_hoa(np.zeros(0, dtype=np.float32), 44100, SR).size == 0


# ---------------- VAD ----------------
def test_vad_tim_duoc_mot_vung_noi():
    song = np.concatenate([tao_im_lang(0.5), tao_tieng(2.0), tao_im_lang(0.5)])
    vung = tim_vung_noi(song)
    assert len(vung) == 1, f"ky vong 1 vung, nhan {len(vung)}"
    b, e = vung[0]
    assert 0.3 < b < 0.8, f"bat dau ~0,5 s, nhan {b:.2f}"
    assert 2.2 < e < 2.8, f"ket thuc ~2,5 s, nhan {e:.2f}"


def test_vad_tach_hai_vung_cach_xa():
    # khoang lang 1 s > nguong gop 0,3 s -> phai thanh hai vung
    song = np.concatenate([tao_tieng(1.5), tao_im_lang(1.0), tao_tieng(1.5)])
    assert len(tim_vung_noi(song)) == 2


def test_vad_gop_hai_vung_cach_gan():
    # khoang lang 0,1 s < nguong gop -> coi la nghi hoi, gop lai
    song = np.concatenate([tao_tieng(1.5), tao_im_lang(0.1), tao_tieng(1.5)])
    assert len(tim_vung_noi(song)) == 1


def test_vad_audio_toan_im_lang():
    assert tim_vung_noi(tao_im_lang(3.0)) == []


# ---------------- chia doan ----------------
def test_audio_ngan_khong_bi_chia():
    doan = chia_doan(tao_tieng(10.0))
    assert len(doan) == 1
    assert doan[0].thoi_luong_s == pytest.approx(10.0, abs=0.1)


@pytest.mark.parametrize("thoi_luong", [35.0, 60.0, 125.0])
def test_audio_dai_bi_chia_va_moi_doan_duoi_30s(thoi_luong):
    """Day la kiem tra quan trong nhat: khong doan nao duoc qua 30 s.

    Ly do: o Task 2, nhom ban thu > 30 s co WER 94,70% vi PhoWhisper giai ma sai
    phan sau 30 giay. Chia doan la cach xu ly o muc he thong.
    """
    doan = chia_doan(tao_tieng(thoi_luong))
    assert len(doan) > 1, "audio dai phai bi chia"
    for d in doan:
        assert d.thoi_luong_s <= 30.0, f"doan {d.moc_thoi_gian()} dai {d.thoi_luong_s:.1f} s"
        assert d.thoi_luong_s <= MAX_DOAN_S + 0.5


def test_chia_doan_phu_het_audio():
    """Khong duoc mat phan nao cua audio co tieng noi."""
    song = tao_tieng(70.0)
    doan = chia_doan(song)
    tong = sum(d.song.size for d in doan)
    assert tong >= song.size * 0.98, f"chi phu {tong / song.size:.1%} audio"


def test_audio_ngan_bat_vad_van_giu_nguyen():
    """Loi Kiet tim ra: ban cu cat audio ngan thanh nhieu manh vun -> WER 34,79%.
    Audio <= 28 s phai giu 1 doan du co khoang lang ben trong."""
    cau = [tao_tieng(8.0), tao_tieng(8.0), tao_tieng(8.0)]
    song = np.concatenate([cau[0], tao_im_lang(1.0), cau[1], tao_im_lang(1.0), cau[2]])
    assert len(chia_doan(song, dung_vad=True)) == 1


def test_vad_cat_tai_khoang_lang_va_gom_doan():
    """Audio 38 s, ba cau 12 s: VAD gom 2 cau dau (25 s) thanh 1 doan, cau 3 thanh doan 2.
    Diem cat phai nam trong khoang lang thu hai (25 s - 26 s)."""
    cau = [tao_tieng(12.0), tao_tieng(12.0), tao_tieng(12.0)]
    song = np.concatenate([cau[0], tao_im_lang(1.0), cau[1], tao_im_lang(1.0), cau[2]])
    doan = chia_doan(song, dung_vad=True)
    assert len(doan) == 2, f"ky vong 2 doan, nhan {len(doan)}"
    assert 24.5 < doan[0].ket_thuc_s < 26.5
    for d in doan:
        assert d.thoi_luong_s <= MAX_DOAN_S


def test_vad_bat_tieng_noi_nho():
    """Loi Kiet tim ra: 28,9% file FLEURS test co RMS < -45 dBFS, nguong tuyet doi cu
    coi ca cau la im lang. Nguong tuong doi phai bat duoc tieng ~-55 dBFS."""
    song = np.concatenate([tao_im_lang(1.0), tao_tieng(3.0, bien_do=0.0025), tao_im_lang(1.0)])
    assert len(tim_vung_noi(song)) == 1


def test_mac_dinh_khong_dung_vad():
    """Mac dinh la cua so truot (cach da do voi model that)."""
    import inspect

    assert inspect.signature(chia_doan).parameters["dung_vad"].default is False


def test_chia_doan_tat_vad_dung_cua_so_truot():
    doan = chia_doan(tao_tieng(60.0), dung_vad=False)
    assert len(doan) > 1
    for d in doan:
        assert d.thoi_luong_s <= 30.0


def test_chia_doan_audio_rong():
    assert chia_doan(np.zeros(0, dtype=np.float32)) == []


def test_moc_thoi_gian_dinh_dang():
    song = np.concatenate([tao_tieng(8.0), tao_im_lang(1.0), tao_tieng(8.0)])
    doan = chia_doan(song)
    mt = doan[0].moc_thoi_gian()
    assert mt.count(":") == 2 and "-" in mt, f"dinh dang sai: {mt}"
    assert mt.startswith("00:00")


def test_doan_khong_qua_ngan():
    """Doan ngan hon 0,3 s thi bo, vi khong con la loi noi."""
    song = np.concatenate([tao_tieng(5.0), tao_im_lang(1.0), tao_tieng(0.05)])
    for d in chia_doan(song):
        assert d.thoi_luong_s >= 0.25


def test_cat_deu_doi_toi_khoang_lang_gan_diem_giua():
    """Loi demo 03/11: file 30,48 s cat dung 15,24 s giua tu -> "co the. co the".
    Co khoang lang 13,7-14,65 s thi diem cat phai roi vao do."""
    song = np.concatenate([tao_tieng(13.7), tao_im_lang(0.95), tao_tieng(15.83)])
    doan = chia_doan(song)
    assert len(doan) == 2
    assert 13.7 <= doan[0].ket_thuc_s <= 14.65
    assert doan[0].ket_thuc_s == doan[1].bat_dau_s


def test_cat_deu_khong_co_lang_thi_cat_giua():
    doan = chia_doan(tao_tieng(40.0))
    assert [round(d.ket_thuc_s, 1) for d in doan] == [20.0, 40.0]


def test_cat_deu_khong_lech_qua_3s_va_doan_duoi_28s():
    # khoang lang o 5 s, xa diem giua 20 s -> khong cat o do; moi doan van <= 28 s
    song = np.concatenate([tao_tieng(5), tao_im_lang(1), tao_tieng(34)])
    doan = chia_doan(song)
    assert all(d.thoi_luong_s <= MAX_DOAN_S for d in doan)
    assert abs(doan[0].ket_thuc_s - 20.0) <= 3.0


def test_cat_deu_audio_dai_nhieu_khoang_lang():
    # 20 cau 4,4 s, nghi 0,6 s (100 s): luon co khoang nghi trong +-3 s quanh diem cat deu,
    # nen moi diem cat phai roi vao mot khoang nghi
    cau = []
    for _ in range(20):
        cau += [tao_tieng(4.4), tao_im_lang(0.6)]
    song = np.concatenate(cau)
    doan = chia_doan(song)
    assert all(d.thoi_luong_s <= MAX_DOAN_S for d in doan)
    for d in doan[:-1]:
        trong_cau = d.ket_thuc_s % 5.0
        assert trong_cau >= 4.4 - 0.02, f"cat o {d.ket_thuc_s:.2f} s, giua cau"
    assert doan[-1].ket_thuc_s == pytest.approx(song.size / SR, abs=0.01)


# ---------------- ghep loi ----------------
def test_bo_lap_cho_noi_vi_du_demo():
    assert bo_lap_cho_noi("học sinh có thể.", "có thể xác định vai trò") == "xác định vai trò"


def test_bo_lap_cho_noi_khong_xoa_lap_1_tu():
    assert bo_lap_cho_noi("rất.", "rất vui") == "rất vui"


def test_bo_lap_cho_noi_khong_lap_thi_giu_nguyen():
    assert bo_lap_cho_noi("hôm nay trời đẹp", "chúng ta đi chơi") == "chúng ta đi chơi"
    assert bo_lap_cho_noi("", "có thể") == "có thể"


def test_ghep_loi_bo_phan_rong():
    assert ghep_loi(["xin chào", "", "  ", "hôm nay"]) == "xin chào hôm nay"


def test_ghep_loi_danh_sach_rong():
    assert ghep_loi([]) == ""


# ---------------- doc file ----------------
def test_doc_wav():
    import io
    import wave

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((tao_tieng(1.0) * 32767).astype("<i2").tobytes())
    song, sr = doc_audio_bytes(buf.getvalue())
    assert sr == SR and abs(song.size - SR) <= 1


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="can ffmpeg")
def test_doc_webm_qua_ffmpeg():
    """Loi Kiet tim ra: file ghi am .webm/.m4a bao 400 vi soundfile khong doc duoc."""
    kq = subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=220:duration=2",
            "-c:a",
            "libopus",
            "-f",
            "webm",
            "pipe:1",
        ],
        capture_output=True,
        check=False,
    )
    if kq.returncode != 0:
        pytest.skip("ffmpeg khong co libopus")
    song, sr = doc_audio_bytes(kq.stdout)
    assert sr == SR
    assert abs(song.size / sr - 2.0) < 0.2


def test_file_rac_bao_loi():
    with pytest.raises(Exception):  # noqa: B017
        doc_audio_bytes(b"\x00\x01rac" * 50)


def _ffmpeg_tao(fmt, codec):
    """Tao file 3 s, stereo, 44,1 kHz (opus chi nhan 48 kHz). Ghi ra file tam vi m4a/webm khong ghi duoc ra pipe."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as d:
        ra = Path(d) / f"a.{fmt}"
        kq = subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=220:duration=3",
                "-ar",
                "48000" if codec == "libopus" else "44100",
                "-ac",
                "2",
                "-c:a",
                codec,
                str(ra),
            ],
            capture_output=True,
            check=False,
        )
        if kq.returncode != 0 or not ra.exists():
            pytest.skip(f"ffmpeg khong tao duoc {fmt}/{codec}")
        return ra.read_bytes()


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="can ffmpeg")
@pytest.mark.parametrize(
    "fmt,codec",
    [
        ("mp3", "libmp3lame"),
        ("flac", "flac"),
        ("ogg", "libvorbis"),
        ("m4a", "aac"),
        ("webm", "libopus"),
    ],
)
def test_doc_cac_dinh_dang_da_cong_bo(fmt, codec):
    """F08: moi dinh dang README/API cong bo (mp3, flac, ogg, m4a, webm) deu doc duoc."""
    song, sr = doc_audio_bytes(_ffmpeg_tao(fmt, codec))
    x = chuan_hoa(song, sr)
    assert abs(x.size / SR - 3.0) < 0.15


def test_file_rong_bao_loi():
    with pytest.raises(Exception):  # noqa: B017
        doc_audio_bytes(b"")


def test_wav_bi_cat_cut_bao_loi_hoac_doc_duoc_mot_phan():
    """File wav hong (mat nua sau) khong duoc lam crash ngoai Exception thuong."""
    import io
    import wave

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((tao_tieng(2.0) * 32767).astype("<i2").tobytes())
    hong = buf.getvalue()[:30]
    try:
        song, _ = doc_audio_bytes(hong)
    except Exception:
        return
    assert song.size < SR


# ---------------- doc tep upload (F05 dot 2) ----------------
@pytest.mark.parametrize(
    "ten,noi_dung,chu",
    [
        ("rong.wav", b"", "rỗng"),
        ("hong.wav", b"RIFF\x10\x00\x00\x00WAVEfmt " + b"\x00" * 7, "hỏng"),
        ("van_ban.wav", "đây là văn bản, không phải audio".encode() * 20, "hỏng"),
    ],
)
def test_doc_tep_bao_loi_tieng_viet(tmp_path, ten, noi_dung, chu):
    p = tmp_path / ten
    p.write_bytes(noi_dung)
    with pytest.raises(ValueError) as e:
        doc_tep(str(p))
    assert chu in str(e.value)
    assert "Traceback" not in str(e.value) and "0x" not in str(e.value)


def test_doc_tep_qua_lon(tmp_path):
    p = tmp_path / "lon.wav"
    p.write_bytes(b"\0" * 2048)
    with pytest.raises(ValueError, match="vượt giới hạn"):
        doc_tep(str(p), max_mb=0.001)


def test_doc_tep_khong_co_tep():
    with pytest.raises(ValueError, match="Chưa có audio"):
        doc_tep(None)
