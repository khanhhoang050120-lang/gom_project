#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CANH GAC - phat hien tool bi TREO VINH VIEN tren o mang (bug.md #25 muc c).

VAN DE
======
Python KHONG co timeout cho I/O filesystem. Mot loi goi `os.*` toi o mang co
the KHONG BAO GIO tra ve khi phien SMB rot hoac server qua tai. Tool van "song"
(tien trinh con do), nhin qua tuong dang chay - da mat 2 tieng nhu vay mot lan.

VI SAO KHO: BA TIN HIEU "HIEN NHIEN" DEU SAI
============================================
Muc #25 da bao dong gia HAI lan, va do dac lai lan nay xac nhan ca ba deu sai:

  1. "Log khong doi > 15 phut"  -> SAI. Log chi in moi 25 clip; gap cum file lon
     thi im lang 20+ phut la BINH THUONG.
  2. "Thay 0 tien trinh ffmpeg" -> SAI. Do duoc: mot phien KHOE MANH co 19 cua
     so "0 ffmpeg" trong 7,35 giay, va ca mot pha hop le (resolve/copy/tu kiem)
     khong co ffmpeg nao suot 51,6 giay.
  3. "Tien trinh CHA khong doc/ghi gi" -> SAI, va day la bao dam cua Windows
     chu khong phai trung hop: bo dem I/O la cua RIENG tung tien trinh, khong
     cong don tu con len cha. Do duoc: trong 41,9 giay giua pha ma hoa, cha chi
     tieu 0,344 s CPU trong khi CA CAY tieu 406,4 s - chenh 1180 lan.

VA MOT CAI BAY THU TU, NANG NHAT
================================
Nhip dap cua CHINH TOOL lam mu canh gac. Thread nhip dap khong bi treo khi
thread chinh chet cung, va moi 60 giay no ghi `_opt_index.json` ra DICH. Moi
dong ghi lam `WriteTransferCount` tang -> luat "moi bo dem dung yen = treo" se
KHONG BAO GIO kich hoat tren tool that. Do duoc: luc treo, bo dem GHI van tang
49 byte/giay.
  -> Vi vay quyet dinh dua tren NGUONG KHOI LUONG trong moi cua so, KHONG phai
     "co thay doi hay khong".

TIN HIEU DUNG (do tren 5 phien ma hoa that + 2 lan chay che do 4)
=================================================================
Hop cua BA nhom, tren CA CAY tien trinh:
  - byte : Read + Write + Other TransferCount
  - thao tac: Read + Write + Other OperationCount
  - CPU  : kernel + user
Phai co DU ca ba, vi moi nhom deu co pha khoe manh lam no dung yen:
  - Pha quet metadata tren NAS: byte read/write dung yen 93% thoi luong pha
    (os.stat qua SMB gan nhu khong chuyen byte, chi tang Other*).
  - Pha copy ket qua len NAS: CPU dung yen 6,7 giay (chuyen byte ao at nhung
    gan nhu khong ton CPU).
  - Khoang im lang dai nhat khi MOI chi so cung dung yen, o phien khoe manh:
    0,2 giay. Lay mau 5 giay thi khong bao gio bat gap.

NGUONG (60 giay mot cua so quan sat)
====================================
Coi la DANG CHAY neu BAT KY dieu nao dung:
    (read + other) >= 64 KB   |   write >= 1 MB
    (rop + wop + oop) >= 200  |   CPU >= 1,0 giay
Kiem chung bang so do:
    pha metadata NAS / 60 s -> other 3,1 MB, oop 98.600, cpu 6 s   -> DAT
    pha ma hoa      / 60 s -> read 474 MB                          -> DAT
    treo-co-nhip-dap/ 60 s -> read 0, other 0, ops 12, cpu 0,
                              write 2,9 KB -> DUOI MOI NGUONG      -> BAT DUNG

