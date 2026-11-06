#!/usr/bin/env python3
"""Sắp xếp slide nhóm theo khung 4 chương của thầy. Chạy sau slide.py. Không đổi số liệu, chỉ tách, gộp, đổi thứ tự."""
import copy
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches, Pt
from chung import *

F = O / "2_slide/Slide_Project_Nhom.pptx"
pr = Presentation(F); SL = list(pr.slides); assert len(SL) == 19
s_ = lambda n: SL[n - 1]
HA = EX_HINH = TW / "repo_cuoi/experiments/reports/data/can_bang"


def dong(sh, lines):
    tf = sh.text_frame; P = list(tf.paragraphs)
    while len(P) < len(lines):
        P[-1]._p.addnext(copy.deepcopy(P[-1]._p)); P = list(tf.paragraphs)
    for p in P[len(lines):]:
        p._p.getparent().remove(p._p)
    for p, t in zip(tf.paragraphs, lines):
        R = p.runs; R[0].text = t
        for r in R[1:]:
            r._r.getparent().remove(r._r)


def tim_s(sl, dau):
    k = [x for x in sl.shapes if x.has_text_frame and x.text_frame.text.startswith(dau)]
    assert k, dau
    return k[0]


def bo(sl, *dau):
    for d in dau:
        e = tim_s(sl, d)._element; e.getparent().remove(e)


def bo_tu_sau(sl, ids):
    S = list(sl.shapes)
    for i in sorted(ids, reverse=True):
        S[i]._element.getparent().remove(S[i]._element)


def dat(sh, x, y, w=None, h=None):
    sh.left, sh.top = Inches(x), Inches(y)
    if w:
        sh.width = Inches(w)
    if h:
        sh.height = Inches(h)


def co(sh, pt):
    for p in sh.text_frame.paragraphs:
        for r in p.runs:
            r.font.size = Pt(pt)


def tieu(sl, ten, phu):
    S = list(sl.shapes); dong(S[0], [ten]); dong(S[1], [phu])


def nhan(sl):
    n = pr.slides.add_slide(sl.slide_layout)
    for e in list(n.shapes._spTree):
        if e.tag.endswith(("}sp", "}pic", "}graphicFrame")):
            n.shapes._spTree.remove(e)
    for x in sl.shapes:
        if x.shape_type == 13:
            n.shapes.add_picture(BytesIO(x.image.blob), x.left, x.top, x.width, x.height)
        else:
            n.shapes._spTree.append(copy.deepcopy(x._element))
    return n


def ghi_chu(sl, t):
    sl.notes_slide.notes_text_frame.text = t


# ---- bản sao lấy từ slide gốc, làm trước khi sửa
s_cb = nhan(s_(5)); s_mt = nhan(s_(6)); s_v2 = nhan(s_(10)); s_t3 = nhan(s_(19))
# ---- 2 Agenda
S = s_(2); L = list(S.shapes); tieu(S, "Agenda", "Input: audio tiếng Việt · Output: transcript tiếng Việt và bản dịch tiếng Anh kèm mốc thời gian · miền ứng dụng: Giáo dục")
for i, (a, b) in zip((7, 11, 15, 19), (("Chương I: Dữ liệu", "nguồn dữ liệu · làm sạch và gán nhãn · mất cân bằng · kết quả xử lý"), ("Chương II: Baseline", "cấu hình môi trường · bảng Paper vs Group · Gap Analysis"),
                                        ("Chương III: Phương pháp đề xuất", "kiến trúc V1 · kết quả V1 · failure cases · đề xuất V2 · bảng ablation tổng hợp"), ("Chương IV: Kết quả và đánh giá", "visual results · đánh giá khả thi · kế hoạch Task 3 · cảm ơn và Q&A"))):
    dong(L[i], [a]); dong(L[i + 1], [b])
ghi_chu(S, "Bai trinh bay gom bon chuong. Chuong mot la du lieu, chuong hai la baseline, chuong ba la phuong phap de xuat, chuong bon la ket qua va danh gia kha thi. Van de trung tam nam o khung tren: loi khau nghe lam mat 15 phay 58 BLEU.")
for n, c, ten in ((3, "I", None), (4, "I", None)):
    S = s_(n); L = list(S.shapes); dong(L[1], [f"Chương {c} · " + L[1].text_frame.text])
# ---- 5 mất cân bằng (định lượng)
S = s_(5); L = list(S.shapes); tieu(S, "Phân tích mất cân bằng", "Chương I · bài sinh chuỗi nên không có phân bố lớp, nhóm xét các phân bố ảnh hưởng tới kết quả")
dat(L[3], .45, 1.42, 7.3, 3.25); dat(L[5], 8.95, 1.42); dat(L[6], 8.95, 3.1)
for i, x in ((7, .45), (10, 3.6), (13, 6.75), (16, 9.9)):
    dy = 4.8 - 3.46
    for j in (i, i + 1, i + 2):
        L[j].top = L[j].top + Inches(dy)
