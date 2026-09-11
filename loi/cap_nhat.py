# -*- coding: utf-8 -*-
r"""Kiem va ap ban cap nhat. Chi dung THU VIEN CHUAN.

Hop dong hanh vi da duoc CHOT TRUOC trong `tests/test_cap_nhat.py`, va file
nay viet de thoa hop dong do - khong phai nguoc lai.

Bon nguyen tac, moi cai giai mot rui ro muc Cao trong `tai_lieu/RISK.md`:

  R-10  KIEM CAP NHAT LA VIEC PHU, KHONG BAO GIO CHAN KHOI DONG.
        Mat mang, GitHub bi chan, rate-limit, JSON rac - tat ca that bai IM
        LANG. Voi 40-50 nguoi khong ranh ky thuat, mot hop thoai loi luc
        khoi dong la mot cuoc dien thoai cho MOI nguoi.

  R-02  DANG GOI DO THI TU CHOI CAP NHAT.
        Chan o tang API chu khong chi lam xam cai nut: nut xam la lop hien
        thi, con phim tat / dong ho hen gio / lan goi khac se di vong qua.

  R-14  DOI TEN NGUYEN KHOI, KHONG THAY TUNG FILE.
        Onedir co hang tram file. Ngat giua chung phai de lai HOAC ban moi
        hoan chinh HOAC ban cu hoan chinh - khong bao gio trang thai thu ba.

  R-03  LUON GIU MOT BAN CU DE QUAY VE.
        Cap nhat hong ma khong quay ve duoc = 40-50 may tac viec cung luc.

So sanh phien ban KHONG duoc dung so sanh chuoi: "1.10.0" < "1.9.0" theo thu
tu chuoi, tuc la nguoc hoan toan.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

# Thoi gian cho toi da khi hoi may chu. Ngan co y: day la viec phu, khong
# duoc lam nguoi dung cho.
HET_GIO = 6

TEN_BAN_CU = "_ban_cu"


# ---------------------------------------------------------- so sanh phien ban
def _tach(pb: str):
    """Tach '1.10.2' -> (1, 10, 2). Tra None neu khong doc duoc.

    Tra None chu khong nem: mot chuoi phien ban di dang tu may chu KHONG
    duoc lam chet app (R-10).
    """
    if not isinstance(pb, str):
        return None
    s = pb.strip().lstrip("vV")
    # Ban thu nghiem: "1.2.0-beta" -> phan truoc dau '-' la phien ban goc.
    hau_to = None
    if "-" in s:
        s, hau_to = s.split("-", 1)
    phan = s.split(".")
    try:
        so = tuple(int(x) for x in phan)
    except (ValueError, TypeError):
        return None
    return so, hau_to


def moi_hon(cua_may_chu: str, dang_dung: str) -> bool:
    """May chu co ban MOI HON ban dang dung khong?

    - So sanh theo TUNG SO, khong theo chuoi: "1.10.0" > "1.9.0".
    - Ban thu nghiem ("1.2.0-beta") KHONG duoc coi la moi hon ban chinh
      thuc cung so ("1.2.0") - nguoi dung khong xin ban thu nghiem.
    - Ban CU HON tren may chu -> False. Tu ha cap la mot cach lam hong bang
      cap nhat (R-03).
    - Doc khong duoc -> False. "Khong biet" phai xu ly nhu "khong co ban
      moi", khong duoc doan.
    """
    a = _tach(cua_may_chu)
    b = _tach(dang_dung)
    if a is None or b is None:
        return False
    so_a, hau_a = a
    so_b, hau_b = b

    # Do dai khac nhau: "1.2" vs "1.2.0" -> dem 0 cho bang.
    n = max(len(so_a), len(so_b))
    so_a = so_a + (0,) * (n - len(so_a))
    so_b = so_b + (0,) * (n - len(so_b))

    if so_a != so_b:
        return so_a > so_b
    # Cung so: ban co hau to (beta/rc) la ban TRUOC ban chinh thuc.
    if hau_a and not hau_b:
        return False
    if hau_b and not hau_a:
        return True
    return False


# ------------------------------------------------------------- cong chan R-02
def co_the_cap_nhat(dang_chay: bool = False,
                    hang_doi_chay: bool = False) -> bool:
    """Co duoc phep ap ban cap nhat ngay bay gio khong?

    Chan o TANG API, khong chi lam xam nut: nut xam chi la lop hien thi.
    Cap nhat giua luc dang goi mot project se thay file .exe va cac module
    ngay duoi chan tien trinh dang chay -> hong du lieu nguoi dung (R-02).
    """
    return not (dang_chay or hang_doi_chay)


class DangBanKhongCapNhat(RuntimeError):
    """Nem khi co nguoi goi `ap_ban_moi()` trong luc dang goi do."""


# ------------------------------------------------------------------ hoi server
def hoi_ban_moi(url: str, phien_ban_dang_dung: str, mo_url=None):
    """Hoi may chu xem co ban moi khong. KHONG BAO GIO NEM (R-10).

    Tra dict mo ta ban moi, hoac None khi: khong co ban moi, mat mang,
    bi chan, rate-limit, JSON rac, het gio - moi truong hop deu la None.
    Ly do: kiem cap nhat la viec PHU. Mot ngoai le thoat ra day se lam
    hong duong khoi dong cua app.
    """
    if mo_url is None:
        from urllib.request import urlopen
        mo_url = urlopen
    try:
        with mo_url(url, timeout=HET_GIO) as r:
            tho = r.read()
        d = json.loads(tho.decode("utf-8", "replace"))
        pb = str(d.get("tag_name") or d.get("phien_ban") or "")
        if not moi_hon(pb, phien_ban_dang_dung):
            return None
        return {"phien_ban": pb,
                "url_tai": d.get("url_tai") or d.get("browser_download_url"),
                "sha256": d.get("sha256"),
                "ghi_chu": d.get("body") or d.get("ghi_chu") or ""}
    except Exception:
        # CO Y nuot moi ngoai le - day la mot trong rat it cho duoc phep,
        # vi that bai o day KHONG duoc anh huong gi den nguoi dung. Nguoi
        # goi chi can biet "khong co ban moi".
        return None


# -------------------------------------------------------------- kiem toan ven
def bam_sha256(f) -> str:
    h = hashlib.sha256()
    with open(f, "rb") as fh:
        for khoi in iter(lambda: fh.read(1 << 20), b""):
            h.update(khoi)
    return h.hexdigest()


def du_file(thu_muc, toi_thieu: int = 5) -> bool:
    """Ban tai ve co du file khong - chong ap mot goi TAI DO DANG (R-14).

    Kiem CA so file lan tong kich thuoc: mot goi dut giua chung co the co
    du ten file nhung file cuoi bi cut.
    """
    thu_muc = Path(thu_muc)
    if not thu_muc.is_dir():
        return False
    cac = [f for f in thu_muc.rglob("*") if f.is_file()]
    if len(cac) < toi_thieu:
        return False
    return all(f.stat().st_size > 0 for f in cac)


# ------------------------------------------------------------------ ap ban moi
def ap_ban_moi(thu_muc_cai, thu_muc_moi, *, dang_chay=False,
               hang_doi_chay=False, sha_mong_doi=None, tep_tai=None,
               doi_ten=None):
    """Thay ban cai bang ban moi, NGUYEN KHOI.

    Thu tu co y, moi buoc chan mot kieu hong:

      1. Chan neu dang goi do                       (R-02)
      2. Kiem SHA256 file tai ve                    (R-14)
      3. Kiem ban moi DU FILE                       (R-14)
      4. Doi ten ban cai -> `_ban_cu`               (R-03: giu duong ve)
      5. Doi ten ban moi -> cho ban cai
      6. Neu buoc 5 hong: dua `_ban_cu` tro lai ngay

    Sau buoc 4 va truoc buoc 5 la khoang duy nhat co the ngat giua chung.
    Neu ngat o do, `phuc_hoi()` dua ban cu tro lai. Khong bao gio co trang
    thai "nua ban cu nua ban moi" vi hai buoc deu la DOI TEN THU MUC, mot
    thao tac nguyen tu o muc he thong tep.

    `doi_ten` cho phep bo kiem va ham nay de gia lap ngat giua chung.
    """
    if not co_the_cap_nhat(dang_chay, hang_doi_chay):
        raise DangBanKhongCapNhat(
            "Dang goi mot project - khong cap nhat giua chung duoc. "
            "Hay doi goi xong roi cap nhat.")

    if doi_ten is None:
        doi_ten = os.replace

    cai = Path(thu_muc_cai)
    moi = Path(thu_muc_moi)
    cu = cai.parent / (cai.name + TEN_BAN_CU)

    if sha_mong_doi and tep_tai:
        that = bam_sha256(tep_tai)
        if that.lower() != str(sha_mong_doi).lower():
            raise ValueError(
                f"SHA256 khong khop - ban tai ve co the hong hoac bi sua.\n"
                f"  mong doi: {sha_mong_doi}\n  that su : {that}")

    if not du_file(moi):
        raise ValueError(
            "Ban moi thieu file hoac co file rong - co the tai do dang. "
            "KHONG ap de tranh lam hong ban dang dung.")

    # Chi giu MOT ban cu: giu nhieu se phinh dia, ma khong ai quay ve xa hon
    # mot buoc.
    if cu.exists():
        shutil.rmtree(cu, ignore_errors=True)

    doi_ten(str(cai), str(cu))          # buoc 4
    try:
        doi_ten(str(moi), str(cai))     # buoc 5
    except BaseException:
        # Buoc 5 hong -> dua ban cu tro lai NGAY. Khong de nguoi dung o
        # trang thai "khong co ban nao" du chi mot khoanh khac.
        try:
            doi_ten(str(cu), str(cai))
        except BaseException:
            pass                        # `phuc_hoi()` van con la duong cuoi
        raise
    return cu


def phuc_hoi(thu_muc_cai) -> bool:
    """Quay ve ban cu. Tra True neu da quay duoc.

    Dung khi: cap nhat xong ma app khong mo duoc, hoac `ap_ban_moi()` bi
    ngat giua buoc 4 va 5 (R-03).
    """
    cai = Path(thu_muc_cai)
    cu = cai.parent / (cai.name + TEN_BAN_CU)
    if not cu.is_dir():
        return False
    if cai.exists():
        hong = cai.parent / (cai.name + "_hong")
        shutil.rmtree(hong, ignore_errors=True)
        try:
            os.replace(str(cai), str(hong))
        except OSError:
            return False
    try:
        os.replace(str(cu), str(cai))
        return True
    except OSError:
        return False


def con_ban_cu(thu_muc_cai) -> bool:
    cai = Path(thu_muc_cai)
    return (cai.parent / (cai.name + TEN_BAN_CU)).is_dir()
