"""F02: micro real-time. Gia lap Gradio gui tung mau 0,5 s trong luc dang thu."""

import numpy as np
import pytest

from src.audio import SR
from src.truc_tiep import GomTrucTiep


def sin(giay, sr=SR):
    t = np.arange(int(giay * sr)) / sr
    return (0.3 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


def cho_an(gom, song, sr=SR, mau_s=0.5):
    """Gui song thanh tung mau mau_s giay. Tra ve (doan, so mau da gui luc doan ra)."""
    ra = []
    n = int(mau_s * sr)
    for k in range(0, song.size, n):
        for d in gom.them(song[k : k + n], sr):
            ra.append((d, k // n + 1))
    return ra


def test_noi_35s_co_doan_truoc_khi_dung():
    gom = GomTrucTiep(cua_so_s=10, toi_da_s=20)
    ra = cho_an(gom, sin(35))
    assert len(ra) >= 1  # da co doan trong luc dang noi
    assert ra[0][1] <= 42  # doan dau ra truoc 21 s (42 mau 0,5 s)


def test_khong_mat_khong_lap_doan():
    gom = GomTrucTiep(cua_so_s=10, toi_da_s=20)
    song = sin(47.3)
    doan = [d for d, _ in cho_an(gom, song)] + gom.ket_thuc()
    assert doan[0][0] == 0.0
    for a, b in zip(doan, doan[1:], strict=False):
        assert a[1] == pytest.approx(b[0], abs=0.011)  # noi lien, khong ho, khong chong
    assert doan[-1][1] == pytest.approx(47.3, abs=0.02)  # flush phan cuoi khi dung
    tong_mau = sum(d[2].size for d in doan)
    assert abs(tong_mau - song.size) <= len(doan) * 2  # lech chi do lam tron resample


def test_noi_lien_tuc_cua_so_10_cat_20():
    """Noi lien tuc khong co khoang lang: cat o toi_da_s (20 s), o cho nho tieng nhat."""
    gom = GomTrucTiep(cua_so_s=10, toi_da_s=20)
    doan = [d for d, _ in cho_an(gom, sin(45))]
    assert len(doan) == 2
    assert doan[0][1] == pytest.approx(20.0, abs=0.15)
    assert doan[1][1] == pytest.approx(40.0, abs=0.15)


def test_moi_doan_duoi_30s():
    gom = GomTrucTiep(cua_so_s=10, toi_da_s=28)
    doan = [d for d, _ in cho_an(gom, sin(90))] + gom.ket_thuc()
    assert all(e - b <= 28.0 + 1e-6 for b, e, _ in doan)


def test_cat_tai_khoang_lang_khi_du_cua_so():
    """9 s noi, 0,6 s lang, 8 s noi: cat o giay 9,3 (giua khoang lang) sau khi den giay 10."""
    song = np.concatenate([sin(9), np.zeros(int(0.6 * SR), np.float32), sin(8)])
    gom = GomTrucTiep(cua_so_s=10, toi_da_s=20, lang_s=0.35)
    doan = [d for d, _ in cho_an(gom, song)]
    assert len(doan) == 1  # doan 1 ra ngay khi den giay ~10, chua can bam dung
    assert 9.1 <= doan[0][1] <= 9.5
    assert gom.ket_thuc()[0][0] == doan[0][1]


def test_noi_lien_tuc_khong_nghi_thi_cat_cho_nho():
    """Khong co khoang lang >= lang_s thi cat bat buoc o toi_da_s, chon khung nho nhat."""
    song = sin(35)
    gom = GomTrucTiep(cua_so_s=10, toi_da_s=20, lang_s=1.0)
    doan = [d for d, _ in cho_an(gom, song)]
    assert len(doan) >= 1
    assert 19.5 <= doan[0][1] <= 20.5


def test_mic_48k_int16_ve_16k():
    sr = 48000
    x = (sin(12, sr) * 32767).astype(np.int16)
    gom = GomTrucTiep(cua_so_s=10)
    doan = [d for d, _ in cho_an(gom, x, sr)] + gom.ket_thuc()
    assert doan[0][2].dtype == np.float32
    assert np.abs(doan[0][2]).max() <= 1.0
    tong_s = sum(d[2].size for d in doan) / SR
    assert tong_s == pytest.approx(12.0, abs=0.01)


def test_dung_ngay_khong_co_gi():
    assert GomTrucTiep().ket_thuc() == []


def test_cua_so_qua_30s_bi_chan():
    with pytest.raises(ValueError):
        GomTrucTiep(cua_so_s=35)


# ---------------- phien thu truc tiep (dung backend gia) ----------------
def _phien(cua_so_s=10, chay_lai=None):
    from src.pipeline import GiaBackend, HeThong
    from src.truc_tiep import PhienTrucTiep

    return PhienTrucTiep(
        HeThong(backend=GiaBackend()).xu_ly_doan, cua_so_s=cua_so_s, chay_lai=chay_lai
    )


def test_phien_cap_nhat_bang_trong_luc_thu():
    ph = _phien(cua_so_s=10)
    so_lan_moi = 0
    x = sin(35)
    for k in range(0, x.size, SR // 2):
        so_lan_moi += ph.them(x[k : k + SR // 2], SR)
    ph.ket_thuc()
    assert so_lan_moi >= 1 and len(ph.bang) >= 1
    assert ph.transcript_vi and ph.ban_dich_en


def test_phien_bo_doan_im_lang():
    ph = _phien()
    x = np.concatenate([sin(10), np.zeros(20 * SR, np.float32), sin(5)])
    for k in range(0, x.size, SR // 2):
        ph.them(x[k : k + SR // 2], SR)
    ph.ket_thuc()
    assert len(ph.bang) >= 1


def test_phien_chay_lai_ca_ban_khi_dung():
    """Chay_lai neu khac None: khi dung thu, he thong nhan dang lai toan bo."""

    def xu_ly(s, b, e, _=None):
        return "doan", "segment"

    def chay_lai_ca_ban(song):
        return [["00:00-00:35", "ca ban gop lai", "full transcript"]]

    from src.truc_tiep import PhienTrucTiep

    ph = PhienTrucTiep(xu_ly, cua_so_s=10, chay_lai=chay_lai_ca_ban)
    x = sin(35)
    for k in range(0, x.size, SR // 2):
        ph.them(x[k : k + SR // 2], SR)
    assert len(ph.bang) >= 1 and ph.bang[0][1] == "doan"  # trong luc thu: hien tung doan
    ph.ket_thuc()
    assert ph.bang_tam[0][1] == "doan"
    assert len(ph.bang) == 1
    assert ph.bang[0][1] == "ca ban gop lai"
    assert ph.da_chay_lai


def test_phien_loi_mot_doan_khong_dung_ca_luot():
    from src.truc_tiep import PhienTrucTiep

    dem = {"n": 0}

    def hong_lan_dau(song, b, e, _=None):
        dem["n"] += 1
        if dem["n"] == 1:
            raise RuntimeError("GPU het bo nho")
        return "vi", "en"

    ph = PhienTrucTiep(hong_lan_dau, cua_so_s=5)
    x = sin(12)
    for k in range(0, x.size, SR // 2):
        ph.them(x[k : k + SR // 2], SR)
    ph.ket_thuc()
    assert "GPU het bo nho" in ph.loi
    assert len(ph.bang) >= 1