dong(L[11], ["3,0×"]); dong(L[12], ["chênh số lần dạy giữa các câu"]); dong(L[17], ["0,82%"]); dong(L[18], ["bản thu > 30 s ở FLEURS test"])
dong(L[22], ["Nguồn: reports/data/eda/eda_nhan_xet.md · eda_tom_tat.json · reports/tong_hop/flowchart_lam_sach.png"])
bo_tu_sau(S, (4, 19, 20, 21))
ghi_chu(S, "Lech ro nhat la gioi tinh: train 74 phay 3 phan tram giong nu nhung dev va test toan giong nam, nen ket qua tren FLEURS chua noi duoc gi ve giong nu. So ban thu moi cau cung lech, co cau duoc day nhieu gap ba lan cau khac.")
# ---- 6 xử lý và kết quả
S = s_cb; L = list(S.shapes); dong(L[0], ["Xử lý mất cân bằng và kết quả"]); dong(L[1], ["Chương I · lấy mẫu lại, chỉ trên train; dev và test giữ nguyên"])
pic2 = S.shapes.add_picture(str(HA / "can_bang_01_theo_cau.png"), Inches(.45), Inches(1.42), height=Inches(2.55))
dat(L[4], 6.75, 1.42, 6.1, 2.55) if False else None
hinh = [x for x in S.shapes if x.shape_type == 13]
for x in hinh:
    if x.image.size == (2000, 940):
        x._element.getparent().remove(x._element)
for x in S.shapes:
    if x.shape_type == 13 and x.image.size[0] == 2000 and x.image.size[1] != 940 and x != pic2:
        x.left, x.top = Inches(6.75), Inches(1.42); x.height = Inches(2.55); x.width = int(x.height * x.image.size[0] / x.image.size[1])
T_ = {x.text_frame.text[:8]: x for x in S.shapes if x.has_text_frame}
bo(S, "74,3%", "giọng nữ", "12,62", "độ dài TB", "Giữ split")
e = [x for x in S.shapes if getattr(x, "has_table", False) and x.has_table][0]; e._element.getparent().remove(e._element)
for t, x in (("3,0×", 3.6), ("chênh số", 3.68), ("2.926", 9.9), ("số mẫu", 9.98)):
    pass
hop = [x for x in S.shapes if x.shape_type == 1 and x.top > Inches(3.3) and x.top < Inches(3.6)]
hop.sort(key=lambda z: z.left)
for x in (hop[0], hop[2]):
    x._element.getparent().remove(x._element)
dat(hop[1], .45, 4.05, 6.1, .78); dat(hop[3], 6.75, 4.05, 6.1, .78)
g = tim_s(S, "3,0×"); dat(g, .45, 4.05, 3.2, .78); co(g, 22); g2 = tim_s(S, "chênh số"); dat(g2, 3.6, 4.16, 2.9, .5)
g = tim_s(S, "2.926"); dat(g, 6.75, 4.05, 3.4, .78); co(g, 22); g2 = tim_s(S, "số mẫu"); dat(g2, 10.1, 4.16, 2.7, .5)
dat(tim_s(S, "Ba bước"), .45, 4.9, 12.4, .85)
dong(tim_s(S, "Nguồn"), ["Nguồn: reports/data/can_bang/can_bang_01_theo_cau.png · can_bang_02_do_dai.png · can_bang_tom_tat.json (seed 42, alpha 0,5) · reports/mt/bootstrap_V2_V3_cascade_test.json"])
ghi_chu(S, "Ba buoc can bang chi lam tren train. Hai bieu do cho thay truoc va sau khi xu ly. Diem quan trong o khung duoi: hieu qua da duoc do bang cap V2 va V3, va ket qua la khong cai thien co y nghia tren test. Vi vay ban cuoi V2 khong dung buoc can bang theo cau va do dai.")
# ---- 7 cấu hình môi trường
S = s_mt; L = list(S.shapes); dong(L[0], ["Cấu hình môi trường và baseline"]); dong(L[1], ["Chương II · bốn baseline, checkpoint công bố chạy zero-shot, cùng một máy và một môi trường"])
tb = [x for x in L if getattr(x, "has_table", False) and x.has_table][0].table
HANG = [("Baseline", "Mô hình", "Revision", "Vai trò"), ("Khối nghe 1", "PhoWhisper-small", "a86b604c", "baseline chính, chuyên tiếng Việt"), ("Khối nghe 2", "Whisper-small", "973afd24", "đối chứng cùng quy mô, đa ngôn ngữ"), ("Khối dịch B0", "VinAI Translate vi2en-v2", "ae7baa85", "baseline khối dịch, cascade"), ("End-to-end B1", "Whisper-small, task=translate", "973afd24", "đối chứng end-to-end")]
while len(tb._tbl.tr_lst) > 5:
    tb._tbl.remove(tb._tbl.tr_lst[-1])
