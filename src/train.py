"""Huấn luyện LoRA cho khối dịch. Code thật ở experiments/scripts/mt/train_lora.py, lệnh đầy đủ ở experiments/chay_lai.sh."""

import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "experiments/scripts/mt/train_lora.py"),
        run_name="__main__",
    )