CANH GAC KHONG TU GIET TIEN TRINH
=================================
Muc #25 ghi ro "van can nguoi van hanh quyet dinh", va do duoc cai gia that:
dung o pha MA LAI thi khong mat cong (cache `_opt_index` dung lai duoc), nhung
dung o pha COPY thi phai copy lai TU DAU. Giet nham mot job 3 tieng de tranh
mot canh bao co the la gia la lo hon nhieu. Canh gac chi NOI, nguoi dung quyet.

QUY TAC SONG CON CUA CHINH CANH GAC
===================================
Than canh gac TUYET DOI khong duoc goi bat ky ham filesystem nao. Neu no cham
vao dia/o mang thi dung luc can no nhat, no ket theo. Chi duoc dung ctypes
(kernel32 - tra cuu bang trong nhan, khong cham thiet bi) va doc bien trong bo
nho.
"""
from __future__ import annotations

import ctypes
import sys
import threading
import time
from ctypes import wintypes

# --------------------------------------------------------------- cau hinh
CHU_KY_GIAY = 30.0          # bao lau lay mau mot lan
CUA_SO_GIAY = 60.0          # do khoi luong trong cua so nay
CANH_BAO_PHUT = 5.0         # im lang bao lau thi CANH BAO
NGHI_TREO_PHUT = 15.0       # im lang bao lau thi ket luan NGHI TREO

# Nguong "coi nhu dang chay" trong MOT cua so 60 giay (xem docstring)
NG_BYTE_DOC = 64 * 1024
NG_BYTE_GHI = 1024 * 1024
NG_THAO_TAC = 200
NG_CPU_GIAY = 1.0

_LA_WINDOWS = (sys.platform == "win32")


# --------------------------------------------------------------- ctypes
class _IO_COUNTERS(ctypes.Structure):
    _fields_ = [("ReadOperationCount", ctypes.c_ulonglong),
                ("WriteOperationCount", ctypes.c_ulonglong),
                ("OtherOperationCount", ctypes.c_ulonglong),
                ("ReadTransferCount", ctypes.c_ulonglong),
                ("WriteTransferCount", ctypes.c_ulonglong),
                ("OtherTransferCount", ctypes.c_ulonglong)]


class _JOB_BASIC_ACCT(ctypes.Structure):
    _fields_ = [("TotalUserTime", ctypes.c_longlong),
                ("TotalKernelTime", ctypes.c_longlong),
                ("ThisPeriodTotalUserTime", ctypes.c_longlong),
                ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
                ("TotalPageFaultCount", wintypes.DWORD),
                ("TotalProcesses", wintypes.DWORD),
                ("ActiveProcesses", wintypes.DWORD),
                ("TotalTerminatedProcesses", wintypes.DWORD)]


class _JOB_ACCT_IO(ctypes.Structure):
    _fields_ = [("BasicInfo", _JOB_BASIC_ACCT), ("IoInfo", _IO_COUNTERS)]


class _PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", ctypes.c_wchar * 260)]


_JOB_ACCT_IO_CLASS = 8              # JobObjectBasicAndIoAccountingInformation
_SNAP_PROCESS = 0x00000002
_QUERY_LIMITED = 0x1000             # PROCESS_QUERY_LIMITED_INFORMATION
_INVALID = ctypes.c_void_p(-1).value


def _k32():
    """Nap kernel32 VA khai bao argtypes/restype cho moi ham ta dung.

    KHAI BAO ARGTYPES LA BAT BUOC, khong phai cho dep: `GetCurrentProcess()`
    tra ve pseudo-handle -1. Khong khai bao thi ctypes coi tri tra ve la
    `c_int` roi khi truyen sang ham khac lai nem `OverflowError: int too long
    to convert`. Da vap dung loi nay: `AssignProcessToJobObject` "that bai" va
    chuong trinh am tham roi ve cach do kem hon - trong khi Job Object hoan
    toan dung duoc. Loi bi `except Exception` nuot nen chan doan sai luon.
    """
    if not _LA_WINDOWS:
        return None
    try:
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.GetCurrentProcess.restype = wintypes.HANDLE
        k.GetCurrentProcess.argtypes = []
        k.GetCurrentProcessId.restype = wintypes.DWORD
        k.GetCurrentProcessId.argtypes = []
        k.CreateJobObjectW.restype = wintypes.HANDLE
        k.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        k.AssignProcessToJobObject.restype = wintypes.BOOL
        k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        k.QueryInformationJobObject.restype = wintypes.BOOL
        k.QueryInformationJobObject.argtypes = [
            wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
            ctypes.c_void_p]
        k.CloseHandle.restype = wintypes.BOOL
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        k.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        k.Process32FirstW.restype = wintypes.BOOL
        k.Process32NextW.restype = wintypes.BOOL
        k.OpenProcess.restype = wintypes.HANDLE
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.GetProcessIoCounters.restype = wintypes.BOOL
        k.GetProcessIoCounters.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
        k.GetProcessTimes.restype = wintypes.BOOL
        k.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.c_void_p] * 4
        return k
    except Exception:
        return None


class _DoBangJob:
    """Do bang Job Object - CACH TOT NHAT.

    Vi sao hon han lay mau cay: ffmpeg cua tool la tien trinh NGAN, moi clip
    mot cai. Lay mau dinh ky chi thay nhung cai tinh co con song dung luc chup;
    nhung cai sinh-ra-roi-chet giua hai lan lay mau KHONG BAO GIO duoc dem, va
    phan lon luong ghi cua ffmpeg lai don vao luc dong file (ngay truoc khi
    thoat). Do duoc: lay mau cay bo sot 74-96% I/O cua ffmpeg. Job Object cong
    don ca tien trinh DA CHET nen dem dung 100% va DON DIEU tuyet doi.
    """

    def __init__(self, k):
        self.k = k
        self.job = None
        self.vi_sao = ""      # vi sao that bai - KHONG duoc nuot im lang

    def bat_dau(self) -> bool:
        k = self.k
        if not k:
            self.vi_sao = "khong nap duoc kernel32"
            return False
        try:
            job = k.CreateJobObjectW(None, None)
            if not job:
                self.vi_sao = (f"CreateJobObjectW that bai"
                               f" (err {ctypes.get_last_error()})")
                return False
            ctypes.set_last_error(0)
            if not k.AssignProcessToJobObject(job, k.GetCurrentProcess()):
                # Hay gap khi tien trinh DA nam trong mot job khong cho long
                # nhau. Khong phai loi cua ta - nhung phai NOI RA, khong duoc
                # am tham roi ve cach do kem hon.
                self.vi_sao = (f"AssignProcessToJobObject that bai"
                               f" (err {ctypes.get_last_error()};"
                               f" thuong la da o trong mot job khac)")
                k.CloseHandle(job)
                return False
            self.job = job
            return True
        except Exception as ex:
            self.vi_sao = f"{type(ex).__name__}: {ex}"
            return False

    def doc(self):
        if not self.job:
            return None
        d = _JOB_ACCT_IO()
        try:
            ok = self.k.QueryInformationJobObject(
                self.job, _JOB_ACCT_IO_CLASS, ctypes.byref(d),
                ctypes.sizeof(d), None)
        except Exception:
            return None
        if not ok:
            return None
        io = d.IoInfo
        # Thoi gian trong Job la don vi 100 nano giay
        cpu = (d.BasicInfo.TotalUserTime + d.BasicInfo.TotalKernelTime) / 1e7
        return {
            "byte_doc": io.ReadTransferCount + io.OtherTransferCount,
            "byte_ghi": io.WriteTransferCount,
            "thao_tac": (io.ReadOperationCount + io.WriteOperationCount
                         + io.OtherOperationCount),
            "cpu": cpu,
            "so_tien_trinh": d.BasicInfo.ActiveProcesses,
        }


class _DoBangCay:
    """Du phong khi khong tao duoc Job Object.

    Kem hon Job Object (bo sot tien trinh chet giua hai lan lay mau) NHUNG van
    du de PHAT HIEN treo: cai ta can khong phai tong chinh xac, ma la phan biet
    "co gi do dang xay ra" voi "khong gi ca". Ke ca chi bat duoc 7% luong byte
    thi 7% cua 474 MB van vuot xa nguong 64 KB.

    Cai BAT BUOC phai lam dung: nho bo dem CUOI CUNG doc duoc cua moi PID va
    GIU LAI sau khi PID do chet. Neu chi cong cac tien trinh DANG SONG thi tong
    se TUT khi mot ffmpeg thoat -> delta am -> ket luan "khong tien trien" ngay
    giua luc chay ngon lanh. Do duoc: 16% khoang do co delta am o phien hoan
    toan khoe manh. Day dung la loai sai lam #25 da mac hai lan.
    """

    def __init__(self, k, pid):
        self.k = k
        self.pid = pid
        self.vi_sao = ""
        self.cuoi = {}          # pid -> (byte_doc, byte_ghi, thao_tac, cpu)

    def bat_dau(self) -> bool:
        if not self.k:
            self.vi_sao = "khong nap duoc kernel32"
            return False
        return True

    def _con_chau(self):
        k = self.k
        snap = k.CreateToolhelp32Snapshot(_SNAP_PROCESS, 0)
        if snap == _INVALID or not snap:
            return []
        try:
            e = _PROCESSENTRY32W()
            e.dwSize = ctypes.sizeof(e)
            cha = {}
            if not k.Process32FirstW(snap, ctypes.byref(e)):
                return [self.pid]
            while True:
                cha.setdefault(e.th32ParentProcessID, []).append(e.th32ProcessID)
                if not k.Process32NextW(snap, ctypes.byref(e)):
                    break
        finally:
            k.CloseHandle(snap)
        ra, hang = [self.pid], [self.pid]
        while hang:
            p = hang.pop()
            for c in cha.get(p, ()):
                if c not in ra:
                    ra.append(c)
                    hang.append(c)
        return ra

    def doc(self):
        k = self.k
        try:
            ds = self._con_chau()
        except Exception:
            return None
        song = 0
        for pid in ds:
            h = k.OpenProcess(_QUERY_LIMITED, False, pid)
            if not h:
                continue            # vua chet, hoac khong du quyen -> bo qua
            try:
                io = _IO_COUNTERS()
                if not k.GetProcessIoCounters(h, ctypes.byref(io)):
                    continue
                a = wintypes.FILETIME()
                b = wintypes.FILETIME()
                c = wintypes.FILETIME()
                d = wintypes.FILETIME()
                if not k.GetProcessTimes(h, ctypes.byref(a), ctypes.byref(b),
                                         ctypes.byref(c), ctypes.byref(d)):
                    continue

                def _ns(f):
                    return ((f.dwHighDateTime << 32) | f.dwLowDateTime) / 1e7

                self.cuoi[pid] = (
                    io.ReadTransferCount + io.OtherTransferCount,
                    io.WriteTransferCount,
                    (io.ReadOperationCount + io.WriteOperationCount
                     + io.OtherOperationCount),
                    _ns(c) + _ns(d),
                )
                song += 1
            finally:
                k.CloseHandle(h)
        if not self.cuoi:
            return None
        # Cong TOAN BO dict (song + da chet) -> don dieu, khong bao gio tut
        t = [0, 0, 0, 0.0]
        for v in self.cuoi.values():
            for i in range(4):
                t[i] += v[i]
        return {"byte_doc": t[0], "byte_ghi": t[1], "thao_tac": t[2],
                "cpu": t[3], "so_tien_trinh": song}


class CanhGac:
    """Thread daemon rieng, doc lap voi nhip dap.

    PHAI la thread RIENG: thread nhip dap cua `optimize_package()` khong chi in
    log - moi 60 giay no ghi `_opt_index.json` NGAY TREN DICH (thuong la NAS).
    Neu canh gac nam trong thread do thi dung luc NAS ket, canh gac ket theo.
    `try/except` bao quanh chi bat duoc khi loi goi TRA VE; mot loi goi khong
    bao gio tra ve thi khong co gi de bat.
    """

    def __init__(self, log=print, chu_ky=CHU_KY_GIAY, cua_so=CUA_SO_GIAY,
                 canh_bao_phut=CANH_BAO_PHUT, nghi_treo_phut=NGHI_TREO_PHUT,
                 dong_ho=time.monotonic):
        self.log = log
        self.chu_ky = chu_ky
        self.cua_so = cua_so
        self.canh_bao_giay = canh_bao_phut * 60.0
        self.nghi_treo_giay = nghi_treo_phut * 60.0
        self.dong_ho = dong_ho          # thay duoc de bo kiem khoi cho 15 phut
        self.pha = {"ten": "(chua bat dau)", "luc": dong_ho()}
        self.tat = threading.Event()
        self.luong = None
        self.do = None
        self.lich_su = []               # [(luc, mau)]
        self.da_bao = 0                 # 0 chua, 1 da canh bao, 2 da nghi treo
        self.so_lan_bao = 0
        self.cach = ""                  # "job" hay "cay" - de bao cao/kiem

    # ------------------------------------------------------------ dieu khien
    def dat_pha(self, ten):
        """`main()` goi moi khi sang pha moi. Chi de NOI dang ket o dau -
        khong tham gia vao quyet dinh song/chet."""
        self.pha = {"ten": ten, "luc": self.dong_ho()}

    def bat_dau(self):
        if not _LA_WINDOWS:
            return False
        k = _k32()
        if not k:
            return False
        d = _DoBangJob(k)
        self.cach = "job"
        if not d.bat_dau():
            # NOI RA vi sao, khong am tham xuong cach kem hon: do duoc la cach
            # do cay bo sot 74-96% I/O cua ffmpeg (tien trinh ngan sinh-va-chet
            # giua hai lan lay mau khong bao gio duoc dem).
            self.log(f"  [canh gac] khong dung duoc Job Object ({d.vi_sao})"
                     f" -> chuyen sang do cay tien trinh (kem chinh xac hon).")
            d = _DoBangCay(k, k.GetCurrentProcessId())
            self.cach = "cay"
            if not d.bat_dau():
                self.log(f"  [canh gac] KHONG BAT DUOC: {d.vi_sao}."
                         f" Se khong co canh bao treo o lan chay nay.")
                return False
        self.do = d
        m = d.doc()
        if m is None:
            self.do = None
            return False
        self.lich_su = [(self.dong_ho(), m)]
        self.luong = threading.Thread(target=self._vong, daemon=True,
                                      name="canh_gac")
        self.luong.start()
        return True

    def dung(self):
        self.tat.set()

    # ------------------------------------------------------------ than
    def _vong(self):
        while not self.tat.wait(self.chu_ky):
            try:
                self._mot_nhip()
            except Exception:
                # Canh gac hong KHONG duoc lam hong lan chay. Nhung cung khong
                # duoc im: mot canh gac chet cam la mot canh gac noi doi.
                self.tat.set()
                try:
                    self.log("  [canh gac] tu tat vi loi noi bo -"
                             " se KHONG con canh bao treo o lan chay nay.")
                except Exception:
                    pass
                return

    def _mot_nhip(self):
        m = self.do.doc()
        if m is None:
            return
        bay_gio = self.dong_ho()
        self.lich_su.append((bay_gio, m))
        # Chi giu du de phu cua so dai nhat ta can hoi
        gioi = bay_gio - (self.nghi_treo_giay + self.cua_so + self.chu_ky * 2)
        self.lich_su = [x for x in self.lich_su if x[0] >= gioi] or self.lich_su[-1:]

        im = self._im_lang_bao_lau(bay_gio)
        if im is None:
            return
        if im >= self.nghi_treo_giay and self.da_bao < 2:
            self.da_bao = 2
            self.so_lan_bao += 1
            self._noi(im, m, nghi_treo=True)
        elif im >= self.canh_bao_giay and self.da_bao < 1:
            self.da_bao = 1
            self.so_lan_bao += 1
            self._noi(im, m, nghi_treo=False)
        elif im < self.canh_bao_giay and self.da_bao:
            # Da chay lai -> bao ro va cho phep canh bao lan sau
            self.da_bao = 0
            self.log("  [canh gac] da co tien trien tro lai - bo canh bao truoc do.")

    def _im_lang_bao_lau(self, bay_gio):
        """Bao lau roi KHONG co cua so `cua_so` giay nao dat nguong 'dang chay'.

        Tra None neu chua du du lieu.
        """
        moc = None      # thoi diem GAN NHAT con thay 'dang chay'
        for i, (t, m) in enumerate(self.lich_su):
            # tim mau cach mau nay >= cua_so giay ve truoc
            j = None
            for k2 in range(i - 1, -1, -1):
                if t - self.lich_su[k2][0] >= self.cua_so:
                    j = k2
                    break
            if j is None:
                continue
            if self._dat_nguong(self.lich_su[j][1], m):
                moc = t
        if moc is None:
            # Chua co cua so nao dat nguong. Tinh tu mau dau tien ta co.
            if bay_gio - self.lich_su[0][0] < self.cua_so:
                return None
            moc = self.lich_su[0][0]
        return bay_gio - moc

    @staticmethod
    def _dat_nguong(truoc, sau):
        """Co BAT KY dau hieu lam viec nao trong cua so nay khong?

        Phai la NGUONG KHOI LUONG chu khong phai 'co thay doi': nhip dap cua
        chinh tool ghi ~49 byte/giay ra dich ngay ca khi da treo, nen luat 'co
        thay doi = con song' khong bao gio kich hoat.
        """
        return (sau["byte_doc"] - truoc["byte_doc"] >= NG_BYTE_DOC
                or sau["byte_ghi"] - truoc["byte_ghi"] >= NG_BYTE_GHI
                or sau["thao_tac"] - truoc["thao_tac"] >= NG_THAO_TAC
                or sau["cpu"] - truoc["cpu"] >= NG_CPU_GIAY)

    # ------------------------------------------------------------ noi
    def _noi(self, im_giay, m, nghi_treo):
        p = self.pha["ten"]
        phut = im_giay / 60.0
        tieu = ("NGHI TOOL DA TREO" if nghi_treo
                else "CANH BAO: khong thay tien trien")
        self.log("")
        self.log("  " + "=" * 62)
        self.log(f"  [canh gac] {tieu}")
        self.log("  " + "=" * 62)
        self.log(f"    Da {phut:.0f} phut khong thay dau hieu lam viec nao.")
        self.log(f"    Dang o buoc: {p}")
        self.log(f"    Do duoc trong cua so {self.cua_so:.0f} giay gan nhat:")
        self.log(f"      doc {m['byte_doc']/2**20:.1f} MB tich luy |"
                 f" ghi {m['byte_ghi']/2**20:.1f} MB tich luy")
        self.log(f"      {m['thao_tac']} thao tac tich luy |"
                 f" CPU {m['cpu']:.1f} giay | {m['so_tien_trinh']} tien trinh")
        if not nghi_treo:
            self.log("    Neu dang copy mot file RAT LON qua mang thi day co the")
            self.log("    la BINH THUONG - cu doi them.")
        else:
            self.log("    Nguyen nhan hay gap: o mang rot phien (SMB treo vo han).")
            self.log("    Python khong co timeout cho I/O nen tool se cho MAI MAI.")
            self.log("")
            self.log("    BAN QUYET DINH - tool KHONG tu dong dung:")
            self.log("      * Doi tiep: neu ban tin la NAS chi dang rat cham.")
            self.log("      * Dung han: dong cua so / dong console.")
            if "ma lai" in p.lower() or "toi uu" in p.lower():
                self.log("        Dung o buoc nay MAT IT: cac clip da ma xong")
                self.log("        duoc ghi nho, lan sau chay lai dung lai duoc.")
            elif "copy" in p.lower() or "gom" in p.lower():
                self.log("        Dung o buoc nay MAT NHIEU: vong copy chua biet")
                self.log("        bo qua file da co, nen lan sau phai copy TU DAU.")
                self.log("        Hay can nhac doi them truoc khi dung.")
        self.log("  " + "=" * 62)
        self.log("")
