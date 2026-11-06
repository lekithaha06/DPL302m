#!/usr/bin/env python3
"""VIỆC 1 – Task 2, TV4 Uyên viết, Kiệt chạy.

NHIỆM VỤ: TẢI 3 BỘ DỮ LIỆU (VIVOS, FLEURS, PhoMT) về <data_dir>, rồi kiểm chứng thông tin (nguồn, giấy phép, cấu trúc, số mẫu, train/dev/test,
nhãn có sẵn) và lập bảng nguồn Online/Offline cho slide 3 / mục 1.1 của báo cáo. Chạy ĐẦU TIÊN.

Script tự đếm từ dữ liệu tải mới, không chép số từ paper:
- nguồn (URL, mã commit của repo), giấy phép, trạng thái gated;
- cấu trúc file, định dạng, dung lượng;
- số mẫu theo train/dev/test, số người nói, số câu gốc, giới tính, thời lượng;
- nhãn có sẵn (trường dữ liệu, chữ hoa/dấu câu trong nhãn);
- so với số nhóm đã ghi ở Task 1 (khớp / lệch).

Chạy nhanh (tải ~360 MB, chủ yếu là PhoMT.zip; thời lượng FLEURS lấy từ cột num_samples):
    python scripts/data/viec1_tai_3_bo_du_lieu.py
Chạy đầy đủ, mở cả audio để kiểm định dạng wav, sample rate, thời lượng VIVOS (tải thêm ~3,8 GB):
    python scripts/data/viec1_tai_3_bo_du_lieu.py --audio_stats
Chạy thử không cần đăng nhập Hugging Face:
    python scripts/data/viec1_tai_3_bo_du_lieu.py --skip_phomt

Đầu ra trong --report_dir (không chứa câu chữ, commit được):
    nguon_du_lieu.md / .csv   bảng nguồn cho slide 3 và mục 1.1 của báo cáo
    kiem_chung.md             số Task 1 so với số đếm thật
    dataset_facts.json        toàn bộ số đếm, mã commit, phiên bản thư viện, máy chạy
Đầu ra trong --data_dir (có câu chữ, KHÔNG commit): vi_du_mau.md (ví dụ mẫu để chọn đưa lên slide)
"""
import argparse
import csv
import datetime
import gzip
import json
import platform
import re
import statistics
import struct
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

from ham_dung_chung import (FLEURS_REPO, PHOMT_REPO, VIVOS_REPO, count_lines, ensure_phomt, fetch, lib_versions,
                      read_fleurs_tsv, repo_meta)

SPLITS = ["train", "dev", "test"]
FLEURS_SR = 16000  # theo dataset card; --audio_stats kiểm lại trên file wav thật

# Số nhóm đã ghi trong proposal Task 1. Script đếm lại và đánh dấu khớp / lệch.
EXPECTED = {
    "VIVOS train: số câu": 11660, "VIVOS train: số người nói": 46,
    "VIVOS test: số câu": 760, "VIVOS test: số người nói": 19,
    "VIVOS train: số giờ (14:55)": 14.92, "VIVOS test: số phút": 44.76,
    "FLEURS vi_vn test: số bản thu": 857, "FLEURS vi_vn test: số câu gốc": 347,
    "FLEURS vi_vn test: số giờ": 3.00, "FLEURS vi_vn test: thời lượng TB (s)": 12.62,
    "FLEURS vi_vn test: dài nhất (s)": 38.10, "FLEURS vi_vn test: số bản thu nhãn MALE": 857,
    "FLEURS vi_vn test: số câu có câu Anh": 347,
    "PhoMT train: số cặp": 2977999, "PhoMT dev: số cặp": 18719, "PhoMT test: số cặp": 19151,
}
OFFLINE_REASON = ("Nhóm không tự thu âm/khảo sát. Dùng dataset công khai đã có nhãn chuẩn, giữ split gốc để so được "
                  "với paper; tự thu cần thời gian gán nhãn và kiểm định mà Task 2 không đủ. Hạn chế: chưa có giọng nữ "
                  "(theo nhãn FLEURS) và micro điện thoại.")


