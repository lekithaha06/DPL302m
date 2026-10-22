"""Reproducibility helpers: fixed seeds and environment report."""
from __future__ import annotations

import json
import os
import platform
import random
import sys


def set_seed(seed: int = 42, deterministic: bool = True) -> None:
    """Fix every RNG we use so runs are repeatable."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        if deterministic:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


def environment_report() -> dict:
    """Collect python/OS/GPU/library versions to paste into the README or report."""
    info: dict = {"python": sys.version.split()[0], "platform": platform.platform()}
    for name in ("torch", "transformers", "sacrebleu", "jiwer", "librosa", "soundfile", "huggingface_hub"):
        try:
            module = __import__(name)
            info[name] = getattr(module, "__version__", "unknown")
        except ImportError:
            info[name] = None
    try:
        import torch

        info["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            info["gpu"] = torch.cuda.get_device_name(0)
            info["cuda"] = torch.version.cuda
            info["vram_gb"] = round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1)
    except ImportError:
        pass
    return info


if __name__ == "__main__":
    set_seed(42)
    print(json.dumps(environment_report(), indent=2, ensure_ascii=False))
