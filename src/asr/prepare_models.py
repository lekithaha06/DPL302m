"""Convert pinned original publisher checkpoints to CTranslate2 int8 for CPU evaluation."""
import argparse
import json
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download
from ctranslate2.converters import TransformersConverter
from transformers import AutoTokenizer
from download_checkpoints import REVISIONS

class CompatibleConverter(TransformersConverter):
    """CTranslate2 4.8 uses dtype; Transformers 4.44 calls this torch_dtype."""
    def load_model(self, model_class, model_name_or_path, **kwargs):
        if "dtype" in kwargs:
            kwargs["torch_dtype"] = kwargs.pop("dtype")
        return super().load_model(model_class, model_name_or_path, **kwargs)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=".work/hf_cache")
    ap.add_argument("--output", default=".work/models")
    ap.add_argument("--source-dir", default="", help="Use snapshots downloaded by download_checkpoints.py")
    ap.add_argument("--models", nargs="+", default=["vinai/PhoWhisper-small", "openai/whisper-small"])
    args = ap.parse_args()
    for model_id in args.models:
        dest = Path(args.output) / model_id.split("/")[-1]
        if (dest / "provenance.json").exists() and (dest / "model.bin").exists():
            print(f"Already converted: {model_id}", flush=True)
            continue
        if args.source_dir:
            source = str(Path(args.source_dir) / model_id.split("/")[-1])
            metadata = json.loads((Path(source) / "source_provenance.json").read_text())
            revision, weight = metadata["revision"], metadata["source_weight_file"]
        else:
            info = HfApi().model_info(model_id, revision=REVISIONS.get(model_id))
            names = {s.rfilename for s in info.siblings}
            weight = "model.safetensors" if "model.safetensors" in names else "pytorch_model.bin"
            revision = info.sha
            print(f"Downloading {model_id}@{revision}, {weight}", flush=True)
            source = snapshot_download(model_id, revision=revision, cache_dir=args.cache,
                                       allow_patterns=["*.json", "*.txt", "*.model", weight])
        print(f"Converting {model_id} to int8", flush=True)
        CompatibleConverter(source).convert(str(dest), quantization="int8", force=True)
        AutoTokenizer.from_pretrained(source).save_pretrained(dest)
        import shutil
        shutil.copyfile(Path(source) / "preprocessor_config.json", dest / "preprocessor_config.json")
        provenance = {"source_model": model_id, "revision": revision, "source_weight_file": weight,
                      "conversion": "CTranslate2 TransformersConverter", "quantization": "int8"}
        (dest / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
        print(json.dumps(provenance), flush=True)

if __name__ == "__main__":
    main()
