#!/usr/bin/env python3
"""Slide nhóm theo bản cuối V2 (làm trên bản sao). Thêm 1 slide: chọn bản cuối và ablation."""
import copy
from pptx import Presentation
from pptx.util import Inches, Pt
from PIL import Image
from chung import *

pr = Presentation(G / "2_slide/Slide_Project_Nhom.pptx"); SL = list(pr.slides); t0, t2 = S.t0, S.t2; ab = S.ab
c = vn(S.c["BLEU"]); de = f"+{vn(S.d['delta'])}"; dci = ci(S.d); gap = vn(S.gap); dw = f"+{vn(S.dw['delta'])}"; dwci = ci(S.dw); dcl = vn(S.dcl).replace("-", "−"); cl = vn(S.cl["BLEU"]); k1 = vn(S.b1["BLEU"])
sh = lambda n, j: SL[n - 1].shapes[j]


def dong(shape, lines):
    tf = shape.text_frame; P = list(tf.paragraphs)
    while len(P) < len(lines):
        el = copy.deepcopy(P[-1]._p); P[-1]._p.addnext(el); P = list(tf.paragraphs)
    for p in P[len(lines):]:
        p._p.getparent().remove(p._p)
    for p, t in zip(tf.paragraphs, lines):
        R = p.runs; R[0].text = t
        for r in R[1:]:
            r._r.getparent().remove(r._r)


def thay_s(shape, cap):
    for cu, moi in cap:
        ok = False
        for p in shape.text_frame.paragraphs:
            ok = sub(p, cu, moi) or ok
        assert ok, cu


def note(n, *cap):
    tf = SL[n - 1].notes_slide.notes_text_frame
    for cu, moi in cap:
        assert cu in tf.text, cu
        tf.text = tf.text.replace(cu, moi)


def ot(tb, i, j, text):
    dong_o = tb.cell(i, j).text_frame
    p = dong_o.paragraphs[0]; p.runs[0].text = text
    for r in p.runs[1:]:
        r._r.getparent().remove(r._r)
    for q in list(dong_o.paragraphs)[1:]:
        q._p.getparent().remove(q._p)


def hg(tb, i, *gt):
    for j, v in enumerate(gt):
        if v is not None:
            ot(tb, i, j, v)


def them(tb, sau):
    tr = copy.deepcopy(tb._tbl.tr_lst[sau]); tb._tbl.tr_lst[sau].addnext(tr)


def anh(shape, tep, giu_cao=True):
    rid = shape._element.blipFill.blip.rEmbed
    shape.part.related_part(rid)._blob = Path(tep).read_bytes()
    w, h = Image.open(tep).size
    if giu_cao:
        shape.width = int(shape.height * w / h)


# ---- 1, 2
dong(sh(1, 2), ["04/11/2026"]); note(11, ("Bang tren la ablation day du, bang duoi", "Bang tren la cac phien ban noi tiep, bang duoi"))
note(1, ("Toan bo thuc nghiem chay moi tren mot may trong hai ngay.", "Toan bo thuc nghiem chay moi tren mot may."))
dong(sh(2, 12), [f"adapter 34,7 MB (2,0% tham số) → {de} BLEU"]); dong(sh(2, 20), ["demo và API chạy thật; Docker, CI/CD đã viết"]); dong(sh(2, 19), ["Đóng gói thành sản phẩm"])
# ---- 6
dong(sh(6, 1), ["Bốn baseline, tất cả là checkpoint công bố chạy zero-shot, cùng một máy và một môi trường"])
tb = sh(6, 3).table; them(tb, 5)
hg(tb, 6, "End-to-end B1 · Whisper-small dịch · FLEURS", "NOT RUN", f"BLEU {k1} · chrF++ {vn(S.b1['chrF++'])}", f"kém B0 {vn(-S.db1['delta'])} BLEU")
for r in tb.rows:
    r.height = Inches(.36)