# ---------------------------------------------------------------- tiện ích

def wav_info(b):
    """Đọc header RIFF/WAVE (PCM hoặc float). Trả về None nếu file hỏng / không phải wav."""
    if len(b) < 12 or b[:4] != b"RIFF" or b[8:12] != b"WAVE":
        return None
    pos, fmt, data_size = 12, None, None
    while pos + 8 <= len(b):
        cid, size = b[pos:pos + 4], int.from_bytes(b[pos + 4:pos + 8], "little")
        if cid == b"fmt " and size >= 16:
            fmt = struct.unpack("<HHIIHH", b[pos + 8:pos + 24])
        elif cid == b"data":
            data_size = min(size, len(b) - pos - 8)
            break
        pos += 8 + size + (size & 1)
    if fmt is None or data_size is None or not fmt[4] or not fmt[2]:
        return None
    audio_format, channels, sr, _, block_align, bits = fmt
    frames = data_size // block_align
    return {"format": {1: "PCM", 3: "float", 0xFFFE: "extensible"}.get(audio_format, str(audio_format)),
            "channels": channels, "sr": sr, "bits": bits, "frames": frames, "dur": frames / sr}


def dur_stats(durs):
    if not durs:
        return {}
    return {"n": len(durs), "hours": round(sum(durs) / 3600, 3), "mean_s": round(statistics.mean(durs), 2),
            "median_s": round(statistics.median(durs), 2), "min_s": round(min(durs), 2), "max_s": round(max(durs), 2)}


def text_flags(texts):
    """Mô tả nhãn có sẵn: bao nhiêu % có chữ hoa, có dấu câu, rỗng."""
    n = len(texts) or 1
    return {"pct_has_upper": round(100 * sum(any(c.isupper() for c in t) for t in texts) / n, 2),
            "pct_all_upper": round(100 * sum(t == t.upper() and any(c.isalpha() for c in t) for t in texts) / n, 2),
            "pct_has_punct": round(100 * sum(bool(re.search(r"[^\w\s]", t)) for t in texts) / n, 2),
            "n_empty": sum(not t.strip() for t in texts),
            "mean_words": round(statistics.mean(len(t.split()) for t in texts), 2) if texts else 0}


def iter_tar(path):
    """Duyệt file .tar.gz một lượt. Trả về (tên, bytes): đọc bytes cho .wav và .txt, file khác trả None."""
    with tarfile.open(path, mode="r:gz") as tar:
        for m in tar:
            if m.isfile():
                yield m.name, (tar.extractfile(m).read() if m.name.endswith((".wav", ".txt")) else None)


def summarize_wavs(infos):
    ok = [i for i in infos if i]
    return {"n_files": len(infos), "n_unreadable": len(infos) - len(ok),
            "sample_rates": dict(Counter(i["sr"] for i in ok)), "channels": dict(Counter(i["channels"] for i in ok)),
            "formats": dict(Counter(f'{i["format"]} {i["bits"]}-bit' for i in ok))}


def mb(n):
    return round(n / 2**20, 1) if n else None


def fmt_int(n):
    return f"{n:,}".replace(",", ".") if isinstance(n, int) else str(n)


# ---------------------------------------------------------------- VIVOS

