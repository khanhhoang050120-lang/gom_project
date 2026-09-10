# -*- coding: utf-8 -*-
"""KIEM DAU VAO truoc khi chay - 10 phep kiem o tai_lieu/SPEC_UI_UX.md muc 8.

Module nay chi QUYET DINH, khong HIEN THI. Moi phep kiem tra ve mot `KetQua`
mo ta: co cho chay tiep khong, mac do gi, tieu de va noi dung thong bao.
Viec dung `messagebox` nao la cua `giao_dien.py`.

Vi sao tach
-----------
Truoc day 10 phep kiem nam thang trong `_bat_dau()`, trộn lan voi loi goi
`messagebox` - nghia la muon kiem chung chung phai dung ca mot cua so Tk va
gia lap thao tac bam nut. Tach ra thi kiem duoc bang cach goi ham va so ket
qua, chay duoc trong CI tren may khong co man hinh.

Ba MUC DO, khac nhau that su chu khong phai mau sac:
    "chan"    - khong cho chay, chi co nut OK
    "canh_bao"- khong cho chay, nhung la loi thieu thong tin nhe nhang hon
    "hoi"     - HOI nguoi dung, ho dong y thi VAN CHAY

Muc "hoi" quan trong: mot USB vua rut khong duoc chan hai thu muc con lai.

Module nay TUYET DOI khong import tkinter.
"""
from __future__ import annotations

import os
from pathlib import Path


class KetQua:
    """Ket qua mot phep kiem.

    `ok=True` nghia la di tiep duoc. Khi `ok=False` thi `muc` cho biet phai
    hien hop thoai kieu gi, va `hoi=True` nghia la nguoi dung van co the chon
    "van chay".
    """

    def __init__(self, ok, muc="", tieu_de="", noi_dung="", hoi=False):
        self.ok = ok
        self.muc = muc
        self.tieu_de = tieu_de
        self.noi_dung = noi_dung
        self.hoi = hoi

    def __repr__(self):
        if self.ok:
            return "KetQua(ok)"
        return f"KetQua({self.muc!r}, {self.tieu_de!r}, hoi={self.hoi})"


DAT = KetQua(True)


def _chan(tieu_de, noi_dung):
    return KetQua(False, "chan", tieu_de, noi_dung)


def _canh_bao(tieu_de, noi_dung):
    return KetQua(False, "canh_bao", tieu_de, noi_dung)


def _hoi(tieu_de, noi_dung):
    return KetQua(False, "hoi", tieu_de, noi_dung, hoi=True)


def kiem_draft(draft, kiem_nhanh_duoc, isdir_safe, isfile_safe, content_names):
    """Muc 1 - folder draft CapCut.

    `isdir_safe` chu KHONG `Path.is_dir()`: thu muc sau gioi han 260 ky tu bi
    `Path.is_dir()` bao "khong ton tai" -> chan oan mot project hop le.
    """
    if not draft:
        return _canh_bao("Thieu thong tin",
                         "Hay chon folder draft CapCut o muc 1.")

    if kiem_nhanh_duoc(draft) and not isdir_safe(Path(draft)):
        return _chan("Sai duong dan", f"Khong thay thu muc:\n{draft}")

    # Chon nham THU MUC ME (vd ...\com.lveditor.draft) la thao tac tu nhien
    # nhat, va truoc day no lam tool hoi lai vo han -> giao dien treo cung,
    # RAM tang lien tuc, chi End Task moi thoat. Chan ngay tai cua vao.
    if (kiem_nhanh_duoc(draft)
            and not any(isfile_safe(Path(draft) / n) for n in content_names)):
        return _chan(
            "Chua phai folder project",
            f"Folder nay khong co draft_content.json:\n{draft}\n\n"
            "Co ve ban dang chon THU MUC ME chua nhieu project,\n"
            "chu khong phai MOT project.\n\n"
            "Hay bam 'Quet thu muc me...' de liet ke cac project ben trong,\n"
            "roi bam 1 dong trong danh sach o tren.")
    return DAT


def kiem_out(out, thu_muc_cam, kiem_nhanh_duoc, isfile_safe, tuyet_doi_that):
    """Muc 2 - folder XUAT RA.

    `thu_muc_cam`: tap cac thu muc KHONG duoc dung lam noi xuat ra. Phai gom
    CA BA - thu muc module, thu muc .exe, thu muc tai nguyen - vi khi dong goi
    .exe chung la ba cho khac nhau (xem loi/phien_ban.py).
    """
    if not out:
        return _canh_bao("Thieu thong tin",
                         "Hay chon folder XUAT RA o muc 2.")

    # "D:" KHONG phai goc o - Windows noi no vao thu muc lam viec, tuc la do ca
    # goi thang vao thu muc cong cu, VA tool van bao "XONG" (bug #23).
    # Phat hien thi phai BAO TO, khong duoc tu sua bang abspath().
    if not tuyet_doi_that(out):
        return _chan(
            "Duong dan chua day du",
            f"O muc 2 dang la:\n    {out}\n\n"
            "Day chua phai duong dan day du nen Windows se hieu no theo\n"
            "thu muc cua chinh cong cu - goi se nam sai cho.\n\n"
            "Phai bat dau bang chu o VA dau gach, vi du:\n"
            "    D:" + chr(92) + "GOI_BAN_GIAO\n"
            "hoac o mang:  " + chr(92) * 2 + "192.168.1.214" + chr(92) + "e"
            + chr(92) + "GOI")

    p_out = Path(os.path.abspath(out))
    cam = {os.path.normcase(str(x)) for x in thu_muc_cam}
    if os.path.normcase(str(p_out)) in cam:
        return _chan("Khong duoc",
                     "Folder XUAT RA khong duoc la chinh thu muc cong cu.")

    if kiem_nhanh_duoc(p_out) and isfile_safe(p_out):
        return _chan("Sai duong dan",
                     f"Muc 2 dang tro vao mot FILE, khong phai thu muc:\n{p_out}")
    return DAT


def kiem_do(do_sach, kiem_nhanh_duoc, isdir_safe):
    """Muc 3 - thu muc de do theo ten.

    CANH BAO chu khong chan: mot USB vua rut khong nen chan hai thu muc con
    lai. Nguoi dung dong y thi van chay.
    """
    xau = [x for x in do_sach.split(";")
           if x and kiem_nhanh_duoc(x) and not isdir_safe(Path(x))]
    if not xau:
        return DAT
    return _hoi(
        "Thu muc do khong ton tai",
        "Cac thu muc sau o muc 3 KHONG ton tai va se bi BO QUA:\n\n  "
        + "\n  ".join(xau)
        + "\n\nNho: nhieu thu muc cach nhau bang dau CHAM PHAY ';'."
          "\n\nVan chay?")


def kiem_toi_uu(trim, scale, cleanup):
    """Muc 4 - khong bat o toi uu nao thi hoi lai."""
    if trim or scale or cleanup:
        return DAT
    return _hoi(
        "Khong bat toi uu nao",
        "Ban chua tich o nao o muc 4.\n\n"
        "Tool se copy NGUYEN BAN (an toan nhat nhung nang hon nhieu).\n"
        "Tiep tuc?")
