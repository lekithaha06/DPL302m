"""Tien xu ly audio: chuan hoa sample rate va chia doan bang VAD.

Yeu cau 5.1.2: "Xu ly duoc am thanh dai (chia doan bang VAD hoac cua so truot),
co tu dong chuan hoa tan so lay mau."

Ly do phai chia doan (do duoc o Task 2): nhom 7 ban thu FLEURS test dai hon 30 s
co WER 94,70% voi I = 401 tren N = 472, tuc PhoWhisper giai ma sai phan sau 30 s
va sinh chu lap. Nghe kiem xac nhan nguoi doc noi den gan het file, nen day khong
phai ao giac tren doan im lang ma la gioi han cach xu ly audio dai.
Nguon: reports/asr/long_form_audit.csv, nghe_kiem/danh_sach_nghe_kiem.csv
"""

from __future__ import annotations

import io
import shutil
import subprocess
from dataclasses import dataclass

import numpy as np

SR = 16000  # PhoWhisper va Whisper deu dung 16 kHz
MAX_DOAN_S = 28.0  # chua 30 s, de lai bien an toan
MIN_DOAN_S = 0.3  # ngan hon thi khong con la loi noi (nguong B3 cua pipeline du lieu)


@dataclass
class Doan:
    """Mot doan audio sau khi chia."""

    bat_dau_s: float
    ket_thuc_s: float
    song: np.ndarray

    @property
    def thoi_luong_s(self) -> float:
        return self.ket_thuc_s - self.bat_dau_s

    def moc_thoi_gian(self) -> str:
        """Tra ve dang mm:ss-mm:ss de hien tren giao dien."""

        def mmss(t: float) -> str:
            return f"{int(t // 60):02d}:{int(t % 60):02d}"

        return f"{mmss(self.bat_dau_s)}-{mmss(self.ket_thuc_s)}"