def inspect_vivos(args, examples):
    local = args.data_dir / "vivos" / "hf"
    meta = repo_meta(VIVOS_REPO, args.vivos_revision)
    rev = meta.get("sha", args.vivos_revision)
    out = {"meta": meta, "fields": ["speaker_id", "path", "audio (wav)", "sentence"],
           "note_loading": "repo dùng loading script vivos.py; datasets>=4 không chạy script nên đọc thẳng file gốc"}
    for split in ("train", "test"):
        p = fetch(VIVOS_REPO, f"data/prompts-{split}.txt.gz", local, rev)
        with gzip.open(p, "rt", encoding="utf-8") as f:
            pairs = [line.rstrip("\n").split(" ", 1) for line in f if line.strip()]
        ids = [x[0] for x in pairs]
        sents = [x[1] if len(x) > 1 else "" for x in pairs]
        spk = Counter(i.split("_")[0] for i in ids)
        out[split] = {"utterances": len(ids), "speakers": len(spk), "duplicate_ids": len(ids) - len(set(ids)),
                      "unique_sentences": len(set(sents)), "utts_per_speaker_min": min(spk.values()),
                      "utts_per_speaker_max": max(spk.values()), "label": text_flags(sents)}
        examples.append(("VIVOS", split, pairs[:2]))
    if args.audio_stats:
        tar_path = fetch(VIVOS_REPO, "data/vivos.tar.gz", local, rev)
        infos, durs, genders, other = defaultdict(list), defaultdict(list), {}, []
        for name, b in iter_tar(tar_path):
            parts = name.split("/")
            split = parts[1] if len(parts) > 1 else "?"
            if name.endswith(".wav"):
                i = wav_info(b)
                infos[split].append(i)
                if i:
                    durs[split].append(i["dur"])
            else:
                other.append(name)
                if name.endswith("genders.txt"):  # mỗi dòng: <speaker_id> <m/f>
                    txt = b.decode("utf-8")
                    genders[split] = dict(Counter(line.split()[1] for line in txt.splitlines() if len(line.split()) == 2))
        out["archive_non_wav_files"] = other
        for split in ("train", "test"):
            out[split]["audio"] = summarize_wavs(infos[split])
            out[split]["duration"] = dur_stats(durs[split])
            out[split]["speaker_gender"] = genders.get(split)
    return out


# ---------------------------------------------------------------- FLEURS

def inspect_fleurs(args, examples):
    local = args.data_dir / "fleurs" / "hf"  # chung chỗ với viec2_ghep_chia_fleurs_chong_trung.py
    meta = repo_meta(FLEURS_REPO, args.fleurs_revision, path_in_repo="data/vi_vn")
    meta_en = repo_meta(FLEURS_REPO, args.fleurs_revision, path_in_repo="data/en_us")
    meta["files"] = {**meta.get("files", {}), **{k: v for k, v in meta_en.get("files", {}).items() if k.endswith(".tsv")}}
    rev = meta.get("sha", args.fleurs_revision)
    out = {"meta": meta, "fields": ["id (ID câu FLoRes)", "file_name", "raw_transcription", "transcription",
                                    "phonemes (trống)", "num_samples", "gender"],
           "note_speaker": "TSV không có trường người nói; dataset card: người nói train khác dev/test"}
    en_ids, en_by_id = set(), {}
    for split in SPLITS:
        rows, bad = read_fleurs_tsv(fetch(FLEURS_REPO, f"data/en_us/{split}.tsv", local, rev))
        en_ids |= {r["sent_id"] for r in rows}
        en_by_id.update({r["sent_id"]: r["raw"] for r in rows})
        out.setdefault("en_us", {})[split] = {"recordings": len(rows), "sentences": len({r["sent_id"] for r in rows}),
                                             "bad_tsv_lines": bad}
    vi_ids_by_split = {}
    for split in SPLITS:
        rows, bad = read_fleurs_tsv(fetch(FLEURS_REPO, f"data/vi_vn/{split}.tsv", local, rev))
        ids = [r["sent_id"] for r in rows]
        per_sent = Counter(ids)
        vi_ids_by_split[split] = set(ids)
        st = {"recordings": len(rows), "sentences": len(per_sent), "bad_tsv_lines": bad,
              "duplicate_file_names": len(rows) - len({r["file_name"] for r in rows}),
              "recordings_per_sentence": dict(sorted(Counter(per_sent.values()).items())),
              "gender": dict(Counter(r["gender"] for r in rows)),
              "duration_from_num_samples": dur_stats([r["num_samples"] / FLEURS_SR for r in rows]),
              "n_over_30s": sum(r["num_samples"] > 30 * FLEURS_SR for r in rows),
              "sentences_with_en": len(set(ids) & en_ids),
              "label_raw_transcription": text_flags([r["raw"] for r in rows]),
              "label_transcription": text_flags([r["transcription"] for r in rows])}
        if args.audio_stats:
            tsv_ns = {r["file_name"]: r["num_samples"] for r in rows}
            infos, seen, mismatch = [], set(), 0
            for name, b in iter_tar(fetch(FLEURS_REPO, f"data/vi_vn/audio/{split}.tar.gz", local, rev)):
                if not name.endswith(".wav"):
                    continue
                fn = Path(name).name
                seen.add(fn)
                i = wav_info(b)
                infos.append(i)
                if i and fn in tsv_ns and i["frames"] != tsv_ns[fn]:
                    mismatch += 1
            st["audio"] = summarize_wavs(infos)
            st["audio"].update({"tsv_rows_without_audio": len(set(tsv_ns) - seen),
                                "audio_without_tsv_row": len(seen - set(tsv_ns)),
                                "frames_differ_from_num_samples": mismatch})
        out[split] = st
        if rows:
            r = rows[0]
            examples.append(("FLEURS", split, [[r["sent_id"], r["raw"], en_by_id.get(r["sent_id"], "(không có)")]]))
    out["id_overlap_between_splits"] = {f"{a}&{b}": len(vi_ids_by_split[a] & vi_ids_by_split[b])
                                        for a, b in (("train", "dev"), ("train", "test"), ("dev", "test"))}
    return out


