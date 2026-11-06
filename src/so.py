"""Doi so doc bang chu (loi ASR) sang chu so truoc khi dich.

PhoWhisper viet so bang chu: "ngay muoi mot thang ba nam hai nghin khong tram hai muoi sau".
Khoi dich hay dich sai so dang chu dai (1755 -> 1971). Doi thanh "ngay 11 thang 3 nam 2026"
roi moi dich.

Lam than trong de khong doi nham chu thuong:
  - cum 2 tu tro len ("muoi bon", "hai muoi", "mot tram") thi doi;
  - 1 tu don ("mot so ca", "hai nguoi") giu nguyen, tru khi dung sau "ngay", "thang",
    truoc "phan tram", hoac co "phay" (2 phay 3);
  - "thu hai", "thu bay" (thu trong tuan, thu tu) giu nguyen;
  - "hai muoi nam" = 20 nam (so 5 sau "muoi" phai doc la "lam"), "mot tram nam" = 100 nam,
    "hai trieu nam" = 2 trieu nam: sau "tram", "nghin" chi nhan cum co "tram/muoi/le".
"""

from __future__ import annotations

import re

CHU_SO = {
    "không": 0,
    "một": 1,
    "hai": 2,
    "ba": 3,
    "bốn": 4,
    "năm": 5,
    "sáu": 6,
    "bảy": 7,
    "bẩy": 7,
    "tám": 8,
    "chín": 9,
}
# so dung sau "muoi"/"muoi": 1 doc "mot/mot", 4 doc "tu/bon", 5 doc "lam/nham"
SAU_MUOI = {
    "mốt": 1,
    "một": 1,
    "hai": 2,
    "ba": 3,
    "bốn": 4,
    "tư": 4,
    "lăm": 5,
    "nhăm": 5,
    "sáu": 6,
    "bảy": 7,
    "bẩy": 7,
    "tám": 8,
    "chín": 9,
}
HANG = {"nghìn": 1000, "ngàn": 1000, "triệu": 10**6, "tỷ": 10**9, "tỉ": 10**9}
LE = ("linh", "lẻ")
TRUOC_TU_DON = ("ngày", "tháng", "lúc", "mùng", "mồng")


def _nhom(t, i):
    """Doc mot nhom < 1000 bat dau tu t[i]. Tra (gia_tri, vi_tri_sau, co_tu_noi) hoac None.
    co_tu_noi = True neu nhom co tram/muoi/muoi/le (khong phai 1 chu so don)."""
    n = len(t)
    if i < n and t[i].isdigit() and len(t[i]) <= 3:  # ASR doi khi viet "19 ngan"
        return int(t[i]), i + 1, True
    gt, noi = 0, False
    if i + 1 < n and t[i] in CHU_SO and t[i + 1] == "trăm":
        gt, i, noi = CHU_SO[t[i]] * 100, i + 2, True
        if i + 1 < n and t[i] in LE and t[i + 1] in CHU_SO:  # mot tram le tam
            return gt + CHU_SO[t[i + 1]], i + 2, True
    elif i + 1 < n and t[i] in LE and t[i + 1] in CHU_SO:  # (hai nghin) le nam
        return CHU_SO[t[i + 1]], i + 2, True
    if i < n and t[i] == "mười":
        gt, i, noi = gt + 10, i + 1, True
        if i < n and t[i] in SAU_MUOI and t[i] not in ("mốt", "tư"):
            gt, i = gt + SAU_MUOI[t[i]], i + 1
    elif i + 1 < n and t[i] in CHU_SO and t[i] not in ("không", "một") and t[i + 1] == "mươi":
        gt, i, noi = gt + CHU_SO[t[i]] * 10, i + 2, True
        # "ba muoi ba muoi mot" = 30 31: chu so sau "muoi" ma lien sau la "muoi" thi thuoc so ke
        if i < n and t[i] in SAU_MUOI and not (i + 1 < n and t[i + 1] == "mươi"):
            gt, i = gt + SAU_MUOI[t[i]], i + 1
    elif not noi and i < n and t[i] in CHU_SO and t[i] != "không":
        return CHU_SO[t[i]], i + 1, False
    if not noi:
        return None
    return gt, i, True


