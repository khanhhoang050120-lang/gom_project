# -*- coding: utf-8 -*-
"""CAU NOI giua giao dien va loi - phan quan trong nhat cua kien truc UI.

Nguyen tac bat kha xam pham (tai_lieu/SPEC_UI_UX.md §1)
-------------------------------------------------------
Giao dien KHONG viet lai logic nao. No LAI chinh `goi_project_capcut.main()`
bang cach:
  - thay `builtins.input` bang mot ham tra loi theo NOI DUNG cau hoi
  - huong `sys.stdout` vao o Nhat ky
Nho vay giao dien va dong lenh KHONG THE lech hanh vi: chung la MOT.

Module nay chua DUNG hai thu do: `Ong` va `TraLoi`.

Vi sao tach rieng
-----------------
1. Day la noi DE SAI NHAT va hau qua nang nhat: tra loi sai mot cau hoi la co
   the xoa nham du lieu nguoi dung.
2. Day la noi DUY NHAT can sua khi loi them/bot cau hoi. Nam lan trong mot
   class 750 dong thi khong ai tim ra.
3. Tach ra thi KIEM THU DUOC MA KHONG CAN tkinter: dua vao mot ban chup form,
   dua vao mot cau hoi, so dap an. Truoc day muon kiem phai dung ca cua so.

Diem 3 la ly do manh nhat - no bien phan rui ro cao nhat cua UI thanh phan
DUY NHAT trong UI co the kiem tu dong trong CI.

Module nay TUYET DOI khong import tkinter.
"""
from __future__ import annotations

from pathlib import Path


class Ong:
    """Thay cho `sys.stdout`: day tung dong vao hang doi cua giao dien.

    Khong dung `contextlib.redirect_stdout` vi no KHONG theo thread (da ghi
    trong bug.md) - nguoi goi phai thay `sys.stdout` truc tiep va tra lai
    trong `finally`.
    """

    def __init__(self, hd):
        self.hd = hd
        self._dem = ""

    def write(self, s):
        self._dem += s
        while "\n" in self._dem:
            dong, self._dem = self._dem.split("\n", 1)
            self.hd.put(("log", dong))
        # Dong chua xuong hang (vd thanh tien do) van phai hien
        if len(self._dem) > 200:
            self.hd.put(("log", self._dem))
            self._dem = ""

    def flush(self):
        if self._dem:
            self.hd.put(("log", self._dem))
            self._dem = ""


# Nguong lap toi da cho MOT cau hoi. Tool hoi lai cung mot cau khi cau tra loi
# khong dung (vd folder khong co draft_content.json) - o dong lenh nguoi that
# se sua, o day ta tra loi y het -> vong lap vo han, giao dien treo cung, RAM
# tang lien tuc, chi End Task moi thoat.
# Nguong 3 de khong pha luong hop le nao co the hoi lai.
NGUONG_LAP = 3


class TraLoi:
    """Thay cho `input()`: tra loi theo NOI DUNG cau hoi, KHONG theo thu tu.

    Vi sao khong theo thu tu: so buoc hoi THAY DOI tuy tinh huong - buoc "do
    theo ten" chi hien khi co file thieu. Mot danh sach cung se lech mot nhip.
    Day la bay da ghi o bug.md #10.

    Ham nay chay o THREAD PHU. No CHI duoc dung `chup` - ban chup gia tri form
    da lay san tren thread chinh. Goi `.get()` cua bat ky bien tkinter nao tu
    day se nem `RuntimeError: main thread is not in main loop`.
    """

    def __init__(self, chup, hd, cho_tien_hanh, doc_tra_loi_tien_hanh):
        """
        chup      : dict {draft, out, do, trim, scale, cleanup} - BAN CHUP form
        hd        : hang doi de day dong log / tin hieu ve giao dien
        cho_tien_hanh : `threading.Event` - dung cho nguoi dung bam nut
        doc_tra_loi_tien_hanh : ham khong tham so, tra "y" / "n" / None

        `doc_tra_loi_tien_hanh` la HAM chu khong phai gia tri: luc dung `TraLoi`
        thi nguoi dung chua bam gi ca, cau tra loi chi co sau khi `Event` day.
        """
        self.chup = chup
        self.hd = hd
        self.cho_tien_hanh = cho_tien_hanh
        self._doc_tra_loi = doc_tra_loi_tien_hanh
        self.lap = {}

    def __call__(self, loi_nhac=""):
        q = str(loi_nhac).lower()
        self.hd.put(("log", str(loi_nhac).rstrip()))

        self.lap[q] = self.lap.get(q, 0) + 1
        if self.lap[q] > NGUONG_LAP:
            raise RuntimeError(
                "Tool hoi lai cung mot cau %d lan:\n  %s\n"
                "Duong dan o muc 1 co le khong phai folder draft CapCut."
                " Da dung de khoi treo may."
                % (self.lap[q], str(loi_nhac).strip()))

        return self._dap(q, loi_nhac)

    def _dap(self, q, loi_nhac):
        c = self.chup

        if "nhap so" in q:
            return "P"
        if "duong dan folder draft" in q:
            return c["draft"]
        if "duong dan thu muc me" in q:
            return str(Path(c["draft"]).parent)
        if "folder xuat ra" in q:
            return c["out"]
        if "chon 1 hoac 4" in q:
            return "4" if (c["trim"] or c["scale"] or c["cleanup"]) else "1"
        if "thu muc" in q and "de do" in q:
            return c["do"]
        if "tien hanh" in q:
            # DUNG lai cho nguoi dung bam nut - day la ranh gioi giua QUET va COPY
            self.hd.put(("cho_tien_hanh", None))
            self.cho_tien_hanh.wait()
            return self._doc_tra_loi() or "n"
        if "enter de dong" in q:
            return ""

        # KHONG doan bua: mot cau hoi la ma tra loi sai co the xoa nham du lieu
        raise RuntimeError(
            f"Giao dien chua biet tra loi cau hoi: {loi_nhac!r}")
