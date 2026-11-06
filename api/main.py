"""FastAPI service cho he thong ASR tieng Viet + dich tieng Anh.

Chay:  uvicorn api.main:app --host 0.0.0.0 --port 8000
Tai lieu endpoint tu sinh: http://localhost:8000/docs

Model nap mot lan luc khoi dong (lifespan), khong nap lai moi request.
Nap model that loi thi service dung luon (khong tu chuyen sang model gia).
"""

from __future__ import annotations

import hmac
import logging
import os
import threading
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.audio import doc_audio_bytes
from src.pipeline import HeThong

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

MAX_MB = int(os.environ.get("MAX_UPLOAD_MB", "50"))
# Dat API_KEY khi mo API ra ngoai (deploy public): /dich bat buoc header X-API-Key.
# De trong = khong kiem (chi nen dung khi chay tren may minh).
API_KEY = os.environ.get("API_KEY", "")
DUOI_CHO_PHEP = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".webm"}

_he_thong: HeThong | None = None
# chi 1 GPU va 1 bo trong so: cho tung request chay lan luot, tranh tran VRAM
_khoa = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _he_thong
    log.info("khoi dong, nap model")
    _he_thong = HeThong()
    log.info("san sang, backend=%s, %s", _he_thong.backend.ten, _he_thong.backend.mo_hinh)
    if not API_KEY:
        log.warning("API_KEY chua dat: /dich mo cho moi nguoi. Dat API_KEY truoc khi public.")
    yield
    _he_thong = None


app = FastAPI(
    title="ASR tiếng Việt + dịch tiếng Anh",
    description=(
        "Nhận audio tiếng Việt, trả transcript tiếng Việt và bản dịch tiếng Anh "
        "kèm mốc thời gian từng đoạn. Kiến trúc cascade: PhoWhisper-small → "
        "VinAI Translate + adapter LoRA."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------- schema ----------------
class DoanRa(BaseModel):
    moc_thoi_gian: str = Field(..., description="Dạng mm:ss-mm:ss", examples=["00:00-00:12"])
    bat_dau_s: float
    ket_thuc_s: float
    transcript_vi: str
    ban_dich_en: str
    transcript_vi_goc: str = Field("", description="Lời ASR nguyên bản, trước khi đổi số")


class KetQuaRa(BaseModel):
    transcript_vi: str = Field(..., description="Transcript tiếng Việt của cả bản thu")
    ban_dich_en: str = Field(..., description="Bản dịch tiếng Anh tương ứng")
    cac_doan: list[DoanRa] = Field(
        default_factory=list, description="Từng đoạn sau khi chia (audio ≤ 28 s là 1 đoạn)"
    )
    thoi_luong_audio_s: float
    thoi_gian_nghe_s: float
    thoi_gian_dich_s: float
    thoi_gian_tong_s: float
    rtf: float = Field(..., description="Real-Time Factor = thời gian xử lý / thời lượng audio")
    backend: str = Field(..., description="'that' = model thật, 'gia' = model giả cho test")
    mo_hinh: str = Field("", description="Model + revision + adapter đã sinh ra kết quả này")
    transcript_vi_goc: str = Field(
        "",
        description="Lời ASR nguyên bản, trước khi đổi số đọc "
        "bằng chữ sang chữ số. Dùng để chấm WER giống Task 2",
    )


class SucKhoe(BaseModel):
    trang_thai: str
    backend: str
    model_da_nap: bool
    mo_hinh: str = ""
    can_api_key: bool = False


def kiem_khoa(x_api_key: str | None = Header(None, description="Bắt buộc nếu server đặt API_KEY")):
    if API_KEY and not hmac.compare_digest(x_api_key or "", API_KEY):
        raise HTTPException(401, "Thiếu hoặc sai X-API-Key")


# ---------------- endpoint ----------------
@app.get(
    "/health",
    response_model=SucKhoe,
    tags=["he thong"],
    summary="Kiểm tra service còn sống và model đã nạp chưa",
)
def health() -> SucKhoe:
    return SucKhoe(
        trang_thai="ok" if _he_thong else "chua san sang",
        backend=_he_thong.backend.ten if _he_thong else "-",
        model_da_nap=_he_thong is not None,
        mo_hinh=_he_thong.backend.mo_hinh if _he_thong else "",
        can_api_key=bool(API_KEY),
    )


@app.post(
    "/dich",
    response_model=KetQuaRa,
    tags=["suy luan"],
    summary="Nhận file audio, trả transcript tiếng Việt và bản dịch tiếng Anh",
    responses={
        400: {"description": "File rỗng, sai định dạng, hoặc không đọc được"},
        401: {"description": "Thiếu hoặc sai X-API-Key (khi server đặt API_KEY)"},
        413: {"description": f"File lớn hơn {MAX_MB} MB"},
        503: {"description": "Model chưa nạp xong"},
    },
    dependencies=[Depends(kiem_khoa)],
)
def dich(
    file: UploadFile = File(..., description="Audio tiếng Việt (wav/mp3/flac/m4a/ogg/webm)"),
    dung_vad: bool = Query(
        False,
        description="Chỉ áp dụng cho audio dài hơn max_doan_s. Tắt (mặc định): cửa sổ trượt "
        "chia đều, đã đo WER 16,31% trên 7 bản > 30 s. Bật: cắt tại khoảng lặng (chưa đo)",
    ),
    max_doan_s: float = Query(
        28.0, ge=1.0, le=30.0, description="Độ dài tối đa mỗi đoạn, giây. Phải dưới 30 s"
    ),
) -> KetQuaRa:
    if _he_thong is None:
        raise HTTPException(503, "Model chưa nạp xong, thử lại sau vài giây")

    ten = (file.filename or "").lower()
    duoi = "." + ten.rsplit(".", 1)[-1] if "." in ten else ""
    if duoi not in DUOI_CHO_PHEP:
        raise HTTPException(
            400,
            f"Định dạng {duoi or '(không rõ)'} không được hỗ trợ. "
            f"Dùng một trong: {', '.join(sorted(DUOI_CHO_PHEP))}",
        )

    raw = file.file.read()
    if not raw:
        raise HTTPException(400, "File rỗng")
    if len(raw) > MAX_MB * 1024 * 1024:
        raise HTTPException(413, f"File {len(raw) / 1024 / 1024:.1f} MB, vượt giới hạn {MAX_MB} MB")

    try:
        song, sr = doc_audio_bytes(raw)
    except Exception as e:
        log.warning("khong doc duoc %s: %s: %s", ten, type(e).__name__, e)
        raise HTTPException(
            400, f"Không đọc được audio {duoi}. File hỏng hoặc sai định dạng."
        ) from None

    if song.size == 0:
        raise HTTPException(400, "Audio không có dữ liệu")

    he = HeThong(backend=_he_thong.backend, max_doan_s=max_doan_s, dung_vad=dung_vad)
    with _khoa:
        kq = he.xu_ly(song, sr)
    return KetQuaRa(**kq.dict())


@app.exception_handler(Exception)
async def loi_chung(request, exc: Exception):
    """Khong de traceback lo ra ngoai, nhung van ghi log day du."""
    log.exception("loi khong mong doi khi xu ly %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": f"Lỗi nội bộ: {type(exc).__name__}"})
