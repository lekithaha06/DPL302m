"""Test FastAPI endpoint bang backend gia. Khong can GPU, khong nap trong so."""

import io
import os
import wave

import numpy as np
import pytest

os.environ["ASR_BACKEND"] = "gia"  # phai dat truoc khi import app

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def wav_bytes(thoi_luong_s=3.0, sr=16000, bien_do=0.3, n_kenh=1):
    t = np.arange(int(thoi_luong_s * sr)) / sr
    song = (bien_do * np.sin(2 * np.pi * 220 * t) * 32767).astype("<i2")
    if n_kenh == 2:
        song = np.repeat(song, 2)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(n_kenh)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(song.tobytes())
    return buf.getvalue()


# ---------------- health ----------------
def test_health_tra_ve_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    d = r.json()
    assert d["trang_thai"] == "ok"
    assert d["model_da_nap"] is True
    assert d["backend"] == "gia"


def test_openapi_co_san(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert "/dich" in r.json()["paths"]


# ---------------- duong di thuan ----------------
def test_dich_tra_du_truong(client):
    r = client.post("/dich", files={"file": ("a.wav", wav_bytes(3.0), "audio/wav")})
    assert r.status_code == 200, r.text
    d = r.json()
    for truong in (
        "transcript_vi",
        "ban_dich_en",
        "cac_doan",
        "thoi_luong_audio_s",
        "thoi_gian_nghe_s",
        "thoi_gian_dich_s",
        "rtf",
        "backend",
    ):
        assert truong in d, f"thieu truong {truong}"
    assert d["thoi_luong_audio_s"] == pytest.approx(3.0, abs=0.2)
    assert d["backend"] == "gia"
    assert len(d["cac_doan"]) == 1


def test_doan_co_moc_thoi_gian(client):
    r = client.post("/dich", files={"file": ("a.wav", wav_bytes(5.0), "audio/wav")})
    doan = r.json()["cac_doan"][0]
    assert doan["moc_thoi_gian"].count(":") == 2
    assert doan["bat_dau_s"] == pytest.approx(0.0, abs=0.1)


def test_audio_dai_bi_chia_nhieu_doan(client):
    """Audio 70 s phai thanh nhieu doan, moi doan duoi 30 s."""
    r = client.post("/dich", files={"file": ("dai.wav", wav_bytes(70.0), "audio/wav")})
    assert r.status_code == 200, r.text
    doan = r.json()["cac_doan"]
    assert len(doan) > 1, f"audio 70 s chi ra {len(doan)} doan"
    for d in doan:
        dai = d["ket_thuc_s"] - d["bat_dau_s"]
        assert dai <= 30.0, f"doan {d['moc_thoi_gian']} dai {dai:.1f} s"


def test_stereo_xu_ly_duoc(client):
    r = client.post("/dich", files={"file": ("st.wav", wav_bytes(2.0, n_kenh=2), "audio/wav")})
    assert r.status_code == 200, r.text


def test_sample_rate_khac_duoc_chuan_hoa(client):
    r = client.post("/dich", files={"file": ("hi.wav", wav_bytes(2.0, sr=44100), "audio/wav")})
    assert r.status_code == 200, r.text
    assert r.json()["thoi_luong_audio_s"] == pytest.approx(2.0, abs=0.2)


def test_tham_so_max_doan_s(client):
    r = client.post("/dich?max_doan_s=10", files={"file": ("a.wav", wav_bytes(45.0), "audio/wav")})
    assert r.status_code == 200, r.text
    for d in r.json()["cac_doan"]:
        assert d["ket_thuc_s"] - d["bat_dau_s"] <= 10.5


def test_tat_vad(client):
    r = client.post("/dich?dung_vad=false", files={"file": ("a.wav", wav_bytes(45.0), "audio/wav")})
    assert r.status_code == 200, r.text
    assert len(r.json()["cac_doan"]) > 1


# ---------------- dau vao xau ----------------
def test_file_rong_tra_400(client):
    r = client.post("/dich", files={"file": ("r.wav", b"", "audio/wav")})
    assert r.status_code == 400
    assert "rỗng" in r.json()["detail"].lower()


def test_dinh_dang_khong_ho_tro_tra_400(client):
    r = client.post("/dich", files={"file": ("a.txt", b"khong phai audio", "text/plain")})
    assert r.status_code == 400
    assert "txt" in r.json()["detail"]


def test_khong_co_duoi_file_tra_400(client):
    r = client.post("/dich", files={"file": ("noext", b"abc", "application/octet-stream")})
    assert r.status_code == 400


def test_file_hong_tra_400_khong_tra_500(client):
    """File co duoi .wav nhung noi dung rac -> phai la 400, khong duoc 500."""
    r = client.post("/dich", files={"file": ("h.wav", b"\x00\x01rac" * 50, "audio/wav")})
    assert r.status_code == 400, f"ky vong 400, nhan {r.status_code}: {r.text}"
    # khong lo chi tiet noi bo nhu "<_io.BytesIO object at 0x...>"
    assert "0x" not in r.json()["detail"] and "BytesIO" not in r.json()["detail"]


def test_audio_ngan_khong_bi_cat_vun(client):
    """Audio 20 s co khoang lang: mac dinh phai ra 1 doan."""
    r = client.post("/dich", files={"file": ("a.wav", wav_bytes(20.0), "audio/wav")})
    assert len(r.json()["cac_doan"]) == 1


def test_audio_toan_im_lang(client):
    """Toan im lang: tra 200 voi ket qua rong hoac 400, khong duoc treo hay bia ket qua."""
    r = client.post("/dich", files={"file": ("il.wav", wav_bytes(3.0, bien_do=0.0), "audio/wav")})
    assert r.status_code in (200, 400)
    if r.status_code == 200:
        assert r.json()["cac_doan"] == []


def test_thieu_file_tra_422(client):
    assert client.post("/dich").status_code == 422


def test_max_doan_s_qua_30_bi_tu_choi(client):
    """Khong cho dat max_doan_s > 30 vi do la gioi han cua khoi nghe."""
    r = client.post("/dich?max_doan_s=45", files={"file": ("a.wav", wav_bytes(5.0), "audio/wav")})
    assert r.status_code == 422


def test_backend_that_nap_loi_thi_bao_loi(monkeypatch):
    """Loi Kiet tim ra: thieu protobuf -> ban cu tu chuyen sang backend gia, tra chu gia
    ma nguoi dung khong biet. Bay gio phai bao loi."""
    import src.pipeline as pl

    def hong(*a, **k):
        raise ImportError("thieu protobuf")

    monkeypatch.setenv("ASR_BACKEND", "that")
    monkeypatch.setattr(pl, "ThatBackend", hong)
    with pytest.raises(RuntimeError, match="protobuf"):
        pl.tao_backend()


# ---------------- F11: API key ----------------
def test_api_key_chan_khi_thieu(client, monkeypatch):
    import api.main as m

    monkeypatch.setattr(m, "API_KEY", "bi-mat-123")
    f = {"file": ("a.wav", wav_bytes(2.0), "audio/wav")}
    assert client.post("/dich", files=f).status_code == 401
    assert client.post("/dich", files=f, headers={"X-API-Key": "sai"}).status_code == 401
    r = client.post("/dich", files=f, headers={"X-API-Key": "bi-mat-123"})
    assert r.status_code == 200
    assert client.get("/health").json()["can_api_key"] is True


def test_ket_qua_ghi_model_da_dung(client):
    r = client.post("/dich", files={"file": ("a.wav", wav_bytes(2.0), "audio/wav")})
    assert r.json()["mo_hinh"]


def test_10_request_lien_tiep_khong_lan_ket_qua(client):
    """F10: 10 luot lien tiep, moi luot tra dung thoi luong cua chinh no."""
    for k in range(10):
        giay = 1.0 + k
        r = client.post("/dich", files={"file": ("a.wav", wav_bytes(giay), "audio/wav")})
        assert r.status_code == 200
        assert r.json()["thoi_luong_audio_s"] == pytest.approx(giay, abs=0.05)
