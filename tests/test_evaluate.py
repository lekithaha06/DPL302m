"""Test scorer. Cac truong hop toan hoc duoc kiem bang tay, khong can model.

Scorer nay da duoc doi chieu voi ket qua that cua goi task3 va tra ve dung
tung con so S/D/I/N:
    PhoWhisper VIVOS test   WER 6,24  S/D/I/N = 448/21/13/7722
    PhoWhisper VIVOS test   CER 3,25  544/167/129/25809
    PhoWhisper FLEURS test  WER 13,68 2057/113/1389/26021
"""

import pytest

from src.evaluate import MOC_TASK2, chuan_hoa_vi, tinh_bleu, tinh_wer


# ---------------- chuan hoa ----------------
def test_chuan_hoa_viet_thuong_va_bo_dau_cau():
    assert chuan_hoa_vi("Xin chào, bạn!") == "xin chào bạn"


def test_chuan_hoa_giu_dau_thanh():
    """Dau thanh phai giu: 'tỉnh' va 'tính' la hai tu khac nhau."""
    assert chuan_hoa_vi("TỈNH") != chuan_hoa_vi("TÍNH")
    assert chuan_hoa_vi("TỈNH") == "tỉnh"


def test_chuan_hoa_gop_khoang_trang():
    assert chuan_hoa_vi("a   b \n c") == "a b c"


def test_chuan_hoa_khong_doi_chu_so():
    """Khong doi 802 thanh 'tam khong hai': doi la lam sai WER."""
    assert "802" in chuan_hoa_vi("Chuẩn 802.11n")


def test_chuan_hoa_doi_xung():
    """Cung mot ham phai ap cho ca tham chieu va du doan."""
    assert chuan_hoa_vi("Hà Nội.") == chuan_hoa_vi("hà nội")


# ---------------- WER ----------------
def test_wer_khop_hoan_toan_bang_khong():
    assert tinh_wer([("xin chào bạn", "xin chào bạn")])["gia_tri"] == 0.0


def test_wer_mot_thay_the():
    """1 thay the tren 3 tu = 33,33%."""
    kq = tinh_wer([("công văn tỉnh", "công văn tính")])
    assert kq["S"] == 1 and kq["D"] == 0 and kq["I"] == 0 and kq["N"] == 3
    assert kq["gia_tri"] == pytest.approx(33.33, abs=0.01)


def test_wer_mot_thieu_tu():
    kq = tinh_wer([("trang phục một màu", "trang phục màu")])
    assert kq["D"] == 1 and kq["N"] == 4
    assert kq["gia_tri"] == 25.0


def test_wer_mot_them_tu():
    kq = tinh_wer([("đó là quà", "unk đó là quà")])
    assert kq["I"] == 1 and kq["S"] == 0 and kq["D"] == 0
    assert kq["gia_tri"] == pytest.approx(33.33, abs=0.01)


def test_wer_du_doan_rong_tinh_het_la_xoa():
    kq = tinh_wer([("một hai ba", "")])
    assert kq["D"] == 3 and kq["gia_tri"] == 100.0


def test_wer_co_the_vuot_100():
    """Nhieu insertion thi WER > 100%, khong chan o 100."""
    kq = tinh_wer([("một", "một hai ba bốn năm")])
    assert kq["gia_tri"] > 100.0


def test_wer_corpus_cong_counts_khong_trung_binh():
    """WER corpus = tong(S+D+I)/tong(N), khong phai trung binh WER tung cau.

    Cau 1: 1 loi tren 1 tu = 100%. Cau 2: 0 loi tren 9 tu = 0%.
    Trung binh cau se ra 50%, nhung WER corpus dung la 1/10 = 10%.
    """
    cap = [("a", "b"), ("một hai ba bốn năm sáu bảy tám chín",) * 2]
    kq = tinh_wer([cap[0], (cap[1][0], cap[1][1])])
    assert kq["N"] == 10
    assert kq["gia_tri"] == 10.0, "phải cộng counts rồi chia, không lấy trung bình câu"


def test_wer_tham_chieu_rong_bi_chan():
    """Tham chieu rong sau chuan hoa phai bao loi, khong duoc bo qua im lang."""
    with pytest.raises(ValueError):
        tinh_wer([("...", "có chữ")])


# ---------------- CER ----------------
def test_cer_tinh_theo_ky_tu():
    """'tỉnh' -> 'tính': khac 1 ky tu tren 4 ky tu = 25%."""
    kq = tinh_wer([("tỉnh", "tính")], muc_ky_tu=True)
    assert kq["N"] == 4 and kq["S"] == 1
    assert kq["gia_tri"] == 25.0


def test_cer_bo_khoang_trang():
    kq = tinh_wer([("a b", "ab")], muc_ky_tu=True)
    assert kq["gia_tri"] == 0.0, "CER phải bỏ khoảng trắng trước khi so"


def test_cer_thuong_nho_hon_wer():
    """Sai mot ky tu trong mot tu dai thi CER thap hon WER nhieu."""
    cap = [("nghiên cứu khoa học", "nghiên cứu khoa hạc")]
    assert tinh_wer(cap, muc_ky_tu=True)["gia_tri"] < tinh_wer(cap)["gia_tri"]


# ---------------- moc Task 2 ----------------
def test_moc_task2_co_du_cac_so_chinh():
    for k in ("wer_phowhisper_vivos", "wer_phowhisper_fleurs", "bleu_v3_cascade"):
        assert k in MOC_TASK2


def test_moc_task2_dung_gia_tri_bao_cao():
    """Chot cac so da bao cao, de ai sua lech thi test bao ngay."""
    assert MOC_TASK2["wer_phowhisper_vivos"] == 6.24
    assert MOC_TASK2["wer_phowhisper_fleurs"] == 13.68
    assert MOC_TASK2["bleu_b0_cascade"] == 22.69
    assert MOC_TASK2["bleu_v3_cascade"] == 27.33
    assert MOC_TASK2["bleu_b0_sach"] == 38.27


# ---------------- BLEU ----------------
def test_bleu_chay_duoc_va_co_signature():
    """Loi Kiet tim ra: ban cu crash vi goi get_signature() tren BLEUScore."""
    pytest.importorskip("sacrebleu")
    cap = [
        ("the cat sat on the mat", "the cat sat on the mat"),
        ("hello world again today", "hello world again today"),
    ]
    kq = tinh_bleu(cap)
    assert kq["gia_tri"] == pytest.approx(100.0)
    assert "nrefs:1" in kq["bleu_signature"]
    assert kq["chrF++"] == pytest.approx(100.0)


def test_bleu_cau_sai_thap_hon():
    pytest.importorskip("sacrebleu")
    dung = tinh_bleu([("the cat sat on the mat", "the cat sat on the mat")])["gia_tri"]
    sai = tinh_bleu([("the cat sat on the mat", "a dog ran in a park")])["gia_tri"]
    assert sai < dung
