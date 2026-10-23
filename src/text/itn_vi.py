"""V3 · chuẩn hóa số tiếng Việt (inverse text normalization) cho chữ máy nghe trước khi dịch.

PhoWhisper đọc số thành chữ ("802.11a" → "tám trăm linh hai chấm mười một a"), làm khối dịch dịch sai số và sinh lặp.
Hàm itn() đổi các cụm số đọc bằng chữ về chữ số. Để không đổi nhầm từ thường ("một hệ thống", "năm nay",
"hàng trăm người"), một cụm chỉ được đổi khi:
  - có từ chỉ hàng (mươi, mười, trăm, nghìn/ngàn, triệu, tỷ) và dài từ 2 từ trở lên, hoặc
  - có "chấm"/"phẩy" kẹp giữa hai phần số (số thập phân, số phiên bản: "hai chấm bốn" → "2.4"), hoặc
  - là dãy từ 3 chữ số đọc từng chữ trở lên ("tám không hai" → "802").
"""
import re

DIGIT = {"không": 0, "một": 1, "mốt": 1, "hai": 2, "ba": 3, "bốn": 4, "tư": 4, "năm": 5, "lăm": 5, "nhăm": 5,
         "sáu": 6, "bảy": 7, "bẩy": 7, "tám": 8, "chín": 9}
UNIT_ONLY = {"mốt", "lăm", "nhăm", "tư"}          # chỉ là số khi đứng sau "mươi"/"mười"
TENS = {"mươi", "mười"}
BIG = {"nghìn": 10**3, "ngàn": 10**3, "triệu": 10**6, "tỷ": 10**9, "tỉ": 10**9}
SEP = {"chấm": ".", "phẩy": ","}
LINK = {"linh", "lẻ"}
NUMWORD = set(DIGIT) | TENS | {"trăm"} | set(BIG) | SEP.keys() | LINK
PUNCT = re.compile(r"^(\W*)(.*?)(\W*)$", re.UNICODE)


def _positional(ws):
    """Đọc số theo hàng: 'hai nghìn không trăm mười một' → 2011. Trả None nếu không đọc được."""
    total, group, num = 0, 0, None
    for i, w in enumerate(ws):
        if w in DIGIT:
            if w in UNIT_ONLY and (i == 0 or ws[i - 1] not in TENS):
                return None
            if num is not None:
                return None                      # hai chữ số liền nhau: không phải cách đọc theo hàng
            num = DIGIT[w]
        elif w == "mười":
            if num is not None:
                return None
            group += 10
        elif w == "mươi":
            if num is None:
                return None
            group += num * 10; num = None
        elif w == "trăm":
            group += (1 if num is None else num) * 100; num = None
        elif w in LINK:
            if num is not None:
                return None
        elif w in BIG:
            v = group + (num or 0)
            total += (v or 1) * BIG[w]; group, num = 0, None
        else:
            return None
    return total + group + (num or 0)


def _number(ws):
    """Một phần số (không chứa chấm/phẩy) → chuỗi chữ số."""
    if not ws:
        return None
    if all(w in DIGIT and w not in UNIT_ONLY for w in ws):
        return "".join(str(DIGIT[w]) for w in ws) if len(ws) > 1 else str(DIGIT[ws[0]])
    v = _positional(ws)
    return None if v is None else str(v)


def _convert(ws):
    """Cả cụm, có thể có chấm/phẩy → chuỗi số, hoặc None nếu cụm không đủ điều kiện."""
    has_big = any(w in TENS or w == "trăm" or w in BIG for w in ws)
    parts, cur, seps = [], [], []
    for w in ws:
        if w in SEP:
            parts.append(cur); seps.append(SEP[w]); cur = []
        else:
            cur.append(w)
    parts.append(cur)
    if seps:
        if any(not p for p in parts):
            return None
    elif not has_big and len(ws) < 3:
        return None                               # "một", "ba bốn", "năm" ... giữ nguyên chữ
    elif has_big and len(ws) < 2:
        return None                               # "trăm", "mười" đứng một mình
    out = []
    for i, p in enumerate(parts):
        s = _number(p)
        if s is None:
            return None
        out.append(s)
        if i < len(seps):
            out.append(seps[i])
    return "".join(out)


def itn(text):
    toks = text.split()
    core = [PUNCT.match(t).groups() for t in toks]          # (dấu đầu, từ, dấu cuối)
    words = [c[1].lower() for c in core]
    out, i = [], 0
    while i < len(toks):
        if words[i] in NUMWORD and words[i] not in SEP and words[i] not in LINK:
            j = i
            while j < len(toks) and words[j] in NUMWORD and (j == i or not core[j - 1][2]):  # dừng ở dấu câu
                j += 1
            while j > i + 1 and (words[j - 1] in SEP or words[j - 1] in LINK):         # bỏ chấm/linh ở cuối cụm
                j -= 1
            for end in range(j, i, -1):                                                 # cụm dài nhất đổi được
                s = _convert(words[i:end])
                if s is not None:
                    out.append(core[i][0] + s + core[end - 1][2])
                    i = end
                    break
            else:
                out.append(toks[i]); i += 1
        else:
            out.append(toks[i]); i += 1
    return " ".join(out)


if __name__ == "__main__":
    tests = ["tương thích ngược với tám trăm linh hai chấm mười một a tám trăm linh hai chấm mười một b",
             "chuẩn tám không hai chấm một một in lời hoạt động trên cả hai tần số hai chấm bốn đi ra hệ và năm chấm không đi ra hệ.",
             "năm hai nghìn không trăm mười một có hơn tám trăm ngàn hồng quân",
             "một hệ thống có hàng trăm người, năm nay ba bốn người đi",
             "khoảng hai mươi lăm phần trăm, mười một giờ ba mươi phút",
             "một trăm hai mươi mốt"]
    for t in tests:
        print(t, "\n  →", itn(t))
