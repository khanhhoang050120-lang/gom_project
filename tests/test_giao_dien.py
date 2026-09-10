# -*- coding: utf-8 -*-

"""Giao dien phai LAI DUOC tool that, khong chi ve ra dep.



Nguyen tac thiet ke: `giao_dien.py` KHONG viet lai logic - no thay `input()` va

`sys.stdout` roi goi thang `goi_project_capcut.main()`. Bo kiem nay chot dung

dieu do, va chot ca cac diem ky thuat de sai:

  - `main()` nhan `tuy_chon` va 3 o tich di DUNG vao `opts`

  - `_tra_loi()` tra loi theo NOI DUNG cau hoi, khong theo thu tu (bay #10)

  - cau hoi la -> NEM LOI, khong duoc doan bua

  - stdout duoc TRA LAI sau khi chay (redirect_stdout khong theo thread)

  - chay TRON MOT LUOT tren draft gia

"""

from __future__ import annotations



import io

import json
import os

import shutil

import sys

import subprocess

import tempfile

import threading

import time

from pathlib import Path



HERE = Path(__file__).resolve().parent

ROOT = HERE.parent

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(HERE))



pas = fail = 0

# Giu MOI root Tk va MOI GiaoDien tao ra trong bo kiem nay - dung tha ra.
#
# Vi sao: khi mot root bi `destroy()` roi doi tuong Python cua no duoc thu gom,
# `Variable.__del__` goi vao mot interpreter Tcl da chet. Da so lan chi la mot
# dong "Exception ignored" vo hai, nhung neu viec thu gom roi vao dung luc/dung
# thread khong mong doi thi Tcl bo ra
#     Tcl_AsyncDelete: async handler deleted by the wrong thread
# - loi GIET CA TIEN TRINH, khong bat duoc, xoa luon ket qua da in.
#
# Da do: voi Python HE THONG thi qua, voi ban DI KEM (thu ban may con dung) thi
# chet - va chet GIUA CHUNG chu khong phai luc thoat, nen `os._exit` o cuoi
# khong cuu duoc. Giu tham chieu thi khong co `__del__` nao chay trong luc chay,
# con luc thoat da co `os._exit` bo qua toan bo giai doan don dep.
_GIU_TK = []


def _nho(x):
    """Ghi nho mot doi tuong Tk de no khong bi thu gom giua chung."""
    _GIU_TK.append(x)
    return x





def check(ten, dk, ct=""):

    global pas, fail

    if dk:

        pas += 1

        print(f"  PASS  {ten}")

    else:

        fail += 1

        print(f"  FAIL  {ten}")

        for d in str(ct).splitlines():

            print(f"           {d}")





def co_tkinter():

    try:

        import tkinter  # noqa: F401

        tkinter.Tk().destroy()

        return True

    except Exception:

        return False





def test_khong_viet_lai_logic():

    print("=" * 72)

    print("Giao dien KHONG duoc viet lai logic - phai goi main() that")

    print("=" * 72)

    src = (ROOT / "giao_dien.py").read_text(encoding="utf-8")

    check("co goi G.main(", "G.main(" in src,

          "phai lai ham main() da duoc kiem chung, khong viet lai")

    check("truyen tuy_chon tu 3 o tich",

          "tuy_chon={" in src and "self.v_trim.get()" in src)

    check("thay builtins.input", "builtins.input = self._tra_loi" in src)

    check("TRA LAI input/stdout trong finally",

          "finally:" in src and "builtins.input, sys.stdout = cu_in, cu_out" in src,

          "khong tra lai thi lan chay sau se dung ham cua lan truoc")

    # KHONG duoc tu cai dat lai cac buoc nang

    for cam in ("shutil.copytree", "subprocess.run", "os.remove", "os.walk"):

        check(f"khong tu lam `{cam}`", cam not in src,

              "giao dien lam viec nay = logic bi nhan doi -> se lech voi dong lenh")





def test_tra_loi_theo_noi_dung():

    print()

    print("=" * 72)

    print("Tra loi theo NOI DUNG cau hoi, cau hoi la thi NEM LOI")

    print("=" * 72)

    if not co_tkinter():

        print("  (khong co tkinter -> bo qua)")

        return

    import tkinter as tk

    import giao_dien



    root = _nho(tk.Tk())

    root.withdraw()

    g = _nho(giao_dien.GiaoDien(root))

    # Ban CHUP: thread phu chi duoc dung cai nay, KHONG cham vao bien tkinter

    # (goi `.get()` tu thread phu nem "main thread is not in main loop").

    g.chup = {"draft": r"D:\DRAFT", "out": r"E:\OUT", "do": r"D:\1363",

              "trim": True, "scale": True, "cleanup": True}

    try:

        cap = [

            ("Nhap so / T / P / Q: ", "P"),

            ("Dan duong dan folder draft: ", r"D:\DRAFT"),

            ("Folder XUAT RA [Enter = ...]: ", r"E:\OUT"),

            ("Chon 1 hoac 4 [Enter = 1]: ", "4"),

            ("  Thu muc/o de do [Enter = tat ca o]: ", r"D:\1363"),

            ("Enter de dong...", ""),

        ]

        for hoi, mong in cap:

            duoc = g._tra_loi(hoi)

            check(f"{hoi.strip()[:36]:38} -> {mong!r}", duoc == mong,

                  f"tra ve {duoc!r}")



        # Cau hoi la PHAI nem loi

        try:

            g._tra_loi("Ban co chac khong (mot cau hoi moi)? ")

            check("cau hoi la -> NEM LOI", False,

                  "doan bua mot cau hoi la co the xoa nham du lieu")

        except RuntimeError:

            check("cau hoi la -> NEM LOI", True)



        # 3 o tich -> chon che do

        g.chup.update(trim=False, scale=False, cleanup=False)

        check("bo het o tich -> chon che do 1 (nguyen ban)",

              g._tra_loi("Chon 1 hoac 4 [Enter = 1]: ") == "1")

        g.chup.update(scale=True)

        check("tich 1 o -> chon che do 4",

              g._tra_loi("Chon 1 hoac 4 [Enter = 1]: ") == "4")

    finally:

        root.destroy()





