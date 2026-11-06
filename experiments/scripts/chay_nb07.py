#!/usr/bin/env python3
"""Chạy thật notebooks/07_chay_san_pham_tren_gpu.ipynb, lưu output sau mỗi ô. Thêm ô kiểm chắc chắn dùng adapter V2."""
import asyncio
import sys
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

T = Path(__file__).resolve().parents[1]; R = T.parent / "repo_cuoi"; RA = T / "notebooks/07_chay_san_pham_tren_gpu.ipynb"
sys.stdout.reconfigure(encoding="utf-8")
KIEM = r'''import hashlib, json
c = json.loads((GOC / "configs/ban_chot.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(GOC))
from src.pipeline import ADAPTER_MAC_DINH
f = ADAPTER_MAC_DINH / "adapter_model.safetensors"
h = hashlib.sha256(f.read_bytes()).hexdigest()
d = [l.split()[0] for l in (GOC / "checkpoints/SHA256SUMS").read_text().splitlines() if l.split()[1] == "V2/best/adapter_model.safetensors"]
print("Bản chốt:", c["ban_chot"], "· adapter mặc định:", ADAPTER_MAC_DINH.relative_to(GOC).as_posix())
print("ADAPTER_PATH trong môi trường:", ENV.get("ADAPTER_PATH", "không đặt, dùng mặc định"))
print("SHA256 adapter:", h[:16], "· khớp SHA256SUMS:", h == d[0])
assert c["ban_chot"] == "V2" and ADAPTER_MAC_DINH.parts[-2:] == ("V2", "best") and "ADAPTER_PATH" not in ENV and h == d[0]
print("ĐẠT: mọi ô bên dưới dùng adapter V2")'''
KIEM_DEMO = r'''dong = [l.strip() for l in (GOC / "demo.log").read_text(encoding="utf-8", errors="replace").splitlines() if "backend=" in l or "gan adapter" in l]
print("\n".join(x[:150] for x in dong))
assert any("V2/best" in x or "V2\\best" in x for x in dong) and not any("V4" in x for x in dong)
print("ĐẠT: demo đang chạy adapter V2")'''


def tao():
    n = nbf.read(R / "notebooks/07_chay_san_pham_tren_gpu.ipynb", 4); C = n.cells
    assert not any("V4" in c.source and "Demo" in c.source for c in C), "còn nhãn V4"
    i = next(k for k, c in enumerate(C) if c.cell_type == "code") + 1
    C[i:i] = [nbf.v4.new_markdown_cell("## Kiểm bản đang dùng\nSản phẩm phải dùng adapter V2. Ô này dừng notebook nếu không đúng."), nbf.v4.new_code_cell(KIEM)]
    i = next(k for k, c in enumerate(C) if c.cell_type == "code" and "gradio_app.py" in c.source) + 1
    C[i:i] = [nbf.v4.new_code_cell(KIEM_DEMO)]
    n.metadata.kernelspec = {"name": "san-pham-gpu", "display_name": "san-pham-gpu", "language": "python"}
    return n


def main():
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    n = tao(); nbf.write(n, RA)
    k = NotebookClient(n, timeout=None, kernel_name="san-pham-gpu", resources={"metadata": {"path": str(R / "notebooks")}})
    with k.setup_kernel():
        for i, c in enumerate(n.cells):
            if c.cell_type != "code":
                continue
            print(__import__("time").strftime("%H:%M:%S"), "Ô", i, repr(c.source[:60]), flush=True)
            try:
                k.execute_cell(c, i)
            except CellExecutionError as e:
                nbf.write(n, RA); print("DỪNG VÌ LỖI", str(e)[-700:], flush=True); sys.exit(1)
            for x in c.outputs:
                if x.get("output_type") == "stream" and x.get("name") == "stderr":
                    x["text"] = ""
            c.outputs = [x for x in c.outputs if x.get("text", "x")]
            nbf.write(n, RA)
    print("NB07_XONG", flush=True)


if __name__ == "__main__":
    main()
