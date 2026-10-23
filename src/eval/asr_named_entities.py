"""Task 2 · lỗi tên riêng của ASR (phần Bảo) trên FLEURS test.

Tên riêng được xấp xỉ bằng từ viết hoa không đứng đầu câu trong transcript gốc (vi_raw), ví dụ "Harappa", "Belarus".
Một từ được tính là nghe đúng khi dạng chuẩn hóa (NFC, viết thường) xuất hiện trong chữ máy nghe của cùng bản thu.
So với tỉ lệ nghe đúng của từ thường (không viết hoa) để thấy tên riêng khó hơn bao nhiêu.
"""
import json, re, unicodedata
from collections import Counter


def norm(t):
    t = unicodedata.normalize("NFC", t).lower()
    t = "".join(" " if unicodedata.category(c)[0] in "PS" else c for c in t)
    return " ".join(t.split())


rows = json.load(open("reports/task1/mt/predictions_fleurs_test.json", encoding="utf-8"))
ent_tot = ent_hit = com_tot = com_hit = 0
foreign_tot = foreign_hit = 0
missed = Counter()
VI = re.compile(r"[ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ]", re.I)
for r in rows:
    hyp = set(norm(r["asr"]).split())
    toks = r["vi_raw"].split()
    for i, t in enumerate(toks):
        w = norm(t)
        if not w or any(ch.isdigit() for ch in w):
            continue
        sentence_start = i == 0 or toks[i - 1][-1:] in ".?!:"
        is_ent = t[:1].isupper() and not sentence_start
        for part in w.split():
            hit = part in hyp
            if is_ent:
                ent_tot += 1; ent_hit += hit
                if not VI.search(part):                      # tên nước ngoài (không có dấu tiếng Việt)
                    foreign_tot += 1; foreign_hit += hit
                if not hit:
                    missed[part] += 1
            else:
                com_tot += 1; com_hit += hit
res = {"named_entity_tokens": ent_tot, "named_entity_recall_percent": round(100 * ent_hit / ent_tot, 1),
       "foreign_name_tokens": foreign_tot, "foreign_name_recall_percent": round(100 * foreign_hit / max(1, foreign_tot), 1),
       "common_word_tokens": com_tot, "common_word_recall_percent": round(100 * com_hit / com_tot, 1),
       "most_missed_named_entities": missed.most_common(15),
       "note": "tên riêng = từ viết hoa không đầu câu trong vi_raw; nghe đúng = có trong chữ máy nghe của cùng bản thu"}
json.dump(res, open("reports/task2/asr/named_entities.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(res, ensure_ascii=False, indent=1))
