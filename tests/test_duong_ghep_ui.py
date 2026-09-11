# -*- coding: utf-8 -*-
r"""Duong GHEP giua cua so chinh va cua so hang doi + HAI LUONG song song.

Hai lo hong duoc dong o day, ca hai deu nam o CHO NOI chu khong o trong mot
module nao - nen cac bo kiem don le khong cham toi:

  LO HONG 1 - `giao_dien._mo_hang_doi()`
    `test_cua_so_hang_doi.py` dung `CuaSoHangDoi` TRUC TIEP, con nguoi dung
    thi di qua `_mo_hang_doi()`. Doan noi do lam ba viec de sai:
      a. CHUP tuy chon muc 4 ngay tren thread chinh (tkinter khong an toan da
         luong - goi `.get()` tu thread phu nem RuntimeError).
      b. Bam lan hai phai LIFT cua so cu, khong duoc tao cua thu hai.
      c. Thieu thu muc `ui/` -> `showerror` huong dan, khong duoc de traceback
         roi vao khoang khong (duoi pythonw stderr la ho den).

  LO HONG 2 - HAI LUONG SONG SONG
    Cua so chinh dang QUET thu muc me (thread phu) + hang doi dang CHAY
    (thread phu khac). Diem nguy hiem: `Ong` thay `sys.stdout` TOAN TIEN
    TRINH. Neu ca hai cung lai `main()` thi hai `Ong` tranh nhau stdout va
    nhat ky lan vao nhau - dung hinh thai nhom C trong bug.md (bao cao sai).

    Ngoai ra hai pha co HAI CO HUY RIENG (`co_huy` cho pha goi, `co_huy_quet`
    cho pha quet - bug da sua truoc day). Phai chac chan lenh dung ben nay
    KHONG cham vao co cua ben kia.

Do bang SO NHIP, khong bang giay (bai hoc `test_dung_do.py`): so nhip bat
bien theo toc do may, con nguong giay thi may cham do oan.

Moi cum chay trong TIEN TRINH RIENG - xem ly do o `tien_ich_tk.chay_con`.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from tien_ich_tk import chay_con, co_tkinter, dem_pass_fail, thoat_an_toan

pas = fail = 0


def check(ten, dk, ct=""):
    global pas, fail
    if dk:
        pas += 1
        print(f"  PASS  {ten}")
    else:
        fail += 1
        print(f"  FAIL  {ten}")
        for d in str(ct).splitlines():
            print(f"           {d}")


DAU = '''
import os, sys, threading, time
from pathlib import Path
ROOT = Path(sys.argv[1])
sys.path.insert(0, str(ROOT))
import tkinter as tk

GIU = []
def nho(x):
    GIU.append(x)
    return x

pas = fail = 0
def check(ten, dk, ct=""):
    global pas, fail
    if dk:
        pas += 1
        print("  PASS  " + ten)
    else:
        fail += 1
        print("  FAIL  " + ten + ("  | " + str(ct) if ct else ""))

def xong():
    print("KET QUA: %d PASS / %d FAIL" % (pas, fail))
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(1 if fail else 0)

def canh(giay=25, nhan="TREO"):
    def _c():
        time.sleep(giay)
        print("  FAIL  " + nhan)
        print("KET QUA: 0 PASS / 1 FAIL")
        sys.stdout.flush()
        os._exit(7)
    threading.Thread(target=_c, daemon=True).start()

from tkinter import messagebox, filedialog
GOI = {"warning": [], "info": [], "error": []}
messagebox.showwarning = lambda *a, **k: GOI["warning"].append(a)
messagebox.showinfo    = lambda *a, **k: GOI["info"].append(a)
messagebox.showerror   = lambda *a, **k: GOI["error"].append(a)
messagebox.askyesno    = lambda *a, **k: True
'''


# --------------------------------------------------------- cum 1: duong ghep
CUM1 = DAU + r'''
canh(30, "TREO khi mo cua so hang doi")

import giao_dien as GD

root = nho(tk.Tk())
root.withdraw()
g = nho(GD.GiaoDien(root))
root.update()

# Dat 3 o tich ve mot to hop KHONG phai mac dinh, de biet gia tri co that su
# duoc chuyen sang hay khong.
g.v_trim.set(True)
g.v_scale.set(False)
g.v_clean.set(False)
g.v_do.set("D:\\mot;D:\\hai")
root.update()

g._mo_hang_doi()
root.update()

cs = getattr(g, "_cs_hd", None)
check("GHEP-01 _mo_hang_doi() tao duoc CuaSoHangDoi", cs is not None)

if cs is not None:
    # --- GHEP-02 tuy chon muc 4 duoc CHUP dung, tren thread chinh
    tc = cs.tc_mac_dinh
    check("GHEP-02 chup dung 'trim'", tc.get("trim") is True, tc)
    check("GHEP-02b chup dung 'scale' (False, khong phai mac dinh True)",
          tc.get("scale") is False, tc)
    check("GHEP-02c chup dung 'cleanup' (False, khong phai mac dinh True)",
          tc.get("cleanup") is False, tc)
    check("GHEP-02d chup ca danh sach thu muc do",
          "mot" in str(tc.get("do", "")) and "hai" in str(tc.get("do", "")), tc)

    # --- GHEP-03 la Toplevel RIENG, cua so chinh van song
    check("GHEP-03 cua so chinh VAN song sau khi mo hang doi",
          root.winfo_exists())
    check("GHEP-03b hang doi la cua so RIENG (Toplevel)",
          isinstance(cs.root, tk.Toplevel), type(cs.root).__name__)

    # --- GHEP-04 G va fixed_drives duoc TRUYEN VAO
    check("GHEP-04 G duoc truyen vao (khong de cua so tu import)",
          cs.G is not None)

    # --- GHEP-05 bam lan hai -> LIFT, khong tao cua thu hai
    dem_top = len([w for w in root.winfo_children()
                   if isinstance(w, tk.Toplevel)])
    cu = cs.root
    g._mo_hang_doi()
    root.update()
    dem_top2 = len([w for w in root.winfo_children()
                    if isinstance(w, tk.Toplevel)])
    check("GHEP-05 bam lan hai KHONG tao cua so thu hai",
          dem_top2 == dem_top, "%d -> %d" % (dem_top, dem_top2))
    check("GHEP-05b van la dung cua so cu", g._cs_hd.root is cu)

    # --- GHEP-06 dong hang doi roi mo lai -> tao cua so MOI, khong nem
    cs.root.destroy()
    root.update()
    g._mo_hang_doi()
    root.update()
    check("GHEP-06 dong roi mo lai -> tao duoc cua so moi",
          g._cs_hd is not None and g._cs_hd.root.winfo_exists())

# --- GHEP-07 thieu thu muc ui/ -> showerror huong dan, KHONG traceback
#  Duoi pythonw stderr la ho den: traceback roi vao khoang khong va nguoi
#  dung chi thay "bam nut khong co gi xay ra".
root2 = nho(tk.Tk())
root2.withdraw()
g2 = nho(GD.GiaoDien(root2))
root2.update()
g2._cs_hd = None

import builtins
_imp = builtins.__import__
def imp_hong(ten, *a, **k):
    if ten.startswith("ui."):
        raise ImportError("gia lap: chep thieu thu muc ui/")
    return _imp(ten, *a, **k)
builtins.__import__ = imp_hong
GOI["error"].clear()
try:
    g2._mo_hang_doi()
    nem_ra = False
except Exception as ex:
    nem_ra = "%s: %s" % (type(ex).__name__, ex)
finally:
    builtins.__import__ = _imp

check("GHEP-07 thieu ui/ -> KHONG nem ra ngoai", nem_ra is False, nem_ra)
check("GHEP-07b thieu ui/ -> hien showerror huong dan",
      len(GOI["error"]) == 1, GOI["error"])
if GOI["error"]:
    noi_dung = " ".join(str(x) for x in GOI["error"][0])
    check("GHEP-07c thong bao NOI RO la thieu thu muc ui/",
          "ui" in noi_dung, noi_dung[:120])

xong()
'''


# -------------------------------------------------- cum 2: hai luong song song
CUM2 = DAU + r'''
canh(40, "TREO khi chay hai luong song song")

import giao_dien as GD
import goi_project_capcut as G

root = nho(tk.Tk())
root.withdraw()
g = nho(GD.GiaoDien(root))
root.update()

# --- Ep pha QUET cua cua so chinh cham lai, co the tha ra khi muon.
cho_quet = threading.Event()
da_vao_quet = threading.Event()
def quet_cham(duong, nen_dung=None, on_error=None):
    da_vao_quet.set()
    cho_quet.wait(30)
    return [], 0, False
G.scan_drafts_recursive = quet_cham

import tkinter.filedialog as fd
fd.askdirectory = lambda *a, **k: str(ROOT)

g._quet_thu_muc_me()
root.update()
da_vao_quet.wait(10)
check("SONG-00 tien de: pha QUET cua cua so chinh da chay",
      da_vao_quet.is_set())
check("SONG-00b tien de: cua so chinh dang o trang thai dang_quet",
      g.dang_quet is True)

# --- Mo hang doi TRONG LUC dang quet
g._mo_hang_doi()
root.update()
cs = getattr(g, "_cs_hd", None)
check("SONG-01 mo duoc hang doi trong luc cua so chinh dang QUET",
      cs is not None and cs.root.winfo_exists())

# --- Cho hang doi chay mot muc (gia, cham), song song voi pha quet
cho_hd = threading.Event()
da_vao_hd = threading.Event()
def chay_mot_cham(muc, nen_dung):
    da_vao_hd.set()
    cho_hd.wait(30)
    return None

if cs is not None:
    cs.hd.chay_mot = chay_mot_cham
    cs._muc_moi()
    cs.v_draft.set("D:\\p1\\draft")
    cs.v_out.set("D:\\p1\\dich")
    cs._luu_form()
    root.update()
    cs._chay()
    root.update()
    da_vao_hd.wait(10)
    check("SONG-02 tien de: hang doi da bat dau chay mot muc",
          da_vao_hd.is_set())

    # --- SONG-03 THREAD CHINH van dap nhip khi CA HAI dang chay
    #  Do bang SO NHIP, khong bang giay.
    nhip = {"n": 0}
    def dap():
        nhip["n"] += 1
        if nhip["n"] < 200:
            root.after(10, dap)
    root.after(10, dap)
    t0 = time.time()
    while time.time() - t0 < 1.5:
        root.update()
        time.sleep(0.003)
    check("SONG-03 thread chinh VAN dap nhip khi ca hai luong dang chay",
          nhip["n"] >= 30, "chi dap %d nhip trong 1,5 giay" % nhip["n"])

    # --- SONG-04 HAI CO HUY doc lap: dung ben nay khong cham ben kia
    check("SONG-04 tien de: hai co huy la hai doi tuong KHAC nhau",
          g.co_huy is not g.co_huy_quet)
    g.co_huy.clear()
    g.co_huy_quet.clear()
    cs.hd.huy()
    root.update()
    check("SONG-04b hang doi huy -> KHONG cham co_huy_quet cua cua so chinh",
          not g.co_huy_quet.is_set())
    check("SONG-04c hang doi huy -> KHONG cham co_huy cua cua so chinh",
          not g.co_huy.is_set())

    # --- SONG-05 dung QUET ben cua so chinh -> khong cham hang doi
    g._dung_do()
    root.update()
    check("SONG-05 dung quet -> dat co_huy_quet", g.co_huy_quet.is_set())
    check("SONG-05b dung quet -> KHONG dong cua so hang doi",
          cs.root.winfo_exists())

    # --- SONG-06 sys.stdout phai duoc TRA LAI, khong bi mot Ong nao giu
    cho_quet.set()
    cho_hd.set()
    t0 = time.time()
    while time.time() - t0 < 3:
        root.update()
        time.sleep(0.01)
    ten_stdout = type(sys.stdout).__name__
    check("SONG-06 sau khi ca hai xong, sys.stdout KHONG con la Ong",
          ten_stdout != "Ong", ten_stdout)

    # --- SONG-07 nhat ky KHONG lan giua hai noi
    #  Cua so chinh ghi vao `g.hd` (queue), hang doi ghi vao `muc.nhat_ky`.
    #  Hai noi phai la hai kho khac nhau.
    m = cs.hd.muc[0] if cs.hd.muc else None
    check("SONG-07 hang doi va cua so chinh dung HAI kho nhat ky khac nhau",
          m is not None and m.nhat_ky is not g.hd, "cung mot doi tuong!")

xong()
'''


CAC_CUM = [
    ("cum 1 - duong ghep _mo_hang_doi()", CUM1, 180),
    ("cum 2 - hai luong song song", CUM2, 180),
]


def main():
    if not co_tkinter():
        print("KET QUA: 0 PASS / 0 FAIL")
        print("BO QUA: khong dung duoc tkinter tren may nay")
        return 2

    for ten, ma, gio in CAC_CUM:
        print(f"\n--- {ten} ---")
        code, ra = chay_con(ma, gio=gio, ten="ghep_")
        for d in ra.splitlines():
            d = d.strip()
            if d.startswith(("PASS", "FAIL")):
                print("  " + d)
        p, f = dem_pass_fail(ra)
        if p is None:
            check(f"{ten}: tien trinh con in duoc ket qua", False,
                  f"ma thoat {code}\n" + ra[-1800:])
            continue
        global pas, fail
        pas += p
        fail += f
        if code == 7:
            check(f"{ten}: KHONG bi treo", False, "dong ho canh da giet")
        elif code not in (0, 1):
            check(f"{ten}: tien trinh con thoat sach", False,
                  f"ma thoat {code}\n" + ra[-1800:])

    print()
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    return 1 if fail else 0


if __name__ == "__main__":
    thoat_an_toan(main())