def chuan_hoa(song: np.ndarray, sr_goc: int, sr_dich: int = SR) -> np.ndarray:
    """Doi ve mono float32 va resample ve sr_dich.

    Dung noi suy tuyen tinh de khong phu thuoc scipy/librosa. Voi tac vu ASR thi
    chenh lech so voi resample chat luong cao la khong dang ke, nhung neu co
    scipy thi uu tien dung polyphase cho dung chuan.
    """
    song = np.asarray(song)
    # phai kiem kieu so nguyen TRUOC khi doi sang float32, sau do thi het biet
    la_so_nguyen = np.issubdtype(song.dtype, np.integer)
    if song.ndim > 1:  # stereo -> mono
        song = song.mean(axis=1)
    song = song.astype(np.float32, copy=False)

    # int16 tu micro hoac file wav -> [-1, 1]
    if la_so_nguyen or np.abs(song).max(initial=0.0) > 1.5:
        song = song / 32768.0

    if sr_goc == sr_dich or song.size == 0:
        return song

    try:
        from math import gcd

        from scipy.signal import resample_poly

        g = gcd(int(sr_goc), int(sr_dich))
        return resample_poly(song, sr_dich // g, sr_goc // g).astype(np.float32)
    except ImportError:
        n_moi = int(round(song.size * sr_dich / sr_goc))
        if n_moi <= 0:
            return np.zeros(0, dtype=np.float32)
        x_cu = np.linspace(0.0, 1.0, song.size, endpoint=False)
        x_moi = np.linspace(0.0, 1.0, n_moi, endpoint=False)
        return np.interp(x_moi, x_cu, song).astype(np.float32)


def _nang_luong_khung(song: np.ndarray, khung: int, buoc: int) -> np.ndarray:
    """RMS tung khung, tinh bang dBFS."""
    if song.size < khung:
        song = np.pad(song, (0, khung - song.size))
    n = 1 + (song.size - khung) // buoc
    idx = np.arange(khung)[None, :] + buoc * np.arange(n)[:, None]
    rms = np.sqrt(np.mean(song[idx] ** 2, axis=1) + 1e-12)
    return 20.0 * np.log10(rms + 1e-12)


NGUONG_IM_LANG_DB = -60.0  # khung to nhat duoi muc nay thi coi ca doan la im lang


def la_im_lang(song: np.ndarray, sr: int = SR, nguong_db: float = NGUONG_IM_LANG_DB) -> bool:
    """True neu ca doan khong co khung 30 ms nao to hon nguong_db.

    Xet khung TO NHAT chu khong xet RMS trung binh: giong nho (vd -50 dBFS) van co
    khung vuot -60 dBFS nen khong bi loc oan. Nguong -60 dBFS thap hon 15 dB so voi
    nguong tuyet doi cu (-45) da lam hong 28,9% file FLEURS test.
    Ly do can: Whisper gap doan im lang van sinh chu (ao giac), nen phai chan truoc.
    """
    if song.size == 0:
        return True
    khung = max(1, int(sr * 0.03))
    return float(_nang_luong_khung(song, khung, max(1, khung // 2)).max()) < nguong_db


def tim_vung_noi(
    song: np.ndarray,
    sr: int = SR,
    nguong_db: float | None = None,
    khung_ms: float = 30.0,
    im_lang_toi_thieu_ms: float = 300.0,
) -> list[tuple[float, float]]:
    """VAD theo nang luong: tra ve danh sach (bat_dau_s, ket_thuc_s) cua cac vung co tieng noi.

    Dung nguong nang luong thay vi Silero VAD de khong can tai them model va khong
    can mang luc chay. Neu nhom muon chinh xac hon thi thay ham nay bang Silero,
    phan chia doan ben duoi khong doi.

    nguong_db = None (mac dinh): nguong TUONG DOI = muc to nhat cua file tru 35 dB,
    khong thap hon -60 dBFS. Ban cu dung nguong tuyet doi -45 dBFS va lam hong file
    thu nho tieng: 248/857 (28,9%) ban thu FLEURS test co RMS < -45 dBFS (Kiet do
    ngay 01/11/2026), nen ca cau bi coi la im lang.
    """
    if song.size == 0:
        return []

    khung = max(1, int(sr * khung_ms / 1000))
    buoc = max(1, khung // 2)
    db = _nang_luong_khung(song, khung, buoc)
    if nguong_db is None:
        nguong_db = max(-60.0, float(np.percentile(db, 95)) - 35.0)
    co_tieng = db > nguong_db
    if not co_tieng.any():
        return []

    # gop cac khung lien nhau thanh vung
    doi = np.diff(co_tieng.astype(np.int8))
    bat_dau = list(np.where(doi == 1)[0] + 1)
    ket_thuc = list(np.where(doi == -1)[0] + 1)
    if co_tieng[0]:
        bat_dau.insert(0, 0)
    if co_tieng[-1]:
        ket_thuc.append(len(co_tieng))

    vung = [
        (b * buoc / sr, min(e * buoc + khung, song.size) / sr)
        for b, e in zip(bat_dau, ket_thuc, strict=True)
    ]

    # noi hai vung cach nhau duoi im_lang_toi_thieu_ms: khoang lang ngan la nghi hoi,
    # khong phai het cau
    khe = im_lang_toi_thieu_ms / 1000.0
    gop: list[list[float]] = []
    for b, e in vung:
        if gop and b - gop[-1][1] < khe:
            gop[-1][1] = e
        else:
            gop.append([b, e])
    return [tuple(x) for x in gop]


def chia_doan(
    song: np.ndarray,
    sr: int = SR,
    max_doan_s: float = MAX_DOAN_S,
    dung_vad: bool = False,
    cat_tai_lang: bool = True,
) -> list[Doan]:
    """Chia audio thanh cac doan khong qua max_doan_s giay.

    Audio <= max_doan_s: giu nguyen 1 doan, ke ca khi bat VAD. Day la cach Task 2
    da do (WER 12,18% tren 850 ban thu <= 30 s). Ban cu luon cat theo VAD nen cau
    bi cat vun ("bac si. ma la. ba lat xo.") va WER len 34,79% tren 20 mau.

    Audio dai hon:
      - dung_vad=False (mac dinh): chia thanh cac phan gan bang nhau, moi diem cat doi toi
        cho nho tieng nhat trong +-3 s (xem _cat_deu). Cat dung giua (ban truoc 04/11) da do
        voi model that tren 7 ban thu > 30 s cua FLEURS test: WER 16,31% (dua thang: 94,70%).
      - dung_vad=True: tim khoang lang roi gom cac vung noi lien nhau thanh doan
        dai nhat co the nhung khong qua max_doan_s, nen chi cat o cho nguoi noi nghi.
        Cach nay CHUA do voi model that.
    """
    if song.size == 0:
        return []

    tong_s = song.size / sr

    def lay(b: float, e: float) -> Doan:
        i, j = max(0, int(b * sr)), min(song.size, int(e * sr))
        return Doan(bat_dau_s=b, ket_thuc_s=e, song=song[i:j])

    if tong_s <= max_doan_s:
        return [lay(0.0, tong_s)]

    if not dung_vad:  # cat_tai_lang=False: cat dung giua nhu ban truoc 04/11 (de so sanh)
        return _cat_deu(0.0, tong_s, max_doan_s, lay, song if cat_tai_lang else None, sr)

    vung = tim_vung_noi(song, sr)
    if not vung:  # toan im lang -> khong co gi de nhan dang
        return []

    ra: list[Doan] = []
    dau = cuoi = None
    for b, e in vung:
        if e - b > max_doan_s:  # mot vung noi qua dai -> chot doan dang gom, cat deu vung nay
            if dau is not None:
                ra.append(lay(dau, cuoi))
                dau = None
            ra += _cat_deu(b, e, max_doan_s, lay, song, sr)
        elif dau is None:
            dau, cuoi = b, e
        elif e - dau <= max_doan_s:  # gom tiep vao doan hien tai
            cuoi = e
        else:
            ra.append(lay(dau, cuoi))
            dau, cuoi = b, e
    if dau is not None:
        ra.append(lay(dau, cuoi))
    return [d for d in ra if d.thoi_luong_s >= MIN_DOAN_S]


def _cat_deu(b: float, e: float, max_doan_s: float, lay, song=None, sr: int = SR) -> list[Doan]:
    """Cat [b, e] thanh cac phan gan bang nhau, moi phan <= max_doan_s.

    Co song: moi diem cat duoc doi toi cho nho tieng nhat trong +-LECH_CAT_S giay quanh diem
    cat deu. Ban cu cat dung diem giua: file FLEURS 30,48 s bi cat o 15,24 s dung luc dang
    noi (-22,6 dB), hai doan cung doan chu "co the" nen ra "hoc sinh co the. co the xac dinh",
    trong khi 13,70-14,65 s la khoang lang that.
    """
    ra, dau = [], b
    while e - dau > max_doan_s:
        so_phan = int(np.ceil((e - dau) / max_doan_s))
        dich = dau + (e - dau) / so_phan
        cat = (
            dich if song is None else _diem_lang(song, sr, dich, dau + MIN_DOAN_S, dau + max_doan_s)
        )
        ra.append(lay(dau, cat))
        dau = cat
    if e - dau >= MIN_DOAN_S:
        ra.append(lay(dau, e))
    return ra


LECH_CAT_S = 3.0  # diem cat duoc lech toi da bao nhieu giay so voi diem cat deu


def _diem_lang(song: np.ndarray, sr: int, dich_s: float, tu_s: float, den_s: float) -> float:
    """Moc (giay) nho tieng nhat trong [dich_s - LECH_CAT_S, dich_s + LECH_CAT_S] giao [tu_s, den_s].

    Nang luong lam tron tren 200 ms de chon khoang lang that, khong chon mot khung lang le
    giua hai am tiet. Nhieu cho nho nhu nhau thi lay cho gan diem cat deu nhat.
    """
    a = max(tu_s, dich_s - LECH_CAT_S)
    z = min(den_s, dich_s + LECH_CAT_S)
    i, j = int(a * sr), int(z * sr)
    khung, buoc = int(0.03 * sr), int(0.01 * sr)
    if j - i < khung * 2:
        return dich_s
    db = _nang_luong_khung(song[i:j], khung, buoc)
    k = max(1, int(0.2 / 0.01))
    tron = np.convolve(db, np.ones(k) / k, mode="same")
    t = a + (np.arange(tron.size) * buoc + khung / 2) / sr
    nho = tron.min()
    gan = np.where(tron <= nho + 1.0)[0]  # cac cho nho tieng gan bang nhau (lech < 1 dB)
    return float(t[gan[np.argmin(np.abs(t[gan] - dich_s))]])


def doc_audio_bytes(raw: bytes) -> tuple[np.ndarray, int]:
    """Doc bytes audio thanh (song, sr).

    wav/flac/ogg/mp3: doc bang soundfile. m4a/webm (file ghi am dien thoai, trinh
    duyet): soundfile khong doc duoc, nen chuyen qua ffmpeg ra 16 kHz mono.
    """
    try:
        import soundfile as sf

        song, sr = sf.read(io.BytesIO(raw), dtype="float32", always_2d=False)
        return np.asarray(song), int(sr)
    except ImportError:
        pass
    except Exception:  # soundfile khong doc duoc dinh dang nay -> thu ffmpeg
        if shutil.which("ffmpeg") is None:
            raise
    if shutil.which("ffmpeg") is None:
        raise ValueError("cần soundfile hoặc ffmpeg để đọc audio")

    kq = subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-i",
            "pipe:0",
            "-f",
            "f32le",
            "-ac",
            "1",
            "-ar",
            str(SR),
            "pipe:1",
        ],
        input=raw,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if kq.returncode != 0 or not kq.stdout:
        raise ValueError("ffmpeg không đọc được file")
    return np.frombuffer(kq.stdout, dtype="<f4").copy(), SR


def doc_tep(duong_dan, max_mb: float = 50) -> tuple[np.ndarray, int]:
    """Doc tep upload tu giao dien. Loi nao cung nem ValueError voi cau tieng Viet de hien ra
    (rong, qua lon, hong, khong phai audio), khong de traceback hay "AppError" chung chung."""
    from pathlib import Path

    if not duong_dan:
        raise ValueError("Chưa có audio. Hãy tải tệp lên.")
    p = Path(duong_dan)
    if not p.is_file():
        raise ValueError("Không tìm thấy tệp vừa tải lên, hãy tải lại.")
    n = p.stat().st_size
    if n == 0:
        raise ValueError("Tệp rỗng (0 byte).")
    if n > max_mb * 1024 * 1024:
        raise ValueError(f"Tệp {n / 1024 / 1024:.1f} MB, vượt giới hạn {max_mb:g} MB.")
    try:
        song, sr = doc_audio_bytes(p.read_bytes())
    except Exception:
        raise ValueError(
            f"Không đọc được tệp {p.suffix}: tệp hỏng hoặc không phải audio "
            "(wav, mp3, flac, m4a, ogg, webm)."
        ) from None
    if np.asarray(song).size == 0:
        raise ValueError("Tệp không có dữ liệu âm thanh.")
    return song, sr


def ghep_loi(cac_loi: list[str]) -> str:
    """Ghep loi cua cac doan thanh mot chuoi.

    Them dau cach giua cac doan va bo khoang trang lap. Khong tu them dau cau:
    khoi nghe da sinh dau cau khi co, va tu them thi se lam sai WER.
    """
    phan = [t.strip() for t in cac_loi if t and t.strip()]
    return " ".join(phan)


def _tu(w: str) -> str:
    return "".join(c for c in w.lower() if c.isalnum())


def bo_lap_cho_noi(truoc: str, sau: str, toi_da: int = 5) -> str:
    """Bo cum tu o dau `sau` neu no lap y het cum tu o cuoi `truoc` (tu 2 den toi_da tu).

    Khi diem cat roi vao giua mot tu, ca hai doan deu doan tu do: "hoc sinh co the." +
    "co the xac dinh ..." -> bo "co the" o doan sau. Chi bo cum >= 2 tu de khong xoa nham
    lap co nghia 1 tu ("rat. rat"); khong so dau cau va hoa thuong.
    """
    a = [_tu(w) for w in truoc.split()]
    w_sau = sau.split()
    b = [_tu(w) for w in w_sau]
    for k in range(min(toi_da, len(a), len(b)), 1, -1):
        if a[-k:] == b[:k] and all(a[-k:]):
            return " ".join(w_sau[k:])
    return sau
