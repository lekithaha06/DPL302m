"""Test HeThong voi backend gia: im lang, giong nho, audio dai. Khong can GPU, khong can fastapi."""

import numpy as np

from src.audio import SR, la_im_lang
from src.pipeline import GiaBackend, HeThong


def sin(giay, bien_do=0.3):
    t = np.arange(int(giay * SR)) / SR
    return (bien_do * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


def im(giay):
    return np.zeros(int(giay * SR), dtype=np.float32)


def he(**k):
    return HeThong(backend=GiaBackend(), **k)


# ---------- F05: im lang ----------
def test_im_lang_3s_khong_sinh_chu():
    kq = he().xu_ly(im(3.0), SR)
    assert kq.cac_doan == []
    assert kq.transcript_vi == "" and kq.ban_dich_en == ""


def test_nhieu_nen_rat_nho_van_la_im_lang():
    rng = np.random.default_rng(0)
    nen = (rng.standard_normal(3 * SR) * 1e-4).astype(np.float32)  # khoang -80 dBFS
    assert la_im_lang(nen)
    assert he().xu_ly(nen, SR).cac_doan == []


def test_giong_nho_khong_bi_loc_oan():
    # -50 dBFS: duoi nguong tuyet doi -45 cu (lam hong 28,9% FLEURS) nhung van la tieng noi
    nho = sin(3.0, bien_do=10 ** (-50 / 20) * np.sqrt(2))
    assert not la_im_lang(nho)
    assert len(he().xu_ly(nho, SR).cac_doan) == 1


def test_audio_dai_bo_doan_im_lang_giu_doan_co_tieng():
    song = np.concatenate([sin(20), im(30), sin(20)])  # 70 s, doan giua im lang
    kq = he().xu_ly(song, SR)
    assert len(kq.cac_doan) == 2
    assert kq.cac_doan[0].bat_dau_s == 0.0
    assert kq.cac_doan[-1].ket_thuc_s == 70.0


def test_im_lang_int16_tu_micro():
    assert he().xu_ly(np.zeros(3 * SR, dtype=np.int16), SR).cac_doan == []


# ---------- F03: audio dai 1/3/5 phut ----------
def test_audio_1_3_5_phut_dung_moc_va_khong_mat_doan():
    for phut in (1, 3, 5):
        tong = phut * 60.0
        kq = he().xu_ly(sin(tong), SR)
        d = kq.cac_doan
        assert all(x.ket_thuc_s - x.bat_dau_s <= 28.0 + 1e-6 for x in d)
        assert d[0].bat_dau_s == 0.0
        assert abs(d[-1].ket_thuc_s - tong) < 0.02
        for a, b in zip(d, d[1:], strict=False):  # lien nhau, khong ho, khong chong
            assert abs(a.ket_thuc_s - b.bat_dau_s) < 0.02
        assert len(d) == int(np.ceil(tong / 28.0))
        assert kq.thoi_luong_audio_s == tong


def test_audio_28s_khong_bi_cat():
    assert len(he().xu_ly(sin(28.0), SR).cac_doan) == 1


# ---------- F08: sample rate, stereo ----------
def test_cac_sample_rate_deu_ve_dung_thoi_luong():
    for sr in (8000, 16000, 22050, 44100, 48000):
        t = np.arange(int(5 * sr)) / sr
        x = (0.3 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
        kq = he().xu_ly(x, sr)
        assert abs(kq.thoi_luong_audio_s - 5.0) < 0.02, sr
        assert len(kq.cac_doan) == 1


def test_stereo_44k():
    x = np.stack([sin(4), sin(4)], axis=1)
    assert len(he().xu_ly(x, SR).cac_doan) == 1


class _BackendCoDinh:
    """Tra loi ASR co dinh theo thu tu doan, ghi lai cau dua vao khoi dich."""

    ten = "gia"
    mo_hinh = "co dinh"

    def __init__(self, loi):
        self.loi = list(loi)
        self.da_dich = []

    def nghe(self, doan):
        return self.loi.pop(0)

    def dich(self, van_ban):
        self.da_dich.append(van_ban)
        return "en"


def _tieng(giay):
    t = np.arange(int(giay * SR)) / SR
    return (0.3 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


def test_bo_lap_cho_noi_va_doi_so_truoc_khi_dich():
    """Loi demo 03/11: 'hoc sinh co the.' + 'co the xac dinh' -> bo lap; so doi truoc khi dich."""
    be = _BackendCoDinh(["học sinh có thể.", "có thể xác định ngày mười một tháng ba"])
    kq = HeThong(backend=be).xu_ly(_tieng(40), SR)
    assert kq.transcript_vi == "học sinh có thể. xác định ngày 11 tháng 3"
    assert kq.transcript_vi_goc == "học sinh có thể. xác định ngày mười một tháng ba"
    assert be.da_dich == ["học sinh có thể.", "xác định ngày 11 tháng 3"]


def test_tat_doi_so(monkeypatch):
    monkeypatch.setenv("CHUAN_HOA_SO", "0")
    be = _BackendCoDinh(["ngày mười một tháng ba"])
    kq = HeThong(backend=be).xu_ly(_tieng(5), SR)
    assert kq.transcript_vi == "ngày mười một tháng ba"
