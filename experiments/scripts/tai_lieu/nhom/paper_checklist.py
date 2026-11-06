#!/usr/bin/env python3
"""Paper LNCS và checklist theo bản cuối V2."""
from docx import Document
from chung import *
from chung import _gop

t0, t2 = S.t0, S.t2; ab = S.ab
# ======== PAPER
d = Document(G / "3_paper/Paper_Springer_LNCS.docx"); Tb = d.tables
c = en(S.c["BLEU"]); de = f"+{en(S.d['delta'])}"; dci = ci(S.d, en); gap = en(S.gap); w = en(S.w["BLEU"]); dw = f"+{en(S.dw['delta'])}"; dwci = ci(S.dw, en); k1 = en(S.b1["BLEU"])
dcl = en(-S.dcl); rt = en(t2["rtf"], 3)
sua = lambda k: ab[k]["Δ test cascade so với V2 (KTC 95%)"].split(", p")[0].replace(";", ",").replace("-", "−")
thay(d, [("6.1 Ablation", "6.1 Variants and ablation"),
         ("This raises cascade BLEU to 27.33 (+4.64, 95% CI [3.32, 5.90], p < 0.001 under paired bootstrap over 347 sentence clusters) and narrows the gap to clean-text translation from 15.58 to 10.94 BLEU.",
          f"This raises cascade BLEU to {c} ({de}, 95% CI {dci}, p < 0.001 under paired bootstrap over 347 sentence clusters) and narrows the gap to clean-text translation from 15.58 to {gap} BLEU."),
         ("(+1.29 BLEU with Whisper-small)", f"({dw} BLEU with Whisper-small)"),
         ("An ablation over four variants shows that only the first component — training on real ASR output — improves the primary metric significantly; the remaining three preserve clean-text translation quality instead.",
          f"Four successive variants and a one-factor ablation show that only training on real ASR output improves the primary metric significantly. An unadapted end-to-end Whisper-small baseline reaches only {k1} BLEU."),
         ("The complete system runs at RTF 0.128", f"The complete system runs at RTF {rt}"),
         ("recovers 4.64 BLEU of that loss", f"recovers {en(S.d['delta'])} BLEU of that loss"),
         ("and report honestly that three of four components do not improve the primary metric.", "and report honestly that the later components do not improve the primary metric."),
         ("Rank 16 balances adapter size against capacity; higher ranks overfit 2,926 examples.", "Rank 16 balances adapter size against capacity; ranks 8 and 32 show no significant difference."),
         ("Table 5. Ablation. ★ marks the final system under the pre-registered rule (highest dev cascade BLEU). CI from paired bootstrap, 1,000 replicates, clustered by sent_id.", "Table 5. Variants. ★ marks the final system (see text). CI from paired bootstrap, 1,000 replicates, clustered by sent_id."),
         ("The central measurement of this paper: 38.27 − 22.69 = 15.58 BLEU lost to recognition errors.", f"The central measurement of this paper: 38.27 − 22.69 = 15.58 BLEU lost to recognition errors. As an end-to-end control, unadapted Whisper-small with task=translate scores {k1} BLEU and {en(S.b1['chrF++'])} chrF++ on the same recordings, {en(-S.db1['delta'])} BLEU below the cascade, with 86 of 857 outputs looping; this describes one multilingual checkpoint, not end-to-end systems in general."),
         ("With PhoWhisper, cascade BLEU rises 22.69 → 27.33 (+4.64, p < 0.001); with Whisper-small, 18.58 → 19.86 (+1.29 [0.56, 2.00], p = 0.001).", f"With PhoWhisper, cascade BLEU rises 22.69 → {c} ({de}, p < 0.001); with Whisper-small, 18.58 → {w} ({dw} {dwci}, p = {en(S.dw['p_one_sided_delta_le_0'], 3)})."),
         ("becomes “coast” under V3 while", "becomes “coast” under V2 while"),
         ("Table 8. Timing and resources. Median of three interleaved runs,", "Table 8. Timing and resources. Median of three interleaved runs in one session,"),
         ("10.76% WER and BLEU rising 26.56 → 30.92 under V3.", f"10.76% WER and BLEU rising 26.56 → {en(S.giao)} under V2."),
         ("gives 11.60% WER and 21.69 → 25.32.", f"gives 11.60% WER and 21.69 → {en(S.dl)}."),
         ("performs worst at 19.18% WER and 18.47 → 23.17,", f"performs worst at 19.18% WER and 18.47 → {en(S.tin)},"),
         ("(+4.64 BLEU with PhoWhisper against +1.29 with Whisper-small)", f"({de} BLEU with PhoWhisper against {dw} with Whisper-small)"),
         ("the seven-to-eight concurrent sessions implied by RTF", "the roughly eight concurrent sessions implied by RTF"),
         ("and reduced it to 10.94 by adapting", f"and reduced it to {gap} by adapting"),
         ("add number normalisation with development-set validation; and re-measure recognition after segmentation.", "validate number normalisation on development data; and evaluate segmentation on real lecture recordings."),
         ("3. Nguyen, T.H., Nguyen, C.V., Nguyen, T.Q., Nguyen, D.Q.: A high-quality and large-scale dataset for English–Vietnamese speech translation.", "3. Nguyen, T.H., Nguyen, T.-D.H., Phung, D., Nguyen, D.T.-C., Tran, H.M., Luong, M., Vo, T.D., Bui, H.H., Phung, D., Nguyen, D.Q.: A Vietnamese-English neural machine translation system."),
         ("5543–5547", "5543–5544")])
