#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TANG TIEN ICH DUNG CHUNG cho ca ba file cua tool.

Vi sao co file nay (E1):
  - Truoc day cac ham tien ich nam trong `goi_project_capcut.py`, con
    `toi_uu_dung_luong.py` phai di lay nguoc lai bang `_find_main_module()`
    -> HAI FILE PHU THUOC VONG TRON, va viec do phai vinh vien lazy-import
    (dua import len dau file la nap file 2 lan hoac crash).
  - `xem_tien_trinh.py` thi CHEP nguyen `_lp()` va `_fmt_time()`. Ma `_lp()` da
    phai sua it nhat ba lan (#1, #23, #34); ban chep khong duoc sua theo la no
    hong am tham tren duong dan UNC.
  - Tach mot tang tien ich diet ca ba van de bang MOT buoc: het vong tron, het
    ban chep, het hack tra `sys.modules` (#48).

QUY TAC: file nay chi chua ham THUAN va hang so. KHONG chua trang thai, KHONG
import nguoc len hai file kia. Neu can them ham vao day, hay giu dung tinh chat do.
"""

from __future__ import annotations
import json, os, re, string, sys
from pathlib import Path


MEDIA_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi",
             ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg",
             ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


# media THAT SU anh huong video xuat ra (thieu = mat hinh/mat tieng)
VIDEO_AUDIO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi",
                   ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}


CONTENT_NAMES = ("draft_content.json", "draft_info.json")


PLACEHOLDER_RE = re.compile(r'##_draftpath_placeholder_([0-9A-Fa-f\-]+)_##')


# GUID nay la HANG SO cua CapCut (da kiem tra: giong nhau o moi project & moi sub-draft)
DEFAULT_GUID = "0E685133-18CE-45ED-8CB8-2904A212EC80"


# Thu muc duoc coi la 1 "draft root" (goc de giai placeholder) neu chua 1 trong cac file nay.
ROOT_MARKERS = ("draft_meta_info.json", "sub_draft_config.json")


def _lp(p):
    """Duong dan an toan cho Windows (prefix extended-length \\\\?\\ de vuot gioi han 260 ky tu).
    XU LY DUNG UNC: \\\\server\\share\\... phai thanh \\\\?\\UNC\\server\\share\\... (KHONG phai
    \\\\?\\\\\\server...). Sai UNC prefix = WinError 123 -> moi copy/getsize/isfile toi o mang hong."""
    if os.name != "nt":
        return str(p)
    s = str(p)
    # da la extended-length (\\\\?\\) hoac device (\\\\.\\) roi -> giu nguyen (idempotent)
    if s.startswith("\\\\?\\") or s.startswith("\\\\.\\"):
        return s
    ap = os.path.abspath(s)
    if ap.startswith("\\\\?\\") or ap.startswith("\\\\.\\"):
        return ap
    if ap.startswith("\\\\"):            # UNC: \\\\server\\share\\...
        return "\\\\?\\UNC\\" + ap[2:]   # -> \\\\?\\UNC\\server\\share\\...
    return "\\\\?\\" + ap                # o co drive letter: D:\\... -> \\\\?\\D:\\...


def _unlp(p):
    """Nguoc cua _lp: bo prefix extended-length de hien thi / tinh relative cho de doc."""
    s = str(p)
    if s.startswith("\\\\?\\UNC\\"):
        return "\\\\" + s[8:]
    if s.startswith("\\\\?\\"):
        return s[4:]
    return s


def _np(p) -> str:
    """Chuan hoa 1 chuoi path trong JSON (co the dung / hoac \\) thanh path native."""
    s = str(p).replace("/", os.sep).replace("\\", os.sep)
    return os.path.normpath(s)


def _is_under(child, parent) -> bool:
    """child co nam trong cay thu muc parent khong (so sanh khong phan biet hoa/thuong)."""
    try:
        c = os.path.normcase(os.path.abspath(_unlp(child)))
        p = os.path.normcase(os.path.abspath(_unlp(parent)))
    except Exception:
        return False
    return c == p or c.startswith(p + os.sep)


def _rel_posix(target, base):
    """Duong dan tuong doi tu base -> target, dung dau '/'. None neu phai di nguoc ra ngoai."""
    try:
        r = os.path.relpath(_unlp(target), _unlp(base))
    except ValueError:      # khac o dia
        return None
    if r == os.pardir or r.startswith(os.pardir + os.sep):
        return None
    return r.replace("\\", "/")


def isfile_safe(p) -> bool:
    try:
        return os.path.isfile(_lp(p))
    except OSError:
        return False


def isdir_safe(p) -> bool:
    """Nhu isfile_safe nhung cho thu muc. PHAI qua _lp: thu muc nam sau gioi han
    260 ky tu se bi bao 'khong ton tai' neu kiem bang Path.is_dir() thuong."""
    try:
        return os.path.isdir(_lp(p))
    except OSError:
        return False


def mtime_an_toan(p) -> float:
    """Thoi diem sua doi cua `p`, 0.0 neu khong doc duoc. PHAI qua `_lp`.

    Vi sao can: `Path(p).stat()` TRAN nem `FileNotFoundError WinError 3` voi
    duong dan qua 260 ky tu - trong khi `is_draft_dir` lai TIM THAY duoc chung
    (no di qua `isfile_safe` -> `_lp`). Hau qua da do duoc: mot `sorted(...,
    key=lambda d: d.stat().st_mtime)` nem giua chung lam VUT SACH ca danh sach
    project vua tim duoc, roi bao "khong quet duoc" - trong khi thuc te da tim
    thay du. Thu muc me dai la chuyen thuong ngay tren NAS ban giao.

    Tra 0.0 thay vi nem: day chi la khoa SAP XEP. Mot project khong doc duoc
    thoi diem sua thi cho no xuong cuoi danh sach, KHONG duoc lam hong ca danh
    sach.
    """
    try:
        return os.stat(_lp(str(p))).st_mtime
    except OSError:
        return 0.0


def tuyet_doi_that(s) -> bool:
    """True CHI khi `s` la duong dan tuyet doi that su - co goc, khong noi vao cwd.

    Vi sao can rieng mot ham chu khong dung `Path(s).is_absolute()`:
      Path("D:").is_absolute() la False, nhung Path("//server/share").is_absolute()
      lai True - khong bao phu het cac dang ma NGUOI DUNG go nham. Ham nay chan
      dung ba nhom da tung gay hong that:
        #23  "D:" hay "D:Videos"  -> drive-relative, Windows am tham noi vao thu
             muc lam viec cua tien trinh, tuc la vao chinh thu muc cong cu.
        #9   "\\192.168.1.214\\e" (MOT backslash, do shell nuot mat mot dau)
             -> khong phai UNC, tro thanh duong dan tuong doi tren o hien tai.
        ten tran ("goi_moi") -> nam trong thu muc cong cu.

    KHONG tu sua bang os.path.abspath(): sua am tham chinh la co che cua bug #23.
    Phat hien ra thi phai BAO TO cho nguoi dung, khong duoc doan y ho.
    """
    s = str(s).strip().strip('"')
    if not s:
        return False
    goc, con = os.path.splitdrive(s)
    if not goc:
        return False                       # "goi_moi", "\\192.168.1.214\\e"
    if goc.startswith("\\\\") or goc.startswith("//"):
        return True                        # UNC \\server\share
    return con[:1] in ("\\", "/")          # "D:\\..." dung; "D:" / "D:Videos" sai


CAU_HINH_NAME = "cau_hinh.json"


# Gia tri mac dinh khi khong co cau_hinh.json. `workers` de None nghia la
# TU CHON theo dich (2 khi dich la o mang, 4 khi la o cuc bo).
CAU_HINH_MAC_DINH = {
    "crf": 21,
    "preset": "veryfast",
    "workers": None,
    "workers_o_mang": 2,
    "workers_o_cuc_bo": 4,
}


# Ma loai o cua Windows (GetDriveTypeW)
_O_KHONG_BIET, _O_KHONG_CO, _O_ROI, _O_CO_DINH, _O_MANG, _O_CD, _O_RAM = range(7)


def _loai_o(chu):
    """Loai cua o `chu` (vd 'D') theo GetDriveTypeW. 0 neu khong xac dinh duoc.

    KHONG dung Path.exists(): tren mot o mang DA MAP nhung phien SMB da rot,
    `exists()` co the chan hang giay toi VO HAN va KHONG nem OSError, nen
    try/except khong cuu duoc. GetDriveTypeW chi tra cuu bang o cuc bo,
    khong dung toi thiet bi -> khong bao gio treo.
    """
    if os.name != "nt":
        return _O_KHONG_BIET
    try:
        import ctypes
        return int(ctypes.windll.kernel32.GetDriveTypeW(f"{chu}:\\"))
    except Exception:
        return _O_KHONG_BIET


def _cac_o_dang_co():
    """Danh sach chu o dang ton tai, lay tu bitmask - khong cham vao thiet bi."""
    if os.name != "nt":
        return []
    try:
        import ctypes
        mask = int(ctypes.windll.kernel32.GetLogicalDrives())
    except Exception:
        return list(string.ascii_uppercase)
    return [L for i, L in enumerate(string.ascii_uppercase) if mask & (1 << i)]


def fixed_drives():
    """Cac o CUC BO dang co. KHONG gom o mang.

    Truoc day ham nay goi `Path(f"{L}:/").exists()` cho ca 26 chu cai. Voi o mang
    da map ma phien SMB da rot, lenh do co the TREO chu khong chi cham - va vi no
    khong nem OSError nen khoi try/except o duoi vo tac dung. Day la nguyen nhan
    goc cua #25/#28 ("Python KHONG co timeout mac dinh cho I/O filesystem") xuat
    hien o mot cho thu ba, ngay TRUOC cau hoi "Thu muc/o de do".
    Ngoai ra viec loai o mang ra khoi danh sach mac dinh chinh la cai tien ma #27
    de nghi: quet cang o mang 22 TB de tim mot file la vo ich va mat hang gio.
    """
    out = []
    for L in _cac_o_dang_co():
        if _loai_o(L) == _O_CO_DINH:
            out.append(Path(f"{L}:/"))
    return out


def la_o_mang(duong_dan) -> bool:
    """Dich co nam tren o MANG khong (UNC hoac o da anh xa)?

    Dung de chon so luong tien trinh ma hoa chay song song: chay 4 luong cung luc
    tren cung mot NAS lam TANG MANH rui ro treo SMB chu khong chi lam cham
    (bug #25). Chi dung thu vien chuan - khong them phu thuoc.
    """
    s = str(duong_dan)
    if s.startswith("\\\\?\\UNC\\") or s.startswith("\\\\") and not s.startswith("\\\\?\\"):
        return True
    s2 = _unlp(s)
    if s2.startswith("\\\\"):
        return True
    dr = os.path.splitdrive(os.path.abspath(s2))[0]
    if len(dr) == 2 and dr[1] == ":":
        return _loai_o(dr[0]) == _O_MANG
    return False


_MOI_TRUONG = None


def mo_ta_moi_truong():
    """Chuoi mo ta may (Python + he dieu hanh), tinh MOT LAN.

    Do duoc: `platform.system()` mat 33,7 ms va `platform.platform()` mat 26,8 ms
    o lan goi dau vi chung truy van WMI. Khong lon so voi mot lan chay hang gio,
    NHUNG:
      - no nam ngay tren duong khoi dong, truoc khi nguoi dung lam gi;
      - WMI co the CHAM hoac TREO tren may bi siet quyen - voi 15-20 nguoi dung
        thi do la rui ro that, va lai la kieu treo khong nem loi (cung ho #25).
    Vi vay: tinh mot lan, boc try/except, va co duong lui KHONG cham WMI.
    """
    global _MOI_TRUONG
    if _MOI_TRUONG is not None:
        return _MOI_TRUONG
    import platform
    py = platform.python_version()
    try:
        he = f"{platform.system()} {platform.release()}"
    except Exception:
        # Duong lui: sys.platform khong cham WMI, luon co
        he = sys.platform
    # BANG MA ANSI cua may: thu quyet dinh viec doc dau ra ffmpeg dung hay sai.
    # May phat trien co ACP 65001 (UTF-8) nen trung voi dau ra ffmpeg va KHONG BAO
    # GIO lo loi giai ma; may con Windows tieng Viet mac dinh 1258. Khi 15-20 nguoi
    # gui bao cao ve, day la con so cho biet ngay ho co o cung mot the gioi khong.
    try:
        import ctypes
        he = f"{he} | ACP {ctypes.windll.kernel32.GetACP()}"
    except Exception:
        pass
    _MOI_TRUONG = (py, he)
    return _MOI_TRUONG


def read_json_loose(path: Path):
    """Doc JSON cho phep bytes thua o cuoi (CapCut hay them). Tra (obj, trailing_text)."""
    txt = Path(_lp(path)).read_text(encoding="utf-8")
    obj, end = json.JSONDecoder().raw_decode(txt)
    return obj, txt[end:]


def write_json_loose(path: Path, obj, trailing: str):
    Path(_lp(path)).write_text(json.dumps(obj, ensure_ascii=False) + trailing, encoding="utf-8")


def iter_json_files(root, loi=None):
    """Moi file .json trong cay (bo *.json.bak vi khong ket thuc bang .json).
    Bo file RONG (0 byte): CapCut co vai file config rong, khong phai loi.

    `loi`: None (mac dinh) = KHONG duyet duoc mot thu muc nao thi NEM OSError.
           Truyen mot list vao = ghi loi vao do roi chay tiep.

    Vi sao mac dinh la nem, khong phai im lang:
      `os.walk` khong co `onerror=` se BO QUA am tham ca mot nhanh cay thu muc khi
      khong liet ke duoc (NAS rot phien SMB - WinError 71 - hay xay ra tren NAS o
      day khi tai nang; hoac bi siet quyen). Khi do:
        - `cleanup_unused()` khong doc duoc cac JSON trong nhanh do
        - media chung dang dung KHONG nam trong `refd`
        - chot an toan `duoc_xoa_mo_coi = not loi_doc` VO HIEU, vi khong JSON nao
          "doc loi" - chung chua he duoc LIET KE
        - media bi XOA THAT, roi bao cao noi "DU"
      Im lang o day = mat du lieu trong goi ban giao. Nen mac dinh phai la nem.
    """
    out = []
    loi_walk = []
    for dp, dirs, fs in os.walk(_lp(root), onerror=loi_walk.append):
        for f in fs:
            if not f.lower().endswith(".json"):
                continue
            fp = os.path.join(dp, f)
            try:
                if os.path.getsize(fp) == 0:
                    continue
            except OSError:
                pass
            out.append(Path(_unlp(fp)))
    if loi_walk:
        if loi is None:
            raise OSError(
                f"khong duyet duoc {len(loi_walk)} thu muc khi quet .json trong"
                f" {_unlp(str(root))}: {loi_walk[0]}"
                f"  -> KHONG duoc coi day la 'quet xong': ket qua thieu se lam"
                f" cleanup xoa nham media va bao cao noi doi la 'DU'")
        loi.extend(loi_walk)
    return out


def draft_root_of(json_file, top, cache=None):
    """Goc de giai placeholder/'./': to tien GAN NHAT cua file JSON co ROOT_MARKERS.
    Khong tim thay thi lay `top`. KHONG BAO GIO di len cao hon `top`.

    Day la cho de sai nhat: file trong subdraft/X/ giai theo subdraft/X, nhung file
    trong Timelines/Y/ lai giai theo draft BAO NGOAI (Timelines khong phai draft root)."""
    top = Path(top)
    d = Path(json_file).parent
    chain = []
    while True:
        key = os.path.normcase(str(d))
        if cache is not None and key in cache:
            found = cache[key]
            break
        chain.append(key)
        if any(isfile_safe(d / m) for m in ROOT_MARKERS):
            found = d
            break
        if os.path.normcase(str(d)) == os.path.normcase(str(top)) or d.parent == d:
            found = top
            break
        d = d.parent
    if cache is not None:
        for k in chain:
            cache[k] = found
    return found


def json_role(name: str) -> str:
    """Vai tro cua 1 file .json trong draft - quyet dinh media cua no CO PHAI GOM khong.

      content  : draft_content.json / draft_info.json -> TIMELINE THAT.
                 Thieu media o day = mat hinh/mat tieng khi xuat video.
      registry : draft_meta_info.json -> 'kho media' hien trong CapCut.
                 Co the tro toi footage da import nhung KHONG dung tren timeline.
      cache    : mini_draft.json, draft_agency_*.json, ... -> cache/lich su cua CapCut.
                 Do tren project that: 3133 file (355 GB) CHI xuat hien o day, tuc la
                 footage khong he duoc dung. Gom chung la vo nghia."""
    if name in CONTENT_NAMES:
        return "content"
    if name == "draft_meta_info.json":
        return "registry"
    return "cache"


def is_real_abs(p: str) -> bool:
    """Duong dan tuyet doi toi 1 file media that (co the gom), khong phai placeholder/relative."""
    if not isinstance(p, str) or not p or p.startswith("##") or p.startswith("./") or p.startswith(".\\"):
        return False
    if Path(p.replace("\\", "/")).suffix.lower() not in MEDIA_EXT:
        return False
    # co drive letter X: hoac UNC \\server
    return (len(p) > 1 and p[1] == ":") or p.startswith("\\\\") or p.startswith("//")


def is_cosmetic(key: str, path: str) -> bool:
    """Anh bia/thumbnail: thieu thi KHONG anh huong video xuat ra (chi xau giao dien)."""
    if Path(path.replace("\\", "/")).suffix.lower() in VIDEO_AUDIO_EXT:
        return False
    k = (key or "").lower()
    return "cover" in k or Path(path.replace("\\", "/")).name.lower().startswith("draft_cover")


def deep_walk_strings(obj, cb, key=None):
    """Goi cb(key, value) cho MOI gia tri chuoi trong cay JSON (ke ca trong list)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                cb(k, v)
            else:
                deep_walk_strings(v, cb, k)
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, str):
                cb(key, v)
            else:
                deep_walk_strings(v, cb, key)


def deep_rewrite_strings(obj, fn, key=None) -> int:
    """Thay chuoi bang fn(key, value); tra so lan da thay."""
    n = 0
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                nv = fn(k, v)
                if nv is not None and nv != v:
                    obj[k] = nv
                    n += 1
            else:
                n += deep_rewrite_strings(v, fn, k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str):
                nv = fn(key, v)
                if nv is not None and nv != v:
                    obj[i] = nv
                    n += 1
            else:
                n += deep_rewrite_strings(v, fn, key)
    return n


def _fmt_time(sec) -> str:
    """Giay -> chuoi de doc: 45s / 3m12s / 1h05m. "?" neu chua tinh duoc.

    Guard `sec is None` la BAT BUOC. Truoc E1 co HAI ban chep cua ham nay va
    CHUNG KHAC NHAU: ban trong `xem_tien_trinh.py` co guard None, ban trong
    `goi_project_capcut.py` thi khong. Hai cho goi dung sentinel khac nhau cho
    "chua biet": mot ben `-1`, mot ben `None`. Khi gop lam mot ban chung ma lay
    nham ban CHUA duoc va, `xem_tien_trinh.py` chet ngay nhip dau tien (vong dau
    luon co speed == 0 nen remain luon la None).
    """
    if sec is None or sec < 0 or sec != sec:   # chua biet / am / NaN
        return "?"
    sec = int(sec)
    if sec < 60:
        return f"{sec}s"
    if sec < 3600:
        return f"{sec // 60}m{sec % 60:02d}s"
    return f"{sec // 3600}h{(sec % 3600) // 60:02d}m"

