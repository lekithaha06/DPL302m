#!/usr/bin/env python3
"""VIỆC 2 (phần làm sạch) – Task 2, TV4 Uyên viết, Kiệt chạy.

NHIỆM VỤ: làm sạch FLEURS, VIVOS (và PhoMT train cho V2) theo quy trình
    thiếu dữ liệu -> trùng lặp -> hỏng/nhiễu -> đổi audio về 16 kHz mono -> chuẩn hoá chữ
và ĐẾM SỐ MẪU BỊ LOẠI Ở TỪNG BƯỚC, tự vẽ flowchart có số cho slide 4 / mục 1.2.
Chạy SAU viec1_tai_3_bo_du_lieu.py và viec2_ghep_chia_fleurs_chong_trung.py (bước ghép + chống leakage).

Nguyên tắc (giữ như Task 1):
- Không bỏ mẫu khó khỏi tập test. Ở test chỉ bỏ mẫu KHÔNG THỂ chấm (thiếu audio/nhãn, audio hỏng);
  mẫu bất thường (quá ngắn, im lặng, dài > 30 s, tốc độ nói lạ) chỉ GẮN CỜ để phân tích riêng.
- Ở train/dev: bỏ mẫu thiếu, trùng, hỏng, quá ngắn, im lặng; mẫu bất thường còn lại chỉ gắn cờ.
- Không sửa nhãn gốc. Chữ chuẩn hoá được lưu thành cột mới, nhãn gốc giữ nguyên.

Chạy:
    pip install numpy soundfile scipy
    python scripts/data/viec2_lam_sach_du_lieu.py
Tuỳ chọn: --bo_vivos, --bo_phomt, --limit N (chạy thử N mẫu mỗi tập).

Đầu ra trong --report_dir (không có câu chữ, commit được):
    lam_sach_dem_tung_buoc.csv   bảng số mẫu trước / bị loại / sau ở mỗi bước, theo bộ dữ liệu và tập
    lam_sach_flowchart.md        flowchart (Mermaid) có số, dán vào slide 4
    lam_sach_mau_bi_loai.csv     ID mẫu bị loại + lý do
    lam_sach_mau_gan_co.csv      ID mẫu giữ lại nhưng bất thường + lý do
    lam_sach_tom_tat.json        toàn bộ số đếm, ngưỡng đã dùng, phiên bản thư viện
Đầu ra trong --data_dir/clean (có câu chữ / audio, KHÔNG commit):
    {fleurs,vivos}_{split}.jsonl  danh sách mẫu sạch: audio_16k, text_vi (gốc), text_vi_norm, text_en
    audio_16k/...                 chỉ chứa file phải đổi sample rate / số kênh / định dạng; file đã chuẩn thì trỏ về file gốc
    phomt/train.vi, train.en      PhoMT train đã bỏ dòng rỗng, cặp trùng, dòng trùng FLEURS test (dùng cho V2)
"""
import argparse
import csv
import datetime
import gzip
import hashlib
import json
import platform
import statistics
import tarfile
from collections import Counter, defaultdict
from math import gcd
from pathlib import Path

from ham_dung_chung import ensure_phomt, lib_versions, norm

TARGET_SR = 16000
PRIORITY = {"test": 0, "dev": 1, "train": 2}  # khi trùng audio giữa các tập: giữ ở test, bỏ ở tập dạy
STEPS = [("B1_thieu", "Thiếu audio / nhãn"), ("B2_trung", "Trùng lặp"), ("B3_hong_nhieu", "Audio hỏng / nhiễu"),
         ("B4_16khz", "Đổi về 16 kHz mono"), ("B5_chuan_hoa_chu", "Chuẩn hoá chữ")]


# ---------------------------------------------------------------- đọc dữ liệu

def load_fleurs(args):
    man = args.data_dir / "fleurs" / "manifest"
    if not man.exists():
        raise SystemExit(f"Chưa có {man}. Chạy viec2_ghep_chia_fleurs_chong_trung.py trước.")
    recs = []
    for split in ("train", "dev", "test"):
        p = man / f"{split}.jsonl"
        if not p.exists():
            continue
        with open(p, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f]
        for r in rows[:args.limit or None]:
            recs.append({"dataset": "fleurs", "split": split, "uid": Path(r["file_name"]).stem, "group": r["sent_id"],
                         "audio": r["audio_path"], "text_vi": r["raw"] or "", "text_en": r["en"],
                         "num_samples": r["num_samples"], "speaker": None, "gender": r["gender"]})
    return recs