for i, h in enumerate(HANG):
    for j, v in enumerate(h):
        c = tb.cell(i, j).text_frame; p = c.paragraphs[0]; p.runs[0].text = v
        for r in p.runs[1:]:
            r._r.getparent().remove(r._r)
bo_tu_sau(S, tuple(range(4, 18)))
L = list(S.shapes); mt = tim_s(S, "Môi trường"); dat(mt, .45, 4.0, 12.4, 1.1); co(mt, 13)
dong(tim_s(S, "Nguồn"), ["Nguồn: env/moi_truong.json · configs/asr_protocol.json · configs/common_suppression_from_task1.json · reports/models.json"])
ghi_chu(S, "Tat ca baseline chay tren mot may RTX 4060 Laptop, cung protocol. LR, optimizer va epoch khong ap dung cho baseline vi baseline chi nap checkpoint de suy luan. B1 la doi chung end-to-end, khong nhan la tai lap paper.")
# ---- 8 Paper vs Group
S = s_(6); dong(list(S.shapes)[0], ["Bảng Paper vs Group"]); dong(list(S.shapes)[1], ["Chương II · cùng dataset thì so với số trong paper; NR = nguồn không báo cáo, không phải 0"])
bo(S, "Môi trường")
# ---- 9 Gap
S = s_(7); L = list(S.shapes); dong(L[0], ["Gap Analysis: 5 giả thuyết đặt trước, kiểm bằng số"]); dong(L[1], ["Chương II · kiểm lỗi triển khai trước; chỉ diễn giải khác biệt miền sau khi các kiểm tra đó đạt"])
for x in S.shapes:
    if x.has_text_frame:
        for p in x.text_frame.paragraphs:
            sub(p, "ở slide 16", "ở slide 19")
# ---- 10, 11 V1
S = s_(8); L = list(S.shapes); dong(L[0], ["Kiến trúc V1: LoRA cho khối dịch, dạy trên lời ASR thật"]); dong(L[1], ["Chương III · giữ nguyên khối nghe, chỉ thích nghi khối dịch để nó chịu được lỗi của khối nghe"])
S = s_(9); L = list(S.shapes); dong(L[1], ["Chương III · so với cả hai baseline khối nghe, trên cùng tập test và cùng protocol"])
# ---- 12 failure cases
S = s_(10); L = list(S.shapes); dong(L[0], ["Failure cases của V1"]); dong(L[1], ["Chương III · phân tích lỗi trên dev, không nhìn test"])
hopvd = L[20]; vd = L[21]; nt = L[22]
dat(hopvd, 5.6, 1.45, 7.25, 3.65); dat(vd, 5.75, 1.55, 6.95, 3.45)
dong(vd, ["Ví dụ lỗi rút gọn mất ý của V1", "Tham chiếu: “The Spaniards started the colonization period which lasted for three centuries.”", "V1 dịch: “The Spanish began a three-century period of colonialism.”", "Nghĩa gần đúng nhưng mất chi tiết. Dạng này chiếm 8/361 câu dev, B0 không có câu nào.", "Quên miền gốc: dịch văn bản chuẩn −2,06, PhoMT −3,83 so với B0.", "Overfit: BLEU dev đỉnh ở epoch 1 rồi giảm."])
dong(nt, ["Lỗi nghe còn lan sang khâu dịch: khối dịch không biết khối nghe sai ở đâu."])
bo_tu_sau(S, tuple(range(5, 20)))
dong(tim_s(S, "Nguồn"), ["Nguồn: reports/mt/failure_V1_dev.md · reports/asr/tone_confusion_*.png · checkpoints/V1/curves.png"])
ghi_chu(S, "Hinh ben trai la ma tran nham dau thanh cua khoi nghe, loi nay truyen sang khau dich. Ben phai la cac dang loi cua V1: rut gon mat y, quen mien goc va overfit tu epoch 2.")
# ---- 13 đề xuất V2
S = s_v2; L = list(S.shapes); dong(L[0], ["Đề xuất V2 và các bản tiếp theo"]); dong(L[1], ["Chương III · mỗi phiên bản chỉ đổi MỘT yếu tố, lý do lấy từ dev, không nhìn test"])
for i in range(5, 20):
    if L[i].left > Inches(6):
        L[i].left = Inches(1.3); L[i].width = Inches(11.4)
    else:
        L[i].left = Inches(.55)
