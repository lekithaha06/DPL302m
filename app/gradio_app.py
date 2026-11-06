"""Demo Gradio: nhan dang giong noi tieng Viet va dich sang tieng Anh.

Dap ung yeu cau 5.1.8: giao dien co upload file va nut thu am, hien transcript
tieng Viet va ban dich tieng Anh. Yeu cau 5.1.2: xu ly ca offline va real-time,
hien ket qua theo tung doan kem moc thoi gian.

Hai che do, chon bang bien moi truong CHE_DO:
  CHE_DO=tu_nap  (mac dinh)  app tu nap model. Don gian, chay mot may.
  CHE_DO=api                 app goi service API qua HTTP. Dung khi chay
                             docker compose, giao dien khong can torch.

Chay:  python app/gradio_app.py
       CHE_DO=api API_URL=http://localhost:8000 python app/gradio_app.py
       GRADIO_SHARE=1 python app/gradio_app.py      # tao link public
"""

from __future__ import annotations

import io
import logging
import os
import sys
import wave
from pathlib import Path

# tat gui thong ke ra ngoai (checkip.amazonaws.com, api.gradio.app), phai dat truoc import gradio
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import gradio as gr
import numpy as np

# App viet cho Gradio 4.x. Gradio 5/6 doi API (vd bo show_copy_button) nen app crash
# ngay luc dung giao dien. Bao ro thay vi de nguoi dung doc traceback.
if not gr.__version__.startswith("4."):
    raise SystemExit(
        f"Dang cai gradio {gr.__version__}, app can gradio 4.44.1. Chay:\n"
        "  pip install gradio==4.44.1 fastapi==0.115.6 pydantic==2.10.6"
    )

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

CHE_DO = os.environ.get("CHE_DO", "tu_nap").lower()
API_URL = os.environ.get("API_URL", "http://localhost:8000").rstrip("/")

API_KEY = os.environ.get("API_KEY", "")
CUA_SO_TRUC_TIEP_S = float(os.environ.get("CUA_SO_TRUC_TIEP_S", "10"))
# Dung thu thi nhan dang lai ca ban thu bang duong cua tab tai tep (mac dinh bat, tat: 0)
CHAY_LAI_KHI_DUNG = os.environ.get("CHAY_LAI_KHI_DUNG", "1") != "0"
# Thu muc luu WAV tho + WAV 16 kHz + tung doan cua moi luot micro, de truy loi. Trong = khong luu
LUU_MIC = os.environ.get("LUU_MIC", "")

from src.audio import doc_tep
from src.truc_tiep import PhienTrucTiep

_he_thong = None
if CHE_DO != "api":
    from src.pipeline import HeThong  # can torch, chi import khi tu nap

    log.info("dang nap model, lan dau co the mat vai phut ...")
    _he_thong = HeThong()  # nap loi thi dung luon, khong chay voi model gia
    MO_HINH = _he_thong.backend.mo_hinh
    log.info("che do tu_nap, backend=%s, %s", _he_thong.backend.ten, MO_HINH)
else:
    MO_HINH = f"service API {API_URL}"
    log.info("che do api, goi %s", API_URL)


CSS = """
.cot-ket-qua textarea { font-size: 15px !important; line-height: 1.55 !important; }
footer { display: none !important; }
"""

