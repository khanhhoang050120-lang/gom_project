# -*- coding: utf-8 -*-
"""CỬA SỔ HÀNG ĐỢI - gói nhiều project một lượt.

Bố cục theo `tai_lieu/SPEC_UI_UX.md` §11 (phương án A, chủ dự án duyệt
2026-09-10):

    Trái : bảng hàng đợi (Project / Trạng thái / Dung lượng / Thời gian)
    Phải : ĐÚNG 4 khối của cửa sổ chính, là form của MỘT mục
    Dưới : hàng nút + ô Nhật ký của mục đang chọn

Mỗi project giữ RIÊNG cả 4 mục — project này hạ 4K, project kia giữ nguyên.

Module này CHỈ dựng giao diện. Mọi quyết định nằm ở `ui/hang_doi.py`, việc
gọi `main()` nằm ở `ui/chay_hang_doi.py`, việc quét thử ở `ui/quet_thu.py`.

Ba điểm kỹ thuật GIỮ NGUYÊN từ cửa sổ chính (SPEC §6):
  1. tkinter không an toàn đa luồng -> hàng đợi chạy ở thread riêng, mọi cập
     nhật đi qua `queue` + `after()` trên thread chính.
  2. Nhịp đập có GIỚI HẠN số tin mỗi lần, và đặt lại `after` trong `finally`.
  3. Bắt `<Destroy>` để huỷ nhịp đập dù cửa sổ bị đóng bằng đường nào.
"""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from ui.hang_doi import CHO, DANG_CHAY, HUY, LOI, XONG, HangDoi, Muc

# Chữ hiển thị cho từng trạng thái. Gom ở một chỗ để không gõ lệch nhau.
NHAN = {
    CHO: "Chờ chạy",
    DANG_CHAY: "Đang chạy",
    XONG: "Xong",
    LOI: "LỖI",
    HUY: "Đã huỷ",
}
MAU = {
    CHO: "#6b7783",
    DANG_CHAY: "#1b3a56",
    XONG: "#3f9142",
    LOI: "#c33333",
    HUY: "#8a6d3b",
}


