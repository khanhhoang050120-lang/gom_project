# -*- coding: utf-8 -*-
"""Canh gac phai bat duoc TREO THAT va TUYET DOI khong bao dong gia.

Vi sao bo kiem nay kho hon ve ngoai:
  Muc #25 trong bug.md da bao dong gia HAI lan roi. Mot canh gac keu oan con
  te hon khong co canh gac: nguoi dung se hoc cach phot lo no, va lan treo
  THAT se khong ai tin. Vi vay o day so phep kiem cho "KHONG duoc bao" nhieu
  hon so phep kiem cho "phai bao".

Cach do: KHONG cho 15 phut that. Bom dong ho gia + cam bien gia, roi goi
`_mot_nhip()` truc tiep. Nho vay bo kiem chay trong mili giay va tai lap duoc
100%, thay vi phu thuoc thoi gian that.
"""
from __future__ import annotations

import ast
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for _p in (str(ROOT), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

pas = fail = 0


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


class DongHoGia:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def toi(self, giay):
        self.t += giay


class CamBienGia:
    """Cam bien gia: ta tu quyet dinh moi nhip 'lam duoc bao nhieu viec'."""

    def __init__(self):
        self.m = {"byte_doc": 0, "byte_ghi": 0, "thao_tac": 0, "cpu": 0.0,
                  "so_tien_trinh": 1}

    def them(self, byte_doc=0, byte_ghi=0, thao_tac=0, cpu=0.0):
        self.m = dict(self.m)
        self.m["byte_doc"] += byte_doc
        self.m["byte_ghi"] += byte_ghi
        self.m["thao_tac"] += thao_tac
        self.m["cpu"] += cpu

    def doc(self):
        return dict(self.m)


def tao_gac(CG, log=None):
    dh = DongHoGia()
    g = CG.CanhGac(log=log or (lambda *a: None), dong_ho=dh)
    cb = CamBienGia()
    g.do = cb
    g.lich_su = [(dh(), cb.doc())]
    return g, cb, dh


def chay_phut(g, cb, dh, phut, moi_nhip):
    """Chay `phut` phut, moi nhip 30 giay goi `moi_nhip(cb)` roi lay mau."""
    for _ in range(int(phut * 60 / g.chu_ky)):
        moi_nhip(cb)
        dh.toi(g.chu_ky)
        g._mot_nhip()


# ------------------------------------------------------------------ T1
def t1_treo_that_phai_bao():
    print()
    print("=" * 72)
    print("T1  TREO THAT -> phai canh bao o 5 phut, nghi treo o 15 phut")
    print("=" * 72)
    import canh_gac as CG

    dong = []
    g, cb, dh = tao_gac(CG, log=dong.append)

    # Treo hoan toan: khong lam gi ca
    chay_phut(g, cb, dh, 4, lambda c: None)
    check("4 phut: CHUA bao gi", g.da_bao == 0, f"da_bao={g.da_bao}")

    chay_phut(g, cb, dh, 2, lambda c: None)
    check("6 phut: da CANH BAO (chua ket luan)", g.da_bao == 1,
          f"da_bao={g.da_bao}")
    van = "\n".join(dong)
    check("canh bao noi ro chua chac (co the binh thuong)",
          "co the" in van.lower(), van[-500:])

    chay_phut(g, cb, dh, 10, lambda c: None)
    check("16 phut: da ket luan NGHI TREO", g.da_bao == 2, f"da_bao={g.da_bao}")
    van = "\n".join(dong)
    check("noi ro BAN QUYET DINH, tool khong tu dung",
          "BAN QUYET DINH" in van and "KHONG tu dong dung" in van, van[-800:])


# ------------------------------------------------------------------ T2
def t2_dang_chay_khong_duoc_bao():
    """Bon dang 'dang chay' - moi dang deu tung lam mot tin hieu don le SAI."""
    print()
    print("=" * 72)
    print("T2  DANG CHAY -> TUYET DOI khong duoc bao (4 dang, deu do that)")
    print("=" * 72)
    import canh_gac as CG

    canh = [
        ("pha ma hoa (doc nhieu byte, CPU cao)",
         lambda c: c.them(byte_doc=200 * 2**20, cpu=25.0)),
        # Pha quet metadata NAS: byte doc/ghi gan nhu 0, CHI Other* nhuc nhich.
        # Tin hieu 'chi doc read+write byte' se bao oan o day.
        ("pha quet metadata NAS (chi Other*, 0 byte doc/ghi)",
         lambda c: c.them(byte_doc=1600 * 1024, thao_tac=49000)),
        # Pha copy len NAS: chuyen byte ao at nhung gan nhu khong ton CPU.
        # Tin hieu 'chi doc CPU' se bao oan o day.
        ("pha copy len NAS (nhieu byte, CPU ~0)",
         lambda c: c.them(byte_ghi=40 * 2**20, cpu=0.05)),
        # Clip rat dai: khong clip nao xong, nhung ffmpeg van doc file.
        ("clip 25 phut (khong clip nao xong suot ca window)",
         lambda c: c.them(byte_doc=80 * 2**20, cpu=28.0)),
        # CHI CPU nhuc nhich, byte DUOI nguong: pha quet metadata tren o CUC BO
        # (do that: +2,09 s CPU trong 3 giay ma gan nhu khong chuyen byte).
        # Bo tin hieu CPU la bao oan o day.
        ("pha metadata o CUC BO (CHI CPU, byte duoi nguong)",
         lambda c: c.them(byte_doc=1024, byte_ghi=1024, thao_tac=10, cpu=20.0)),
        # CHI so THAO TAC nhuc nhich: hoi metadata qua SMB, moi lan chi 48 byte
        # nen ca window van duoi nguong byte, nhung so thao tac thi rat lon.
        # Bo tin hieu thao_tac la bao oan o day.
        ("hoi metadata qua SMB (CHI thao tac, byte + CPU duoi nguong)",
         lambda c: c.them(byte_doc=48 * 300, thao_tac=9000, cpu=0.02)),
    ]
    for ten, viec in canh:
        import canh_gac as CG2
        g, cb, dh = tao_gac(CG2)
        chay_phut(g, cb, dh, 20, viec)
        check(f"20 phut {ten}: KHONG bao", g.da_bao == 0,
              f"da_bao={g.da_bao} -> BAO DONG GIA, dung loai #25 da mac 2 lan")


# ------------------------------------------------------------------ T3
def t3_nhip_dap_khong_duoc_lam_mu():
    """Cai bay NANG NHAT: nhip dap cua chinh tool ghi ra NAS moi 60 giay."""
    print()
    print("=" * 72)
    print("T3  TREO nhung nhip dap van ghi -> VAN phai bat duoc")
    print("=" * 72)
    import canh_gac as CG

    g, cb, dh = tao_gac(CG)
    # Do that luc treo: bo dem GHI van tang ~49 byte/giay, va vai thao tac.
    # Luat "co thay doi = con song" se KHONG BAO GIO kich hoat o day.
    chay_phut(g, cb, dh, 16,
              lambda c: c.them(byte_ghi=49 * 30, thao_tac=6))
    check("nhip dap 49 byte/giay KHONG cuu duoc khoi ket luan treo",
          g.da_bao == 2,
          f"da_bao={g.da_bao} -> canh gac bi chinh nhip dap cua tool lam mu,"
          " se im lang vinh vien tren tool that")

    # Doi chung: chi can them mot chut viec THAT la khong bao nua
    g2, cb2, dh2 = tao_gac(CG)
    chay_phut(g2, cb2, dh2, 16,
              lambda c: c.them(byte_ghi=49 * 30, thao_tac=6,
                               byte_doc=CG.NG_BYTE_DOC + 1))
    check("DOI CHUNG: them viec that thi KHONG bao", g2.da_bao == 0,
          f"da_bao={g2.da_bao}")


# ------------------------------------------------------------------ T4
def t4_hoi_phuc():
    print()
    print("=" * 72)
    print("T4  treo roi chay lai -> phai BO canh bao, khong ket luan bua")
    print("=" * 72)
    import canh_gac as CG

    dong = []
    g, cb, dh = tao_gac(CG, log=dong.append)
    chay_phut(g, cb, dh, 7, lambda c: None)
    check("da canh bao", g.da_bao >= 1, f"da_bao={g.da_bao}")
    chay_phut(g, cb, dh, 4, lambda c: c.them(byte_doc=200 * 2**20, cpu=25.0))
    check("chay lai thi bo canh bao", g.da_bao == 0, f"da_bao={g.da_bao}")
    check("co noi ra la da co tien trien tro lai",
          any("tien trien tro lai" in d for d in dong), "\n".join(dong)[-400:])


# ------------------------------------------------------------------ T5
def t5_khong_cham_filesystem():
    """Than canh gac cham vao dia = dung luc can no nhat, no ket theo."""
    print()
    print("=" * 72)
    print("T5  than canh gac KHONG duoc goi bat ky ham filesystem nao")
    print("=" * 72)
    src = (ROOT / "canh_gac.py").read_text(encoding="utf-8")
    cay = ast.parse(src)

    CAM = {"open", "listdir", "scandir", "walk", "stat", "remove", "rename",
           "replace", "copy", "copy2", "copytree", "rmtree", "mkdir",
           "makedirs", "unlink", "getsize", "isfile", "isdir", "exists"}
    xau = []
    for nut in ast.walk(cay):
        if isinstance(nut, ast.Call):
            f = nut.func
            ten = (f.attr if isinstance(f, ast.Attribute)
                   else (f.id if isinstance(f, ast.Name) else ""))
            if ten in CAM:
                xau.append(f"dong {nut.lineno}: {ten}()")
    check("khong goi ham filesystem nao", not xau, "\n".join(xau))

    nap = set()
    for nut in ast.walk(cay):
        if isinstance(nut, ast.Import):
            nap |= {a.name.split(".")[0] for a in nut.names}
        elif isinstance(nut, ast.ImportFrom) and nut.module:
            nap.add(nut.module.split(".")[0])
    check("chi nap thu vien chuan, khong nap module cua tool",
          not (nap & {"chung", "goi_project_capcut", "toi_uu_dung_luong"}),
          f"nap {sorted(nap)} - nap module cua tool la keo theo ca I/O cua chung")
    check("khong import os / shutil / pathlib",
          not (nap & {"os", "shutil", "pathlib"}), f"nap {sorted(nap)}")


# ------------------------------------------------------------------ T6
def t6_khong_tu_giet():
    print()
    print("=" * 72)
    print("T6  canh gac KHONG duoc tu giet tien trinh")
    print("=" * 72)
    src = (ROOT / "canh_gac.py").read_text(encoding="utf-8")
    cay = ast.parse(src)
    xau = []
    for nut in ast.walk(cay):
        if isinstance(nut, ast.Call):
            f = nut.func
            ten = (f.attr if isinstance(f, ast.Attribute)
                   else (f.id if isinstance(f, ast.Name) else ""))
            if ten in {"_exit", "exit", "kill", "terminate", "abort",
                       "TerminateProcess", "TerminateJobObject"}:
                xau.append(f"dong {nut.lineno}: {ten}()")
    check("khong co loi goi giet tien trinh nao", not xau,
          "\n".join(xau) + "\n#25 da tu choi phuong an tu giet:"
          " giet nham mot job 3 tieng te hon mot canh bao co the la gia")


# ------------------------------------------------------------------ T7
def t7_cam_bien_that():
    print()
    print("=" * 72)
    print("T7  cam bien THAT tren may nay (khong phai cam bien gia)")
    print("=" * 72)
    import canh_gac as CG

    g = CG.CanhGac(log=lambda *a: None)
    ok = g.bat_dau()
    check("bat duoc canh gac", ok, "khong bat duoc -> khong co canh bao treo")
    if not ok:
        return
    try:
        print(f"    cach do dang dung: {g.cach}")
        check("dung Job Object (chinh xac 100%)", g.cach == "job",
              f"dang dung '{g.cach}' - do cay bo sot 74-96% I/O cua ffmpeg"
              " (tien trinh ngan sinh-va-chet giua hai lan lay mau)")
        a = g.do.doc()
        check("doc duoc mau", a is not None)
        # Lam mot viec that: doc chinh file nay nhieu lan
        d = (ROOT / "canh_gac.py").read_bytes()
        for _ in range(400):
            d = (ROOT / "goi_project_capcut.py").read_bytes()
        b = g.do.doc()
        check("lam viec that -> vuot nguong", CG.CanhGac._dat_nguong(a, b),
              f"delta byte_doc={b['byte_doc']-a['byte_doc']}"
              f" thao_tac={b['thao_tac']-a['thao_tac']}"
              f" cpu={b['cpu']-a['cpu']:.2f}")
        c1 = g.do.doc()
        time.sleep(3)
        c2 = g.do.doc()
        check("ngu 3 giay -> DUOI nguong", not CG.CanhGac._dat_nguong(c1, c2),
              f"delta {[c2[k]-c1[k] for k in ('byte_doc','byte_ghi','thao_tac')]}")
    finally:
        g.dung()


# ------------------------------------------------------------------ T8
def t8_main_luon_tat_canh_gac():
    """`main()` co 13 duong return. O che do giao dien tien trinh KHONG thoat,
    nen mot canh gac quen tat se bao dong khong sau 5 phut giao dien nam im."""
    print()
    print("=" * 72)
    print("T8  main() phai LUON tat canh gac (13 duong return)")
    print("=" * 72)
    src = (ROOT / "goi_project_capcut.py").read_text(encoding="utf-8")
    cay = ast.parse(src)
    fn = next((x for x in cay.body
               if isinstance(x, ast.FunctionDef) and x.name == "main"), None)
    check("co ham main()", fn is not None)
    if fn is None:
        return
    co_finally = any(isinstance(x, ast.Try) and x.finalbody
                     for x in ast.walk(fn))
    check("main() dung try/finally de bao dam tat", co_finally,
          "va tung duong return mot thi som muon se sot mot duong")
    check("main() chi la vo mong", fn.end_lineno - fn.lineno < 40,
          f"main() dai {fn.end_lineno - fn.lineno} dong - than phai o ham khac")
    check("than that nam o _main_than", "def _main_than(" in src)

    # Chay THAT: goi main() roi kiem thread canh gac da chet chua
    con = (
        "import sys, threading, time\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "import goi_project_capcut as G\n"
        "import builtins\n"
        "builtins.input = lambda *a: (_ for _ in ()).throw(EOFError())\n"
        "try:\n"
        "    G.main()\n"
        "except BaseException:\n"
        "    pass\n"
        "time.sleep(0.5)\n"
        "con = [t.name for t in threading.enumerate() if t.name == 'canh_gac']\n"
        "print('CANH_GAC_CON_SONG:', bool(con))\n"
    )
    tmp = Path(tempfile.mkdtemp(prefix="cg_main_"))
    try:
        f = tmp / "con.py"
        f.write_text(con, encoding="utf-8")
        r = subprocess.run([sys.executable, str(f), str(ROOT)],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=180, cwd=str(ROOT))
        ra = (r.stdout or "") + (r.stderr or "")
        check("sau khi main() tra ve, thread canh gac DA CHET",
              "CANH_GAC_CON_SONG: False" in ra, ra[-600:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    t1_treo_that_phai_bao()
    t2_dang_chay_khong_duoc_bao()
    t3_nhip_dap_khong_duoc_lam_mu()
    t4_hoi_phuc()
    t5_khong_cham_filesystem()
    t6_khong_tu_giet()
    t7_cam_bien_that()
    t8_main_luon_tat_canh_gac()
    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
