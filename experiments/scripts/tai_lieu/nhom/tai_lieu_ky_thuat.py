#!/usr/bin/env python3
"""Tài liệu kỹ thuật cho Bảo và Uyên: minh chứng, giải thích khoa học, hình. Mọi số đọc từ file kết quả."""
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from chung import *

EXP = TW / "repo_cuoi/experiments/reports"; t2, t0 = S.t2, S.t0; ab = S.ab; R = robust()
c = vn(S.c["BLEU"]); gap = vn(S.gap); rb = {k: s for k, _, _, s in R}
wer = lambda k: vn(rb[k]["WER_percent"])
d = Document()
sec = d.sections[0]; sec.page_width, sec.page_height = Cm(21), Cm(29.7); sec.left_margin = sec.right_margin = Cm(2.3); sec.top_margin = sec.bottom_margin = Cm(2.2)
XANH = RGBColor(0x1F, 0x27, 0x66)
st = d.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(11); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri"); st.paragraph_format.space_after = Pt(6); st.paragraph_format.line_spacing = 1.12
for n, sz, tr in (("Title", 22, 6), ("Heading 1", 15, 16), ("Heading 2", 12.5, 10)):
    x = d.styles[n]; x.font.name = "Calibri"; x.font.size = Pt(sz); x.font.bold = True; x.font.color.rgb = XANH; x.paragraph_format.space_before = Pt(tr); x.paragraph_format.space_after = Pt(5); x.paragraph_format.keep_with_next = True
    x.element.rPr.rFonts.set(qn("w:asciiTheme"), "") if False else None
    rf = x.element.rPr.find(qn("w:rFonts"))
    if rf is not None:
        for k in list(rf.attrib):
            del rf.attrib[k]
        rf.set(qn("w:ascii"), "Calibri"); rf.set(qn("w:hAnsi"), "Calibri"); rf.set(qn("w:eastAsia"), "Calibri")
H1 = lambda t: d.add_heading(t, 1)
H2 = lambda t: d.add_heading(t, 2)


def P(t):
    p = d.add_paragraph()
    for i, s in enumerate(t.split("**")):
        r = p.add_run(s); r.bold = i % 2 == 1
    return p


def B(*ds):
    for t in ds:
        p = d.add_paragraph(style="List Bullet")
        for i, s in enumerate(t.split("**")):
            r = p.add_run(s); r.bold = i % 2 == 1


def NG(t):
    p = d.add_paragraph(); r = p.add_run("Nguồn: " + t); r.italic = True; r.font.size = Pt(9); r.font.color.rgb = RGBColor(0x55, 0x5B, 0x66)


def CT(t):
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; r = p.add_run(t); r.font.name = "Cambria Math"; r.font.size = Pt(11.5)


def TB(hang, rong=None):
    t = d.add_table(rows=len(hang), cols=len(hang[0])); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(hang):
        for j, v in enumerate(h):
            o = t.cell(i, j); o.text = ""; p = o.paragraphs[0]; p.paragraph_format.space_after = Pt(1); r = p.add_run(str(v)); r.font.size = Pt(9.5)
            if i == 0:
                r.bold = True; r.font.color.rgb = RGBColor(255, 255, 255); sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:fill"), "1F2766"); o._tc.get_or_add_tcPr().append(sh)
            if rong:
                o.width = Cm(rong[j])
    tr = t.rows[0]._tr.get_or_add_trPr(); e = OxmlElement("w:tblHeader"); tr.append(e)
    d.add_paragraph().paragraph_format.space_after = Pt(2)


def HI(f, chu, w=15.5):
    d.add_picture(str(f), width=Cm(w)); d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER; d.paragraphs[-1].paragraph_format.keep_with_next = True
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; r = p.add_run(chu); r.italic = True; r.font.size = Pt(9.5)


