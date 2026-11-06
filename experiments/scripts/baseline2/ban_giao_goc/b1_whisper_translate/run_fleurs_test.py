"""Chạy B1 Whisper Translate trên toàn bộ FLEURS test (857 mẫu)."""
import json
import argparse
from pathlib import Path
from tqdm import tqdm
import torch
from inference import WhisperTranslator

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, help="FLEURS manifest JSONL")
    parser.add_argument("--output", default="predictions_b1.jsonl", help="Output predictions")
    parser.add_argument("--device", default=None, help="cuda or cpu")
    parser.add_argument("--dtype", default="float16", help="float16 or float32")
    parser.add_argument("--limit", type=int, default=None, help="Số mẫu tối đa (để test)")
    args = parser.parse_args()

    # Load manifest
    manifest_path = Path(args.manifest)
    data = [json.loads(line) for line in open(manifest_path)]

    if args.limit:
        data = data[:args.limit]
        print(f"⚠️  Chỉ chạy {args.limit} mẫu đầu tiên (test mode)")

    print(f"Tổng số mẫu: {len(data)}")
    print(f"Device: {args.device or 'auto'}")
    print(f"Dtype: {args.dtype}")

    # Load model
    translator = WhisperTranslator(
        model_name="openai/whisper-small",
        device=args.device,
        dtype=args.dtype
    )

    # Inference
    results = []
    total_latency = 0
    total_duration = 0

    manifest_dir = manifest_path.parent

    for record in tqdm(data, desc="Translating"):
        sample_id = record["sample_id"]
        audio_path = manifest_dir / record["audio_path"]
        reference_en = record["reference_en"]

        try:
            result = translator.translate(str(audio_path))

            output = {
                "id": str(sample_id),
                "audio_path": str(audio_path),
                "prediction_en": result["translation"],
                "reference_en": reference_en,
                "latency_s": result["latency_s"],
                "audio_duration_s": result["audio_duration_s"],
                "rtf": result["rtf"],
                "domain": record.get("domain", "unknown")
            }

            results.append(output)
            total_latency += result["latency_s"]
            total_duration += result["audio_duration_s"]

        except Exception as e:
            print(f"\n❌ Lỗi tại {sample_id}: {e}")
            results.append({
                "id": str(sample_id),
                "audio_path": str(audio_path),
                "prediction_en": "",
                "reference_en": reference_en,
                "error": str(e),
                "domain": record.get("domain", "unknown")
            })

    # Ghi kết quả
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n✅ Đã ghi {len(results)} kết quả vào {output_path}")

    # Summary
    avg_rtf = total_latency / total_duration if total_duration > 0 else 0
    successful = sum(1 for r in results if "error" not in r)

    print(f"\nTHỐNG KÊ:")
    print(f"  Thành công: {successful}/{len(results)}")
    print(f"  Tổng thời lượng audio: {total_duration:.1f}s")
    print(f"  Tổng latency: {total_latency:.1f}s")
    print(f"  RTF trung bình: {avg_rtf:.3f}")

if __name__ == "__main__":
    main()
