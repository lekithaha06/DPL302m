#!/usr/bin/env python3
"""Báo cáo nhóm theo bản cuối V2. Làm trên bản sao, không đụng file gốc của Đăng."""
from docx import Document
from chung import *

d = Document(G / "1_bao_cao/BaoCao_Project_Nhom.docx")
T_ = d.tables; t0, t2 = S.t0, S.t2
c, cf = vn(S.c["BLEU"]), vn(S.c["chrF++"]); de = f"+{vn(S.d['delta'])}"; dci = ci(S.d); dw = f"+{vn(S.dw['delta'])}"; dwci = ci(S.dw); gap = vn(S.gap); w = vn(S.w["BLEU"])
cl, dcl = vn(S.cl["BLEU"]), vn(S.dcl).replace("-", "−"); ph = vn(S.ph["BLEU"])
ab = S.ab; dsach = lambda k: vn(ab[k]["dev sạch"])
kq = vn(S.b1["BLEU"]); kqc = vn(S.b1["chrF++"]); db1 = vn(-S.db1["delta"]); db1ci = ci(S.db1)
phien = max(1 / t2["rtf"] - .5, 0)

thay(d, [("Hà Nội, tháng 10 năm 2026", "Hà Nội, tháng 11 năm 2026"),
         ("WER khối nghe 10,76% và BLEU 30,92, so với miền Tin tức là 19,18% và 23,17", f"WER khối nghe 10,76% và BLEU {vn(S.giao)}, so với miền Tin tức là 19,18% và {vn(S.tin)}"),
         ("tự chia audio dài thành các đoạn không quá 28 giây bằng VAD", "tự chia audio dài hơn 28 giây thành các đoạn không quá 28 giây tại chỗ ngắt nghỉ"),
         ("tăng BLEU cascade từ 22,69 lên 27,33, tức +4,64 với khoảng tin cậy 95% là [3,32; 5,90]", f"tăng BLEU cascade từ 22,69 lên {c}, tức {de} với khoảng tin cậy 95% là {dci}"),
         ("Khoảng cách cascade so với văn bản chuẩn thu từ 15,58 xuống 10,94 BLEU.", f"Khoảng cách cascade so với văn bản chuẩn thu từ 15,58 xuống {gap} BLEU."),
         ("và xử lý bằng bước chia đoạn ở mức hệ thống.", f"và xử lý bằng bước chia đoạn ở mức hệ thống; sau khi chia đoạn, 10 bản thu dài hơn 28 giây còn WER {vn(S.dai['WER_asr'])}%."),
         ("Thứ tư, đóng gói thành sản phẩm chạy được gồm demo Gradio có cả tải tệp và thu âm, API FastAPI tách riêng, Docker hai service, và CI/CD tự kiểm.",
          "Thứ tư, đóng gói thành sản phẩm gồm demo Gradio có cả tải tệp và thu âm, API FastAPI tách riêng, kèm cấu hình Docker hai service và CI/CD. Demo và API đã chạy với model thật; Docker và CI đã viết nhưng chưa chạy thật (mục 8.2)."),
         ("Chuẩn hoá số là nguồn lỗi có thể xử lý ở mức hệ thống, không cần đổi mô hình. Nhóm ghi vào hướng phát triển ở mục 8.", "Chuẩn hoá số là nguồn lỗi có thể xử lý ở mức hệ thống, không cần đổi mô hình. Bước này đã được thêm vào sản phẩm, xem mục 7.2."),
         ("Nhóm đặt ba baseline, tất cả đều là checkpoint công bố chạy zero-shot không fine-tune:", "Nhóm đặt bốn baseline, tất cả đều là checkpoint công bố chạy zero-shot không fine-tune:"),
         ("nên cả B0 và V3 đều dịch sai", "nên cả B0 và V2 đều dịch sai"), ("bị V3 dịch thành “coast”", "bị V2 dịch thành “coast”"),
         ("Điều này được xác nhận bằng số đo tốc độ ở mục 6.4.", "Điều này được xác nhận bằng số đo tốc độ ở mục 6.6."),
         ("luồng dưới là luồng của sản phẩm, có thêm VAD chia đoạn và đầu vào từ micro.", "luồng dưới là luồng của sản phẩm, có thêm chia đoạn, bỏ lặp ở chỗ nối, đổi số và đầu vào từ micro."),
         ("vốn chỉ 1,52 giây ở p50", f"vốn chỉ {vn(t2['p50'])} giây ở p50"),
         ("Chia đoạn audio bằng VAD. ", "Chia đoạn audio dài. "), ("7.2 Hai bước xử lý phải thêm cho sản phẩm", "7.2 Các bước xử lý phải thêm cho sản phẩm"),
         ("nhận wav, mp3, flac, m4a, ogg;", "nhận wav, mp3, flac, ogg, và m4a nếu máy có ffmpeg;"),
         ("Thu âm trực tiếp dùng micro.", "Thu âm trực tiếp dùng micro, hiện kết quả theo từng đoạn trong lúc nói và nhận dạng lại cả bản khi bấm Stop."),
         ("Hai tuỳ chọn cho người dùng: bật tắt VAD (tắt thì dùng cửa sổ trượt, để so sánh hai cách), và đặt độ dài tối đa mỗi đoạn trong khoảng 5 đến 30 giây.", "Hai tuỳ chọn cho người dùng: bật VAD cho audio dài hơn 28 giây (mặc định tắt), và đặt độ dài tối đa mỗi đoạn trong khoảng 5 đến 30 giây."),
         ("liệt kê sáu giới hạn đã đo được", "liệt kê các giới hạn đã đo được"),
         (".github/workflows/ci.yml có bốn job chạy tuần tự:", ".github/workflows/ci.yml có năm job:"),
         ("Về baseline. Ba baseline chạy trên cùng tập test và cùng protocol.", "Về baseline. Bốn baseline chạy trên cùng tập test và cùng protocol."),
         ("Năm giả thuyết phân tích lỗi đều được kiểm bằng số: ba có bằng chứng, một đúng một phần, một không được ủng hộ.", f"Năm giả thuyết phân tích lỗi đều được kiểm bằng số: ba có bằng chứng, một đúng một phần, một không được ủng hộ. Baseline end-to-end Whisper-small đạt BLEU {kq}."),
         ("Cách này tăng BLEU cascade từ 22,69 lên 27,33 (+4,64, KTC 95% [3,32; 5,90], p < 0,001) và vẫn tăng có ý nghĩa khi đổi sang khối nghe thứ hai (+1,29 [0,56; 2,00]).", f"Cách này tăng BLEU cascade từ 22,69 lên {c} ({de}, KTC 95% {dci}, p < 0,001) và vẫn tăng có ý nghĩa khi đổi sang khối nghe thứ hai ({dw} {dwci})."),
         ("Khoảng cách giữa cascade và dịch văn bản chuẩn thu từ 15,58 xuống 10,94 BLEU. Bảng ablation cho thấy rõ thành phần nào đóng góp bao nhiêu.", f"Khoảng cách giữa cascade và dịch văn bản chuẩn thu từ 15,58 xuống {gap} BLEU. Bảng phiên bản và ablation một yếu tố cho thấy rõ thành phần nào đóng góp bao nhiêu."),
         ("Docker hai service tách giao diện khỏi suy luận. CI/CD bốn job, trong đó job build khởi động container thật và gọi thử endpoint.", f"Trên 857 bản FLEURS test, cả hệ đạt WER {vn(S.tat['WER_asr'])}%, BLEU {vn(S.tat['BLEU'])}, chrF++ {vn(S.tat['chrF++'])}. Cấu hình Docker hai service và CI/CD năm job đã viết nhưng chưa chạy thật."),
         ("+4,64 BLEU với PhoWhisper so với +1,29 với Whisper", f"{de} BLEU với PhoWhisper so với {dw} với Whisper"),
         ("Con số “7 đến 8 phiên song song”", "Con số “khoảng 8 phiên song song”"),
         ("Mọi thí nghiệm chạy trên một máy và một môi trường:", "Baseline và toàn bộ seed 42 chạy trên một máy và một môi trường:"),
         ("Toàn bộ chạy trên một máy duy nhất đã mô tả ở mục 4.2.", "Seed 42 chạy trên máy đã mô tả ở mục 4.2. Seed 1 và 2 train trên Modal, xem mục 6.2."),
         ("reports/toc_do/lap/*.json", "reports/toc_do/lap_V2/*.json"), ("ADAPTER_PATH=checkpoints/V4/best python app/gradio_app.py", "ADAPTER_PATH=none python app/gradio_app.py                 # baseline B0, mặc định là V2")])