# ---------------------------------------------------------------- PhoMT

def inspect_phomt(args, examples):
    meta = repo_meta(PHOMT_REPO, "main")
    files = ensure_phomt(args.phomt_dir)
    out = {"meta": meta, "fields": ["câu tiếng Việt (.vi)", "câu tiếng Anh (.en)", "song song theo số dòng"],
           "files_used": {f"{s}.{l}": str(p.relative_to(args.phomt_dir)) for (s, l), p in files.items()},
           "has_tokenization_folder": any("token" in str(p).lower() and "detok" not in str(p).lower()
                                          for p in args.phomt_dir.rglob("*") if p.is_dir()),
           "domain_note": "PhoMT không kèm nhãn miền từng câu; tỉ lệ miền lấy từ Table 1 của paper PhoMT"}
    for split in SPLITS:
        nv, ev = count_lines(files[(split, "vi")])
        ne, ee = count_lines(files[(split, "en")])
        out[split] = {"pairs_vi_lines": nv, "pairs_en_lines": ne, "line_counts_match": nv == ne,
                      "empty_vi": ev, "empty_en": ee}
    with open(files[("test", "vi")], encoding="utf-8") as fv, open(files[("test", "en")], encoding="utf-8") as fe:
        examples.append(("PhoMT (không đưa lên GitHub)", "test", [[v.strip(), e.strip()] for v, e, _ in zip(fv, fe, range(2))]))
    return out


# ---------------------------------------------------------------- bảng và kiểm chứng

def actual_values(f):
    a = {}
    v = f.get("vivos")
    if v:
        for split in ("train", "test"):
            a[f"VIVOS {split}: số câu"] = v[split]["utterances"]
            a[f"VIVOS {split}: số người nói"] = v[split]["speakers"]
        if "duration" in v["train"]:
            a["VIVOS train: số giờ (14:55)"] = v["train"]["duration"].get("hours")
            a["VIVOS test: số phút"] = round(v["test"]["duration"].get("hours", 0) * 60, 2)
    fl = f.get("fleurs")
    if fl:
        t = fl["test"]
        d = t["duration_from_num_samples"]
        a.update({"FLEURS vi_vn test: số bản thu": t["recordings"], "FLEURS vi_vn test: số câu gốc": t["sentences"],
                  "FLEURS vi_vn test: số giờ": round(d["hours"], 2), "FLEURS vi_vn test: thời lượng TB (s)": d["mean_s"],
                  "FLEURS vi_vn test: dài nhất (s)": d["max_s"], "FLEURS vi_vn test: số bản thu nhãn MALE": t["gender"].get("MALE", 0),
                  "FLEURS vi_vn test: số câu có câu Anh": t["sentences_with_en"]})
    p = f.get("phomt")
    if p:
        for split in SPLITS:
            a[f"PhoMT {split}: số cặp"] = p[split]["pairs_vi_lines"]
    return a


