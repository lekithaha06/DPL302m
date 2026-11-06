"""Doi so doc bang chu (loi ASR) sang chu so truoc khi dich. Vi du lay tu loi that cua PhoWhisper."""

import json
from pathlib import Path

import pytest

from src.so import doi_so


@pytest.mark.parametrize(
    "vao,ra",
    [
        # cau nguoi dung noi o demo 03/11
        (
            "hôm nay là ngày mười một tháng ba năm hai nghìn không trăm hai mươi sáu",
            "hôm nay là ngày 11 tháng 3 năm 2026",
        ),
        ("ngày mười một tháng ba hai không hai sáu.", "ngày 11 tháng 3 2026."),
        # loi ASR that tren FLEURS dev/test
        ("một trăm lẻ tám đĩa", "108 đĩa"),
        ("một trăm linh tám đĩa", "108 đĩa"),
        ("trên mười chín ngàn năm trăm km", "trên 19.500 km"),
        ("trên 19 ngàn năm trăm km", "trên 19.500 km"),
        ("vào năm một ngàn bảy trăm sáu mươi bảy đường", "vào năm 1767 đường"),
        ("với gần bảy ngàn đảo", "với gần 7.000 đảo"),
        ("tám trăm ngàn", "800.000"),
        ("tới tám trăm triệu người", "tới 800 triệu người"),
        ("hai phẩy ba triệu galông", "2,3 triệu galông"),
        ("mười bốn phẩy bảy tỷ usd", "14,7 tỷ usd"),
        ("xuân năm hai không mười sáu.", "xuân năm 2016."),
        ("hai không lẻ chín.", "2009."),
        ("năm một chín tám tám", "năm 1988"),
        ("hai mươi mốt tuổi", "21 tuổi"),
        ("hai mươi tư giờ", "24 giờ"),
        ("ba mươi lăm", "35"),
        ("tháng mười hai", "tháng 12"),
        ("năm mươi phần trăm", "50%"),
        ("ozil david hai nghìn không trăm linh hai.", "ozil david 2002."),
    ],
)
def test_doi_dung(vao, ra):
    assert doi_so(vao) == ra


@pytest.mark.parametrize(
    "cau",
    [
        "một số ca mắc bệnh",  # 1 tu don: khong doi
        "ba người, hai con",
        "thứ bảy và thứ hai",  # thu trong tuan
        "một hai ba bốn",  # dem, khong phai nam (khong co "nam" dung truoc)
        "hai người đi chơi",
        "",
    ],
)
def test_khong_doi_nham(cau):
    assert doi_so(cau) == cau


def test_nam_sau_so():
    """ "hai muoi nam" = 20 nam (khong doc thanh 25), "hai trieu nam" = 2 trieu nam."""
    assert doi_so("hai mươi năm qua") == "20 năm qua"
    assert doi_so("hai triệu năm") == "2 triệu năm"
    assert doi_so("một trăm năm") == "100 năm"


def test_hai_so_lien_nhau():
    assert doi_so("ba mươi ba mươi mốt.") == "30 31."
    assert doi_so("hai mươi sáu hai mươi bảy.") == "26 27."


def test_khong_doc_qua_dau_phay():
    assert doi_so("ba mươi, hai mươi") == "30, 20"


GOC = Path(__file__).resolve().parents[1]
DEV = GOC / "experiments" / "runs" / "mt_data"


@pytest.mark.skipif(not (DEV / "fleurs_dev_asr_pho.jsonl").exists(), reason="thieu du lieu dev")
def test_dev_fleurs_so_khop_tham_chieu_nhieu_hon():
    """Tren 361 loi ASR dev: so cac con so trung voi cau tham chieu phai tang ro (0 -> >= 60 / 88).
    So lieu luc viet (04/11/2026): truoc 0, sau 72; thua 29; thieu 16."""
    import re

    asr = [
        json.loads(x)
        for x in (DEV / "fleurs_dev_asr_pho.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    sach = {
        json.loads(x)["id"]: json.loads(x)["src"]
        for x in (DEV / "fleurs_dev_clean.jsonl").read_text(encoding="utf-8").splitlines()
    }

    def so(s):
        return set(re.findall(r"\d+", s.replace(".", "")))

    truoc = sau = 0
    for r in asr:
        g = so(sach[r["id"]])
        truoc += len(g & so(r["src"]))
        sau += len(g & so(doi_so(r["src"])))
    assert truoc <= 2 and sau >= 60
