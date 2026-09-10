# -*- coding: utf-8 -*-
"""Xac dinh THU MUC GOC va NOI GHI DU LIEU - dung chung cho ca tool.

Vi sao module nay ton tai
-------------------------
`Path(__file__).resolve().parent` dang duoc dung o 9 cho trong 6 file. Khi
con chay bang Python thuong thi no dung. Khi DONG GOI thanh .exe thi no SAI,
va sai theo hai kieu khac nhau:

  - onefile : `__file__` tro vao thu muc GIAI NEN TAM (`sys._MEIPASS`), khong
              phai thu muc chua .exe.
  - onedir  : `__file__` tro vao thu muc `_internal/`, khong phai thu muc
              chua .exe.

Hau qua deu la kieu "hong im lang" - khong exception, khong log, chi la file
nam sai cho hoac khong tim thay.

Loi giai NAY DA CO SAN trong `toi_uu_dung_luong._cac_goc_ffmpeg()` (ghi chu
"E2" trong do giai thich rat ro), nhung no chi ap dung cho viec tim ffmpeg.
Module nay nang no thanh ham dung chung cho MOI cho.

Ba khai niem KHAC NHAU, dung nham la sinh bug
---------------------------------------------
  `thu_muc_tai_nguyen()` - noi CHUA file di kem tool (ffmpeg, cau_hinh.json).
                           CHI DE DOC. Khi dong goi co the la thu muc tam.
  `thu_muc_chuong_trinh()` - noi chua .exe (hoac file .py khi chua dong goi).
                           Nguoi dung nhin thay thu muc nay.
  `thu_muc_ghi()`        - noi GHI duoc (log, dau tu kiem). Khi cai vao
                           `Program Files` thi hai cai tren KHONG ghi duoc.

Chi dung thu vien chuan (dieu kien ban giao trong CLAUDE.md).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ten thu muc con trong %LOCALAPPDATA% khi khong ghi duoc canh chuong trinh.
_TEN_APP = "GoiProjectCapCut"


def da_dong_goi() -> bool:
    """True khi dang chay tu ban .exe da dong goi (PyInstaller dat `sys.frozen`)."""
    return bool(getattr(sys, "frozen", False))


def thu_muc_chuong_trinh() -> Path:
    """Thu muc chua .exe (da dong goi) hoac chua ma nguon (chua dong goi).

    Day la thu muc NGUOI DUNG nhin thay. Dung no de:
      - so sanh voi folder XUAT RA (chan goi de len chinh thu muc tool)
      - hien trong thong bao loi cho nguoi dung doc
    KHONG dung no de doc file di kem - xem `thu_muc_tai_nguyen()`.
    """
    if da_dong_goi():
        # `sys.executable` la duong dan .exe THAT o ca onefile lan onedir.
        return Path(sys.executable).resolve().parent
    # Chua dong goi: file nay nam trong `loi/`, lui mot bac ra goc repo.
    return Path(__file__).resolve().parent.parent


def thu_muc_tai_nguyen() -> Path:
    """Thu muc chua file DI KEM tool (ffmpeg/, cau_hinh.json...). CHI DE DOC.

    onefile: la thu muc giai nen tam `sys._MEIPASS` - noi PyInstaller bung
    toan bo tai nguyen ra. Thu muc nay BIEN MAT khi tien trinh thoat, nen
    tuyet doi khong ghi gi vao day.
    """
    if da_dong_goi():
        mei = getattr(sys, "_MEIPASS", None)
        if mei:
            return Path(mei)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def cac_thu_muc_tai_nguyen() -> list:
    """MOI noi co the chua tai nguyen di kem, theo THU TU UU TIEN.

    Tra ve danh sach chu khong phai mot duong dan vi khi dong goi, tai nguyen
    co the nam o thu muc .exe (neu de canh, khong nhet vao gia) HOAC o thu muc
    giai nen tam. Thu ca hai roi hay ket luan "khong co".

    Day chinh la logic cua `toi_uu_dung_luong._cac_goc_ffmpeg()`, nang len
    thanh dung chung.
    """
    ra = []
    if da_dong_goi():
        ra.append(Path(sys.executable).resolve().parent)
        mei = getattr(sys, "_MEIPASS", None)
        if mei:
            ra.append(Path(mei))
    ra.append(Path(__file__).resolve().parent.parent)
    # Bo trung, giu thu tu
    kq, da = [], set()
    for g in ra:
        k = os.path.normcase(str(g))
        if k not in da:
            da.add(k)
            kq.append(g)
    return kq


def tim_tai_nguyen(duong_doi):
    """Tim mot file/thu muc di kem tool. Tra `Path` dau tien CO THAT, hoac None.

    `duong_doi` la duong dan TUONG DOI, vd "ffmpeg/bin/ffmpeg.exe" hoac
    "cau_hinh.json".

    Tra None (khong nem) de nguoi goi tu quyet: co cai thieu duoc phep thieu
    (cau_hinh.json -> dung mac dinh), co cai thi khong (ffmpeg).
    """
    for goc in cac_thu_muc_tai_nguyen():
        p = goc / duong_doi
        try:
            if p.exists():
                return p
        except OSError:
            # Duong dan qua dai / o mang rot phien: coi nhu khong co o goc nay,
            # thu goc tiep theo. KHONG duoc de mot OSError chan ca vong lap.
            continue
    return None


def _ghi_duoc(thu_muc) -> bool:
    """Thu GHI THAT mot file vao thu muc. Khong doan bang quyen.

    `os.access(W_OK)` tra ket qua SAI tren Windows (no doc quyen he thong chu
    khong tinh UAC virtualization). Cach dung nhat la thu ghi that roi xoa.
    """
    try:
        thu_muc = Path(thu_muc)
        thu_muc.mkdir(parents=True, exist_ok=True)
        thu = thu_muc / f".thu_ghi_{os.getpid()}.tmp"
        thu.write_text("x", encoding="utf-8")
        thu.unlink()
        return True
    except Exception:
        return False


_CACHE_GHI = None


def thu_muc_ghi() -> Path:
    """Thu muc GHI DUOC cho log va dau tu kiem.

    Uu tien ghi CANH CHUONG TRINH: de ban tu chua that su tu chua, va nguoi
    dung tim log ngay canh .exe khi can gui di ho tro.

    Neu khong ghi duoc (cai vao `Program Files`, o chi doc, USB khoa ghi) thi
    lui ve `%LOCALAPPDATA%\\GoiProjectCapCut`. Mat log la mat DUNG THU can nhat
    khi ho tro tu xa, nen phai co duong lui chu khong duoc bo qua.

    Ket qua duoc nho lai: phep thu ghi ton mot vong I/O, ma ham nay bi goi
    nhieu lan (moi dong log).
    """
    global _CACHE_GHI
    if _CACHE_GHI is not None:
        return _CACHE_GHI

    canh = thu_muc_chuong_trinh()
    if _ghi_duoc(canh):
        _CACHE_GHI = canh
        return _CACHE_GHI

    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if base:
        p = Path(base) / _TEN_APP
        if _ghi_duoc(p):
            _CACHE_GHI = p
            return _CACHE_GHI

    # Duong cuoi: thu muc tam cua he thong. Luon ghi duoc, nhung co the bi don
    # dep - chap nhan, con hon khong ghi duoc gi.
    import tempfile
    p = Path(tempfile.gettempdir()) / _TEN_APP
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception:
        p = Path(tempfile.gettempdir())
    _CACHE_GHI = p
    return _CACHE_GHI


def _dat_lai_cache_ghi():
    """Chi dung cho BO KIEM: xoa ket qua nho cua `thu_muc_ghi()`."""
    global _CACHE_GHI
    _CACHE_GHI = None


def mo_ta_noi_chay() -> str:
    """Mot dong mo ta de in ra nhat ky khi ho tro tu xa."""
    if da_dong_goi():
        kieu = "onefile" if getattr(sys, "_MEIPASS", None) else "onedir"
        return f"ban dong goi ({kieu}) tai {thu_muc_chuong_trinh()}"
    return f"ma nguon tai {thu_muc_chuong_trinh()}"
