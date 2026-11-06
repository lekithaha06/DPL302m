"""Train thêm seed cho V1–V4 trên Modal, song song. Quy tắc: reports/ba_seed/QUY_TAC_3SEED.md.

Hai bước vì cùng adapter V2 trên cùng tập dev cho BLEU 26,45 với torch 2.0.1 (khớp máy nhóm) nhưng 26,24 với torch 2.7.1:
  train: RTX PRO 6000 + torch 2.7.1 (GPU này không chạy được torch 2.0.1)
  dịch và chấm: T4 + torch 2.0.1, đúng môi trường của seed 42, để số các seed so được với nhau

Dữ liệu nằm trong Volume riêng tư, xoá sau khi tải kết quả về. Không đưa PhoMT dev/test lên.
  modal run scripts/modal_3seed.py::kiem          # V2 seed 42 dịch dev, phải ra 26,45
  modal run --detach scripts/modal_3seed.py::chay # chạy tất cả, tắt máy vẫn chạy tiếp
"""
import json
import shutil
import subprocess
from pathlib import Path

import modal

REV = "ae7baa85da07dbe8e23ac26a9f5ef560c17e2138"
MT = "vinai/vinai-translate-vi2en-v2"
GOC = Path(__file__).resolve().parent / "mt"


def tai_model():
    from huggingface_hub import snapshot_download
    snapshot_download(MT, revision=REV)


def anh(torch_ver, idx):
    return (modal.Image.debian_slim(python_version="3.11")
            .pip_install(f"torch=={torch_ver}", index_url=idx)
            .pip_install("numpy==1.26.4", "transformers==4.44.2", "tokenizers==0.19.1", "huggingface_hub==0.24.6", "accelerate==0.33.0", "peft==0.12.0",
                         "sentencepiece==0.2.0", "sacrebleu==2.4.3", "protobuf==4.25.3", "safetensors", "matplotlib==3.9.2", "psutil")
            .env({"TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD": "1"})
            .run_function(tai_model)
            .add_local_file(GOC / "train_lora.py", "/code/scripts/mt/train_lora.py")
            .add_local_file(GOC / "translate.py", "/code/scripts/mt/translate.py"))


anh_train = anh("2.7.1", "https://download.pytorch.org/whl/cu128")
anh_cham = anh("2.0.1", "https://download.pytorch.org/whl/cu117")
app = modal.App("dpl302m-3seed")
vol = modal.Volume.from_name("dpl302m-3seed", create_if_missing=True)
D = "/vol/data"
TRAIN = {"V1": (["fleurs_train_asr_pho"], 2e-4), "V2": (["fleurs_train_asr_pho", "phomt_train_mix"], 2e-4),
         "V3": (["fleurs_train_asr_pho_canbang", "phomt_train_mix"], 2e-4), "V4": (["fleurs_train_asr_pho_canbang", "phomt_train_mix"], 5e-5),
         "A_r8": (["fleurs_train_asr_pho", "phomt_train_mix"], 2e-4, 8, 16), "A_r32": (["fleurs_train_asr_pho", "phomt_train_mix"], 2e-4, 32, 64),
         "A_aug": (["fleurs_train_asr_pho", "phomt_train_mix", "fleurs_train_clean_asrstyle"], 2e-4)}
TAP = ["fleurs_dev_asr_pho", "fleurs_dev_clean", "fleurs_test_asr_pho", "fleurs_test_clean", "fleurs_test_asr_wsp"]


def dich(tap, ra, adapter):
    if (Path(ra) / "score.json").exists():
        return
    subprocess.run(["python", "/code/scripts/mt/translate.py", "--input", f"{D}/{tap}.jsonl", "--out_dir", ra, "--revision", REV, "--adapter", adapter], cwd="/code", check=True)


@app.function(image=anh_train, gpu="RTX-PRO-6000", timeout=5 * 3600, volumes={"/vol": vol})
def train(v, seed):
    ten = f"{v}_s{seed}"; ck = f"/vol/out/checkpoints/{ten}"; files, lr, r, al = (*TRAIN[v], 16, 32)[:4]
    if not Path(ck, "best/adapter_model.safetensors").exists():
        subprocess.run(["python", "/code/scripts/mt/train_lora.py", "--train", *[f"{D}/{f}.jsonl" for f in files], "--dev", f"{D}/fleurs_dev_asr_pho.jsonl", "--out_dir", ck, "--revision", REV,
                        "--epochs", "5", "--lr", str(lr), "--batch_size", "4", "--grad_accum", "4", "--lora_r", str(r), "--lora_alpha", str(al), "--seed", str(seed), "--resume"], cwd="/code", check=True)
        for p in Path(ck).glob("epoch_*"):
            shutil.rmtree(p)
        vol.commit()
    return ten


@app.function(image=anh_cham, gpu="T4", timeout=2 * 3600, volumes={"/vol": vol})
def cham(ten):
    vol.reload()
    for t in TAP:
        dich(t, f"/vol/out/runs/mt/{ten}/{t}", f"/vol/out/checkpoints/{ten}/best"); vol.commit()
    return ten, json.loads(Path(f"/vol/out/runs/mt/{ten}/fleurs_dev_asr_pho/score.json").read_text())["BLEU"]


@app.function(image=anh_cham, timeout=12 * 3600, volumes={"/vol": vol})
def dieu_phoi():
    jobs = [(v, s) for v in ("A_r8", "A_r32", "A_aug") for s in (1, 2)]
    xong = [k for k in train.starmap(jobs, return_exceptions=True) if isinstance(k, str)]
    print("TRAIN_XONG", xong, flush=True)
    kq = list(cham.map(xong, return_exceptions=True))
    print("TAT_CA_XONG", kq, flush=True)
    vol.reload(); Path("/vol/out").mkdir(exist_ok=True); Path("/vol/out/XONG.json").write_text(json.dumps([str(x) for x in kq], ensure_ascii=False)); vol.commit()


@app.function(image=anh_cham, gpu="T4", timeout=1800, volumes={"/vol": vol})
def kiem_gpu():
    import torch
    print(torch.__version__, torch.cuda.get_device_name(0))
    dich("fleurs_dev_asr_pho", "/tmp/kiem", "/vol/adapter_V2")
    return Path("/tmp/kiem/score.json").read_text()


@app.local_entrypoint()
def kiem():
    print(kiem_gpu.remote())


@app.local_entrypoint()
def chay():
    dieu_phoi.spawn()