class CuaSoHangDoi:
    """Cửa sổ hàng đợi. Truyền `chay_mot` để kiểm chứng được mà không gói thật."""

    def __init__(self, root, chay_mot, tuy_chon_mac_dinh=None, G=None,
                 fixed_drives=None):
        self.root = root
        self.G = G
        self._fixed_drives = fixed_drives
        self.tin = queue.Queue()
        self.hd = HangDoi(chay_mot=chay_mot,
                          bao=lambda k, m: self.tin.put(("hd", (k, m))))
        self.tc_mac_dinh = dict(tuy_chon_mac_dinh or
                                {"trim": True, "scale": True,
                                 "cleanup": True, "do": ""})
        self.luong = None
        self._nhip = None
        self._dang_them = True     # True = form đang là "mục mới"
        self._luong_quet = None
        # CHỐNG TÁI NHẬP. `_ve_bang()` gọi `selection_set()` để giữ lại dòng
        # đang chọn; Tk sinh `<<TreeviewSelect>>` -> `_chon_muc()` ->
        # `_ve_tat_ca()` -> `_ve_bang()` -> ... đệ quy VÔ HẠN, cửa sổ treo
        # cứng ngay khi thêm mục đầu tiên. Đo thật: `root.update()` không bao
        # giờ trả về, script bị timeout ở mã 124.
        self._dang_ve = False

        root.title("Gói Project CapCut — Hàng đợi nhiều project")
        cao = min(780, max(560, root.winfo_screenheight() - 120))
        root.geometry(f"1180x{cao}")
        root.minsize(1000, 560)

        self._dung()
        self._nhip = root.after(120, self._rut_tin)
        root.protocol("WM_DELETE_WINDOW", self._dong)
        root.bind("<Destroy>", self._huy_nhip, add="+")
        self._ve_tat_ca()

    # ------------------------------------------------------------------ dựng
    def _dung(self):
        ngoai = ttk.Frame(self.root, padding=8)
        ngoai.pack(fill="both", expand=True)

        tren = ttk.Frame(ngoai)
        tren.pack(fill="both", expand=True)

        self._dung_bang(tren)
        self._dung_form(tren)
        self._dung_dieu_khien(ngoai)
        self._dung_nhat_ky(ngoai)

        self.v_chan = tk.StringVar(master=self.root, value="")
        ttk.Label(self.root, textvariable=self.v_chan, foreground="#5c6773",
                  padding=(10, 3)).pack(fill="x")

    def _dung_bang(self, cha):
        """Trái: bảng hàng đợi, 4 cột."""
        trai = ttk.Frame(cha)
        trai.pack(side="left", fill="both", expand=True)

        hang = ttk.Frame(trai)
        hang.pack(fill="x")
        ttk.Label(hang, text="Hàng đợi",
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        self.v_tomtat = tk.StringVar(master=self.root, value="Hàng đợi trống.")
        ttk.Label(hang, textvariable=self.v_tomtat,
                  foreground="#5c6773").pack(side="right")

        hop = ttk.Frame(trai)
        hop.pack(fill="both", expand=True, pady=(3, 0))
        # `Treeview` chứ không `Listbox`: bốn cột cần căn thẳng hàng, mà
        # Listbox chỉ có một chuỗi nên phải đệm khoảng trắng bằng tay — lệch
        # ngay khi tên project dài ngắn khác nhau.
        self.bang = ttk.Treeview(
            hop, columns=("tt", "dl", "tg"), show="tree headings",
            selectmode="browse", height=10)
        self.bang.heading("#0", text="Project")
        self.bang.heading("tt", text="Trạng thái")
        self.bang.heading("dl", text="Dung lượng")
        self.bang.heading("tg", text="Thời gian")
        self.bang.column("#0", width=190, minwidth=120)
        self.bang.column("tt", width=130, minwidth=90, anchor="w")
        self.bang.column("dl", width=130, minwidth=90, anchor="e")
        self.bang.column("tg", width=80, minwidth=60, anchor="e")
        self.bang.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(hop, orient="vertical", command=self.bang.yview)
        sb.pack(side="right", fill="y")
        self.bang.config(yscrollcommand=sb.set)
        self.bang.bind("<<TreeviewSelect>>", self._chon_muc)
        for tt, mau in MAU.items():
            self.bang.tag_configure(tt, foreground=mau)

        h = ttk.Frame(trai)
        h.pack(fill="x", pady=(6, 0))
        ttk.Button(h, text="Mục mới", command=self._muc_moi).pack(side="left")
        self.nut_bo = ttk.Button(h, text="Bỏ khỏi hàng đợi", state="disabled",
                                 command=self._bo)
        self.nut_bo.pack(side="left", padx=6)

    def _dung_form(self, cha):
        """Phải: ĐÚNG 4 khối của cửa sổ chính."""
        phai = ttk.Frame(cha, padding=(10, 0, 0, 0))
        phai.pack(side="left", fill="both", expand=True)

        self.v_dau_form = tk.StringVar(master=self.root, value="")
        ttk.Label(phai, textvariable=self.v_dau_form,
                  font=("Segoe UI", 10, "bold"),
                  foreground="#1b3a56").pack(anchor="w", pady=(0, 4))

        # --- 1) Chọn project ---
        k1 = ttk.LabelFrame(phai, text="1) Chọn project (thư mục draft CapCut)",
                            padding=6)
        k1.pack(fill="x")
        ttk.Label(k1, text="Dán thẳng đường dẫn vào ô dưới (Ctrl+V),"
                           " hoặc bấm Chọn...:").pack(anchor="w", pady=(0, 2))
        h1 = ttk.Frame(k1)
        h1.pack(fill="x")
        # master= LÀ BẮT BUỘC — xem SPEC §6.6. Thiếu nó, biến bám vào
        # `tkinter._default_root` và có thể nằm ở interpreter Tcl KHÁC với
        # Entry: ô luôn trống dù `.set()` đã chạy, không exception, không log.
        self.v_draft = tk.StringVar(master=self.root)
        self.e_draft = ttk.Entry(h1, textvariable=self.v_draft)
        self.e_draft.pack(side="left", fill="x", expand=True)
        ttk.Button(h1, text="Chọn...", width=10,
                   command=lambda: self._chon_thu_muc(self.v_draft)).pack(
            side="left", padx=(6, 0))

        # --- 2) Thư mục xuất ra ---
        k2 = ttk.LabelFrame(phai, text="2) Thư mục XUẤT RA (bản tự chứa)",
                            padding=6)
        k2.pack(fill="x", pady=(8, 0))
        h2 = ttk.Frame(k2)
        h2.pack(fill="x")
        self.v_out = tk.StringVar(master=self.root)
        self.e_out = ttk.Entry(h2, textvariable=self.v_out)
        self.e_out.pack(side="left", fill="x", expand=True)
        ttk.Button(h2, text="Chọn...", width=10,
                   command=lambda: self._chon_thu_muc(self.v_out)).pack(
            side="left", padx=(6, 0))

        # --- 3) Dò theo tên ---
        k3 = ttk.LabelFrame(
            phai, text="3) Nếu thiếu file — dò theo TÊN ở đâu"
                       " (nhiều thư mục cách nhau bằng dấu ';')", padding=6)
        k3.pack(fill="x", pady=(8, 0))
        h3 = ttk.Frame(k3)
        h3.pack(fill="x")
        self.v_do = tk.StringVar(master=self.root)
        self.e_do = ttk.Entry(h3, textvariable=self.v_do)
        self.e_do.pack(side="left", fill="x", expand=True)
        ttk.Button(h3, text="Thêm thư mục...", width=16,
                   command=self._them_thu_muc_do).pack(side="left", padx=(6, 0))
        try:
            # Nối bằng "; " CHỨ KHÔNG PHẢI ", ": đây là ví dụ duy nhất người
            # dùng nhìn thấy, mà bộ đọc lại tách bằng ';'. In dấu phẩy là dạy
            # họ gõ sai rồi cả chuỗi thành MỘT đường dẫn rác — im lặng.
            o = "; ".join(str(x) for x in (self._fixed_drives or (lambda: []))())
        except Exception:
            o = "(không dò được)"
        ttk.Label(k3, text=f"Ổ phát hiện: {o}").pack(anchor="w", pady=(4, 0))
        ttk.Label(k3, text="Ổ MẠNG và USB KHÔNG được quét tự động."
                           " Footage nằm ở đó thì bấm 'Thêm thư mục...'.",
                  foreground="#7a4a00").pack(anchor="w")

        # --- 4) Tối ưu dung lượng ---
        k4 = ttk.LabelFrame(phai, text="4) Tối ưu dung lượng", padding=6)
        k4.pack(fill="x", pady=(8, 0))
        self.v_trim = tk.BooleanVar(master=self.root, value=True)
        self.v_scale = tk.BooleanVar(master=self.root, value=True)
        self.v_clean = tk.BooleanVar(master=self.root, value=True)
        ttk.Checkbutton(k4, text="Cắt gọn footage dài (giữ đoạn dùng + đệm ~×3)",
                        variable=self.v_trim).pack(anchor="w")
        ttk.Checkbutton(k4, text="Hạ 4K / nén bitrate khung"
                                 " (H.264, giữ nét theo zoom)",
                        variable=self.v_scale).pack(anchor="w")
        ttk.Checkbutton(k4, text="Bỏ file không dùng / mồ côi / lịch sử",
                        variable=self.v_clean).pack(anchor="w")

        h4 = ttk.Frame(phai)
        h4.pack(fill="x", pady=(8, 0))
        self.nut_luu = ttk.Button(h4, text="+ Thêm vào hàng đợi",
                                  command=self._luu_form)
        self.nut_luu.pack(side="left")
        self.nut_quet_thu = ttk.Button(h4, text="Quét thử mục này",
                                       command=self._quet_thu)
        self.nut_quet_thu.pack(side="left", padx=6)

    def _dung_dieu_khien(self, cha):
        h = ttk.Frame(cha)
        h.pack(fill="x", pady=(10, 0))
        self.nut_chay = ttk.Button(h, text="CHẠY CẢ HÀNG ĐỢI", state="disabled",
                                   command=self._chay)
        self.nut_chay.pack(side="left")
        self.nut_dung = ttk.Button(h, text="Dừng", state="disabled",
                                   command=self._dung_lai)
        self.nut_dung.pack(side="left", padx=6)
        self.v_trangthai = tk.StringVar(master=self.root, value="Sẵn sàng.")
        ttk.Label(h, textvariable=self.v_trangthai).pack(side="left", padx=12)

    def _dung_nhat_ky(self, cha):
        self.v_ten_log = tk.StringVar(master=self.root, value="Nhật ký")
        ttk.Label(cha, textvariable=self.v_ten_log).pack(anchor="w",
                                                         pady=(10, 2))
        # wrap="char" chứ KHÔNG "none": không có thanh cuộn ngang nên dòng dài
        # bị cắt mất đuôi, giấu luôn tên thư mục đích (SPEC §4.1).
        self.log = scrolledtext.ScrolledText(cha, height=11, wrap="char",
                                             font=("Consolas", 9))
        self.log.pack(fill="both", expand=True)
        self.log.config(state="disabled")

    # ------------------------------------------------------------- thao tác
    def _chon_thu_muc(self, bien):
        d = filedialog.askdirectory(parent=self.root)
        if d:
            bien.set(d.replace("/", "\\"))

    def _them_thu_muc_do(self):
        d = filedialog.askdirectory(title="Thêm thư mục để dò",
                                    parent=self.root)
        if not d:
            return
        d = d.replace("/", "\\")
        cu = self.v_do.get().strip().strip(";")
        self.v_do.set(f"{cu};{d}" if cu else d)

    def _muc_dang_chon(self):
        """ĐỌC THẲNG từ bảng, không giữ bản sao.

        Bản sao chỉ cập nhật lúc người dùng bấm sẽ lệch ngay khi danh sách
        đổi, và khung phải đứng im dù mục đó đang chạy. Không có bản sao thì
        không có chuyện bản sao lệch với bản thật.
        """
        s = self.bang.selection()
        if not s:
            return None
        try:
            i = int(s[0])
        except (ValueError, TypeError):
            return None
        return self.hd.muc[i] if 0 <= i < len(self.hd.muc) else None

    def _muc_moi(self):
        self._dang_them = True
        self.bang.selection_remove(*self.bang.selection())
        self.v_draft.set("")
        self.v_out.set("")
        self.v_do.set(self.tc_mac_dinh.get("do", ""))
        self.v_trim.set(bool(self.tc_mac_dinh.get("trim", True)))
        self.v_scale.set(bool(self.tc_mac_dinh.get("scale", True)))
        self.v_clean.set(bool(self.tc_mac_dinh.get("cleanup", True)))
        self._ve_tat_ca()

    def _doc_form(self):
        return (self.v_draft.get().strip().strip('"'),
                self.v_out.get().strip().strip('"'),
                {"trim": bool(self.v_trim.get()),
                 "scale": bool(self.v_scale.get()),
                 "cleanup": bool(self.v_clean.get()),
                 "do": self.v_do.get().strip()})

    def _luu_form(self):
        draft, out, tc = self._doc_form()
        if not draft or not out:
            messagebox.showwarning(
                "Thiếu thông tin",
                "Cần cả mục 1 (thư mục draft) và mục 2 (thư mục xuất ra).",
                parent=self.root)
            return
        if self._dang_them:
            m = self.hd.them(Muc(draft, out, tuy_chon=tc))
            self._dang_them = False
            self._ve_bang()
            # `selection_set` PHẢI nằm trong vùng khoá: nó sinh
            # `<<TreeviewSelect>>`, mà `_chon_muc` lại gọi `_ve_tat_ca` ->
            # `_ve_bang` -> ... Khoá ở trong `_ve_bang` thôi là CHƯA ĐỦ vì
            # dòng này nằm NGOÀI hàm đó.
            cu = self._dang_ve
            self._dang_ve = True
            try:
                self.bang.selection_set(str(len(self.hd.muc) - 1))
            finally:
                self._dang_ve = cu
        else:
            m = self._muc_dang_chon()
            if m is None:
                return
            if m.trang_thai == DANG_CHAY:
                messagebox.showinfo(
                    "Đang chạy",
                    "Mục này đang chạy — không sửa giữa chừng được.",
                    parent=self.root)
                return
            m.draft, m.out, m.tuy_chon = draft, out, tc
            m.ten = Muc._ten_tu_duong_dan(draft)
            # Đổi cấu hình thì số liệu quét cũ không còn đúng nữa.
            m.byte_goc = m.so_file = None
        self._ve_tat_ca()

    def _bo(self):
        m = self._muc_dang_chon()
        if m is None:
            return
        if not self.hd.bo(m):
            messagebox.showinfo(
                "Không bỏ được",
                "Mục này đang chạy — không bỏ giữa chừng được.\n\n"
                "Bấm 'Dừng' trước nếu muốn dừng hẳn.", parent=self.root)
            return
        self._muc_moi()

    def _quet_thu(self):
        """Quét MỘT mục để xem trước số liệu. KHÔNG ghi gì ra đĩa."""
        if self._luong_quet is not None and self._luong_quet.is_alive():
            return
        if self.G is None:
            messagebox.showinfo("Chưa sẵn sàng",
                                "Không nạp được phần lõi để quét.",
                                parent=self.root)
            return
        m = self._muc_dang_chon()
        if m is None:
            draft, out, tc = self._doc_form()
            if not draft:
                messagebox.showwarning(
                    "Thiếu thông tin",
                    "Hãy chọn thư mục draft ở mục 1 trước khi quét thử.",
                    parent=self.root)
                return
            m = Muc(draft, out or draft, tuy_chon=tc)   # mục tạm, không thêm

        self.nut_quet_thu.config(state="disabled", text="Đang quét thử...")
        self.v_trangthai.set(f"Đang quét thử {m.ten}... (chưa ghi gì ra đĩa)")

        def chay():
            from ui.quet_thu import quet_thu
            kq = quet_thu(m, self.G)
            self.tin.put(("quet_xong", (m, kq)))

        self._luong_quet = threading.Thread(target=chay, daemon=True)
        self._luong_quet.start()

    def _chay(self):
        if self.hd.dang_chay or not self.hd.cho_chay():
            return
        self.luong = threading.Thread(target=self.hd.chay, daemon=True)
        self.luong.start()
        self._cap_nhat_nut()

    def _dung_lai(self):
        self.hd.huy()
        self.nut_dung.config(state="disabled", text="Đang dừng...")
        self.v_chan.set("Đã nhận lệnh DỪNG — đang thoát khỏi mục đang chạy...")

    def _chon_muc(self, _e=None):
        if self._dang_ve:
            return          # sự kiện do chính `_ve_bang()` sinh ra, không phải người dùng
        m = self._muc_dang_chon()
        if m is None:
            return
        self._dang_them = False
        self.v_draft.set(m.draft)
        self.v_out.set(m.out)
        self.v_do.set(m.tuy_chon.get("do", ""))
        self.v_trim.set(bool(m.tuy_chon.get("trim", True)))
        self.v_scale.set(bool(m.tuy_chon.get("scale", True)))
        self.v_clean.set(bool(m.tuy_chon.get("cleanup", True)))
        # KHONG goi `_ve_tat_ca()` o day: no ve lai BANG, ma ve bang lai sinh
        # `<<TreeviewSelect>>` -> quay lai chinh ham nay. Do that: 39 lan goi
        # `_chon_muc`, 21 lan `_ve_bang`, `root.update()` khong bao gio tra ve.
        # Chon mot dong KHONG lam doi noi dung bang, nen ve lai bang vua thua
        # vua sinh vong lap. Chi cap nhat nhung gi that su doi.
        self._ve_form_head()
        self._ve_nhat_ky()
        self._cap_nhat_nut()

    # ------------------------------------------------------------ hiển thị
    def _ve_bang(self):
        giu = self.bang.selection()
        # Khoá TRƯỚC khi động vào bảng: `delete` và `selection_set` đều sinh
        # `<<TreeviewSelect>>`, mà xử lý sự kiện đó lại vẽ bảng.
        cu = self._dang_ve
        self._dang_ve = True
        try:
            self.bang.delete(*self.bang.get_children())
            for i, m in enumerate(self.hd.muc):
                self.bang.insert("", "end", iid=str(i), text="  " + m.ten,
                                 values=(NHAN[m.trang_thai],
                                         m.mo_ta_dung_luong(),
                                         m.mo_ta_thoi_gian()),
                                 tags=(m.trang_thai,))
            if giu and giu[0] in self.bang.get_children():
                self.bang.selection_set(giu[0])
        finally:
            self._dang_ve = cu

    def _ve_form_head(self):
        if self._dang_them:
            self.v_dau_form.set("Mục mới — điền 4 ô dưới rồi bấm"
                                " “+ Thêm vào hàng đợi”")
            self.nut_luu.config(text="+ Thêm vào hàng đợi")
        else:
            m = self._muc_dang_chon()
            self.v_dau_form.set(f"Đang sửa: {m.ten}" if m else "")
            self.nut_luu.config(text="Lưu thay đổi")

    def _ve_nhat_ky(self):
        m = self._muc_dang_chon()
        self.v_ten_log.set(f"Nhật ký — {m.ten}" if m else "Nhật ký")
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        if m is not None:
            # Chỉ hiện 400 dòng CUỐI: một lần gói sinh hàng nghìn dòng, đổ ra
            # hết làm giao diện giật. Dòng mới nhất là dòng quan trọng nhất.
            for d in m.nhat_ky[-400:]:
                self.log.insert("end", d + "\n")
            self.log.see("end")
        self.log.config(state="disabled")

    def _cap_nhat_nut(self):
        chay = self.hd.dang_chay
        con = bool(self.hd.cho_chay())
        self.nut_chay.config(state="disabled" if (chay or not con) else "normal")
        self.nut_dung.config(state="normal" if chay else "disabled", text="Dừng")
        m = self._muc_dang_chon()
        self.nut_bo.config(
            state="normal" if (m is not None and m.trang_thai != DANG_CHAY)
            else "disabled")
        self.nut_luu.config(state="disabled" if chay else "normal")
        self.v_tomtat.set(self.hd.mo_ta_tong_ket() if self.hd.muc
                          else "Hàng đợi trống.")
        if not chay:
            self.v_trangthai.set("Sẵn sàng." if con else
                                 ("Xong." if self.hd.muc else "Hàng đợi trống."))

    def _ve_tat_ca(self):
        self._ve_bang()
        self._ve_form_head()
        self._ve_nhat_ky()
        self._cap_nhat_nut()

    # ------------------------------------------------------ vòng lặp hiển thị
    def _rut_tin(self):
        # PHẢI khởi tạo TRƯỚC `try`: nếu khai báo bên trong mà exception xảy ra
        # ngay dòng đầu, `finally` sẽ đọc biến chưa tồn tại -> NameError, và
        # nhịp đập chết vĩnh viễn.
        ve_bang = ve_log = ve_nut = False
        try:
            # GIỚI HẠN mỗi nhịp: không có nó thì một lần gói sinh hàng nghìn
            # dòng sẽ làm `while True` không bao giờ gặp `queue.Empty` ->
            # `after()` không được đặt lại -> mainloop CHẾT (SPEC §6.5).
            for _ in range(200):
                loai, gt = self.tin.get_nowait()
                if loai == "hd":
                    ve_bang = ve_log = ve_nut = True
                elif loai == "log_muc":
                    m, _d = gt
                    if m is self._muc_dang_chon():
                        ve_log = True
                elif loai == "quet_xong":
                    m, kq = gt
                    m.nhat_ky.extend(kq.cac_dong())
                    self.nut_quet_thu.config(state="normal",
                                             text="Quét thử mục này")
                    self.v_trangthai.set(
                        f"Quét thử xong: {kq.so_file_gom} file"
                        if kq.dat else "Quét thử THẤT BẠI — xem Nhật ký.")
                    ve_bang = ve_log = ve_nut = True
        except queue.Empty:
            pass
        except Exception:
            # Một lỗi ở đây KHÔNG được làm chết nhịp đập vĩnh viễn.
            pass
        finally:
            try:
                if ve_bang:
                    self._ve_bang()
                if ve_log:
                    self._ve_nhat_ky()
                if ve_nut:
                    self._cap_nhat_nut()
            except Exception:
                pass
            # PHẢI ở `finally` VÀ phải kiểm cửa sổ còn sống (SPEC §6.5).
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
                "Đang chạy",
                "Hàng đợi đang chạy. Đóng cửa sổ sẽ BỎ DỞ mục đang làm.\n\n"
                "Vẫn đóng?", parent=self.root):
            return
        self.hd.huy()
        self._huy_nhip()
        self.root.destroy()
