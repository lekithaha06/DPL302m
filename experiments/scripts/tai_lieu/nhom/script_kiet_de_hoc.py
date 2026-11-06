#!/usr/bin/env python3
"""Bản học thuyết trình cho Kiệt: slide 10–15, giải thích khái niệm, lời nói, số cần nhớ, câu hỏi."""
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

d = Document()
s = d.sections[0]; s.page_width, s.page_height = Cm(21), Cm(29.7); s.left_margin = s.right_margin = Cm(2.2); s.top_margin = s.bottom_margin = Cm(2)
XANH = RGBColor(0x1F, 0x27, 0x66); XAM = RGBColor(0x55, 0x5B, 0x66)
st = d.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(12); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri"); st.paragraph_format.space_after = Pt(6); st.paragraph_format.line_spacing = 1.15
for n, z, b in (("Title", 22, 0), ("Heading 1", 16, 14), ("Heading 2", 13, 10)):
    x = d.styles[n]; x.font.name = "Calibri"; x.font.size = Pt(z); x.font.bold = True; x.font.color.rgb = XANH; x.paragraph_format.space_before = Pt(b); x.paragraph_format.space_after = Pt(5); x.paragraph_format.keep_with_next = True
    rf = x.element.rPr.find(qn("w:rFonts"))
    if rf is not None:
        for k in list(rf.attrib):
            del rf.attrib[k]
        rf.set(qn("w:ascii"), "Calibri"); rf.set(qn("w:hAnsi"), "Calibri"); rf.set(qn("w:eastAsia"), "Calibri")


def chay(p, t, co=None):
    for i, c in enumerate(t.split("**")):
        r = p.add_run(c); r.bold = i % 2 == 1
        if co:
            r.font.size = Pt(co)


def P(t):
    chay(d.add_paragraph(), t)


def B(*ds):
    for t in ds:
        chay(d.add_paragraph(style="List Bullet"), t)


def nen(o, mau):
    sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:fill"), mau); o._tc.get_or_add_tcPr().append(sh)


def NOI(*cau):
    """Khung lời nói."""
    t = d.add_table(rows=1, cols=1); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER; o = t.cell(0, 0); nen(o, "EEF3FB")
    for i, c in enumerate(cau):
        p = o.paragraphs[0] if i == 0 else o.add_paragraph(); p.paragraph_format.space_after = Pt(5); chay(p, c)
    d.add_paragraph().paragraph_format.space_after = Pt(2)


def TB(hang, rong):
    t = d.add_table(rows=len(hang), cols=len(hang[0])); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(hang):
        for j, v in enumerate(h):
            o = t.cell(i, j); o.width = Cm(rong[j]); p = o.paragraphs[0]; p.paragraph_format.space_after = Pt(1)
            if i == 0:
                r = p.add_run(v); r.bold = True; r.font.size = Pt(10.5); r.font.color.rgb = RGBColor(255, 255, 255); nen(o, "1F2766")
            else:
                chay(p, v, 10.5)
    t.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    d.add_paragraph().paragraph_format.space_after = Pt(2)


d.add_paragraph("Bản học thuyết trình của Kiệt", style="Title")
P("Phần của bạn: **slide 10 đến 15**, khoảng **7 phút**. Tài liệu này giải thích từ đầu, không cần biết trước về AI.")
P("**Cách học nhanh:** đọc Phần 1 và 2 để hiểu chuyện gì đang xảy ra, học thuộc số ở Phần 4, rồi vừa mở slide vừa đọc to Phần 3 ba lần. Không cần thuộc từng chữ, chỉ cần nói đúng ý và đúng số.")