thay(d, [("All experiments run on one machine:", "Baselines and all seed 42 runs use one machine:")])
hang(Tb[2], 3, "V2 ★"); hang(Tb[2], 4, "V3")
hang(Tb[5], 1, None, en(t0["rtf"], 3), f"{en(t0['p50'])} s", f"{en(t0['p95'])} s", f"{en(t0['vram'])} GiB", f"{en(t0['ram'])} GiB", f"{en(t0['size'])} GB")
hang(Tb[5], 2, "V2", rt, f"{en(t2['p50'])} s", f"{en(t2['p95'])} s", f"{en(t2['vram'])} GiB", f"{en(t2['ram'])} GiB", f"{en(t2['size'])} GB")
p = tim(d, "Differences among V1 to V4")
dat(p, f"Differences among V1 to V4 on test cascade BLEU fall inside the bootstrap confidence intervals, so we do not claim any variant is superior on that metric. Selection used development data only: our first rule, highest dev cascade BLEU, gave V3 (26.71). As dev differences were small, on 3 Nov 2026 we revised it: variants within 0.5 BLEU of the best tie, and the tie goes to the highest dev clean-text BLEU. All four tie and V2 wins ({en(ab['V2']['dev sạch'])}). This revision came after V1–V4 test scores were known, and the 0.5 margin drew on them, so the choice is not blind to the test set; only the ablation runs below followed the written rule.")
dc_ = DC["dev cascade"]; tc_ = DC["test cascade"]
q_ = chen_sau(p, f"Three-seed check. Seeds 1 and 2 were trained in the cloud (RTX PRO 6000, PyTorch 2.7.1) and scored with PyTorch 2.0.1 like seed 42, since one adapter scores dev {26.45} under 2.0.1 but 26.24 under 2.7.1. V2 reaches {B3.eng('V2', 'test cascade')} test cascade and {B3.eng('V2', 'test sạch')} clean-text, +{en(D_TB)} ± {en(D_SD)} over B0. The rule applied to mean dev scores still selects V2; V3's dev lead disappears ({B3.eng('V3', 'dev cascade')}), and V1's higher mean test score ({B3.eng('V1', 'test cascade')}) was not used for selection. Rank has no clear effect ({B3.eng('A_r8', 'test cascade')} and {B3.eng('A_r32', 'test cascade')}); added clean transcripts lower test cascade on every seed ({B3.eng('A_aug', 'test cascade')}). Retraining V2 seed 42 in the cloud moved dev from {en(dc_['seed 42 máy nhóm (torch 2.0.1)'])} to {en(dc_['seed 42 Modal (train torch 2.7.1)'])} and test from {en(tc_['seed 42 máy nhóm (torch 2.0.1)'])} to {en(tc_['seed 42 Modal (train torch 2.7.1)'])}, so the training environment matters about as much as the seed.")
chen_sau(q_, f"One-factor ablation against V2 changes a single setting each. At seed 42 rank 8 gives {sua('A_r8')}, rank 32 gives {sua('A_r32')} and adding 2,926 clean transcript pairs gives {sua('A_aug')} on test cascade.")
dat(tim(d, "Three observations. The adapter does not slow"), f"Three observations. The adapter does not slow the system: per-run RTF values are {' / '.join(en(x, 3) for x in t2['lan'])} for V2 against {' / '.join(en(x, 3) for x in t0['lan'])} for B0, within run-to-run variation, so the correct claim is that adaptation is free at inference, not that V2 is faster. Recognition accounts for roughly {t2['asr'] / t2['rtf'] * 100:.0f}% of latency (RTF {en(t2['asr'], 3)} against {en(t2['mt'], 3)} for translation), so optimisation effort belongs there. Peak inference memory of {en(t2['vram'])} GiB is well below the 5.99 GiB required during training, meaning deployment fits a 4 GB GPU.")
dat(tim(d, "We address this at the system level."), f"We address this at the system level. Audio above 28 s is cut into segments of at most 28 s, each cut moved to the quietest point within ±3 s; recognition runs per segment, phrases repeated at a join are removed, and hypotheses are concatenated before translation. Spoken numbers are converted to digits before translation. Voice activity detection is optional and off by default, because an early version that always applied it raised WER on 20 short samples from 15.05% to 34.79%. On all 857 test recordings the product path reaches {en(S.tat['WER_asr'])}% WER, {en(S.tat['BLEU'])} BLEU and {en(S.tat['chrF++'])} chrF++; the 10 recordings above 28 s reach {en(S.dai['WER_asr'])}% WER. Against the earlier processing the gain is {en(S.hb['delta'])} BLEU, CI {ci(S.hb, en)}, not significant. These steps were measured on the test set for acceptance only and were not validated separately on development data.")
dat(tim(d, "One trade-off deserves emphasis."), f"One trade-off deserves emphasis. V2 sits {dcl} BLEU below the baseline on clean-text translation at seed 42 and {en(-SACH_TB)} below on the three-seed mean, and no seed meets our no-regression criterion.")
R = robust()
if R[2][3]:
    dat(tim(d, "Several limitations bound these results."), tim(d, "Several limitations bound these results.").text.replace("noisy environments are unevaluated", f"real noise are unevaluated (synthetic white noise at 10 dB SNR moves WER from {en(R[0][3]['WER_percent'])}% to {en(R[2][3]['WER_percent'])}%)"))