def _doc_nam(t, i):
    """Nam doc kieu "hai khong muoi sau" (2016), "hai khong le chin" (2009), "mot chin tam tam".
    Chi nhan the ky 10-20 de khong doi nham "mot hai ba"."""
    if i + 2 >= len(t) or t[i] not in ("một", "hai") or t[i + 1] not in CHU_SO:
        return None
    the_ky = CHU_SO[t[i]] * 10 + CHU_SO[t[i + 1]]
    if not 10 <= the_ky <= 20:
        return None
    # 4 chu so don ("mot chin tam tam") chi nhan sau "nam" hoac ngay sau "thang <so>",
    # tranh doi nham "mot hai ba bon"
    sau_nam = i > 0 and t[i - 1] == "năm"
    sau_thang = i > 1 and t[i - 2] == "tháng"
    if (sau_nam or sau_thang) and i + 3 < len(t) and t[i + 2] in CHU_SO and t[i + 3] in CHU_SO:
        return the_ky * 100 + CHU_SO[t[i + 2]] * 10 + CHU_SO[t[i + 3]], i + 4
    sau = _nhom(t, i + 2)
    if sau is not None and sau[2] and sau[0] < 100:
        return the_ky * 100 + sau[0], sau[1]
    return None


def _doc_so(t, i):
    """Doc so dai nhat tu t[i]. Tra (gia_tri, vi_tri_sau) hoac None."""
    nam = _doc_nam(t, i)
    if nam is not None:
        return nam
    dau = _nhom(t, i)
    if dau is None:
        return None
    tong, cur, j, hang_truoc = 0, dau[0], dau[1], None
    while j < len(t) and t[j] in HANG:
        h = HANG[t[j]]
        if hang_truoc is not None and h >= hang_truoc:
            break
        tong += cur * h
        cur, hang_truoc, j = 0, h, j + 1
        sau = _nhom(t, j)
        if sau is None or not sau[2]:  # "hai trieu nam", "hai nghin nguoi": dung o day
            break
        cur, j = sau[0], sau[1]
    return tong + cur, j


def _viet(v: int) -> str:
    """Viet so theo cach du lieu FLEURS: 1767 (nam), 7.000, 19.500, 800 trieu."""
    if v >= 10**9 and v % 10**9 == 0:
        return f"{v // 10 ** 9} tỷ"
    if v >= 10**6 and v % 10**6 == 0:
        return f"{v // 10 ** 6} triệu"
    if v < 1000 or 1000 <= v <= 2100:
        return str(v)
    return f"{v:,}".replace(",", ".")


def _tach(tu: str):
    """Tach dau cau o hai dau tu: '(hai' -> ('(', 'hai', '')."""
    m = re.match(r"^(\W*)(.*?)(\W*)$", tu)
    return m.group(1), m.group(2), m.group(3)


def _lam_tron_cum(phan, i):
    """Vi tri het cum tu i: khong doc qua dau cau (dau phay, ngoac) o giua cum."""
    k = i
    while k < len(phan):
        if k > i and phan[k][0]:
            return k
        if phan[k][2]:
            return k + 1
        k += 1
    return k


def doi_so(van_ban: str) -> str:
    """Doi cac cum so doc bang chu trong van_ban sang chu so."""
    goc = van_ban.split()
    phan = [_tach(w) for w in goc]
    t = [p[1].lower() for p in phan]
    ra, i = [], 0
    while i < len(t):
        lim = _lam_tron_cum(phan, i)
        kq = _doc_so(t[:lim], i)
        if kq is None:
            ra.append(goc[i])
            i += 1
            continue
        v, j = kq
        truoc = t[i - 1] if i > 0 else ""
        sau = t[j : j + 2]
        doi = (
            j - i >= 2
            or t[i].isdigit()
            or t[i] == "mười"
            or truoc in TRUOC_TU_DON
            or sau == ["phần", "trăm"]
            or (sau[:1] == ["phẩy"] and j < lim)
        )
        if truoc == "thứ" and j - i == 1:
            doi = False  # thu hai, thu bay: thu trong tuan / thu tu
        if not doi:
            ra.append(goc[i])
            i += 1
            continue
        chu = _viet(v)
        if sau[:1] == ["phẩy"] and j < lim:  # "hai phay ba" -> "2,3"
            k, le = j + 1, ""
            while k < lim and t[k] in CHU_SO:
                le += str(CHU_SO[t[k]])
                k += 1
            if le:
                chu, j = f"{v},{le}", k
                if j < lim and t[j] in ("triệu", "tỷ", "tỉ"):
                    chu, j = chu + " " + t[j], j + 1
        ra.append(phan[i][0] + chu + phan[j - 1][2])
        i = j
    s = " ".join(ra)
    s = re.sub(r"(\d) phần trăm\b", r"\1%", s)
    return s
