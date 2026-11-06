import hashlib
import json

import src.pipeline as pl

GOC = pl.GOC / "checkpoints"


def test_co_san_adapter_v2_v3_v4():
    for v in ("V2", "V3", "V4"):
        d = GOC / v / "best"
        assert (d / "adapter_model.safetensors").exists()
        cfg = json.loads((d / "adapter_config.json").read_text(encoding="utf-8"))
        assert cfg["peft_type"] == "LORA"
        assert cfg["r"] == 16 and cfg["lora_alpha"] == 32
        assert cfg["base_model_name_or_path"] == pl.MT_REPO


def test_adapter_khop_sha256():
    for dong in (GOC / "SHA256SUMS").read_text().splitlines():
        ma, ten = dong.split()
        assert hashlib.sha256((GOC / ten).read_bytes()).hexdigest() == ma


def test_mac_dinh_la_v2(monkeypatch):
    monkeypatch.delenv("ADAPTER_PATH", raising=False)
    assert pl.chon_adapter() == str(pl.ADAPTER_MAC_DINH)


def test_bien_moi_truong(monkeypatch):
    monkeypatch.setenv("ADAPTER_PATH", "checkpoints/V3/best")
    assert pl.chon_adapter().replace("\\", "/").endswith("checkpoints/V3/best")


def test_none_la_b0(monkeypatch):
    monkeypatch.setenv("ADAPTER_PATH", "none")
    assert pl.chon_adapter() is None


def test_sai_duong_dan_thi_bao_loi(monkeypatch):
    monkeypatch.setenv("ASR_BACKEND", "that")
    monkeypatch.setenv("ADAPTER_PATH", "khong_co/V9")
    try:
        pl.tao_backend()
    except FileNotFoundError:
        return
    raise AssertionError("phai bao loi khi khong thay adapter")


def test_mac_dinh_khop_ban_chot():
    """F06: app/API/CLI dung chung mot ban, va ban do khop configs/ban_chot.json."""
    chot = json.loads((pl.GOC / "configs" / "ban_chot.json").read_text(encoding="utf-8"))
    assert pl.GOC / chot["adapter"] == pl.ADAPTER_MAC_DINH
    assert chot["khong_dung_diem_test_de_chon"] is True


def test_ly_do_chot_v2_dung_so_dev():
    """So trong ly do chot (quy tac DEV) phai khop file score.json tren dev."""

    def bleu(p):
        return json.loads((GOC / p).read_text(encoding="utf-8"))["BLEU"]

    assert bleu("V3/best/dev_translate/score.json") == 26.71
    assert bleu("V4/best/dev_translate/score.json") == 26.33
    assert bleu("B0/dev_clean/score.json") == 37.57
    assert bleu("V2/best/dev_translate/score.json") == 26.45
    assert 26.71 - bleu("V2/best/dev_translate/score.json") <= 0.5  # V2 trong nhom hoa
    assert bleu("V2/best/dev_clean/score.json") == 36.93
    for v in ("V3", "V4"):
        assert bleu("V2/best/dev_clean/score.json") > bleu(f"{v}/best/dev_clean/score.json")
    chot = json.loads((pl.GOC / "configs" / "ban_chot.json").read_text(encoding="utf-8"))
    assert chot["ban_chot"] == "V2" and pl.ADAPTER_MAC_DINH.parent.name == "V2"