out = O / "3_paper"; out.mkdir(exist_ok=True); d.save(out / "Paper_Springer_LNCS.docx"); print("Paper xong")
ST = J(O / "_script/so_trang.json") if (O / "_script/so_trang.json").exists() else {"BC": "?", "SL": "?", "PP": "?"}

# ======== CHECKLIST
d = Document(G / "4_checklist/Checklist_Nop_Bai.docx"); Tb = d.tables
c = vn(S.c["BLEU"]); rtv = vn(t2["rtf"], 3)
thay(d, [("cập nhật 31/10/2026", "cập nhật 04/11/2026"), ("ví dụ runs/mt/V3/fleurs_test_asr_pho/score.json", "ví dụ runs/mt/V2/fleurs_test_asr_pho/score.json"),
         ("demo xử lý theo lượt (gửi một đoạn, nhận kết quả), không phải streaming liên tục.", "demo hiện kết quả theo từng đoạn trong lúc thu và nhận dạng lại cả bản khi dừng, nhưng chưa đo như phụ đề thời gian thực."),
         ("(ghép hai khối, có lớp backend giả để test không cần GPU), tests/ (57 test).", "(ghép hai khối, có lớp backend giả để test không cần GPU), src/so.py (đổi số), src/truc_tiep.py (thu âm trực tiếp), tests/ (151 test)."),
         ("src/audio.py (chuẩn hoá sample rate và VAD chia đoạn)", "src/audio.py (chuẩn hoá sample rate và chia đoạn)"),
         ("“Hệ thống có chỗ nào chưa chạy được?” Mục 8.2. Audio dài hơn 30 giây nếu đưa trực tiếp vào khối nghe thì WER 94,70%; đã xử lý bằng VAD chia đoạn ở mức hệ thống, có 21 test chặn hồi quy.",
          f"“Hệ thống có chỗ nào chưa chạy được?” Mục 8.2. Docker, GitHub Actions, m4a/webm (cần ffmpeg) và micro thật chưa kiểm được. Audio dài hơn 30 giây nếu đưa trực tiếp vào khối nghe thì WER 94,70%; đã xử lý bằng chia đoạn ở mức hệ thống, 10 bản dài hơn 28 giây còn WER {vn(S.dai['WER_asr'])}%."),
         ("“Sao V3 là bản cuối mà lại đề xuất dùng V4?” Mục 7.9. Quy tắc chọn bản cuối định trước là BLEU dev cao nhất nên V3 là bản cuối; nhưng V4 đạt tiêu chí mà V3 chưa đạt và hai bản không phân biệt được trên test.",
          f"“Sao chọn V2 mà không phải V3 có dev cao nhất?” Mục 6.2. Quy tắc đầu cho ra V3. Vì V1–V4 chênh rất ít, nhóm đổi sang: cách đỉnh dev cascade không quá 0,5 thì hoà, chọn dev sạch cao nhất, ra V2 ({vn(ab['V2']['dev sạch'])}). Phải nói thật là quy tắc này chốt sau khi đã thấy số test của V1–V4."),
         ("“Tiêu chí nào chưa đạt?” Mục 7.9. Không giảm BLEU khi dịch văn bản chuẩn: V3 tụt 1,51 BLEU.", f"“Tiêu chí nào chưa đạt?” Mục 7.9. Không giảm BLEU khi dịch văn bản chuẩn: V2 seed 42 thấp hơn ngưỡng {vn(-S.dcl)} BLEU, trung bình 3 seed thấp hơn {vn(-SACH_TB)}."),
         ("“Từng thành phần đóng góp bao nhiêu?” Mục 6.2, bảng thứ hai.", "“Từng thành phần đóng góp bao nhiêu?” Mục 6.2."),
         ("BaoCao_Project_Nhom.docx — báo cáo đầy đủ theo 9 mục, 21 trang.", "BaoCao_Project_Nhom.docx — báo cáo đầy đủ theo 9 mục, @TRANG_BC@ trang."),
         ("Slide_Project_Nhom.pptx — 17 slide, có ghi chú trình bày từng slide.", "Slide_Project_Nhom.pptx — @SLIDE@ slide, có ghi chú trình bày từng slide."),
         ("Paper_Springer_LNCS.docx — bản bài báo 8 trang.", "Paper_Springer_LNCS.docx — bản bài báo @TRANG_PP@ trang.")])