d.add_paragraph("Tài liệu kỹ thuật cho Report và Slide FINAL", style="Title")
P("Project DPL302m, Đề tài 1: nhận dạng giọng nói tiếng Việt và dịch sang văn bản tiếng Anh, miền Giáo dục.")
P("Dành cho Dương Gia Bảo và Bùi Ngọc Phương Uyên. Cập nhật 04/11/2026.")
H1("Cách dùng tài liệu")
P("Tài liệu này gom ba thứ: **minh chứng kỹ thuật**, **giải thích khoa học**, và **hình** để viết Report, Slide FINAL. Mọi số đều lấy từ file kết quả đã xác nhận, nên không cần chạy lại thí nghiệm.")
B("Cần viết phần nào: đọc mục tương ứng rồi diễn đạt lại bằng lời của mình.", "Cần số: lấy từ bảng ở đây, rồi đối chiếu file ghi ở dòng Nguồn. Đường dẫn tính từ thư mục gốc của gói.", "Cần hình: lấy file gốc độ phân giải cao trong thư mục 2_hinh.", "Mục 11 và 12 chỉ rõ từng slide và từng dòng checklist lấy minh chứng ở đâu.")
# ---- 1
H1("1. Bài toán và lý do chọn cascade")
P("Hệ thống nhận audio tiếng Việt, trả về transcript tiếng Việt và bản dịch tiếng Anh kèm mốc thời gian. Có hai hướng: **end-to-end** dùng một mô hình đi thẳng từ audio sang chữ tiếng Anh, và **cascade** ghép một mô hình nhận dạng (ASR) với một mô hình dịch (MT).")
P("Nhóm chọn cascade vì lý do dữ liệu. Sau khi làm sạch chỉ có 2.926 bản thu FLEURS train có cả audio tiếng Việt lẫn câu tiếng Anh, trong khi khối dịch có PhoMT 2.977.170 cặp câu. Cascade tận dụng được dữ liệu dồi dào của từng khối. Đổi lại, nó bị **lỗi lan truyền**: khối dịch không biết khối nghe đã sai ở đâu.")
P(f"Đây là điểm nghẽn trung tâm. Cùng 857 bản thu FLEURS test, khối dịch đạt BLEU {vn(S.b0s['BLEU'])} với transcript chuẩn nhưng chỉ {vn(S.b0c['BLEU'])} với lời do khối nghe sinh ra, tức **mất 15,58 BLEU**.")
HI(H / "kien_truc_he_thong.png", "Hình 1. Kiến trúc: luồng đo thực nghiệm ở trên, luồng sản phẩm ở dưới")
P("Sơ đồ tách hai luồng vì số của chúng khác bối cảnh. Luồng trên chạy trực tiếp trên tệp có sẵn. Luồng dưới có thêm chia đoạn, bỏ lặp ở chỗ nối và đổi số.")
# ---- 2
H1("2. Dữ liệu")
TB([("Nguồn", "Dùng cho", "Train / dev / test sau làm sạch", "Giấy phép"), ("VIVOS", "đánh giá khối nghe", "11.656 / – / 760 câu", "CC BY-NC-SA 4.0"), ("FLEURS vi_vn + en_us", "huấn luyện, đánh giá cả hệ", "2.926 / 361 / 857 bản thu", "CC BY 4.0"), ("PhoMT", "khối dịch", "2.977.170 / 18.719 / 19.151 cặp", "chỉ nghiên cứu, cấm phân phối lại"), ("FLoRes+", "nhãn miền từng câu", "metadata 1.945 câu", "CC BY-SA 4.0")], [3.4, 4, 5, 4])
NG("3_bang_so/data/nguon_du_lieu.md, 3_bang_so/data/kiem_chung.md")
P("**Làm sạch sáu bước:** ghép và chống rò rỉ, loại mẫu thiếu, loại trùng, xử lý audio hỏng hoặc im lặng, chuẩn hoá audio về 16 kHz mono PCM 16-bit, chuẩn hoá chữ. Nguyên tắc: train và dev có thể loại mẫu, test chỉ gắn cờ, để điểm không đẹp hơn thực tế.")
P("**Gán nhãn:** nhóm không gán nhãn mới, dùng nhãn gốc của dataset. Vì không có hai người gán độc lập cùng một tập câu nên **Cohen's Kappa không áp dụng**, không được điền số.")
P("**Chống rò rỉ:** năm phép kiểm đều cho 0. Ngoại lệ phải nói rõ: 178/760 câu VIVOS test trùng chữ với câu train, do người khác đọc, và PhoWhisper đã fine-tune trên VIVOS train, nên WER trên VIVOS dễ hơn thực tế. Đây là lý do báo cả hai bộ test.")
P("**Mất cân bằng:** lệch rõ nhất là giới tính: FLEURS train 74,3% giọng nữ nhưng dev và test 100% giọng nam, nên kết quả chưa nói được gì về giọng nữ. Số bản thu mỗi câu cũng lệch, có câu được dạy nhiều gấp ba lần câu khác.")
HI(EXP / "data/can_bang/can_bang_02_do_dai.png", "Hình 2. Phân bố độ dài câu trước và sau cân bằng, chỉ trên train", 13)
P("**Kết quả cân bằng:** số mẫu dạy 2.926 → 4.468, chênh số lần dạy 3,0× → 1,5×. Nhưng đo cặp V2 và V3 cho thấy bước này không cải thiện có ý nghĩa trên test, nên bản cuối V2 không dùng nó. Báo cáo đúng như vậy thay vì chỉ nêu thiết kế.")
# ---- 3
H1("3. Các thước đo")
P("**WER và CER** đo khối nghe, tính bằng khoảng cách chỉnh sửa giữa tham chiếu và dự đoán:")
CT("WER = (S + D + I) / N")
P("Trong đó S là số từ thay thế, D xoá, I chèn, N số từ tham chiếu. CER dùng cùng công thức trên ký tự. WER có thể vượt 100% vì I không bị chặn. Với tiếng Việt, đơn vị tách bằng khoảng trắng gần với âm tiết. Báo cả S, D, I giúp thấy loại lỗi: nhóm audio dài có D = 2 nhưng I = 401 trên N = 472, tức lỗi là chèn chứ không phải thiếu từ.")
P("**BLEU** đo độ khớp n-gram của bản dịch với tham chiếu, từ 0 đến 100:")
CT("BLEU = BP · exp( (1/4) · Σ log pₙ ),  n = 1…4")
P("pₙ là độ chính xác n-gram, BP phạt bản dịch quá ngắn. Điểm BLEU chỉ có ý nghĩa khi so trên cùng tập và cùng cách tính, nên nhóm dùng sacreBLEU 2.4.3 và ghi kèm chữ ký cấu hình.")
P("**chrF++** đo trên n-gram ký tự kết hợp từ, ít phụ thuộc tách từ hơn BLEU. Nhóm dùng word_order = 2.")
P("**RTF** là tổng thời gian xử lý chia tổng thời lượng audio. RTF < 1 nghĩa là nhanh hơn thời gian thực.")
P("**Bootstrap theo cụm:** để biết chênh lệch có thật hay do ngẫu nhiên, nhóm lấy mẫu lại 1.000 lần theo 347 cụm sent_id, seed 42. Phải lấy theo cụm vì FLEURS có nhiều bản thu cho một câu; coi chúng độc lập sẽ làm khoảng tin cậy hẹp hơn thực tế. Nếu khoảng tin cậy 95% của chênh lệch không chứa 0 thì coi là có ý nghĩa. Bootstrap chỉ đo dao động theo tập test, không đo dao động do train lại, nên cần thêm kiểm tra nhiều seed.")
# ---- 4
H1("4. Cơ sở mô hình")
H2("Khối nghe")
P("**Whisper** là mô hình encoder-decoder nhận phổ log-mel, huấn luyện trên lượng lớn audio đa ngôn ngữ với giám sát yếu. **PhoWhisper** dùng kiến trúc đó và fine-tune cho tiếng Việt. Nhóm dùng bản small, khoảng 244 triệu tham số. Mô hình xử lý từng cửa sổ 30 giây, nên audio dài cần xử lý riêng.")
H2("Khối dịch")
P("**VinAI Translate vi2en-v2** là mô hình dịch Việt sang Anh. Paper của tác giả có giả lập lời ASR bằng cách viết thường và bỏ dấu câu. Đó chỉ là khác biệt hình thức, còn lời ASR thật có lỗi nghe như “Aristotle” thành “arizona”. Khoảng trống này là chỗ phương pháp đề xuất nhắm vào.")
H2("LoRA")
P("LoRA giữ nguyên ma trận trọng số gốc W và học thêm hai ma trận hạng thấp A, B:")
CT("W′ = W + (α / r) · B · A")
P("r là hạng, α là hệ số co giãn. Nhóm dùng r = 16, α = 32, áp cho q, k, v, out_proj, fc1, fc2. Số tham số huấn luyện là 8.650.752 trên 431.850.496, tức 2,0%, adapter 34,7 MB. Sau khi train, adapter được gộp vào trọng số nên lúc chạy không tốn thêm phép tính đáng kể.")
P("Nhóm chọn LoRA vì dữ liệu ít và chỉ có một GPU 8 GB. Fine-tune toàn phần 431 triệu tham số trên vài nghìn câu dễ overfit; ngay cả với LoRA, BLEU dev cũng đạt đỉnh ở epoch 1 rồi giảm.")
H2("Ý tưởng chính của phương pháp")
P("Giữ nguyên khối nghe. Chạy PhoWhisper trên FLEURS train để lấy lời ASR thật có lỗi nghe thật, ghép với câu tiếng Anh đúng, rồi dạy adapter. **Điểm mới nằm ở dữ liệu huấn luyện, không phải kiến trúc**, nhờ đó khối dịch học cách đoán ý từ đúng loại lỗi nó sẽ gặp. Cần nói rõ: LoRA chỉ ở khối dịch, nên WER khối nghe không đổi.")
# ---- 5
H1("5. Baseline, Paper vs Group, Gap Analysis")
TB([("Mô hình · tập test", "Paper", "Nhóm"), ("PhoWhisper-small · VIVOS", "WER 6,33%", "WER 6,24%, CER 3,25%"), ("PhoWhisper-small · FLEURS", "NR", "WER 13,68%, CER 9,88%"), ("Whisper-small · VIVOS", "NR", "WER 25,99%, CER 16,49%"), ("Whisper-small · FLEURS", "WER 21,2%", "WER 21,24%, CER 12,26%"), ("VinAI Translate · PhoMT", "BLEU 40,42", "BLEU 40,79"), ("Cascade PhoWhisper → B0", "NR", f"BLEU {vn(S.b0c['BLEU'])}"), ("Whisper-small end-to-end B1", "NOT RUN", f"BLEU {vn(S.b1['BLEU'])}, chrF++ {vn(S.b1['chrF++'])}")], [7, 3.4, 6])
NG("3_bang_so/asr/results_task2.csv, 3_bang_so/asr/paper_comparison.csv. NR = nguồn không báo cáo, không phải 0.")
P("Ba số có paper để đối chiếu đều khớp sát, lệch −0,09 và +0,04 điểm WER, +0,37 BLEU. Không kết luận “tái lập chính xác” vì paper không mô tả đủ chi tiết. Không lấy 6,33 trừ 21,2 để so hai mô hình vì đó là hai dataset khác nhau; phép so hợp lệ phải cùng tập test.")
P("**Gap Analysis** gồm năm giả thuyết đặt trước khi có số:")
TB([("Giả thuyết", "Kết luận", "Bằng chứng chính"), ("H1 Miền và độ dài ảnh hưởng WER", "Có bằng chứng", "VIVOS 6,24% so với FLEURS 13,68%; WER tăng theo độ dài"), ("H2 Chuẩn hoá số gây một phần gap", "Một phần", "Câu có chữ số WER 27,43% so với 5,89%"), ("H3 Checkpoint tiếng Việt giảm lỗi", "Có bằng chứng", "Chênh +19,75 trên VIVOS, +7,56 trên FLEURS"), ("H4 Beam 5 so với greedy", "Đã kiểm", "PhoWhisper 10,70 / 10,91 trên dev; giữ beam 5"), ("H5 Audio bị cắt làm thiếu từ", "Không ủng hộ", "D = 2, I = 401 / N = 472: lỗi là chèn")], [6, 2.8, 7.6])
NG("3_bang_so/asr/gap_hypotheses.csv, strata.csv, long_form_audit.csv")
P(f"**B1** là đối chứng end-to-end, kém B0 {vn(-S.db1['delta'])} BLEU, KTC 95% {ci(S.db1)}, với 86/857 câu lặp vòng khi giải mã. Đây là số của một checkpoint đa ngôn ngữ chạy nguyên bản, không phải giới hạn của mọi mô hình end-to-end. Ghi là baseline đối chứng, không nhận là tái lập paper.")
# ---- 6
H1("6. Kết quả phương pháp đề xuất")
H2("Bốn phiên bản, seed 42")
hg = [("Bản", "Thay đổi", "Dev cascade", "Dev sạch", "Test cascade", "Test sạch", "PhoMT")]
for k, m in (("B0", "VinAI gốc"), ("V1", "LoRA trên lời ASR"), ("V2", "V1 + PhoMT 1:1"), ("V3", "V2 + cân bằng"), ("V4", "V3, lr 5e-5")):
    r = next(v for q, v in ab.items() if q.startswith(k)); hg.append((k + (" ★" if k == "V2" else ""), m, vn(r["dev cascade"]), vn(r["dev sạch"]), vn(r["test cascade"]), vn(r["test sạch"]), vn(r["PhoMT test"])))