thay_s(sh(6, 19), [("runs/mt/B0/*/score.json", "runs/mt/B0/*/score.json · runs/mt/B1_whisper-small_translate/")])
note(6, ("Va con so quan trong nhat la khung duoi", "B1 la doi chung end-to-end, chi dat BLEU 3 phay 80, day la so cua Whisper small chay nguyen ban. Va con so quan trong nhat la khung duoi"))
# ---- 7
thay_s(sh(7, 4), [("ở slide 14", "ở slide 16")])
# ---- 11
dong(sh(11, 0), ["Các phiên bản: từng thành phần đóng góp bao nhiêu"]); dong(sh(11, 1), ["★ = bản cuối, chọn theo quy tắc ở slide 12 · số seed 42 · các phiên bản nối tiếp; ablation ở slide 12, 3 seed ở slide 13"])
tb = sh(11, 4).table; ot(tb, 3, 0, "V2 ★"); ot(tb, 4, 0, "V3")
anh(sh(11, 3), H / "ablation_V2.png", giu_cao=False)
thay_s(sh(11, 7), [("reports/tong_hop/ablation.csv", "reports/ablation/bang_ablation.csv")])
# ---- 13 (bản cũ 12)
tb = sh(12, 4).table; hg(tb, 0, None, None, None, None, "V2")
for i, k in ((1, "Giáo dục"), (2, "Du lịch"), (3, "Tin tức")):
    ot(tb, i, 4, vn(S.mien[k]["BLEU"]))
anh(sh(12, 3), H / "visual_results_tot.png")
dong(sh(12, 6), ["Ví dụ 1: khối nghe nghe “kho báu” thành “kho báo”, B0 dịch thành “newspaper warehouse map” — sai hoàn toàn nghĩa. V2 đoán được ý.    Ví dụ 2: khối nghe viết “hai mươi lăm đến ba mươi năm”; B0 dịch nguyên văn còn V2 viết đúng “25 to 30 years”. Không phải lúc nào cũng đúng: “1920” có câu bị V2 dịch thành “the 1990s”."])
thay_s(sh(12, 8), [("runs/mt/B0 và runs/mt/V3/", "runs/mt/B0 và runs/mt/V2/")])
note(12, ("Vi du mot cho thay V3 sua duoc loi nghia.", "Vi du mot cho thay V2 sua duoc loi nghia."))
# ---- 14 (cũ 13)
anh(sh(13, 3), H / "visual_results_loi.png"); sh(13, 3).left = int((pr.slide_width - sh(13, 3).width) / 2)
thay_s(sh(13, 4), [("nên cả B0 và V3 đều sai", "nên cả B0 và V2 đều sai"), ("thu hẹp xuống 10,94", f"thu hẹp xuống {gap}"), ("bị V3 dịch thành", "bị V2 dịch thành")])
thay_s(sh(13, 5), [("runs/mt/V3/", "runs/mt/V2/"), ("failure_V3_dev.md", "failure_V2_dev.md")])
# ---- 15 (cũ 14)
dong(sh(14, 0), ["Kiến trúc hệ thống và các bước thêm cho sản phẩm"])
p = sh(14, 3); anh(p, H / "kien_truc_he_thong.png", giu_cao=False)
p.left, p.top, p.width = Inches(.45), Inches(1.36), Inches(7.5); p.height = int(p.width * 1237 / 2180)
for j, (x, y, w_, h_) in {5: (8.1, 1.38, 4.75, 2.05), 6: (8.2, 1.44, 4.55, 1.93), 7: (8.1, 3.53, 4.75, 2.05), 8: (8.2, 3.59, 4.55, 1.93)}.items():
    s = sh(14, j); s.left, s.top, s.width, s.height = Inches(x), Inches(y), Inches(w_), Inches(h_)
