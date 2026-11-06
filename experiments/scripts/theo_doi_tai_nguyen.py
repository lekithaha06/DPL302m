#!/usr/bin/env python3
"""Ghi RAM và VRAM mỗi 10 s vào logs/tai_nguyen.csv trong lúc chạy hàng đợi (dừng khi có file logs/DUNG_THEO_DOI).

Cột: thời điểm, RAM hệ thống đã dùng / tổng (MB), tổng RSS các tiến trình python (MB), VRAM đã dùng / tổng (MB, nvidia-smi), % GPU.
"""
import csv
import subprocess
import time
from pathlib import Path

import psutil

T = Path(__file__).resolve().parents[1]
LOG, STOP = T / "logs" / "tai_nguyen.csv", T / "logs" / "DUNG_THEO_DOI"
STOP.unlink(missing_ok=True)
new = not LOG.exists()
with open(LOG, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    if new:
        w.writerow(["time", "ram_used_mb", "ram_total_mb", "python_rss_mb", "vram_used_mb", "vram_total_mb", "gpu_util_pct"])
    while not STOP.exists():
        vm = psutil.virtual_memory()
        rss = sum(p.info["memory_info"].rss for p in psutil.process_iter(["name", "memory_info"])
                  if (p.info["name"] or "").lower().startswith("python") and p.info["memory_info"])
        g = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"],
                           capture_output=True, text=True).stdout.strip().split(", ")
        w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), (vm.total - vm.available) >> 20, vm.total >> 20, rss >> 20, *g]); f.flush()
        time.sleep(10)