GIOI_HAN = """
### Giới hạn đã biết của hệ thống

Những điều này đo được ở Task 2, nên cần biết trước khi tin vào kết quả:

- Hệ chỉ được đo trên **audio đọc rõ, một người nói, phòng yên tĩnh**. Chưa đo với hội thoại tự nhiên, nhiều người nói chồng tiếng hay môi trường ồn.
- Tập đánh giá FLEURS dev và test đều **100% giọng nam**, nên chưa có cơ sở kết luận hệ hoạt động như nhau với giọng nữ.
- Hệ làm tốt nhất ở **miền Giáo dục** (BLEU 31,45, WER khối nghe 10,76%) và kém nhất ở miền Tin tức (BLEU 22,51, WER 19,18%). Nguyên nhân chính của phần kém là tên riêng nước ngoài.
- **Tên riêng thường bị nghe sai** và lỗi đó không sửa được ở khâu dịch. Ví dụ "Aristotle" bị nghe thành "arizona".
- Bản dịch có thể **rút gọn làm mất chi tiết**: 4 trên 361 câu dev có bản dịch ngắn hơn 0,7 lần tham chiếu (V2).
- Audio dài hơn 28 giây được **chia đoạn** trước khi nhận dạng. Đưa thẳng audio dài hơn 30 giây vào khối nghe thì WER lên tới 94,70%; chia đoạn: 10 bản thu dài hơn 28 s của FLEURS test: WER 15,59%, BLEU 18,74 (đưa thẳng audio > 30 s vào khối nghe thì WER lên tới 94,70%).
- Toàn bộ hệ thống đo trên 857 bản thu FLEURS test: **WER 12,26%, BLEU 28,15, chrF++ 53,10 (adapter V2, đo 04/11/2026, `experiments/reports/he_thong_V2/`)**.
- Audio dài hơn 28 giây: điểm cắt được dời tới **chỗ ngắt nghỉ** gần nhất (trong ±3 s), chữ lặp ở chỗ nối được bỏ.
- Số đọc bằng chữ được đổi sang chữ số trước khi dịch ("mười một tháng ba" → "11 tháng 3"). Nếu khối nghe đã nghe sai thì không sửa được: ví dụ "hôm nay" nghe thành "có may" là lỗi của PhoWhisper (khối nghe không fine-tune).
- Thu âm trực tiếp: trong lúc nói, cắt đoạn khi bạn **ngừng nghỉ** sau khoảng 10 giây (nói liền thì cắt ở 20 giây). Khi bấm Stop, **cả bản thu được nhận dạng lại** giống tab tải tệp, nên kết quả cuối không bị cắt giữa câu. Chưa đo WER với micro thật.

Đây là công cụ hỗ trợ, không dùng cho mục đích cần độ chính xác cao như dịch văn bản pháp lý hay y tế.
"""


def _wav(song: np.ndarray, sr: int) -> bytes:
    x = np.asarray(song)
    if x.ndim > 1:
        x = x.mean(axis=1)
    if not np.issubdtype(x.dtype, np.integer):
        x = np.clip(x, -1.0, 1.0) * 32767
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(sr))
        w.writeframes(x.astype("<i2").tobytes())
    return buf.getvalue()


def _goi_api(song: np.ndarray, sr: int, dung_vad: bool, max_doan_s: float) -> dict:
    """Dong goi audio thanh WAV roi POST len service API."""
    import httpx

    try:
        r = httpx.post(
            f"{API_URL}/dich",
            files={"file": ("thu_am.wav", _wav(song, sr), "audio/wav")},
            params={"dung_vad": str(dung_vad).lower(), "max_doan_s": max_doan_s},
            headers={"X-API-Key": API_KEY} if API_KEY else {},
            timeout=300.0,
        )
    except httpx.TransportError as e:
        raise RuntimeError(
            f"Không kết nối được API {API_URL} ({type(e).__name__}). "
            "Kiểm tra service api đã chạy chưa."
        ) from None
    if r.status_code != 200:
        try:
            chi_tiet = r.json().get("detail", r.text)
        except ValueError:
            chi_tiet = r.text[:200]
        raise RuntimeError(f"API trả {r.status_code}: {chi_tiet}")
    return r.json()


def _goi_tu_nap(song: np.ndarray, sr: int, dung_vad: bool, max_doan_s: float) -> dict:
    from src.pipeline import HeThong

    he = HeThong(backend=_he_thong.backend, max_doan_s=max_doan_s, dung_vad=dung_vad)
    return he.xu_ly(np.asarray(song), int(sr)).dict()


def _canh_bao(backend: str) -> str:
    if backend == "gia":
        return (
            "  ·  **CẢNH BÁO: đang chạy backend giả, kết quả không có nghĩa.** "
            "Đặt ASR_BACKEND=that để dùng model thật."
        )
    return ""


def bao_dang_xu_ly():
    """Chay ngay khi bam nut: xoa ket qua cu de khong nham voi lan truoc."""
    return "", "", [], "⏳ **Đang xử lý...** Audio dài có thể mất vài chục giây."


MAX_MB = int(os.environ.get("MAX_UPLOAD_MB", "50"))


def xu_ly(duong_dan, dung_vad: bool, max_doan_s: float):
    """duong_dan: tep tu gr.Audio(type="filepath"), hoac None."""
    try:
        song, sr = doc_tep(duong_dan, MAX_MB)
    except ValueError as e:
        return "", "", [], f"❌ {e}"

    try:
        d = (_goi_api if CHE_DO == "api" else _goi_tu_nap)(song, sr, dung_vad, max_doan_s)
    except Exception as e:
        log.exception("loi khi xu ly audio")
        return "", "", [], f"❌ **Lỗi khi xử lý:** {type(e).__name__}: {e}. Có thể thử lại."

    doan = d.get("cac_doan") or []
    if not doan:
        return "", "", [], "Không tìm thấy tiếng nói trong audio (có thể toàn khoảng lặng)."

    bang = [[x["moc_thoi_gian"], x["transcript_vi"], x["ban_dich_en"]] for x in doan]
    tom_tat = (
        f"✅ Thời lượng audio **{d['thoi_luong_audio_s']:.1f} s**  ·  "
        f"chia thành **{len(doan)} đoạn**  ·  "
        f"nghe **{d['thoi_gian_nghe_s']:.2f} s** + dịch **{d['thoi_gian_dich_s']:.2f} s** "
        f"= **{d['thoi_gian_tong_s']:.2f} s**  ·  "
        f"RTF **{d['rtf']:.3f}**  ·  {d.get('mo_hinh', '')}" + _canh_bao(d.get("backend", ""))
    )
    return d["transcript_vi"], d["ban_dich_en"], bang, tom_tat