def test_tuy_chon_di_vao_opts():

    print()

    print("=" * 72)

    print("3 o tich di DUNG vao `opts` cua main()")

    print("=" * 72)

    import goi_project_capcut as G

    import inspect

    check("main() nhan tham so `tuy_chon`",

          "tuy_chon" in inspect.signature(G.main).parameters)

    src = (ROOT / "goi_project_capcut.py").read_text(encoding="utf-8")

    for khoa in ("trim", "scale", "cleanup"):

        check(f"`{khoa}` lay tu tuy_chon", f'_tc.get("{khoa}"' in src)

    check("mac dinh khi KHONG co tuy_chon van la True (giu hanh vi dong lenh)",

          '_tc.get("trim", True)' in src,

          "10 lan chay tren project that deu dung mac dinh nay")





def test_chay_tron_mot_luot():

    print()

    print("=" * 72)

    print("CHAY TRON MOT LUOT tren draft gia (khong chi ve giao dien)")

    print("=" * 72)

    if not co_tkinter():

        print("  (khong co tkinter -> bo qua)")

        return

    import toi_uu_dung_luong as TU

    ffmpeg, ffprobe = TU.ff_paths(ROOT)

    if not ffmpeg:

        print("  (khong co ffmpeg -> bo qua)")

        return



    import tkinter as tk

    import giao_dien

    from draft_gia import tao_draft_gia



    tmp = Path(tempfile.mkdtemp(prefix="gui_e2e_"))

    root = _nho(tk.Tk())

    root.withdraw()

    try:

        mo = tao_draft_gia(tmp, ffmpeg, ffprobe)

        draft = Path(mo["draft_dir"])

        out = tmp / "GOI_RA"



        g = _nho(giao_dien.GiaoDien(root))

        g.v_draft.set(str(draft))

        g.v_out.set(str(out))

        g.v_do.set(str(tmp))          # KHONG de trong (bug #27)

        g.v_trim.set(True); g.v_scale.set(True); g.v_clean.set(True)



        g._bat_dau()



        # Bam "TIEN HANH COPY" NGAY TRONG VONG LAP CHINH.

        # KHONG duoc doi o mot thread phu roi doc `g.nut_copy["state"]`: doc

        # thuoc tinh cua widget tkinter tu thread phu cung nem "main thread is

        # not in main loop" - dung loi vua sua trong `giao_dien.py`.

        t0 = time.time()

        da_bam = False

        while g.dang_chay and time.time() - t0 < 300:

            root.update()

            if not da_bam and str(g.nut_copy["state"]) == "normal":

                g._tien_hanh()

                da_bam = True

            time.sleep(0.05)

        check("da bam duoc nut TIEN HANH COPY", da_bam,

              "nut khong bao gio bat len -> tool khong den buoc hoi")



        van = g.log.get("1.0", "end")

        check("chay xong trong thoi gian cho", not g.dang_chay,

              f"van con chay sau {time.time()-t0:.0f}s")

        check("co di qua buoc hoi 'Tien hanh?'", "Tien hanh" in van,

              van[-400:])

        check("tao ra folder xuat", out.is_dir(), f"khong thay {out}")

        check("co file bao cao", (out / "_BAO_CAO_THIEU.txt").is_file())

        check("nhat ky co ket luan", "Ban tu chua" in van, van[-400:])

        check("khong co traceback trong nhat ky", "Traceback" not in van,

              van[-600:])



        # stdout PHAI duoc tra lai

        check("sys.stdout da duoc tra lai sau khi chay",

              not isinstance(sys.stdout, giao_dien.Ong),

              "khong tra lai -> moi print sau nay bay vao giao dien da dong")

    finally:

        root.destroy()

        shutil.rmtree(tmp, ignore_errors=True)







# ---------------------------------------------------------------- tien ich

def _chay_con(than, gio=180):

    """Chay mot doan ma trong TIEN TRINH RIENG, tra (ma_thoat, stdout+stderr).



    PHAI la tien trinh rieng: bug root Tk lac chi lo ra khi `_default_root` la

    None luc `giao_dien.main()` bat dau. Neu bo kiem nay chay chung tien trinh

    voi cac bo kiem khac (chung da tao tk.Tk()), loi bi CHE hoan toan.



    Ghi ma ra FILE roi chay, khong truyen qua `-c`: doi so dai di qua shell de

    bi nuot backslash (bug #9/#34).

    """

    tmp = Path(tempfile.mkdtemp(prefix="gui_con_"))

    try:

        f = tmp / "con.py"

        f.write_text(than, encoding="utf-8")

        r = subprocess.run([sys.executable, str(f), str(ROOT)],

                           capture_output=True, text=True, encoding="utf-8",

                           errors="replace", timeout=gio, cwd=str(ROOT))

        return r.returncode, (r.stdout or "") + (r.stderr or "")

    finally:

        shutil.rmtree(tmp, ignore_errors=True)





