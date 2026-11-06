"""Nhận xét/kết luận tính từ số (dùng chung cho tao_bao_cao.py và tao_slide.py) – không có câu kết luận nào viết sẵn kèm số.

Tiêu chí khả thi lấy từ đề cương Task 1 của nhóm: real-time (RTF < 1), đo latency median/p95, không giảm BLEU khi dịch văn bản chuẩn,
thu hẹp khoảng cách BLEU cascade – văn bản chuẩn. Ngưỡng độ trễ cho ứng dụng web (p95 ≤ 5 s) là ngưỡng nhóm đề xuất cho Task 3, ghi rõ là đề xuất.
"""
import json
from pathlib import Path

T = Path(__file__).resolve().parents[1]


def _j(p):
    p = T / p
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def vn(x, d=2):
    return f"{float(x):.{d}f}".replace(".", ",")


def bleu(v, s):
    j = _j(f"runs/mt/{v}/{s}/score.json")
    return j["BLEU"] if j else None


def nhan_xet(v, prev):
    """So v với bản trước theo dev (dùng để chọn) và test (báo cáo), kèm bootstrap nếu có."""
    dd = bleu(v, "fleurs_dev_asr_pho") - bleu(prev, "fleurs_dev_asr_pho")
    dt = bleu(v, "fleurs_test_asr_pho") - bleu(prev, "fleurs_test_asr_pho")
    ds = bleu(v, "fleurs_test_clean") - bleu(prev, "fleurs_test_clean")
    dp = (bleu(v, "phomt_test") or 0) - (bleu(prev, "phomt_test") or 0)
    bs = _j(f"reports/mt/bootstrap_{prev}_{v}_cascade_test.json")
    sig = ""
    if bs:
        sig = " (có ý nghĩa)" if bs["p_one_sided_delta_le_0"] < 0.05 or bs["p_one_sided_delta_le_0"] > 0.95 else f" (không có ý nghĩa, p = {vn(bs['p_one_sided_delta_le_0'])})"
    return (f"So với {prev}: dev {dd:+.2f}; test cascade {dt:+.2f}{sig}; dịch sạch {ds:+.2f}; PhoMT {dp:+.2f}").replace(".", ",")


def thu_muc_lap():
    """Phiên đo dùng cho mọi bảng tốc độ (chỉ so các hệ trong CÙNG một phiên):
    lap_V2/ (04/11, B0/V2/V4 xen kẽ, sau khi quy tắc DEV chọn V2) → lap_V4/ (03/11, B0/V3/V4) → lap/ (30–31/10, B0/V3)."""
    for ten, he in (("lap_V2", ("B0", "V2", "V4")), ("lap_V4", ("B0", "V3", "V4"))):
        d = T / "reports" / "toc_do" / ten
        if all(len(list(d.glob(f"toc_do_{v}_lan*.json"))) >= 3 for v in he):
            return d
    return T / "reports" / "toc_do" / "lap"


def toc_do(v):
    """Trung vị các lần đo lặp xen kẽ (reports/toc_do/<phiên>/toc_do_<v>_lanK.json); thêm khoảng min–max. Không có thì dùng lần đo đơn."""
    import statistics
    runs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(thu_muc_lap().glob(f"toc_do_{v}_lan*.json"))]
    if not runs:
        return _j(f"reports/toc_do/toc_do_{v}.json")
    out = dict(runs[0])
    for k in ("RTF_total", "RTF_asr", "RTF_mt", "latency_p50_s", "latency_p95_s", "latency_mean_s", "asr_mean_s", "mt_mean_s"):
        xs = [r[k] for r in runs]
        out[k] = statistics.median(xs); out[k + "_min"], out[k + "_max"] = min(xs), max(xs)
    for k in ("gpu_peak_allocated_bytes", "ram_rss_peak_bytes"):
        out[k] = max(r[k] for r in runs)
    out["n_lan_do"] = len(runs)
    return out


def toc_do_ban_cuoi(final):
    """Tốc độ của bản cuối. V4 chưa đo riêng (chỉ có lần đo xen kẽ B0/V3): dùng số V3 và trả ghi chú,
    vì V3 và V4 cùng kiến trúc, cùng kích thước adapter. Không tự đặt số."""
    f = toc_do(final)
    if f:
        return f, final, ""
    f = toc_do("V3")
    n = f"{f['adapter_bytes']:,}".replace(",", ".") if f else ""
    return f, "V3", (f"{final} chưa đo riêng tốc độ; số là của V3 (cùng kiến trúc, adapter cùng {n} byte)" if f else "")


def he_thong():
    """Số đo cả hệ của sản phẩm chạy GPU: reports/he_thong_V2/ (repo cuối, adapter V2) nếu có,
    không thì reports/he_thong/ (fix.zip, adapter V4, 03/11). Trả (ket_qua, bootstrap, ten_thu_muc)."""
    for d in ("he_thong_V2", "he_thong"):
        kq = _j(f"reports/{d}/ket_qua.json")
        if kq:
            return kq, _j(f"reports/{d}/bootstrap_cu_vs_moi.json"), d
    return None, None, None


