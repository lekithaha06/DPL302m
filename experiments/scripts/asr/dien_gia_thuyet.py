#!/usr/bin/env python3
"""Điền kết quả kiểm giả thuyết H1–H5 (gap_hypotheses.csv của Bảo) từ số đã chạy → reports/asr/gap_hypotheses.csv.

Mỗi kết luận đọc số từ file kết quả; trạng thái: CO_BANG_CHUNG / MOT_PHAN / KHONG_UNG_HO / DA_KIEM. Không tuyên bố nhân quả.
"""
import csv
import json
from pathlib import Path

T = Path(__file__).resolve().parents[2]
vn = lambda x, d=2: f"{float(x):.{d}f}".replace(".", ",")


def main():
    st = {(r["run_id"], r["group_type"], r["group_value"]): r for r in csv.DictReader(open(T / "reports/asr/strata.csv", encoding="utf-8-sig"))}
    P = "kiet_t2_phowhisper-small_fleurs_test"; W = "kiet_t2_whisper-small_fleurs_test"
    g = lambda run, t, v: st[(run, t, v)]
    sh = [g(P, "duration_s", b) for b in ("<=5", ">5_to_15", ">15_to_30")]
    le30 = 100 * sum(int(r["S"]) + int(r["D"]) + int(r["I"]) for r in sh) / sum(int(r["n_reference_units"]) for r in sh)
    R = {r["run_id"]: r for r in csv.DictReader(open(T / "reports/asr/results_task2.csv", encoding="utf-8-sig"))}
    bw = json.loads((T / "reports/asr/bootstrap_wer_H3.json").read_text(encoding="utf-8"))
    tone = {}
    for run in ("kiet_t2_phowhisper-small_vivos_test", P, "kiet_t2_whisper-small_vivos_test", W):
        tone[run] = sum(int(r["tone_only_substitutions"]) for r in csv.DictReader(open(T / f"runs/asr/{run}/score/per_utterance.csv", encoding="utf-8-sig")))
    lf = list(csv.DictReader(open(T / "reports/asr/long_form_audit.csv", encoding="utf-8-sig")))
    lfp = [r for r in lf if r["run_id"] == P]
    lg = g(P, "duration_s", ">30")
    nghe = {r["stt"]: r for r in csv.DictReader(open(T / "nghe_kiem/danh_sach_nghe_kiem.csv", encoding="utf-8-sig"))}
    res = {
        "H1": ("CO_BANG_CHUNG", f"PhoWhisper VIVOS {vn(R['kiet_t2_phowhisper-small_vivos_test']['WER_percent'])}% vs FLEURS {vn(R[P]['WER_percent'])}%; "
                                f"FLEURS chỉ tính ≤ 30 s vẫn {vn(le30)}%. WER FLEURS tăng theo độ dài: 5–15 s {vn(sh[1]['WER_percent'])} → 15–30 s {vn(sh[2]['WER_percent'])} → > 30 s {vn(lg['WER_percent'])}. "
                                "Quan sát trên hai corpus, không xác lập nhân quả.", "reports/asr/strata.csv"),
        "H2": ("MOT_PHAN", f"Câu có chữ số: WER {vn(g(P, 'name_or_number', 'number')['WER_percent'])}% (chèn {g(P, 'name_or_number', 'number')['I']}) vs câu không tên/số {vn(g(P, 'name_or_number', 'neither')['WER_percent'])}%. "
                           f"Nghe kiểm mục 10: người đọc nói 'tám không hai' cho '802', model ghi đúng âm → lỗi do cách viết. Chưa chạy chấm lại bằng mapping số khoá từ dev.",
               "reports/asr/strata.csv; nghe_kiem/danh_sach_nghe_kiem.csv"),
        "H3": ("CO_BANG_CHUNG", f"Ghép cặp cùng ID, bootstrap cụm 1000 lần: Whisper − PhoWhisper = +{vn(bw['vivos']['delta_whisper_minus_pho'])} [{vn(bw['vivos']['ci95'][0])}; {vn(bw['vivos']['ci95'][1])}] (VIVOS), "
                                f"+{vn(bw['fleurs']['delta_whisper_minus_pho'])} [{vn(bw['fleurs']['ci95'][0])}; {vn(bw['fleurs']['ci95'][1])}] (FLEURS). Thay thế chỉ sai dấu: PhoWhisper {tone['kiet_t2_phowhisper-small_vivos_test']}/{tone[P]} vs Whisper "
                                f"{tone['kiet_t2_whisper-small_vivos_test']}/{tone[W]} (VIVOS/FLEURS). Câu có tên riêng (heuristic): {vn(g(P, 'name_or_number', 'name')['WER_percent'])} vs {vn(g(W, 'name_or_number', 'name')['WER_percent'])}. "
                                "PhoWhisper đã thấy VIVOS train → không tách được kiến trúc với dữ liệu.", "reports/asr/bootstrap_wer_H3.json; tone_confusion_*.csv"),
        "H4": ("DA_KIEM", "FLEURS dev, chỉ đổi num_beams: bản thu ≤ 30 s PhoWhisper beam 5/1 = 10,70/10,91; Whisper 19,90/27,82 (beam 1 có 2 bản chạm cap 440). "
                          "Beam 1 không nhanh hơn rõ (Whisper RTF 0,147 vs 0,144). → Giữ beam 5.", "runs/asr/kiet_t2_*_fleurs_dev*, NHAT_KY.md"),
        "H5": ("KHONG_UNG_HO", f"{sum(r['has_output'] == 'True' for r in lfp)}/{len(lfp)} bản > 30 s có output, coverage phủ hết audio, không cắt 30 s; nhóm > 30 s: D = {lg['D']}, I = {lg['I']} "
                               f"/ N = {lg['n_reference_units']} → lỗi là CHÈN (lặp/sai đoạn sau 30 s), không phải thiếu từ. {sum(r['hit_cap_440'] == 'True' for r in lfp)}/7 chạm cap 440. "
                               f"Nghe kiểm: {nghe['1']['nguoi_noi_noi_den_giay_may (vd 28.5)'] if 'nguoi_noi_noi_den_giay_may (vd 28.5)' in nghe['1'] else nghe['1'].get('nguoi_noi_noi_den_giay_may', '')}.",
               "reports/asr/long_form_audit.csv; nghe_kiem/"),
    }
    rows = list(csv.DictReader(open(T / "tai_lieu/bang_mau_bao/gap_hypotheses.csv", encoding="utf-8-sig")))
    fields = list(rows[0]) + ["ket_qua_kiet", "nguon"]
    for r in rows:
        s, k, n = res[r["id"]]
        r["status"], r["ket_qua_kiet"], r["nguon"] = s, k, n
    with open(T / "reports/asr/gap_hypotheses.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    (T / "reports/asr/gap_hypotheses.json").write_text(json.dumps({k: {"status": v[0], "ket_qua": v[1], "nguon": v[2]} for k, v in res.items()}, ensure_ascii=False, indent=2), encoding="utf-8")
    for k, v in res.items():
        print(k, v[0], "|", v[1][:150])


if __name__ == "__main__":
    main()