def test_o_duong_dan_hien_that():

    """3 o duong dan / 3 o tich phai SONG khi chay qua main() THAT.



    Bug: `ttk.Style()` o dau main() goi khi chua co tk.Tk() nao -> tkinter TU

    TAO mot root Tk lac. Moi StringVar/BooleanVar khong master bam vao root lac

    do, con Entry/Checkbutton nam o root that -> hai interpreter Tcl khac nhau,

    o luon TRONG du `.set()` da chay va `.get()` luon rong du nguoi dung da go.

    Khong exception, khong log - chi la giao dien khong lam gi ca.

    """

    print()

    print("=" * 72)

    print("3 o duong dan + 3 o tich phai SONG (chay qua main() THAT)")

    print("=" * 72)

    if not co_tkinter():

        print("  (khong co tkinter -> bo qua)")

        return



    than = """

import json, sys, os

sys.path.insert(0, sys.argv[1]); os.chdir(sys.argv[1])

import tkinter as tk

from tkinter import ttk

import giao_dien, tu_kiem_lan_dau as TK



# Bo qua tu kiem lan dau: no cham vao dau kiem THAT o thu muc goc.

TK.da_kiem = lambda *a, **k: True



giu = []

_oi = giao_dien.GiaoDien.__init__

def spy(self, root):

    _oi(self, root); giu.append(self)

giao_dien.GiaoDien.__init__ = spy

tk.Tk.mainloop = lambda self, n=0: None

_ot = tk.Tk.__init__

def ti(self, *a, **k):

    _ot(self, *a, **k); self.withdraw()

tk.Tk.__init__ = ti



giao_dien.main()



g = giu[-1]; root = g.root

es = []

def duyet(w):

    for c in w.winfo_children():

        es.append(c); duyet(c)

duyet(root)

E = [x for x in es if isinstance(x, ttk.Entry)]

C = [x for x in es if isinstance(x, ttk.Checkbutton)]



kq = {}

kq["khong co root Tk lac"] = (tk._default_root is root)

kq["moi bien tkinter bam dung root"] = all(

    getattr(g, t)._root is root for t in

    ("v_draft", "v_out", "v_do", "v_trim", "v_scale", "v_clean", "v_trangthai"))

kq["tim thay du 3 o Entry"] = (len(E) >= 3)



giao_dien.filedialog.askdirectory = lambda **kw: "D:/X/Y"

g._chon_thu_muc(g.v_draft, g.e_draft); root.update()

kq["bam Chon... thi o HIEN RA duong dan"] = (

    g.e_draft.get() == g.v_draft.get() != "")



g.e_out.delete(0, "end"); g.e_out.insert(0, "E:/OUT"); root.update()

kq["dan vao o thi code DOC DUOC"] = (g.v_out.get() == "E:/OUT")



g._dat_danh_sach(["D:/P1", "D:/P2"], "")

g.ds.selection_set(0); g._chon_tu_danh_sach(); root.update()

kq["chon tu danh sach thi o HIEN RA"] = (g.e_draft.get() != "")



kq["3 o tich muc 4 hien dung tich"] = all("selected" in c.state() for c in C[:3])

if C:

    C[0].invoke(); root.update()

    kq["bo tich thi code DOC DUOC"] = (g.v_trim.get() is False)

try:

    root.tk.globalgetvar(str(g.v_trangthai)); kq["nhan trang thai song"] = True

except Exception:

    kq["nhan trang thai song"] = False



print("KETQUA" + json.dumps(kq))

"""

    ma, ra = _chay_con(than)

    dong = [l for l in ra.splitlines() if l.startswith("KETQUA")]

    if not dong:

        check("chay duoc giao_dien.main()", False, ra[-1200:])

        return

    kq = json.loads(dong[0][6:])

    check("da kiem du 8 dieu", len(kq) >= 8, f"chi co {len(kq)}")

    for ten, ok in kq.items():

        check(ten, ok, "root Tk lac -> bien tkinter bam nham interpreter Tcl")





def test_lan_dau_khong_treo():

    """LAN CHAY DAU (may vua giai nen) phai mo duoc giao dien.



    Root Tk lac lam `r0.mainloop()` cua cua so tu kiem KHONG BAO GIO tra ve:

    mainloop chi thoat khi Tk_GetNumMainWindows() == 0, ma root lac van song.

    Do la: code loi -> het 20s, GiaoDien chua tung duoc tao. Zip ban giao KHONG

    chua dau tu kiem, nen day la cu bam dup DAU TIEN cua MOI may con.

    """

    print()

    print("=" * 72)

    print("LAN CHAY DAU: cua so tu kiem xong phai mo duoc giao dien")

    print("=" * 72)

    if not co_tkinter():

        print("  (khong co tkinter -> bo qua)")

        return



    than = """

import sys, os, threading, time

sys.path.insert(0, sys.argv[1]); os.chdir(sys.argv[1])

import tkinter as tk

import giao_dien, tu_kiem_lan_dau as TK



# Ep di duong LAN DAU, nhung KHONG cham vao dau kiem that o thu muc goc.

TK.da_kiem = lambda *a, **k: False

TK.ghi_dau = lambda *a, **k: None

def chay_gia(goc, bao=None):

    if bao:

        bao(1, 2, "buoc gia 1", True, "")

        bao(2, 2, "buoc gia 2", True, "")

    return True, [{"buoc": "gia", "dat": True, "chi_tiet": ""}]

TK.chay = chay_gia

TK.CAC_BUOC = getattr(TK, "CAC_BUOC", [1, 2])



# KHONG duoc va tk.Tk.mainloop: chinh viec mainloop khong tra ve LA cai bug.

# Thay vao do cho GiaoDien tu dong dong sau 300ms de mainloop THU HAI thoat.

tao = []

_oi = giao_dien.GiaoDien.__init__

def spy(self, root):

    _oi(self, root); tao.append(self); root.after(300, root.destroy)

giao_dien.GiaoDien.__init__ = spy



def canh():

    time.sleep(25)

    print("QUA GIO - GiaoDien da tao?", bool(tao), flush=True)

    os._exit(7)

threading.Thread(target=canh, daemon=True).start()



giao_dien.main()

print("GiaoDien da tao?", bool(tao))

print("XONG_BINH_THUONG")

"""

    ma, ra = _chay_con(than, gio=90)

    check("main() tra ve duoc (khong treo)", ma == 0 and "XONG_BINH_THUONG" in ra,

          f"ma thoat {ma} (7 = het gio, tuc la TREO)\n{ra[-800:]}")

    check("giao dien THUC SU duoc tao", "GiaoDien da tao? True" in ra, ra[-500:])