# ---------------- thu am truc tiep (F02) ----------------
def _xu_ly_doan_truc_tiep(song_16k: np.ndarray, b: float, e: float, loi_truoc: str = ""):
    """Nhan dang 1 doan <= 28 s. Tra (vi, en, loi_goc) hoac None neu im lang."""
    if CHE_DO == "api":
        d = _goi_api(song_16k, 16000, False, 28.0)
        if not d.get("cac_doan"):
            return None
        return d["transcript_vi"], d["ban_dich_en"], d.get("transcript_vi_goc", "")
    return _he_thong.xu_ly_doan(song_16k, b, e, loi_truoc)


def _chay_lai_ca_ban(song_16k: np.ndarray):
    """Dung thu: nhan dang lai ca ban thu bang dung duong cua tab tai tep."""
    d = (_goi_api if CHE_DO == "api" else _goi_tu_nap)(song_16k, 16000, False, 28.0)
    return [
        [x["moc_thoi_gian"], x["transcript_vi"], x["ban_dich_en"]] for x in d.get("cac_doan") or []
    ]


def _phien_moi():
    return PhienTrucTiep(
        _xu_ly_doan_truc_tiep,
        cua_so_s=CUA_SO_TRUC_TIEP_S,
        chay_lai=_chay_lai_ca_ban if CHAY_LAI_KHI_DUNG else None,
        luu_vao=LUU_MIC or None,
    )


def _hien_phien(ph: PhienTrucTiep | None, dang_thu: bool):
    if ph is None:
        return "", "", [], ""
    if dang_thu:
        trang_thai = (
            f"🔴 **Đang thu** {ph.da_thu_s:.0f} s · đã xử lý {len(ph.bang)} đoạn "
            f"(cắt khi bạn ngừng nghỉ, sau khoảng {CUA_SO_TRUC_TIEP_S:.0f} s)"
        )
    else:
        trang_thai = (
            f"✅ **Đã dừng** · {ph.da_thu_s:.1f} s · {len(ph.bang)} đoạn có tiếng nói"
            + (" · đã nhận dạng lại cả bản thu" if ph.da_chay_lai else "")
            + f" · {MO_HINH}"
        )
        if getattr(ph, "thu_muc_luu", None):
            trang_thai += f" · đã lưu `{ph.thu_muc_luu}`"
    if ph.loi:
        trang_thai += f"  ·  ❌ {ph.loi}"
    return ph.transcript_vi, ph.ban_dich_en, [r[:] for r in ph.bang], trang_thai


def bat_dau_thu():
    ph = _phien_moi()
    return (ph, *_hien_phien(ph, True))


def nhan_mau(mau, ph: PhienTrucTiep | None):
    """Gradio goi lien tuc trong luc thu, moi lan mot mau nho (sr, int16)."""
    if ph is None:
        ph = _phien_moi()
    if mau is not None:
        sr, x = mau
        if x is not None and np.asarray(x).size:
            ph.them(x, int(sr))
    return (ph, *_hien_phien(ph, True))


def dung_thu(ph: PhienTrucTiep | None):
    if ph is not None:
        ph.ket_thuc()  # xu ly not phan cuoi chua du cua so
    return (ph, *_hien_phien(ph, False))


