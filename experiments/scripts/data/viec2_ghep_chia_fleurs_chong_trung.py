#!/usr/bin/env python3
"""VIỆC 2 (phần chia tập + chống leakage) – Task 2, TV4 Uyên viết, Kiệt chạy.

NHIỆM VỤ: tải FLEURS train/dev, ghép bản thu tiếng Việt (vi_vn) với câu tiếng Anh (en_us) theo ID câu,
giữ cách chia gốc theo ID câu, và loại khỏi tập dạy các câu trùng với tập test / PhoMT test (chống leakage).
Chạy SAU viec1_tai_3_bo_du_lieu.py (dùng lại audio đã tải).

Script tải mới từ nguồn gốc (Hugging Face google/fleurs), không dùng bản ai đó tải sẵn.
- vi_vn: tải TSV + audio của train/dev (test chỉ tải TSV để kiểm trùng; thêm --with_test_audio nếu cần audio test).
- en_us: chỉ tải TSV của cả 3 tập để lấy câu tiếng Anh theo ID câu (không cần audio tiếng Anh).
- Kiểm trùng: ID câu giữa các tập, câu train/dev trùng câu test FLEURS, trùng PhoMT test,
  và (cho V2) dòng PhoMT train trùng câu FLEURS test.

Dữ liệu (audio, chữ) nằm trong --data_dir (đã .gitignore). Thư mục --report_dir chỉ chứa ID, số đếm,
không chứa câu chữ, nên commit được.

Chạy đầy đủ (máy Kiệt / Bảo):
    huggingface-cli login            # cần cho PhoMT (gated), phải bấm đồng ý điều khoản trên web trước
    python scripts/data/viec2_ghep_chia_fleurs_chong_trung.py --data_dir data --report_dir reports/task2/data

Chạy thử ít mẫu (máy Uyên), không cần PhoMT:
    python scripts/data/viec2_ghep_chia_fleurs_chong_trung.py --limit 20 --skip_phomt --data_dir data_thu --report_dir data_thu/report
"""
import argparse
import csv
import datetime
import json
import platform
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

from ham_dung_chung import FLEURS_REPO, ensure_phomt, lib_versions, norm, read_fleurs_tsv as read_tsv, repo_meta
from ham_dung_chung import fetch as hf_fetch

SPLITS = ["train", "dev", "test"]
SR = 16000
# Thứ tự ưu tiên khi một ID câu nằm ở nhiều tập: giữ ở test, bỏ khỏi tập dạy
PRIORITY = {"test": 0, "dev": 1, "train": 2}


# ---------------------------------------------------------------- tải từ Hugging Face

def fetch(relpath, args):
    """Tải 1 file của repo FLEURS vào <data_dir>/fleurs/hf (chung chỗ với viec1_tai_3_bo_du_lieu.py, không tải lại)."""
    return hf_fetch(FLEURS_REPO, relpath, args.data_dir / "fleurs" / "hf", args.revision)


def stream_tar_members(relpath, n, args):
    """Chế độ --limit: đọc dần file .tar.gz qua mạng, lấy n file wav đầu tiên rồi dừng (không tải cả file)."""
    import requests
    from huggingface_hub import get_token, hf_hub_url
    url = hf_hub_url(FLEURS_REPO, relpath, repo_type="dataset", revision=args.revision)
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    with requests.get(url, headers=headers, stream=True, timeout=120) as r:
        r.raise_for_status()
        with tarfile.open(fileobj=r.raw, mode="r|gz") as tar:
            got = 0
            for m in tar:
                if m.isfile() and m.name.endswith(".wav"):
                    yield Path(m.name).name, tar.extractfile(m).read()
                    got += 1
                    if got >= n:
                        return


def full_tar_members(relpath, args):
    with tarfile.open(fetch(relpath, args), mode="r:gz") as tar:
        for m in tar:
            if m.isfile() and m.name.endswith(".wav"):
                yield Path(m.name).name, tar.extractfile(m).read()


def resolve_revision(args):
    return repo_meta(FLEURS_REPO, args.revision, path_in_repo="data/vi_vn/dev.tsv").get("sha", "unknown")


def phomt_files(args):
    return ensure_phomt(args.phomt_dir, splits=("train", "test"))


def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]