def test_lam_sach_ds_duong_dan():

    """O 3 phai chiu duoc 'Copy as path' (co nhay kep) va xuong hang."""

    print()

    print("=" * 72)

    print("O 3: lam sach chuoi nhieu duong dan")

    print("=" * 72)

    if not co_tkinter():

        print("  (khong co tkinter -> bo qua)")

        return

    import giao_dien

    f = giao_dien.GiaoDien._lam_sach_ds_duong_dan

    B = chr(92)

    cap = [

        # Windows 11 "Copy as path" cho ra CO nhay kep

        ('"C:' + B + 'W";"C:' + B + 'U"', 'C:' + B + 'W;C:' + B + 'U'),

        # dan nhieu dong

        ('C:' + B + 'W' + chr(13) + chr(10) + 'C:' + B + 'U',

         'C:' + B + 'W;C:' + B + 'U'),

        # KHONG duoc pha ten thu muc co chu 'n' sau backslash

        ('D:' + B + 'reports;E:' + B + 'news', 'D:' + B + 'reports;E:' + B + 'news'),

        # khu trung

        ('C:' + B + 'W;C:' + B + 'W', 'C:' + B + 'W'),

        # UNC giu du HAI backslash

        (B * 2 + 'localhost' + B + 'C$;C:' + B + 'W',

         B * 2 + 'localhost' + B + 'C$;C:' + B + 'W'),

        ('', ''),

    ]

    for vao, mong in cap:

        ra = f(vao)

        check(f"lam sach {vao!r}", ra == mong, f"ra {ra!r}, mong {mong!r}")





def test_bat_dau_phai_chan_dau_vao_xau():

    """`_bat_dau` phai CHAN, khong duoc khoi dong thread, voi dau vao xau."""

    print()

    print("=" * 72)

    print("_bat_dau phai CHAN dau vao xau (khong khoi dong thread)")

    print("=" * 72)

    if not co_tkinter():

        print("  (khong co tkinter -> bo qua)")

        return

    import tkinter as tk

    import giao_dien

    B = chr(92)



    tmp = Path(tempfile.mkdtemp(prefix="gui_chan_"))

    root = _nho(tk.Tk())

    root.withdraw()

    goi = []

    that = []

    cu_thread = giao_dien.threading.Thread



    class ThreadGia:

        def __init__(self, *a, **k):

            that.append(1)



        def start(self):

            pass



    try:

        me = tmp / "MEP"

        (me / "P1").mkdir(parents=True)

        (me / "P1" / "draft_content.json").write_text("{}", encoding="utf-8")

        mot_file = tmp / "la_file.txt"

        mot_file.write_text("x", encoding="utf-8")



        g = _nho(giao_dien.GiaoDien(root))

        for ten in ("showerror", "showwarning", "showinfo"):

            setattr(giao_dien.messagebox, ten,

                    lambda *a, **k: goi.append(a[0] if a else "?"))

        giao_dien.messagebox.askyesno = lambda *a, **k: False

        giao_dien.threading.Thread = ThreadGia



        canh = [

            ("thu muc me (khong co draft_content.json)", str(me), str(tmp / "RA")),

            ("o 2 la ten tran 'goi_moi'", str(me / "P1"), "goi_moi"),

            ("o 2 la 'D:' (bug #23)", str(me / "P1"), "D:"),

            (f"o 2 UNC thieu backslash '{B}192.168.1.214{B}e'",

             str(me / "P1"), B + "192.168.1.214" + B + "e"),

            ("o 2 tro vao mot FILE", str(me / "P1"), str(mot_file)),

            ("o 2 la chinh thu muc cong cu", str(me / "P1"), str(ROOT)),

        ]

        for ten, d, o in canh:

            goi.clear()

            that.clear()

            g.v_draft.set(d)

            g.v_out.set(o)

            g.v_do.set("")

            g._bat_dau()

            check(f"CHAN: {ten}", bool(goi) and not that,

                  f"hop thoai={goi}, so thread khoi dong={len(that)}")



        # Duong hop le PHAI cho chay

        goi.clear()

        that.clear()

        g.v_draft.set(str(me / "P1"))

        g.v_out.set(str(tmp / "RA"))

        g.v_do.set(str(tmp))

        g._bat_dau()

        check("CHO CHAY: draft that + o 2 tuyet doi", len(that) == 1 and not goi,

              f"hop thoai={goi}, so thread={len(that)}")

    finally:

        giao_dien.threading.Thread = cu_thread

        try:

            root.destroy()

        except Exception:

            pass

        shutil.rmtree(tmp, ignore_errors=True)





