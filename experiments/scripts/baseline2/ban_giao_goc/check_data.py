"""Kiểm tra dataset FLEURS test - Giai đoạn A."""
import json
import os
import wave
import hashlib
from pathlib import Path
from collections import Counter

FLEURS_DIR = Path("/tmp/dang_fleurs/GUI_DANG_FLEURS_TEST")
MANIFEST = FLEURS_DIR / "manifest_fleurs_test.jsonl"

def check_audio(path):
    """Kiểm tra audio: đọc được, lấy duration, channels, sample_rate."""
    try:
        w = wave.open(str(path), 'rb')
        duration = w.getnframes() / w.getframerate()
        channels = w.getnchannels()
        sr = w.getframerate()
        w.close()
        return {"ok": True, "duration_s": duration, "channels": channels, "sr": sr}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def main():
    print("=== KIỂM TRA DATASET FLEURS TEST ===\n")

    # Đọc manifest
    data = [json.loads(line) for line in open(MANIFEST)]
    print(f"Tổng số mẫu trong manifest: {len(data)}")

    # Kiểm tra trùng ID
    ids = [r['sample_id'] for r in data]
    duplicates = len(ids) - len(set(ids))
    print(f"Trùng sample_id: {duplicates}")

    # Kiểm tra audio
    missing = []
    corrupt = []
    sha_mismatch = []
    durations = []
    channels_count = Counter()
    sr_count = Counter()

    for r in data:
        audio_path = FLEURS_DIR / r['audio_path']

        if not audio_path.exists():
            missing.append(r['sample_id'])
            continue

        # Check audio
        check = check_audio(audio_path)
        if not check['ok']:
            corrupt.append((r['sample_id'], check['error']))
            continue

        durations.append(check['duration_s'])
        channels_count[check['channels']] += 1
        sr_count[check['sr']] += 1

        # Check SHA256
        if 'audio_sha256' in r and r['audio_sha256']:
            actual_sha = hashlib.sha256(audio_path.read_bytes()).hexdigest()
            if actual_sha != r['audio_sha256']:
                sha_mismatch.append(r['sample_id'])

    print(f"\nAudio missing: {len(missing)}")
    print(f"Audio corrupt: {len(corrupt)}")
    print(f"SHA256 mismatch: {len(sha_mismatch)}")

    if durations:
        print(f"\nDuration: min={min(durations):.2f}s, max={max(durations):.2f}s, avg={sum(durations)/len(durations):.2f}s")
    print(f"Channels: {dict(channels_count)}")
    print(f"Sample rates: {dict(sr_count)}")

    # Domain distribution
    domains = Counter(r.get('domain', 'unknown') for r in data)
    print(f"\nDomain phân bố:")
    for d, c in domains.most_common():
        print(f"  {d}: {c} ({c/len(data)*100:.1f}%)")

    # Check reference
    no_vi = sum(1 for r in data if not r.get('reference_vi'))
    no_en = sum(1 for r in data if not r.get('reference_en'))
    print(f"\nThiếu reference_vi: {no_vi}")
    print(f"Thiếu reference_en: {no_en}")

    # Kiểm tra ID khớp với repo manifest
    repo_manifest = Path("/sessions/serene-dazzling-noether/mnt/outputs/repo/experiments/runs/manifests/asr_fleurs_test.jsonl")
    if repo_manifest.exists():
        repo_data = [json.loads(l) for l in open(repo_manifest)]
        repo_ids = {r['id'].replace('.wav', '') for r in repo_data}
        fleurs_ids = {str(r['sample_id']) for r in data}
        only_repo = repo_ids - fleurs_ids
        only_fleurs = fleurs_ids - repo_ids
        print(f"\nSo sánh với repo manifest:")
        print(f"  Repo có {len(repo_data)} mẫu")
        print(f"  Chỉ có trong repo: {len(only_repo)}")
        print(f"  Chỉ có trong FLEURS GUI: {len(only_fleurs)}")

    print("\n=== KẾT LUẬN ===")
    if missing or corrupt or sha_mismatch or duplicates or no_vi or no_en:
        print("❌ Dataset có vấn đề cần xử lý")
        return 1
    else:
        print("✅ Dataset hợp lệ, sẵn sàng cho thực nghiệm")
        return 0

if __name__ == "__main__":
    exit(main())
