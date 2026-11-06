"""HÀM DÙNG CHUNG – Task 2, TV4 Uyên. KHÔNG chạy trực tiếp file này.

NHIỆM VỤ: chứa các hàm mà các script viecX_*.py cùng dùng: tải file từ Hugging Face, tải + giải nén PhoMT,
đọc TSV của FLEURS, chuẩn hoá chữ để so trùng. Phải để chung thư mục với các script viecX_*.py.
"""
import re
import sys
import unicodedata
import zipfile
from pathlib import Path

FLEURS_REPO = "google/fleurs"
VIVOS_REPO = "AILAB-VNUHCM/vivos"
PHOMT_REPO = "vinai/PhoMT"
PHOMT_ZIP = "PhoMT.zip"


def norm(s):
    """Chuẩn hoá để so trùng: NFC, viết thường, bỏ dấu câu, gộp khoảng trắng (giữ dấu thanh)."""
    s = unicodedata.normalize("NFC", s).lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return " ".join(s.split())


def fetch(repo, relpath, local_dir, revision="main"):
    """Tải 1 file của repo dataset (có cache, tải tiếp được nếu đứt mạng)."""
    from huggingface_hub import hf_hub_download
    return Path(hf_hub_download(repo, relpath, repo_type="dataset", revision=revision, local_dir=local_dir))


def repo_meta(repo, revision="main", path_in_repo=None):
    """Mã commit, giấy phép, trạng thái gated và danh sách file (kèm dung lượng) của một repo dataset."""
    from huggingface_hub import HfApi
    api = HfApi()
    meta = {"repo": repo, "url": f"https://huggingface.co/datasets/{repo}", "revision_requested": revision}
    try:
        info = api.dataset_info(repo, revision=revision)
        meta["sha"] = info.sha
        meta["gated"] = getattr(info, "gated", None)
        card = info.card_data.to_dict() if info.card_data else {}
        meta["license_card"] = card.get("license")
        files = [(f.path, f.size) for f in api.list_repo_tree(repo, path_in_repo=path_in_repo, recursive=True,
                                                               repo_type="dataset", revision=info.sha)
                 if getattr(f, "size", None) is not None]
        meta["files"] = dict(files)
    except Exception as e:  # không chặn cả script chỉ vì không đọc được metadata
        meta["error"] = f"{type(e).__name__}: {e}"
    return meta


def find_phomt_file(root, split, lang):
    root = Path(root)
    cands = sorted(p for p in root.rglob(f"*{split}*.{lang}") if p.is_file() and not p.name.startswith("."))
    exact = [c for c in cands if c.name == f"{split}.{lang}"]
    cands = exact or cands
    detok = [c for c in cands if "detok" in str(c).lower()]  # ưu tiên bản detokenization như Task 1
    return (detok or cands or [None])[0]


def ensure_phomt(phomt_dir, splits=("train", "dev", "test"), langs=("vi", "en")):
    """Trả về {(split, lang): Path}. Nếu chưa có thì tải PhoMT.zip (gated, cần huggingface-cli login) và giải nén."""
    phomt_dir = Path(phomt_dir)
    need = [(s, l) for s in splits for l in langs]

    def scan():
        return {k: find_phomt_file(phomt_dir, *k) for k in need} if phomt_dir.exists() else {k: None for k in need}

    found = scan()
    if None in found.values():
        zips = list(phomt_dir.rglob("*.zip")) if phomt_dir.exists() else []
        if not zips:
            print(f"[PhoMT] chưa có dữ liệu trong {phomt_dir}, tải {PHOMT_ZIP} từ {PHOMT_REPO} ...")
            try:
                zips = [fetch(PHOMT_REPO, PHOMT_ZIP, phomt_dir)]
            except Exception as e:
                sys.exit(f"[PhoMT] tải thất bại ({type(e).__name__}). PhoMT là dataset gated: vào "
                         f"https://huggingface.co/datasets/{PHOMT_REPO} bấm đồng ý điều khoản, rồi chạy "
                         f"`huggingface-cli login`. Hoặc trỏ --phomt_dir tới bản PhoMT đã có trên máy.")
        for z in zips:
            print(f"[PhoMT] giải nén {z} ...")
            with zipfile.ZipFile(z) as zf:
                zf.extractall(z.parent)
        found = scan()
    missing = [f"{s}.{l}" for (s, l), p in found.items() if p is None]
    if missing:
        sys.exit(f"[PhoMT] không tìm thấy {missing} trong {phomt_dir}. Kiểm tra lại cấu trúc thư mục PhoMT.")
    return found


def count_lines(path):
    n = empty = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            n += 1
            empty += not line.strip()
    return n, empty


def lib_versions():
    out = {"python": sys.version.split()[0]}
    for mod in ("huggingface_hub", "requests"):
        try:
            out[mod] = __import__(mod).__version__
        except ImportError:
            pass
    return out


def read_fleurs_tsv(path):
    """TSV FLEURS không có header, 7 cột: id, file_name, raw_transcription, transcription, phonemes, num_samples, gender.
    Trả về (danh sách dòng hợp lệ, số dòng sai định dạng)."""
    rows, bad = [], 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) != 7 or not p[5].isdigit():
                bad += 1
                continue
            rows.append({"sent_id": p[0], "file_name": p[1], "raw": p[2], "transcription": p[3],
                         "num_samples": int(p[5]), "gender": p[6]})
    return rows, bad
