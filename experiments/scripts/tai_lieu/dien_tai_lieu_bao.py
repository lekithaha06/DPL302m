#!/usr/bin/env python3
"""Điền ô [CHỜ KIỆT] trên BẢN CHÉP báo cáo + slide ASR của Bảo bằng số từ log thật (reports/asr/*, runs/asr/*).

Đầu vào (bản chép, không phải bản gốc trong teamwork/task2): tai_lieu/BaoCao_ASR_Task2.docx, tai_lieu/Slide_ASR_Task2.pptx
Đầu ra: tai_lieu/BaoCao_ASR_Task2_DA_DIEN.docx, tai_lieu/Slide_ASR_Task2_DA_DIEN.pptx, tai_lieu/NGUON_SO_DA_DIEN.csv (ô nào ← file nào).
Ô "đã nghe audio" lấy từ nghe_kiem/danh_sach_nghe_kiem.csv; nếu người nghe chưa điền thì ghi CHƯA NGHE (không đoán).
Ô V1 trong báo cáo (đoạn "Ô kết quả V1 LoRA") chỉ điền khi có reports/tong_hop/ban_cuoi.txt (bản cuối khối dịch).
"""
import csv
import json
from pathlib import Path

from docx import Document
from pptx import Presentation

T = Path(__file__).resolve().parents[1]
PH = "[CHỜ KIỆT]"
src_log = []


def vn(x, d=2):
    return f"{x:.{d}f}".replace(".", ",")


def fill_paragraph(p, values, where, size=None):
    """Thay lần lượt từng [CHỜ KIỆT] trong một đoạn (docx/pptx), giữ định dạng run đầu tiên."""
    text = "".join(r.text for r in p.runs)
    if PH not in text:
        return 0
    n = text.count(PH)
    for v in values[:n]:
        text = text.replace(PH, v[0], 1)
        src_log.append({"vi_tri": where, "gia_tri": v[0], "nguon": v[1]})
    del values[:n]
    p.runs[0].text = text
    if size:
        from pptx.util import Pt
        p.runs[0].font.size = Pt(size)
    for r in p.runs[1:]:
        r.text = ""
    return n


def bo_nhan(paragraphs):
    """Gỡ nhãn người cập nhật khỏi nội dung hiển thị (nguồn từng ô vẫn ở NGUON_SO_DA_DIEN.csv)."""
    import re
    mau = re.compile(r"\[Kiệt cập nhật( \d\d/\d\d/\d{4})?\]:?\s*| \(Kiệt\)(?=\.)")
    for p in paragraphs:
        for r in p.runs:
            t = re.sub(r"\[Kiệt cập nhật \d\d/\d\d/\d{4}: (.*?)\]", r"\1", r.text)
            t = mau.sub("", t)
            if t != r.text:
                r.text = t


def tat_ca_doan_docx(d):
    yield from d.paragraphs
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                yield from c.paragraphs


def tat_ca_doan_pptx(pr):
    for sl in pr.slides:
        for sh in sl.shapes:
            if sh.has_text_frame:
                yield from sh.text_frame.paragraphs
            if sh.has_table:
                for row in sh.table.rows:
                    for c in row.cells:
                        yield from c.text_frame.paragraphs