p = tim(d, "“Tiêu chí nào chưa đạt?”")
chen_sau(p, f"“Sao không chọn V1 khi test cascade trung bình cao hơn?” Mục 6.2. V1 đạt {B3.vi('V1', 'test cascade')}, V2 đạt {B3.vi('V2', 'test cascade')}, nhưng nhóm không chọn theo test. Theo dev, V1 và V2 hoà và V2 có dev sạch cao hơn. Seed 1 và 2 train trên Modal bằng torch 2.7.1, chấm lại bằng torch 2.0.1.", kieu=p)
chen_sau(p, f"“Khối nghe có fine-tune không?” Không. LoRA chỉ gắn ở khối dịch; PhoWhisper-small giữ nguyên, nên WER 13,68% không đổi. B1 end-to-end chỉ đạt BLEU {vn(S.b1['BLEU'])}, đây là số của Whisper-small chạy nguyên bản, không phải giới hạn của mọi mô hình end-to-end.", kieu=p)
t = Tb[0]
hang(t, 6, None, None, f"Whisper-small: WER 25,99% VIVOS / 21,24% FLEURS · reports/asr/results_task2.csv. B1 end-to-end: BLEU {vn(S.b1['BLEU'])} · runs/mt/B1_whisper-small_translate/")
hang(t, 11, None, None, "V2 là bản cuối, kèm V3, V4 · configs/mt/ · quy tắc chọn: reports/ablation/QUY_TAC_CHON.md")
hang(t, 12, None, None, "Báo cáo mục 6.2 · reports/ablation/bang_ablation.csv · rank 8, rank 32, augmentation")
hang(t, 13, None, None, f"Báo cáo mục 6.6 · RTF {rtv} · p95 {vn(t2['p95'])} s · 2,69 GB · reports/toc_do/lap_V2/*.json")
hang(t, 14, "Slide 18–25 trang", None, "Slide_Project_Nhom.pptx — @SLIDE@ slide, theo khung 4 chương")
hang(t, 15, None, "Một phần", "repo/docker/ hai service · .github/workflows/ci.yml năm job đã viết; Docker và GitHub Actions chưa chạy thật")
hang(t, 16, None, None, "Paper_Springer_LNCS.docx — @TRANG_PP@ trang")
t = Tb[1]
hang(t, 2, None, None, None, "Xong — BaoCao_Project_Nhom.docx, @TRANG_BC@ trang"); hang(t, 3, None, "Slide 18–25 slide", "theo khung 4 chương của thầy", "Xong — @SLIDE@ slide, có ghi chú trình bày từng slide")
hang(t, 5, None, None, None, "Xong — repo/data/README.md, checkpoints/V1–V4, ablation")
t = Tb[2]
hang(t, 4, None, None, "EDA, phân tích lỗi, B1, ablation, đánh giá tổng hợp (năm notebook có output)"); hang(t, 9, None, None, "protocol ASR, bản chốt V2, cấu hình từng phiên bản")
hang(t, 13, None, "Có, chưa chạy", "ci.yml: lint, test, cai-sach, build, deploy; repo chưa đẩy lên GitHub"); hang(t, 12, None, "Có, chưa chạy", "Dockerfile.api, Dockerfile.app, docker-compose.yml; chưa build thật")
hang(t, 14, None, None, "toàn bộ bảng số, hình và workbook ba sheet")
t = Tb[3]
hang(t, 1, None, None, "wav, mp3, flac, ogg; m4a và webm cần ffmpeg, chưa kiểm được"); hang(t, 2, None, "Một phần", "tab thu âm có trong demo; micro thật chưa đo")
hang(t, 4, "Xử lý audio dài: chia đoạn", None, f"src/audio.py, mỗi đoạn ≤ 28 s tại chỗ ngắt nghỉ, VAD là tuỳ chọn; 10 bản dài: WER {vn(S.dai['WER_asr'])}%")
hang(Tb[4], 4, None, None, f"Xong — đây là chỉ số chính: 22,69 → {c}")
hang(Tb[4], 5, None, None, "Xong — ba lần đo xen kẽ, cùng phiên 04/11; mục 6.6")
hang(Tb[5], 1, None, None, "3 seed: 42, 1, 2 cho V1–V4 và ablation; seed 42 chạy trên máy nhóm, seed 1 và 2 train trên Modal · reports/ba_seed/")
hang(Tb[5], 5, None, None, "chọn epoch theo BLEU dev cascade; bản cuối chọn bằng số dev, nhưng quy tắc cuối chốt sau khi đã thấy test V1–V4 (mục 6.2)")
t = Tb[6]
hang(t, 6, "Bản cuối đã chốt V2. Gửi nhóm đọc lại mục 6.2 để thống nhất cách trả lời khi vấn đáp", "cả nhóm", "Trước khi nộp")
hang(t, 7, "Thu 20 câu trong tests/bo_cau_tu_thu/: có giọng nữ và micro điện thoại", "Uyên", "Nên làm, +2 điểm cộng")
them_hang(t, 7, "Thử micro thật với câu “Hôm nay là ngày 11 tháng 3 năm 2026” trên Chrome", "Kiệt", "Trước khi nộp")
t = Tb[7]
hang(t, 2, "Docker và GitHub Actions", "Docker Desktop đang tắt; repo chưa đẩy lên GitHub", "Điểm cộng; hiện mới có cấu hình, không ghi là đã chạy")
hang(t, 5, "m4a và webm", "máy nhóm không có ffmpeg", "Nghiệm thu T05 trượt vì lý do này; wav, mp3, flac, ogg không phụ thuộc")
hang(t, 6, "Đo tải đồng thời nhiều người dùng", "chưa có môi trường triển khai", "Mới thử 3 người cùng lúc không lẫn kết quả, chưa đo tải")
hang(t, 7, "Thu audio tự build và B1 so với paper", "thiếu thời gian", "Mất 2 điểm cộng; B1 ghi NOT RUN ở phần so paper")
for a_, b_ in (("@TRANG_BC@", str(ST["BC"])), ("@SLIDE@", str(ST["SL"])), ("@TRANG_PP@", str(ST["PP"]))):
    for p in tat_ca_doan(d):
        while a_ in _gop(p):
            sub(p, a_, b_)
tach_dam(d, "“Sao chọn V2", "“Sao chọn V2 mà không phải V3 có dev cao nhất?”")
out = O / "4_checklist"; out.mkdir(exist_ok=True); d.save(out / "Checklist_Nop_Bai.docx"); print("Checklist xong")
