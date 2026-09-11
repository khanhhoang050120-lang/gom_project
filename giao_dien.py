# -*- coding: utf-8 -*-
"""GIAO DIEN cho GOI PROJECT CAPCUT.

NGUYEN TAC THIET KE QUAN TRONG NHAT: giao dien nay KHONG viet lai logic nao.
No LAI chinh `goi_project_capcut.main()` - ham da chay that tren 10 project va
duoc 25 bo kiem bao ve - bang cach:
  - thay `builtins.input` bang mot ham tra loi theo NOI DUNG cau hoi (lay tu form)
  - huong `sys.stdout` vao o Nhat ky
Nho vay giao dien va dong lenh KHONG THE lech hanh vi: chung la MOT.

Ba diem ky thuat de sai, da xu ly:
  1. tkinter KHONG an toan da luong -> `main()` chay o thread rieng, moi cap nhat
     giao dien di qua `queue` + `after()` tren thread chinh.
  2. `contextlib.redirect_stdout` KHONG theo thread (da ghi trong bug.md) -> thay
     `sys.stdout` mot lan cho ca phien chay, va tra lai trong `finally`.
  3. Cau hoi "Tien hanh? (y/N)" phai DUNG cho nguoi dung bam nut -> dung
     `threading.Event`, khong dung vong lap ban.
"""
from __future__ import annotations

import builtins
import os
import queue
import sys
import threading
import traceback
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

_GOC = Path(__file__).resolve().parent
if str(_GOC) not in sys.path:
    sys.path.insert(0, str(_GOC))

# `_GOC` o tren dung de nap module (phai la thu muc chua file .py nay).
# NHUNG ba viec duoi day can BA thu muc KHAC nhau khi dong goi .exe:
#   _TAI_NGUYEN - doc file di kem (ffmpeg, cac .py)  -> co the la thu muc tam
#   _CHUONG_TRINH - thu muc chua .exe                 -> de so voi folder XUAT RA
#   _GHI        - noi ghi log/dau kiem                -> co the la %LOCALAPPDATA%
# Dung nham la hong im lang: log bay mat, hoac chan oan folder xuat ra.
try:
    from loi import phien_ban as _PB
    _TAI_NGUYEN = _PB.thu_muc_tai_nguyen()
    _CHUONG_TRINH = _PB.thu_muc_chuong_trinh()
except ImportError:
    _PB = None
    _TAI_NGUYEN = _CHUONG_TRINH = _GOC

# EP UTF-8 truoc khi thay `sys.stdout` o duoi: may con ACP 1258 khong in duoc
# chu co dau (bug.md #68, #105).
try:
    from loi.bang_ma import ep_utf8 as _ep_utf8
    _ep_utf8()
except Exception:
    pass


def _thu_muc_ghi():
    """Goi LUC CAN chu khong tinh san: phep thu ghi cham mot chut, va o giai
    doan nap module co the chua co quyen gi ca."""
    return _PB.thu_muc_ghi() if _PB else _GOC


class _KhongDau:
    """stdout gia. Duoi `pythonw.exe` KHONG co console nen `sys.stdout` co the
    la None; luc do moi `print()` se nem AttributeError o cho khong ngo toi.
    Gan cai nay vao de chuong trinh khong chet vi mot dong print vo hai."""

    def write(self, s):
        # Duoi pythonw KHONG co console: neu chi nuot di thi moi traceback bay hoi
        # va nguoi dung bam dup xong khong thay gi. Ghi ra file de con dau vet.
        try:
            if s and s.strip():
                with open(_thu_muc_ghi() / "_LOI_GIAO_DIEN.log", "a",
                          encoding="utf-8", errors="replace") as f:
                    f.write(s)
        except Exception:
            pass
        return len(s)

    def flush(self):
        pass

    def isatty(self):
        return False


if sys.stdout is None:
    sys.stdout = _KhongDau()
if sys.stderr is None:
    sys.stderr = _KhongDau()

import goi_project_capcut as G   # noqa: E402
import tu_kiem_lan_dau as TK     # noqa: E402
from chung import (fixed_drives, isdir_safe, isfile_safe,   # noqa: E402
                   mtime_an_toan, tuyet_doi_that)
# CAU NOI giua giao dien va loi - xem ui/cau_noi.py va SPEC_UI_UX.md muc 1.
# Tach ra module rieng vi day la phan de sai nhat cua UI, va la phan DUY NHAT
# kiem thu duoc ma khong can tkinter.
from ui.cau_noi import Ong, TraLoi   # noqa: E402
from ui import kiem_dau_vao as KDV   # noqa: E402