def test_dan_vao_o():

    """Dan duoc bang Ctrl+V, Ctrl+Shift+V va menu chuot phai - DUNG 1 LAN."""

    print()

    print("=" * 72)

    print("Dan vao o: Ctrl+V / Ctrl+Shift+V / menu chuot phai")

    print("=" * 72)

    if not co_tkinter():

        print("  (khong co tkinter -> bo qua)")

        return

    import tkinter as tk

    import giao_dien



    root = _nho(tk.Tk())

    # KHONG withdraw(): cua so an thi Tk khong giao su kien ban phim va MOI

    # phep do ra False - duong tinh gia. Dat ra ngoai man hinh thay vi an.

    root.geometry("500x400+4000+4000")

    try:

        g = _nho(giao_dien.GiaoDien(root))

        root.update()



        check("o co menu chuot phai", g.e_draft.bind("<Button-3>") != "",

              "tkinter KHONG co san menu ngu canh cho Entry; thieu no thi bam"

              " chuot phai de dan (phan xa cua nguoi Windows) khong ra gi")



        ms = [w for w in g.e_draft.winfo_children() if isinstance(w, tk.Menu)]

        check("menu co ton tai", bool(ms))

        if not ms:

            return

        m = ms[0]

        nhan = [m.entrycget(i, "label") for i in range(m.index("end") + 1)

                if m.type(i) == "command"]

        check("menu co du Dan/Chep/Cat/Chon het/Xoa het",

              all(x in nhan for x in ("Dan", "Chep", "Cat", "Chon het",

                                      "Xoa het")), str(nhan))



        root.clipboard_clear()

        root.clipboard_append("D:/PASTE")

        root.update()



        # menu "Dan" phai DE LEN chuoi cu, khong noi duoi

        g.e_draft.delete(0, "end")

        g.e_draft.insert(0, "E:/CU")

        root.update()

        m.invoke(m.index("Dan"))

        root.update()

        check("menu Dan DE LEN chuoi cu (khong noi duoi)",

              g.e_draft.get() == "D:/PASTE", repr(g.e_draft.get()))



        # KHONG dung event_generate("<Button-3>"): tk_popup chan ham xu ly hang

        # chuc giay khi khong co chuot that -> bo kiem trong nhu bi treo.

        for phim in ("<Control-Key-v>", "<Control-Shift-Key-V>",

                     "<Control-Lock-Key-V>"):

            g.e_draft.delete(0, "end")

            g.e_draft.focus_force()

            root.update()

            g.e_draft.event_generate(phim)

            root.update()

            v = g.e_draft.get()

            check(f"{phim} dan DUNG 1 lan", v == "D:/PASTE",

                  "DAN HAI LAN (bind_all?)" if v == "D:/PASTE" * 2 else repr(v))

    finally:

        try:

            root.destroy()

        except Exception:

            pass





def test_dong_cua_so_khong_de_lai_rac():

    """Dong giao dien phai IM LANG tuyet doi tren stderr.



    Nhip dap `after(80, _rut_hang_doi)` tu dat lai moi 80ms. Neu cua so bi huy

    ma khong huy nhip, Tcl con mot hen gio tro toi mot lenh vua bi xoa va in

    `invalid command name "..._rut_hang_doi"` ra stderr luc thoat.



    Vi sao dieu nay QUAN TRONG chu khong phai rac vo hai: duoi `pythonw.exe`

    (dung lenh trong GIAO_DIEN.bat) `sys.stderr` la `_KhongDau`, va no ghi moi

    thu vao `_LOI_GIAO_DIEN.log`. Nguoi dung mo file ten "LOI" ra thay day loi

    Tcl kho hieu sau MOI lan dong cong cu - trong khi khong co gi hong ca. Mot

    file bao loi keu oan thi lan sau co loi that se khong ai tin nua.

    """

    print()

    print("=" * 72)

    print("Dong giao dien: stderr phai SACH")

    print("=" * 72)

    if not co_tkinter():

        print("  (khong co tkinter -> bo qua)")

        return



    than = """

import sys, os

sys.path.insert(0, sys.argv[1]); os.chdir(sys.argv[1])

import tkinter as tk

import giao_dien

for _ in range(3):

    r = tk.Tk(); r.withdraw()

    g = giao_dien.GiaoDien(r)

    r.update()

    r.destroy()          # huy THANG, khong qua nut X - dung nhu bo kiem lam

print("XONG")

"""

    ma, ra = _chay_con(than, gio=120)

    check("chay xong", ma == 0 and "XONG" in ra, ra[-600:])

    check("stderr KHONG co 'invalid command name'",

          "invalid command name" not in ra,

          "nhip dap chua duoc huy khi cua so bi destroy\n" + ra[-600:])

    check("khong co rac 'after script'", 'after" script' not in ra, ra[-400:])