def main():
    R = {r["run_id"]: r for r in csv.DictReader(open(T / "reports" / "asr" / "results_task2.csv", encoding="utf-8-sig"))}
    S = lambda rid: f"reports/asr/results_task2.csv#{rid}"
    pho_v, pho_f = R["kiet_t2_phowhisper-small_vivos_test"], R["kiet_t2_phowhisper-small_fleurs_test"]
    wsp_v, wsp_f = R["kiet_t2_whisper-small_vivos_test"], R["kiet_t2_whisper-small_fleurs_test"]
    W = lambda r: vn(float(r["WER_percent"])) + "%"
    C = lambda r: vn(float(r["CER_percent"])) + "%"
    nghe = {r["recording_id"]: r for r in csv.DictReader(open(T / "nghe_kiem" / "danh_sach_nghe_kiem.csv", encoding="utf-8-sig"))}

    def heard(rid):
        r = nghe.get(rid, {})
        who = (r.get("NGUOI_NGHE_dien") or "").strip()
        if not who:
            return "CHƯA NGHE (chờ thành viên nghe)"
        parts = [r.get(k, "").strip() for k in ("nghe_ro_khong (ro/kho_nghe/nhieu)", "cau_goc_dung_voi_audio (dung/sai_cho_nao)",
                                                 "loi_la_do (model_nghe_sai/nhan_sai/audio_kem/ao_giac)", "nhan_xet")]
        short = {"model_nghe_sai": "người đọc rõ, đúng câu gốc → model nghe sai"}.get(parts[2], "")
        return f"Đã nghe ({who.split(' (')[0]}): " + (short or parts[3] or "; ".join(x for x in parts if x))

    # ---------- báo cáo docx ----------
    d = Document(T / "tai_lieu" / "BaoCao_ASR_Task2.docx")
    for p in d.paragraphs:
        if p.text.startswith("Trạng thái kết quả Task 2 là CHỜ KIỆT."):
            t = p.text.replace("Trạng thái kết quả Task 2 là CHỜ KIỆT.",
                               "Trạng thái kết quả Task 2: ĐÃ CHẠY (Kiệt, 30/10/2026, run_id kiet_t2_*; số trong các bảng dưới lấy từ reports/asr/ của Kiệt).")
            p.runs[0].text = t
            for r in p.runs[1:]:
                r.text = ""
            src_log.append({"vi_tri": "docx đoạn trạng thái", "gia_tri": "ĐÃ CHẠY", "nguon": "NHAT_KY.md"})
    t5 = d.tables[5]
    for row, r, rid in zip(t5.rows[1:], (pho_v, pho_f, wsp_v, wsp_f), ("pv", "pf", "wv", "wf")):
        fill_paragraph(row.cells[3].paragraphs[0], [(W(r), S(r["run_id"]))], f"docx T5 {r['run_id']}")
    t8 = d.tables[8]
    for row, r in zip(t8.rows[1:], (pho_v, wsp_v, pho_f, wsp_f)):
        vals = [(f"{r['n_scored']}/{r['n_expected']}", S(r["run_id"])),
                (f"WER {W(r)} · CER {C(r)}", S(r["run_id"])),
                (f"RTF {vn(float(r['rtf']), 3)} · p50 {vn(float(r['latency_p50_s']))} s · p95 {vn(float(r['latency_p95_s']))} s", S(r["run_id"]))]
        for k, c in enumerate(row.cells[2:5]):
            fill_paragraph(c.paragraphs[0], [vals[k]], f"docx T8 {r['run_id']} cột {k + 3}")
    bc = T / "reports" / "tong_hop" / "ban_cuoi.txt"
    if bc.exists():
        v = bc.read_text(encoding="utf-8").strip().split()[-1]
        sc = json.loads((T / "runs" / "mt" / v / "fleurs_test_asr_pho" / "score.json").read_text(encoding="utf-8"))
        ch = json.loads((T / "checkpoints" / v / "best" / "chon.json").read_text(encoding="utf-8"))
        for p in d.paragraphs:
            if p.text.startswith("Ô kết quả V1 LoRA"):
                fill_paragraph(p, [
                    (f"{W(pho_f)} (không đổi – V1..Vn của nhóm là LoRA cho KHỐI DỊCH, khối ASR giữ PhoWhisper-small baseline)", S(pho_f["run_id"])),
                    (f"{C(pho_f)} (như trên); chỉ số chính của bản đề xuất là BLEU cascade FLEURS test {vn(sc['BLEU'])} ({v})", f"runs/mt/{v}/fleurs_test_asr_pho/score.json"),
                    (f"vinai/vinai-translate-vi2en-v2 @ae7baa85 + adapter LoRA checkpoints/{v}/best", f"checkpoints/{v}/best/chon.json"),
                    (" + ".join(json.loads((T / "checkpoints" / v / "config.json").read_text(encoding="utf-8"))["train"]).replace("\\", "/") +
                     f" ({json.loads((T / 'checkpoints' / v / 'config.json').read_text(encoding='utf-8'))['n_train']} mẫu; phần FLEURS là lời PhoWhisper của FLEURS train)", f"checkpoints/{v}/config.json"),
                    (f"epoch {ch['best_epoch']}, BLEU dev cascade {vn(ch['dev_BLEU_translate'])} (translate.py)", f"checkpoints/{v}/best/chon.json")], "docx đoạn V1 LoRA")
                bs = json.loads((T / "reports" / "mt" / f"bootstrap_B0_{v}_cascade_test.json").read_text(encoding="utf-8"))
                old = "Chưa có số nên chưa kết luận tín hiệu cải thiện hoặc khả thi Task 3."
                if old in p.runs[0].text:
                    new = (f"[Kiệt cập nhật 31/10/2026] Đã có số: tín hiệu cải thiện ở khối dịch – BLEU cascade {v} hơn B0 {vn(bs['delta'])} điểm "
                           f"(KTC 95% [{vn(bs['ci95'][0])}; {vn(bs['ci95'][1])}]); khối ASR không đổi. Khả thi Task 3: xem báo cáo Task 2 của Kiệt, mục 5.")
                    p.runs[0].text = p.runs[0].text.replace(old, new)
                    src_log.append({"vi_tri": "docx đoạn V1 LoRA – câu kết", "gia_tri": new, "nguon": f"reports/mt/bootstrap_B0_{v}_cascade_test.json"})
    gh = T / "reports" / "asr" / "gap_hypotheses.json"
    GH = json.loads(gh.read_text(encoding="utf-8")) if gh.exists() else {}
    STV = {"CO_BANG_CHUNG": "Có bằng chứng", "MOT_PHAN": "Một phần", "KHONG_UNG_HO": "Không ủng hộ", "DA_KIEM": "Đã kiểm"}
    if GH:
        for t in d.tables:
            if any(c.text.startswith("H1 ") for r in t.rows for c in r.cells):
                from docx.oxml import OxmlElement
                from docx.shared import Pt
                from docx.text.paragraph import Paragraph
                anchor = t._tbl
                for hid in ("H5", "H4", "H3", "H2", "H1"):  # chèn ngược để thứ tự cuối là H1..H5
                    np_ = OxmlElement("w:p"); anchor.addnext(np_)
                    para = Paragraph(np_, t._parent)
                    txt = f"[Kiệt cập nhật] {hid} – {STV[GH[hid]['status']]}: {GH[hid]['ket_qua']} (nguồn: {GH[hid]['nguon']})"
                    run = para.add_run(txt); run.font.size = Pt(10)
                    src_log.append({"vi_tri": f"docx sau bảng giả thuyết {hid}", "gia_tri": txt[:80], "nguon": "reports/asr/gap_hypotheses.json"})
                break
    # Câu của Bảo đã lỗi thời khi có run Task 2: giữ nguyên câu gốc, nối thêm câu cập nhật có đánh dấu.
    UPD = {"FLEURS và các phiên bản V1–Vn chưa có kết quả ASR mới":
           f" [Kiệt cập nhật 31/10/2026: đã có run Task 2 – PhoWhisper FLEURS test {W(pho_f)}, Whisper {W(wsp_f)}; V1–Vn của nhóm là LoRA khối dịch nên WER ASR không đổi.]",
           "Chưa có run Task 2 được Kiệt xác nhận":
           " [Kiệt cập nhật 31/10/2026: đã có run Task 2 (kiet_t2_*), ID/n khớp manifest, 7/7 bản > 30 s có output; kết quả kiểm H1–H5 ở các đoạn dưới bảng giả thuyết.]"}
    for p in d.paragraphs:
        for key, add in UPD.items():
            if key in p.text and "[Kiệt cập nhật" not in p.text:
                p.add_run(add)
                src_log.append({"vi_tri": "docx nối câu cập nhật: " + key[:40], "gia_tri": add.strip()[:80], "nguon": "reports/asr/results_task2.csv"})
    out_d = T / "tai_lieu" / "BaoCao_ASR_Task2_DA_DIEN.docx"
    bo_nhan(tat_ca_doan_docx(d))
    d.save(out_d)

    # ---------- slide pptx ----------
    pr = Presentation(T / "tai_lieu" / "Slide_ASR_Task2.pptx")
    s4 = pr.slides[3]
    for sh in s4.shapes:
        if sh.has_table:
            for row, r in zip(list(sh.table.rows)[1:], (pho_v, pho_f, wsp_v, wsp_f)):
                fill_paragraph(row.cells[2].text_frame.paragraphs[0], [(W(r), S(r["run_id"]))], f"pptx S4 WER {r['run_id']}")
                fill_paragraph(row.cells[3].text_frame.paragraphs[0], [(C(r), S(r["run_id"]))], f"pptx S4 CER {r['run_id']}")
    if GH:
        SHORT = {"H1": "(≤30 s vẫn {})", "H2": "(chưa chấm mapping số)", "H3": "(KTC 95% ≠ 0)", "H4": "(beam 5 tốt hơn)", "H5": "(lỗi là chèn)"}
        for sh in pr.slides[5].shapes:
            if sh.has_table:
                for row in list(sh.table.rows)[1:]:
                    hid = row.cells[0].text.split()[0]
                    if hid in GH:
                        note = SHORT[hid].format(GH[hid]["ket_qua"].split("vẫn ")[1].split(".")[0] if hid == "H1" else "")
                        para = row.cells[2].text_frame.paragraphs[0]
                        size = para.runs[0].font.size if para.runs else None
                        for r in para.runs[1:]:
                            r.text = ""
                        para.runs[0].text = f"{STV[GH[hid]['status']]} {note}"
                        from pptx.util import Pt
                        para.runs[0].font.size = Pt(12)
                        src_log.append({"vi_tri": f"pptx S6 {hid}", "gia_tri": para.runs[0].text, "nguon": "reports/asr/gap_hypotheses.json"})
        for sh in pr.slides[5].shapes:
            if sh.has_text_frame and sh.text_frame.text.startswith("Chưa có run Task 2"):
                pa = sh.text_frame.paragraphs[0]
                pa.runs[0].text = "[Kiệt cập nhật] Đã kiểm bằng run Task 2 của Kiệt (30–31/10/2026); chi tiết: reports/asr/gap_hypotheses.csv"
                for r in pa.runs[1:]:
                    r.text = ""
                src_log.append({"vi_tri": "pptx S6 phụ đề", "gia_tri": pa.runs[0].text, "nguon": "reports/asr/gap_hypotheses.csv"})
    s7 = pr.slides[6]
    al = {}
    for f in ("kiet_t2_phowhisper-small_vivos_test", "kiet_t2_phowhisper-small_fleurs_test"):
        for r in csv.DictReader(open(T / "runs" / "asr" / f / "score" / "per_utterance.csv", encoding="utf-8-sig")):
            al[r["id"]] = (f, r)
    cases = [r for r in nghe.values() if r["stt"] in ("8", "9")]
    for sh in s7.shapes:
        if sh.has_text_frame and PH in sh.text_frame.text:
            for p in sh.text_frame.paragraphs:
                fill_paragraph(p, [("PhoWhisper-small (không adapter)", "configs/asr_protocol.json"),
                                   ("kiet_t2_phowhisper-small_*_test", "runs/asr/"),
                                   ("VIVOS / FLEURS test", "runs/manifests/")], "pptx S7 tiêu đề", size=16)
        if sh.has_table:
            rows = list(sh.table.rows)
            for k, cs in enumerate(cases):
                f, pu = al[cs["recording_id"]]
                lab = "chỉ sai dấu thanh" if cs["stt"] == "8" else "tên riêng"
                if "model_nghe_sai" in cs.get("loi_la_do (model_nghe_sai/nhan_sai/audio_kem/ao_giac)", ""):
                    lab = "gợi ý tự động: " + lab + "; nghe kiểm: model nghe sai"; lab_tail = ""
                else:
                    lab_tail = " (gợi ý)"
                vals = [f"{cs['recording_id']} (nghe_kiem mục {int(cs['stt']):02d})", cs["cau_goc_dataset"], cs["PhoWhisper_nhan_ra"],
                        f"{pu['S']} {pu['D']} {pu['I']} / {pu['N']} · {lab}{lab_tail}", heard(cs["recording_id"])]
                for ri, v in enumerate(vals, 1):
                    fill_paragraph(rows[ri].cells[k + 1].text_frame.paragraphs[0], [(v, f"runs/asr/{f}/score/per_utterance.csv; nghe_kiem/danh_sach_nghe_kiem.csv")], f"pptx S7 hàng {ri} TH{k + 1}", size=12)
    s8 = pr.slides[7]
    for sh in s8.shapes:
        if sh.has_table:
            rows = list(sh.table.rows)
            for k, (rv, rf) in enumerate(((pho_v, pho_f), (wsp_v, wsp_f))):
                vals = [f"VIVOS {W(rv)} / {C(rv)} ({rv['S']}/{rv['D']}/{rv['I']}/{rv['N']})\nFLEURS {W(rf)} / {C(rf)} ({rf['S']}/{rf['D']}/{rf['I']}/{rf['N']})",
                        f"VIVOS {vn(float(rv['rtf']), 3)} · {vn(float(rv['latency_p50_s']))} / {vn(float(rv['latency_p95_s']))} s\nFLEURS {vn(float(rf['rtf']), 3)} · {vn(float(rf['latency_p50_s']))} / {vn(float(rf['latency_p95_s']))} s",
                        f"{vn(max(int(rv['gpu_peak_allocated_bytes']), int(rf['gpu_peak_allocated_bytes'])) / 2**30)} GiB · {vn(int(rv['checkpoint_bytes']) / 1e6, 0)} MB",
                        f"{rv['config_sha256'][:8]}… · {rv['manifest_sha256'][:8]}… / {rf['manifest_sha256'][:8]}…"]
                for ri, v in enumerate(vals, 1):
                    fill_paragraph(rows[ri].cells[k + 1].text_frame.paragraphs[0], [(v, S(rv["run_id"]) + " ; " + S(rf["run_id"]))], f"pptx S8 hàng {ri} cột {k + 2}", size=12)
    FOOT = {"Khung phân tích của Bảo. Chưa có dự đoán V1 trong gói": "[Kiệt cập nhật] Ví dụ từ run baseline PhoWhisper Task 2 (V1–Vn là LoRA khối dịch, ASR không đổi); đã nghe kiểm 31/10.",
            "Nguồn: phân công Task 2; protocol ASR của Bảo. Chưa kết luận khả thi Task 3.": "Nguồn: reports/asr/results_task2.csv (Kiệt). [Kiệt cập nhật] Khả thi Task 3: xem báo cáo/slide Task 2 của Kiệt, mục 5."}
    for s in pr.slides:
        for sh in s.shapes:
            if sh.has_text_frame:
                for key, new in FOOT.items():
                    if sh.text_frame.text.startswith(key):
                        pa = sh.text_frame.paragraphs[0]; pa.runs[0].text = new
                        for r in pa.runs[1:]:
                            r.text = ""
                        src_log.append({"vi_tri": "pptx chân trang: " + key[:40], "gia_tri": new, "nguon": "NHAT_KY.md"})
    out_p = T / "tai_lieu" / "Slide_ASR_Task2_DA_DIEN.pptx"
    bo_nhan(tat_ca_doan_pptx(pr))
    pr.save(out_p)

    with open(T / "tai_lieu" / "NGUON_SO_DA_DIEN.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["vi_tri", "gia_tri", "nguon"]); w.writeheader(); w.writerows(src_log)
    left = lambda texts: sum(t.count(PH) for t in texts)
    dd = Document(out_d)
    doc_left = left([p.text for p in dd.paragraphs] + [c.text for t in dd.tables for r in t.rows for c in r.cells])
    pp = Presentation(out_p)
    ppt_left = left([sh.text_frame.text for s in pp.slides for sh in s.shapes if sh.has_text_frame] +
                    [c.text for s in pp.slides for sh in s.shapes if sh.has_table for r in sh.table.rows for c in r.cells])
    print(f"đã điền {len(src_log)} ô; còn [CHỜ KIỆT]: docx {doc_left}, pptx {ppt_left}")


if __name__ == "__main__":
    main()
