"""Gom audio tu micro theo thoi gian thuc thanh tung doan de nhan dang ngay khi dang thu.

Gradio gui tung mau nho (vai tram ms) khi nguoi dung dang noi. Lop nay giu cac mau
lai va cat mot doan khi nguoi noi NGHI (khoang lang >= lang_s) sau khoang cua_so_s giay.
Noi lien tuc khong nghi thi cat bat buoc o toi_da_s giay, tai cho nho tieng nhat.

Ban truoc 04/11 cat cung moi 10 s: cau dang noi bi cat doi, dau doan sau mat ngu canh.
Khi dung thu, PhienTrucTiep co the nhan dang lai CA ban thu bang dung duong xu ly cua tab
tai tep (chay_lai_khi_dung), nen ket qua cuoi cua micro giong het upload cung file do.

Khong phu thuoc Gradio va model, nen test duoc bang numpy.
"""

from __future__ import annotations

import inspect
import json
import time
import wave
from pathlib import Path

import numpy as np

from .audio import MIN_DOAN_S, SR, _nang_luong_khung, chuan_hoa

DEM_DAU_S = 0.2  # them 0,2 s im lang truoc moi doan: am dau cau khong bi cut ngay khung 0


class GomTrucTiep:
    def __init__(
        self,
        cua_so_s: float = 10.0,
        toi_da_s: float | None = None,
        lang_s: float = 0.3,
        tim_lang_s: float = 2.0,
    ):
        if not 1.0 <= cua_so_s <= 28.0:
            raise ValueError("cua_so_s phai trong khoang 1-28 giay")
        self.cua_so_s = cua_so_s
        self.toi_da_s = min(28.0, max(cua_so_s, toi_da_s or cua_so_s * 2))
        self.lang_s = lang_s
        self.tim_lang_s = min(tim_lang_s, cua_so_s / 2)
        self.sr: int | None = None
        self.dem = np.zeros(0, dtype=np.float32)  # audio chua xu ly, o sr goc
        self.bat_dau_dem_s = 0.0  # moc thoi gian cua mau dau tien trong dem

    def them(self, mau: np.ndarray, sr: int) -> list[tuple[float, float, np.ndarray]]:
        """Them mot mau tu micro. Tra ve cac doan da du (bat_dau_s, ket_thuc_s, song_16k)."""
        mau = chuan_hoa(np.asarray(mau), sr, sr)  # mono float [-1, 1], chua doi sample rate
        ra = []
        if self.sr is not None and sr != self.sr:  # doi micro giua chung: chot phan cu
            ra += self.ket_thuc()
        self.sr = sr
        self.dem = np.concatenate([self.dem, mau])

        while True:
            c = self._tim_cho_nghi()
            if c is None and self.dem.size >= int(self.toi_da_s * sr):
                c = self._cho_nho_nhat(int(self.toi_da_s * sr))
            if c is None:
                break
            ra.append(self._cat(c))
        return ra

    def ket_thuc(self) -> list[tuple[float, float, np.ndarray]]:
        """Goi khi dung thu: tra phan con lai (neu du dai)."""
        ra = []
        if self.sr and self.dem.size >= int(MIN_DOAN_S * self.sr):
            ra.append(self._cat(self.dem.size))
        else:
            self.dem = np.zeros(0, dtype=np.float32)
        return ra

    def _tim_cho_nghi(self) -> int | None:
        """Vi tri giua khoang nghi >= lang_s dau tien nam sau (cua_so_s - tim_lang_s) giay.

        Nghi = nang luong lam tron 200 ms thap hon muc to cua dem (p95) 20 dB. Do tren 7 ban
        FLEURS that: nguong p95-30 dB tren khung 30 ms khong bat duoc lan nghi nao (nhieu nen),
        p95-20 dB tren nang luong lam tron bat duoc cac cho ngung giua cau o 6/7 file."""
        sr = self.sr
        tu = int((self.cua_so_s - self.tim_lang_s) * sr)
        if self.dem.size < tu + int(self.lang_s * sr):
            return None
        khung, buoc = int(0.03 * sr), int(0.01 * sr)
        db = _nang_luong_khung(self.dem, khung, buoc)
        tron = np.convolve(db, np.ones(20) / 20, mode="same")
        nguong = max(-60.0, float(np.percentile(db, 95)) - 20.0)
        lang = tron < nguong
        can = int(self.lang_s / 0.01)
        dem_lang = 0
        for k in range(tu // buoc, lang.size - 10):  # bo 100 ms cuoi: lam tron chua du du lieu
            dem_lang = dem_lang + 1 if lang[k] else 0
            if dem_lang >= can:
                c = (k - dem_lang // 2) * buoc + khung // 2  # cat giua khoang nghi
                return min(c, int(self.toi_da_s * sr))
        return None

    def _cho_nho_nhat(self, n: int) -> int:
        """Noi lien tuc khong nghi: cat o khung 30 ms nho tieng nhat trong tim_lang_s giay truoc n."""
        khung = max(1, int(self.sr * 0.03))
        dau = max(khung, n - int(self.tim_lang_s * self.sr))
        vung = self.dem[dau:n]
        so_khung = vung.size // khung
        if so_khung == 0:
            return n
        nl = (vung[: so_khung * khung].reshape(so_khung, khung) ** 2).mean(axis=1)
        k = int(np.argmin(nl))
        if nl[k] > 0.1 * float(np.median(nl)):  # khong co cho nao nho han ro rang
            return n
        return dau + k * khung + khung // 2

    def _cat(self, c: int) -> tuple[float, float, np.ndarray]:
        doan, self.dem = self.dem[:c], self.dem[c:]
        b = self.bat_dau_dem_s
        e = b + c / self.sr
        self.bat_dau_dem_s = e
        return round(b, 2), round(e, 2), chuan_hoa(doan, self.sr, SR)


class PhienTrucTiep:
    """Mot luot thu am truc tiep: gom mau, nhan dang tung doan ngay khi du, giu bang ket qua.

    xu_ly_doan(song_16k, bat_dau_s, ket_thuc_s, loi_truoc) -> (vi, en) hoac (vi, en, loi_goc),
    hoac None neu doan im lang. App truyen ham goi model (tu_nap) hoac goi API (api).
    chay_lai(song_16k) -> list[[moc, vi, en]]: neu co, khi dung thu se nhan dang lai ca ban
    thu bang duong xu ly cua tab tai tep va thay bang tam bang ket qua do.
    luu_vao: thu muc luu WAV tho, WAV 16 kHz, tung doan va ket_qua.json (de truy loi F01/F03).
    """

    def __init__(
        self, xu_ly_doan, cua_so_s: float = 10.0, chay_lai=None, luu_vao: str | Path | None = None
    ):
        self.xu_ly_doan = xu_ly_doan
        # ham xu_ly_doan cu chi nhan 3 tham so (song, b, e); ham moi nhan them loi_truoc
        self._nhan_loi_truoc = len(inspect.signature(xu_ly_doan).parameters) >= 4
        self.chay_lai = chay_lai
        self.luu_vao = Path(luu_vao) if luu_vao else None
        self.gom = GomTrucTiep(cua_so_s=cua_so_s)
        self.bang: list[list[str]] = []  # [moc thoi gian, vi, en]
        self.bang_tam: list[list[str]] = []  # ban hien trong luc thu (truoc khi chay lai)
        self.loi: str = ""
        self.da_chay_lai = False
        self._loi_truoc = ""
        self._tho: list[np.ndarray] = []  # mau goc tu trinh duyet
        self._sr_tho: int | None = None
        self._doan_16k: list[tuple[float, float, np.ndarray]] = []

    def _chay(self, cac_doan) -> bool:
        co_moi = False
        for b, e, song in cac_doan:
            self._doan_16k.append((b, e, song))
            vao = np.concatenate([np.zeros(int(DEM_DAU_S * SR), np.float32), song])
            try:
                if self._nhan_loi_truoc:
                    kq = self.xu_ly_doan(vao, b, e, self._loi_truoc)
                else:
                    kq = self.xu_ly_doan(vao, b, e)
            except Exception as ex:  # loi 1 doan khong lam dung ca luot thu
                self.loi = f"Lỗi ở đoạn {b:.0f}-{e:.0f} s: {type(ex).__name__}: {ex}"
                continue
            if kq is None:
                continue
            vi, en = kq[0], kq[1]
            self._loi_truoc = kq[2] if len(kq) > 2 else vi
            if not vi.strip():
                continue
            self.bang.append([_mmss(b) + "-" + _mmss(e), vi, en])
            co_moi = True
        return co_moi

    def them(self, mau, sr: int) -> bool:
        x = np.asarray(mau)
        if self._sr_tho in (None, sr):
            self._tho.append(x.copy())
            self._sr_tho = sr
        return self._chay(self.gom.them(x, sr))

    def ket_thuc(self) -> bool:
        co_moi = self._chay(self.gom.ket_thuc())
        self.bang_tam = [r[:] for r in self.bang]
        if self.chay_lai is not None and self._doan_16k:
            ca_ban = np.concatenate([s for _, _, s in self._doan_16k])
            try:
                self.bang = self.chay_lai(ca_ban)
                self.da_chay_lai = True
                co_moi = True
            except Exception as ex:
                self.loi = f"Không nhận dạng lại được cả bản: {type(ex).__name__}: {ex}"
        if self.luu_vao is not None:
            try:
                self._luu()
            except OSError as ex:
                self.loi = f"Không lưu được bản thu: {ex}"
        return co_moi

    def _luu(self):
        d = self.luu_vao / time.strftime("mic_%Y%m%d_%H%M%S")
        d.mkdir(parents=True, exist_ok=True)
        if self._tho:
            tho = chuan_hoa(np.concatenate(self._tho), self._sr_tho, self._sr_tho)
            _ghi_wav(d / f"tho_{self._sr_tho}hz.wav", tho, self._sr_tho)
        if self._doan_16k:
            _ghi_wav(d / "ca_ban_16k.wav", np.concatenate([s for _, _, s in self._doan_16k]), SR)
        for k, (b, e, s) in enumerate(self._doan_16k):
            _ghi_wav(d / f"doan_{k:02d}_{b:06.2f}-{e:06.2f}.wav", s, SR)
        (d / "ket_qua.json").write_text(
            json.dumps(
                {
                    "sr_tho": self._sr_tho,
                    "doan": [[b, e] for b, e, _ in self._doan_16k],
                    "bang_trong_luc_thu": self.bang_tam,
                    "bang_cuoi": self.bang,
                    "da_chay_lai": self.da_chay_lai,
                    "loi": self.loi,
                },
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )
        self.thu_muc_luu = d

    @property
    def transcript_vi(self) -> str:
        return " ".join(r[1] for r in self.bang if r[1])

    @property
    def ban_dich_en(self) -> str:
        return " ".join(r[2] for r in self.bang if r[2])

    @property
    def da_thu_s(self) -> float:
        g = self.gom
        return g.bat_dau_dem_s + (g.dem.size / g.sr if g.sr else 0.0)


def _ghi_wav(p: Path, x: np.ndarray, sr: int):
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(sr))
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


def _mmss(t: float) -> str:
    return f"{int(t // 60):02d}:{int(t % 60):02d}"