p = tim(d, "[3] T. H. Nguyen")
sub(p, "[3] T. H. Nguyen, C. V. Nguyen, T. Q. Nguyen, and D. Q. Nguyen,", "[3] T. H. Nguyen, T.-D. H. Nguyen, D. Phung, D. T.-C. Nguyen, H. M. Tran, M. Luong, T. D. Vo, H. H. Bui, D. Phung, and D. Q. Nguyen,")
sub(p, "A high-quality and large-scale dataset for English–Vietnamese speech translation,", "A Vietnamese-English neural machine translation system,")
sub(p, "5543–5547", "5543–5544")
# ---- 1.5 kết quả tóm tắt
t = T_[1]
hang(t, 1, None, None, c, f"{de} {dci}"); hang(t, 2, None, None, w, f"{dw} {dwci}"); hang(t, 3, None, vn(S.giao0), vn(S.giao), f"+{vn(S.giao - S.giao0)}"); hang(t, 4, None, None, cl, f"{dcl} (đánh đổi)")
hang(t, 6, None, vn(t0["rtf"], 3), vn(t2["rtf"], 3), "nhanh hơn thời gian thực khoảng 8 lần"); hang(t, 7, None, f"{vn(t0['p95'])} s", f"{vn(t2['p95'])} s", "–")
them_hang(t, 4, "BLEU dịch văn bản chuẩn, trung bình 3 seed", vn(S.b0s["BLEU"]), B3.vi("V2", "test sạch"), f"{vn(SACH_TB).replace(chr(45), chr(8722))}")
them_hang(t, 1, "BLEU cascade, trung bình 3 seed", "22,69", B3.vi("V2", "test cascade"), f"+{vn(D_TB)} ± {vn(D_SD)}")
them_hang(t, 5, "BLEU cả hệ sản phẩm, có chia đoạn và đổi số", "–", vn(S.tat["BLEU"]), f"chrF++ {vn(S.tat['chrF++'])}")
them_hang(t, 2, "BLEU end-to-end B1, Whisper-small dịch trực tiếp", kq, "–", f"kém B0 {db1} {db1ci}")

