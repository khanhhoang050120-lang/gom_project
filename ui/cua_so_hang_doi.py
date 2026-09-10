# -*- coding: utf-8 -*-
"""CUA SO HANG DOI - giao dien cho viec gom nhieu project mot luot.

Bo cuc theo tai_lieu/SPEC_UI_UX.md (huong C):
    Thanh cong cu tren cung
    Trai : danh sach hang doi (ten + trang thai + thanh tien do nho)
    Phai : chi tiet muc dang chon (so lieu + nhat ky rieng)
    Duoi : dong trang thai

Module nay CHI dung giao dien. Moi quyet dinh nam o `ui/hang_doi.py`, va viec
goi `main()` nam o `ui/chay_hang_doi.py`.

Ba diem ky thuat GIU NGUYEN tu giao dien chinh (SPEC muc 6):
  1. tkinter khong an toan da luong -> hang doi chay o thread rieng, moi cap
     nhat di qua `queue` + `after()` tren thread chinh.
  2. Nhip dap co GIOI HAN so tin moi lan, va dat lai `after` trong `finally`.
  3. Bat `<Destroy>` de huy nhip dap du cua so bi dong bang duong nao.
"""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from ui.hang_doi import CHO, DANG_CHAY, HUY, LOI, XONG, HangDoi, Muc

# Chu hien thi cho tung trang thai. Gom o mot cho de khong go lech nhau.
NHAN = {
    CHO: "Cho chay",
    DANG_CHAY: "Dang chay",
    XONG: "Xong",
    LOI: "LOI",
    HUY: "Da huy",
}
MAU = {
    CHO: "#6b7783",
    DANG_CHAY: "#1b3a56",
    XONG: "#3f9142",
    LOI: "#c33",
    HUY: "#8a6d3b",
}