# ---------------------------------------------------------------- chính

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data_dir", type=Path, default=Path("data"))
    ap.add_argument("--report_dir", type=Path, default=Path("reports/task2/data"))
    ap.add_argument("--phomt_dir", type=Path, default=None, help="mặc định <data_dir>/phomt")
    ap.add_argument("--revision", default="main", help="nhánh/commit của google/fleurs; mã commit thật được ghi vào summary")
    ap.add_argument("--limit", type=int, default=0, help="chạy thử: chỉ lấy N bản thu đầu tiên mỗi tập")
    ap.add_argument("--with_test_audio", action="store_true")
    ap.add_argument("--skip_phomt", action="store_true", help="bỏ kiểm trùng PhoMT (chỉ dùng khi chạy thử)")
    args = ap.parse_args()
    args.phomt_dir = args.phomt_dir or args.data_dir / "phomt"
    args.report_dir.mkdir(parents=True, exist_ok=True)
    man_dir = args.data_dir / "fleurs" / "manifest"
    man_dir.mkdir(parents=True, exist_ok=True)

    summary = {"script": "viec2_ghep_chia_fleurs_chong_trung.py", "time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
               "args": {k: str(v) for k, v in vars(args).items()}, "versions": lib_versions(),
               "platform": platform.platform(), "fleurs_revision": resolve_revision(args)}

    # 1) Câu tiếng Anh theo ID câu, lấy từ cả 3 tập en_us (một ID câu có thể nằm ở tập khác bên vi_vn)
    en_texts = defaultdict(Counter)
    en_bad = 0
    for split in SPLITS:
        rows, bad = read_tsv(fetch(f"data/en_us/{split}.tsv", args))
        en_bad += bad
        for r in rows:
            en_texts[r["sent_id"]][r["raw"]] += 1
    en_of = {sid: c.most_common(1)[0][0] for sid, c in en_texts.items()}
    summary["en_us"] = {"sentences": len(en_of), "bad_tsv_lines": en_bad,
                        "ids_with_different_en_text": sum(len(c) > 1 for c in en_texts.values())}

    # 2) vi_vn: TSV + audio
    rows_by_split, stats = {}, {}
    for split in SPLITS:
        rows, bad = read_tsv(fetch(f"data/vi_vn/{split}.tsv", args))
        st = {"tsv_rows": len(rows), "bad_tsv_lines": bad}
        audio_dir = args.data_dir / "fleurs" / "audio" / "vi_vn" / split
        want_audio = split != "test" or args.with_test_audio
        if want_audio:
            audio_dir.mkdir(parents=True, exist_ok=True)
            rel = f"data/vi_vn/audio/{split}.tar.gz"
            members = stream_tar_members(rel, args.limit, args) if args.limit else full_tar_members(rel, args)
            got = set()
            for name, data in members:
                (audio_dir / name).write_bytes(data)
                got.add(name)
            st["wav_in_archive"] = len(got)
            if args.limit:  # chạy thử: chỉ giữ dòng TSV có audio vừa lấy
                rows = [r for r in rows if r["file_name"] in got]
        elif args.limit:
            rows = rows[:args.limit]
        for r in rows:
            r["split"] = split
            r["duration_s"] = round(r["num_samples"] / SR, 3)
            path = audio_dir / r["file_name"]
            r["audio_path"] = str(path) if want_audio else None
            r["audio_exists"] = path.exists() if want_audio else None
            r["en"] = en_of.get(r["sent_id"])
            r["vi_norm"] = norm(r["raw"])
            r["en_norm"] = norm(r["en"]) if r["en"] else None
            r["drop"] = None
        rows_by_split[split] = rows
        stats[split] = st

    # 3) Chia theo ID câu: một ID câu chỉ được nằm ở một tập
    id_splits = defaultdict(set)
    for split, rows in rows_by_split.items():
        for r in rows:
            id_splits[r["sent_id"]].add(split)
    conflict_ids = {sid: sorted(s, key=PRIORITY.get) for sid, s in id_splits.items() if len(s) > 1}
    for split, rows in rows_by_split.items():
        for r in rows:
            sp = conflict_ids.get(r["sent_id"])
            if sp and split != sp[0]:
                r["drop"] = f"id_also_in_{sp[0]}"
    summary["id_split_conflicts"] = {"n_ids": len(conflict_ids), "examples": dict(list(conflict_ids.items())[:10])}

    # 4) Câu train/dev trùng chữ với câu test FLEURS (khác ID nhưng cùng nội dung)
    test_vi = {r["vi_norm"] for r in rows_by_split["test"]}
    test_en = {r["en_norm"] for r in rows_by_split["test"] if r["en_norm"]}
    for split in ("train", "dev"):
        for r in rows_by_split[split]:
            if r["drop"] is None and (r["vi_norm"] in test_vi or (r["en_norm"] and r["en_norm"] in test_en)):
                r["drop"] = "text_in_fleurs_test"

    # 5) PhoMT
    if args.skip_phomt:
        summary["phomt"] = "skipped (--skip_phomt)"
    else:
        pf = phomt_files(args)
        pt_vi_lines = read_lines(pf[("test", "vi")])
        pt_vi = {norm(x) for x in pt_vi_lines}
        pt_en = {norm(x) for x in read_lines(pf[("test", "en")])}
        for split in ("train", "dev"):
            for r in rows_by_split[split]:
                if r["drop"] is None and (r["vi_norm"] in pt_vi or (r["en_norm"] and r["en_norm"] in pt_en)):
                    r["drop"] = "text_in_phomt_test"
        fleurs_test_in_phomt_test = len({r["sent_id"] for r in rows_by_split["test"]
                                         if r["vi_norm"] in pt_vi or (r["en_norm"] and r["en_norm"] in pt_en)})
        # Cho V2 (trộn PhoMT train): dòng PhoMT train nào trùng câu FLEURS test thì phải bỏ khi trộn
        exclude, n_train = [], 0
        with open(pf[("train", "vi")], encoding="utf-8") as fv, open(pf[("train", "en")], encoding="utf-8") as fe:
            for i, (v, e) in enumerate(zip(fv, fe)):  # đọc từng dòng, không nạp cả 3 triệu câu vào RAM
                n_train += 1
                if norm(v) in test_vi or norm(e) in test_en:
                    exclude.append(i)
        (args.report_dir / "phomt_train_exclude_idx.txt").write_text("".join(f"{i}\n" for i in exclude))
        summary["phomt"] = {"files": {f"{s}.{l}": str(p) for (s, l), p in pf.items()},
                            "test_pairs": len(pt_vi_lines), "train_pairs": n_train,
                            "fleurs_test_sentences_in_phomt_test": fleurs_test_in_phomt_test,
                            "phomt_train_lines_matching_fleurs_test": len(exclude),
                            "note": "so trùng tuyệt đối sau chuẩn hoá; chưa kiểm câu gần giống"}

    # 6) Ghi kết quả
    id_rows = []
    for split, rows in rows_by_split.items():
        kept = [r for r in rows if r["drop"] is None]
        st = stats[split]
        st.update({
            "recordings_kept": len(kept),
            "dropped": dict(Counter(r["drop"] for r in rows if r["drop"])),
            "sentences_kept": len({r["sent_id"] for r in kept}),
            "hours_kept": round(sum(r["duration_s"] for r in kept) / 3600, 3),
            "missing_en": sum(r["en"] is None for r in kept),
            "missing_audio": sum(r["audio_exists"] is False for r in kept),
            "gender": dict(Counter(r["gender"] for r in kept)),
        })
        with open(man_dir / f"{split}.jsonl", "w", encoding="utf-8") as f:
            for r in kept:
                f.write(json.dumps({k: r[k] for k in ("split", "sent_id", "file_name", "audio_path", "num_samples",
                                                     "duration_s", "gender", "raw", "transcription", "en")},
                                   ensure_ascii=False) + "\n")
        id_rows += [{"split": split, "sent_id": r["sent_id"], "file_name": r["file_name"], "num_samples": r["num_samples"],
                     "gender": r["gender"], "status": r["drop"] or "kept"} for r in rows]
    summary["splits"] = stats

    with open(args.report_dir / "fleurs_split_ids.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(id_rows[0]) if id_rows else ["split"])
        w.writeheader()
        w.writerows(id_rows)
    (args.report_dir / "prepare_fleurs_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nFLEURS revision: {summary['fleurs_revision']}")
    print(f"{'tập':<6}{'TSV':>7}{'giữ':>7}{'câu':>6}{'giờ':>8}  bị bỏ")
    for split in SPLITS:
        st = stats[split]
        print(f"{split:<6}{st['tsv_rows']:>7}{st['recordings_kept']:>7}{st['sentences_kept']:>6}{st['hours_kept']:>8}  {st['dropped'] or '-'}")
    print(f"ID câu nằm ở nhiều tập: {len(conflict_ids)}")
    if isinstance(summary["phomt"], dict):
        p = summary["phomt"]
        print(f"FLEURS test trùng PhoMT test: {p['fleurs_test_sentences_in_phomt_test']} câu; "
              f"PhoMT train trùng FLEURS test: {p['phomt_train_lines_matching_fleurs_test']} dòng (ghi ở phomt_train_exclude_idx.txt)")
    print(f"\nManifest (có chữ, không commit): {man_dir}/")
    print(f"Báo cáo (commit được): {args.report_dir}/")


if __name__ == "__main__":
    main()