def test_khong_io_treo_tren_thread_chinh():

    """`_bat_dau()` chay tren THREAD CHINH - khong duoc goi I/O co the treo.



    Mot loi goi `isdir_safe` vao host SMB khong noi duoc chan 11-21 giay (do

    that). Trong 21 giay do cua so hien "Not Responding" va nut "Dung do" dang

    XAM, tuc la nguoi dung khong co duong thoat nao. Cung hinh thai bug #58.



    Voi duong dan UNC, phep kiem truoc phai duoc BO QUA de loi no o thread phu.

    """

    print()

    print("=" * 72)

    print("_bat_dau khong duoc goi I/O co the treo tren thread chinh")

    print("=" * 72)

    if not co_tkinter():

        print("  (khong co tkinter -> bo qua)")

        return

    import tkinter as tk

    import giao_dien

    B = chr(92)



    K = giao_dien.GiaoDien._kiem_nhanh_duoc

    for t, mong in ((B * 2 + "192.168.1.214" + B + "e", False),

                    ("//localhost/C$", False),

                    ('"' + B * 2 + 'NAS' + B + 'x"', False),

                    ("D:" + B + "a", True), ("C:" + B, True)):

        check(f"kiem nhanh {t!r} -> {mong}", K(t) is mong, f"ra {K(t)}")



    # Dem so lan cham vao filesystem khi ba o deu la UNC

    root = _nho(tk.Tk())

    root.withdraw()

    goi = []

    cu_dir, cu_file = giao_dien.isdir_safe, giao_dien.isfile_safe

    try:

        g = _nho(giao_dien.GiaoDien(root))

        giao_dien.isdir_safe = lambda p: (goi.append(("dir", str(p))), False)[1]

        giao_dien.isfile_safe = lambda p: (goi.append(("file", str(p))), False)[1]

        giao_dien.messagebox.showerror = lambda *a, **k: None

        giao_dien.messagebox.showwarning = lambda *a, **k: None

        giao_dien.messagebox.askyesno = lambda *a, **k: False



        g.v_draft.set(B * 2 + "192.168.1.214" + B + "e" + B + "DU_AN")

        g.v_out.set(B * 2 + "192.168.1.214" + B + "e" + B + "GOI")

        g.v_do.set(B * 2 + "192.168.1.214" + B + "e" + B + "KHO")

        g._bat_dau()

        unc = [x for x in goi if x[1].lstrip('"').startswith(B * 2)]

        check("KHONG cham filesystem lan nao voi duong dan UNC", not unc,

              f"{len(unc)} lan cham: {unc[:3]}"

              " -> NAS chet se dong bang giao dien 11-21 giay")

    finally:

        giao_dien.isdir_safe, giao_dien.isfile_safe = cu_dir, cu_file

        try:

            root.destroy()

        except Exception:

            pass





def test_quet_thu_muc_me_khong_chan_thread_chinh():
    """#96: quet phai chay o THREAD PHU.

    Do duoc truoc khi sua: dong bang mainloop 19,6 giay tren o mang, Windows
    dan nhan "Not Responding" 14,6 giay, MOI cu bam nut bi hoan 19,3 giay - ke
    ca nut X. Cung hinh thai #58.

    Do bang SO NHIP `after` chay duoc trong luc quet, KHONG bang giay: neu
    thread chinh bi chan thi khong mot nhip nao chay, va con so do khong doi
    theo toc do may.

    CHAY O TIEN TRINH RIENG - xem chu thich o `test_ket_qua_quet_cu...`.
    """
    print()
    print("=" * 72)
    print("#96  quet thu muc me KHONG duoc chan thread chinh")
    print("=" * 72)
    if not co_tkinter():
        print("  (khong co tkinter -> bo qua)")
        return

    than = """
import json, os, sys, threading, time
sys.path.insert(0, sys.argv[1]); os.chdir(sys.argv[1])
sys.path.insert(0, os.path.join(sys.argv[1], "tests"))
import tkinter as tk
import giao_dien

root = tk.Tk(); root.withdraw()
g = giao_dien.GiaoDien(root)
vao = threading.Event()
cho = threading.Event()

def quet_cham(parent, max_depth=3, nen_dung=None, on_error=None):
    vao.set()
    cho.wait(20)                      # gia lam mot loi goi I/O cham
    return [], 0, bool(nen_dung and nen_dung())

giao_dien.G.scan_drafts_recursive = quet_cham
giao_dien.filedialog.askdirectory = lambda **kw: sys.argv[1]

nhip = [0]
id_dem = [None]
def dem():
    nhip[0] += 1
    id_dem[0] = root.after(20, dem)
id_dem[0] = root.after(20, dem)

kq = {}
g._quet_thu_muc_me()
kq["da vao ham quet"] = vao.wait(10)

t0 = time.time()
while time.time() - t0 < 1.0:
    root.update(); time.sleep(0.02)
kq["thread chinh VAN CHAY trong luc quet"] = nhip[0] >= 10
kq["_nhip"] = nhip[0]
kq["nut QUET bi xam trong luc quet"] = str(g.nut_quet["state"]) == "disabled"
kq["nut Dung doi nhan sang 'Dung quet'"] = "quet" in str(g.nut_dung["text"]).lower()

g._dung_do()
kq["bam Dung khi dang quet -> dat co_huy_quet"] = g.co_huy_quet.is_set()
kq["KHONG dung nham co cua pha goi"] = not g.co_huy.is_set()

cho.set()
t0 = time.time()
while g.dang_quet and time.time() - t0 < 10:
    root.update(); time.sleep(0.02)
kq["quet ket thuc, ve trang thai san sang"] = not g.dang_quet
kq["nut QUET duoc bat lai"] = str(g.nut_quet["state"]) == "normal"

if id_dem[0] is not None:
    root.after_cancel(id_dem[0])
root.destroy()
print("KETQUA" + json.dumps(kq))
"""
    ma, ra = _chay_con(than, gio=120)
    dong = [l for l in ra.splitlines() if l.startswith("KETQUA")]
    if not dong:
        check("chay duoc phep kiem quet", False, ra[-1200:])
        return
    kq = json.loads(dong[0][6:])
    print(f"    thread chinh chay {kq.pop('_nhip', '?')} nhip trong 1 giay"
          f" khi dang quet")
    for ten, ok in kq.items():
        check(ten, ok,
              "quet van dang chan thread chinh" if "VAN CHAY" in ten else
              "dung chung co thi `_bat_dau` se xoa nham va HOI SINH thread quet"
              if "nham co" in ten else "")


