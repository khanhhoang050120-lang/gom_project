# -*- coding: utf-8 -*-
"""`ui/chay_hang_doi.py` - ghi log ra ngoai + gioi han nhat ky.

Hai loi phat hien khi chay THAT (2026-09-10, gom DS1_124 qua hang doi):
  1. Chay KHONG GIAO DIEN thi moi dong log nam trong RAM cho toi luc ket thuc
     -> file log chi 358 byte sau 30 phut chay; tien trinh bi giet la mat sach.
  2. `muc.nhat_ky` la list KHONG GIOI HAN -> mot lan gom sinh hang chuc nghin
     dong, 5 project trong hang doi se phinh RAM lien tuc.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui import chay_hang_doi as CHD   # noqa: E402
from ui.hang_doi import Muc           # noqa: E402

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


class GiaG:
    """`goi_project_capcut` gia: in ra mot so dong roi tra ve."""

    CONTENT_NAMES = ("draft_content.json",)

    def __init__(self, so_dong=5, nem=None):
        self.so_dong = so_dong
        self.nem = nem

    def main(self, tuy_chon=None):
        for i in range(self.so_dong):
            print(f"dong {i}")
        if self.nem:
            raise self.nem


print("=" * 68)
print(" `ui/chay_hang_doi.py` - ghi log ra ngoai + gioi han nhat ky")
print("=" * 68)

# ------------------------------------------------------------ ghi_ra
print("\nGHI THANG RA NGOAI (`ghi_ra`)")
m = Muc(r"D:\a\P1", r"D:\g\P1", ten="P1")
thu = []
CHD.chay_mot_project(m, lambda: False, GiaG(so_dong=4), ghi_ra=thu.append)
check("moi dong deu di qua `ghi_ra`",
      len([d for d in thu if d.startswith("dong ")]) == 4,
      f"nhan {len(thu)} dong: {thu[:6]}")
check("nhat ky cua muc VAN co day du",
      len([d for d in m.nhat_ky if d.startswith("dong ")]) == 4,
      m.nhat_ky[:6])

# Khong truyen `ghi_ra` -> van chay binh thuong (tuong thich nguoc)
m2 = Muc(r"D:\a\P2", r"D:\g\P2", ten="P2")
CHD.chay_mot_project(m2, lambda: False, GiaG(so_dong=3))
check("khong co `ghi_ra` van chay duoc",
      len([d for d in m2.nhat_ky if d.startswith("dong ")]) == 3, m2.nhat_ky)

# `ghi_ra` HONG khong duoc lam hong lan gom
def ghi_hong(_d):
    raise OSError("o dia day")


m3 = Muc(r"D:\a\P3", r"D:\g\P3", ten="P3")
try:
    CHD.chay_mot_project(m3, lambda: False, GiaG(so_dong=3), ghi_ra=ghi_hong)
    check("`ghi_ra` hong KHONG lam hong lan gom", True)
except Exception as ex:
    check("`ghi_ra` hong KHONG lam hong lan gom", False,
          f"{type(ex).__name__}: {ex}")

# ------------------------------------------------------------ gioi han
print(f"\nGIOI HAN NHAT KY ({CHD.GIOI_HAN_NHAT_KY} dong)")
m4 = Muc(r"D:\a\P4", r"D:\g\P4", ten="P4")
n = CHD.GIOI_HAN_NHAT_KY + 500
CHD.chay_mot_project(m4, lambda: False, GiaG(so_dong=n))
check("nhat ky KHONG vuot gioi han",
      len(m4.nhat_ky) <= CHD.GIOI_HAN_NHAT_KY + 5,
      f"co {len(m4.nhat_ky)} dong, gioi han {CHD.GIOI_HAN_NHAT_KY}")
check("giu dong MOI NHAT (khong phai dong cu)",
      any(f"dong {n - 1}" == d for d in m4.nhat_ky),
      f"dong cuoi: {m4.nhat_ky[-3:]}")
check("noi RO da bo bao nhieu dong (khong im lang)",
      any("đã bỏ" in d and "dòng đầu" in d for d in m4.nhat_ky),
      m4.nhat_ky[:2])

# ------------------------------------------------------------ loi van ghi
print("\nLOI van phai di qua `ghi_ra` va vao nhat ky")
m5 = Muc(r"D:\a\P5", r"D:\g\P5", ten="P5")
thu5 = []
try:
    CHD.chay_mot_project(m5, lambda: False,
                         GiaG(so_dong=2, nem=OSError("het cho tren dia")),
                         ghi_ra=thu5.append)
    check("loi duoc nem len cho HangDoi bat", False, "KHONG nem")
except OSError:
    check("loi duoc nem len cho HangDoi bat", True)
check("nhat ky co dong giai thich loi ghi/doc",
      any("KHÔNG GHI/ĐỌC ĐƯỢC" in d for d in m5.nhat_ky), m5.nhat_ky[-4:])
check("nhat ky co goi y kiem o dich",
      any("đủ chỗ" in d for d in m5.nhat_ky), m5.nhat_ky[-4:])

# ------------------------------------------------- tra lai trang thai toan cuc
print("\nTRA LAI trang thai toan cuc du co loi")
import builtins   # noqa: E402
check("builtins.input da tra lai",
      "TraLoi" not in type(builtins.input).__name__,
      type(builtins.input).__name__)
check("sys.stdout da tra lai", type(sys.stdout).__name__ != "Ong",
      type(sys.stdout).__name__)

print()
print("=" * 68)
print(f"KET QUA: {pas} PASS / {fail} FAIL")
print("=" * 68)
sys.exit(1 if fail else 0)