def load_vivos(args):
    hf = args.data_dir / "vivos" / "hf" / "data"
    audio_root = args.data_dir / "vivos" / "audio"
    tar_path = hf / "vivos.tar.gz"
    if not (audio_root / "vivos").exists():
        if not tar_path.exists():
            raise SystemExit(f"Chưa có {tar_path}. Chạy viec1_tai_3_bo_du_lieu.py --audio_stats trước, hoặc thêm --bo_vivos.")
        print(f"[VIVOS] giải nén {tar_path} -> {audio_root} ...")
        with tarfile.open(tar_path, "r:gz") as t:
            try:
                t.extractall(audio_root, filter="data")
            except TypeError:  # Python cũ chưa có tham số filter
                t.extractall(audio_root)
    genders = {}
    for g in audio_root.glob("vivos/*/genders.txt"):
        for line in g.read_text(encoding="utf-8").splitlines():
            if len(line.split()) == 2:
                genders[line.split()[0]] = line.split()[1]
    recs = []
    for split in ("train", "test"):
        with gzip.open(hf / f"prompts-{split}.txt.gz", "rt", encoding="utf-8") as f:
            rows = [line.rstrip("\n").split(" ", 1) for line in f if line.strip()]
        for x in rows[:args.limit or None]:
            uid, spk = x[0], x[0].split("_")[0]
            recs.append({"dataset": "vivos", "split": split, "uid": uid, "group": uid,
                         "audio": str(audio_root / "vivos" / split / "waves" / spk / f"{uid}.wav"),
                         "text_vi": x[1] if len(x) > 1 else "", "text_en": None, "num_samples": None,
                         "speaker": spk, "gender": genders.get(spk)})
    return recs


# ---------------------------------------------------------------- các bước

def mark(r, step, reason, drop):
    """drop=True: bỏ mẫu; drop=False: giữ nhưng gắn cờ."""
    if drop:
        r["drop_step"], r["drop_reason"] = step, reason
    else:
        r["flags"].append(reason)


def is_test(r):
    return r["split"] == "test"


def b1_thieu(recs):
    for r in recs:
        if not r["audio"]:
            mark(r, "B1_thieu", "chua_co_audio (chạy viec2_ghep... với --with_test_audio)", True)
        elif not Path(r["audio"]).exists():
            mark(r, "B1_thieu", "thieu_file_audio", True)
        elif not r["text_vi"].strip():
            mark(r, "B1_thieu", "nhan_vi_rong", True)
        elif r["dataset"] == "fleurs" and not (r["text_en"] or "").strip():
            mark(r, "B1_thieu", "thieu_cau_en", True)


def b2_trung(recs):
    alive = [r for r in recs if not r.get("drop_step")]
    by_uid = defaultdict(list)
    for r in alive:
        by_uid[(r["dataset"], r["split"], r["uid"])].append(r)
    for rs in by_uid.values():
        for r in rs[1:]:
            mark(r, "B2_trung", "trung_id_mau", True)
    # Trùng nội dung audio (cùng mã băm file) trong cùng bộ dữ liệu, kể cả khác tập -> leakage nếu một bản ở test
    by_hash = defaultdict(list)
    for r in alive:
        if not r.get("drop_step"):
            with open(r["audio"], "rb") as f:
                r["md5"] = hashlib.md5(f.read()).hexdigest()
            by_hash[(r["dataset"], r["md5"])].append(r)
    n_groups = 0
    for rs in by_hash.values():
        if len(rs) > 1:
            n_groups += 1
            rs.sort(key=lambda r: PRIORITY[r["split"]])
            for r in rs[1:]:
                mark(r, "B2_trung", f"trung_audio_voi_{rs[0]['split']}_{rs[0]['uid']}", True)
    # Lưu ý: một câu FLEURS có nhiều bản thu (khác người đọc) là THIẾT KẾ của dataset, không phải trùng lặp,
    # nên không bỏ ở đây; phần này xử lý ở việc 4 (mất cân bằng).
    return n_groups