# ---- 2.1 B1
p = tim(d, "Nhóm chọn cascade. Lý do định lượng")
chen_sau(p, f"Nhóm cũng đo thật một đối chứng end-to-end: Whisper-small với task=translate, không fine-tune, đạt BLEU {kq} trên cùng 857 bản thu, kém cascade B0 {db1} BLEU (mục 4.3). Số này chỉ nói về một checkpoint đa ngôn ngữ chạy nguyên bản, không phải giới hạn của mọi mô hình end-to-end.")
# ---- 3.5
p = tim(d, "Hiệu quả đã được đo, không chỉ đề xuất.")
sub(p, "và nhóm báo cáo đúng như vậy.", "và nhóm báo cáo đúng như vậy. Bản cuối V2 không dùng bước cân bằng theo câu và độ dài.")
sub(tim(d, "Nhóm chọn lấy mẫu lại và chỉ áp dụng trên tập train"), "chứ không huấn luyện khối nghe.", "chứ không huấn luyện khối nghe; audio nhiễu chỉ dùng để đo độ bền ở mục 4.5.")
# ---- 4 baseline
t = T_[5]; them_hang(t, 3, "End-to-end B1", "Whisper-small @973afd24, task=translate", "đối chứng end-to-end theo đề cương Task 1, không nhận là tái lập paper")
p = tim(d, "Khối dịch: fp16, beam 5, max_new_tokens 256")
chen_sau(p, "B1: cùng revision với Whisper-small, fp16, beam 5, batch 1, max_new_tokens 440, seed 42, language=vi, task=translate; bản thu dài hơn 30 giây chạy long-form như khối nghe. B1 không sinh transcript tiếng Việt nên không có WER.")
t = T_[6]; them_hang(t, 8, "B1 Whisper-small task=translate · FLEURS test", "NOT RUN", f"BLEU {kq} · chrF++ {kqc}", "–")
sub(tim(d, "Nguồn: reports/asr/results_task2.csv, paper_comparison.csv"), "runs/mt/B0/*/score.json.", "runs/mt/B0/*/score.json, runs/mt/B1_whisper-small_translate/fleurs_test_audio/score.json, reports/mt/bootstrap_B0_fleurs_test_asr_pho_vs_B1.json.")
p = tim(d, "Con số quan trọng nhất của mục này")
chen_sau(p, f"Baseline end-to-end B1 đạt BLEU {kq}, chrF++ {kqc}, kém cascade B0 {db1} BLEU, KTC 95% {db1ci}. Có 86/857 câu bị lặp vòng khi giải mã. B1 được ghi là baseline đối chứng theo đề cương; phần so với số của paper Whisper chưa làm nên ghi NOT RUN.")
# ---- 4.5 độ bền
p96 = tim(d, "Chuẩn hoá số là nguồn lỗi có thể xử lý")
tieu = copy.deepcopy(tim(d, "4.4 Phân tích lỗi baseline")._p); p96._p.addnext(tieu)
from docx.text.paragraph import Paragraph
tieu = Paragraph(tieu, p96._parent); dat(tieu, "4.5 Độ bền khối nghe khi audio bị nhiễu")
gt = chen_sau(tieu, "PhoWhisper-small được đo lại trên 857 bản FLEURS test sau khi thêm nhiễu nhân tạo. Mỗi điều kiện đổi đúng một yếu tố so với bản gốc. Đây chỉ là bài đo độ bền: khối nghe không được fine-tune, kết quả không dùng để chọn mô hình.", kieu=tim(d, "Nhóm đặt năm giả thuyết trước khi có số"))
R = robust(); goc = R[0][3]["WER_percent"] if "WER_percent" in R[0][3] else None
hangs = [("Điều kiện", "WER", "CER", "Chênh WER so với bản gốc")]
for k, v, e, s in R:
    if s is None:
        hangs.append((v, "NOT RUN", "NOT RUN", "–"))
    else:
        hangs.append((v, f"{vn(s['WER_percent'])}%", f"{vn(s['CER_percent'])}%", "–" if k == "goc" else f"{float(s['WER_percent']) - float(goc):+.2f}".replace(".", ",").replace("-", "−")))
bg = chep_bang(T_[5], gt, [(h[0], h[1], h[2]) for h in hangs])
from docx.oxml.ns import qn
tbl = bg._tbl
# bảng 3 cột: gộp chênh vào cột WER để không đổi lưới bảng
for i, h in enumerate(hangs):
    if i == 0:
        hang(bg, 0, "Điều kiện", "WER (chênh so với bản gốc)", "CER")
    else:
        hang(bg, i, h[0], h[1] if h[3] == "–" else f"{h[1]} ({h[3]} điểm)", h[2])
