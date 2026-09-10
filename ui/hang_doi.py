# -*- coding: utf-8 -*-
"""HANG DOI nhieu project - lop dieu phoi chay `main()` nhieu lan.

RANG BUOC QUAN TRONG NHAT (tai_lieu/SPEC_UI_UX.md muc 1)
---------------------------------------------------------
Lop nay goi `goi_project_capcut.main()` LAN LUOT cho tung project.
No TUYET DOI KHONG duoc tu goi cac ham con ben trong (`collect_refs`,
`plan_package`, `optimize_package`...).

Vi sao: nguyen tac "giao dien khong viet lai logic" sinh ra de giao dien va
dong lenh KHONG THE lech hanh vi. Neu hang doi tu dieu phoi cac pha, moi ban
va logic sau nay phai sua HAI noi, va hai noi se troi khoi nhau. Do dung la
cai bay ma nguyen tac do sinh ra de tranh.

Vi vay module nay chi lam ba viec:
  1. Giu danh sach project can goi va trang thai tung cai
  2. Goi `chay_mot()` - ham do nguoi goi truyen vao - cho tung muc
  3. Bao cao tien do qua hang doi tin

Trang thai toan cuc giua cac lan chay
-------------------------------------
`main()` da tu xoa bo nho dem o dau moi lan chay (bug.md #103) va tu tat canh
gac trong `finally`. Module nay KHONG duoc tu lam lai viec do - lam hai lan la
che mat neu mot ngay nao do `main()` thoi lam.

Module nay TUYET DOI khong import tkinter.
"""
from __future__ import annotations

import threading
import time


# Cac trang thai cua mot muc. Dung hang so chu khong go chuoi truc tiep: go
# nham mot chu la muc do bien mat khoi moi bo loc, im lang.
CHO = "cho"          # chua den luot
DANG_CHAY = "dang_chay"
XONG = "xong"
LOI = "loi"
HUY = "huy"          # nguoi dung dung hang doi truoc khi den luot / giua chung

# Trang thai KET THUC - khong chay lai tru khi nguoi dung yeu cau
KET_THUC = (XONG, LOI, HUY)


class Muc:
    """Mot project trong hang doi."""

    def __init__(self, draft, out, tuy_chon=None, ten=None):
        self.draft = str(draft)
        self.out = str(out)
        self.tuy_chon = dict(tuy_chon or {})
        self.ten = ten or self._ten_tu_duong_dan(self.draft)
        self.trang_thai = CHO
        self.thong_bao = ""      # mo ta ngan cho nguoi dung doc
        self.nhat_ky = []        # cac dong log cua RIENG muc nay
        self.bat_dau = None      # time.monotonic()
        self.ket_thuc = None

    @staticmethod
    def _ten_tu_duong_dan(d):
        # Khong dung Path().name: duong dan co the ket thuc bang dau gach,
        # luc do `.name` tra chuoi rong va nguoi dung thay mot dong trong.
        d = str(d).rstrip("\\/")
        for dau in ("\\", "/"):
            if dau in d:
                d = d.rsplit(dau, 1)[-1]
        return d or "(khong ten)"

    @property
    def giay(self):
        """So giay da chay. None neu chua bat dau."""
        if self.bat_dau is None:
            return None
        return (self.ket_thuc or time.monotonic()) - self.bat_dau

    def __repr__(self):
        return f"Muc({self.ten!r}, {self.trang_thai})"