d.add_heading("Phần 1. Hiểu dự án bằng một ví dụ", 1)
P("Hãy tưởng tượng hệ thống của nhóm là **hai người làm việc nối tiếp nhau**:")
B("**Người chép lời** nghe tiếng Việt rồi ghi thành chữ tiếng Việt. Đây là **PhoWhisper**.", "**Người phiên dịch** đọc chữ tiếng Việt rồi dịch sang tiếng Anh. Đây là **VinAI Translate**.")
P("Vấn đề: người chép lời đôi khi nghe sai. Ví dụ nghe “Byzantine” thành “bikini tin”. Người phiên dịch nhận chữ sai nên dịch sai. Chép chuẩn thì dịch được **38,27 điểm**, còn nhận chữ có lỗi chỉ được **22,69 điểm**.")
P("**Ý tưởng của nhóm:** không dạy lại người chép lời, mà **dạy người phiên dịch quen với chữ có lỗi**, để nhìn chữ sai vẫn đoán đúng ý. Kết quả: **22,69 tăng lên 27,47**.")
P("Toàn bộ phần của bạn chỉ kể đúng câu chuyện đó.")

d.add_heading("Giải thích từng từ khó", 2)
TB([("Từ", "Là gì", "Nói dễ hiểu"),
    ("Whisper", "Mô hình nhận dạng giọng nói của OpenAI", "Nghe nhiều thứ tiếng rồi ghi ra chữ"),
    ("PhoWhisper", "Whisper được luyện thêm riêng cho tiếng Việt", "Người chép lời chuyên tiếng Việt. Nhóm dùng nguyên, **không train**"),
    ("VinAI Translate", "Mô hình dịch Việt sang Anh", "Người phiên dịch. Đây là phần nhóm dạy thêm"),
    ("FLEURS", "Bộ dữ liệu giọng nói của Google, nhiều ngôn ngữ", "Có audio người Việt đọc câu, và có câu tiếng Anh tương ứng"),
    ("FLEURS train", "Phần dùng để dạy: 2.926 bản thu", "Bài tập cho mô hình luyện"),
    ("Dev", "Phần dùng để chọn bản tốt: 361 bản thu", "Bài kiểm tra thử"),
    ("Test", "Phần chấm điểm cuối: 857 bản thu", "Đề thi thật, không dùng để học"),
    ("PhoMT", "Bộ gần 3 triệu cặp câu Việt–Anh", "Sách luyện dịch câu bình thường"),
    ("Cascade", "Nối khối nghe với khối dịch", "Hai người làm nối tiếp"),
    ("LoRA", "Cách dạy thêm một phần rất nhỏ, giữ nguyên mô hình gốc", "Không viết lại cả cuốn sách, chỉ thêm một cuốn sổ tay nhỏ"),
    ("Adapter", "Phần LoRA học được, 34,7 MB", "Chính là cuốn sổ tay đó"),
    ("Epoch", "Học hết dữ liệu dạy một lượt", "Làm hết bộ bài tập một lần"),
    ("Overfit", "Học thuộc bài tập, làm bài mới kém đi", "Học vẹt"),
    ("BLEU", "Điểm bản dịch giống câu mẫu tới đâu, từ 0 đến 100", "Điểm dịch, càng cao càng tốt, chỉ so trên cùng một đề"),
    ("WER", "Tỉ lệ từ nghe sai", "Điểm lỗi nghe, càng thấp càng tốt"),
    ("B0", "VinAI gốc, chưa thêm LoRA", "Bản gốc để so sánh"),
    ("Dịch sạch", "Dịch câu tiếng Việt chuẩn, không có lỗi nghe", "Kiểm tra xem có quên cách dịch bình thường không"),
    ("Khoảng tin cậy (KTC)", "Khoảng mà mức tăng thật có khả năng nằm trong đó", "Không chứa 0 nghĩa là tăng thật, không phải may"),
    ("Bootstrap", "Lấy mẫu lại đề thi 1.000 lần rồi tính lại", "Đổi đề 1.000 lần xem kết quả có bền không"),
    ("Seed", "Số khởi tạo ngẫu nhiên khi train", "Train lại với điểm xuất phát khác"),
    ("Ablation", "Đổi đúng một thứ để xem thứ đó tác dụng ra sao", "Thử bỏ hoặc đổi từng nguyên liệu")], [3.2, 6.8, 6.6])