def b3_hong_nhieu(recs, args):
    import numpy as np
    import soundfile as sf
    for r in recs:
        if r.get("drop_step"):
            continue
        try:
            x, sr = sf.read(r["audio"], dtype="float32", always_2d=True)
        except Exception as e:
            mark(r, "B3_hong_nhieu", f"audio_hong ({type(e).__name__})", True)
            continue
        r["sr_goc"], r["kenh_goc"], r["frames"] = sr, x.shape[1], x.shape[0]
        r["subtype_goc"] = sf.info(r["audio"]).subtype
        dur = x.shape[0] / sr if sr else 0
        r["dur"] = dur
        if dur == 0:
            mark(r, "B3_hong_nhieu", "audio_rong_0s", True)
            continue
        rms = float(np.sqrt(np.mean(np.square(x.mean(axis=1), dtype=np.float64))))
        r["dbfs"] = 20 * np.log10(rms) if rms > 0 else -120.0
        peak = float(np.max(np.abs(x)))
        if dur < args.min_dur:
            mark(r, "B3_hong_nhieu", f"qua_ngan_<{args.min_dur}s", not is_test(r))
        elif r["dbfs"] < args.silence_dbfs:
            mark(r, "B3_hong_nhieu", f"im_lang_<{args.silence_dbfs}dBFS", not is_test(r))
        # Các cờ dưới đây không bỏ mẫu, chỉ để phân tích riêng
        if dur > args.max_dur_flag:
            r["flags"].append(f"dai_>{args.max_dur_flag}s")
        if peak >= 0.999:
            r["flags"].append("bi_cat_dinh_clipping")
        if r["num_samples"] and r["sr_goc"] == TARGET_SR and abs(r["frames"] - r["num_samples"]) > args.mismatch_tol * r["num_samples"]:
            r["flags"].append("so_mau_khac_num_samples_tsv")
    # Tốc độ nói (ký tự / giây) lệch xa bất thường -> nghi nhãn không khớp audio. Ngưỡng theo IQR, tính riêng mỗi bộ.
    by_ds = defaultdict(list)
    for r in recs:
        if not r.get("drop_step") and r.get("dur"):
            r["cps"] = len(norm(r["text_vi"]).replace(" ", "")) / r["dur"]
            by_ds[r["dataset"]].append(r)
    bounds = {}
    for ds, rs in by_ds.items():
        if len(rs) >= 4:
            q1, _, q3 = statistics.quantiles([r["cps"] for r in rs], n=4)
            lo, hi = q1 - 3 * (q3 - q1), q3 + 3 * (q3 - q1)
            bounds[ds] = (round(lo, 2), round(hi, 2))
            for r in rs:
                if not lo <= r["cps"] <= hi:
                    r["flags"].append("toc_do_noi_bat_thuong")
    return bounds


