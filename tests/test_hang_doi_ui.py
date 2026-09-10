# -*- coding: utf-8 -*-
"""`ui/hang_doi.py` - lop dieu phoi chay nhieu project, KHONG can tkinter.

Kiem cac tinh chat QUAN TRONG NHAT cua mot hang doi:
  - Mot muc LOI khong duoc chan cac muc con lai (ly do chinh de co hang doi)
  - Dung giua chung khong duoc bao "Xong." (bao cao sai ket qua - SPEC 5.2)
  - Muc da chay xong khong bi chay lai
  - Tong ket do tren TRANG THAI THAT cua tung muc, khong tren bo dem rieng
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.hang_doi import (CHO, DANG_CHAY, HUY, LOI, XONG,   # noqa: E402
                         HangDoi, Muc)

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


def hd_voi(chay_mot):
    h = HangDoi(chay_mot=chay_mot)
    for i in (1, 2, 3):
        h.them(Muc(rf"D:\draft\P{i}", rf"D:\goi\P{i}"))
    return h


print("=" * 68)
print(" `ui/hang_doi.py` - dieu phoi nhieu project")
print("=" * 68)

# ------------------------------------------------------------ chay binh thuong
print("\nCHAY BINH THUONG")
da = []
h = hd_voi(lambda m, nd: da.append(m.ten))
h.chay()
check("chay het ca 3 muc", da == ["P1", "P2", "P3"], f"{da}")
check("ca 3 deu XONG", len(h.theo_trang_thai(XONG)) == 3)
check("tong ket dung", h.mo_ta_tong_ket() == "3/3 xong", h.mo_ta_tong_ket())
check("moi muc co do thoi gian", all(m.giay is not None for m in h.muc))

# ------------------------------------------- mot muc LOI khong chan muc khac
print("\nMOT MUC LOI khong duoc chan cac muc con lai")


def hong_o_p2(m, nd):
    if m.ten == "P2":
        raise OSError("There is not enough space on the disk")


da = []
h = HangDoi(chay_mot=lambda m, nd: (da.append(m.ten), hong_o_p2(m, nd)))
for i in (1, 2, 3):
    h.them(Muc(rf"D:\draft\P{i}", rf"D:\goi\P{i}"))
h.chay()
check("VAN chay het ca 3", da == ["P1", "P2", "P3"], f"{da}")
check("P1 va P3 XONG",
      [m.trang_thai for m in h.muc] == [XONG, LOI, XONG],
      [m.trang_thai for m in h.muc])
p2 = h.muc[1]
check("P2 la LOI", p2.trang_thai == LOI)
check("loi giu nguyen thong diep goc",
      "not enough space" in p2.thong_bao, p2.thong_bao)
check("loi duoc ghi vao nhat ky cua muc",
      any("not enough space" in d for d in p2.nhat_ky), p2.nhat_ky)
check("tong ket dem ca loi",
      h.mo_ta_tong_ket() == "2/3 xong, 1 lỗi", h.mo_ta_tong_ket())

# ------------------------------------------------- BaseException cung phai bat
print("\nBaseException (KeyboardInterrupt...) cung phai thanh LOI cua muc")


def nem_base(m, nd):
    if m.ten == "P1":
        raise KeyboardInterrupt("nguoi dung bam Ctrl+C trong mot pha con")


h = hd_voi(nem_base)
try:
    h.chay()
    check("hang doi KHONG chet vi BaseException", True)
except BaseException as ex:
    check("hang doi KHONG chet vi BaseException", False, f"{type(ex).__name__}")
check("P1 thanh LOI, hai muc sau van chay",
      [m.trang_thai for m in h.muc] == [LOI, XONG, XONG],
      [m.trang_thai for m in h.muc])

# ------------------------------------------------------------ huy giua chung
print("\nHUY giua chung")


def huy_o_p1(m, nd):
    if m.ten == "P1":
        h.huy()          # nguoi dung bam Dung ngay khi P1 dang chay


h = hd_voi(lambda m, nd: huy_o_p1(m, nd))
h.chay()
check("P1 dang chay khi huy -> HUY, KHONG phai Xong",
      h.muc[0].trang_thai == HUY,
      f"{h.muc[0].trang_thai} - bao 'Xong.' sau khi huy la bao cao sai")
check("thong bao noi ro da dung giua chung",
      "giữa chừng" in h.muc[0].thong_bao, h.muc[0].thong_bao)
check("P2, P3 chua chay -> HUY",
      [m.trang_thai for m in h.muc[1:]] == [HUY, HUY],
      [m.trang_thai for m in h.muc[1:]])
check("thong bao cua muc chua chay khac muc dang chay",
      "trước khi đến lượt" in h.muc[1].thong_bao, h.muc[1].thong_bao)
check("tong ket dem huy",
      h.mo_ta_tong_ket() == "0/3 xong, 3 huỷ", h.mo_ta_tong_ket())

# --------------------------------------------- muc da xong khong chay lai
print("\nMUC DA KET THUC khong duoc chay lai")
da = []
h = hd_voi(lambda m, nd: da.append(m.ten))
h.chay()
da.clear()
h.chay()          # chay lan hai
check("khong chay lai muc nao", da == [], f"{da}")

# Them mot muc moi roi chay tiep -> chi muc moi chay
h.them(Muc(r"D:\draft\P4", r"D:\goi\P4"))
da.clear()
h.chay()
check("chi chay muc MOI them", da == ["P4"], f"{da}")

# ------------------------------------------------------------ bo muc
print("\nBO MUC khoi hang doi")
h = hd_voi(lambda m, nd: None)
check("bo duoc muc dang CHO", h.bo(h.muc[0]) is True)
check("hang doi con 2", len(h.muc) == 2)

h.muc[0].trang_thai = DANG_CHAY
check("KHONG bo duoc muc DANG CHAY", h.bo(h.muc[0]) is False,
      "bo muc dang chay -> tien trinh gom van chay ma khong ai theo doi")

# ------------------------------------------------------------ ten muc
print("\nTEN MUC suy tu duong dan")
check("duong dan thuong",
      Muc(r"D:\draft\Tet_2027", "x").ten == "Tet_2027")
check("duong dan ket thuc bang dau gach (KHONG ra chuoi rong)",
      Muc("D:" + chr(92) + "draft" + chr(92) + "Tet" + chr(92), "x").ten == "Tet")
check("duong dan UNC",
      Muc(chr(92) * 2 + "192.168.1.214" + chr(92) + "e" + chr(92) + "P1",
          "x").ten == "P1")
check("ten do nguoi goi dat thi giu nguyen",
      Muc(r"D:\a\b", "x", ten="Ten rieng").ten == "Ten rieng")

# ------------------------------------------------------------ bao tien do
print("\nBAO TIEN DO")
tin = []
h = HangDoi(chay_mot=lambda m, nd: None, bao=lambda k, m: tin.append(k))
h.them(Muc(r"D:\a\P1", r"D:\g\P1"))
h.chay()
check("co tin 'them'", "them" in tin, tin)
check("co tin 'doi' khi doi trang thai", tin.count("doi") >= 2, tin)
check("co tin 'het' khi xong ca hang doi", tin[-1] == "het", tin)

# ------------------------------------------- nen_dung duoc truyen xuong
print("\n`nen_dung` phai duoc truyen xuong ham chay")
nhan = []
h = HangDoi(chay_mot=lambda m, nd: nhan.append(callable(nd)))
h.them(Muc(r"D:\a\P1", r"D:\g\P1"))
h.chay()
check("ham chay nhan duoc `nen_dung` goi duoc", nhan == [True], nhan)

print()
print("=" * 68)
print(f"  PASS {pas}   FAIL {fail}")
print("=" * 68)
sys.exit(1 if fail else 0)
