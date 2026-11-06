#!/usr/bin/env python3
"""Thực thi notebook theo thứ tự, LƯU OUTPUT vào chính file sau mỗi notebook (kernel task3-dpl302m, không giới hạn thời gian).
Dừng ở notebook đầu tiên có lỗi. Dùng: env/.venv/Scripts/python.exe scripts/chay_notebook.py notebooks/03_*.ipynb notebooks/04_*.ipynb ..."""
import asyncio
import sys
import time
from pathlib import Path

import nbformat
from nbclient import NotebookClient

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
for f in map(Path, sys.argv[1:]):
    t0 = time.time(); print(time.strftime("%H:%M:%S"), "BẮT ĐẦU", f.name, flush=True)
    n = nbformat.read(f, as_version=4)
    try:
        NotebookClient(n, timeout=None, kernel_name="task3-dpl302m", resources={"metadata": {"path": str(f.parent)}}).execute()
        ok = True
    except Exception as e:  # vẫn lưu output tới ô lỗi
        ok = False; print("LỖI:", type(e).__name__, str(e)[-1500:], flush=True)
    for c in n.cells:
        if c.cell_type == "code":
            c.outputs = [o for o in c.outputs if not (o.get("output_type") == "stream" and o.get("name") == "stderr")]
    nbformat.write(n, f)
    print(time.strftime("%H:%M:%S"), "XONG" if ok else "DỪNG VÌ LỖI", f.name, f"({(time.time() - t0) / 60:.1f} phút)", flush=True)
    if not ok:
        sys.exit(1)
print("TAT_CA_XONG", flush=True)