TB(hg, [1.5, 4.2, 2.1, 2, 2.2, 2, 1.8])
NG("3_bang_so/ablation/bang_ablation.csv")
P("**Đọc bảng:** bước B0 → V1 mang gần như toàn bộ cải thiện (+4,81 BLEU cascade, KTC 95% [3,75; 5,92]). V1 → V2 không tăng cascade nhưng kéo dịch sạch lên +1,88 và PhoMT lên +3,45, tức sửa lỗi quên miền gốc. V3 không cải thiện có ý nghĩa. V4 giữ được dịch sạch nhưng không hơn trên cascade.")
HI(H / "ablation_V2.png", "Hình 3. Các phiên bản và ablation, seed 42", 13.5)
H2("Failure cases")
B("**Rút gọn mất ý:** 8/361 câu dev của V1 ngắn hơn 0,7 lần tham chiếu, B0 không có câu nào. Nghĩa gần đúng nhưng mất chi tiết.", "**Quên miền gốc:** V1 tụt 2,06 BLEU ở dịch sạch và 3,83 ở PhoMT so với B0.", "**Overfit:** BLEU dev đỉnh ở epoch 1 rồi giảm.", "**Lan truyền không sửa được:** “Aristotle” nghe thành “arizona” thì khối dịch không có thông tin để sửa.", "**Kém hơn baseline:** thuật ngữ “maria” bị V2 dịch thành “coast”, B0 giữ được “marina”.")
P("Nhóm câu khối nghe sai nhiều cải thiện mạnh nhất: câu sai ≥ 30% tăng +8,15, câu có chữ số +7,43, còn nhóm nghe tốt chỉ +0,84. Đây là bằng chứng phương pháp hoạt động đúng cơ chế dự kiến.")
NG("3_bang_so/mt/failure_V1_dev.md, failure_V2_dev.md")
HI(H / "visual_results_tot.png", "Hình 4. Ví dụ V2 tốt hơn B0, chữ giữ nguyên trong file kết quả")
HI(H / "visual_results_loi.png", "Hình 5. Hai ca lỗi còn lại, chọn có chủ đích để thấy giới hạn")
H2("Chọn bản cuối và ablation")
P(f"Quy tắc ban đầu là BLEU dev cascade cao nhất, cho ra V3. Vì chênh lệch dev rất nhỏ, ngày 03/11/2026 nhóm chốt lại: bản cách đỉnh không quá 0,5 BLEU là hoà, trong nhóm hoà chọn dev sạch cao nhất, ra **V2** ({vn(ab['V2']['dev sạch'])}). **Quy tắc này chốt sau khi đã thấy số test của V1–V4**, nên không được viết là lựa chọn mù với test.")
hg = [("Bản", "Test cascade, 3 seed", "Test sạch, 3 seed", "So với V2 cùng seed")]
for k, m in (("V2", "V2 ★"), ("A_r8", "A_r8: rank 8"), ("A_r32", "A_r32: rank 32"), ("A_aug", "A_aug: thêm transcript sạch")):
    hg.append((m, B3.vi(k, "test cascade"), B3.vi(k, "test sạch"), "–" if k == "V2" else B3.d(k, "test cascade").replace(".", ",").replace("-", "−")))