def verify(f):
    a = actual_values(f)
    rows = []
    for k, exp in EXPECTED.items():
        got = a.get(k)
        if got is None:
            status = "chưa đo (bỏ qua / cần --audio_stats)"
        elif isinstance(exp, float):
            status = "khớp" if abs(got - exp) <= 0.01 + 1e-9 else f"LỆCH {got - exp:+.2f}"
        else:
            status = "khớp" if got == exp else f"LỆCH {got - exp:+d}"
        rows.append({"muc": k, "task1": exp, "dem_lai": got, "ket_qua": status})
    return rows


def source_rows(f):
    rows = []
    v = f.get("vivos")
    if v:
        files = v["meta"].get("files", {})
        dur = {s: v[s].get("duration", {}).get("hours") for s in ("train", "test")}
        rows.append({
            "nguon": "VIVOS", "loai": "Online (public)", "url": f"{v['meta']['url']} (gốc: zenodo.org/record/7068130)",
            "giay_phep": v["meta"].get("license_card") or "CC BY-NC-SA 4.0 (theo card)",
            "so_mau": f"train {fmt_int(v['train']['utterances'])} câu / {v['train']['speakers']} người nói; "
                      f"test {fmt_int(v['test']['utterances'])} câu / {v['test']['speakers']} người nói"
                      + (f"; {dur['train']} + {dur['test']} giờ" if dur["train"] else ""),
            "dinh_dang": "WAV trong vivos.tar.gz + prompts .txt.gz" + (
                f" ({', '.join(f'{k} Hz' for k in v['train'].get('audio', {}).get('sample_rates', {}))})" if "audio" in v["train"] else ""),
            "dung_luong_mb": mb(sum(files.values())),
            "truong": ", ".join(v["fields"]) + ("; giới tính theo người nói (genders.txt)" if v["train"].get("speaker_gender") else ""),
        })
    fl = f.get("fleurs")
    if fl:
        files = fl["meta"].get("files", {})
        vi_bytes = sum(s for k, s in files.items() if k.startswith("data/vi_vn/"))
        en_bytes = sum(s for k, s in files.items() if k.startswith("data/en_us/"))
        rows.append({
            "nguon": "FLEURS vi_vn", "loai": "Online (public)", "url": f"{fl['meta']['url']} (thư mục data/vi_vn)",
            "giay_phep": fl["meta"].get("license_card") or "CC BY 4.0",
            "so_mau": "; ".join(f"{s} {fmt_int(fl[s]['recordings'])} bản thu / {fmt_int(fl[s]['sentences'])} câu, "
                                f"{fl[s]['duration_from_num_samples'].get('hours')} giờ" for s in SPLITS),
            "dinh_dang": "WAV trong audio/{split}.tar.gz + TSV" + (
                f" ({', '.join(f'{k} Hz' for k in fl['train'].get('audio', {}).get('sample_rates', {}))})" if "audio" in fl["train"] else ""),
            "dung_luong_mb": mb(vi_bytes), "truong": ", ".join(fl["fields"]),
        })
        rows.append({
            "nguon": "FLEURS en_us (chỉ lấy câu Anh)", "loai": "Online (public)", "url": f"{fl['meta']['url']} (data/en_us/*.tsv)",
            "giay_phep": fl["meta"].get("license_card") or "CC BY 4.0",
            "so_mau": "; ".join(f"{s} {fmt_int(fl['en_us'][s]['sentences'])} câu" for s in SPLITS),
            "dinh_dang": "TSV (không dùng audio tiếng Anh)", "dung_luong_mb": mb(en_bytes),
            "truong": "id (ghép với vi_vn), raw_transcription = câu Anh tham chiếu",
        })
    p = f.get("phomt")
    if p:
        files = p["meta"].get("files", {})
        rows.append({
            "nguon": "PhoMT", "loai": "Online (gated)", "url": p["meta"]["url"],
            "giay_phep": "Chỉ nghiên cứu/giáo dục, cấm phân phối lại",
            "so_mau": "; ".join(f"{s} {fmt_int(p[s]['pairs_vi_lines'])} cặp" for s in SPLITS),
            "dinh_dang": "Văn bản song song .vi/.en trong PhoMT.zip", "dung_luong_mb": mb(sum(files.values())),
            "truong": ", ".join(p["fields"]),
        })
    rows.append({"nguon": "Dữ liệu tự thu", "loai": "Offline", "url": "Không thu thập", "giay_phep": "-", "so_mau": "0",
                 "dinh_dang": "-", "dung_luong_mb": "-", "truong": OFFLINE_REASON})
    return rows


