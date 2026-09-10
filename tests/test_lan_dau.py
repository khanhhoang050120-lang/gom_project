# -*- coding: utf-8 -*-
"""LAN DAU tu kiem, LAN SAU vao thang - va console phai bien mat.

Hai yeu cau cua nguoi dung:
  1. Lan dau bam GIAO_DIEN.bat -> kiem bo cong cu; cac lan sau vao thang giao dien
  2. Khong duoc de cua so den (console) nam sau giao dien

Bo kiem nay chot ca hai, VA chot cac cho de sai:
  - dau kiem phai theo PHIEN BAN (ban moi phai kiem lai)
  - dau HONG = coi nhu chua kiem (khong duoc tin bua)
  - tu kiem that bai thi KHONG duoc ghi dau
  - tu kiem KHONG duoc la lop bao ve duy nhat cho ffmpeg
  - `.bat` phai giu console TRONG LUC KIEM (neu khong moi loi deu im lang)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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


def test_dau_kiem():
    print("=" * 72)
    print("Dau kiem: theo phien ban, hong thi coi nhu chua kiem")
    print("=" * 72)
    import tu_kiem_lan_dau as TK

    tmp = Path(tempfile.mkdtemp(prefix="dau_kiem_"))
    try:
        check("chua co dau -> can kiem", not TK.da_kiem(tmp, "1.1.0"))

        TK.ghi_dau(tmp, "1.1.0", [{"buoc": "x", "dat": True, "chi_tiet": ""}])
        check("ghi dau xong -> khong can kiem nua", TK.da_kiem(tmp, "1.1.0"))

        check("PHIEN BAN KHAC -> phai kiem lai", not TK.da_kiem(tmp, "1.2.0"),
              "ban moi ma dung dau cu thi thay doi ve file/ffmpeg khong bao gio"
              " duoc kiem")

        # Dau HONG
        (tmp / TK.ten_dau("1.1.0")).write_text("{khong phai json", encoding="utf-8")
        check("dau HONG -> coi nhu chua kiem", not TK.da_kiem(tmp, "1.1.0"),
              "tin mot dau hong con nguy hon kiem lai 5 giay")

        # Dau ghi ket qua KHONG DAT
        (tmp / TK.ten_dau("1.1.0")).write_text(
            json.dumps({"phien_ban": "1.1.0", "ket_qua": "HONG"}), encoding="utf-8")
        check("dau ghi 'HONG' -> van phai kiem lai",
              not TK.da_kiem(tmp, "1.1.0"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_khong_ghi_dau_khi_hong():
    print()
    print("=" * 72)
    print("Tu kiem THAT BAI -> KHONG duoc ghi dau")
    print("=" * 72)
    import tu_kiem_lan_dau as TK

    tmp = Path(tempfile.mkdtemp(prefix="hong_"))
    try:
        # Thu muc rong -> thieu het file bat buoc
        dat, ds = TK.chay(tmp)
        check("thu muc rong -> tu kiem BAO HONG", not dat)
        check("noi ro thieu file nao",
              any("THIEU file" in str(x["chi_tiet"]) for x in ds),
              str([x["chi_tiet"] for x in ds])[:200])
        check("khong ghi dau khi hong", not TK.da_kiem(tmp, "1.1.0"),
              "ghi dau khi hong = lan sau bo qua luon van de")

        # Chay het CAC BUOC du buoc dau da hong (de nguoi dung thay het van de)
        check("chay HET cac buoc du buoc dau hong", len(ds) == len(TK.CAC_BUOC),
              f"chi chay {len(ds)}/{len(TK.CAC_BUOC)} buoc -> nguoi dung phai sua"
              " tung cai mot roi chay lai")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_van_kiem_ffmpeg_moi_lan():
    print()
    print("=" * 72)
    print("Tu kiem KHONG duoc la lop bao ve DUY NHAT cho ffmpeg")
    print("=" * 72)
    src = (ROOT / "goi_project_capcut.py").read_text(encoding="utf-8")
    check("main() VAN goi kiem_ffmpeg_chay_duoc moi lan chon che do 4",
          "kiem_ffmpeg_chay_duoc(" in src,
          "neu bo di, ffmpeg bi cach ly SAU lan kiem dau se khong ai bat duoc")
    tk_src = (ROOT / "tu_kiem_lan_dau.py").read_text(encoding="utf-8")
    check("tu_kiem ghi ro no khong phai lop duy nhat",
          "KHONG phai lop bao ve duy nhat" in tk_src,
          "phai ghi ro, neu khong nguoi sau se tuong bo qua duoc kiem o main()")


def test_bat_an_console():
    print()
    print("=" * 72)
    print("GIAO_DIEN.bat: an console nhung KHONG im lang khi loi")
    print("=" * 72)
    b = (ROOT / "GIAO_DIEN.bat").read_bytes()
    van = b.decode("ascii", "replace")

    check("dung pythonw (khong tao console)", "PYW=" in van and "pythonw" in van)
    check("dung `start` de tach tien trinh", "start \"\"" in van)
    check("thoat ngay sau khi bat giao dien (console bien mat)",
          "exit /b 0" in van)
    check("KHONG `pause` o duong chay thanh cong",
          van.index("exit /b 0") < van.index("pause"),
          "pause truoc khi thoat -> console nam lai")
    check("VAN co `pause` o duong bao loi", "pause" in van,
          "khong co thi moi loi deu im lang")
    check("thu `import giao_dien` NGAY trong .bat", "import giao_dien" in van,
          "phai chay THU dung chuoi import ma pythonw se chay, luc console CON"
          " HIEN. Kiem moi `import tkinter` la chua du: tkinter chay duoc ma"
          " `chung.py` hong thi pythonw van chet im lang.")
    check("ASCII thuan", not [x for x in b if x > 127])
    check("CRLF", b.count(b"\r\n") > 0 and b.count(b"\n") == b.count(b"\r\n"))


def test_stdout_none():
    print()
    print("=" * 72)
    print("Duoi pythonw, `sys.stdout` co the la None -> khong duoc chet")
    print("=" * 72)
    src = (ROOT / "giao_dien.py").read_text(encoding="utf-8")
    check("co chot chan sys.stdout is None", "if sys.stdout is None" in src,
          "print() vao None nem AttributeError o cho khong ngo toi")
    check("chot ca sys.stderr", "if sys.stderr is None" in src)

    # Ep sys.stdout = None roi nap module -> khong duoc no
    ma = ("import sys\n"
          "sys.stdout = None\n"
          "sys.stderr = None\n"
          f"sys.path.insert(0, r'{ROOT}')\n"
          "import giao_dien\n"
          "print('VAN PRINT DUOC')\n"
          "sys.__stdout__.write('OK_STDOUT_NONE\\n')\n")
    r = subprocess.run([sys.executable, "-c", ma], capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       timeout=180, cwd=str(ROOT))
    ra = (r.stdout or "") + (r.stderr or "")
    check("nap giao_dien voi stdout=None -> khong nem loi",
          "OK_STDOUT_NONE" in ra, f"ma thoat {r.returncode}\n{ra[-400:]}")


def test_hai_duong_chay():
    print()
    print("=" * 72)
    print("Lan DAU tu kiem, lan SAU vao thang (do bang giay)")
    print("=" * 72)
    import tu_kiem_lan_dau as TK
    import goi_project_capcut as G

    dau = ROOT / TK.ten_dau(G.TOOL_VERSION)
    sao_luu = dau.read_bytes() if dau.is_file() else None
    try:
        if dau.is_file():
            dau.unlink()
        check("da xoa dau -> can tu kiem", not TK.da_kiem(ROOT, G.TOOL_VERSION))

        t = time.time()
        dat, ds = TK.chay(ROOT)
        gio_dau = time.time() - t
        check("tu kiem DAT tren ban that", dat,
              str([x for x in ds if not x["dat"]])[:300])
        print(f"    lan dau : {gio_dau:.1f}s ({len(ds)} buoc)")

        if dat:
            TK.ghi_dau(ROOT, G.TOOL_VERSION, ds)
        check("ghi dau xong -> lan sau bo qua", TK.da_kiem(ROOT, G.TOOL_VERSION))

        t = time.time()
        bo_qua = TK.da_kiem(ROOT, G.TOOL_VERSION)
        gio_sau = time.time() - t
        print(f"    lan sau : {gio_sau * 1000:.1f} ms (chi doc dau)")
        check("lan sau nhanh hon lan dau it nhat 10 lan",
              gio_sau * 10 < gio_dau, f"{gio_sau:.3f}s vs {gio_dau:.3f}s")
    finally:
        if sao_luu is not None:
            dau.write_bytes(sao_luu)


def test_dau_khong_vao_zip():
    print()
    print("=" * 72)
    print("Dau kiem KHONG duoc nam trong zip ban giao")
    print("=" * 72)
    # Neu dau di theo zip, may con giai nen ra se BO QUA tu kiem lan dau -
    # dung luc no can nhat (vua giai nen xong, chua biet co thieu file khong).
    dg = HERE.parent / "tests" / "_khong_co_file_nay"
    src = None
    for p in (Path(r"C:\Users\Padoma1\AppData\Local\Temp\claude"),):
        pass
    # Kiem gian tiep: ten dau bat dau bang dau cham va co tien to co dinh
    import tu_kiem_lan_dau as TK
    ten = TK.ten_dau("1.1.0")
    check("ten dau bat dau bang '.' (de loc de)", ten.startswith("."))
    check("ten dau co tien to on dinh `.da_tu_kiem_`",
          ten.startswith(".da_tu_kiem_"), ten)


def test_chan_doan_dung_khi_thieu_file():
    """Thieu file cua tool KHONG duoc bi bao thanh "may chua co Python".

    Bug #89: ban dau `.bat` kiem Python TRUOC, bang `import chung, tkinter`.
    Thieu `chung.py` -> moi phep kiem Python deu that bai -> .bat ket luan
    "may nay chua co Python 3.8". Nguoi dung di cai Python mat 3 phut, quay
    lai van hong, va khong con manh moi nao. Chan doan sai con te hon khong
    chan doan.

    Phep kiem nay chay THAT file .bat trong thu muc thieu `chung.py`.
    Khong can Python di kem: lop kiem file phai chan TRUOC khi cham den
    Python - do chinh la dieu dang kiem.
    """
    print()
    print("=" * 72)
    print("Thieu file tool -> chan doan phai DUNG (khong do oan cho Python)")
    print("=" * 72)

    van_bat = (ROOT / "GIAO_DIEN.bat").read_text("ascii", "replace")
    check("kiem file tool TRUOC khi cham den Python",
          van_bat.index("THIEU=") < van_bat.index("python\\python.exe"),
          "kiem Python truoc -> thieu file .py se bi bao nham thanh loi Python")
    for t in ("giao_dien.py", "goi_project_capcut.py", "chung.py",
              "tu_kiem_lan_dau.py"):
        check(f"co kiem su ton tai cua {t}", f'"%~dp0{t}"' in van_bat,
              f"{t} duoc nap NGAY luc import -> thieu no thi pythonw chet im"
              " lang, khong console khong cua so")

    tmp = Path(tempfile.mkdtemp(prefix="chan_doan_"))
    try:
        d = tmp / "TOOL"
        d.mkdir()
        for f in ("GIAO_DIEN.bat", "giao_dien.py", "goi_project_capcut.py",
                  "tu_kiem_lan_dau.py", "toi_uu_dung_luong.py",
                  "xem_tien_trinh.py", "cau_hinh.json"):
            shutil.copy2(ROOT / f, d / f)
        # chung.py CO Y khong chep

        log = tmp / "log.txt"
        with open(log, "w", encoding="utf-8", errors="replace") as fh:
            # Ghi ra FILE chu khong pipe: tien trinh tach ra bang `start` thua
            # ke dau pipe, nen `run()` se cho den khi giao dien dong (bug #88).
            r = subprocess.run(["cmd", "/c", str(d / "GIAO_DIEN.bat")],
                               stdout=fh, stderr=subprocess.STDOUT,
                               stdin=subprocess.DEVNULL, timeout=180, cwd=str(d))
        ra = log.read_text(encoding="utf-8", errors="replace")

        check("bao dung la THIEU FILE", "THIEU FILE" in ra.upper(), ra[:400])
        check("goi ten file thieu", "chung.py" in ra, ra[:400])
        check("KHONG do oan cho Python", "chua co Python" not in ra,
              f"chan doan sai -> nguoi dung cai Python roi van hong\n{ra[:400]}")
        check("chi ro cach sua (giai nen lai)", "GIAI NEN LAI" in ra.upper(),
              ra[:400])
        check("ma thoat khac 0", r.returncode != 0,
              f"ma thoat {r.returncode} -> script goi khong biet la that bai")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    test_dau_kiem()
    test_khong_ghi_dau_khi_hong()
    test_van_kiem_ffmpeg_moi_lan()
    test_bat_an_console()
    test_chan_doan_dung_khi_thieu_file()
    test_stdout_none()
    test_dau_khong_vao_zip()
    test_hai_duong_chay()
    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
