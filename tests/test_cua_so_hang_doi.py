# -*- coding: utf-8 -*-
"""Cua so HANG DOI (`ui/cua_so_hang_doi.py`) - 553 dong, 27 method, 0 bo kiem.

Vi sao bo kiem nay ra doi:
  `test_phu_file.py` (chot tinh E-03) neu dich danh file nay la file ma nguon
  DUY NHAT tu 150 dong tro len khong co bo kiem nao cham toi. No lai la lop
  giao dien viet GAN DAY NHAT, va chinh trong ma nguon cua no da ghi lai BA
  cai bay da vap:
    - dong  66: de quy VO HAN khi them muc dau tien (`_ve_bang` ->
                `selection_set` -> `<<TreeviewSelect>>` -> `_chon_muc` ->
                `_ve_tat_ca` -> `_ve_bang` -> ...). Do that: `root.update()`
                khong bao gio tra ve.
    - dong 318: `selection_set` nam NGOAI ham `_ve_bang` nen khoa o trong ham
                do la CHUA DU.
    - dong 489: `ve_bang/ve_log/ve_nut` phai khoi tao TRUOC `try`, khong thi
                `finally` doc bien chua ton tai -> nhip dap chet vinh vien.
  Ba loi do DA SUA. Nhung khong co gi giu cho chung khoi quay lai - va do
  chinh la dieu bo kiem nay lam.

  Ngoai ra `_rut_tin` co `except Exception: pass` (dong 515) - dung nhom B
  trong bug.md (nuot loi am tham). O day no la CO Y (mot loi ve khong duoc
  giet nhip dap vinh vien), nhung phai chung minh duoc rang nhip dap THAT SU
  song sot - chu khong phai tin vao chu thich.

Chia CUM - bat buoc, khong phai cho gon:
  Moi cum chay trong MOT tien trinh rieng qua `tien_ich_tk.chay_con`. So root
  Tk trong mot tien trinh la nguyen nhan gay `Tcl_AsyncDelete: async handler
  deleted by the wrong thread` - loi GIET CA TIEN TRINH va xoa luon ket qua
  da in. Bo kiem nay tao ~20 root; gom mot cho la chac chan vuot nguong.

  Cum 1 - dung cua so + form (them/sua/bo muc)
  Cum 2 - nhip dap `_rut_tin` (gioi han 200 tin, song sot loi, huy nhip)
  Cum 3 - quet thu (thread phu, chong chay chong, muc tam)
  Cum 4 - trang thai nut + dong cua so

Do DE QUY bang SO LAN GOI, khong bang GIAY (bai hoc `test_dung_do.py`): so
lan bat bien theo toc do may, con nguong giay thi may cham se do oan.

PHEP THU DOT BIEN da chay tren bo kiem nay: 12 dot bien, 10 bi giet (83%).
Hai con SONG SOT, va da dieu tra tung con - ca hai la DOT BIEN TUONG DUONG
(doi ma nhung khong doi hanh vi quan sat duoc), KHONG phai lo hong:

  1. "bo khoi tao `ve_bang = ve_log = ve_nut = False` truoc try"
     `finally` co `try/except Exception` bao ben trong, nen `NameError` bi
     NUOT ngay tai cho. Khong quan sat duoc tu ben ngoai. Phep HDUI-10c van
     giu vi no chot dung dieu duy nhat co the chot: nhip dap phai song sot.

  2. "bo khoa `_dang_ve` quanh `selection_set` trong `_luu_form`"
     De quy da duoc chan o GOC: `_chon_muc` khong con goi `_ve_tat_ca()`
     (dong 413-417), nen vong lap khong con ton tai. Khoa o dong 320 la lop
     phong thu THU HAI, du thua. Do that ca hai ban: ve_bang=3/4, chon_muc=3/6
     - GIONG HET nhau.

Ghi lai de nguoi sau khong mat cong "sua" mot phep kiem khong hong. Neu sau
nay `_chon_muc` duoc sua de goi lai `_ve_tat_ca()`, khoa dong 320 se tro lai
thanh phong thu THU NHAT va dot bien so 2 se bi giet ngay.
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


# Phan dau dung chung cho moi cum chay trong tien trinh con.
DAU = '''
import os, sys, threading, time
from pathlib import Path
ROOT = Path(sys.argv[1])
sys.path.insert(0, str(ROOT))
import tkinter as tk
from tkinter import ttk

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

# Thay hop thoai bang ban ghi lai - KHONG duoc de hop thoai that hien ra,
# no se chan tien trinh con vinh vien va bo kiem chi biet la "qua gio".
from tkinter import messagebox, filedialog
GOI = {"warning": [], "info": [], "error": [], "yesno": []}
messagebox.showwarning = lambda *a, **k: GOI["warning"].append(a)
messagebox.showinfo    = lambda *a, **k: GOI["info"].append(a)
messagebox.showerror   = lambda *a, **k: GOI["error"].append(a)

from ui.cua_so_hang_doi import CuaSoHangDoi
from ui.hang_doi import Muc, CHO, DANG_CHAY, XONG, LOI, HUY

def khong_chay(m, nen_dung):
    """chay_mot gia - bo kiem nay la T2, khong duoc cham vao loi that."""
    return None

def dung_cua(chay_mot=khong_chay, G=None, tc=None):
    root = nho(tk.Tk())
    root.withdraw()
    cs = nho(CuaSoHangDoi(root, chay_mot=chay_mot, tuy_chon_mac_dinh=tc,
                          G=G, fixed_drives=lambda: ["C:"]))
    return root, cs
'''


# ------------------------------------------------------------------- cum 1
CUM1 = DAU + r'''
# --- HDUI-01 dung cua so khong nem
root, cs = dung_cua()
root.update()
check("HDUI-01 dung cua so + update() khong nem", True)
check("HDUI-01b hang doi rong luc dau", len(cs.hd.muc) == 0)

# --- HDUI-02/03 them muc dau tien KHONG de quy vo han
#  Do bang SO LAN GOI, khong bang giay. Neu de quy quay lai thi so lan se
#  vot len hang tram/nghin (hoac treo han, va dong ho canh se giet tien trinh).
# Va vao LOP chu khong vao doi tuong - va PHAI truoc khi dung cua so.
#
# Bay da vap khi viet bo kiem nay, do phep thu dot bien phat hien: dong 134
# lam `self.bang.bind("<<TreeviewSelect>>", self._chon_muc)` - Tk CHUP LAI
# bound method NGAY LUC DUNG cua so. Gan `cs._chon_muc = ...` sau do thi Tk
# van goi ban goc, va bo dem luon bang 0. Phep kiem "khong de quy" khi ay do
# mot thu khong bao gio xay ra: ban goc va ban DA PHA cho ket qua GIONG HET
# nhau - dung hinh thai lo hong ghi o test_giao_dien.py:1536.
dem = {"ve_bang": 0, "chon_muc": 0}
_VB, _CM = CuaSoHangDoi._ve_bang, CuaSoHangDoi._chon_muc
def _dem_vb(self, *a, **k):
    dem["ve_bang"] += 1
    if dem["ve_bang"] > 400:
        print("  FAIL  HDUI-03 DE QUY VO HAN: _ve_bang goi qua 400 lan")
        print("KET QUA: 0 PASS / 1 FAIL")
        sys.stdout.flush()
        os._exit(9)
    return _VB(self, *a, **k)
def _dem_cm(self, *a, **k):
    dem["chon_muc"] += 1
    return _CM(self, *a, **k)
CuaSoHangDoi._ve_bang = _dem_vb
CuaSoHangDoi._chon_muc = _dem_cm

# Dung cua so MOI - cua so cu da chup ban goc roi.
root2, cs = dung_cua()
root2.update()
dem["ve_bang"] = dem["chon_muc"] = 0

# Dong ho canh: de quy vo han lam `update()` khong bao gio tra ve. Khong co
# dong ho nay thi bo kiem chi "qua gio" ma khong noi duoc dang ket o dau.
def canh():
    time.sleep(20)
    print("  FAIL  HDUI-02 TREO: update() khong tra ve (de quy vo han?)")
    print("KET QUA: 0 PASS / 1 FAIL")
    sys.stdout.flush()
    os._exit(7)
threading.Thread(target=canh, daemon=True).start()

cs.v_draft.set(r"D:\mot\draft")
cs.v_out.set(r"D:\mot\dich")
cs._luu_form()
root.update()

check("HDUI-02 them muc dau tien KHONG treo (khong de quy vo han)", True)
check("HDUI-02b muc da vao hang doi", len(cs.hd.muc) == 1, len(cs.hd.muc))
check("HDUI-03 _ve_bang goi so lan CO HAN khi them 1 muc",
      dem["ve_bang"] <= 6, "so lan=%d" % dem["ve_bang"])
check("HDUI-03b _chon_muc goi so lan CO HAN",
      dem["chon_muc"] <= 4, "so lan=%d" % dem["chon_muc"])
# TIEN DE: neu handler khong he duoc goi thi hai phep tren do mot thu khong
# ton tai va se xanh ke ca khi khoa chong de quy bi go bo.
check("HDUI-03c tien de: <<TreeviewSelect>> THAT SU goi _chon_muc",
      dem["chon_muc"] >= 1,
      "chon_muc=0 -> phep do khong cham duoc handler, HDUI-02/03 vo nghia")
CuaSoHangDoi._ve_bang, CuaSoHangDoi._chon_muc = _VB, _CM

# --- HDUI-04 thieu o 1 hoac o 2 -> canh bao, KHONG them muc
GOI["warning"].clear()
cs._muc_moi()
cs.v_draft.set("")
cs.v_out.set(r"D:\dich")
cs._luu_form()
check("HDUI-04 thieu o 1 -> hien canh bao", len(GOI["warning"]) == 1)
check("HDUI-04b thieu o 1 -> KHONG them muc", len(cs.hd.muc) == 1, len(cs.hd.muc))

GOI["warning"].clear()
cs.v_draft.set(r"D:\hai\draft")
cs.v_out.set("")
cs._luu_form()
check("HDUI-04c thieu o 2 -> hien canh bao", len(GOI["warning"]) == 1)
check("HDUI-04d thieu o 2 -> KHONG them muc", len(cs.hd.muc) == 1)

# --- HDUI-05 sua muc DANG CHAY bi TU CHOI
cs._muc_moi()
cs.v_draft.set(r"D:\hai\draft")
cs.v_out.set(r"D:\hai\dich")
cs._luu_form()
root.update()
check("tien de: da co 2 muc", len(cs.hd.muc) == 2, len(cs.hd.muc))

m2 = cs.hd.muc[1]
m2.trang_thai = DANG_CHAY
draft_cu = m2.draft
cs.bang.selection_set("1")
root.update()
GOI["info"].clear()
cs.v_draft.set(r"D:\DOI\THANH\CAI\KHAC")
cs._luu_form()
check("HDUI-05 sua muc DANG CHAY -> hien thong bao tu choi", len(GOI["info"]) == 1)
check("HDUI-05b sua muc DANG CHAY -> du lieu KHONG doi",
      m2.draft == draft_cu, "%r -> %r" % (draft_cu, m2.draft))

# --- HDUI-06 bo muc DANG CHAY bi TU CHOI
GOI["info"].clear()
cs._bo()
check("HDUI-06 bo muc DANG CHAY -> hien thong bao tu choi", len(GOI["info"]) == 1)
check("HDUI-06b bo muc DANG CHAY -> van con trong hang doi", len(cs.hd.muc) == 2)

# --- HDUI-07 doi cau hinh -> so lieu quet cu bi XOA
m2.trang_thai = CHO
m2.byte_goc, m2.so_file = 12345, 67
cs.bang.selection_set("1")
root.update()
cs.v_draft.set(r"D:\hai\draft_moi")
cs.v_out.set(r"D:\hai\dich")
cs._luu_form()
check("HDUI-07 doi cau hinh -> byte_goc bi xoa", m2.byte_goc is None, m2.byte_goc)
check("HDUI-07b doi cau hinh -> so_file bi xoa", m2.so_file is None, m2.so_file)

# --- HDUI-08 iid rac -> tra None, khong nem
cs.bang.selection_remove(*cs.bang.selection())
check("HDUI-08 khong chon gi -> _muc_dang_chon() tra None",
      cs._muc_dang_chon() is None)

# --- HDUI-20 noi danh sach o 3 bang ';' chu KHONG phai ','
import tkinter.filedialog as fd
fd.askdirectory = lambda *a, **k: "D:/mot"
cs.v_do.set("")
cs._them_thu_muc_do()
fd.askdirectory = lambda *a, **k: "D:/hai"
cs._them_thu_muc_do()
gt = cs.v_do.get()
check("HDUI-20 noi hai thu muc bang dau ';'", gt.count(";") == 1, repr(gt))
check("HDUI-20b KHONG dung dau ',' de noi", "," not in gt, repr(gt))

# --- HDUI-21 doi '/' thanh '\' (o 3 va o chon thu muc)
bs = chr(92)
check("HDUI-21 _them_thu_muc_do doi / thanh " + bs,
      "/" not in gt, repr(gt))
fd.askdirectory = lambda *a, **k: "D:/ba/bon"
cs._chon_thu_muc(cs.v_out)
check("HDUI-21b _chon_thu_muc doi / thanh " + bs,
      "/" not in cs.v_out.get(), repr(cs.v_out.get()))

# --- HDUI-26 fixed_drives nem -> van dung duoc cua so
def nem():
    raise OSError("o mang khong tra loi")
try:
    r2 = nho(tk.Tk())
    r2.withdraw()
    cs2 = nho(CuaSoHangDoi(r2, chay_mot=khong_chay, G=None, fixed_drives=nem))
    r2.update()
    check("HDUI-26 fixed_drives nem -> van dung duoc cua so", True)
except Exception as ex:
    check("HDUI-26 fixed_drives nem -> van dung duoc cua so", False,
          "%s: %s" % (type(ex).__name__, ex))

xong()
'''


# ------------------------------------------------------------------- cum 2
CUM2 = DAU + r'''
root, cs = dung_cua()
root.update()

# --- HDUI-09 `_rut_tin` co GIOI HAN moi nhip
#  Khong co gioi han thi `while True` khong bao gio gap queue.Empty ->
#  `after()` khong duoc dat lai -> mainloop CHET (SPEC 6.5).
for i in range(5000):
    cs.tin.put(("hd", ("x", "y")))
truoc = cs.tin.qsize()
cs._rut_tin()
sau = cs.tin.qsize()
rut = truoc - sau
check("tien de: da day duoc 5000 tin vao hang doi", truoc >= 5000, truoc)
check("HDUI-09 mot nhip rut CO GIOI HAN (khong rut het 5000)",
      rut <= 400, "rut %d tin" % rut)
check("HDUI-09b mot nhip van rut duoc dang ke (khong dung im)",
      rut >= 100, "rut %d tin" % rut)
check("HDUI-09c sau khi rut, nhip dap VAN duoc dat lai",
      cs._nhip is not None)

# --- HDUI-10 `_rut_tin` gap exception VAN dat lai nhip dap
#  Day la diem quan trong nhat cua cum nay: ma nguon co
#  `except Exception: pass` (nuot loi - nhom B). Viec nuot la CO Y, nhung
#  phai chung minh nhip dap that su song sot chu khong tin vao chu thich.
while not cs.tin.empty():
    cs.tin.get_nowait()
cs._nhip = None
def ve_bang_nem():
    raise RuntimeError("ep loi ve bang")
cs._ve_bang = ve_bang_nem
cs.tin.put(("hd", ("x", "y")))
try:
    cs._rut_tin()
    nem_ra_ngoai = False
except Exception:
    nem_ra_ngoai = True
check("HDUI-10 loi khi ve KHONG thoat ra ngoai _rut_tin", not nem_ra_ngoai)
check("HDUI-10b loi khi ve KHONG giet nhip dap vinh vien",
      cs._nhip is not None, "nhip=%r" % (cs._nhip,))

# --- HDUI-10c bien co phai khoi tao TRUOC `try` (bay dong 489)
#  Ep loi o NGAY dong dau trong `try`: neu bien khai bao ben trong thi
#  `finally` doc bien chua ton tai -> NameError thoat ra ngoai.
cs._ve_bang = ve_bang_nem
cs._nhip = None
class TinNem:
    def get_nowait(self):
        raise RuntimeError("ep loi ngay dong dau")
    def empty(self):
        return True
tin_cu = cs.tin
cs.tin = TinNem()
try:
    cs._rut_tin()
    loi_ra = None
except NameError as ex:
    loi_ra = "NameError: %s" % ex
except Exception as ex:
    loi_ra = "%s: %s" % (type(ex).__name__, ex)
cs.tin = tin_cu
check("HDUI-10c loi o dong DAU tien khong gay NameError trong finally",
      loi_ra is None, loi_ra)
check("HDUI-10d va nhip dap van duoc dat lai", cs._nhip is not None)

# --- HDUI-12 `_huy_nhip` bo qua <Destroy> cua widget CON
cs._ve_bang = lambda *a, **k: None
cs._nhip = root.after(10000, lambda: None)
class EvGia:
    pass
ev = EvGia()
ev.widget = cs.bang          # widget con, khong phai root
cs._huy_nhip(ev)
check("HDUI-12 <Destroy> cua widget CON khong huy nhip dap",
      cs._nhip is not None)
ev.widget = root
cs._huy_nhip(ev)
check("HDUI-12b <Destroy> cua ROOT thi huy nhip dap", cs._nhip is None)

# --- HDUI-11 dong cua so -> stderr SACH (khong 'invalid command name')
#  Duoi pythonw, rac nay roi thang vao _LOI_GIAO_DIEN.log va lam nguoi dung
#  tuong co loi that.
import io
for i in range(3):
    r = nho(tk.Tk())
    r.withdraw()
    c = nho(CuaSoHangDoi(r, chay_mot=khong_chay, G=None,
                         fixed_drives=lambda: ["C:"]))
    r.update()
    c._dong()
    for _ in range(5):
        try:
            r.update()
        except tk.TclError:
            break
check("HDUI-11 tao/huy cua so 3 lan khong nem", True)

xong()
'''


# ------------------------------------------------------------------- cum 3
CUM3 = DAU + r'''
root, cs = dung_cua(G=None)
root.update()

# --- HDUI-15 G is None -> bao ro, KHONG nem, KHONG tao thread
GOI["info"].clear()
cs._quet_thu()
check("HDUI-15 G=None -> hien thong bao", len(GOI["info"]) == 1)
check("HDUI-15b G=None -> KHONG tao luong quet", cs._luong_quet is None)

# --- HDUI-18 chua chon muc + o 1 trong -> canh bao, khong tao muc tam
class GGia:
    pass
root2, cs2 = dung_cua(G=GGia())
root2.update()
GOI["warning"].clear()
cs2._quet_thu()
check("HDUI-18 o 1 trong -> hien canh bao", len(GOI["warning"]) == 1)
check("HDUI-18b o 1 trong -> KHONG them muc vao hang doi",
      len(cs2.hd.muc) == 0, len(cs2.hd.muc))

# --- HDUI-16 quet thu chay o THREAD PHU, thread chinh VAN dap nhip
#  Do bang SO NHIP, khong bang giay (bai hoc test_dung_do.py).
cho = threading.Event()
import ui.quet_thu as QT
class KQGia:
    dat = True
    so_file_gom = 7
    def cac_dong(self):
        return ["dong mot", "dong hai"]
def quet_cham(m, G, nen_dung=None):
    cho.wait(10)
    return KQGia()
QT.quet_thu = quet_cham

cs2.v_draft.set(r"D:\mot\draft")
cs2.v_out.set(r"D:\mot\dich")
cs2._quet_thu()

nhip = {"n": 0}
def dap():
    nhip["n"] += 1
    if nhip["n"] < 60:
        root2.after(20, dap)
root2.after(20, dap)
t0 = time.time()
while time.time() - t0 < 1.2:
    root2.update()
    time.sleep(0.005)

check("HDUI-16 thread chinh VAN dap nhip trong luc quet thu",
      nhip["n"] >= 20, "chi dap %d nhip trong 1,2 giay" % nhip["n"])
check("HDUI-16b luong quet dang song", cs2._luong_quet is not None
      and cs2._luong_quet.is_alive())

# --- HDUI-17 bam Quet thu lan hai -> KHONG tao thread thu hai
luong_cu = cs2._luong_quet
cs2._quet_thu()
check("HDUI-17 bam lan hai khi dang quet -> khong tao luong moi",
      cs2._luong_quet is luong_cu)

# --- HDUI-19 muc TAM khong duoc lot vao hang doi
check("HDUI-19 quet thu muc tam -> hang doi VAN rong",
      len(cs2.hd.muc) == 0, len(cs2.hd.muc))

cho.set()
cs2._luong_quet.join(timeout=10)

# tin `quet_xong` phai duoc xu ly ma khong nem
cs2._rut_tin()
root2.update()
check("HDUI-19b xu ly tin 'quet_xong' khong nem", True)
check("HDUI-19c quet xong -> nut tro lai dung duoc",
      str(cs2.nut_quet_thu["state"]) == "normal", cs2.nut_quet_thu["state"])

xong()
'''


# ------------------------------------------------------------------- cum 4
CUM4 = DAU + r'''
root, cs = dung_cua()
root.update()

# --- HDUI-23 KHONG duoc noi "Xong." khi con muc CHO
#  Day la nhom C trong bug.md - nguy hiem nhat. Nguoi dung tin cai ho DOC,
#  khong phai cai tool DEM.
for i in range(3):
    cs._muc_moi()
    cs.v_draft.set(r"D:\p%d\draft" % i)
    cs.v_out.set(r"D:\p%d\dich" % i)
    cs._luu_form()
root.update()
check("tien de: da co 3 muc", len(cs.hd.muc) == 3, len(cs.hd.muc))

cs.hd.muc[0].trang_thai = XONG
cs._cap_nhat_nut()
tt = cs.v_trangthai.get()
check("HDUI-23 1 xong + 2 cho -> KHONG noi 'Xong.'",
      "Xong." not in tt, repr(tt))
check("HDUI-23b 1 xong + 2 cho -> noi 'San sang'",
      "ng" in tt, repr(tt))

# --- HDUI-24 tom tat khop trang thai THAT
cs.hd.muc[1].trang_thai = LOI
cs.hd.muc[2].trang_thai = CHO
cs._cap_nhat_nut()
tom = cs.v_tomtat.get()
that = cs.hd.mo_ta_tong_ket()
check("HDUI-24 v_tomtat khop mo_ta_tong_ket() cua lop dieu phoi",
      tom == that, "%r vs %r" % (tom, that))

# --- HDUI-24b het muc cho -> moi duoc noi "Xong."
cs.hd.muc[2].trang_thai = XONG
cs._cap_nhat_nut()
tt2 = cs.v_trangthai.get()
check("HDUI-24b het muc cho -> moi noi 'Xong.'", "Xong." in tt2, repr(tt2))

# --- HDUI-22 dang chay -> nut Luu bi xam, nut Dung sang
class HDGia:
    dang_chay = True
    muc = cs.hd.muc
    def cho_chay(self):
        return []
    def mo_ta_tong_ket(self):
        return "1/3 xong"
hd_that = cs.hd
cs.hd = HDGia()
cs._cap_nhat_nut()
check("HDUI-22 dang chay -> nut Luu bi xam",
      str(cs.nut_luu["state"]) == "disabled", cs.nut_luu["state"])
check("HDUI-22b dang chay -> nut Dung sang",
      str(cs.nut_dung["state"]) == "normal", cs.nut_dung["state"])
check("HDUI-22c dang chay -> nut Chay bi xam",
      str(cs.nut_chay["state"]) == "disabled", cs.nut_chay["state"])
cs.hd = hd_that

# --- HDUI-25 hang doi rong -> noi ro la rong
root3, cs3 = dung_cua()
root3.update()
cs3._cap_nhat_nut()
check("HDUI-25 hang doi rong -> v_tomtat noi 'trong'",
      "trống" in cs3.v_tomtat.get() or "trong" in cs3.v_tomtat.get(),
      repr(cs3.v_tomtat.get()))

# --- HDUI-13/14 dong cua so khi DANG CHAY phai HOI truoc
from tkinter import messagebox
root4, cs4 = dung_cua()
root4.update()
cs4._muc_moi()
cs4.v_draft.set(r"D:\x\draft")
cs4.v_out.set(r"D:\x\dich")
cs4._luu_form()

class HDChay:
    dang_chay = True
    def __init__(self, that):
        self.muc = that.muc
        self.da_huy = False
    def cho_chay(self):
        return []
    def mo_ta_tong_ket(self):
        return "0/1 xong"
    def huy(self):
        self.da_huy = True
    def bo(self, m):
        return False
cs4.hd = HDChay(cs4.hd)

messagebox.askyesno = lambda *a, **k: False
cs4._dong()
check("HDUI-13 dang chay + tra loi KHONG -> cua so VAN song",
      root4.winfo_exists())
check("HDUI-13b tra loi KHONG -> KHONG goi huy", not cs4.hd.da_huy)

messagebox.askyesno = lambda *a, **k: True
cs4._dong()
check("HDUI-14 tra loi CO -> goi huy() truoc khi dong", cs4.hd.da_huy)

xong()
'''


CAC_CUM = [
    ("cum 1 - dung cua so + form", CUM1, 120),
    ("cum 2 - nhip dap _rut_tin", CUM2, 120),
    ("cum 3 - quet thu (thread phu)", CUM3, 120),
    ("cum 4 - trang thai nut + dong cua so", CUM4, 120),
]


def main():
    if not co_tkinter():
        print("KET QUA: 0 PASS / 0 FAIL")
        print("BO QUA: khong dung duoc tkinter tren may nay"
              " (thieu Tcl/Tk hoac khong co phien man hinh)")
        return 2

    for ten, ma, gio in CAC_CUM:
        print(f"\n--- {ten} ---")
        code, ra = chay_con(ma, gio=gio, ten="hdui_")
        for d in ra.splitlines():
            d = d.strip()
            if d.startswith(("PASS", "FAIL")):
                print("  " + d)
        p, f = dem_pass_fail(ra)
        if p is None:
            check(f"{ten}: tien trinh con in duoc ket qua", False,
                  f"ma thoat {code}\n" + ra[-1500:])
            continue
        global pas, fail
        pas += p
        fail += f
        if code == 7:
            check(f"{ten}: KHONG bi treo", False, "dong ho canh da giet tien trinh")
        elif code not in (0, 1):
            check(f"{ten}: tien trinh con thoat sach", False,
                  f"ma thoat {code}\n" + ra[-1500:])

    print()
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    return 1 if fail else 0


if __name__ == "__main__":
    _ma = main()
    thoat_an_toan(_ma)
