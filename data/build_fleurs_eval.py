"""Build the FLEURS vi->en eval set: align Vietnamese utterances with English references by FLoRes sentence id.

Inputs (download from https://huggingface.co/datasets/google/fleurs):
  <fleurs>/data/vi_vn/test.tsv, <fleurs>/data/en_us/test.tsv, <fleurs>/data/vi_vn/audio/test.tar.gz extracted to --audio-dir
"""
import argparse, csv, glob, json, os

ap = argparse.ArgumentParser()
ap.add_argument("--fleurs", default="data/fleurs")
ap.add_argument("--audio-dir", default="data/fleurs_audio_test")
ap.add_argument("--split", default="test")
ap.add_argument("--output", default="data/processed/fleurs_vi_en_test.json")
args = ap.parse_args()

vi_tsv = f"{args.fleurs}/data/vi_vn/{args.split}.tsv"
en_tsv = f"{args.fleurs}/data/en_us/{args.split}.tsv"
wavs = {os.path.basename(p): p for p in glob.glob(f"{args.audio_dir}/**/*.wav", recursive=True)}

en = {}
with open(en_tsv, encoding="utf-8") as f:
    for r in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
        en.setdefault(r[0], r[2])  # raw_transcription, first occurrence

rows, missing_en, missing_wav = [], 0, 0
with open(vi_tsv, encoding="utf-8") as f:
    for r in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
        sid, fn, raw, norm = r[0], r[1], r[2], r[3]
        if sid not in en:
            missing_en += 1
            continue
        if fn not in wavs:
            missing_wav += 1
            continue
        rows.append({"id": sid, "audio": wavs[fn], "vi_raw": raw, "vi_norm": norm, "en_ref": en[sid]})

print(f"utterances={len(rows)} unique_sentences={len({r['id'] for r in rows})} "
      f"missing_en={missing_en} missing_wav={missing_wav}")
os.makedirs(os.path.dirname(args.output), exist_ok=True)
json.dump(rows, open(args.output, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
