# -*- coding: utf-8 -*-
"""Tien ich dung chung cho cac bo kiem co cham toi tkinter.

KHONG phai mot bo kiem - day la thu vien. `test_khuon_mau_bo_kiem.py` chi doi
khuon `KET QUA:` o cac file `test_*.py`, nen ten file nay co y khong bat dau
bang `test_`.

Vi sao phai tach ra: `test_giao_dien.py` da tich luy mot bo ky thuat tkinter
TRA GIA MOI CO (xem tung phan ben duoi). Bo kiem thu hai va thu ba cham toi
tkinter ma chep lai nguyen khoi thi vua vi pham nguyen tac chong God Component,
vua co nguy co ban chep lech dan - mot trong nhung cach hong am tham nhat
(`xem_tien_trinh.py` da tung co ban chep `_lp` hong am tham ba lan).

Bon thu o day:
  _GIU_TK / _nho   - chong `Tcl_AsyncDelete` giet ca tien trinh
  co_tkinter       - phat hien tkinter dung duoc (thu THAT, khong chi import)
  chay_con         - chay mot doan ma trong tien trinh RIENG
  thoat_an_toan    - `os._exit` sau khi flush, bo qua giai doan don dep
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


# --------------------------------------------------------------- giu tham chieu
#
# Giu MOI root Tk va MOI doi tuong giao dien tao ra trong bo kiem - dung tha ra.
#
# Vi sao: khi mot root bi `destroy()` roi doi tuong Python cua no duoc thu gom,
# `Variable.__del__` goi vao mot interpreter Tcl DA CHET. Da so lan chi la mot
# dong "Exception ignored" vo hai, nhung neu viec thu gom roi vao dung luc /
# dung thread khong mong doi thi Tcl bo ra
#     Tcl_AsyncDelete: async handler deleted by the wrong thread
# - loi GIET CA TIEN TRINH, khong bat duoc, xoa luon ket qua da in.
#
# Da do: voi Python HE THONG thi qua, voi ban DI KEM thi chet - va chet GIUA
# CHUNG chu khong phai luc thoat, nen `os._exit` o cuoi khong cuu duoc. Giu
# tham chieu thi khong co `__del__` nao chay trong luc chay; con luc thoat da
# co `thoat_an_toan()` bo qua toan bo giai doan don dep.
#
# Nguong tran KHAC NHAU theo ban Python va NGAU NHIEN theo thoi diem GC - nen
# khong duoc dua vao "so root nho thi chac khong sao".
_GIU_TK: list = []


def _nho(x):
    """Ghi nho mot doi tuong Tk de no khong bi thu gom giua chung."""
    _GIU_TK.append(x)
    return x


def co_tkinter() -> bool:
    """tkinter co DUNG DUOC khong - thu THAT chu khong chi `import`.

    `import tkinter` thanh cong khong chung minh duoc gi: may thieu thu vien
    Tcl/Tk van import duoc nhung `Tk()` se nem. Phai tao roi huy mot root that.
    """
    try:
        import tkinter
        tkinter.Tk().destroy()
        return True
    except Exception:
        return False


def chay_con(than: str, gio: int = 180, ten: str = "tk_con_"):
    """Chay mot doan ma trong TIEN TRINH RIENG, tra (ma_thoat, stdout+stderr).

    Vi sao phai la tien trinh rieng - HAI ly do doc lap:

    1. So luong root Tk trong MOT tien trinh la nguyen nhan gay
       `Tcl_AsyncDelete`. Mot bo kiem tao hai chuc root chac chan vuot nguong.
       Chia thanh cum, moi cum mot tien trinh, thi moi cum bat dau lai tu 0.

    2. Vai loi CHI lo ra khi `tkinter._default_root` con la None luc bat dau -
       vi du bug root Tk lac do `ttk.Style()` goi truoc `tk.Tk()`. Neu chay
       chung tien trinh voi bo kiem khac (chung da tao Tk roi), loi bi CHE
       HOAN TOAN.

    Ghi ma ra FILE roi chay, KHONG truyen qua `-c`: doi so dai di qua shell de
    bi nuot backslash (bug #9 / #34). Duong dan repo di qua `argv[1]` duoi
    dang mot doi so DUY NHAT, va ma con doc no bang `sys.argv[1]`.
    """
    tmp = Path(tempfile.mkdtemp(prefix=ten))
    try:
        f = tmp / "con.py"
        f.write_text(than, encoding="utf-8")
        r = subprocess.run([sys.executable, str(f), str(ROOT)],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=gio, cwd=str(ROOT))
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def thoat_an_toan(ma: int):
    """Thoat NGAY, bo qua giai doan don dep cua Python.

    Bo kiem da in xong ket qua roi moi goi day. Giai doan don dep binh thuong
    se thu gom cac doi tuong Tk con lai va co the ban ra `Tcl_AsyncDelete` -
    giet tien trinh voi ma khac 0 va XOA ket qua vua in. Chuyen do bien mot
    lan chay DAT thanh mot lan chay "THAT BAI" ma khong ai hieu vi sao.

    `flush()` TRUOC khi thoat la bat buoc: `os._exit` khong day bo dem ra.
    """
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass
    os._exit(ma)


def dem_pass_fail(ra: str):
    """Doc dong `KET QUA: N PASS / M FAIL` tu dau ra mot tien trinh con.

    Tra (pas, fail) hoac (None, None) neu khong tim thay - khong doan bua.
    """
    import re
    m = None
    for d in ra.splitlines():
        k = re.search(r"KET QUA:\s*(\d+)\s*PASS\s*/\s*(\d+)\s*FAIL", d)
        if k:
            m = k
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))
