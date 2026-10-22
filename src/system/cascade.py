"""Task 2 · hệ thống đầu cuối (phần Đăng): âm thanh → (VAD) → PhoWhisper-small → VinAI Translate (+ LoRA) → tiếng Anh.

Âm thanh được đọc, trộn về mono và đổi về 16 kHz. Với âm thanh dài, Silero VAD cắt đoạn có tiếng nói,
gộp các đoạn liền nhau thành khối tối đa --max-seg giây, rồi nghe và dịch từng khối kèm mốc thời gian.
"""
import time
import numpy as np, soundfile as sf, librosa, torch
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

SR = 16000


def load_audio(path):
    a, sr = sf.read(path, dtype="float32", always_2d=True)
    a = a.mean(1)
    return librosa.resample(a, orig_sr=sr, target_sr=SR) if sr != SR else a


class Cascade:
    def __init__(self, asr_dir, mt_dir, adapter="", device="cuda"):
        self.dev = device
        self.asr = pipeline("automatic-speech-recognition", model=asr_dir, device=0, torch_dtype=torch.float16)
        self.tok = AutoTokenizer.from_pretrained(mt_dir, src_lang="vi_VN")
        mt = AutoModelForSeq2SeqLM.from_pretrained(mt_dir, torch_dtype=torch.float16)
        if adapter:
            from peft import PeftModel
            mt = PeftModel.from_pretrained(mt, adapter).merge_and_unload()
        self.mt = mt.to(device).eval()
        self.en_id = self.tok.convert_tokens_to_ids("en_XX")
        self.vad = None

    def transcribe(self, audio):
        return self.asr({"raw": audio, "sampling_rate": SR}, generate_kwargs={"language": "vi", "task": "transcribe"},
                        chunk_length_s=30)["text"].strip()

    @torch.no_grad()
    def translate(self, texts):
        enc = self.tok(texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(self.dev)
        cap = min(512, 2 * enc.input_ids.shape[1] + 10)  # same output cap as src/mt/eval_mt.py
        out = self.mt.generate(**enc, decoder_start_token_id=self.en_id, num_beams=5, early_stopping=True, max_length=cap)
        return self.tok.batch_decode(out, skip_special_tokens=True)

    def segments(self, audio, max_seg=25.0):
        if self.vad is None:
            from silero_vad import load_silero_vad
            self.vad = load_silero_vad()
        from silero_vad import get_speech_timestamps
        ts = get_speech_timestamps(torch.from_numpy(audio), self.vad, sampling_rate=SR)
        segs, cur = [], None
        for t in ts:
            if cur and (t["end"] - cur[0]) / SR <= max_seg:
                cur[1] = t["end"]
            else:
                if cur: segs.append(cur)
                cur = [t["start"], t["end"]]
        if cur: segs.append(cur)
        return segs

    def run(self, audio, use_vad=True, max_seg=25.0):
        """Trả về danh sách đoạn {start, end, vi, en} và thời gian từng khối."""
        t = {"vad": 0.0, "asr": 0.0, "mt": 0.0}
        if use_vad:
            t0 = time.perf_counter(); segs = self.segments(audio, max_seg); t["vad"] = time.perf_counter() - t0
        else:
            segs = [[0, len(audio)]]
        out = []
        for s, e in segs:
            torch.cuda.synchronize(); t0 = time.perf_counter()
            vi = self.transcribe(audio[s:e])
            torch.cuda.synchronize(); t["asr"] += time.perf_counter() - t0
            out.append({"start": round(s / SR, 2), "end": round(e / SR, 2), "vi": vi})
        torch.cuda.synchronize(); t0 = time.perf_counter()
        ens = self.translate([o["vi"] for o in out]) if out else []
        torch.cuda.synchronize(); t["mt"] = time.perf_counter() - t0
        for o, en in zip(out, ens):
            o["en"] = en
        return out, t
