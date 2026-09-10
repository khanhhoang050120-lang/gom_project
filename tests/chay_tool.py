# -*- coding: utf-8 -*-
"""Lai `goi_project_capcut.main()` tu dong de chay E2E.

HAI CAI BAY DA TUNG LAM HONG VIEC NAY (bug.md #9, #10, #34) va cach ne o day:

 1. KHONG truyen duong dan qua shell / stdin redirect / argv - backslash bi nuot,
    `\\\\NAS\\share` thanh `\\NAS\\share` roi Windows hieu la drive-relative nen
    ket qua nam SAI O. O day path duoc truyen bang BIEN Python, khong qua shell.

 2. KHONG tra loi theo DANH SACH CUNG theo thu tu. So buoc hoi thay doi tuy tinh
    huong (buoc "do theo ten" chi hien khi co file thieu) nen danh sach cung se
    lech mot nhip va gay EOFError. O day tra loi theo NOI DUNG cau hoi.
"""
from __future__ import annotations

import builtins
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path


class KhongBietTraLoi(Exception):
    """Gap mot cau hoi chua co quy tac tra loi - phai bao ro, khong doan bua."""


def tao_bo_tra_loi(draft_dir, out_dir, che_do="1", tien_hanh=True, thu_muc_do=None):
    """Tra ve ham thay cho input(), tra loi dua tren NOI DUNG cau hoi.

    thu_muc_do: thu muc de "do theo ten" khi co file thieu. BAT BUOC phai co gia
    tri - de trong nghia la "tat ca o", va tren may nay co o mang nhieu TB nen
    test se treo hang gio (dung bug #27). Neu khong truyen, ta tao mot thu muc
    RONG tam thoi de buoc do ket thuc ngay lap tuc.
    """
    lich_su = []
    if thu_muc_do is None:
        import tempfile
        thu_muc_do = tempfile.mkdtemp(prefix="do_rong_")

    def tra_loi(loi_nhac=""):
        q = str(loi_nhac).lower()
        lich_su.append(str(loi_nhac))

        # Menu chon project: dung 'P' de dan thang duong dan folder draft
        if "nhap so" in q and "t" in q and "p" in q:
            return "P"
        if "duong dan folder draft" in q:
            return str(draft_dir)
        if "duong dan thu muc me" in q:
            return str(Path(draft_dir).parent)
        if "folder xuat ra" in q:
            return str(out_dir)
        if "chon 1 hoac 4" in q:
            return che_do
        # Buoc nay CHI hien khi co file thieu - khong duoc gia dinh no luon xuat hien
        if "thu muc" in q and "de do" in q:
            return thu_muc_do
        if "tien hanh" in q:
            return "y" if tien_hanh else "n"
        if "enter de dong" in q:
            return ""
        raise KhongBietTraLoi(f"Cau hoi chua co quy tac tra loi: {loi_nhac!r}")

    tra_loi.lich_su = lich_su
    return tra_loi


def chay(G, draft_dir, out_dir, che_do="1", tien_hanh=True, thu_muc_do=None,
         im_lang=True):
    """Chay main() mot lan. Tra (ma_thoat, van_ban_in_ra, lich_su_cau_hoi).

    ma_thoat: None neu main() tra ve binh thuong, hoac ma cua SystemExit.
    """
    tra_loi = tao_bo_tra_loi(draft_dir, out_dir, che_do, tien_hanh, thu_muc_do)
    goc = builtins.input
    builtins.input = tra_loi
    buf = io.StringIO()
    ma = None
    try:
        if im_lang:
            with redirect_stdout(buf):
                G.main()
        else:
            G.main()
    except SystemExit as e:
        ma = e.code
    finally:
        builtins.input = goc
    return ma, buf.getvalue(), list(tra_loi.lich_su)


def nap_tool(thu_muc_tool=None):
    """Nap goi_project_capcut nhu mot module rieng (khong dung __main__)."""
    import importlib.util
    goc = Path(thu_muc_tool or Path(__file__).resolve().parent.parent)
    if str(goc) not in sys.path:
        sys.path.insert(0, str(goc))
    spec = importlib.util.spec_from_file_location(
        "goi_project_capcut", goc / "goi_project_capcut.py")
    G = importlib.util.module_from_spec(spec)
    sys.modules["goi_project_capcut"] = G
    spec.loader.exec_module(G)
    return G
