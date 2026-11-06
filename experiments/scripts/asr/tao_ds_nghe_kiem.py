#!/usr/bin/env python3
"""Tạo bộ nghe kiểm audio cho thành viên nhóm → nghe_kiem/ (chọn tự động, không chọn tay).

Chọn:
  - 7 bản thu FLEURS test dài > 30 s (kiểm ảo giác long-form của PhoWhisper; xem cả output whisper-small để so).
  - Trường hợp 1 (slide 7 của Bảo): PhoWhisper × VIVOS test, bản thu có lỗi chỉ sai dấu thanh, WER cao nhất.
  - Trường hợp 2 (slide 7): PhoWhisper × FLEURS test (≤ 30 s), có tên riêng, WER cao nhất.
  - Thêm 1 ca số: PhoWhisper × FLEURS test (≤ 30 s), tham chiếu có chữ số, WER cao nhất.
Đo tín hiệu (không phải nghe): mức âm RMS (dBFS) từng giây; "giây cuối có tiếng" = cửa sổ 0,5 s cuối có RMS > −45 dBFS.
Đầu ra: nghe_kiem/audio/*.wav (bản chép của audio model đã dùng), nghe_kiem/danh_sach_nghe_kiem.csv (mở bằng Excel, điền cột trống),
        nghe_kiem/nghe_kiem.html (mở bằng trình duyệt để nghe từng file ngay trên trang), nghe_kiem/HUONG_DAN.txt.
"""
import csv
import html
import json
import re
import shutil
from pathlib import Path

import numpy as np
import soundfile as sf

T = Path(__file__).resolve().parents[2]
OUT = T / "nghe_kiem"


def per_utt(rid):
    return {r["id"]: r for r in csv.DictReader(open(T / "runs" / "asr" / rid / "score" / "per_utterance.csv", encoding="utf-8-sig"))}


def manifest(ds):
    return {json.loads(l)["id"]: json.loads(l) for l in open(T / "runs" / "manifests" / f"asr_{ds}_test.jsonl", encoding="utf-8")}


def signal(path):
    a, sr = sf.read(path, dtype="float32")
    w = int(0.5 * sr)
    rms = [20 * np.log10(np.sqrt(np.mean(a[i:i + w] ** 2)) + 1e-9) for i in range(0, len(a) - w + 1, w)]
    loud = [i for i, r in enumerate(rms) if r > -45]
    last = (loud[-1] + 1) * 0.5 if loud else 0.0
    tail = a[30 * sr:] if len(a) > 30 * sr else a[:0]
    tail_db = 20 * np.log10(np.sqrt(np.mean(tail ** 2)) + 1e-9) if len(tail) else None
    return round(len(a) / sr, 2), round(last, 1), (round(float(tail_db), 1) if tail_db is not None else "")