with gr.Blocks(
    title="ASR tiếng Việt → dịch tiếng Anh", css=CSS, theme=gr.themes.Soft(primary_hue="teal")
) as demo:
    gr.Markdown(
        "# Nhận dạng giọng nói tiếng Việt và dịch sang tiếng Anh\n"
        "Kiến trúc cascade: **PhoWhisper-small** → **VinAI Translate + adapter LoRA**. "
        f"Đang dùng: `{MO_HINH}`"
    )

    with gr.Tab("Tải tệp lên"):
        with gr.Row():
            with gr.Column(scale=2):
                # gr.File chu khong phai gr.Audio: gr.Audio giai ma file ngay khi nhan, file
                # rong/hong lam Gradio loi truoc callback va chi hien "AppError" chung chung
                a_file = gr.File(
                    type="filepath",
                    file_count="single",
                    file_types=[".wav", ".mp3", ".flac", ".m4a", ".ogg", ".webm"],
                    label="Tệp audio (wav, mp3, flac, m4a, ogg, webm)",
                )
                nut_file = gr.Button("Nhận dạng và dịch", variant="primary")
            with gr.Column(scale=1):
                gr.Markdown("**Tuỳ chọn xử lý**")
                c_vad = gr.Checkbox(
                    value=False,
                    label="Cắt audio dài tại khoảng lặng (VAD)",
                    info="Chỉ dùng cho audio dài hơn 28 s. Mặc định tắt: chia đều, đã đo kỹ hơn",
                )
                c_max = gr.Slider(
                    5,
                    30,
                    value=28,
                    step=1,
                    label="Độ dài tối đa mỗi đoạn (giây)",
                    info="Phải dưới 30 s: khối nghe giải mã sai phần sau 30 giây",
                )
        f_tom_tat = gr.Markdown()
        with gr.Row():
            f_vi = gr.Textbox(
                label="Transcript tiếng Việt",
                lines=7,
                show_copy_button=True,
                elem_classes="cot-ket-qua",
            )
            f_en = gr.Textbox(
                label="Bản dịch tiếng Anh",
                lines=7,
                show_copy_button=True,
                elem_classes="cot-ket-qua",
            )
        f_bang = gr.Dataframe(
            headers=["Mốc thời gian", "Transcript tiếng Việt", "Bản dịch tiếng Anh"],
            datatype=["str", "str", "str"],
            label="Kết quả theo từng đoạn",
            wrap=True,
        )

    with gr.Tab("Thu âm trực tiếp"):
        gr.Markdown(
            f"Bấm **Record** rồi nói. Sau khoảng **{CUA_SO_TRUC_TIEP_S:.0f} giây**, lúc bạn ngừng nghỉ, hệ "
            "nhận dạng và dịch một đoạn, kết quả hiện ngay trong lúc bạn vẫn nói. Bấm **Stop**: cả bản thu "
            "được nhận dạng lại một lần cho kết quả cuối (không bị cắt giữa câu). "
            'Nói rõ, gần micro; đọc số như bình thường ("ngày mười một tháng ba").'
        )
        a_mic = gr.Audio(
            sources=["microphone"], type="numpy", streaming=True, label="Micro (thu trực tiếp)"
        )
        phien = gr.State(None)
        m_tom_tat = gr.Markdown()
        with gr.Row():
            m_vi = gr.Textbox(
                label="Transcript tiếng Việt",
                lines=7,
                show_copy_button=True,
                elem_classes="cot-ket-qua",
            )
            m_en = gr.Textbox(
                label="Bản dịch tiếng Anh",
                lines=7,
                show_copy_button=True,
                elem_classes="cot-ket-qua",
            )
        m_bang = gr.Dataframe(
            headers=["Mốc thời gian", "Transcript tiếng Việt", "Bản dịch tiếng Anh"],
            datatype=["str", "str", "str"],
            label="Kết quả theo từng đoạn",
            wrap=True,
        )

    with gr.Accordion("Giới hạn đã biết của hệ thống — nên đọc", open=False):
        gr.Markdown(GIOI_HAN)

    ra_file = [f_vi, f_en, f_bang, f_tom_tat]
    nut_file.click(bao_dang_xu_ly, None, ra_file, queue=False).then(
        xu_ly, [a_file, c_vad, c_max], ra_file
    )
    a_file.change(
        lambda: ("", "", [], ""), None, ra_file, queue=False
    )  # tai tep moi -> xoa ket qua cu

    ra_mic = [phien, m_vi, m_en, m_bang, m_tom_tat]
    a_mic.start_recording(bat_dau_thu, None, ra_mic)
    # trigger_mode="multiple": khong bo mau nao khi lan xu ly truoc chua xong (bo mau = mat chu)
    a_mic.stream(nhan_mau, [a_mic, phien], ra_mic, trigger_mode="multiple", show_progress="hidden")
    a_mic.stop_recording(dung_thu, [phien], ra_mic)


if __name__ == "__main__":
    # 1 GPU: moi luc chi 1 lan xu ly, cac lan bam khac xep hang (giao dien hien vi tri hang doi)
    demo.queue(default_concurrency_limit=1, max_size=20)
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", "7860")),
        share=os.environ.get("GRADIO_SHARE") == "1",
    )