s = sh(14, 4); s.top = Inches(5.75); s.height = Inches(.5)
dong(s, [f"Chia thời gian: khối nghe RTF {vn(t2['asr'], 3)}, khối dịch {vn(t2['mt'], 3)} → khối nghe chiếm khoảng {t2['asr'] / t2['rtf'] * 100:.0f}% thời gian, nên muốn tăng tốc thì phải tối ưu khối nghe trước.   Cả hệ sản phẩm: WER {vn(S.tat['WER_asr'])}%, BLEU {vn(S.tat['BLEU'])}; so với xử lý cũ +{vn(S.hb['delta'])} {ci(S.hb)}, chưa có ý nghĩa thống kê."])
dong(sh(14, 6), ["1. Audio dài hơn 30 s — lỗi chặn", f"Đưa thẳng vào khối nghe: WER 94,70%, I = 401 / N = 472. Chỉ chiếm 0,82% tập test nhưng với ghi âm bài giảng thì thường gặp.", f"→ Chia ≤ 28 s tại chỗ ngắt nghỉ, bỏ lặp ở chỗ nối. 10 bản dài hơn 28 s: WER {vn(S.dai['WER_asr'])}%, BLEU {vn(S.ht['truoc_0411']['dai']['BLEU'])} → {vn(S.dai['BLEU'])}."])
dong(sh(14, 8), ["2. Số đọc thành chữ — đã thêm", "Câu có chữ số WER 27,43% so với 5,89%. Khối nghe viết số bằng chữ, còn dữ liệu dịch dùng chữ số.", f"→ Đổi sang chữ số trước khi dịch: {S.hb['cau_co_chu_so']['n']} câu có số tăng {vn(S.hb['cau_co_chu_so']['BLEU_A'])} → {vn(S.hb['cau_co_chu_so']['BLEU_B'])}. Mới đo trên test, chưa đo riêng trên dev."])
s = sh(14, 9); s.top = Inches(6.3); dong(s, ["Nguồn: reports/toc_do/lap_V2/toc_do_V2_lan{1,2,3}.json · reports/he_thong_V2/ket_qua.json, bootstrap_cu_vs_moi.json · reports/asr/long_form_audit.csv · strata.csv"])
SL[13].notes_slide.notes_text_frame.text = "So do tach hai luong vi day la hai thu khac nhau, tron lai se thanh bao cao sai. Luong tren la da do trong thuc nghiem, khong chia doan dung theo protocol da khoa. Luong duoi la luong san pham, them chia doan, bo lap, doi so va dau vao tu micro. Hai van de ben phai deu xuat phat tu loi da quan sat duoc. Cac buoc nay do tren test de nghiem thu san pham, khong dung de chon mo hinh."
# ---- 16 (cũ 15)
dong(sh(15, 1), ["Demo và API chạy với model thật · Docker hai service và CI/CD năm job đã viết, chưa chạy thật"])
thay_s(sh(15, 5), [("Hai tab: tải tệp (wav, mp3, flac, m4a, ogg) và thu âm từ micro", "Hai tab: tải tệp (wav, mp3, flac, ogg; m4a cần ffmpeg) và thu âm"), ("Tuỳ chọn bật tắt VAD và đặt độ dài đoạn 5–30 s", "Tuỳ chọn VAD cho audio dài (mặc định tắt), độ dài đoạn 5–30 s")])
dong(sh(15, 11), ["Hai service: api có torch, app chỉ giao diện và gọi api qua HTTP", "Ảnh chạy user thường, healthcheck, cache trọng số trong volume", "CI: lint · pytest · cài sạch · build hai ảnh · deploy", "Docker chưa build thật; CI chưa chạy vì repo chưa lên GitHub", "Ruff và pytest đã chạy tay trên máy nhóm"])
dong(sh(15, 13), ["Kiểm thử: 151 test — 145 qua, 6 bỏ qua (cần ffmpeg), 0 trượt", "Nghiệm thu model thật 6/7 mục (m4a, webm trượt vì thiếu ffmpeg). Demo thật: file rỗng, file hỏng, im lặng, nhiều lượt và 3 người cùng lúc đều xử lý được. Test quan trọng nhất kiểm audio 35, 60, 125 giây không đoạn nào vượt 30 giây."])
SL[14].notes_slide.notes_text_frame.text = "Ba khoi: demo Gradio co ca tai tep va thu am, API FastAPI tach rieng, va cau hinh Docker hai service kem CI CD nam job. Em noi ro: demo va API da chay voi model that, con Docker va GitHub Actions moi viet chua chay. Hai ket qua kiem chung o khung duoi: nhom tim ra mot loi that khi viet test, va scorer viet doc lap tai lap dung tung con so cua thuc nghiem."
# ---- 17 (cũ 16)
dong(sh(16, 0), ["Đánh giá tính khả thi của bản cuối V2"])
tb = sh(16, 3).table
hg(tb, 0, None, None, None, "V2"); hg(tb, 1, None, None, None, f"{de} {dci}"); hg(tb, 2, None, None, None, f"{dw} {dwci}"); hg(tb, 3, None, None, None, f"15,58 → {gap}")
hg(tb, 4, None, None, None, f"{cl} ({dcl})"); hg(tb, 5, None, None, None, vn(t2["rtf"], 3)); hg(tb, 6, None, None, None, f"{vn(t2['p95'])} s")
dong(sh(16, 5), [vn(t2["rtf"], 3)]); dong(sh(16, 8), [f"{vn(t2['p95'])} s"]); dong(sh(16, 14), ["6 / 7"]); dong(sh(16, 15), ["tiêu chí có ngưỡng đạt"])
tb = sh(16, 16).table
hg(tb, 0, "Chỉ số", "Cascade V2", "Cả hệ sản phẩm"); hg(tb, 1, "WER khối nghe", "13,68%", f"{vn(S.tat['WER_asr'])}%"); hg(tb, 2, "BLEU", c, vn(S.tat["BLEU"])); hg(tb, 3, "chrF++", vn(S.c["chrF++"]), vn(S.tat["chrF++"]))
hg(tb, 4, "RTF", vn(t2["rtf"], 3), vn(S.tat["RTF"], 3)); hg(tb, 5, "Bản > 28 s (10 bản)", "–", f"WER {vn(S.dai['WER_asr'])}%")
dong(sh(16, 17), [f"Dịch văn bản chuẩn, trung bình 3 seed: {B3.vi('V2', 'test sạch')}, thiếu {vn(-SACH_TB)} so với ngưỡng, không seed nào đạt.", "", "Cả hệ thêm chia đoạn, bỏ lặp và đổi số. So với xử lý cũ: " f"+{vn(S.hb['delta'])} {ci(S.hb)}, chưa có ý nghĩa thống kê. Hai cột khác cách xử lý nên không dùng để so mô hình."])
dong(sh(16, 19), [f"KHẢ THI để đóng gói thành ứng dụng web chạy GPU.  Chưa đạt: không giảm BLEU khi dịch văn bản chuẩn ({dcl}). Nhóm không diễn giải lại ngưỡng cho vừa kết quả."])
thay_s(sh(16, 20), [("reports/toc_do/lap/*.json (trung vị 3 lần đo xen kẽ, 100 bản thu, batch 1)", "reports/toc_do/lap_V2/*.json (trung vị 3 lần đo xen kẽ, 100 bản thu, batch 1) · reports/he_thong_V2/ket_qua.json")])
SL[15].notes_slide.notes_text_frame.text = "Rubric nay dat ra truoc khi co so, va ghi ro nguong nao tu de cuong nguong nao la de xuat cua nhom. Sau trong bay tieu chi co nguong dat. Rieng tieu chi khong giam BLEU khi dich van ban chuan thi V2 chua dat, thieu 0 phay 18. Bang ben phai la so cua ca he san pham, co them chia doan va doi so."
# ---- 18 (cũ 17)
R = robust()
dong(sh(17, 7), ["Định lượng điểm nghẽn cascade: 15,58 BLEU mất do lỗi khâu nghe", f"Thu hẹp còn {gap} bằng adapter 34,7 MB, chỉ 2,0% tham số", f"+{vn(D_TB)} ± {vn(D_SD)} BLEU cascade trung bình 3 seed", "Chỉ ra lỗi audio dài mà chỉ số tổng che mất (0,82% tập test)", "Demo và API chạy với model thật; Docker, CI/CD đã viết"])
han = f"Nhiễu trắng 10 dB: WER {vn(R[0][3]['WER_percent'])}% → {vn(R[2][3]['WER_percent'])}%; chưa thử ồn thật, micro điện thoại" if R[2][3] else "Chưa thử micro điện thoại và môi trường ồn"
dong(sh(17, 10), ["Chỉ đo trên audio đọc rõ, một người nói", "Dev và test FLEURS 100% giọng nam", han, "Quy tắc chọn V2 chốt sau khi đã thấy test; seed train khác môi trường", "Docker, CI, micro thật và 20 câu tự thu chưa chạy"])
dong(sh(17, 13), ["Thu bộ audio thử nghiệm: giọng nữ, micro điện thoại, có tiếng ồn", "Đo bước đổi số trên dev, mở rộng cho ngày tháng và đơn vị", "Chấm cách chia đoạn trên audio bài giảng thật", "Thử phục hồi dấu câu cho lời ASR trước khi dịch", "Huấn luyện một mô hình end-to-end để so với cascade"])