d.add_heading("Câu chuyện V1 đến V4", 2)
TB([("Bản", "Làm gì", "Kết quả, nói ngắn"),
    ("V1", "Dạy trên lời có lỗi nghe thật", "Dịch lời có lỗi tốt lên rõ, nhưng **quên** cách dịch câu chuẩn"),
    ("V2 ★", "V1 + 4.468 cặp câu PhoMT", "Giữ điểm tốt và **nhớ lại** cách dịch chuẩn. Đây là bản cuối"),
    ("V3", "V2 + cân bằng dữ liệu", "Không hơn V2"),
    ("V4", "V3 + học chậm lại (lr 5e-5)", "Không hơn V2 có ý nghĩa")], [2, 7, 7.6])

d.add_heading("Phần 2. Bốn ý phải nhớ", 1)
for t in ("**Khối nghe giữ nguyên, chỉ dạy khối dịch.** Vì vậy WER không đổi, vẫn 13,68%.", "**Điểm mới nằm ở dữ liệu dạy:** dùng lỗi nghe thật, không đổi kiến trúc.", "**V1 tăng mạnh nhưng quên cách dịch chuẩn, V2 sửa được.** V2 là bản cuối.", "**Phải nói thật ba điều:** quy tắc chọn chốt sau khi đã thấy test; V1 có test cao hơn nhưng không chọn theo test; tiêu chí dịch câu chuẩn chưa đạt."):
    chay(d.add_paragraph(style="List Number"), t)

d.add_heading("Phần 3. Lời nói từng slide", 1)
P("Phần trong khung xanh là lời nói. Chữ trong ngoặc vuông là động tác, không đọc ra.")
d.add_heading("Slide 10. Kiến trúc V1 · khoảng 1 phút 15", 2)
P("**Ý chính:** khối nghe giữ nguyên, dạy khối dịch bằng lỗi nghe thật.")
NOI("Dạ, em là Kiệt. Ý tưởng của nhóm rất đơn giản: **khối nghe giữ nguyên, mình dạy khối dịch cách đọc hiểu lời có lỗi.**",
    "[Chỉ hàng trên] Khi huấn luyện, nhóm cho PhoWhisper nghe 2.926 bản thu FLEURS. Lời nó ghi ra có lỗi nghe thật, ví dụ “Byzantine” thành “bikini tin”. Nhóm ghép lời có lỗi đó với câu tiếng Anh đúng, rồi dạy VinAI Translate.",
    "[Chỉ hàng dưới] Lúc chạy thật, luồng vẫn như cũ, chỉ là khối dịch có thêm adapter.",
    "Khác baseline ở đâu? Paper VinAI chỉ giả lập lời ASR bằng cách viết thường và bỏ dấu câu. Nhóm dạy bằng đúng loại lỗi sẽ gặp. **Điểm mới nằm ở dữ liệu dạy, không phải kiến trúc.**",
    "Nhóm dùng LoRA: giữ nguyên trọng số gốc, chỉ học thêm hai ma trận nhỏ, khoảng 2% tham số, adapter 34,7 MB. Lý do là dữ liệu ít và chỉ có một GPU 8 GB.")
d.add_heading("Slide 11. Kết quả V1 · khoảng 1 phút", 2)
P("**Ý chính:** V1 tăng 4,81 điểm là có thật, nhưng phải đánh đổi.")
NOI("Trên cùng 857 bản thu test, BLEU cascade tăng từ **22,69 lên 27,49**, tức **tăng 4,81 điểm**.",
    "Nhóm chạy bootstrap 1.000 lần, khoảng tin cậy từ 3,75 đến 5,92, không chứa 0, nên đây là cải thiện có ý nghĩa. chrF++ cũng tăng từ 49,38 lên 52,50.",
    "Nhưng có đánh đổi. [Chỉ hai dòng cuối] Dịch câu chuẩn kém bản gốc 2,06 điểm, PhoMT kém 3,83 điểm. Tức là khối dịch học được lời có lỗi nhưng **quên bớt cách dịch câu bình thường**. WER vẫn 13,68% vì nhóm không đụng vào khối nghe.")