def warnings(f):
    """Những điểm bất thường cần ghi vào báo cáo hoặc xử lý ở bước làm sạch (việc 2)."""
    w = []
    v = f.get("vivos", {})
    for split in ("train", "test"):
        st = v.get(split, {})
        if st.get("duplicate_ids"):
            w.append(f"VIVOS {split}: {st['duplicate_ids']} ID câu bị trùng trong prompts")
        if st.get("label", {}).get("n_empty"):
            w.append(f"VIVOS {split}: {st['label']['n_empty']} câu nhãn rỗng")
        if st.get("audio", {}).get("n_unreadable"):
            w.append(f"VIVOS {split}: {st['audio']['n_unreadable']} file wav không đọc được")
        if st.get("audio") and st["audio"]["n_files"] != st["utterances"]:
            w.append(f"VIVOS {split}: {st['audio']['n_files']} file wav nhưng {st['utterances']} dòng prompts")
    fl = f.get("fleurs", {})
    for split in SPLITS:
        st = fl.get(split, {})
        if not st:
            continue
        for key, msg in (("bad_tsv_lines", "dòng TSV sai định dạng"), ("duplicate_file_names", "tên file audio bị trùng"),
                         ("n_over_30s", "bản thu dài hơn 30 giây (Whisper cắt 30 s)")):
            if st.get(key):
                w.append(f"FLEURS vi_vn {split}: {st[key]} {msg}")
        if st["sentences_with_en"] < st["sentences"]:
            w.append(f"FLEURS vi_vn {split}: {st['sentences'] - st['sentences_with_en']} câu không có câu Anh trong en_us")
        if len(st["gender"]) == 1:
            w.append(f"FLEURS vi_vn {split}: 100% bản thu cùng nhãn giới tính {list(st['gender'])[0]}")
        a = st.get("audio", {})
        for key, msg in (("n_unreadable", "file wav không đọc được"), ("tsv_rows_without_audio", "dòng TSV không có audio"),
                         ("audio_without_tsv_row", "file audio không có dòng TSV"),
                         ("frames_differ_from_num_samples", "file có số mẫu audio khác cột num_samples")):
            if a.get(key):
                w.append(f"FLEURS vi_vn {split}: {a[key]} {msg}")
    for pair, n in fl.get("id_overlap_between_splits", {}).items():
        if n:
            w.append(f"FLEURS vi_vn: {n} ID câu nằm ở cả {pair.replace('&', ' và ')} (viec2_ghep_chia_fleurs_chong_trung.py sẽ bỏ khỏi tập dạy)")
    p = f.get("phomt", {})
    for split in SPLITS:
        st = p.get(split, {})
        if st and not st["line_counts_match"]:
            w.append(f"PhoMT {split}: số dòng .vi ({st['pairs_vi_lines']}) khác .en ({st['pairs_en_lines']})")
        if st.get("empty_vi") or st.get("empty_en"):
            w.append(f"PhoMT {split}: {st['empty_vi']} dòng vi rỗng, {st['empty_en']} dòng en rỗng")
    return w


HEAD = [("nguon", "Nguồn"), ("loai", "Loại"), ("url", "URL / Cách thu thập"), ("so_mau", "Số lượng mẫu"),
        ("dinh_dang", "Định dạng file"), ("dung_luong_mb", "Dung lượng (MB)"), ("truong", "Các trường dữ liệu"),
        ("giay_phep", "Giấy phép")]