# ---- slide mới: chọn bản cuối
m = SL[10]; nw = pr.slides.add_slide(m.slide_layout)
for e in list(nw.shapes._spTree):
    if e.tag.endswith(("}sp", "}pic", "}graphicFrame")):
        nw.shapes._spTree.remove(e)
keep = {}
for j in (0, 1, 2, 4, 6, 7):
    el = copy.deepcopy(m.shapes[j]._element); nw.shapes._spTree.append(el)
for j in (16, 17):
    nw.shapes._spTree.append(copy.deepcopy(SL[5].shapes[j]._element))
b = list(nw.shapes); ten, phu, so, bang, kl, ng, hop, chu = b
hop2, chu2 = None, None
el = copy.deepcopy(hop._element); nw.shapes._spTree.append(el); el2 = copy.deepcopy(chu._element); nw.shapes._spTree.append(el2)
b = list(nw.shapes); hop2, chu2 = b[-2], b[-1]
dong(ten, ["Chọn bản cuối và ablation một yếu tố"]); dong(phu, ["Chỉ dùng số dev để chọn · ablation đổi đúng một yếu tố so với V2"])
tb = bang.table
while len(tb.rows) < 8:
    them(tb, len(tb.rows) - 1)
bang.left, bang.top = Inches(.45), Inches(1.42)
for w_, col in zip((3.1, 1.4, 1.4, 1.4, 1.4, 3.7), tb.columns):
    col.width = Inches(w_)