def b4_16khz(recs, args):
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    out_root = args.data_dir / "clean" / "audio_16k"
    for r in recs:
        if r.get("drop_step"):
            continue
        ok = r["sr_goc"] == TARGET_SR and r["kenh_goc"] == 1 and r["subtype_goc"] == "PCM_16"
        if ok:
            r["audio_16k"], r["doi"] = r["audio"], []
            continue
        x, sr = sf.read(r["audio"], dtype="float32", always_2d=True)
        doi = []
        if x.shape[1] > 1:
            x, doi = x.mean(axis=1, keepdims=True), doi + [f"{r['kenh_goc']}kenh->mono"]
        if sr != TARGET_SR:
            g = gcd(sr, TARGET_SR)
            x = resample_poly(x, TARGET_SR // g, sr // g, axis=0).astype("float32")
            doi.append(f"{sr}Hz->16kHz")
        if r["subtype_goc"] != "PCM_16":
            doi.append(f"{r['subtype_goc']}->PCM_16")
        out = out_root / r["dataset"] / r["split"] / f"{r['uid']}.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        sf.write(out, np.clip(x, -1, 1), TARGET_SR, subtype="PCM_16")
        r["audio_16k"], r["doi"] = str(out), doi


def b5_chuan_hoa_chu(recs):
    for r in recs:
        if r.get("drop_step"):
            continue
        r["text_vi_norm"] = norm(r["text_vi"])
        if not r["text_vi_norm"]:
            mark(r, "B5_chuan_hoa_chu", "nhan_rong_sau_chuan_hoa", True)
            continue
        r["chu_doi"] = r["text_vi_norm"] != " ".join(r["text_vi"].split())


# ---------------------------------------------------------------- PhoMT train (cho V2)

def clean_phomt(args):
    files = ensure_phomt(args.phomt_dir, splits=("train",))
    excl_path = args.report_dir / "phomt_train_exclude_idx.txt"
    exclude = set()
    if excl_path.exists():
        exclude = {int(x) for x in excl_path.read_text().split()}
    else:
        print(f"[PhoMT] không thấy {excl_path}; chưa bỏ được dòng trùng FLEURS test (chạy viec2_ghep... trước).")
    out = args.data_dir / "clean" / "phomt"
    out.mkdir(parents=True, exist_ok=True)
    c = Counter()
    seen = set()
    with open(files[("train", "vi")], encoding="utf-8") as fv, open(files[("train", "en")], encoding="utf-8") as fe, \
            open(out / "train.vi", "w", encoding="utf-8") as ov, open(out / "train.en", "w", encoding="utf-8") as oe:
        for i, (v, e) in enumerate(zip(fv, fe)):
            c["truoc"] += 1
            v, e = v.strip(), e.strip()
            if not v or not e:
                c["B1_dong_rong"] += 1
            elif hash((v, e)) in seen:
                c["B2_cap_trung"] += 1
            elif i in exclude:
                c["B6_trung_fleurs_test"] += 1
            else:
                seen.add(hash((v, e)))
                ov.write(v + "\n")
                oe.write(e + "\n")
                c["sau"] += 1
    c["exclude_list_found"] = excl_path.exists()
    return dict(c)


# ---------------------------------------------------------------- báo cáo

def step_table(recs, ghep_summary):
    """Bảng trước / bị loại / sau cho từng (bộ dữ liệu, tập, bước)."""
    rows = []
    groups = defaultdict(list)
    for r in recs:
        groups[(r["dataset"], r["split"])].append(r)
    for (ds, split), rs in sorted(groups.items(), key=lambda k: (k[0][0], -PRIORITY[k[0][1]])):  # train, dev, test
        if ds == "fleurs" and ghep_summary:
            st = ghep_summary["splits"].get(split, {})
            n_tsv = st.get("tsv_rows")
            if n_tsv is not None:
                n_after = n_tsv - sum(st.get("dropped", {}).values())
                rows.append({"dataset": ds, "split": split, "buoc": "B0_ghep_chong_leakage",
                             "ten_buoc": "Ghép vi-en + chống leakage (viec2_ghep)", "truoc": n_tsv,
                             "bi_loai": n_tsv - n_after, "sau": n_after,
                             "chi_tiet": json.dumps(st.get("dropped", {}), ensure_ascii=False)})
        n = len(rs)
        for step, name in STEPS:
            dropped = [r for r in rs if r.get("drop_step") == step]
            detail = Counter(r["drop_reason"] for r in dropped)
            if step == "B4_16khz":
                detail = Counter(d for r in rs if not r.get("drop_step") for d in r.get("doi", []))
                detail["so_file_doi"] = sum(bool(r.get("doi")) for r in rs if not r.get("drop_step"))
            elif step == "B5_chuan_hoa_chu":
                detail["so_cau_doi_chu"] = sum(bool(r.get("chu_doi")) for r in rs if not r.get("drop_step"))
            rows.append({"dataset": ds, "split": split, "buoc": step, "ten_buoc": name, "truoc": n,
                         "bi_loai": len(dropped), "sau": n - len(dropped),
                         "chi_tiet": json.dumps(dict(detail), ensure_ascii=False)})
            n -= len(dropped)
        flags = Counter(f for r in rs if not r.get("drop_step") for f in r["flags"])
        rows.append({"dataset": ds, "split": split, "buoc": "KET_QUA", "ten_buoc": "Sạch (giữ lại)", "truoc": n,
                     "bi_loai": 0, "sau": n, "chi_tiet": json.dumps({"gan_co": dict(flags)}, ensure_ascii=False)})
    return rows


def mermaid(rows, phomt):
    """Flowchart cho slide 4: mỗi bộ dữ liệu một nhánh, số = tổng các tập."""
    lines = ["```mermaid", "flowchart LR"]
    for ds in sorted({r["dataset"] for r in rows}):
        rs = [r for r in rows if r["dataset"] == ds]
        order = [s for s in ["B0_ghep_chong_leakage"] + [s for s, _ in STEPS] if any(r["buoc"] == s for r in rs)]
        first = sum(r["truoc"] for r in rs if r["buoc"] == order[0])
        lines.append(f'  {ds}0["{ds.upper()} gốc<br/>{first} mẫu"]')
        prev = f"{ds}0"
        for k, step in enumerate(order, 1):
            name = next(r["ten_buoc"] for r in rs if r["buoc"] == step)
            lost = sum(r["bi_loai"] for r in rs if r["buoc"] == step)
            left = sum(r["sau"] for r in rs if r["buoc"] == step)
            node = f"{ds}{k}"
            label = f"-{lost} → còn {left}"
            if step in ("B4_16khz", "B5_chuan_hoa_chu"):  # 2 bước này chủ yếu là biến đổi, ghi thêm số mẫu được đổi
                key, unit = ("so_cau_doi_chu", "câu") if step == "B5_chuan_hoa_chu" else ("so_file_doi", "file")
                changed = sum(json.loads(r["chi_tiet"]).get(key, 0) for r in rs if r["buoc"] == step)
                label = f"đổi {changed} {unit}, {label}"
            lines.append(f'  {prev} --> {node}["{name}<br/>{label}"]')
            prev = node
        per_split = ", ".join(f'{r["split"]} {r["sau"]}' for r in rs if r["buoc"] == "KET_QUA")
        lines.append(f'  {prev} --> {ds}X(["{ds.upper()} sạch: {per_split}"])')
    if phomt:
        lines.append(f'  phomt0["PHOMT train gốc<br/>{phomt["truoc"]} cặp"] --> phomt1["Dòng rỗng -{phomt.get("B1_dong_rong", 0)}<br/>'
                     f'Cặp trùng -{phomt.get("B2_cap_trung", 0)}<br/>Trùng FLEURS test -{phomt.get("B6_trung_fleurs_test", 0)}"]'
                     f' --> phomtX(["PhoMT train sạch: {phomt["sau"]} cặp"])')
    lines.append("```")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data_dir", type=Path, default=Path("data"))
    ap.add_argument("--report_dir", type=Path, default=Path("reports/task2/data"))
    ap.add_argument("--phomt_dir", type=Path, default=None, help="mặc định <data_dir>/phomt")
    ap.add_argument("--bo_vivos", action="store_true", help="không làm sạch VIVOS")
    ap.add_argument("--bo_phomt", action="store_true", help="không làm sạch PhoMT train")
    ap.add_argument("--limit", type=int, default=0, help="chạy thử: N mẫu đầu mỗi tập")
    ap.add_argument("--min_dur", type=float, default=0.3, help="giây; ngắn hơn = quá ngắn")
    ap.add_argument("--silence_dbfs", type=float, default=-60.0, help="RMS thấp hơn = im lặng")
    ap.add_argument("--max_dur_flag", type=float, default=30.0, help="giây; dài hơn thì gắn cờ (Whisper cắt 30 s)")
    ap.add_argument("--mismatch_tol", type=float, default=0.01, help="lệch tối đa giữa số mẫu audio và cột num_samples")
    args = ap.parse_args()
    args.phomt_dir = args.phomt_dir or args.data_dir / "phomt"
    args.report_dir.mkdir(parents=True, exist_ok=True)
    clean_dir = args.data_dir / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)

    print("[Đọc] FLEURS ...")
    recs = load_fleurs(args)
    if not args.bo_vivos:
        print("[Đọc] VIVOS ...")
        recs += load_vivos(args)
    for r in recs:
        r["flags"] = []
    print(f"[B1] kiểm thiếu audio / nhãn trên {len(recs)} mẫu ...")
    b1_thieu(recs)
    print("[B2] kiểm trùng ID và trùng nội dung audio ...")
    n_dup_groups = b2_trung(recs)
    print("[B3] kiểm audio hỏng / quá ngắn / im lặng / bất thường ...")
    cps_bounds = b3_hong_nhieu(recs, args)
    print("[B4] đổi về 16 kHz mono PCM 16-bit ...")
    b4_16khz(recs, args)
    print("[B5] chuẩn hoá chữ ...")
    b5_chuan_hoa_chu(recs)
    phomt = None
    if not args.bo_phomt:
        print("[PhoMT] làm sạch train cho V2 ...")
        phomt = clean_phomt(args)

    ghep_path = args.report_dir / "prepare_fleurs_summary.json"
    ghep = json.loads(ghep_path.read_text(encoding="utf-8")) if ghep_path.exists() else None
    if ghep and args.limit:
        ghep = None  # chạy thử: số của bước ghép không khớp số mẫu đã cắt
    rows = step_table(recs, ghep)

    # Chống leakage cho VIVOS: split gốc chia theo người nói, kiểm lại không người nói nào ở cả train và test
    vivos_spk = {sp: {r["speaker"] for r in recs if r["dataset"] == "vivos" and r["split"] == sp} for sp in ("train", "test")}
    vivos_leak = {"nguoi_noi_o_ca_train_va_test": len(vivos_spk["train"] & vivos_spk["test"]),
                  "cau_test_trung_chu_train": len({norm(r["text_vi"]) for r in recs if r["dataset"] == "vivos" and r["split"] == "test"}
                                                  & {norm(r["text_vi"]) for r in recs if r["dataset"] == "vivos" and r["split"] == "train"})}

    # Ghi danh sách mẫu sạch (có chữ -> data/, không commit)
    keep_fields = ["dataset", "split", "uid", "group", "speaker", "gender", "audio_16k", "dur", "text_vi", "text_vi_norm",
                   "text_en", "flags"]
    by = defaultdict(list)
    for r in recs:
        if not r.get("drop_step"):
            by[(r["dataset"], r["split"])].append({k: (round(r[k], 3) if k == "dur" else r.get(k)) for k in keep_fields})
    for (ds, split), rs in by.items():
        with open(clean_dir / f"{ds}_{split}.jsonl", "w", encoding="utf-8") as f:
            f.writelines(json.dumps(x, ensure_ascii=False) + "\n" for x in rs)

    # Báo cáo (không có chữ -> commit được)
    fields = ["dataset", "split", "buoc", "ten_buoc", "truoc", "bi_loai", "sau", "chi_tiet"]
    with open(args.report_dir / "lam_sach_dem_tung_buoc.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    with open(args.report_dir / "lam_sach_mau_bi_loai.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["dataset", "split", "uid", "buoc", "ly_do"])
        w.writerows([r["dataset"], r["split"], r["uid"], r["drop_step"], r["drop_reason"]] for r in recs if r.get("drop_step"))
    with open(args.report_dir / "lam_sach_mau_gan_co.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["dataset", "split", "uid", "co", "dur_s", "dbfs", "ky_tu_moi_giay"])
        w.writerows([r["dataset"], r["split"], r["uid"], ";".join(r["flags"]), round(r.get("dur", 0), 2),
                     round(r.get("dbfs", 0), 1), round(r.get("cps", 0), 2)] for r in recs if not r.get("drop_step") and r["flags"])
    flow = mermaid(rows, phomt)
    (args.report_dir / "lam_sach_flowchart.md").write_text(
        "# Flowchart làm sạch (slide 4)\n\nDán khối dưới vào https://mermaid.live để xuất ảnh PNG/SVG.\n\n" + flow + "\n",
        encoding="utf-8")
    summary = {"script": "viec2_lam_sach_du_lieu.py",
               "time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
               "args": {k: str(v) for k, v in vars(args).items()}, "versions": lib_versions(), "platform": platform.platform(),
               "nhom_audio_trung_noi_dung": n_dup_groups, "vivos_kiem_leakage": None if args.bo_vivos else vivos_leak, "nguong_toc_do_noi_ky_tu_moi_giay": cps_bounds,
               "phomt_train": phomt, "bang": rows}
    for mod in ("numpy", "soundfile", "scipy"):
        summary["versions"][mod] = __import__(mod).__version__
    (args.report_dir / "lam_sach_tom_tat.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'bộ':<7}{'tập':<6}{'bước':<24}{'trước':>8}{'bỏ':>6}{'sau':>8}  chi tiết")
    for r in rows:
        print(f"{r['dataset']:<7}{r['split']:<6}{r['buoc']:<24}{r['truoc']:>8}{r['bi_loai']:>6}{r['sau']:>8}  {r['chi_tiet']}")
    if phomt:
        print(f"PhoMT train: {phomt}")
    if not args.bo_vivos:
        print(f"VIVOS kiểm leakage: {vivos_leak}")
    print(f"\nBáo cáo (commit được): {args.report_dir}/lam_sach_*")
    print(f"Dữ liệu sạch (không commit): {clean_dir}/")


if __name__ == "__main__":
    main()