class HangDoi:
    """Chay lan luot nhieu project.

    `chay_mot(muc, nen_dung)` la ham do NGUOI GOI truyen vao. No phai:
      - goi `goi_project_capcut.main()` DUNG MOT LAN cho muc do
      - nem exception neu that bai
      - tra ve khi xong
    Tach nhu vay de kiem chung duoc `HangDoi` ma khong can chay gom that.
    """

    def __init__(self, chay_mot, bao=None):
        self.chay_mot = chay_mot
        self.bao = bao or (lambda *a, **k: None)
        self.muc = []
        self.dang_chay = False
        self._co_huy = threading.Event()
        self._muc_hien_tai = None

    # ------------------------------------------------------------ quan ly muc
    def them(self, muc):
        """Them mot muc. Tra ve chinh no de tien noi chuoi."""
        self.muc.append(muc)
        self.bao("them", muc)
        return muc

    def bo(self, muc):
        """Bo mot muc khoi hang doi.

        KHONG bo duoc muc DANG CHAY: bo no thi tien trinh gom van chay tiep ma
        khong ai theo doi nua, va thu muc dich nam do dang khong ai biet.
        """
        if muc.trang_thai == DANG_CHAY:
            return False
        if muc in self.muc:
            self.muc.remove(muc)
            self.bao("bo", muc)
            return True
        return False

    def cho_chay(self):
        """Cac muc con phai chay."""
        return [m for m in self.muc if m.trang_thai not in KET_THUC]

    def theo_trang_thai(self, tt):
        return [m for m in self.muc if m.trang_thai == tt]

    # ------------------------------------------------------------- dieu khien
    def huy(self):
        """Yeu cau dung. Muc DANG CHAY tu quyet dinh dung the nao qua
        `nen_dung`; cac muc CHO se thanh HUY."""
        self._co_huy.set()
        self.bao("huy_yeu_cau", None)

    @property
    def bi_huy(self):
        return self._co_huy.is_set()

    def chay(self):
        """Chay het hang doi. Goi ham nay o THREAD PHU.

        Mot muc LOI KHONG chan cac muc con lai - day la ly do chinh de co hang
        doi: gom ca loat qua dem, sang ra xem cai nao hong thi lam lai cai do.
        """
        if self.dang_chay:
            return
        self.dang_chay = True
        self._co_huy.clear()
        try:
            for m in self.muc:
                if m.trang_thai in KET_THUC:
                    continue          # da chay roi, khong chay lai
                if self._co_huy.is_set():
                    m.trang_thai = HUY
                    m.thong_bao = "Da huy truoc khi den luot."
                    self.bao("doi", m)
                    continue
                self._chay_mot_muc(m)
        finally:
            self.dang_chay = False
            self._muc_hien_tai = None
            self.bao("het", None)

    def _chay_mot_muc(self, m):
        self._muc_hien_tai = m
        m.trang_thai = DANG_CHAY
        m.bat_dau = time.monotonic()
        m.ket_thuc = None
        m.thong_bao = "Dang chay..."
        self.bao("doi", m)
        try:
            self.chay_mot(m, self._co_huy.is_set)
            # Nguoi dung bam dung GIUA CHUNG: khong duoc bao "Xong." - do la
            # bao cao sai ket qua, va khong phan biet duoc voi mot lan chay
            # thanh cong. Cung bay da ghi o SPEC muc 5.2.
            if self._co_huy.is_set():
                m.trang_thai = HUY
                m.thong_bao = "Da dung giua chung."
            else:
                m.trang_thai = XONG
                m.thong_bao = "Xong."
        except BaseException as ex:
            # Bat BaseException chu khong Exception: `KeyboardInterrupt` va
            # `SystemExit` tu mot pha con cung phai duoc ghi nhan la LOI cua
            # muc nay, khong duoc lam chet ca hang doi im lang.
            m.trang_thai = LOI
            m.thong_bao = f"{type(ex).__name__}: {ex}"
            m.nhat_ky.append(f"! LOI: {m.thong_bao}")
            self.bao("loi", m)
        finally:
            m.ket_thuc = time.monotonic()
            self.bao("doi", m)

    # ------------------------------------------------------------- tong ket
    def tong_ket(self):
        """Dem theo trang thai. Do tren KET QUA THUC TE cua tung muc, khong
        tren mot bo dem rieng - bo dem rieng se lech khi co ai do doi trang
        thai mot muc ma quen cong tru."""
        d = {CHO: 0, DANG_CHAY: 0, XONG: 0, LOI: 0, HUY: 0}
        for m in self.muc:
            d[m.trang_thai] = d.get(m.trang_thai, 0) + 1
        return d

    def mo_ta_tong_ket(self):
        d = self.tong_ket()
        phan = [f"{d[XONG]}/{len(self.muc)} xong"]
        if d[LOI]:
            phan.append(f"{d[LOI]} loi")
        if d[HUY]:
            phan.append(f"{d[HUY]} huy")
        if d[CHO]:
            phan.append(f"{d[CHO]} cho")
        return ", ".join(phan)