class CuaSoHangDoi:
    """Cua so hang doi. Truyen `chay_mot` de kiem chung duoc ma khong gom that."""

    def __init__(self, root, chay_mot, tuy_chon_mac_dinh=None):
        self.root = root
        self.tin = queue.Queue()
        self.hd = HangDoi(chay_mot=chay_mot,
                          bao=lambda k, m: self.tin.put(("hd", (k, m))))
        self.tc = dict(tuy_chon_mac_dinh or
                       {"trim": True, "scale": True, "cleanup": True, "do": ""})
        self.luong = None
        self._nhip = None

        root.title("Goi Project CapCut - Hang doi")
        cao = min(660, max(520, root.winfo_screenheight() - 160))
        root.geometry(f"1000x{cao}")
        root.minsize(860, 480)

        self._dung()
        self._nhip = root.after(120, self._rut_tin)
        root.protocol("WM_DELETE_WINDOW", self._dong)
        root.bind("<Destroy>", self._huy_nhip, add="+")

    # ------------------------------------------------------------------ dung
    def _dung(self):
        cong_cu = ttk.Frame(self.root, padding=(8, 6))
        cong_cu.pack(fill="x")
        self.nut_them = ttk.Button(cong_cu, text="Them project...",
                                   command=self._them)
        self.nut_them.pack(side="left")
        self.nut_bo = ttk.Button(cong_cu, text="Bo khoi hang doi",
                                 command=self._bo, state="disabled")
        self.nut_bo.pack(side="left", padx=(6, 0))
        ttk.Separator(cong_cu, orient="vertical").pack(
            side="left", fill="y", padx=8, pady=2)
        self.nut_chay = ttk.Button(cong_cu, text="Chay hang doi",
                                   command=self._chay, state="disabled")
        self.nut_chay.pack(side="left")
        self.nut_dung = ttk.Button(cong_cu, text="Dung", state="disabled",
                                   command=self._dung_lai)
        self.nut_dung.pack(side="left", padx=(6, 0))
        self.v_tomtat = tk.StringVar(master=self.root,
                                     value="Hang doi trong.")
        ttk.Label(cong_cu, textvariable=self.v_tomtat).pack(side="right")

        chia = ttk.Panedwindow(self.root, orient="horizontal")
        chia.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        # --- trai: danh sach ---
        trai = ttk.Frame(chia)
        chia.add(trai, weight=1)
        ttk.Label(trai, text="Hang doi").pack(anchor="w")
        hop = ttk.Frame(trai)
        hop.pack(fill="both", expand=True)
        self.ds = tk.Listbox(hop, exportselection=False, activestyle="none")
        self.ds.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(hop, orient="vertical", command=self.ds.yview)
        sb.pack(side="right", fill="y")
        self.ds.config(yscrollcommand=sb.set)
        self.ds.bind("<<ListboxSelect>>", self._chon_muc)

        # --- phai: chi tiet ---
        phai = ttk.Frame(chia)
        chia.add(phai, weight=2)
        self.v_ten = tk.StringVar(master=self.root, value="(chua chon muc nao)")
        ttk.Label(phai, textvariable=self.v_ten,
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.v_duong = tk.StringVar(master=self.root, value="")
        ttk.Label(phai, textvariable=self.v_duong, foreground="#6b7783",
                  wraplength=560, justify="left").pack(anchor="w", pady=(1, 6))

        self.thanh = ttk.Progressbar(phai, mode="determinate", maximum=100)
        self.thanh.pack(fill="x")
        self.v_tt = tk.StringVar(master=self.root, value="")
        ttk.Label(phai, textvariable=self.v_tt).pack(anchor="w", pady=(3, 6))

        ttk.Label(phai, text="Nhat ky cua muc nay").pack(anchor="w")
        # wrap="char" chu khong "none": khong co thanh cuon ngang nen dong dai
        # bi cat mat duoi, giau luon ten folder dich (cung ly do o SPEC muc 4.1).
        self.log = scrolledtext.ScrolledText(phai, height=14, wrap="char",
                                             font=("Consolas", 9))
        self.log.pack(fill="both", expand=True)
        self.log.config(state="disabled")

        self.v_day = tk.StringVar(master=self.root, value="")
        ttk.Label(self.root, textvariable=self.v_day, foreground="#5c6773",
                  padding=(10, 3)).pack(fill="x")

    # ------------------------------------------------------------- thao tac
    def _them(self):
        d = filedialog.askdirectory(title="Chon folder draft CapCut",
                                    parent=self.root)
        if not d:
            return
        o = filedialog.askdirectory(title=f"Goi '{Muc(d, '').ten}' vao dau?",
                                    parent=self.root)
        if not o:
            return
        self.hd.them(Muc(d, o, tuy_chon=self.tc))

    def _bo(self):
        m = self._muc_dang_chon()
        if m is None:
            return
        if not self.hd.bo(m):
            messagebox.showinfo(
                "Khong bo duoc",
                "Muc nay dang chay - khong bo giua chung duoc.\n\n"
                "Bam 'Dung' truoc neu muon dung han.", parent=self.root)

    def _chay(self):
        if self.hd.dang_chay or not self.hd.cho_chay():
            return
        self.luong = threading.Thread(target=self.hd.chay, daemon=True)
        self.luong.start()
        self._cap_nhat_nut()

    def _dung_lai(self):
        self.hd.huy()
        self.nut_dung.config(state="disabled", text="Dang dung...")
        self.v_day.set("Da nhan lenh DUNG - dang thoat khoi muc dang chay...")

    def _muc_dang_chon(self):
        s = self.ds.curselection()
        if not s or s[0] >= len(self.hd.muc):
            return None
        return self.hd.muc[s[0]]

    def _chon_muc(self, _e=None):
        self._ve_chi_tiet()
        self._cap_nhat_nut()

    # ------------------------------------------------------------ hien thi
    def _ve_danh_sach(self):
        giu = self.ds.curselection()
        self.ds.delete(0, "end")
        for m in self.hd.muc:
            self.ds.insert("end", f"  {m.ten}   [{NHAN[m.trang_thai]}]")
            self.ds.itemconfig("end", foreground=MAU[m.trang_thai])
        if giu and giu[0] < self.ds.size():
            self.ds.selection_set(giu[0])

    def _ve_chi_tiet(self):
        # DOC THANG tu Listbox chu khong giu ban sao: mot bien `_chon` chi duoc
        # cap nhat luc nguoi dung bam se lech ngay khi danh sach doi, va khung
        # phai dung im du muc do dang chay.
        m = self._muc_dang_chon()
        if m is None:
            self.v_ten.set("(chua chon muc nao)")
            self.v_duong.set("")
            self.v_tt.set("")
            self.thanh["value"] = 0
            self._dat_log([])
            return
        self.v_ten.set(f"{m.ten}  -  {NHAN[m.trang_thai]}")
        self.v_duong.set(f"Tu: {m.draft}\nVao: {m.out}")
        giay = m.giay
        thoi = f"  ({giay:.0f} giay)" if giay else ""
        self.v_tt.set(f"{m.thong_bao}{thoi}")
        self.thanh["value"] = {XONG: 100, DANG_CHAY: 50}.get(m.trang_thai, 0)
        self._dat_log(m.nhat_ky)

    def _dat_log(self, dong):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        # Chi hien 400 dong CUOI: mot lan gom co the sinh hang nghin dong, va
        # do ra het lam giao dien giat. Dong moi nhat la dong quan trong nhat.
        for d in dong[-400:]:
            self.log.insert("end", d + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _cap_nhat_nut(self):
        chay = self.hd.dang_chay
        con = bool(self.hd.cho_chay())
        self.nut_chay.config(state="disabled" if (chay or not con) else "normal")
        self.nut_dung.config(state="normal" if chay else "disabled",
                             text="Dung")
        self.nut_them.config(state="disabled" if chay else "normal")
        m = self._muc_dang_chon()
        co_bo = m is not None and m.trang_thai != DANG_CHAY
        self.nut_bo.config(state="normal" if co_bo else "disabled")
        self.v_tomtat.set(self.hd.mo_ta_tong_ket() if self.hd.muc
                          else "Hang doi trong.")

    # ------------------------------------------------------- vong lap hien thi
    def _rut_tin(self):
        # PHAI khoi tao TRUOC `try`: neu khai bao ben trong ma exception xay ra
        # ngay dong dau, `finally` se doc bien chua ton tai -> NameError, va
        # nhip dap chet vinh vien. Dung loai loi ma `finally` sinh ra de tranh.
        ve_ds = ve_ct = False
        try:
            # GIOI HAN moi nhip: khong co no thi mot lan gom sinh hang nghin
            # dong se lam `while True` khong bao gio gap `queue.Empty` ->
            # `after()` khong duoc dat lai -> mainloop CHET (SPEC muc 6.5).
            for _ in range(200):
                loai, gt = self.tin.get_nowait()
                if loai == "hd":
                    ve_ds = ve_ct = True
                elif loai == "log_muc":
                    m, _dong = gt
                    # Chi ve lai khi dong log thuoc muc DANG XEM - khong thi
                    # moi dong cua moi muc deu bat ve lai, giao dien giat.
                    if m is self._muc_dang_chon():
                        ve_ct = True
        except queue.Empty:
            pass
        except Exception:
            # Mot loi o day KHONG duoc lam chet nhip dap vinh vien.
            pass
        finally:
            try:
                if ve_ds:
                    self._ve_danh_sach()
                    self._cap_nhat_nut()
                if ve_ct:
                    self._ve_chi_tiet()
            except Exception:
                pass
            # PHAI o `finally` VA phai kiem cua so con song (SPEC muc 6.5).
            try:
                if self.root.winfo_exists():
                    self._nhip = self.root.after(120, self._rut_tin)
            except tk.TclError:
                pass

    def _huy_nhip(self, ev=None):
        if ev is not None and ev.widget is not self.root:
            return
        if self._nhip is not None:
            try:
                self.root.after_cancel(self._nhip)
            except (tk.TclError, RuntimeError):
                pass
            self._nhip = None

    def _dong(self):
        if self.hd.dang_chay and not messagebox.askyesno(
                "Dang chay",
                "Hang doi dang chay. Dong cua so se BO DO muc dang lam.\n\n"
                "Van dong?", parent=self.root):
            return
        self.hd.huy()
        self._huy_nhip()
        self.root.destroy()
