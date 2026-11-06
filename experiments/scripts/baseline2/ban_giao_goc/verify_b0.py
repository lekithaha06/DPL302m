"""Kiểm chứng B0 (Cascade: PhoWhisper + VinAI pretrained) - Giai đoạn B."""
import json
from pathlib import Path

REPO = Path("/sessions/serene-dazzling-noether/mnt/outputs/repo/experiments")
FLEURS_MANIFEST = Path("/tmp/dang_fleurs/GUI_DANG_FLEURS_TEST/manifest_fleurs_test.jsonl")

def main():
    print("=== KIỂM CHỨNG B0 (CASCADE) ===\n")

    # 1. Xác định các file
    asr_pred = REPO / "runs/asr/kiet_t2_phowhisper-small_fleurs_test/predictions.jsonl"
    mt_hyp = REPO / "runs/mt/B0/fleurs_test_asr_pho/hyp.jsonl"
    mt_score = REPO / "runs/mt/B0/fleurs_test_asr_pho/score.json"

    print("1. CÁC FILE B0:")
    print(f"   ASR predictions: {asr_pred.exists()} - {asr_pred}")
    print(f"   MT hypotheses: {mt_hyp.exists()} - {mt_hyp}")
    print(f"   MT score: {mt_score.exists()} - {mt_score}")

    if not all([asr_pred.exists(), mt_hyp.exists(), mt_score.exists()]):
        print("\n❌ Thiếu file B0")
        return 1

    # 2. Đọc score
    score = json.load(open(mt_score))
    print(f"\n2. KẾT QUẢ B0 (từ score.json):")
    print(f"   BLEU: {score['BLEU']}")
    print(f"   chrF++: {score['chrF++']}")
    print(f"   Số mẫu: {score['n']}")
    print(f"   Model MT: {score['model']}")
    print(f"   Revision: {score['revision']}")
    print(f"   Adapter: {score['adapter']}")
    print(f"   Dtype: {score['dtype']}")
    print(f"   Decode config: {score['decode']}")

    # 3. Kiểm tra ASR predictions
    asr_data = [json.loads(l) for l in open(asr_pred)]
    print(f"\n3. ASR PREDICTIONS:")
    print(f"   Số mẫu: {len(asr_data)}")
    print(f"   Run fingerprint: {asr_data[0].get('run_fingerprint', 'N/A')}")

    # Sample
    print(f"\n   Mẫu đầu tiên:")
    print(f"   ID: {asr_data[0]['id']}")
    print(f"   Reference VI: {asr_data[0]['reference'][:80]}...")
    print(f"   Prediction VI: {asr_data[0]['prediction'][:80]}...")

    # 4. Kiểm tra MT predictions
    mt_data = [json.loads(l) for l in open(mt_hyp)]
    print(f"\n4. MT PREDICTIONS:")
    print(f"   Số mẫu: {len(mt_data)}")

    # Sample
    print(f"\n   Mẫu đầu tiên:")
    print(f"   ID: {mt_data[0]['id']}")
    print(f"   Source VI (từ ASR): {mt_data[0]['src'][:60]}...")
    print(f"   Reference EN: {mt_data[0]['ref'][:60]}...")
    print(f"   Hypothesis EN: {mt_data[0]['hyp'][:60]}...")

    # 5. Kiểm tra khớp với FLEURS manifest
    fleurs_data = [json.loads(l) for l in open(FLEURS_MANIFEST)]
    fleurs_ids = {str(r['sample_id']) for r in fleurs_data}
    mt_ids = {r['id'].replace('.wav', '') for r in mt_data}

    missing_in_b0 = fleurs_ids - mt_ids
    extra_in_b0 = mt_ids - fleurs_ids

    print(f"\n5. KIỂM TRA KHỚP VỚI FLEURS MANIFEST:")
    print(f"   Thiếu trong B0: {len(missing_in_b0)}")
    print(f"   Thừa trong B0: {len(extra_in_b0)}")

    # 6. Tạo bản tổng hợp B0
    b0_summary = {
        "name": "B0_Cascade_PhoWhisper_VinAI",
        "architecture": "Vietnamese Audio → PhoWhisper-small → Vietnamese Text → VinAI Translate (pretrained) → English Text",
        "asr_model": "vinai/PhoWhisper-small",
        "mt_model": score['model'],
        "mt_revision": score['revision'],
        "mt_adapter": score['adapter'],
        "mt_dtype": score['dtype'],
        "decode_config": score['decode'],
        "metrics": {
            "BLEU": score['BLEU'],
            "chrF++": score['chrF++'],
            "n_samples": score['n']
        },
        "files": {
            "asr_predictions": str(asr_pred.relative_to(REPO)),
            "mt_hypotheses": str(mt_hyp.relative_to(REPO)),
            "mt_score": str(mt_score.relative_to(REPO))
        }
    }

    out_file = Path("/sessions/serene-dazzling-noether/mnt/outputs/dang_baseline/b0_summary.json")
    json.dump(b0_summary, open(out_file, 'w'), indent=2, ensure_ascii=False)
    print(f"\n6. ĐÃ GHI: {out_file}")

    print("\n=== KẾT LUẬN ===")
    if len(missing_in_b0) == 0 and len(extra_in_b0) == 0:
        print("✅ B0 đầy đủ và khớp với FLEURS test")
        return 0
    else:
        print("❌ B0 không khớp hoàn toàn với FLEURS test")
        return 1

if __name__ == "__main__":
    exit(main())
