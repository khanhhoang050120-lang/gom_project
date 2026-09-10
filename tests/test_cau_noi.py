# -*- coding: utf-8 -*-
"""`ui/cau_noi.py` - bang dich cau hoi -> dap an, KHONG can tkinter.

Vi sao bo kiem nay ton tai: `TraLoi` la phan DE SAI NHAT cua giao dien - tra
loi sai mot cau hoi la co the xoa nham du lieu nguoi dung. Truoc khi tach ra
module rieng, muon kiem no phai dung ca mot cua so Tk; gio kiem duoc bang
mot dict va vai lenh goi, nen chay duoc trong CI tren may khong co man hinh.

Kiem ba nhom:
  1. Moi cau hoi tra dung dap an (theo NOI DUNG, khong theo thu tu)
  2. Cau hoi la -> NEM, khong doan bua
  3. Hoi lai qua nhieu lan -> NEM, khong treo vo han
"""
from __future__ import annotations

import queue
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.cau_noi import NGUONG_LAP, Ong, TraLoi   # noqa: E402

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


CHUP = {
    "draft": r"D:\CapCut\Projects\com.lveditor.draft\Tet_2027",
    "out": r"D:\GOI_BAN_GIAO\Tet_2027",
    "do": r"Y:\Footage;Z:\Nhac",
    "trim": True, "scale": True, "cleanup": True,
}


def moi(chup=None, tra_loi_tien_hanh="y"):
    """Tao mot bo TraLoi voi Event DA day san - de khong phai cho."""
    ev = threading.Event()
    ev.set()
    return TraLoi(chup=dict(chup or CHUP), hd=queue.Queue(),
                  cho_tien_hanh=ev,
                  doc_tra_loi_tien_hanh=lambda: tra_loi_tien_hanh)


print("=" * 68)
print(" `ui/cau_noi.py` - cau noi giao dien <-> loi")
print("=" * 68)

# ------------------------------------------------------------ bang dich
print("\nBANG DICH cau hoi -> dap an")
t = moi()
check("'nhap so' -> P", t("Nhap so cua project, hoac P:") == "P")

t = moi()
check("'duong dan folder draft' -> muc 1",
      t("Dan duong dan folder draft:") == CHUP["draft"])

t = moi()
check("'duong dan thu muc me' -> THU MUC CHA cua muc 1",
      t("Dan duong dan thu muc me:") == str(Path(CHUP["draft"]).parent))

t = moi()
check("'folder xuat ra' -> muc 2",
      t("Dan duong dan folder xuat ra:") == CHUP["out"])

t = moi()
check("'thu muc' + 'de do' -> muc 3",
      t("Nhap cac thu muc de do theo ten:") == CHUP["do"])

t = moi()
check("'enter de dong' -> chuoi rong",
      t("Bam Enter de dong...") == "")

# ------------------------------------------------- chon che do theo o tich
print("\nCHON CHE DO theo o tich muc 4")
t = moi()
check("co bat toi uu -> '4'", t("Chon 1 hoac 4:") == "4")

t = moi({**CHUP, "trim": False, "scale": False, "cleanup": False})
check("khong bat gi -> '1'", t("Chon 1 hoac 4:") == "1")

for khoa in ("trim", "scale", "cleanup"):
    c = {**CHUP, "trim": False, "scale": False, "cleanup": False, khoa: True}
    t = moi(c)
    check(f"chi bat '{khoa}' -> van la '4'", t("Chon 1 hoac 4:") == "4")

# ------------------------------------------------------------ khong phan biet hoa thuong
print("\nKHONG phan biet HOA/thuong (loi in cau hoi kieu gi cung phai hieu)")
t = moi()
check("cau hoi VIET HOA van hieu",
      t("DAN DUONG DAN FOLDER XUAT RA:") == CHUP["out"])

# ------------------------------------------------------------ tien hanh
print("\nCAU HOI 'tien hanh' - ranh gioi QUET / COPY")
t = moi(tra_loi_tien_hanh="y")
check("nguoi dung bam COPY -> 'y'", t("Tien hanh? (y/N)") == "y")
check("co day tin 'cho_tien_hanh' vao hang doi",
      any(m[0] == "cho_tien_hanh" for m in list(t.hd.queue)),
      f"hang doi = {list(t.hd.queue)}")

t = moi(tra_loi_tien_hanh="n")
check("nguoi dung HUY -> 'n'", t("Tien hanh? (y/N)") == "n")

t = moi(tra_loi_tien_hanh=None)
check("chua tra loi gi -> mac dinh 'n' (an toan)",
      t("Tien hanh? (y/N)") == "n")

# ------------------------------------------------------------ cau hoi la
print("\nCAU HOI LA -> phai NEM, khong duoc doan bua")
t = moi()
try:
    t("Ban co muon xoa toan bo o D khong?")
    check("cau hoi la -> nem RuntimeError", False, "KHONG nem - da doan bua!")
except RuntimeError as ex:
    check("cau hoi la -> nem RuntimeError", True)
    check("loi noi ro cau hoi nao", "xoa toan bo" in str(ex), str(ex))

# ------------------------------------------------------------ chong lap vo han
print(f"\nCHONG LAP VO HAN (nguong {NGUONG_LAP})")
t = moi()
cau = "Dan duong dan folder draft:"
for i in range(NGUONG_LAP):
    t(cau)
check(f"{NGUONG_LAP} lan dau van tra loi binh thuong", True)
try:
    t(cau)
    check("qua nguong -> nem", False, "KHONG nem - se treo vo han!")
except RuntimeError as ex:
    check("qua nguong -> nem RuntimeError", True)
    check("loi noi ro so lan va goi y nguyen nhan",
          str(NGUONG_LAP + 1) in str(ex) and "draft" in str(ex).lower(), str(ex))

# Hai cau hoi KHAC nhau thi dem RIENG
t = moi()
for i in range(NGUONG_LAP):
    t("Dan duong dan folder draft:")
try:
    r = t("Dan duong dan folder xuat ra:")
    check("cau hoi KHAC dem rieng, khong bi lay", r == CHUP["out"])
except RuntimeError as ex:
    check("cau hoi KHAC dem rieng, khong bi lay", False, str(ex))

# ------------------------------------------------------------ log
print("\nMOI cau hoi phai duoc GHI vao nhat ky")
t = moi()
t("Dan duong dan folder xuat ra:")
dong = [m[1] for m in list(t.hd.queue) if m[0] == "log"]
check("cau hoi duoc day vao hang doi log",
      any("folder xuat ra" in d for d in dong), f"log = {dong}")

# ------------------------------------------------------------ Ong
print("\n`Ong` - chuyen sys.stdout thanh dong hang doi")
hd = queue.Queue()
o = Ong(hd)
o.write("dong mot\ndong hai\n")
ds = [m[1] for m in list(hd.queue)]
check("tach dung theo xuong dong", ds == ["dong mot", "dong hai"], f"{ds}")

hd = queue.Queue()
o = Ong(hd)
o.write("chua xuong dong")
check("dong chua xuong hang thi CHUA day", hd.qsize() == 0)
o.flush()
check("flush() day not phan con lai",
      [m[1] for m in list(hd.queue)] == ["chua xuong dong"])

hd = queue.Queue()
o = Ong(hd)
o.write("x" * 250)
check("dong rat dai (thanh tien do) van hien khong cho xuong dong",
      hd.qsize() == 1)

print()
print("=" * 68)
print(f"  PASS {pas}   FAIL {fail}")
print("=" * 68)
sys.exit(1 if fail else 0)