for r in tb.rows:
    r.height = Inches(.32)
sua = lambda k: ab[k]["Δ test cascade so với V2 (KTC 95%)"].split(", p")[0].replace(".", ",").replace("-", "−")
hg(tb, 0, "Bản", "Dev cascade", "Dev sạch", "Test cascade", "Test sạch", "Δ test cascade so với V2")
for i, (k, n) in enumerate((("V1", "V1"), ("V2", "V2 ★"), ("V3", "V3"), ("V4", "V4"), ("A_r8", "A_r8: rank 8"), ("A_r32", "A_r32: rank 32"), ("A_aug", "A_aug: thêm transcript sạch")), 1):
    r = ab[k]; hg(tb, i, n, vn(r["dev cascade"]), vn(r["dev sạch"]), vn(r["test cascade"]), vn(r["test sạch"]), sua(k) if k.startswith("A_") else "–")
hop.left, hop.top, hop.width, hop.height = Inches(.45), Inches(4.3), Inches(6.1), Inches(1.3); chu.left, chu.top, chu.width, chu.height = Inches(.57), Inches(4.34), Inches(5.86), Inches(1.22)
hop2.left, hop2.top, hop2.width, hop2.height = Inches(6.75), Inches(4.3), Inches(6.1), Inches(1.3); chu2.left, chu2.top, chu2.width, chu2.height = Inches(6.87), Inches(4.34), Inches(5.86), Inches(1.22)
dong(chu, [f"Quy tắc: bản cách đỉnh dev cascade (26,71) không quá 0,5 BLEU là hoà; trong nhóm hoà chọn dev sạch cao nhất. V1–V4 đều hoà, V2 có dev sạch {vn(ab['V2']['dev sạch'])} nên V2 là bản cuối."])
dong(chu2, ["Phải nói rõ: quy tắc đầu tiên (dev cascade cao nhất) cho ra V3. Quy tắc mới chốt ngày 03/11, sau khi đã thấy số test của V1–V4, nên không phải lựa chọn mù với test. Chỉ ba bản ablation chạy sau khi có quy tắc."])
for x in (chu, chu2):
    for p in x.text_frame.paragraphs:
        for r in p.runs:
            r.font.size = Pt(11.5)
kl.top = Inches(5.74); kl.height = Inches(.5)
dong(kl, [f"Rank 8 và rank 32 không khác V2 có ý nghĩa. Rank 32 có test cascade cao nhất nhưng dev cascade thấp hơn nhóm hoà nên không được chọn. Thêm transcript sạch tăng dev sạch lên {vn(ab['A_aug']['dev sạch'])} nhưng dev cascade giảm còn {vn(ab['A_aug']['dev cascade'])}, test cascade kém V2 có ý nghĩa."])
for p in kl.text_frame.paragraphs:
    for r in p.runs:
        r.font.size = Pt(11)
