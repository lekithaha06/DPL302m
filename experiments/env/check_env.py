import json, platform, sys, torch, transformers, huggingface_hub
x = torch.randn(512, 512, device="cuda", dtype=torch.float16); y = (x @ x).sum().item()
conv = torch.nn.Conv1d(80, 64, 3).cuda().half()(torch.randn(1, 80, 100, device="cuda", dtype=torch.float16)).shape
info = {"python": sys.version.split()[0], "torch": torch.__version__, "cuda_runtime": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version(), "gpu": torch.cuda.get_device_name(0),
        "gpu_capability": torch.cuda.get_device_capability(0), "arch_list": torch.cuda.get_arch_list(),
        "vram_total_bytes": torch.cuda.get_device_properties(0).total_memory, "transformers": transformers.__version__,
        "huggingface_hub": huggingface_hub.__version__, "platform": platform.platform(), "cpu": platform.processor(),
        "fp16_matmul_ok": y == y, "conv_ok": list(conv)}
print(json.dumps(info, indent=2))