def md_table(rows, head):
    lines = ["| " + " | ".join(h for _, h in head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(str(r[k]).replace("|", "/") for k, _ in head) + " |" for r in rows]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data_dir", type=Path, default=Path("data"))
    ap.add_argument("--report_dir", type=Path, default=Path("reports/task2/data"))
    ap.add_argument("--phomt_dir", type=Path, default=None, help="mặc định <data_dir>/phomt")
    ap.add_argument("--fleurs_revision", default="main")
    ap.add_argument("--vivos_revision", default="main")
    ap.add_argument("--audio_stats", action="store_true", help="tải audio VIVOS + FLEURS vi_vn để kiểm wav thật")
    ap.add_argument("--skip_phomt", action="store_true")
    args = ap.parse_args()
    args.phomt_dir = args.phomt_dir or args.data_dir / "phomt"
    args.report_dir.mkdir(parents=True, exist_ok=True)
    args.data_dir.mkdir(parents=True, exist_ok=True)

    examples = []
    facts = {"script": "viec1_tai_3_bo_du_lieu.py",
             "time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
             "args": {k: str(v) for k, v in vars(args).items()}, "versions": lib_versions(), "platform": platform.platform()}
    print("[1/3] VIVOS ...")
    facts["vivos"] = inspect_vivos(args, examples)
    print("[2/3] FLEURS vi_vn + en_us ...")
    facts["fleurs"] = inspect_fleurs(args, examples)
    if args.skip_phomt:
        print("[3/3] PhoMT: bỏ qua (--skip_phomt)")
    else:
        print("[3/3] PhoMT ...")
        facts["phomt"] = inspect_phomt(args, examples)

    check = verify(facts)
    facts["kiem_chung"] = check
    facts["canh_bao"] = warn = warnings(facts)
    rows = source_rows(facts)
    (args.report_dir / "dataset_facts.json").write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(args.report_dir / "nguon_du_lieu.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=[k for k, _ in HEAD])
        w.writerow({k: h for k, h in HEAD})
        w.writerows(rows)
    shas = {k: facts[k]["meta"].get("sha", "?") for k in ("vivos", "fleurs", "phomt") if k in facts}
    (args.report_dir / "nguon_du_lieu.md").write_text(
        "# Bảng nguồn dữ liệu (slide 3, mục 1.1)\n\n" + md_table(rows, HEAD) +
        f"\n\nSinh bởi viec1_tai_3_bo_du_lieu.py lúc {facts['time_utc']}. Mã commit repo: {shas}.\n", encoding="utf-8")
    (args.report_dir / "kiem_chung.md").write_text(
        "# Kiểm chứng số liệu Task 1\n\n" +
        md_table(check, [("muc", "Mục"), ("task1", "Số ghi ở Task 1"), ("dem_lai", "Script đếm lại"), ("ket_qua", "Kết quả")]) +
        "\n\n## Cảnh báo (đưa vào bước làm sạch / mục hạn chế)\n\n" + ("\n".join(f"- {x}" for x in warn) or "- Không có") +
        "\n", encoding="utf-8")
    with open(args.data_dir / "vi_du_mau.md", "w", encoding="utf-8") as f:
        f.write("# Ví dụ mẫu (KHÔNG commit; PhoMT cấm phân phối lại)\n")
        for name, split, items in examples:
            f.write(f"\n## {name} - {split}\n")
            for it in items:
                f.write("- " + " | ".join(it) + "\n")

    print("\n" + md_table(check, [("muc", "Mục"), ("task1", "Task 1"), ("dem_lai", "Đếm lại"), ("ket_qua", "Kết quả")]))
    n_bad = sum(r["ket_qua"].startswith("LỆCH") for r in check)
    print(f"\n{n_bad} mục lệch so với Task 1." if n_bad else "\nTất cả mục đã đo đều khớp Task 1.")
    print("\nCảnh báo:\n" + ("\n".join(f"  - {x}" for x in warn) or "  (không có)"))
    print(f"Báo cáo (commit được): {args.report_dir}/  |  Ví dụ mẫu (không commit): {args.data_dir / 'vi_du_mau.md'}")


if __name__ == "__main__":
    main()