d.add_heading("Slide 12. Failure cases · khoảng 1 phút 15", 2)
P("**Ý chính:** V1 có ba lỗi, nhưng câu nghe sai nhiều lại được cải thiện nhiều nhất.")
NOI("V1 có các loại lỗi chính.", "Một là **overfit**. [Chỉ biểu đồ] BLEU dev cao nhất ở epoch 1 là 26,47, rồi giảm dần còn 23,64. Nên nhóm chọn checkpoint epoch 1.",
    "Hai là **rút gọn mất ý**. Câu này khối nghe nghe đúng, nhưng V1 dịch gọn lại nên mất chi tiết.", "Ba là **lỗi nghe lan truyền**. Khối nghe ghi “bikini tin” thay cho Byzantine, khối dịch không có thông tin để sửa.",
    "Ngoài ra là quên miền gốc như em vừa nói.", "[Chỉ bảng] Điểm tích cực: nhóm câu nghe sai từ 30% trở lên tăng từ 7,86 lên 16,01, gần gấp đôi. Nhóm câu nghe tốt gần như không đổi. Tức là phương pháp hoạt động đúng cơ chế dự kiến.")
d.add_heading("Slide 13. Đề xuất V2 và các bản sau · khoảng 1 phút 15", 2)
P("**Ý chính:** mỗi bản sửa một lỗi. V2 có tác dụng, V3 và V4 không hơn.")
NOI("Từ các lỗi đó, nhóm làm ba phiên bản, mỗi bản đổi một thứ.", "**V2** sửa lỗi quên miền gốc: trộn thêm 4.468 cặp PhoMT. BLEU cascade giữ 27,47, còn dịch câu chuẩn hồi lại **38,09**, PhoMT hồi lại **40,41**.",
    "**V3** thay phần FLEURS bằng bản cân bằng. **V4** giảm learning rate vì mô hình học quá nhanh. Cả hai đều không hơn V2 một cách có ý nghĩa.", "Em lưu ý V1 đến V4 là các phiên bản nối tiếp. Ablation đổi đúng một yếu tố so với V2, nằm ở slide sau.")
d.add_heading("Slide 14. Bảng tổng hợp và chọn bản cuối · khoảng 1 phút 15", 2)
P("**Ý chính:** chọn V2 bằng số dev, và nói thật về thời điểm chốt quy tắc.")
NOI("[Chỉ biểu đồ] Bước từ baseline lên V1 là bước nhảy lớn nhất. Từ V1 tới V4 gần như đi ngang, quanh 27,3 đến 27,5.",
    "Ba dòng cuối là ablation so với V2. Đổi rank xuống 8 hay lên 32 không tạo khác biệt rõ. Thêm augmentation thì kém hơn, còn 25,49.",
    "Chọn bản cuối thế nào? Nhóm dùng số dev. Bản nào cách đỉnh dev không quá 0,5 điểm thì coi là hoà, là V1 đến V4. Trong nhóm hoà, bản dịch câu chuẩn tốt nhất trên dev là **V2**.",
    "Nhóm nói thẳng: quy tắc này chốt **sau khi đã thấy số test** của V1 đến V4. Quy tắc ban đầu ra V3. Vì vậy đây không phải lựa chọn mù với test.")
d.add_heading("Slide 15. Kiểm tra 3 seed · khoảng 1 phút 15", 2)
P("**Ý chính:** train lại với seed khác, V2 vẫn thắng baseline và vẫn được chọn.")
NOI("Bootstrap chỉ cho biết kết quả dao động theo tập test. Muốn biết train lại có giữ được không, nhóm train thêm seed 1 và 2 cho cả bốn phiên bản và ba bản ablation, tính cả seed 42 là 21 adapter.",
    "[Chỉ ô +4,65] V2 hơn baseline ở cả ba seed, trung bình **hơn 4,65 điểm**, độ lệch chỉ 0,12. Áp lại quy tắc trên trung bình dev thì **vẫn ra V2**.",
    "Có hai điểm phải nói rõ. Một là V1 có test trung bình cao hơn V2, 27,83 so với 27,34, nhưng nhóm không chọn theo test. Hai là tiêu chí dịch câu chuẩn **chưa đạt**: không seed nào đạt, trung bình thiếu 0,47 điểm.", "Em xin chuyển cho bạn Đăng.")

