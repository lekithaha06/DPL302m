"""B1: Whisper Speech Translation (Vietnamese Audio → English Text).

Sử dụng openai/whisper-small với task="translate" và language="vi".
Khác với B0 (cascade), B1 dịch trực tiếp từ audio không qua transcript VI.
"""
import torch
import torchaudio
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional

class WhisperTranslator:
    """Whisper Speech-to-Text Translation."""

    def __init__(
        self,
        model_name: str = "openai/whisper-small",
        device: Optional[str] = None,
        dtype: str = "float16"
    ):
        """
        Args:
            model_name: HuggingFace model ID
            device: 'cuda' hoặc 'cpu', None để tự động
            dtype: 'float16' hoặc 'float32'
        """
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        print(f"Loading {model_name} on {self.device}...")
        self.processor = WhisperProcessor.from_pretrained(model_name)
        self.model = WhisperForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if dtype == "float16" and self.device == "cuda" else torch.float32
        )
        self.model.to(self.device)
        self.model.eval()

        # Generation config for translation
        self.generation_config = {
            "task": "translate",
            "language": "vi",  # Vietnamese
            "num_beams": 5,
            "max_new_tokens": 256,
            "early_stopping": True,
            "do_sample": False
        }

        print("✅ Model loaded")

    def load_audio(self, audio_path: str, target_sr: int = 16000):
        """Đọc audio và resample về 16kHz mono."""
        waveform, sr = torchaudio.load(audio_path)

        # Stereo → mono
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        # Resample
        if sr != target_sr:
            resampler = torchaudio.transforms.Resample(sr, target_sr)
            waveform = resampler(waveform)

        return waveform.squeeze().numpy()

    def translate(self, audio_path: str) -> Dict[str, Any]:
        """
        Dịch 1 file audio VI → EN.

        Returns:
            {
                "audio_path": str,
                "translation": str,
                "latency_s": float,
                "audio_duration_s": float,
                "rtf": float  # Real-Time Factor
            }
        """
        start_time = time.time()

        # Load audio
        audio = self.load_audio(audio_path)
        audio_duration = len(audio) / 16000.0

        # Process
        inputs = self.processor(
            audio,
            sampling_rate=16000,
            return_tensors="pt"
        )
        inputs = inputs.to(self.device)

        # Generate (với forced language và task)
        with torch.no_grad():
            generated_ids = self.model.generate(
                inputs["input_features"],
                **self.generation_config
            )

        # Decode
        translation = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0]

        latency = time.time() - start_time
        rtf = latency / audio_duration if audio_duration > 0 else 0

        return {
            "audio_path": str(audio_path),
            "translation": translation.strip(),
            "latency_s": round(latency, 3),
            "audio_duration_s": round(audio_duration, 3),
            "rtf": round(rtf, 3)
        }

if __name__ == "__main__":
    # Test với 1 file
    import sys
    if len(sys.argv) < 2:
        print("Usage: python inference.py <audio.wav>")
        sys.exit(1)

    audio_path = sys.argv[1]
    translator = WhisperTranslator()
    result = translator.translate(audio_path)

    print(json.dumps(result, ensure_ascii=False, indent=2))
