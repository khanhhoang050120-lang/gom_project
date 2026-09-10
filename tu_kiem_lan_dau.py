# -*- coding: utf-8 -*-
"""TU KIEM LAN DAU - chay mot lan sau khi giai nen, lan sau vao thang giao dien.

Muc dich: bat SOM va NOI RO nhung hong hoc cua viec giai nen/chep, thay vi de
nguoi dung phat hien sau 20 phut chay:
  - giai nen thieu file (zip qua NAS bi dut, hoac WinRAR bo qua file)
  - ffmpeg bi Windows Defender cach ly
  - ban Python di kem thieu DLL

QUAN TRONG - day KHONG phai lop bao ve duy nhat:
`kiem_ffmpeg_chay_duoc()` VAN chay moi lan chon che do 4 (bug #72). Neu ffmpeg
bi cach ly SAU lan kiem dau, tool van bat duoc dung luc can. Nho vay viec bo qua
tu kiem o cac lan sau la AN TOAN - no chi la canh bao som cho than thien, khong
phai thu duy nhat dung giua nguoi dung va mot lan chay hong.

Dau kiem duoc dat TEN THEO PHIEN BAN, nen ban moi se tu kiem lai tu dau.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

try:
    from loi import phien_ban as _PB
except ImportError:      # chay rieng le / thu muc la -> lui ve cach cu
    _PB = None

# GOC = noi DOC tai nguyen di kem (ffmpeg, cac file .py cua tool).
# Khi dong goi .exe thi day KHONG phai thu muc chua .exe - xem loi/phien_ban.py.
GOC = _PB.thu_muc_tai_nguyen() if _PB else Path(__file__).resolve().parent

# File BAT BUOC phai co sau khi giai nen. Thieu mot cai la hong theo kieu khac
# nhau, nen liet ke ro thay vi dem tong so file.
FILE_BAT_BUOC = [
    "goi_project_capcut.py",
    "toi_uu_dung_luong.py",
    "chung.py",
    "xem_tien_trinh.py",
    "giao_dien.py",
    "cau_hinh.json",
    # Package con: thieu MOT file la giao dien chet ngay khi khoi dong bang
    # ModuleNotFoundError - dung loai loi ma danh sach nay sinh ra de bat.
    "loi/__init__.py",
    "loi/phien_ban.py",
    "ui/__init__.py",
    "ui/cau_noi.py",
    "ui/kiem_dau_vao.py",
    "ui/hang_doi.py",
    "ui/chay_hang_doi.py",
    "ui/cua_so_hang_doi.py",
    "ui/quet_thu.py",
    "loi/bang_ma.py",
    "ffmpeg/bin/ffmpeg.exe",
    "ffmpeg/bin/ffprobe.exe",
]


def ten_dau(ver: str) -> str:
    """Dau kiem theo PHIEN BAN: ban moi se tu kiem lai, khong dung dau cu."""
    return f".da_tu_kiem_{ver}.json"


def thu_muc_dau() -> Path:
    """Noi GHI dau tu kiem. KHAC voi `GOC` (noi doc tai nguyen).

    Khi cai vao `Program Files`, thu muc chuong trinh khong ghi duoc; luc do
    `thu_muc_ghi()` lui ve `%LOCALAPPDATA%`. Neu van ghi canh chuong trinh nhu
    truoc thi dau kiem KHONG BAO GIO ghi duoc -> lan nao mo cung tu kiem lai,
    ton ~3,2 giay phep thu ffmpeg moi lan, va khong mot loi bao nao.
    """
    return _PB.thu_muc_ghi() if _PB else GOC


def da_kiem(goc: Path, ver: str) -> bool:
    p = Path(goc) / ten_dau(ver)
    if not p.is_file():
        return False
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d.get("phien_ban") == ver and d.get("ket_qua") == "DAT"
    except Exception:
        # Dau hong = coi nhu chua kiem. Kiem lai ton 5 giay, con tin nham thi
        # co the bo qua mot goi giai nen thieu file.
        return False


def ghi_dau(goc: Path, ver: str, chi_tiet: list) -> None:
    p = Path(goc) / ten_dau(ver)
    p.write_text(json.dumps({
        "phien_ban": ver,
        "ket_qua": "DAT",
        "luc": time.strftime("%Y-%m-%d %H:%M:%S"),
        "chi_tiet": chi_tiet,
    }, ensure_ascii=False, indent=1), encoding="utf-8")


# --------------------------------------------------------------- cac phep kiem
def _kiem_du_file(goc: Path):
    thieu = [t for t in FILE_BAT_BUOC if not (goc / t).is_file()]
    if thieu:
        return False, ("Giai nen THIEU file:\n  - " + "\n  - ".join(thieu)
                       + "\n\nHay giai nen LAI ca file zip.")
    return True, f"{len(FILE_BAT_BUOC)} file bat buoc deu co"


def _kiem_module(goc: Path):
    try:
        import chung          # noqa: F401
        import goi_project_capcut as G
        import toi_uu_dung_luong   # noqa: F401
        import xem_tien_trinh      # noqa: F401
        return True, f"nap duoc 4 module (ban {G.TOOL_VERSION})"
    except Exception as ex:
        return False, (f"Khong nap duoc module cua tool:\n  {type(ex).__name__}: {ex}"
                       "\n\nThuong la chep thieu file, hoac chep rieng le thay vi"
                       " ca thu muc.")


def _kiem_tkinter(goc: Path):
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        v = tk.TkVersion
        r.destroy()
        return True, f"tkinter {v} tao duoc cua so"
    except Exception as ex:
        return False, (f"Khong dung duoc giao dien (tkinter):\n  "
                       f"{type(ex).__name__}: {ex}"
                       "\n\nThu muc `python\\` co the bi giai nen thieu file."
                       "\nVan chay duoc bang `goi_project_capcut.bat` (dong lenh).")


def _kiem_ffmpeg(goc: Path):
    try:
        import toi_uu_dung_luong as TU
        ff, fp = TU.ff_paths(goc)
        if not ff:
            return False, ("Khong tim thay ffmpeg trong thu muc `ffmpeg\\bin\\`."
                           "\nChe do 4 (toi uu dung luong) se khong dung duoc.")
        ok, vi = TU.kiem_ffmpeg_chay_duoc(ff, fp)
        if not ok:
            return False, (f"ffmpeg co file nhung KHONG chay duoc:\n  {vi}"
                           "\n\nHay gap: (a) Windows Defender cach ly file,"
                           " (b) giai nen thieu.")
        return True, "ffmpeg chay duoc, co encoder libx264"
    except Exception as ex:
        return False, f"Loi khi kiem ffmpeg: {type(ex).__name__}: {ex}"


CAC_BUOC = [
    ("Kiem du file sau khi giai nen", _kiem_du_file),
    ("Nap cac module cua tool", _kiem_module),
    ("Kiem giao dien (tkinter)", _kiem_tkinter),
    ("Kiem ffmpeg (cho che do toi uu)", _kiem_ffmpeg),
]


def chay(goc: Path = None, bao=None):
    """Chay het cac buoc. `bao(i, tong, ten, ok, chi_tiet)` duoc goi sau moi buoc.

    Tra (tat_ca_dat, danh_sach_ket_qua).
    """
    goc = Path(goc or GOC)
    if str(goc) not in sys.path:
        sys.path.insert(0, str(goc))
    ds = []
    tat_ca = True
    for i, (ten, ham) in enumerate(CAC_BUOC, 1):
        try:
            ok, ct = ham(goc)
        except Exception as ex:
            ok, ct = False, f"{type(ex).__name__}: {ex}"
        # KHONG dung sau buoc dau tien that bai: nguoi dung nen thay HET van de
        # trong mot lan, thay vi sua mot cai roi chay lai de gap cai tiep theo.
        tat_ca = tat_ca and ok
        ds.append({"buoc": ten, "dat": ok, "chi_tiet": ct})
        if bao:
            bao(i, len(CAC_BUOC), ten, ok, ct)
    return tat_ca, ds


if __name__ == "__main__":
    def _in(i, tong, ten, ok, ct):
        print(f"  [{i}/{tong}] {'OK  ' if ok else 'HONG'} {ten}")
        for d in str(ct).splitlines():
            print(f"          {d}")

    print("=" * 70)
    print(" TU KIEM LAN DAU")
    print("=" * 70)
    _ok, _ds = chay(bao=_in)
    print()
    if _ok:
        import goi_project_capcut as _G
        ghi_dau(GOC, _G.TOOL_VERSION, _ds)
        print(f"  => TAT CA DAT. Da ghi dau {ten_dau(_G.TOOL_VERSION)}")
    else:
        print("  => CO VAN DE - xem o tren. KHONG ghi dau (lan sau se kiem lai).")
    sys.exit(0 if _ok else 1)