def main():
    (OUT / "audio").mkdir(parents=True, exist_ok=True)
    mf, mv = manifest("fleurs"), manifest("vivos")
    pf, wf = per_utt("kiet_t2_phowhisper-small_fleurs_test"), per_utt("kiet_t2_whisper-small_fleurs_test")
    pv, wv = per_utt("kiet_t2_phowhisper-small_vivos_test"), per_utt("kiet_t2_whisper-small_vivos_test")
    picks = []
    for i in sorted((i for i, m in mf.items() if m["duration_s"] > 30), key=lambda i: mf[i]["duration_s"]):
        picks.append(("Bản thu dài > 30 s: có ảo giác ở đoạn cuối không?", "fleurs", i))
    tone = [r for r in pv.values() if int(r["tone_only_substitutions"]) > 0]
    picks.append(("Trường hợp 1 (slide 7): lỗi dấu thanh – người nói đọc dấu nào?", "vivos", max(tone, key=lambda r: (float(r["WER_percent"]), r["id"]))["id"]))
    short = [r for r in pf.values() if mf[r["id"]]["duration_s"] <= 30]
    name = [r for r in short if any(t[:1].isupper() for t in r["reference_raw"].split()[1:] if t[:1].isalpha()) and not re.search(r"\d", r["reference_raw"])]
    picks.append(("Trường hợp 2 (slide 7): tên riêng – người nói đọc tên thế nào?", "fleurs", max(name, key=lambda r: (float(r["WER_percent"]), r["id"]))["id"]))
    num = [r for r in short if re.search(r"\d", r["reference_raw"]) and r["id"] not in {p[2] for p in picks}]
    picks.append(("Số: người nói đọc số thế nào (vd 'hai nghìn' hay 'hai ngàn')?", "fleurs", max(num, key=lambda r: (float(r["WER_percent"]), r["id"]))["id"]))

    rows = []
    for k, (why, ds, i) in enumerate(picks, 1):
        m = (mf if ds == "fleurs" else mv)[i]
        p, w = ((pf, wf) if ds == "fleurs" else (pv, wv))
        src = Path(m["audio"])
        dst = OUT / "audio" / f"{k:02d}_{ds}_{src.name if src.suffix else src.name + '.wav'}"
        shutil.copyfile(src, dst)
        dur, last, tail_db = signal(src)
        rows.append({"stt": k, "muc_dich": why, "dataset": "FLEURS vi_vn test" if ds == "fleurs" else "VIVOS test", "recording_id": i,
                     "file_nghe": f"audio/{dst.name}", "duong_dan_goc_model_dung": str(src), "thoi_luong_s": dur,
                     "giay_cuoi_co_tieng_do_tin_hieu": last, "muc_am_sau_30s_dBFS": tail_db,
                     "cau_goc_dataset": m["reference"], "PhoWhisper_nhan_ra": p[i]["hypothesis_raw"], "PhoWhisper_WER": round(float(p[i]["WER_percent"]), 1),
                     "PhoWhisper_S_D_I_N": f"{p[i]['S']} {p[i]['D']} {p[i]['I']} / {p[i]['N']}",
                     "Whisper_nhan_ra": w[i]["hypothesis_raw"], "Whisper_WER": round(float(w[i]["WER_percent"]), 1),
                     "NGUOI_NGHE_dien": "", "nghe_ro_khong (ro/kho_nghe/nhieu)": "", "cau_goc_dung_voi_audio (dung/sai_cho_nao)": "",
                     "nguoi_noi_noi_den_giay_may": "", "loi_la_do (model_nghe_sai/nhan_sai/audio_kem/ao_giac)": "", "nhan_xet": ""})
    fields = list(rows[0])
    with open(OUT / "danh_sach_nghe_kiem.csv", "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=fields); wr.writeheader(); wr.writerows(rows)

    e = html.escape
    cards = []
    for r in rows:
        cards.append(f"""<section><h2>{r['stt']:02d}. {e(r['muc_dich'])}</h2>
<p class=meta>{e(r['dataset'])} · <code>{e(r['recording_id'])}</code> · {r['thoi_luong_s']} s · tín hiệu: có tiếng đến ~{r['giay_cuoi_co_tieng_do_tin_hieu']} s{(' · mức âm sau 30 s ' + str(r['muc_am_sau_30s_dBFS']) + ' dBFS') if r['muc_am_sau_30s_dBFS'] != '' else ''}</p>
<audio controls preload=none src="{e(r['file_nghe'])}"></audio>
<dl><dt>Câu gốc (dataset)</dt><dd>{e(r['cau_goc_dataset'])}</dd>
<dt>PhoWhisper nhận ra (WER {r['PhoWhisper_WER']}%, S D I / N = {r['PhoWhisper_S_D_I_N']})</dt><dd>{e(r['PhoWhisper_nhan_ra'])}</dd>
<dt>Whisper-small nhận ra (WER {r['Whisper_WER']}%)</dt><dd>{e(r['Whisper_nhan_ra'])}</dd></dl></section>""")
    (OUT / "nghe_kiem.html").write_text(f"""<!doctype html><html lang=vi><head><meta charset=utf-8><title>Nghe kiểm ASR</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;max-width:900px;margin:24px auto;padding:0 16px;line-height:1.5;color:#222;background:#fff}}
section{{border:1px solid #ccc;border-radius:8px;padding:12px 16px;margin:16px 0}}h2{{font-size:17px;margin:0 0 4px}}
.meta{{color:#555;font-size:13px;margin:0 0 8px}}audio{{width:100%}}dt{{font-weight:600;margin-top:8px}}dd{{margin:2px 0 0 0;word-break:break-word}}</style></head><body>
<h1>Nghe kiểm audio – ASR Task 2</h1><p>Nghe từng file, rồi điền các cột trống trong <b>danh_sach_nghe_kiem.csv</b> (mở bằng Excel). Số "có tiếng đến ~x s" là đo bằng tín hiệu, không phải nghe.</p>
{''.join(cards)}</body></html>""", encoding="utf-8")
    (OUT / "HUONG_DAN.txt").write_text(
        "NGHE KIỂM AUDIO (khoảng 15–20 phút)\n\n"
        "1. Mở nghe_kiem.html bằng trình duyệt (Chrome/Edge): mỗi mục có nút phát, câu gốc và câu 2 model nhận ra.\n"
        "   Hoặc mở thẳng file trong thư mục audio/ bằng trình phát nhạc.\n"
        "2. Mở danh_sach_nghe_kiem.csv bằng Excel, mỗi dòng điền:\n"
        "   - NGUOI_NGHE_dien: tên người nghe\n"
        "   - nghe_ro_khong: ro / kho_nghe / nhieu\n"
        "   - cau_goc_dung_voi_audio: dung, hoặc ghi chỗ người nói đọc khác câu gốc\n"
        "   - nguoi_noi_noi_den_giay_may: với 7 bản dài, người nói dừng ở khoảng giây thứ mấy\n"
        "   - loi_la_do: model_nghe_sai / nhan_sai / audio_kem / ao_giac (có thể ghi nhiều)\n"
        "   - nhan_xet: tự do\n"
        "3. Lưu lại (giữ định dạng CSV UTF-8). Kiệt/Claude sẽ đọc file này để điền ô 'đã nghe audio' trong slide/báo cáo của Bảo.\n"
        "Lưu ý: chỉ ghi điều nghe thấy thật; chỗ nào không chắc ghi 'khong_chac'.\n", encoding="utf-8")
    for r in rows:
        print(r["stt"], r["recording_id"], r["thoi_luong_s"], "tieng den", r["giay_cuoi_co_tieng_do_tin_hieu"], "sau30", r["muc_am_sau_30s_dBFS"], "Pho WER", r["PhoWhisper_WER"], "Wsp", r["Whisper_WER"])


if __name__ == "__main__":
    main()
