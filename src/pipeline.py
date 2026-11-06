"""Pipeline cascade: audio tieng Viet -> transcript tieng Viet -> ban dich tieng Anh.

Kien truc (bao cao chuong 4):
    audio -> chuan hoa 16 kHz -> chia doan <= 28 s (cat tai cho lang) -> PhoWhisper-small
          -> loi ASR -> bo lap o cho noi -> doi so doc bang chu sang chu so
          -> VinAI Translate + adapter LoRA V2 -> cau tieng Anh
LoRA chi gan vao khoi DICH. Khoi nghe la PhoWhisper-small pretrained, khong fine-tune.

Hai backend:
  - ThatBackend: nap model that bang transformers + peft. Can GPU de chay nhanh.
  - GiaBackend:  model gia, khong nap trong so. Dung cho unit test va CI, noi khong
                 co GPU va khong tai duoc 2,69 GB trong so.

Chon backend bang bien moi truong ASR_BACKEND=that|gia (mac dinh: that).
Neu chon "that" ma nap loi thi BAO LOI LUON, khong tu chuyen sang gia: ban cu tu
chuyen nen khi thieu protobuf, API van chay nhung tra chu gia ma nguoi dung khong biet.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from .audio import SR, Doan, bo_lap_cho_noi, chia_doan, chuan_hoa, ghep_loi, la_im_lang
from .so import doi_so

log = logging.getLogger(__name__)

# Revision co dinh - khop protocol bao_asr_v1_20261027 va bao cao Task 2
ASR_REPO = "vinai/PhoWhisper-small"
ASR_REV = "a86b604c346caf7148c37512eafe783a16420adb"
MT_REPO = "vinai/vinai-translate-vi2en-v2"
MT_REV = "ae7baa85da07dbe8e23ac26a9f5ef560c17e2138"
SUPPRESS = Path(__file__).resolve().parent.parent / "configs" / "common_suppression_from_task1.json"


@dataclass
class KetQuaDoan:
    """Ket qua cua mot doan audio."""

    moc_thoi_gian: str
    bat_dau_s: float
    ket_thuc_s: float
    transcript_vi: str
    ban_dich_en: str
    transcript_vi_goc: str = ""  # loi ASR nguyen ban, chua doi so (de cham WER kieu Task 2)


@dataclass
class KetQua:
    """Ket qua cua ca ban thu."""

    transcript_vi: str
    ban_dich_en: str
    cac_doan: list[KetQuaDoan] = field(default_factory=list)
    thoi_luong_audio_s: float = 0.0
    thoi_gian_nghe_s: float = 0.0
    thoi_gian_dich_s: float = 0.0
    backend: str = ""
    mo_hinh: str = ""  # model + revision + adapter da dung, de biet ket qua do ban nao sinh ra
    transcript_vi_goc: str = ""  # loi ASR nguyen ban, chua doi so

    @property
    def thoi_gian_tong_s(self) -> float:
        return self.thoi_gian_nghe_s + self.thoi_gian_dich_s

    @property
    def rtf(self) -> float:
        """Real-Time Factor: thoi gian xu ly chia thoi luong audio."""
        if self.thoi_luong_audio_s <= 0:
            return 0.0
        return self.thoi_gian_tong_s / self.thoi_luong_audio_s

    def dict(self) -> dict:
        d = asdict(self)
        d["rtf"] = round(self.rtf, 4)
        d["thoi_gian_tong_s"] = round(self.thoi_gian_tong_s, 4)
        return d


class GiaBackend:
    """Model gia cho test va CI. Khong nap trong so, khong can GPU.

    Tra ve chuoi xac dinh theo do dai audio nen test lap lai duoc. KHONG dung de
    bao cao bat ky con so chat luong nao.
    """

    ten = "gia"
    mo_hinh = "gia (khong co model)"

    def nghe(self, doan: Doan) -> str:
        return f"[gia] loi asr doan {doan.moc_thoi_gian()} dai {doan.thoi_luong_s:.1f} giay"

    def dich(self, van_ban: str) -> str:
        return f"[mock] english translation of {len(van_ban.split())} vietnamese tokens"


class ThatBackend:
    """Nap PhoWhisper-small va VinAI Translate + adapter LoRA.

    Trong so nap mot lan luc khoi tao va giu trong bo nho: rieng trong so da 2,69 GB,
    nap lai moi luot goi thi thoi gian nap lon hon nhieu lan thoi gian xu ly that
    (p50 do duoc la 1,52 s).
    """

    ten = "that"

    def __init__(self, adapter: str | None = None, thiet_bi: str | None = None):
        import torch
        from transformers import (
            AutoModelForSeq2SeqLM,
            AutoTokenizer,
            WhisperForConditionalGeneration,
            WhisperProcessor,
        )

        self.torch = torch
        ten_ad = "khong (B0)"
        if adapter:
            p = Path(adapter)
            ten_ad = f"{p.parent.name}/{p.name}" if p.name == "best" else str(p)
        self.mo_hinh = f"{ASR_REPO}@{ASR_REV[:8]} + {MT_REPO}@{MT_REV[:8]} + LoRA {ten_ad}"
        self.thiet_bi = thiet_bi or ("cuda" if torch.cuda.is_available() else "cpu")
        self.dtype = torch.float16 if self.thiet_bi == "cuda" else torch.float32

        log.info("nap khoi nghe %s @%s", ASR_REPO, ASR_REV[:8])
        self.asr_proc = WhisperProcessor.from_pretrained(ASR_REPO, revision=ASR_REV)
        self.asr = (
            WhisperForConditionalGeneration.from_pretrained(
                ASR_REPO, revision=ASR_REV, torch_dtype=self.dtype
            )
            .to(self.thiet_bi)
            .eval()
        )
        # danh sach suppress tokens giong het luc do Task 2 (run_asr.py cua Kiet)
        if SUPPRESS.exists():
            sup = json.loads(SUPPRESS.read_text(encoding="utf-8"))
            self.asr.generation_config.suppress_tokens = sup["suppress_tokens"]
            self.asr.generation_config.begin_suppress_tokens = sup["begin_suppress_tokens"]

        log.info("nap khoi dich %s @%s", MT_REPO, MT_REV[:8])
        self.mt_tok = AutoTokenizer.from_pretrained(MT_REPO, revision=MT_REV, src_lang="vi_VN")
        # nap fp32, gop adapter o fp32 roi moi doi sang fp16, giong translate.py cua Task 2.
        # Ban cu gop o fp16: Kiet do BLEU 27,86 so voi 28,17 cua Task 2 (850 ban <= 30 s).
        mt = AutoModelForSeq2SeqLM.from_pretrained(
            MT_REPO, revision=MT_REV, torch_dtype=torch.float32
        )
        if adapter:
            from peft import PeftModel

            log.info("gan adapter LoRA %s", adapter)
            mt = PeftModel.from_pretrained(mt, adapter)
            mt = mt.merge_and_unload()
        self.mt = mt.to(self.dtype).to(self.thiet_bi).eval()

    @property
    def _vram_dinh_gib(self) -> float:
        if self.thiet_bi != "cuda":
            return 0.0
        return self.torch.cuda.max_memory_allocated() / 2**30

    def nghe(self, doan: Doan) -> str:
        """Nhan dang mot doan. Doan luon <= 28 s nen dung nhanh short-form."""
        feats = self.asr_proc(doan.song, sampling_rate=SR, return_tensors="pt").input_features
        feats = feats.to(self.thiet_bi, dtype=self.dtype)
        with self.torch.inference_mode():
            ids = self.asr.generate(
                feats,
                language="vi",
                task="transcribe",
                num_beams=5,
                do_sample=False,
                max_new_tokens=440,
                return_timestamps=False,
            )
        return self.asr_proc.batch_decode(ids, skip_special_tokens=True)[0].strip()

    def dich(self, van_ban: str) -> str:
        if not van_ban.strip():
            return ""
        batch = self.mt_tok(van_ban, return_tensors="pt", truncation=True, max_length=512).to(
            self.thiet_bi
        )
        with self.torch.inference_mode():
            ids = self.mt.generate(
                **batch,
                num_beams=5,
                do_sample=False,
                max_new_tokens=256,
                early_stopping=True,
                decoder_start_token_id=self.mt_tok.lang_code_to_id["en_XX"],
            )
        return self.mt_tok.batch_decode(ids, skip_special_tokens=True)[0].strip()


GOC = Path(__file__).resolve().parent.parent
# Ban chot V2 theo quy tac DEV chot truoc ablation (configs/ban_chot.json):
# V1-V4 hoa tren dev cascade (cach V3 26,71 <= 0,5) -> chon dev sach cao nhat = V2 (36,93).
# Ablation rank 8/32, augmentation deu thap hon tren dev. Khong dung diem test de chon.
ADAPTER_MAC_DINH = GOC / "checkpoints" / "V2" / "best"


def chon_adapter(adapter: str | None = None) -> str | None:
    """Adapter LoRA se dung. Thu tu: tham so -> ADAPTER_PATH -> checkpoints/V2/best (ban chot).
    ADAPTER_PATH=none thi khong gan adapter (chay baseline B0)."""
    if adapter is None:
        adapter = os.environ.get("ADAPTER_PATH") or None
    if adapter is None:
        if ADAPTER_MAC_DINH.exists():
            return str(ADAPTER_MAC_DINH)
        log.warning("khong thay %s, chay KHONG co adapter (B0)", ADAPTER_MAC_DINH)
        return None
    if adapter.lower() in ("none", "b0", "khong"):
        return None
    p = Path(adapter)
    if not p.is_absolute() and not p.exists() and (GOC / p).exists():
        p = GOC / p  # cho phep chay tu thu muc khac voi goc repo
    return str(p)


def tao_backend(adapter: str | None = None):
    """Chon backend theo bien moi truong ASR_BACKEND (that | gia)."""
    muon = os.environ.get("ASR_BACKEND", "that").lower()
    if muon == "gia":
        log.warning("ASR_BACKEND=gia: dung model GIA, ket qua khong co nghia")
        return GiaBackend()
    adapter = chon_adapter(adapter)
    log.info("adapter LoRA: %s", adapter or "khong (B0)")
    if adapter and not (Path(adapter) / "adapter_model.safetensors").exists():
        raise FileNotFoundError(f"khong thay adapter {adapter}")
    try:
        return ThatBackend(adapter=adapter)
    except Exception as e:
        raise RuntimeError(
            f"Khong nap duoc model that ({type(e).__name__}: {e}). "
            "Kiem tra: da cai du requirements.txt chua (nhat la protobuf, sentencepiece), "
            "co mang de tai trong so lan dau khong. Muon chay thu khong can model thi "
            "dat ASR_BACKEND=gia."
        ) from e


def _bat(ten: str, mac_dinh: str = "1") -> bool:
    return os.environ.get(ten, mac_dinh).lower() not in ("0", "false", "khong", "no")


class HeThong:
    """Lop goi ngoai cung: nhan audio, tra transcript va ban dich kem moc thoi gian.

    doi_so=True (mac dinh, tat bang CHUAN_HOA_SO=0): doi so doc bang chu cua ASR sang chu so
    ("muoi mot thang ba" -> "11 thang 3") truoc khi dich. Xem src/so.py.
    """

    def __init__(
        self,
        backend=None,
        adapter: str | None = None,
        max_doan_s: float = 28.0,
        dung_vad: bool = False,
        doi_so: bool | None = None,
        cat_tai_lang: bool = True,
        bo_lap: bool = True,
    ):
        self.backend = backend or tao_backend(adapter)
        self.max_doan_s = max_doan_s
        self.dung_vad = dung_vad
        self.doi_so = _bat("CHUAN_HOA_SO") if doi_so is None else doi_so
        self.cat_tai_lang = (
            cat_tai_lang  # False + bo_lap=False + doi_so=False = cach xu ly truoc 04/11
        )
        self.bo_lap = bo_lap

    def _hau_xu_ly(self, vi: str) -> str:
        return doi_so(vi) if self.doi_so else vi

    def xu_ly_doan(
        self, song_16k: np.ndarray, bat_dau_s: float, ket_thuc_s: float, loi_truoc: str = ""
    ):
        """Nhan dang + dich mot doan da chia san (dung cho micro truc tiep).
        loi_truoc: loi ASR cua doan ngay truoc, de bo cum tu bi lap o cho noi.
        Tra (transcript_vi, ban_dich_en, loi_asr_goc), hoac None neu doan im lang."""
        if la_im_lang(song_16k):
            return None
        d = Doan(bat_dau_s=bat_dau_s, ket_thuc_s=ket_thuc_s, song=song_16k)
        goc = self.backend.nghe(d)
        if loi_truoc and self.bo_lap:
            goc = bo_lap_cho_noi(loi_truoc, goc)
        vi = self._hau_xu_ly(goc)
        return vi, self.backend.dich(vi) if vi.strip() else "", goc

    def xu_ly(self, song: np.ndarray, sr: int) -> KetQua:
        song = chuan_hoa(song, sr)
        thoi_luong = song.size / SR

        doan = chia_doan(
            song,
            SR,
            max_doan_s=self.max_doan_s,
            dung_vad=self.dung_vad,
            cat_tai_lang=self.cat_tai_lang,
        )
        # bo doan im lang TRUOC khi goi model: Whisper gap im lang van bia ra chu
        doan = [d for d in doan if not la_im_lang(d.song)]
        if not doan:
            return KetQua(
                transcript_vi="",
                ban_dich_en="",
                thoi_luong_audio_s=thoi_luong,
                backend=self.backend.ten,
                mo_hinh=self.backend.mo_hinh,
            )

        t0 = time.perf_counter()
        goc = [self.backend.nghe(d) for d in doan]
        # diem cat roi giua tu thi 2 doan cung doan tu do -> bo cum lap o dau doan sau
        for k in range(1, len(goc) if self.bo_lap else 1):
            goc[k] = bo_lap_cho_noi(goc[k - 1], goc[k])
        loi = [self._hau_xu_ly(t) for t in goc]
        t_nghe = time.perf_counter() - t0

        t0 = time.perf_counter()
        dich = [self.backend.dich(t) if t.strip() else "" for t in loi]
        t_dich = time.perf_counter() - t0

        return KetQua(
            transcript_vi=ghep_loi(loi),
            ban_dich_en=ghep_loi(dich),
            transcript_vi_goc=ghep_loi(goc),
            cac_doan=[
                KetQuaDoan(
                    moc_thoi_gian=d.moc_thoi_gian(),
                    bat_dau_s=round(d.bat_dau_s, 2),
                    ket_thuc_s=round(d.ket_thuc_s, 2),
                    transcript_vi=t,
                    ban_dich_en=b,
                    transcript_vi_goc=g,
                )
                for d, t, b, g in zip(doan, loi, dich, goc, strict=True)
            ],
            thoi_luong_audio_s=round(thoi_luong, 2),
            thoi_gian_nghe_s=round(t_nghe, 3),
            thoi_gian_dich_s=round(t_dich, 3),
            backend=self.backend.ten,
            mo_hinh=self.backend.mo_hinh,
        )