def kha_thi(final):
    b0 = toc_do("B0")
    f, ten_td, ghi_chu_td = toc_do_ban_cuoi(final)
    rows, ok = [], True
    if not f:
        return [], "Chưa đo tốc độ bản cuối."
    td = "" if ten_td == final else f" (đo trên {ten_td})"
    rows.append(("Real-time: RTF < 1 (đề cương Task 1)", vn(f["RTF_total"], 3) + td, f["RTF_total"] < 1))
    rows.append(("Độ trễ mỗi bản thu p50 / p95 (đo theo đề cương)", f"{vn(f['latency_p50_s'])} / {vn(f['latency_p95_s'])} s", None))
    rows.append(("Đề xuất cho web Task 3: p95 ≤ 5 s", f"{vn(f['latency_p95_s'])} s" + td, f["latency_p95_s"] <= 5))
    rows.append(("Chạy trên GPU 8 GB: VRAM đỉnh khi suy luận", f"{vn(f['gpu_peak_allocated_bytes'] / 2**30)} GiB", f["gpu_peak_allocated_bytes"] < 8 * 2**30))
    rows.append(("RAM tiến trình", f"{vn(f['ram_rss_peak_bytes'] / 2**30)} GiB", None))
    size = (f["asr_checkpoint_bytes"] + f["mt_checkpoint_bytes"] + f["adapter_bytes"]) / 1e9
    rows.append(("Kích thước model (ASR + MT + adapter)", f"{vn(size)} GB (adapter {vn(f['adapter_bytes'] / 1e6, 1)} MB)", None))
    gap0 = bleu("B0", "fleurs_test_clean") - bleu("B0", "fleurs_test_asr_pho")
    gapf = bleu("B0", "fleurs_test_clean") - bleu(final, "fleurs_test_asr_pho")
    rows.append(("Thu hẹp khoảng cách cascade – văn bản chuẩn (so với dịch sạch của B0)", f"{vn(gap0)} → {vn(gapf)} BLEU", gapf < gap0))
    dclean = bleu(final, "fleurs_test_clean") - bleu("B0", "fleurs_test_clean")
    rows.append(("Không giảm BLEU khi dịch văn bản chuẩn (đề cương Task 1)", f"{dclean:+.2f} BLEU".replace(".", ","), dclean >= 0))
    fails = [r[0] for r in rows if r[2] is False]
    if ghi_chu_td:
        rows.append(("Ghi chú tốc độ", ghi_chu_td, None))
    verdict = ("KHẢ THI để đóng gói thành ứng dụng web chạy GPU ở Task 3" if all(r[2] is not False for r in rows[:4]) else "CHƯA KHẢ THI về tốc độ/bộ nhớ")
    if fails:
        verdict += "; chưa đạt: " + "; ".join(fails)
    return rows, verdict


def quy_tac_chon(final):
    """Lý do chọn bản cuối = quy tắc DEV chốt TRƯỚC khi chạy ablation (reports/ablation/QUY_TAC_CHON.md),
    kết quả áp dụng ở reports/ablation/chon_ban_cuoi.json. Mọi số đọc từ file."""
    c = _j("reports/ablation/chon_ban_cuoi.json")
    if not c:
        return f"Bản cuối {final}."
    dv = {r["bản"]: r for r in c["bang_dev"]}
    ngoai = [v for v in dv if v not in c["nhom_hoa"]]
    t = (f"Quy tắc chọn trên DEV, chốt trước khi chạy ablation (reports/ablation/QUY_TAC_CHON.md): M = BLEU dev cascade cao nhất "
         f"({vn(c['M_dev_cascade'])}, {max(dv, key=lambda v: dv[v]['dev cascade'])}); các bản ≥ M − 0,5 coi là hoà: {', '.join(c['nhom_hoa'])}; "
         f"trong nhóm hoà chọn BLEU dev dịch sạch cao nhất → {c['ban_chon']} ("
         + ", ".join(f"{v} {vn(dv[v]['dev sạch'])}" for v in c["nhom_hoa"]) + ").")
    if ngoai:
        t += " Ablation ngoài nhóm hoà (dev cascade): " + ", ".join(f"{v} {vn(dv[v]['dev cascade'])}" for v in ngoai) + "."
    if c["ban_chon"] != final:
        t += f" LƯU Ý: bản đang ghi là {final}, khác bản quy tắc chọn ({c['ban_chon']})."
    t += " Quy tắc này chốt sau khi đã có số test của V1–V4 (quy tắc đầu, lấy dev cascade cao nhất, cho ra V3), nên không phải lựa chọn mù với test; chỉ ba bản ablation chạy sau khi có quy tắc. Giữa V1–V4 chênh lệch trên test nằm trong khoảng tin cậy bootstrap."
    b3 = _j("reports/ba_seed/ket_qua_3seed.json")
    if b3:
        t += f" Kiểm tra 3 seed (reports/ba_seed/): áp quy tắc trên trung bình dev vẫn ra {b3['quy_tac_tren_trung_binh_ra']}; seed 1 và 2 train trên Modal, chấm cùng môi trường với seed 42."
    return t