ng = chen_sau(bg, "Nguồn: runs/robust/robust_pho_*/score/summary.json, scripts/asr/tao_audio_robust.py, scripts/hang_doi_robust.sh. Nhiễu tất định theo id bản thu, seed 42. Chấm bằng score_asr.py, cùng protocol ASR.", kieu=tim(d, "Nguồn: env/moi_truong.json"))
chen_sau(ng, f"WER tăng từ {vn(R[0][3]['WER_percent'])}% lên {vn(R[2][3]['WER_percent'])}% ở nhiễu 10 dB, là mức giảm nặng nhất; các điều kiện còn lại tăng dưới 3 điểm. Đổi tốc độ còn làm thay đổi độ dài audio nên ảnh hưởng cả nhóm bản thu dài hơn 30 giây. Đây là nhiễu trắng và đổi tốc độ bằng resample, không phải tiếng ồn lớp học hay micro thật, nên số trên chỉ cho biết xu hướng. Câu hỏi hệ chạy thế nào ngoài dataset vẫn cần bộ audio tự thu.", kieu=tim(d, "Ba kết luận rút ra."))
# ---- 5
hang(T_[8], 1, None, None, "cân bằng giữa dung lượng adapter và khả năng học; ablation rank 8 và rank 32 không khác rank 16 có ý nghĩa (mục 6.2)")
# ---- 6.2
sub(tim(d, "6.2 Bảng ablation"), "6.2 Bảng ablation", "6.2 Bảng phiên bản và ablation")
t = T_[10]; hang(t, 3, "V2 ★"); hang(t, 4, "V3")
sub(tim(d, "★ = bản cuối theo quy tắc định trước"), "★ = bản cuối theo quy tắc định trước: BLEU dev cascade cao nhất. Nguồn: reports/tong_hop/ablation.csv, reports/mt/bootstrap_*.json.", "★ = bản cuối, chọn theo quy tắc dưới đây. Nguồn: reports/ablation/bang_ablation.csv, reports/mt/bootstrap_*.json.")
pc = tim(d, "★ = bản cuối, chọn theo quy tắc")
q1 = chen_sau(pc, f"Chọn bản cuối. Quy tắc ban đầu là lấy BLEU dev cascade cao nhất và cho ra V3 (26,71). Vì chênh lệch dev giữa V1–V4 rất nhỏ, ngày 03/11/2026 nhóm chốt lại: bản cách mức cao nhất không quá 0,5 BLEU được coi là hoà, trong nhóm hoà chọn BLEU dev dịch sạch cao nhất. Bốn bản đều hoà, V2 có dev sạch {dsach('V2')} cao nhất nên V2 là bản cuối.", kieu=tim(d, "Đóng góp của từng thành phần"))
q2 = chen_sau(q1, "Cần nói rõ giới hạn của phép chọn này: quy tắc chỉ dùng số dev, nhưng được chốt sau khi nhóm đã thấy số test của V1–V4, và ngưỡng 0,5 có tham khảo mức chênh trên test. Vì vậy đây không phải lựa chọn mù với test. Riêng ba bản ablation được chạy sau khi quy tắc đã ghi file (reports/ablation/QUY_TAC_CHON.md, chon_ban_cuoi.json).", kieu=tim(d, "Đóng góp của từng thành phần"))
sua = lambda k: ab[k]["Δ test cascade so với V2 (KTC 95%)"].split(", p")[0].replace(".", ",").replace("-", "−")
hb_ = [("Bản", "Dev cascade", "Dev sạch", "Test cascade", "Test sạch", "Δ test cascade so với V2 (KTC 95%)")]
for k, ten in (("V1", "V1"), ("V2", "V2 ★"), ("V3", "V3"), ("V4", "V4"), ("A_r8", "A_r8: rank 8"), ("A_r32", "A_r32: rank 32"), ("A_aug", "A_aug: thêm transcript sạch")):
    r = ab[k]; hb_.append((ten, vn(r["dev cascade"]), vn(r["dev sạch"]), vn(r["test cascade"]), vn(r["test sạch"]), sua(k) if k.startswith("A_") else "–"))
bn = chep_bang(T_[10], q2, hb_)
ng2 = chen_sau(bn, "Nguồn: reports/ablation/bang_ablation.csv, reports/mt/bootstrap_V2_A_*.json, checkpoints/A_*.", kieu=tim(d, "Nguồn: env/moi_truong.json"))
chen_sau(ng2, f"Ablation một yếu tố so với V2. Rank 8 và rank 32 không khác V2 có ý nghĩa trên test: {sua('A_r8')} và {sua('A_r32')}. Rank 32 có test cascade cao nhất ({vn(ab['A_r32']['test cascade'])}) nhưng dev cascade thấp hơn nhóm hoà nên không được chọn. Thêm 2.926 cặp transcript sạch làm dev sạch tăng lên {dsach('A_aug')} nhưng dev cascade giảm còn {vn(ab['A_aug']['dev cascade'])}, test cascade kém V2 có ý nghĩa: {sua('A_aug')}.", kieu=tim(d, "Đóng góp của từng thành phần"))
aa = tim(d, "Ablation một yếu tố so với V2.")
sub(aa, "test cascade kém V2 có ý nghĩa: ", "test cascade kém V2: ")
q3 = chen_sau(aa, f"Kiểm tra 3 seed. Bảng trên dùng seed 42. Nhóm train thêm seed 1 và 2 cho cả bảy bản với cấu hình giữ nguyên. Các seed mới train trên Modal (RTX PRO 6000, torch 2.7.1) vì GPU này không chạy được torch 2.0.1, nhưng dịch và chấm bằng torch 2.0.1 như seed 42: cùng adapter V2 cho dev 26,45 khi chấm bằng torch 2.0.1 và 26,24 khi chấm bằng torch 2.7.1. Quy tắc xử lý được ghi file trước khi train seed mới (reports/ba_seed/QUY_TAC_3SEED.md).", kieu=tim(d, "Đóng góp của từng thành phần"))
hb3 = [("Bản", "Dev cascade", "Dev sạch", "Test cascade", "Test sạch", "Δ test cascade so với V2")]
for k, ten in (("V1", "V1"), ("V2", "V2 ★"), ("V3", "V3"), ("V4", "V4"), ("A_r8", "A_r8: rank 8"), ("A_r32", "A_r32: rank 32"), ("A_aug", "A_aug: thêm transcript sạch")):
    hb3.append((ten, B3.vi(k, "dev cascade"), B3.vi(k, "dev sạch"), B3.vi(k, "test cascade"), B3.vi(k, "test sạch"), B3.d(k, "test cascade").replace(".", ",").replace("-", "−") if k.startswith("A_") else "–"))