dong(ng, ["Nguồn: reports/ablation/QUY_TAC_CHON.md · chon_ban_cuoi.json · bang_ablation.csv · reports/mt/bootstrap_V2_A_*.json · checkpoints/A_*"])
nw.notes_slide.notes_text_frame.text = "Quy tac dau tien la lay dev cascade cao nhat, cho ra V3. Nhung bon ban chenh rat it, nen nhom chot lai quy tac: cach dinh khong qua 0 phay 5 thi coi la hoa, chon ban co dev sach cao nhat, ra V2. Em noi ro quy tac nay chot sau khi da thay so test cua V1 den V4, nen khong phai lua chon mu voi test. Ablation doi dung mot yeu to so voi V2: rank 8, rank 32 khong khac co y nghia, them transcript sach thi kem di."
# ---- slide mới: 3 seed, dựng từ slide chọn bản cuối
n3 = pr.slides.add_slide(m.slide_layout)
for e in list(n3.shapes._spTree):
    if e.tag.endswith(("}sp", "}pic", "}graphicFrame")):
        n3.shapes._spTree.remove(e)
for s_ in nw.shapes:
    n3.shapes._spTree.append(copy.deepcopy(s_._element))
ten3, phu3, so3, bang3, kl3, ng3, hop3, chu3, hop4, chu4 = list(n3.shapes)
dong(ten3, ["Kiểm tra 3 seed: kết luận có đứng vững không"]); dong(phu3, ["Trung bình ± độ lệch chuẩn của seed 42, 1, 2 · dịch và chấm cùng môi trường torch 2.0.1"])
tb = bang3.table
hg(tb, 0, "Bản", "Dev cascade", "Dev sạch", "Test cascade", "Test sạch", "Δ test cascade so với V2")
for i, (k, n_) in enumerate((("V1", "V1"), ("V2", "V2 ★"), ("V3", "V3"), ("V4", "V4"), ("A_r8", "A_r8: rank 8"), ("A_r32", "A_r32: rank 32"), ("A_aug", "A_aug: thêm transcript sạch")), 1):
    hg(tb, i, n_, B3.vi(k, "dev cascade"), B3.vi(k, "dev sạch"), B3.vi(k, "test cascade"), B3.vi(k, "test sạch"), B3.d(k, "test cascade").replace(".", ",").replace("-", "−") if k.startswith("A_") else "–")
dong(chu3, [f"V2 hơn B0 +{vn(D_TB)} ± {vn(D_SD)} BLEU. Áp quy tắc trên trung bình dev, nhóm hoà còn V1 và V2, và V2 vẫn được chọn. Lợi thế dev của V3 ở seed 42 không lặp lại."])
dc_ = DC["dev cascade"]
dong(chu4, [f"Hạn chế: seed 1, 2 train trên Modal bằng torch 2.7.1. Train lại V2 seed 42 ở đó cho dev {vn(dc_['seed 42 Modal (train torch 2.7.1)'])} so với {vn(dc_['seed 42 máy nhóm (torch 2.0.1)'])}, nên môi trường làm lệch gần bằng seed."])
dong(kl3, [f"V1 có test cascade trung bình cao hơn ({B3.vi('V1', 'test cascade')}) nhưng nhóm không chọn theo test. Rank không tạo khác biệt rõ; thêm transcript sạch kém V2 ở cả ba seed. Dịch sạch của V2 thiếu {vn(-SACH_TB)} so với ngưỡng, không seed nào đạt."])
dong(ng3, ["Nguồn: reports/ba_seed/QUY_TAC_3SEED.md · bang_3seed.csv · bang_ablation_3seed.csv · ket_qua_3seed.json · notebooks/04_kiem_tra_3_seed.ipynb"])
n3.notes_slide.notes_text_frame.text = "Nhom train them seed 1 va 2 cho ca bay ban. Ket luan chinh giu nguyen: V2 hon B0 khoang 4 phay 65 BLEU, va ap quy tac tren trung binh van ra V2. Em noi ro hai diem: V1 co test cao hon nhung nhom khong chon theo test, va seed moi train o moi truong khac nen so lech mot phan do moi truong."
lst = pr.slides._sldIdLst; ids = list(lst); e2 = ids[-1]; e = ids[-2]; lst.remove(e); lst.remove(e2); lst.insert(11, e); lst.insert(12, e2)
# đánh lại số trang
for i, s in enumerate(pr.slides, 1):
    if i > 1:
        for x in s.placeholders:
            if x.has_text_frame and x.text_frame.text.strip().isdigit():
                dong(x, [str(i)])
out = O / "2_slide"; out.mkdir(exist_ok=True); pr.save(out / "Slide_Project_Nhom.pptx"); print("Slide xong", len(pr.slides))