TB(hg, [5.5, 4, 3.8, 3.3])
NG("3_bang_so/ba_seed/bang_ablation_3seed.csv")
P("Ablation đổi đúng một yếu tố so với V2. Đổi rank không tạo khác biệt rõ, chênh lệch nhỏ và đổi dấu giữa các seed. Thêm transcript sạch kém V2 ở cả ba seed. V1–V4 là các phiên bản nối tiếp, không gọi là ablation một yếu tố.")
H2("Kiểm tra 3 seed")
hg = [("Bản", "Dev cascade", "Dev sạch", "Test cascade", "Test sạch")]
for k in ("V1", "V2", "V3", "V4"):
    hg.append((k + (" ★" if k == "V2" else ""), B3.vi(k, "dev cascade"), B3.vi(k, "dev sạch"), B3.vi(k, "test cascade"), B3.vi(k, "test sạch")))
TB(hg, [2, 3.6, 3.6, 3.6, 3.6])
NG("3_bang_so/ba_seed/bang_3seed.csv, ket_qua_3seed.json. Trung bình ± độ lệch chuẩn của seed 42, 1, 2.")
P(f"V2 hơn B0 **+{vn(D_TB)} ± {vn(D_SD)} BLEU**, và áp quy tắc trên trung bình dev vẫn ra V2. Lợi thế dev của V3 ở seed 42 không lặp lại. V1 có test cascade trung bình cao hơn V2 nhưng nhóm không chọn theo test. Seed 1, 2 train trên Modal bằng torch 2.7.1, dịch và chấm bằng torch 2.0.1 như seed 42. Train lại V2 seed 42 trên Modal làm dev cascade đổi 26,45 → 25,66, nên môi trường train ảnh hưởng gần bằng seed. Chỉ có 3 seed nên số này cho biết mức dao động, chưa đủ cho kết luận thống kê riêng.")
HI(EXP / "ba_seed/bieu_do_3seed.png", "Hình 6. Trung bình 3 seed, thanh sai là độ lệch chuẩn", 13)
# ---- 7
H1("7. Sản phẩm, độ bền và tính khả thi")
P(f"Audio dài hơn 30 giây nếu đưa thẳng vào khối nghe có WER 94,70% do chèn chữ. Sản phẩm chia đoạn không quá 28 giây tại chỗ ngắt nghỉ, bỏ cụm lặp ở chỗ nối và đổi số đọc thành chữ số trước khi dịch. Trên 857 bản, cả hệ đạt **WER {vn(S.tat['WER_asr'])}%, BLEU {vn(S.tat['BLEU'])}, chrF++ {vn(S.tat['chrF++'])}**. So với xử lý cũ, BLEU tăng {vn(S.hb['delta'])}, KTC 95% {ci(S.hb)}, chưa có ý nghĩa thống kê. Riêng câu có chữ số tăng {vn(S.hb['cau_co_chu_so']['BLEU_A'])} → {vn(S.hb['cau_co_chu_so']['BLEU_B'])}, 10 bản dài hơn 28 giây tăng {vn(S.ht['truoc_0411']['dai']['BLEU'])} → {vn(S.dai['BLEU'])}, WER {vn(S.dai['WER_asr'])}%.")
NG("3_bang_so/he_thong_V2/ket_qua.json, bootstrap_cu_vs_moi.json")
P(f"**Độ bền khối nghe**, chỉ đo, không fine-tune: WER gốc {wer('goc')}%, nhiễu 20 dB {wer('noise_snr20')}%, nhiễu 10 dB {wer('noise_snr10')}%, tốc độ 0,9 {wer('speed_0.9')}%, tốc độ 1,1 {wer('speed_1.1')}%, giảm 12 dB {wer('vol_-12dB')}%. Đây là nhiễu nhân tạo, chỉ cho biết xu hướng.")
HI(EXP / "robust/bang_robust.png", "Hình 7. Độ bền PhoWhisper-small trên 857 bản FLEURS test", 12.5)
TB([("Tiêu chí", "Ngưỡng", "Kết quả V2", "Đạt?"), ("Cải thiện so với baseline cascade", "có ý nghĩa", f"+{vn(S.d['delta'])} {ci(S.d)}", "Đạt"), ("Cải thiện với khối nghe thứ hai", "có ý nghĩa", f"+{vn(S.dw['delta'])} {ci(S.dw)}", "Đạt"), ("Thu hẹp khoảng cách với văn bản chuẩn", "giảm so với B0", f"15,58 → {gap}", "Đạt"), ("Không giảm BLEU dịch văn bản chuẩn", "≥ 38,27", f"{vn(S.cl['BLEU'])} (trung bình 3 seed {vn(B3.m('V2', 'test sạch'))})", "Chưa đạt"), ("Nhanh hơn thời gian thực", "RTF < 1", vn(t2["rtf"], 3), "Đạt"), ("Độ trễ p95", "≤ 5 s", f"{vn(t2['p95'])} s", "Đạt"), ("VRAM đỉnh", "≤ 8 GiB", f"{vn(t2['vram'])} GiB", "Đạt")], [6.6, 2.8, 5.4, 1.8])
NG("3_bang_so/toc_do/, 3_bang_so/mt/bootstrap_B0_V2_cascade_test.json, bootstrap_B0_V2_cascade_wsp_test.json")
P("Kết luận: khả thi để đóng gói thành ứng dụng web chạy GPU, 6/7 tiêu chí có ngưỡng đạt. Tiêu chí dịch văn bản chuẩn chưa đạt ở cả ba seed, không diễn giải lại ngưỡng. Adapter không làm chậm hệ: chênh RTF giữa B0 và V2 nằm trong dao động giữa các lần đo.")
# ---- 8
H1("8. Hạn chế phải nêu")
B("Số chính đo trên audio đọc rõ, một người nói. Dev và test FLEURS 100% giọng nam.", "Adapter gắn với lỗi của khối nghe dùng khi huấn luyện: tăng +4,78 với PhoWhisper nhưng chỉ +1,10 với Whisper-small.", "Docker, GitHub Actions, micro thật, 20 câu tự thu, m4a và webm **chưa chạy thật**. Không viết là đã chạy.", "Demo và API đã chạy với model thật. Nghiệm thu đạt 6/7 mục, mục còn lại trượt vì máy không có ffmpeg.", "So B1 với paper đang là NOT RUN.")
# ---- 9
H1("9. Những cách viết phải tránh")
TB([("Không viết", "Viết đúng"), ("Chỉ xem test sau khi chọn", "Quy tắc chỉ dùng số dev nhưng chốt sau khi đã thấy test V1–V4"), ("V2 tốt nhất trên test", "V2 được chọn theo dev; V1 có test cascade trung bình cao hơn"), ("LoRA cải thiện ASR", "LoRA chỉ ở khối dịch, WER khối nghe không đổi"), ("V1–V4 là ablation", "V1–V4 là phiên bản nối tiếp; ablation là A_r8, A_r32, A_aug"), ("Tái lập chính xác paper", "Khớp sát với số paper, không tuyên bố tái lập chính xác"), ("Đạt mọi tiêu chí", "6/7 tiêu chí có ngưỡng đạt, dịch văn bản chuẩn chưa đạt"), ("Hệ chạy streaming thời gian thực", "Chưa đo ở chế độ streaming"), ("Docker và CI đã chạy", "Đã viết cấu hình, chưa chạy thật")], [6.8, 9.8])
# ---- 10
H1("10. Câu hỏi vấn đáp dễ gặp")
for q, a in (("Vì sao không làm end-to-end?", "Dữ liệu audio kèm bản dịch quá ít so với dữ liệu riêng từng khối. B1 chạy nguyên bản chỉ đạt BLEU 3,80."), ("Điểm mới ở đâu?", "Ở dữ liệu huấn luyện: dạy khối dịch bằng lời ASR thật, không phải lời giả lập."), ("Vì sao không fine-tune khối nghe?", "Khối nghe đã khớp paper, chi phí cao hơn nhiều so với adapter 34,7 MB, và lỗi lan truyền xử lý được ở khối dịch."), ("Vì sao chọn V2 mà không chọn V1 có test cao hơn?", "Không chọn theo test. Theo dev, V1 và V2 hoà và V2 có dev sạch cao hơn, giữ được chất lượng dịch văn bản chuẩn."), ("Vì sao cần 3 seed khi đã có bootstrap?", "Bootstrap đo dao động theo tập test, không đo dao động do train lại."), ("Sao không có Kappa?", "Không có hai người gán nhãn độc lập cùng một tập câu.")):
    P(f"**{q}** {a}")