b3 = chep_bang(T_[10], q3, hb3)
ng3 = chen_sau(b3, "Trung bình ± độ lệch chuẩn của seed 42, 1, 2. Cột cuối so theo từng cặp cùng seed. Nguồn: reports/ba_seed/bang_3seed.csv, bang_ablation_3seed.csv, ket_qua_3seed.json, notebooks/04_kiem_tra_3_seed.ipynb.", kieu=tim(d, "Nguồn: env/moi_truong.json"))
q4 = chen_sau(ng3, f"Kết luận chính giữ nguyên: V2 hơn B0 +{vn(D_TB)} ± {vn(D_SD)} BLEU cascade, và seed nào cũng hơn B0 trên 4,5 BLEU. Áp quy tắc trên trung bình dev, nhóm hoà còn V1 và V2, và V2 vẫn được chọn. Lợi thế dev của V3 ở seed 42 không lặp lại: trung bình chỉ {B3.vi('V3', 'dev cascade')}. V1 có test cascade trung bình cao hơn V2 ({B3.vi('V1', 'test cascade')}) nhưng nhóm không chọn theo test. Đổi rank không tạo khác biệt rõ, còn thêm transcript sạch làm test cascade thấp hơn V2 ở cả ba seed.", kieu=tim(d, "Đóng góp của từng thành phần"))
chen_sau(q4, f"Hạn chế của phép kiểm này: V1 đến V4 và ablation có seed train khác môi trường. Train lại V2 seed 42 trên Modal cho dev {vn(DC['dev cascade']['seed 42 Modal (train torch 2.7.1)'])} so với {vn(DC['dev cascade']['seed 42 máy nhóm (torch 2.0.1)'])}, test cascade {vn(DC['test cascade']['seed 42 Modal (train torch 2.7.1)'])} so với {vn(DC['test cascade']['seed 42 máy nhóm (torch 2.0.1)'])}. Riêng việc đổi môi trường đã làm số lệch gần bằng dao động giữa các seed. Ba seed chỉ cho biết mức dao động, chưa đủ cho kết luận thống kê riêng.", kieu=tim(d, "Đóng góp của từng thành phần"))
p = tim(d, "Cải thiện với cả hai baseline khối nghe.")
sub(p, "Với PhoWhisper, cascade tăng 22,69 → 27,33 (+4,64, p < 0,001). Với Whisper-small, cascade tăng 18,58 → 19,86 (+1,29 [0,56; 2,00], p = 0,001).", f"Với PhoWhisper, cascade tăng 22,69 → {c} ({de}, p < 0,001). Với Whisper-small, cascade tăng 18,58 → {w} ({dw} {dwci}, p = {vn(S.dw['p_one_sided_delta_le_0'], 3)}).")
# ---- 6.4
t = T_[13]
ex = {json.loads(l)["id"]: json.loads(l) for l in open(T / "runs/mt/V2/fleurs_test_asr_pho/hyp.jsonl", encoding="utf-8")}
ex0 = {json.loads(l)["id"]: json.loads(l) for l in open(T / "runs/mt/B0/fleurs_test_asr_pho/hyp.jsonl", encoding="utf-8")}
a1, a2 = "3554584753359809648.wav", "5600578667047148114.wav"
hang(t, 1, None, None, f"{a2} · 11,82 s · miền Giáo dục"); hang(t, 2, None, None, ex[a2]["src"]); hang(t, 3, None, None, ex[a2]["ref"]); hang(t, 4, None, None, ex0[a2]["hyp"]); hang(t, 5, "V2", ex[a1]["hyp"], ex[a2]["hyp"])
thay(d, [("runs/mt/V3/fleurs_test_asr_pho/hyp.jsonl", "runs/mt/V2/fleurs_test_asr_pho/hyp.jsonl")])
dat(tim(d, "Ví dụ 1 cho thấy V3"), "Ví dụ 1 cho thấy V2 sửa được lỗi nghĩa: “bản đồ kho báu” bị khối nghe nghe thành “bản đồ kho báo”, và B0 dịch thành “newspaper warehouse map” — sai hoàn toàn. V2 đoán được ý “a map of the treasure trove”.")
dat(tim(d, "Ví dụ 2 cho thấy V3"), "Ví dụ 2 cho thấy V2 xử lý được số đọc thành chữ: khối nghe viết “hai mươi lăm đến ba mươi năm”, B0 dịch nguyên văn “twenty - five to thirty years” còn V2 viết lại đúng “25 to 30 years”. Ca này không phải lúc nào cũng đúng: ở bản thu 397388263370720788.wav, V2 dịch “1920” thành “the 1990s”.")
hang(T_[14], 0, None, None, None, None, None, "V2 ★")
# ---- 6.6
t = T_[15]
hang(t, 1, None, vn(t0["rtf"], 3), vn(t0["asr"], 3), vn(t0["mt"], 3), f"{vn(t0['p50'])} s", f"{vn(t0['p95'])} s", f"{vn(t0['vram'])} GiB", f"{vn(t0['ram'])} GiB", f"{vn(t0['size'])} GB")
hang(t, 2, "V2", vn(t2["rtf"], 3), vn(t2["asr"], 3), vn(t2["mt"], 3), f"{vn(t2['p50'])} s", f"{vn(t2['p95'])} s", f"{vn(t2['vram'])} GiB", f"{vn(t2['ram'])} GiB", f"{vn(t2['size'])} GB")
sub(tim(d, "Nguồn: reports/toc_do/lap_V2/*.json"), "trung vị ba lần đo xen kẽ B0 và V3", "trung vị ba lần đo xen kẽ B0, V2 và V4 trong cùng phiên 04/11/2026")
dat(tim(d, "Adapter không làm hệ chậm đi."), f"Adapter không làm hệ chậm đi. RTF ba lần đo của V2 là {' / '.join(vn(x, 3) for x in t2['lan'])} và của B0 là {' / '.join(vn(x, 3) for x in t0['lan'])}. Chênh lệch nằm trong khoảng dao động giữa các lần đo, nên cách phát biểu đúng là thêm adapter không làm chậm, chứ không phải V2 nhanh hơn B0. Lý do: adapter được merge vào trọng số trước khi suy luận.")
dat(tim(d, "Khối nghe chiếm khoảng 70% thời gian."), f"Khối nghe chiếm khoảng {t2['asr'] / t2['rtf'] * 100:.0f}% thời gian. Nếu sau này cần tăng tốc thì phải tối ưu khối nghe trước, không phải khối dịch.")
dat(tim(d, "RTF 0,128 nghĩa là"), f"RTF {vn(t2['rtf'], 3)} nghĩa là một phút audio xử lý trong khoảng {vn(t2['rtf'] * 60, 1)} giây. Nếu chỉ xét tỉ lệ này thì một GPU có thể phục vụ khoảng 8 phiên song song, nhưng đó là chặn trên lý thuyết vì phép đo chạy batch 1 trên một tiến trình, chưa kiểm tải đồng thời. Số tốc độ các bản trước đo ở phiên khác nên không so trực tiếp với bảng này.")
# ---- 7
dat(tim(d, "Sơ đồ tách làm hai luồng"), "Sơ đồ tách làm hai luồng vì đây là hai thứ khác nhau và trộn chúng lại sẽ thành báo cáo sai. Luồng thực nghiệm nhận tệp WAV 16 kHz có sẵn trong dataset và không chia đoạn, đúng theo protocol đã khoá. Luồng sản phẩm thêm đầu vào từ micro hoặc tệp người dùng, bước chia đoạn trước khối nghe, bỏ lặp ở chỗ nối và đổi số trước khi dịch. Số của hai luồng được báo riêng.")
dat(tim(d, "Cách xử lý trong src/audio.py"), "Cách xử lý trong src/audio.py: audio không quá 28 giây giữ nguyên một đoạn. Audio dài hơn được chia thành các đoạn không quá 28 giây (để lại biên an toàn so với 30), và mỗi điểm cắt được dời tới chỗ nhỏ tiếng nhất trong khoảng ±3 giây để không cắt giữa từ. Sau khi nhận dạng, hàm bo_lap_cho_noi bỏ cụm từ hai từ trở lên bị lặp ở chỗ nối giữa hai đoạn, rồi ghép lời lại trước khi dịch. VAD theo năng lượng vẫn có nhưng là tuỳ chọn.")
dat(tim(d, "Một quyết định thiết kế cần nói rõ"), "Một quyết định thiết kế cần nói rõ: bản đầu bật VAD mặc định và cắt cả audio ngắn. Kiểm thử với model thật cho thấy cách đó làm WER tăng lên 34,79% so với 15,05% trên 20 mẫu ngắn, nên VAD chuyển thành tuỳ chọn, mặc định tắt, chỉ áp dụng cho audio dài hơn 28 giây.")
dat(tim(d, "Bước chuẩn hoá số đọc thành chữ"), "Đổi số đọc thành chữ. src/so.py đổi số do khối nghe viết bằng chữ sang chữ số trước khi dịch, vì dữ liệu dịch dùng chữ số. Lời gốc vẫn được giữ để đối chiếu. Bước này chỉ sửa cách viết, nếu khối nghe đã nghe sai thì không sửa được.")
p = tim(d, "Đổi số đọc thành chữ.")
q = chen_sau(p, f"Kết quả đo cả hệ. Trên 857 bản FLEURS test, adapter V2 kèm các bước trên đạt WER {vn(S.tat['WER_asr'])}%, BLEU {vn(S.tat['BLEU'])}, chrF++ {vn(S.tat['chrF++'])}, RTF {vn(S.tat['RTF'], 3)}. So với cách xử lý cũ (cắt đều, không đổi số), BLEU tăng {vn(S.hb['delta'])}, KTC 95% {ci(S.hb)}, chưa có ý nghĩa thống kê. Riêng {S.hb['cau_co_chu_so']['n']} câu có chữ số tăng {vn(S.hb['cau_co_chu_so']['BLEU_A'])} → {vn(S.hb['cau_co_chu_so']['BLEU_B'])}, và 10 bản thu dài hơn 28 giây tăng {vn(S.ht['truoc_0411']['dai']['BLEU'])} → {vn(S.dai['BLEU'])}. Các bước này đo trực tiếp trên test để nghiệm thu sản phẩm, không dùng chọn mô hình và chưa đo riêng trên dev. Nguồn: reports/he_thong_V2/ket_qua.json, bootstrap_cu_vs_moi.json.")
sub(tim(d, "Lý do tách: service suy luận"), "hai phần scale độc lập được.", "hai phần scale độc lập được. Docker chưa được build và chạy thật trên máy nhóm, phần này mới dừng ở cấu hình.")
sub(tim(d, "Job build không chỉ build"), "chứ không chỉ kiểm cú pháp.", "chứ không chỉ kiểm cú pháp. CI chưa chạy lần nào vì repo chưa đẩy lên GitHub; lint và pytest đã chạy tay trên máy nhóm.")
t = T_[19]; them_hang(t, 2, "cai-sach", "cài requirements.txt trong môi trường sạch, chạy pip check, lưu log làm artifact")
t = T_[20]
hang(t, 1, None, "47"); hang(t, 2, None, "20"); hang(t, 3, None, "21")
them_hang(t, 3, "tests/test_pipeline.py, test_so.py, test_truc_tiep.py, test_adapter.py", "63", "ghép hai khối, đổi số, thu âm trực tiếp, nạp adapter")
sub(tim(d, "Thứ hai, scorer trong src/evaluate.py"), "Đây là xác nhận độc lập cho cả scorer và các con số trong báo cáo.", "Đây là xác nhận độc lập cho cả scorer và các con số trong báo cáo.")
p = tim(d, "Hai kết quả kiểm chứng đáng ghi lại.")
chen_sau(p, "Tổng cộng 151 test: 145 qua, 6 bỏ qua vì cần ffmpeg, 0 trượt. Ruff 0.5.7 đạt. Ngoài unit test, demo và API đã chạy với model thật: file rỗng, file hỏng, audio im lặng, nhiều lượt liên tiếp và ba người dùng cùng lúc đều xử lý được (reports/he_thong_V2/thu_gradio/). Nghiệm thu với model thật đạt 6/7 mục; mục còn lại là m4a và webm, trượt vì máy không có ffmpeg. Micro thật và 20 câu tự thu chưa làm.")
# ---- 7.9
t = T_[21]
hang(t, 0, None, None, None, None, "Kết quả V2")
hang(t, 1, None, None, None, None, f"{de} {dci}"); hang(t, 2, None, None, None, None, f"{dw} {dwci}"); hang(t, 3, None, None, None, None, f"15,58 → {gap}")
hang(t, 4, None, None, None, None, f"{cl}, tức {dcl}"); hang(t, 5, None, None, None, None, vn(t2["rtf"], 3)); hang(t, 6, None, None, None, None, f"{vn(t2['p95'])} s"); hang(t, 8, None, None, None, None, f"2,69 GB · {vn(t2['ram'])} GiB")
dat(tim(d, "Kết luận: hệ thống khả thi"), f"Kết luận: hệ thống khả thi để đóng gói thành ứng dụng web chạy trên GPU. Trong bảy tiêu chí có ngưỡng, sáu tiêu chí đạt và một chưa đạt; kích thước và RAM là mục đo và báo cáo. Tiêu chí “không giảm BLEU khi dịch văn bản chuẩn” thì adapter V2 seed 42 thấp hơn ngưỡng {vn(-S.dcl)} BLEU, trung bình 3 seed thấp hơn {vn(-SACH_TB)}, và không seed nào đạt. Nhóm không diễn giải lại ngưỡng cho vừa kết quả nên ghi chưa đạt.")
xoa(tim(d, "Chọn bản nào cho sản phẩm.")); xoa(T_[22]); xoa(tim(d, "Hai bản không phân biệt được về cascade")); xoa(tim(d, "Một ghi chú khi chọn"))
# ---- 8
dat(tim(d, "Về điều kiện thu âm."), "Về điều kiện thu âm. Toàn bộ số chính đo trên audio đọc rõ, một người nói, phòng yên tĩnh. Mục 4.5 mới đo nhiễu nhân tạo; chưa đo với hội thoại tự nhiên, nhiều người nói chồng tiếng hay tiếng ồn thật. Chưa thử micro điện thoại. Kết quả trên audio thật rất có thể kém hơn số trong báo cáo.")
dat(tim(d, "Về đánh đổi."), f"Về đánh đổi. V2 thấp hơn baseline {vn(-SACH_TB)} BLEU khi dịch văn bản chuẩn theo trung bình 3 seed, nên tiêu chí này ghi là chưa đạt. Quy tắc chọn bản cuối chốt sau khi đã thấy số test của V1–V4, như đã nói ở mục 6.2. Seed 42 và hai seed còn lại train ở hai môi trường khác nhau.")
p = tim(d, "Về dữ liệu tự thu.")
sub(p, "và nó làm yếu phần đánh giá tính tổng quát.", "và nó làm yếu phần đánh giá tính tổng quát. Bộ 20 câu tự thu đã soạn sẵn trong tests/bo_cau_tu_thu/ nhưng chưa thu.")
chen_sau(p, "Về triển khai. Docker và GitHub Actions chưa chạy thật. Đọc m4a và webm cần ffmpeg, chưa kiểm được trên máy nhóm. Micro thật chưa đo WER.", kieu=p)
dat(tim(d, "Làm được ngay, tác động trung bình."), "Làm được ngay, tác động trung bình. Bước đổi số đã có trong sản phẩm nhưng mới đo trên test; nên đo riêng trên dev và mở rộng cho ngày tháng, đơn vị đo. Phân tích lỗi cho thấy câu có chữ số có WER 27,43% so với 5,89%, nên đây là nguồn lỗi đáng kể.")
dat(tim(d, "Cần thêm công, tác động rõ."), "Cần thêm công, tác động rõ. Đo lại cách chia đoạn trên audio bài giảng thật dài vài phút. Hiện bước chia đoạn mới được chấm trên 10 bản thu FLEURS dài hơn 28 giây, và đã kiểm chạy được với audio 1, 3 và 5 phút nhưng chưa có nhãn để chấm.")
dat(tim(d, "Hướng dài hơn."), f"Hướng dài hơn. B1 cho thấy Whisper-small chạy nguyên bản chỉ đạt BLEU {kq}. Để kiểm giả thuyết ở mục 2.1 rằng dữ liệu là yếu tố quyết định, cần một mô hình end-to-end được huấn luyện trên dữ liệu audio kèm bản dịch, có thể lấy từ IWSLT hoặc MTet.")
# ---- phụ lục
hang(T_[24], 3, None, None, None, "chạy pipeline dữ liệu, các baseline, bốn phiên bản LoRA, ablation một yếu tố, sửa và chạy B1, kiểm tra 3 seed, bootstrap, phân tích lỗi, đo tốc độ, đo độ bền, đánh giá cả hệ, notebook, workbook, tích hợp repo cuối, mục 5 và 6 của báo cáo")
hang(T_[24], 4, None, None, None, "kiến trúc hệ thống, rubric khả thi, chia đoạn, demo Gradio, API FastAPI, Docker, CI/CD, test, gói baseline bàn giao (B1 bản đầu, gap analysis), mục 1, 2, 7, 8 và ghép toàn bộ báo cáo cùng slide")
t = T_[25]
hang(t, 1, None, "audio.py chuẩn hoá và chia đoạn, so.py đổi số, pipeline.py ghép hai khối, truc_tiep.py thu âm trực tiếp, evaluate.py chấm điểm, inference.py suy luận dòng lệnh")
hang(t, 5, None, "ci.yml năm job"); hang(t, 6, None, "151 test cho audio, đổi số, scorer, API, pipeline, thu âm trực tiếp, adapter")
hang(t, 7, "configs/", "protocol ASR, bản chốt, cấu hình từng phiên bản")
for i, k in ((8, "data/"), (9, "asr/"), (10, "mt/"), (11, "domain/")):
    hang(t, i, f"experiments/reports/{k}")