for i in (7, 12, 17):
    co(L[i], 15)
for i in (8, 13, 18):
    co(L[i], 12.5)
for i in (9, 14, 19):
    co(L[i], 13)
dat(L[22], .45, 5.3, 12.4, .6); co(L[22], 13)
dong(L[23], ["Nguồn: reports/mt/failure_V1_dev.md · configs/mt/V2.json, V3.json, V4.json"])
bo_tu_sau(S, (3, 4, 20, 21))
ghi_chu(S, "Tu ba loai loi, nhom de xuat ba phien ban tiep theo, moi ban doi mot yeu to. V2 tron them PhoMT de sua loi quen mien goc. V3 can bang theo cau va do dai. V4 giam learning rate. Ban cuoi la V2.")
# ---- 14–16
S = s_(11); L = list(S.shapes); dong(L[0], ["Bảng ablation tổng hợp"]); dong(L[1], ["Chương III · ★ = bản cuối · số seed 42 · V1–V4 là các phiên bản nối tiếp; ablation một yếu tố ở slide 15, 3 seed ở slide 16"])
for n in (12, 13):
    S = s_(n); L = list(S.shapes); dong(L[1], ["Chương III · " + L[1].text_frame.text])
# ---- 17–21
S = s_(14); L = list(S.shapes); dong(L[0], ["Visual results và kết quả theo miền"]); dong(L[1], ["Chương IV · ví dụ thật trên FLEURS test, miền Giáo dục · chữ giữ nguyên như trong file kết quả"])
for n, t in ((15, None), (16, None), (17, None), (18, None)):
    S = s_(n); L = list(S.shapes); dong(L[1], ["Chương IV · " + L[1].text_frame.text])
# ---- 22 kế hoạch Task 3
S = s_t3; L = list(S.shapes); dong(L[0], ["Kế hoạch Task 3"]); dong(L[1], ["Chương IV · đóng gói và hoàn thiện sản phẩm · theo KIEM_THU_CUOI.md"])
dong(L[4], ["Mục tiêu: sản phẩm chạy được với model thật và có bằng chứng kiểm thử"]); dong(L[6], ["Đã có"]); dong(L[9], ["Đang làm"]); dong(L[12], ["Trước khi nộp"])
dong(L[7], ["Demo Gradio và API chạy với model thật", "Chia đoạn, bỏ lặp, đổi số; đo trên 857 bản", "Kiểm tra 3 seed và độ bền khối nghe", "Nghiệm thu model thật 6/7 mục", "151 test: 145 qua, 6 bỏ qua"])
dong(L[10], ["Docker hai service: đã viết, chưa build thật", "CI năm job: đã viết, chưa chạy", "Đọc m4a, webm: cần ffmpeg", "Thử micro thật trên Chrome"])
dong(L[13], ["Đẩy repo lên GitHub", "Quay video demo 2–5 phút", "Thu 20 câu tự thu: giọng nữ, micro điện thoại", "Điền mã nhóm, GVHD, tỷ lệ đóng góp"])
for x in (L[7], L[10], L[13]):
    co(x, 12)
bo_tu_sau(S, (14, 15, 16))
ghi_chu(S, "Ke hoach Task 3 chia ba cot. Cot dau la nhung gi da chay that. Cot giua la phan da viet nhung chua chay that, nhom noi ro de khong nham. Cot cuoi la viec phai xong truoc khi nop.")
# ---- 23
S = s_(19); dong(list(S.shapes)[0], ["Kết luận, cảm ơn và Q&A"]); dong(list(S.shapes)[1], ["Chương IV · đóng góp, hạn chế và việc nên làm tiếp"])
# ---- thứ tự
TT = [s_(1), s_(2), s_(3), s_(4), s_(5), s_cb, s_mt, s_(6), s_(7), s_(8), s_(9), s_(10), s_v2, s_(11), s_(12), s_(13), s_(14), s_(15), s_(16), s_(17), s_(18), s_t3, s_(19)]
lst = pr.slides._sldIdLst; id_ = {pr.slides.get(int(e.get("id"))).slide_id: e for e in lst}
moi = [id_[x.slide_id] for x in TT]
for e in list(lst):
    lst.remove(e)
for e in moi:
    lst.append(e)
for i, s in enumerate(pr.slides, 1):
    if i > 1:
        for x in s.placeholders:
            if x.has_text_frame and x.text_frame.text.strip().isdigit():
                dong(x, [str(i)])
pr.save(F); print("Slide khung xong", len(pr.slides))