def test_ket_qua_quet_cu_khong_duoc_de_len_moi():
    """Huy KHONG cat duoc loi goi I/O dang chay, nen ket qua phien CU van se ve
    - chi la ve muon. Khong danh so phien thi no de len danh sach phien moi.

    CHAY O TIEN TRINH RIENG: bo kiem nay tao them mot root Tk, va do duoc rang
    them dung MOT root nua vao tien trinh da co 13 cai la du lam Tcl bo ra
    `Tcl_AsyncDelete: async handler deleted by the wrong thread` luc thoat -
    loi giet ca tien trinh, xoa luon dong "KET QUA". Chay rieng le thi khong
    cai nao crash; chinh SO LUONG root moi la nguyen nhan.
    """
    print()
    print("=" * 72)
    print("#96  ket qua phien quet CU ve muon phai bi BO")
    print("=" * 72)
    if not co_tkinter():
        print("  (khong co tkinter -> bo qua)")
        return

    than = """
import json, os, sys
sys.path.insert(0, sys.argv[1]); os.chdir(sys.argv[1])
import tkinter as tk
import giao_dien
from pathlib import Path

root = tk.Tk(); root.withdraw()
g = giao_dien.GiaoDien(root)
kq = {}
g.phien_quet = 7
g.dang_quet = True

# Ket qua phien 3 (CU) ve muon -> phai bi bo
g.hd.put(("quet_xong", (3, "D:/CU", [Path("D:/CU/P1")], 0, False)))
g._rut_hang_doi(); root.update()
kq["ket qua phien CU bi bo qua"] = (g.drafts == [])
kq["van dang o trang thai quet"] = (g.dang_quet is True)

# Ket qua phien HIEN TAI -> phai nhan
g.hd.put(("quet_xong", (7, "D:/MOI", [Path("D:/MOI/P9")], 0, False)))
g._rut_hang_doi(); root.update()
kq["ket qua phien HIEN TAI duoc nhan"] = (len(g.drafts) == 1)
kq["thoat trang thai quet"] = (g.dang_quet is False)

# Bao loi doc thu muc KHONG duoc nuot (#37)
g.phien_quet = 9
g.dang_quet = True
g.hd.put(("quet_xong", (9, "D:/X", [], 4, False)))
g._rut_hang_doi(); root.update()
van = g.log.get("1.0", "end")
kq["so thu muc khong doc duoc phai duoc BAO RA"] = ("4 thu muc khong doc duoc" in van)
kq["noi ro danh sach co the THIEU"] = ("THIEU project" in van)

root.destroy()
print("KETQUA" + json.dumps(kq))
"""
    ma, ra = _chay_con(than, gio=120)
    dong = [l for l in ra.splitlines() if l.startswith("KETQUA")]
    if not dong:
        check("chay duoc phep kiem so phien", False, ra[-1200:])
        return
    for ten, ok in json.loads(dong[0][6:]).items():
        check(ten, ok, "")