# ---- 11
H1("11. Bản đồ minh chứng theo khung slide của thầy")
TB([("Slide", "Nội dung", "Mục tài liệu", "File và hình"), ("1–2", "Tiêu đề, Agenda", "Mở đầu", "Mã nhóm, GVHD nhóm tự điền"), ("3", "Nguồn dữ liệu", "Mục 2", "3_bang_so/data/nguon_du_lieu.md"), ("4", "Làm sạch, gán nhãn", "Mục 2", "2_hinh/tong_hop/flowchart_lam_sach.png"), ("5", "Mất cân bằng", "Mục 2", "2_hinh/du_lieu/eda/"), ("6", "Kết quả xử lý, biểu đồ", "Mục 2", "2_hinh/du_lieu/can_bang/"), ("7", "Cấu hình môi trường", "Mục 4, 5", "5_tham_khao/README.md"), ("8", "Paper vs Group", "Mục 5", "3_bang_so/asr/paper_comparison.csv"), ("9", "Gap Analysis", "Mục 5", "3_bang_so/asr/gap_hypotheses.csv"), ("10", "Kiến trúc V1", "Mục 4", "2_hinh/kien_truc_va_vi_du/kien_truc_he_thong.png"), ("11", "Kết quả V1", "Mục 6", "3_bang_so/ablation/bang_ablation.csv"), ("12", "Failure cases", "Mục 6", "3_bang_so/mt/failure_V1_dev.md, 2_hinh/asr/"), ("13", "Đề xuất V2", "Mục 6", "3_bang_so/mt/failure_V1_dev.md"), ("14", "Bảng ablation tổng hợp", "Mục 6", "2_hinh/kien_truc_va_vi_du/ablation_V2.png, 3_bang_so/ba_seed/"), ("15", "Visual results", "Mục 6", "2_hinh/kien_truc_va_vi_du/visual_results_*.png"), ("16", "Đánh giá khả thi", "Mục 7", "3_bang_so/toc_do/, he_thong_V2/"), ("17", "Kế hoạch Task 3", "Mục 7, 8", "5_tham_khao/KIEM_THU_CUOI.md, VIEC_CON_LAI.md"), ("18", "Cảm ơn và Q&A", "Mục 10", "–")], [1.3, 4.4, 2, 8.9])
H1("12. Bản đồ minh chứng theo checklist của thầy")
TB([("Hạng mục", "Trạng thái", "Bằng chứng trong gói"), ("Bảng thống kê nguồn dữ liệu", "Xong", "3_bang_so/data/nguon_du_lieu.md"), ("Quy trình làm sạch và gán nhãn", "Xong", "3_bang_so/data/lam_sach_dem_tung_buoc.csv"), ("Phân tích mất cân bằng", "Xong", "2_hinh/du_lieu/eda/, 4_notebook/eda.ipynb"), ("Xử lý mất cân bằng, biểu đồ trước/sau", "Xong", "2_hinh/du_lieu/can_bang/"), ("Baseline 1, Baseline 2", "Xong", "3_bang_so/asr/results_task2.csv"), ("Bảng Paper vs Thực nghiệm", "Xong", "3_bang_so/asr/paper_comparison.csv"), ("Gap Analysis", "Xong", "3_bang_so/asr/gap_hypotheses.csv"), ("Proposed V1", "Xong", "3_bang_so/ablation/bang_ablation.csv"), ("Failure case analysis", "Xong", "3_bang_so/mt/failure_V1_dev.md"), ("V2 và các bản tiếp theo", "Xong", "3_bang_so/ablation/, 3_bang_so/ba_seed/"), ("Bảng ablation tổng hợp", "Xong", "3_bang_so/ablation/bang_ablation.csv"), ("Latency, model size", "Xong", "3_bang_so/toc_do/"), ("Slide 18–25 trang", "Nhóm làm", "Khung ở DOC_TRUOC.md"), ("(RAG) Docker, microservices, CI/CD", "Đang làm", "Đã viết cấu hình, chưa chạy thật: 5_tham_khao/KIEM_THU_CUOI.md"), ("(Nếu có) Paper Springer 6–8 trang", "Nhóm quyết", "Số liệu trong gói này")], [6.3, 2, 8.3])
H1("13. Tài liệu tham khảo chính")
for x in ("A. Radford et al., “Robust speech recognition via large-scale weak supervision,” in Proc. ICML, 2023, pp. 28492–28518.", "T.-T. Le, L. T. Nguyen, and D. Q. Nguyen, “PhoWhisper: Automatic speech recognition for Vietnamese,” in Proc. ICLR 2024 Tiny Papers, 2024.", "T. H. Nguyen et al., “A Vietnamese-English neural machine translation system,” in Proc. Interspeech, 2022, pp. 5543–5544.", "L. Doan et al., “PhoMT: A high-quality and large-scale benchmark dataset for Vietnamese–English machine translation,” in Proc. EMNLP, 2021, pp. 4495–4503.", "E. J. Hu et al., “LoRA: Low-rank adaptation of large language models,” in Proc. ICLR, 2022.", "A. Conneau et al., “FLEURS: Few-shot learning evaluation of universal representations of speech,” in Proc. IEEE SLT, 2023, pp. 798–805.", "M. Post, “A call for clarity in reporting BLEU scores,” in Proc. WMT, 2018, pp. 186–191.", "M. Popović, “chrF++: words helping character n-grams,” in Proc. WMT, 2017, pp. 612–618."):
    d.add_paragraph(x, style="List Number")
d.save(O / "TAI_LIEU_KY_THUAT_BAO_UYEN.docx"); print("xong")
