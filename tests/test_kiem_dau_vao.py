# -*- coding: utf-8 -*-
"""`ui/kiem_dau_vao.py` - 10 phep kiem dau vao, KHONG can tkinter.

Truoc day cac phep kiem nay nam thang trong `_bat_dau()`, tron lan voi loi goi
`messagebox` - muon kiem phai dung ca cua so Tk va gia lap bam nut. Gio kiem
duoc bang cach goi ham va so ket qua.

Diem quan trong nhat cua bo kiem nay: phan biet "chan" voi "hoi". Mot phep
kiem le ra chi CANH BAO ma bi lam thanh CHAN se chan oan nguoi dung (vd mot
USB vua rut khong duoc chan ca lan gom).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui import kiem_dau_vao as KDV   # noqa: E402
from chung import tuyet_doi_that     # noqa: E402

pas = fail = 0


def check(ten, dk, chi_tiet=""):
    global pas, fail
    if dk:
        pas += 1
        print(f"  PASS  {ten}")
    else:
        fail += 1
        print(f"  FAIL  {ten}")
        if chi_tiet:
            for d in str(chi_tiet).splitlines():
                print(f"           {d}")


CONTENT_NAMES = ("draft_content.json", "draft_info.json")


def gia(co_thu_muc=(), co_file=()):
    """Tao bo ba ham gia lap filesystem - khong dung dia that."""
    tm = {str(Path(x)).lower() for x in co_thu_muc}
    tp = {str(Path(x)).lower() for x in co_file}
    return (lambda p: True,                                  # kiem_nhanh_duoc
            lambda p: str(Path(p)).lower() in tm,            # isdir_safe
            lambda p: str(Path(p)).lower() in tp)            # isfile_safe


D = r"D:\CapCut\Projects\com.lveditor.draft\Tet_2027"
OUT = r"D:\GOI_BAN_GIAO\Tet_2027"

print("=" * 68)
print(" `ui/kiem_dau_vao.py` - kiem dau vao truoc khi chay")
print("=" * 68)

# ---------------------------------------------------------------- muc 1
print("\nMUC 1 - folder draft")
kn, isd, isf = gia([D], [Path(D) / "draft_content.json"])
check("duong dan hop le -> DAT",
      KDV.kiem_draft(D, kn, isd, isf, CONTENT_NAMES).ok)

kq = KDV.kiem_draft("", kn, isd, isf, CONTENT_NAMES)
check("bo trong -> canh bao (khong phai chan)",
      not kq.ok and kq.muc == "canh_bao", repr(kq))

kn, isd, isf = gia([], [])
kq = KDV.kiem_draft(r"D:\khong_co", kn, isd, isf, CONTENT_NAMES)
check("thu muc khong ton tai -> chan",
      not kq.ok and kq.muc == "chan", repr(kq))

# Chon nham THU MUC ME - loi tu nhien nhat, truoc day lam treo may
me = r"D:\CapCut\Projects\com.lveditor.draft"
kn, isd, isf = gia([me], [])
kq = KDV.kiem_draft(me, kn, isd, isf, CONTENT_NAMES)
check("chon nham THU MUC ME -> chan",
      not kq.ok and kq.muc == "chan", repr(kq))
check("loi huong dan bam 'Quet thu muc me'",
      "Quet thu muc me" in kq.noi_dung, kq.noi_dung)

# draft_info.json cung duoc chap nhan
kn, isd, isf = gia([D], [Path(D) / "draft_info.json"])
check("chi co draft_info.json cung DAT",
      KDV.kiem_draft(D, kn, isd, isf, CONTENT_NAMES).ok)

# Duong dan dai qua 260 ky tu: `kiem_nhanh_duoc` tra False -> BO QUA phep kiem
dai = "D:" + chr(92) + ("x" * 300)
kn_cham = lambda p: False        # noqa: E731
check("duong dan qua dai -> KHONG chan oan",
      KDV.kiem_draft(dai, kn_cham, isd, isf, CONTENT_NAMES).ok)

# ---------------------------------------------------------------- muc 2
print("\nMUC 2 - folder XUAT RA")
CAM = [r"D:\tools_goi_project_capcut"]
kn, isd, isf = gia([], [])
check("duong dan hop le -> DAT",
      KDV.kiem_out(OUT, CAM, kn, isf, tuyet_doi_that).ok)

kq = KDV.kiem_out("", CAM, kn, isf, tuyet_doi_that)
check("bo trong -> canh bao", not kq.ok and kq.muc == "canh_bao", repr(kq))

# bug #23: "D:" khong phai goc o
for xau in ("D:", "GOI", r"..\GOI", "goi_ban_giao"):
    kq = KDV.kiem_out(xau, CAM, kn, isf, tuyet_doi_that)
    check(f"{xau!r} chua day du -> chan",
          not kq.ok and kq.muc == "chan", repr(kq))

kq = KDV.kiem_out("D:", CAM, kn, isf, tuyet_doi_that)
check("loi giai thich ro hau qua (goi nam sai cho)",
      "sai cho" in kq.noi_dung, kq.noi_dung)

# Chinh thu muc cong cu
kq = KDV.kiem_out(CAM[0], CAM, kn, isf, tuyet_doi_that)
check("chon chinh thu muc cong cu -> chan",
      not kq.ok and kq.muc == "chan", repr(kq))

kq = KDV.kiem_out(CAM[0].upper(), CAM, kn, isf, tuyet_doi_that)
check("khong phan biet HOA/thuong khi so thu muc cam",
      not kq.ok and kq.muc == "chan", repr(kq))

# Nhieu thu muc cam (khi dong goi .exe la BA cho khac nhau)
BA = [r"D:\app", r"D:\app_exe", r"C:\Temp\_MEI123"]
for c in BA:
    kq = KDV.kiem_out(c, BA, kn, isf, tuyet_doi_that)
    check(f"chan ca {c}", not kq.ok, repr(kq))

# Tro vao mot FILE
f = r"D:\mot_file.txt"
kn, isd, isf = gia([], [f])
kq = KDV.kiem_out(f, CAM, kn, isf, tuyet_doi_that)
check("tro vao mot FILE -> chan", not kq.ok and kq.muc == "chan", repr(kq))

# ---------------------------------------------------------------- muc 3
print("\nMUC 3 - thu muc do (CANH BAO chu khong chan)")
kn, isd, isf = gia([r"Y:\Footage"], [])
check("moi thu muc deu co -> DAT",
      KDV.kiem_do(r"Y:\Footage", kn, isd).ok)

kq = KDV.kiem_do(r"Y:\Footage;Z:\Da_rut_USB", kn, isd)
check("mot thu muc mat -> HOI, KHONG chan",
      not kq.ok and kq.hoi is True, repr(kq))
check("mot USB vua rut khong chan hai thu muc con lai",
      kq.muc == "hoi", repr(kq))
check("loi neu dung thu muc nao mat",
      "Da_rut_USB" in kq.noi_dung, kq.noi_dung)
check("loi KHONG bao nham thu muc con song",
      "Footage" not in kq.noi_dung, kq.noi_dung)
check("nhac dau CHAM PHAY", "CHAM PHAY" in kq.noi_dung, kq.noi_dung)

check("bo trong muc 3 -> DAT (chi quet o trong may)",
      KDV.kiem_do("", kn, isd).ok)

# ---------------------------------------------------------------- muc 4
print("\nMUC 4 - toi uu")
check("co bat mot o -> DAT", KDV.kiem_toi_uu(True, False, False).ok)
check("bat ca ba -> DAT", KDV.kiem_toi_uu(True, True, True).ok)

kq = KDV.kiem_toi_uu(False, False, False)
check("khong bat gi -> HOI, khong chan",
      not kq.ok and kq.hoi is True, repr(kq))
check("loi noi ro hau qua (nang hon nhieu)",
      "nang hon" in kq.noi_dung, kq.noi_dung)

# ------------------------------------------------- phan biet chan vs hoi
print("\nPHAN BIET 'chan' voi 'hoi' (sai la chan oan nguoi dung)")
kn, isd, isf = gia([], [])
chan = KDV.kiem_do(r"Z:\mat", kn, isd)
check("muc 3 KHONG BAO GIO la 'chan'", chan.muc == "hoi", repr(chan))
check("muc 4 KHONG BAO GIO la 'chan'",
      KDV.kiem_toi_uu(False, False, False).muc == "hoi")

kq = KDV.kiem_out("D:", CAM, kn, isf, tuyet_doi_that)
check("muc 2 duong dan sai PHAI la 'chan' (bug #23)",
      kq.muc == "chan" and kq.hoi is False, repr(kq))

print()
print("=" * 68)
print(f"  PASS {pas}   FAIL {fail}")
print("=" * 68)
sys.exit(1 if fail else 0)