def test_quet_khong_nuot_loi_va_huy_duoc():
    """`scan_drafts_recursive`: huy duoc + KHONG nuot loi (#37).
    Khong tao Tk nen chay thang duoc."""
    print()
    print("=" * 72)
    print("#96  scan_drafts_recursive: huy duoc + khong nuot loi")
    print("=" * 72)
    import goi_project_capcut as G
    from chung import mtime_an_toan

    tmp = Path(tempfile.mkdtemp(prefix="quet96_"))
    try:
        for i in range(60):
            (tmp / f"p{i:03d}").mkdir(parents=True)
            # PHAI co CA HAI: `is_draft_dir` doi draft_content.json VA
            # draft_meta_info.json. Thieu mot cai thi bo kiem xanh rong -
            # `scan_drafts_recursive` tra ve 0 project ma van "dat".
            for _t in ("draft_content.json", "draft_meta_info.json"):
                (tmp / f"p{i:03d}" / _t).write_text("{}", encoding="utf-8")

        cu = G.scan_drafts_recursive(tmp)
        check("goi kieu CU van tra ve list tran", isinstance(cu, list),
              f"tra ve {type(cu).__name__} - duong dong lenh se vo")
        check("tim du project", len(cu) == 60, f"tim thay {len(cu)}")

        ds, n_loi, huy = G.scan_drafts_recursive(
            tmp, nen_dung=lambda: False, on_error=lambda ls: None)
        check("goi kieu MOI tra ve (list, so_loi, da_dung)",
              isinstance(ds, list) and n_loi == 0 and huy is False,
              f"{type(ds).__name__}, {n_loi}, {huy}")

        ds2, _, huy2 = G.scan_drafts_recursive(tmp, nen_dung=lambda: True)
        check("huy tu dau -> dung NGAY, truoc ca isdir_safe",
              ds2 == [] and huy2 is True, f"{len(ds2)} project, huy={huy2}")

        dem = [0]

        def nd():
            dem[0] += 1
            return dem[0] > 3
        ds3, _, huy3 = G.scan_drafts_recursive(tmp, nen_dung=nd)
        check("huy giua chung -> it hon quet het",
              huy3 is True and len(ds3) < 60,
              f"{len(ds3)} project (quet het la 60), huy={huy3}")

        # PHAI dung mot thu muc CO THAT va DAI hon 260 ky tu. Kiem tren duong
        # dan khong ton tai la bo kiem XANH RONG: `os.stat()` tran cung nem o
        # do, nen ban vá va ban chua vá cho ket qua GIONG NHAU. Phep thu dot
        # bien da bat duoc dung lo hong nay.
        from chung import _lp
        sau = tmp
        for _ in range(8):
            sau = sau / ("d" * 40)
        os.makedirs(_lp(str(sau)), exist_ok=True)
        dai = len(str(sau))
        check(f"da dung duoc thu muc that dai {dai} ky tu", dai > 260,
              "khong du dai thi phep kiem nay VO NGHIA")
        check("mtime_an_toan DOC DUOC thu muc that dai hon 260 ky tu",
              mtime_an_toan(sau) > 0,
              "`Path.stat()` tran nem WinError 3 o day - va mot `sorted()` nem"
              " giua chung se VUT SACH ca danh sach project vua quet duoc")
        check("mtime_an_toan tra 0.0 (khong NEM) khi that su khong co",
              mtime_an_toan(tmp / ("z" * 200) / ("y" * 200)) == 0.0)
        check("sorted bang mtime_an_toan KHONG nem",
              isinstance(sorted(cu + [tmp / ("q" * 250)], key=mtime_an_toan),
                         list),
              "day chinh la cho lam VUT SACH danh sach vua quet duoc")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_chot_tinh_chong_tai_phat():

    """Chot TINH - re, khong can Tk, chan loi root lac quay lai."""

    print()

    print("=" * 72)

    print("Chot tinh: khong duoc tao widget/bien tkinter truoc khi co tk.Tk()")

    print("=" * 72)

    import ast

    import re

    src = (ROOT / "giao_dien.py").read_text(encoding="utf-8")



    # Doc bang AST chu KHONG bang chuoi: chuoi "ttk.Style()" con nam trong

    # chinh cac comment giai thich cai bay nay. Bo kiem bao dong khi khong co

    # loi thi som muon cung bi tat di.

    cay0 = ast.parse(src)

    tran = [nut.lineno for nut in ast.walk(cay0)

            if isinstance(nut, ast.Call)

            and isinstance(nut.func, ast.Attribute) and nut.func.attr == "Style"

            and isinstance(nut.func.value, ast.Name) and nut.func.value.id == "ttk"

            and not nut.args and not nut.keywords]

    check("khong con `ttk.Style()` tran (khong master)", not tran,

          f"o dong {tran}: ttk.Style() khi CHUA co tk.Tk() se TU TAO mot root"

          " Tk lac - moi bien khong master bam nham interpreter -> 3 o duong"

          " dan chet, va mainloop() cua cua so tu kiem khong bao gio tra ve.")



    thieu = [m.group(0) for m in

             re.finditer(r"tk\.(?:String|Boolean|Int|Double)Var\(([^)]*)\)", src)

             if "master=" not in m.group(1)]

    check("moi bien tkinter deu co master=", not thieu,

          f"con {len(thieu)} bien thieu: {thieu}")



    check("3 o Entry duoc gan vao self",

          all(f"self.e_{t} = ttk.Entry(" in src for t in ("draft", "out", "do")),

          "Entry an danh -> moi ban va cham toi self.e_* se AttributeError, va"

          " duoi pythonw thi loi do IM LANG hoan toan")



    # parent= cho moi hop thoai - dem bang AST vi 6/10 loi goi trai nhieu dong

    cay = ast.parse(src)

    tong, thieu_p = 0, []

    for nut in ast.walk(cay):

        if (isinstance(nut, ast.Call) and isinstance(nut.func, ast.Attribute)

                and isinstance(nut.func.value, ast.Name)

                and nut.func.value.id in ("filedialog", "messagebox")):

            tong += 1

            if "parent" not in [k.arg for k in nut.keywords]:

                thieu_p.append((nut.lineno,

                                nut.func.value.id + "." + nut.func.attr))

    check("da quet duoc it nhat 10 hop thoai", tong >= 10, f"chi thay {tong}")

    check("moi hop thoai deu ghim parent=", not thieu_p, str(thieu_p))





def main():

    test_khong_viet_lai_logic()

    test_chot_tinh_chong_tai_phat()

    test_dong_cua_so_khong_de_lai_rac()

    test_khong_io_treo_tren_thread_chinh()
    test_quet_thu_muc_me_khong_chan_thread_chinh()
    test_ket_qua_quet_cu_khong_duoc_de_len_moi()
    test_quet_khong_nuot_loi_va_huy_duoc()

    test_tuy_chon_di_vao_opts()

    test_tra_loi_theo_noi_dung()

    test_lam_sach_ds_duong_dan()

    test_o_duong_dan_hien_that()

    test_lan_dau_khong_treo()

    test_dan_vao_o()

    test_bat_dau_phai_chan_dau_vao_xau()

    test_chay_tron_mot_luot()

    print()

    print("=" * 72)

    print(f"KET QUA: {pas} PASS / {fail} FAIL")

    print("=" * 72)

    return 1 if fail else 0





if __name__ == "__main__":
    _ma = main()
    # THOAT NGAY, bo qua giai doan don dep cua Python.
    #
    # Bo kiem nay tao hon muoi root Tk trong CUNG MOT tien trinh (app that chi
    # tao MOT). Luc thoat, Python thu gom cac bien tkinter con lai trong khi
    # interpreter Tcl da bi huy, va Tcl bo ra
    #     Tcl_AsyncDelete: async handler deleted by the wrong thread
    # - loi GIET CA TIEN TRINH, xoa luon dong "KET QUA" vua in, khien
    # `chay_het.py` bao THAT BAI du moi phep kiem deu dat.
    #
    # Nguong tran KHAC NHAU theo ban Python va con NGAU NHIEN theo thoi diem
    # thu gom rac: Python he thong thi qua, ban DI KEM (thu ban may con dung)
    # thi chet - va khong phai lan nao cung chet. Do dung la ly do buoc dong
    # goi luon chay lai ca bo kiem bang ban Python di kem.
    #
    # Da thu va KHONG du: huy `after` con treo; giu tham chieu de don tren
    # thread chinh; tach cac phep kiem nang sang tien trinh rieng (van giu, vi
    # do la cach lam dung). `os._exit` bo qua han giai doan don dep - nhung
    # PHAI flush truoc, neu khong ket qua vua in se mat theo.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(_ma)
