"""Task 2 · dữ liệu phụ cho V2/V3 (chỉ lấy từ train, không đụng dev/test).

  fleurs_train_clean.jsonl : mỗi câu gốc FLEURS train một cặp (chữ Việt chuẩn → câu Anh)
  phomt_train_subset.jsonl : N cặp lấy ngẫu nhiên (seed 42) từ PhoMT train, để khối dịch không quên văn bản sạch
PhoMT là dữ liệu cấm phân phối lại nên file ra nằm trong data/ (không commit).
"""
import argparse, json, os, random

ap = argparse.ArgumentParser()
ap.add_argument("--fleurs-train", default="data/processed/fleurs_vi_en_train.json")
ap.add_argument("--phomt", default="")
ap.add_argument("--n-phomt", type=int, default=3000)
ap.add_argument("--out", default="data/mt")
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)

seen, clean = set(), []
for r in json.load(open(args.fleurs_train, encoding="utf-8")):
    if r["id"] not in seen:
        seen.add(r["id"]); clean.append({"src": r["vi_raw"], "en_ref": r["en_ref"], "id": r["id"]})
with open(f"{args.out}/fleurs_train_clean.jsonl", "w", encoding="utf-8") as f:
    f.writelines(json.dumps(x, ensure_ascii=False) + "\n" for x in clean)
print("fleurs clean pairs", len(clean))

if args.phomt:
    d = f"{args.phomt}/detokenization/train/train"
    vi = open(d + ".vi", encoding="utf-8").read().split("\n")
    en = open(d + ".en", encoding="utf-8").read().split("\n")
    idx = [i for i in range(min(len(vi), len(en))) if vi[i].strip() and en[i].strip() and len(vi[i]) < 400]
    random.Random(42).shuffle(idx)
    with open(f"{args.out}/phomt_train_subset.jsonl", "w", encoding="utf-8") as f:
        for i in idx[: args.n_phomt]:
            f.write(json.dumps({"src": vi[i], "en_ref": en[i], "line": i}, ensure_ascii=False) + "\n")
    print("phomt subset", args.n_phomt, "of", len(idx), "eligible lines")