d.add_heading("Phần 4. Số phải thuộc", 1)
TB([("Số", "Nghĩa"), ("**2.926**", "bản thu FLEURS dùng để dạy"), ("**857**", "bản thu test"), ("**38,27 → 22,69**", "dịch chữ chuẩn so với dịch lời có lỗi, mất 15,58"), ("**22,69 → 27,49**", "B0 lên V1, tăng 4,81, KTC [3,75; 5,92]"),
    ("**27,47**", "BLEU cascade của V2, bản cuối"), ("**38,09 và 40,41**", "V2 dịch câu chuẩn và PhoMT"), ("**13,68%**", "WER khối nghe, không đổi"), ("**2% · 34,7 MB**", "phần LoRA phải train và dung lượng adapter"), ("**r = 16, α = 32**", "cấu hình LoRA"), ("**0,5**", "ngưỡng coi là hoà khi chọn bản"), ("**+4,65 ± 0,12**", "V2 hơn B0, trung bình 3 seed"), ("**27,34 ± 0,12**", "V2 trung bình 3 seed"), ("**thiếu 0,47**", "tiêu chí dịch câu chuẩn chưa đạt")], [5, 11.6])

d.add_heading("Phần 5. Câu hỏi thầy dễ hỏi bạn", 1)
for q, a in (("Điểm mới của nhóm là gì?", "Dạy khối dịch bằng lời ASR thật có lỗi nghe thật, thay vì chỉ viết thường và bỏ dấu câu như paper VinAI."), ("LoRA có làm khối nghe tốt hơn không?", "Không. LoRA chỉ ở khối dịch, WER vẫn 13,68%."),
             ("LoRA hoạt động thế nào?", "Giữ nguyên trọng số gốc, học thêm hai ma trận nhỏ A và B. Công thức: W′ = W + (α / r) · B · A."), ("Sao chọn V2 mà không chọn V1 có test cao hơn?", "Nhóm không chọn theo test. Theo dev, V1 và V2 hoà, V2 dịch câu chuẩn tốt hơn. Quy tắc chốt sau khi đã thấy test, nhóm nói rõ điều đó."),
             ("V2 không tăng so với V1, sao gọi là cải tiến?", "V2 giữ được cascade (27,47 so với 27,49) nhưng kéo dịch câu chuẩn từ 36,21 lên 38,09, PhoMT từ 36,96 lên 40,41."), ("Đã có bootstrap sao còn chạy 3 seed?", "Bootstrap đo dao động theo tập test, không đo dao động khi train lại."),
             ("Seed 1, 2 chạy máy khác thì so được không?", "Train trên Modal nhưng dịch và chấm đúng môi trường của seed 42. Môi trường có ảnh hưởng: train lại V2 seed 42 trên Modal làm dev đổi từ 26,45 thành 25,66. Nhóm ghi rõ điều này."),
             ("Sao augmentation kém hơn?", "Nhóm phỏng đoán thêm transcript sạch giả dạng ASR làm loãng tín hiệu lỗi nghe thật. Kết quả chắc chắn là kém V2 ở cả 3 seed, trung bình −1,72."), ("Sao 27,49 trừ 22,69 lại ra +4,81?", "Vì tính trên số chưa làm tròn: 27,4948 trừ 22,6893 bằng 4,8055."),
             ("Train mất bao lâu?", "Khoảng 3 đến 18 phút mỗi epoch tuỳ bản, V2 khoảng 6,6 phút. VRAM đỉnh 5,58 GiB."), ("BLEU 27,47 là cao hay thấp?", "Paper không báo số cascade để so. Mốc tham khảo là dịch câu chuẩn 38,27, khoảng cách giảm từ 15,58 xuống 10,80.")):
    p = d.add_paragraph(); p.paragraph_format.keep_with_next = True; chay(p, f"**Hỏi: {q}**"); P("Đáp: " + a)
P("**Nếu không biết câu trả lời:** nói “Phần này nhóm chưa đo, nên nhóm không dám kết luận.” Không đoán số.")
d.save(r"D:\CAIDCM\teamwork\BAN_NOP_CUOI\Script_Kiet_de_hoc.docx"); print("xong")