hang(t, 12, "experiments/reports/toc_do/", "các lần đo tốc độ; lap_V2/ là phiên dùng trong báo cáo")
hang(t, 13, "experiments/reports/tong_hop/, ablation/", "bảng phiên bản, ablation, quy tắc chọn, flowchart, biểu đồ")
hang(t, 14, "experiments/runs/asr/, robust/"); hang(t, 14, None, "dự đoán thô và kết quả chấm bốn run baseline, năm điều kiện độ bền")
hang(t, 15, "experiments/runs/mt/, b1/, ba_seed/", "bản dịch và score của B0, B1, V1 đến V4, ba bản ablation và các seed mới")
hang(t, 16, "checkpoints/", "adapter tốt nhất V1 đến V4 và ba bản ablation, đủ 3 seed, kèm config, log, curves")
hang(t, 17, "experiments/nghe_kiem/", "10 audio nghe kiểm và kết quả nghe"); hang(t, 18, "notebooks/, reports/", "notebook có output, 00_toan_bo_code gom toàn bộ code, workbook, KIEM_THU_CUOI.md")
p = tim(d, "Hai thứ không có trong gói")
sub(p, "Hai thứ không có trong gói: dữ liệu gốc khoảng 12 GB", "Những thứ không có trong gói: checkpoint từng epoch, dữ liệu gốc khoảng 12 GB")
chen_sau(p, "Các đường dẫn nguồn trong báo cáo tính từ thư mục experiments/ của repo.", kieu=p)
doi_hinh(d, 0, H / "kien_truc_he_thong.png")

tach_dam(d, "Thứ tư, đóng gói thành sản phẩm", "Thứ tư, đóng gói thành sản phẩm")
tach_dam(d, "Khối nghe chiếm khoảng", tim(d, "Khối nghe chiếm khoảng").text.split(". ")[0] + ".")
out = O / "1_bao_cao"; out.mkdir(exist_ok=True); d.save(out / "BaoCao_Project_Nhom.docx"); print("Báo cáo xong")