class GiaoDien:
    def __init__(self, root):
        self.root = root
        root.title("Gói Project CapCut")
        # Laptop 1366x768 chi con ~728 px vung lam viec; 775 + vien lam mat
        # 3-4 dong CUOI cua Nhat ky - dung nhung dong moi nhat (cau hoi xac
        # nhan va duong dan dich). Co lai theo man hinh that.
        cao = min(775, max(560, root.winfo_screenheight() - 120))
        root.geometry(f"895x{cao}")
        root.minsize(760, 560)

        self.hd = queue.Queue()
        self.luong = None
        self.cho_tien_hanh = threading.Event()
        # `threading.Event` chu khong phai `bool` tran: `is_set` la bound method
        # cua mot doi tuong C, doc tu thread phu an toan, ton 41-48 ns/lan va
        # KHONG BAO GIO nem - dung yeu cau cua `nen_dung`.
        # TUYET DOI khong truyen lambda doc bien tkinter (`self.v_x.get()`) lam
        # `nen_dung`: goi tu thread phu se nem "main thread is not in main loop".
        self.co_huy = threading.Event()
        # Event RIENG cho pha quet thu muc me. TUYET DOI khong dung lai
        # `co_huy`: `_bat_dau()` co `co_huy.clear()`, nen kich ban thuong ngay
        # (bam "Quet thu muc me...", thay lau qua nen bam "Dung do", roi bam
        # "1) QUET" de goi project khac) se XOA dung cai co ma thread quet dang
        # doc -> no HOI SINH, quet tiep den het cay roi de len danh sach moi.
        self.co_huy_quet = threading.Event()
        self.dang_quet = False
        self.phien_quet = 0       # so phien: ket qua phien cu ve muon phai bo
        self.tra_loi_tien_hanh = None
        self.dang_chay = False
        self.drafts = []
        self._menus = []          # giu menu chuot phai khoi bi thu gom rac
        self._nhip = None         # id cua `after` nhip dap - phai huy khi dong
        self._lap = {}            # dem cau hoi lap lai -> chan vong lap vo han
        self._bo_tra_loi = None   # `ui.cau_noi.TraLoi`, dung khi bat dau chay
        self._cs_hd = None        # cua so hang doi (Toplevel), mo khi can

        # Duoi pythonw moi loi trong callback deu IM LANG (stderr la ho den).
        # Khong co luoi nay thi "nut bam khong lam gi ca" - dung trieu chung
        # ma ta dang chua.
        def _loi_callback(exc, val, tb):
            ct = "".join(traceback.format_exception(exc, val, tb))
            try:
                self._ghi("! LỖI GIAO DIỆN:")
                for d in ct.splitlines():
                    self._ghi("   " + d)
            except Exception:
                pass
            try:
                messagebox.showerror("Lỗi giao diện", ct[-1500:], parent=self.root)
            except Exception:
                pass
        root.report_callback_exception = _loi_callback

        self._dung_giao_dien()
        self._nap_danh_sach_mac_dinh()
        self._nhip = self.root.after(80, self._rut_hang_doi)
        root.protocol("WM_DELETE_WINDOW", self._dong)
        # `WM_DELETE_WINDOW` CHI chay khi nguoi dung bam nut X. Cua so con bi
        # huy bang `root.destroy()` truc tiep (bo kiem, hoac luoi bao loi) -
        # luc do nhip dap van con mot `after` dang cho tro toi mot lenh sap
        # bien mat, va Tcl in `invalid command name "..._rut_hang_doi"` ra
        # stderr. Duoi pythonw dong rac do di thang vao `_LOI_GIAO_DIEN.log`,
        # lam nguoi dung tuong co loi that. Bat <Destroy> thi huy duoc du cua
        # so bi dong bang duong nao.
        root.bind("<Destroy>", self._huy_nhip, add="+")

    # ------------------------------------------------------------------ dung
    def _dung_giao_dien(self):
        ngoai = ttk.Frame(self.root, padding=8)
        ngoai.pack(fill="both", expand=True)

        # --- 1) Chon project ---
        k1 = ttk.LabelFrame(ngoai, text="1) Chọn project (thư mục draft CapCut)",
                            padding=6)
        k1.pack(fill="x")
        hop = ttk.Frame(k1)
        hop.pack(fill="both")
        self.ds = tk.Listbox(hop, height=6, exportselection=False)
        self.ds.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(hop, orient="vertical", command=self.ds.yview)
        sb.pack(side="right", fill="y")
        self.ds.config(yscrollcommand=sb.set)
        self.ds.bind("<<ListboxSelect>>", self._chon_tu_danh_sach)

        hang = ttk.Frame(k1)
        hang.pack(fill="x", pady=(6, 0))
        ttk.Button(hang, text="Quét thư mục mẹ...",
                   command=self._quet_thu_muc_me).pack(side="left")
        ttk.Button(hang, text="Làm mới danh sách mặc định",
                   command=self._nap_danh_sach_mac_dinh).pack(side="left", padx=6)

        ttk.Label(k1, text="Hoặc DÁN thẳng đường dẫn thư mục draft vào ô dưới"
                          " (Ctrl+V hoặc chuột phải), hoặc bấm Chọn...:").pack(
            anchor="w", pady=(8, 2))
        h2 = ttk.Frame(k1)
        h2.pack(fill="x")
        # master= LA BAT BUOC. Thieu no, bien bam vao `tkinter._default_root`;
        # neu co mot root Tk khac ra doi truoc (vi du do `ttk.Style()` goi khi
        # chua co Tk nao) thi bien nam o interpreter Tcl KHAC voi Entry -> o
        # luon TRONG du `.set()` da chay, va `.get()` luon rong du nguoi dung
        # da go. Khong exception, khong log. Xem bug.md.
        self.v_draft = tk.StringVar(master=self.root)
        self.e_draft = ttk.Entry(h2, textvariable=self.v_draft)
        self.e_draft.pack(side="left", fill="x", expand=True)
        ttk.Button(h2, text="Chọn...", width=10,
                   command=lambda: self._chon_thu_muc(self.v_draft,
                                                      self.e_draft)).pack(
            side="left", padx=(6, 0))

        # --- 2) Folder xuat ra ---
        k2 = ttk.LabelFrame(ngoai, text="2) Thư mục XUẤT RA (bản tự chứa)"
                                     " — bấm Chọn... hoặc DÁN đường dẫn vào ô",
                            padding=6)
        k2.pack(fill="x", pady=(8, 0))
        h3 = ttk.Frame(k2)
        h3.pack(fill="x")
        self.v_out = tk.StringVar(master=self.root)
        self.e_out = ttk.Entry(h3, textvariable=self.v_out)
        self.e_out.pack(side="left", fill="x", expand=True)
        ttk.Button(h3, text="Chọn...", width=10,
                   command=lambda: self._chon_thu_muc(self.v_out,
                                                      self.e_out)).pack(
            side="left", padx=(6, 0))

        # --- 3) Do theo ten ---
        k3 = ttk.LabelFrame(
            ngoai, text="3) Nếu thiếu file — dò theo TÊN ở đâu"
                        " (nhiều thư mục cách nhau bằng dấu ';'"
                        " — bỏ trống = chỉ quét ổ TRONG MÁY)", padding=6)
        k3.pack(fill="x", pady=(8, 0))
        h4 = ttk.Frame(k3)
        h4.pack(fill="x")
        self.v_do = tk.StringVar(master=self.root)
        self.e_do = ttk.Entry(h4, textvariable=self.v_do)
        self.e_do.pack(side="left", fill="x", expand=True)
        ttk.Button(h4, text="Thêm thư mục...", width=16,
                   command=self._them_thu_muc_do).pack(side="left", padx=(6, 0))
        try:
            # Noi bang "; " CHU KHONG PHAI ", ": day la vi du duy nhat nguoi dung
            # nhin thay, ma bo doc lai tach bang ';'. In dau phay o day la day ho
            # go sai roi ca chuoi thanh MOT duong dan rac - im lang.
            o = "; ".join(str(x) for x in fixed_drives())
        except Exception:
            o = "(khong do duoc)"
        ttk.Label(k3, text=f"Ổ phát hiện: {o}").pack(anchor="w", pady=(4, 0))
        ttk.Label(k3, text="Ổ MẠNG và USB KHÔNG được quét tự động."
                           " Footage nằm ở đó thì bấm 'Thêm thư mục...'.",
                  foreground="#7a4a00").pack(anchor="w")

        # --- 4) Toi uu ---
        k4 = ttk.LabelFrame(
            ngoai, text="4) Tối ưu dung lượng (chỗ nào nghi vấn thì tool tự copy nguyên)",
            padding=6)
        k4.pack(fill="x", pady=(8, 0))
        self.v_trim = tk.BooleanVar(master=self.root, value=True)
        self.v_scale = tk.BooleanVar(master=self.root, value=True)
        self.v_clean = tk.BooleanVar(master=self.root, value=True)
        h5 = ttk.Frame(k4)
        h5.pack(fill="x")
        ttk.Checkbutton(h5, text="Cắt gọn footage dài (giữ đoạn dùng + đệm ~×3)",
                        variable=self.v_trim).pack(side="left")
        ttk.Checkbutton(h5, text="Hạ 4K / nén bitrate khung (H.264, giữ nét theo zoom)",
                        variable=self.v_scale).pack(side="left", padx=12)
        ttk.Checkbutton(h5, text="Bỏ file không dùng / mồ côi / lịch sử",
                        variable=self.v_clean).pack(side="left")

        # --- Nut dieu khien ---
        h6 = ttk.Frame(ngoai)
        h6.pack(fill="x", pady=(10, 0))
        self.nut_quet = ttk.Button(h6, text="1) QUÉT", command=self._bat_dau)
        self.nut_quet.pack(side="left")
        self.nut_dung = ttk.Button(h6, text="Dừng dò", state="disabled",
                                   command=self._dung_do)
        self.nut_dung.pack(side="left", padx=6)
        self.nut_copy = ttk.Button(h6, text="2) TIẾN HÀNH COPY", state="disabled",
                                   command=self._tien_hanh)
        self.nut_copy.pack(side="left")
        self.v_trangthai = tk.StringVar(master=self.root, value="Sẵn sàng.")
        ttk.Label(h6, textvariable=self.v_trangthai).pack(side="left", padx=12)
        # Hang doi nhieu project - mot cua so RIENG. De ben phai de khong lan
        # voi luong mot-project o ben trai.
        ttk.Button(h6, text="Hàng đợi nhiều project...",
                   command=self._mo_hang_doi).pack(side="right")

        # --- Nhat ky ---
        for _o in (self.e_draft, self.e_out, self.e_do):
            self._gan_menu_chuot_phai(_o)

        ttk.Label(ngoai, text="Nhật ký").pack(anchor="w", pady=(10, 2))
        # wrap="char" chu khong "none": khong co thanh cuon ngang nen dong dai
        # (vd "Se gom ... vao <duong dan dich>") bi cat mat duoi, giau luon ten
        # folder dich ngay tai man hinh xac nhan.
        self.log = scrolledtext.ScrolledText(ngoai, height=16, wrap="char",
                                             font=("Consolas", 9))
        self.log.pack(fill="both", expand=True)
        self.log.config(state="disabled")

    # ------------------------------------------------------------- tien ich
    @staticmethod
    def _lam_sach_ds_duong_dan(s):
        """Lam sach chuoi nhieu duong dan cach nhau bang ';'.

        - Bo nhay kep TUNG PHAN TU: Windows 11 "Copy as path" (Shift+chuot phai)
          cho ra CO nhay kep; dan hai thu muc se thanh '"A";"B"' va ca hai deu
          hong. Chi strip nhay KEP - thu muc ten `Kho 'B'` la hop le tren Windows.
        - Coi xuong hang la dau ngan cach (nguoi dung dan nhieu dong).
        - Khu trung.
        Dung splitlines() chu KHONG replace("\n", ";") - viet literal se pha
        'D:\reports\news' thanh rac.
        """
        ra = []
        for dong in str(s).splitlines():
            for phan in dong.split(";"):
                phan = phan.strip().strip('"').strip()
                if phan and phan not in ra:
                    ra.append(phan)
        return ";".join(ra)

    @staticmethod
    def _kiem_nhanh_duoc(p):
        """False neu KHONG duoc kiem duong dan nay tren thread chinh.

        `_bat_dau()` chay tren THREAD CHINH. Mot loi goi `isdir_safe` vao host
        SMB khong noi duoc chan 11-21 giay (do that), cua so hien "Not
        Responding", va dung luc do nut "Dung do" con dang xam - nguoi dung
        khong co duong thoat nao. Cung hinh thai bug #58.

        Voi duong dan UNC ta BO QUA phep kiem truoc va de loi no o `_chay()`
        (thread phu), noi da co san nhanh dich `OSError` sang tieng Viet.
        O cuc bo thi kiem binh thuong - no chi ton vai chuc micro giay.
        """
        t = str(p).strip().strip('"')
        return not (t.startswith("\\\\") or t.startswith("//"))

    @staticmethod
    def _cuon_ve_cuoi(o):
        """Duong dan thuong dai hon o -> phan CUOI (ten folder) bi giau.
        Cuon toi cuoi de nguoi dung thay ngay thu ho vua chon."""
        try:
            o.icursor("end")
            o.xview_moveto(1.0)
        except tk.TclError:
            pass

    def _gan_menu_chuot_phai(self, e):
        """tkinter KHONG co san menu ngu canh cho Entry (da do: bind_class rong).
        Bam chuot phai de dan la phan xa cua nguoi dung Windows - thieu no thi
        ho ket luan la o khong dan duoc."""
        m = tk.Menu(e, tearoff=0)

        def dan():
            # DAN DE LEN, khong noi duoi: o dang 'E:/CU' ma dan tiep se ra
            # 'E:/CUD:/MOI' - mot duong dan rac khong bao gio ton tai.
            e.focus_force()
            e.select_range(0, "end")
            e.icursor("end")
            e.event_generate("<<Paste>>")
            self._cuon_ve_cuoi(e)

        m.add_command(label="Dan", command=dan)
        m.add_command(label="Chep", command=lambda: e.event_generate("<<Copy>>"))
        m.add_command(label="Cat", command=lambda: e.event_generate("<<Cut>>"))
        m.add_separator()
        m.add_command(label="Chon het",
                      command=lambda: (e.focus_force(), e.select_range(0, "end"),
                                       e.icursor("end")))
        m.add_command(label="Xoa het",
                      command=lambda: (e.focus_force(), e.delete(0, "end")))
        self._menus.append(m)

        def hien(ev):
            e.focus_force()
            try:
                m.tk_popup(ev.x_root, ev.y_root)
            finally:
                m.grab_release()
            return "break"

        for phim in ("<Button-3>", "<Shift-F10>", "<App>"):
            e.bind(phim, hien)

        # Ctrl+Shift+V: bind o MUC WIDGET. TUYET DOI khong bind_all - lop
        # 'TEntry' chay TRUOC lop 'all' va Tk da co san <Control-Lock-Key-V>,
        # nen bind_all se lam CapsLock bat -> dan HAI lan.
        e.bind("<Control-V>",
               lambda ev, w=e: (w.event_generate("<<Paste>>"), "break")[1])

        # Vao o thi chon het -> mot lan Ctrl+V la thay sach, khong chen giua
        # chuoi cu thanh duong dan rac.
        def chon_het(ev):
            w = ev.widget
            w.after_idle(lambda: (w.select_range(0, "end"), w.icursor("end")))
        e.bind("<FocusIn>", chon_het, add="+")

    def _chon_thu_muc(self, bien, o=None):
        cu = bien.get().strip().strip('"')
        # `parent` phai la doi so TUONG MINH chu khong nam trong **kw: bo kiem
        # tinh doc bang AST se khong nhin thay no neu no an trong dict, va mot
        # bo kiem khong nhin thay duoc thi khong bao ve duoc gi.
        kw = {}
        # KHONG tham do UNC lam initialdir: host khong noi duoc lam treo giao
        # dien hang chuc giay (da do 42,6s).
        if cu and not cu.startswith("\\\\") and isdir_safe(Path(cu)):
            kw["initialdir"] = cu
        d = filedialog.askdirectory(title="Chon thu muc", parent=self.root,
                                    **kw)
        if d:                      # Cancel tra ve chuoi rong -> giu nguyen o
            bien.set(str(Path(d)))
            if o is not None:
                self._cuon_ve_cuoi(o)

    def _them_thu_muc_do(self):
        d = filedialog.askdirectory(title="Chon thu muc de do theo ten",
                                    parent=self.root)
        if not d:
            return
        moi = str(Path(d))

        def chuan(x):
            x = x.strip().strip('"').strip()
            try:
                return os.path.normcase(os.path.normpath(x)) if x else ""
            except Exception:
                return x.lower()

        cu = [x.strip() for x in self.v_do.get().split(";") if x.strip()]
        if any(chuan(x) == chuan(moi) for x in cu):
            self.v_trangthai.set(f"Da co trong danh sach: {moi}")
            return
        cu.append(moi)
        self.v_do.set(";".join(cu))
        self._cuon_ve_cuoi(self.e_do)

    def _ghi(self, dong):
        self.log.config(state="normal")
        self.log.insert("end", dong + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _dat_danh_sach(self, ds, nhan):
        self.drafts = list(ds)
        self.ds.delete(0, "end")
        if not ds:
            self.ds.insert("end", nhan)
            return
        for d in ds:
            self.ds.insert("end", str(d))

    def _nap_danh_sach_mac_dinh(self):
        try:
            ds = G.list_drafts(G.capcut_roots())
        except Exception as ex:
            self._ghi(f"! Khong liet ke duoc thu muc CapCut mac dinh: {ex}")
            ds = []
        self._dat_danh_sach(ds, "(Khong thay project nao.)")

    def _quet_thu_muc_me(self):
        """Quet o THREAD PHU. Truoc day chay thang tren thread chinh: do duoc
        dong bang mainloop 19,6 giay tren o mang, Windows dan nhan "Not
        Responding" 14,6 giay, MOI cu bam nut bi hoan 19,3 giay - ke ca nut X.
        Cung hinh thai #58."""
        if self.dang_quet or self.dang_chay:
            return
        d = filedialog.askdirectory(
            title="Chon THU MUC ME de quet project ben trong", parent=self.root)
        if not d:
            return

        self.phien_quet += 1
        phien = self.phien_quet
        self.dang_quet = True
        self.co_huy_quet.clear()
        self.v_trangthai.set("Đang quét thư mục mẹ...")
        self.nut_quet.config(state="disabled")
        self.nut_dung.config(state="normal", text="Dừng quét")
        self._ghi(f"Dang quet {d} ...")

        def viec():
            # Chay o thread phu: TUYET DOI khong cham vao tkinter o day, moi
            # thu di qua hang doi roi `_rut_hang_doi` moi ve len giao dien.
            try:
                ds, n_loi, huy = G.scan_drafts_recursive(
                    Path(d), nen_dung=self.co_huy_quet.is_set,
                    on_error=lambda ls: None)
                # `mtime_an_toan` khong nem, nhung sort van co the cham I/O lau
                # -> giu no o thread phu luon.
                ds.sort(key=mtime_an_toan, reverse=True)
                self.hd.put(("quet_xong", (phien, d, ds, n_loi, huy)))
            except BaseException:
                self.hd.put(("quet_loi", (phien, traceback.format_exc())))

        threading.Thread(target=viec, daemon=True).start()

    def _chon_tu_danh_sach(self, _e=None):
        s = self.ds.curselection()
        if s and self.drafts and s[0] < len(self.drafts):
            self.v_draft.set(str(self.drafts[s[0]]))
            self._cuon_ve_cuoi(self.e_draft)

    # ------------------------------------------------------------- chay tool
    def _bat_dau(self):
        # Chan chay chong len pha quet thu muc me: hai thread cung ghi vao
        # `self.hd` va cung doi nut la trang thai giao dien thanh vo nghia.
        if self.dang_chay or self.dang_quet:
            return
        draft = self.v_draft.get().strip().strip('"')
        out = self.v_out.get().strip().strip('"')
        # O 3: lam sach truoc (nhay kep cua "Copy as path", xuong hang, trung)
        do_sach = self._lam_sach_ds_duong_dan(self.v_do.get())

        # Cac phep kiem QUYET DINH nam o `ui/kiem_dau_vao.py` (SPEC muc 8);
        # o day chi HIEN THI ket qua. Tach nhu vay de kiem chung duoc chung ma
        # khong can dung cua so Tk.
        _cam = (_GOC, _CHUONG_TRINH, _TAI_NGUYEN)
        for kq in (
            KDV.kiem_draft(draft, self._kiem_nhanh_duoc, isdir_safe,
                           isfile_safe, G.CONTENT_NAMES),
            KDV.kiem_out(out, _cam, self._kiem_nhanh_duoc, isfile_safe,
                         tuyet_doi_that),
            KDV.kiem_do(do_sach, self._kiem_nhanh_duoc, isdir_safe),
            KDV.kiem_toi_uu(self.v_trim.get(), self.v_scale.get(),
                            self.v_clean.get()),
        ):
            if kq.ok:
                continue
            if kq.hoi:
                # Nguoi dung van co quyen chay tiep - vd mot USB vua rut khong
                # duoc chan ca lan gom.
                if messagebox.askyesno(kq.tieu_de, kq.noi_dung, parent=self.root):
                    continue
                return
            if kq.muc == "canh_bao":
                messagebox.showwarning(kq.tieu_de, kq.noi_dung, parent=self.root)
            else:
                messagebox.showerror(kq.tieu_de, kq.noi_dung, parent=self.root)
            return

        self.dang_chay = True
        self._lap = {}            # bo dem chong lap, cho moi lan chay
        # PHAI xoa: bo tra loi cu giu BAN CHUP cua lan chay TRUOC. Khong xoa thi
        # lan chay thu hai se dung duong dan cu - im lang va sai hoan toan.
        self._bo_tra_loi = None
        self.cho_tien_hanh.clear()
        # QUEN DONG NAY = lan chay THU HAI sau mot lan huy se ngat ngay o thu muc
        # dau tien va giao goi THIEU FILE ma van moi nguoi dung bam COPY.
        # Do that: lan 2 quet DUNG 1 thu muc, 0,15 s, goi ra thieu file.
        self.co_huy.clear()
        self.tra_loi_tien_hanh = None
        self.nut_quet.config(state="disabled")
        self.nut_dung.config(state="normal", text="Dừng dò")
        self.nut_copy.config(state="disabled")
        self.v_trangthai.set("Đang quét...")
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")

        # CHUP toan bo gia tri form NGAY BAY GIO, tren THREAD CHINH.
        # tkinter khong an toan da luong: goi `.get()` cua mot BooleanVar tu
        # thread phu nem `RuntimeError: main thread is not in main loop`.
        # Thread phu chi duoc dung cac gia tri thuan duoi day.
        self.chup = {
            "draft": draft,
            "out": out,
            "do": do_sach,
            "trim": bool(self.v_trim.get()),
            "scale": bool(self.v_scale.get()),
            "cleanup": bool(self.v_clean.get()),
        }
        self.luong = threading.Thread(target=self._chay, daemon=True)
        self.luong.start()

    def _tra_loi(self, loi_nhac=""):
        """Uy quyen cho `ui.cau_noi.TraLoi` - xem module do de biet chi tiet.

        Giu lai ham nay lam cua vao de bo kiem cu (goi thang `gd._tra_loi(...)`)
        van chay duoc, va de `self._lap` van soi duoc tu ben ngoai.
        """
        if self._bo_tra_loi is None:
            self._bo_tra_loi = TraLoi(
                chup=self.chup,
                hd=self.hd,
                cho_tien_hanh=self.cho_tien_hanh,
                doc_tra_loi_tien_hanh=lambda: self.tra_loi_tien_hanh,
            )
            # Dung CHUNG mot dict dem: bo kiem va `_bat_dau()` deu soi `self._lap`.
            self._bo_tra_loi.lap = self._lap
        return self._bo_tra_loi(loi_nhac)

    def _chay(self):
        cu_in, cu_out = builtins.input, sys.stdout
        # `redirect_stdout` KHONG theo thread (bug.md) -> thay truc tiep, tra lai
        # trong `finally`. Giao dien khong in ra stdout nen khong xung dot.
        builtins.input = self._tra_loi
        sys.stdout = Ong(self.hd)
        try:
            c = self.chup       # chi dung BAN CHUP, khong cham vao tkinter
            G.main(tuy_chon={"trim": c["trim"], "scale": c["scale"],
                             "cleanup": c["cleanup"],
                             "nen_dung": self.co_huy.is_set})
            # Ket thuc bang "Xong." sau mot cu HUY la bao cao sai ket qua: do
            # duoc 5/5 lan nhan CUOI CUNG la "Xong.", khong phan biet duoc voi
            # mot lan chay thanh cong. Hai nhanh `except` giu NGUYEN - loi that
            # phai thang nhanh huy, khong duoc bi che thanh "da huy".
            self.hd.put(("xong", "Đã huỷ — chưa copy gì cả."
                                 if self.co_huy.is_set() else "Xong."))
        except OSError as ex:
            sys.stdout.flush()
            self.hd.put(("log", f"! KHÔNG GHI/ĐỌC ĐƯỢC: {ex.strerror or ex}"))
            self.hd.put(("log", "  -> Kiểm lại mục 2 (thư mục XUẤT RA): ổ đĩa có"
                                " tồn tại không, có đủ chỗ không, có quyền ghi"
                                " không."))
            self.hd.put(("log", "  -> Nếu là ổ mạng: kiểm kết nối và đăng nhập."))
            for d in traceback.format_exc().splitlines():
                self.hd.put(("log", d))
            self.hd.put(("xong", "CÓ LỖI — xem Nhật ký."))
        except BaseException:
            sys.stdout.flush()
            for d in traceback.format_exc().splitlines():
                self.hd.put(("log", d))
            self.hd.put(("xong", "CÓ LỖI — xem Nhật ký."))
        finally:
            try:
                sys.stdout.flush()
            except Exception:
                pass
            builtins.input, sys.stdout = cu_in, cu_out

    def _mo_hang_doi(self):
        """Mo cua so hang doi nhieu project.

        Cua so RIENG (`tk.Toplevel`) chu khong thay the cua so nay: nguoi dung
        quen luong mot-project van dung nguyen duoc.
        """
        if getattr(self, "_cs_hd", None) is not None:
            try:
                if self._cs_hd.root.winfo_exists():
                    self._cs_hd.root.lift()
                    return
            except tk.TclError:
                pass
            self._cs_hd = None
        try:
            from ui.chay_hang_doi import chay_mot_project
            from ui.cua_so_hang_doi import CuaSoHangDoi
        except ImportError as ex:
            messagebox.showerror(
                "Thiếu file",
                f"Không nạp được phần hàng đợi:\n  {ex}\n\n"
                "Có vẻ bạn chép thiếu thư mục `ui/`. Hãy chép LẠI CẢ THƯ MỤC"
                " công cụ.", parent=self.root)
            return

        cua = tk.Toplevel(self.root)
        # CHUP tuy chon muc 4 NGAY BAY GIO, tren THREAD CHINH: hang doi chay o
        # thread phu va khong duoc goi `.get()` cua bien tkinter (SPEC muc 6.1).
        tc = {
            "trim": bool(self.v_trim.get()),
            "scale": bool(self.v_scale.get()),
            "cleanup": bool(self.v_clean.get()),
            "do": self._lam_sach_ds_duong_dan(self.v_do.get()),
        }
        self._cs_hd = CuaSoHangDoi(
            cua,
            chay_mot=lambda m, nd: chay_mot_project(m, nd, G),
            tuy_chon_mac_dinh=tc,
            # Truyen G va fixed_drives vao chu KHONG de cua so tu import:
            # nho vay bo kiem dung duoc module gia, va `ui/` khong phu thuoc
            # cung vao `goi_project_capcut`.
            G=G,
            fixed_drives=fixed_drives)

    def _tien_hanh(self):
        self.tra_loi_tien_hanh = "y"
        self.nut_copy.config(state="disabled")
        self.v_trangthai.set("Đang copy / tối ưu...")
        self.cho_tien_hanh.set()

    def _dung_do(self):
        # Nhanh QUET DUNG TRUOC: no la mot pha khac han, co Event rieng.
        # Dat o dau ham de khong dung toi `tra_loi_tien_hanh` / `co_huy` cua
        # pha gói - hai pha khong duoc lan vao nhau.
        if self.dang_quet:
            self.co_huy_quet.set()
            self.nut_dung.config(state="disabled", text="Đang dừng...")
            self.v_trangthai.set("Đang dừng quét...")
            self.hd.put(("log", "! Đã nhận lệnh DỪNG quét thư mục mẹ..."))
            return
        # BA trang thai, khong phai hai. Chot cu
        #     if self.cho_tien_hanh.is_set() or self.tra_loi_tien_hanh:
        # gop "da bam COPY" voi "vua bam HUY" lam mot - chinh cu bam thu nhat
        # lam ca hai ve thanh dung - nen bam lan hai sau khi huy lai hien hop
        # thoai "Da bat dau copy roi", noi doi trang tron khi chua copy mot byte
        # nao. `cho_tien_hanh.is_set()` tuong duong `tra_loi_tien_hanh in
        # ("y","n")`, nen chi can kiem == "y" la du VA dung.
        if self.tra_loi_tien_hanh == "y":
            messagebox.showinfo(
                "Đang chạy",
                "Đã bắt đầu COPY rồi — không dừng giữa chừng được.\n\n"
                "Muốn dừng hẳn thì đóng cửa sổ này. Nhưng LẦN SAU:\n"
                "  - KHÔNG chạy lại vào CHÍNH thư mục xuất ra này: tool sẽ copy"
                " lại từ đầu VÀ tạo thêm bản trùng (canh1_1.mp4...), gói phình"
                " gấp đôi và lần cũ thành rác.\n"
                "  - Hãy XOÁ thư mục xuất ra đó đi, hoặc chọn một thư mục MỚI."
                "\n\n(Riêng phần mã lại video ở mục 4 thì phần lớn được giữ lại.)",
                parent=self.root)
            return
        if self.co_huy.is_set():
            return          # da bam roi - nut da xam, khong noi gi them

        # Thu tu QUAN TRONG: dat `co_huy` TRUOC `cho_tien_hanh`. Neu thread phu
        # dang doi o `_tra_loi` thi luc no tinh day va `main()` tra ve, `_chay`
        # da nhin thay co huy roi - khong thi nhan cuoi lai thanh "Xong.".
        self.co_huy.set()
        self.nut_dung.config(state="disabled", text="Đang dừng...")
        self.v_trangthai.set("Đang dừng...")
        # Day qua HANG DOI (khong goi `_ghi` truc tiep) de dong nay nam DUNG thu
        # tu so voi dau ra cua thread phu. Khong co dong nay thi nguoi dung chi
        # thay mot nhan nho doi chu roi im lang, va se bam lai nhieu lan.
        self.hd.put(("log", ""))
        self.hd.put(("log", "! Đã nhận lệnh DỪNG — đang thoát khỏi pha đang"
                            " chạy (thường dưới 1 giây; ổ mạng lạnh có thể"
                            " vài giây)..."))
        self.tra_loi_tien_hanh = "n"
        self.cho_tien_hanh.set()

    # ------------------------------------------------------- vong lap hien thi
    def _rut_hang_doi(self):
        try:
            # Gioi han moi nhip: thread phu day duoc ~2 trieu dong/giay con giao
            # dien nuot ~19 nghin/giay, nen `while True` khong bao gio gap
            # queue.Empty -> after() khong duoc dat lai -> mainloop CHET, nut X
            # cung vo hieu. Co gioi han thi lu dong chi lam CHAM, khong treo.
            for _ in range(300):
                loai, gt = self.hd.get_nowait()
                if loai == "log":
                    self._ghi(gt)
                elif loai == "quet_xong":
                    phien, d, ds, n_loi, huy = gt
                    if phien != self.phien_quet:
                        continue      # ket qua phien CU ve muon -> bo di
                    self.dang_quet = False
                    self.nut_quet.config(state="normal")
                    self.nut_dung.config(state="disabled", text="Dừng dò")
                    self._dat_danh_sach(
                        ds, "(Không thấy project nào trong thư mục đó.)")
                    if huy:
                        self._ghi(f"Da DUNG quet theo yeu cau - moi tim duoc"
                                  f" {len(ds)} project trong {d}."
                                  f" Danh sach nay CHUA day du.")
                        self.v_trangthai.set("Đã dừng quét.")
                    else:
                        self._ghi(f"Quet {d}: tim thay {len(ds)} project.")
                        self.v_trangthai.set("Sẵn sàng.")
                    if n_loi:
                        # KHONG duoc nuot: mot nhanh cay khong doc duoc nghia la
                        # danh sach co the THIEU project, nguoi dung phai biet.
                        self._ghi(f"! {n_loi} thu muc khong doc duoc khi quet"
                                  f" (thieu quyen / o mang rot phien) -"
                                  f" danh sach co the THIEU project.")
                elif loai == "quet_loi":
                    phien, ct = gt
                    if phien != self.phien_quet:
                        continue
                    self.dang_quet = False
                    self.nut_quet.config(state="normal")
                    self.nut_dung.config(state="disabled", text="Dừng dò")
                    self.v_trangthai.set("Không quét được.")
                    for dg in ct.splitlines():
                        self._ghi("   " + dg)
                    messagebox.showerror(
                        "Lỗi", "Không quét được thư mục đó — xem Nhật ký.",
                        parent=self.root)
                elif loai == "cho_tien_hanh":
                    # Luoi an toan. Voi ban va nay `main()` return TRUOC cau hoi
                    # "Tien hanh?" nen tin nay gan nhu khong bao gio toi sau khi
                    # huy - TRU dung khe hep khi nguoi dung bam dung luc
                    # `_tra_loi` vua day tin nay xong. De lot thi giao dien se
                    # BAT LAI nut COPY va moi nguoi VUA HUY di bam "TIEN HANH".
                    if self.co_huy.is_set():
                        continue
                    self.nut_copy.config(state="normal")
                    self.v_trangthai.set(
                        "Đã quét xong — xem Nhật ký rồi bấm 2) TIẾN HÀNH COPY")
                elif loai == "xong":
                    self.dang_chay = False
                    self.nut_quet.config(state="normal")
                    self.nut_dung.config(state="disabled", text="Dừng dò")
                    self.nut_copy.config(state="disabled")
                    self.v_trangthai.set(gt)
        except queue.Empty:
            pass
        except Exception:
            # Mot loi o day KHONG duoc lam chet nhip dap vinh vien
            try:
                self._ghi("! Lỗi khi cập nhật giao diện (đã bỏ qua 1 nhịp)")
            except Exception:
                pass
        finally:
            # PHAI o `finally`: neu no nam cuoi than ham, mot exception se lam
            # nhip dap dung han - im lang, giao dien dong bang mai mai.
            #
            # NHUNG phai kiem cua so con song: dat `after` len mot root da bi
            # destroy khien Tcl nem `invalid command name "..._rut_hang_doi"`
            # ra stderr luc dong chuong trinh. Duoi pythonw thi dong rac do di
            # thang vao `_LOI_GIAO_DIEN.log`, lam nguoi dung tuong co loi that.
            try:
                if self.root.winfo_exists():
                    self._nhip = self.root.after(80, self._rut_hang_doi)
            except tk.TclError:
                pass          # cua so da dong - dung nhip, khong con gi de cap nhat

    def _huy_nhip(self, ev=None):
        """Huy nhip dap. `<Destroy>` lan truyen tu MOI widget con nen phai loc
        dung cua so goc, khong thi huy ngay khi mot widget con bat ky bi go."""
        if ev is not None and ev.widget is not self.root:
            return
        if self._nhip is not None:
            try:
                self.root.after_cancel(self._nhip)
            except (tk.TclError, RuntimeError):
                pass
            self._nhip = None

    def _dong(self):
        if self.dang_chay and not messagebox.askyesno(
                "Đang chạy", "Tool đang chạy. Đóng cửa sổ sẽ DỪNG giữa chừng.\n\n"
                             "Vẫn đóng?", parent=self.root):
            return
        self._huy_nhip()
        self.root.destroy()


class CuaSoTuKiem:
    """Cua so tien trinh cho LAN CHAY DAU (sau khi giai nen).

    Chi hien khi CHUA co dau kiem cua dung phien ban nay. Kiem xong va dat thi
    ghi dau -> cac lan sau vao thang giao dien (tiet kiem ~3,2 giay cua phep
    thu ffmpeg).
    """

    def __init__(self, root):
        self.root = root
        self.dat = None
        self.ds = []
        root.title("Kiểm tra lần đầu...")
        root.resizable(False, False)

        k = ttk.Frame(root, padding=16)
        k.pack(fill="both", expand=True)
        ttk.Label(k, text="Đang kiểm tra bộ công cụ (chỉ làm MỘT LẦN)",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(k, text="Các lần sau sẽ vào thẳng giao diện.",
                  foreground="#555").pack(anchor="w", pady=(2, 10))

        self.thanh = ttk.Progressbar(k, length=420, maximum=len(TK.CAC_BUOC))
        self.thanh.pack(fill="x")
        self.v_buoc = tk.StringVar(master=root, value="Đang bắt đầu...")
        ttk.Label(k, textvariable=self.v_buoc).pack(anchor="w", pady=(6, 0))

        self.o = scrolledtext.ScrolledText(k, height=9, width=62, wrap="word",
                                           font=("Consolas", 9))
        self.o.pack(fill="both", expand=True, pady=(10, 0))
        self.o.config(state="disabled")

        self.nut = ttk.Frame(k)
        self.nut.pack(fill="x", pady=(10, 0))

        def _loi_callback(exc, val, tb):
            ct = "".join(traceback.format_exception(exc, val, tb))
            try:
                self._ghi("! LOI: " + ct.strip().splitlines()[-1])
            except Exception:
                pass
            try:
                messagebox.showerror("Lỗi khi tự kiểm", ct[-1500:], parent=root)
            except Exception:
                pass
        root.report_callback_exception = _loi_callback

        root.after(150, self._chay)

    def _ghi(self, s):
        self.o.config(state="normal")
        self.o.insert("end", s + "\n")
        self.o.see("end")
        self.o.config(state="disabled")

    def _chay(self):
        def bao(i, tong, ten, ok, ct):
            self.thanh["value"] = i
            self.v_buoc.set(f"[{i}/{tong}] {ten}")
            self._ghi(f"[{'OK' if ok else 'HONG'}] {ten}")
            if not ok:
                for d in str(ct).splitlines():
                    self._ghi("      " + d)
            self.root.update()

        # DOC tai nguyen (ffmpeg, cac .py) -> thu muc tai nguyen
        self.dat, self.ds = TK.chay(_TAI_NGUYEN, bao=bao)
        if self.dat:
            try:
                # GHI dau -> thu muc ghi duoc (co the la %LOCALAPPDATA%)
                TK.ghi_dau(TK.thu_muc_dau(), G.TOOL_VERSION, self.ds)
            except Exception as ex:
                # Ghi dau that bai KHONG duoc chan nguoi dung - chi nghia la lan
                # sau kiem lai (ton 5 giay), khong phai loi nghiem trong.
                self._ghi(f"(khong ghi duoc dau kiem: {ex} - lan sau se kiem lai)")
            self.v_buoc.set("Tất cả ĐẠT. Đang mở giao diện...")
            self.root.after(700, self.root.destroy)
        else:
            self.v_buoc.set("CÓ VẤN ĐỀ — xem chi tiết ở trên.")
            ttk.Button(self.nut, text="Vẫn mở giao diện",
                       command=self.root.destroy).pack(side="left")
            ttk.Button(self.nut, text="Thoát",
                       command=lambda: (setattr(self, "dat", None),
                                        self.root.destroy())).pack(side="left",
                                                                   padx=6)


def _dat_theme(root):
    """PHAI truyen master. `ttk.Style()` tran se tu tao root - xem `main()`."""
    try:
        ttk.Style(root).theme_use("vista")
    except Exception:
        pass


def main():
    # TUYET DOI khong goi ttk.Style() (hay tao bat ky widget/Variable nao) truoc
    # khi co tk.Tk(). ttk.Style() -> setup_master(None) -> _get_default_root()
    # goi KHONG co tham so `what` -> `if _default_root is None: root = Tk()`:
    # no TU TAO mot cua so Tk that, hien tren man hinh, ten "tk". Hau qua:
    #   1. Moi StringVar/BooleanVar khong master bam vao root LAC do, con
    #      Entry/Checkbutton nam o root that -> hai interpreter Tcl khac nhau ->
    #      3 o duong dan va 3 o tich CHET CA HAI CHIEU, khong exception nao.
    #   2. `r0.mainloop()` cua cua so tu kiem KHONG BAO GIO tra ve (no chi thoat
    #      khi Tk_GetNumMainWindows()==0, ma root lac van song) -> LAN CHAY DAU
    #      tren may vua giai nen TREO HAN, giao dien khong bao gio mo.
    # Xem bug.md.
    try:
        # --- Lan dau: tu kiem roi moi mo giao dien ---
        # DOC dau: phai cung cho voi noi GHI, khong thi lan nao cung kiem lai
        if not TK.da_kiem(TK.thu_muc_dau(), G.TOOL_VERSION):
            r0 = tk.Tk()
            _dat_theme(r0)
            ck = CuaSoTuKiem(r0)
            r0.mainloop()
            if ck.dat is None:
                return          # nguoi dung bam Thoat

        root = tk.Tk()
        _dat_theme(root)
        GiaoDien(root)
        root.mainloop()
    except Exception:
        # Luoi cuoi cung: loi luc KHOI TAO khong duoc report_callback_exception
        # bat, ma duoi pythonw thi stderr la ho den -> "bam dup, khong co gi
        # xay ra, tuyet doi khong mot chu nao".
        ct = traceback.format_exc()
        try:
            r = tk.Tk()
            r.withdraw()
            messagebox.showerror("Không mở được giao diện", ct[-1500:],
                                 parent=r)
            r.destroy()
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
