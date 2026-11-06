"""Đánh giá B1: BLEU, chrF++ và so sánh với B0."""
import json
import argparse
from pathlib import Path
from collections import defaultdict
import sys

# Import sacreBLEU nếu có; không thì dùng _bleu13a.py từ notebooks
try:
    from sacrebleu import BLEU, CHRF
    USE_SACREBLEU = True
except ImportError:
    USE_SACREBLEU = False
    sys.path.insert(0, str(Path(__file__).parents[2] / "repo/notebooks"))
    from _bleu13a import bleu13a_corpus

def compute_bleu(refs, hyps):
    """Tính BLEU bằng sacreBLEU hoặc _bleu13a."""
    if USE_SACREBLEU:
        bleu = BLEU()
        result = bleu.corpus_score(hyps, [refs])
        return round(result.score, 2)
    else:
        return round(bleu13a_corpus(refs, hyps), 2)

def compute_chrf(refs, hyps):
    """Tính chrF++ bằng sacreBLEU."""
    if USE_SACREBLEU:
        chrf = CHRF(word_order=2)
        result = chrf.corpus_score(hyps, [refs])
        return round(result.score, 2)
    else:
        return None  # Không có _chrf13a

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, help="predictions_b1.jsonl")
    parser.add_argument("--manifest", required=True, help="FLEURS manifest")
    parser.add_argument("--output", default="metrics_b1.json", help="Output metrics")
    parser.add_argument("--b0_score", default=None, help="B0 score.json để so sánh")
    args = parser.parse_args()

    # Load predictions
    predictions = [json.loads(l) for l in open(args.predictions)]
    print(f"Số mẫu: {len(predictions)}")

    # Lọc mẫu thành công
    successful = [p for p in predictions if "error" not in p and p.get("prediction_en")]
    failed = len(predictions) - len(successful)

    if failed > 0:
        print(f"⚠️  Có {failed} mẫu lỗi, chỉ đánh giá {len(successful)} mẫu")

    if len(successful) == 0:
        print("❌ Không có mẫu nào thành công")
        sys.exit(1)

    # Extract refs và hyps
    refs = [p["reference_en"] for p in successful]
    hyps = [p["prediction_en"] for p in successful]

    # Compute metrics
    bleu = compute_bleu(refs, hyps)
    chrf = compute_chrf(refs, hyps) if USE_SACREBLEU else None

    # RTF
    total_latency = sum(p.get("latency_s", 0) for p in successful)
    total_duration = sum(p.get("audio_duration_s", 0) for p in successful)
    avg_rtf = total_latency / total_duration if total_duration > 0 else 0

    # Theo domain
    domain_metrics = defaultdict(lambda: {"refs": [], "hyps": []})
    for p in successful:
        domain = p.get("domain", "unknown")
        domain_metrics[domain]["refs"].append(p["reference_en"])
        domain_metrics[domain]["hyps"].append(p["prediction_en"])

    domain_bleu = {}
    for domain, data in domain_metrics.items():
        domain_bleu[domain] = compute_bleu(data["refs"], data["hyps"])

    # Metrics summary
    metrics = {
        "model": "openai/whisper-small",
        "task": "translate",
        "language": "vi",
        "n_total": len(predictions),
        "n_successful": len(successful),
        "n_failed": failed,
        "BLEU": bleu,
        "chrF++": chrf,
        "RTF_avg": round(avg_rtf, 3),
        "total_audio_duration_s": round(total_duration, 1),
        "total_latency_s": round(total_latency, 1),
        "domain_BLEU": domain_bleu,
        "sacrebleu_version": "2.4.3" if USE_SACREBLEU else "_bleu13a"
    }

    # So sánh với B0
    if args.b0_score and Path(args.b0_score).exists():
        b0 = json.load(open(args.b0_score))
        metrics["comparison_with_B0"] = {
            "B0_BLEU": b0["BLEU"],
            "B1_BLEU": bleu,
            "delta_BLEU": round(bleu - b0["BLEU"], 2),
            "B0_chrF++": b0.get("chrF++"),
            "B1_chrF++": chrf,
            "delta_chrF++": round(chrf - b0["chrF++"], 2) if chrf and "chrF++" in b0 else None
        }

    # Ghi kết quả
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(metrics, open(output_path, "w"), indent=2, ensure_ascii=False)

    print(f"\n✅ KẾT QUẢ B1:")
    print(f"   BLEU: {bleu}")
    if chrf:
        print(f"   chrF++: {chrf}")
    print(f"   RTF: {avg_rtf:.3f}")
    print(f"   Thành công: {len(successful)}/{len(predictions)}")

    if "comparison_with_B0" in metrics:
        comp = metrics["comparison_with_B0"]
        print(f"\n📊 SO SÁNH VỚI B0:")
        print(f"   B0 BLEU: {comp['B0_BLEU']}")
        print(f"   B1 BLEU: {comp['B1_BLEU']}")
        print(f"   Δ BLEU: {comp['delta_BLEU']:+.2f}")

    print(f"\nĐã ghi: {output_path}")

if __name__ == "__main__":
    main()
