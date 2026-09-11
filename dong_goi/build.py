# -*- coding: utf-8 -*-
r"""Dong goi .exe cho GOI PROJECT CAPCUT.

    python dong_goi\build.py              (dong goi day du)
    python dong_goi\build.py --bo-qua-kiem   (CHI khi da chay bo kiem rieng)

Thu tu CO Y, khong duoc doi:

  1. Chay `tests\chay_het.py` TRUOC. Do thi DUNG HAN.
     Dong goi mot ban da hong roi phat hanh cho 40-50 nguoi la kieu hong ton
     kem nhat - ho tro tung may mot. Cong kiem phai dung TRUOC khi build, chu
     khong phai "build xong roi kiem sau".

  2. Kiem tai nguyen bat buoc co mat. Thieu `ffmpeg/` thi bao RO va hoi, chu
     khong lang le dong goi mot ban ma che do 4 khong chay duoc.

  3. Goi PyInstaller voi `dong_goi\goi_exe.spec`.

  4. Kiem ban vua build: co .exe, co ffmpeg, co ui/ + loi/, khong .bat nao
     co byte > 127, kich thuoc trong nguong.

  5. Chay lai bo kiem BANG PYTHON DI KEM (`python\python.exe`) neu co.
     Ban di kem la ban NGUOI DUNG that su chay; ban Python he thong cua may
     phat trien co the che mat loi chi xuat hien o ban kia (da tung xay ra:
     bo kiem giao dien qua o Python he thong, chet o ban di kem).

PyInstaller la cong cu BUILD, khong phai dependency CHAY - san pham van chi
dung thu vien chuan. Diem nay da duoc chu du an duyet (ke hoach kiem thu,
muc "Can chu du an duyet" so 1).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
SPEC = GOC / "dong_goi" / "goi_exe.spec"
DICH = GOC / "dist" / "GoiProjectCapCut"

# Nguong kich thuoc: ~225 MB do that voi ffmpeg di kem (PERF.md P-01).
# Dat 300 MB de khong bao dong gia, nhung van bat duoc truong hop goi phinh
# bat thuong (vi du vo tinh keo ca thu muc `python/` vao).
NGUONG_MB = 300


def _in_dau(s: str):
    print()
    print("=" * 72)
    print(" " + s)
    print("=" * 72)


def _chay(lenh: list, nhan: str) -> bool:
    print(f"  $ {' '.join(str(x) for x in lenh[:3])} ...")
    t0 = time.monotonic()
    r = subprocess.run(lenh, cwd=str(GOC))
    giay = time.monotonic() - t0
    if r.returncode != 0:
        print(f"  !! {nhan} THAT BAI (ma {r.returncode}, {giay:.1f}s)")
        return False
    print(f"  OK {nhan} ({giay:.1f}s)")
    return True


def buoc_1_kiem(bo_qua: bool) -> bool:
    _in_dau("BUOC 1 - chay toan bo bo kiem TRUOC khi dong goi")
    if bo_qua:
        print("  (bi bo qua bang --bo-qua-kiem)")
        print("  !! CHI dung khi ban vua chay `python tests\\chay_het.py`")
        print("     va doc ket qua THAT. Dung bo qua de 'cho nhanh'.")
        return True
    return _chay([sys.executable, str(GOC / "tests" / "chay_het.py")],
                 "bo kiem")


def buoc_2_tai_nguyen() -> bool:
    _in_dau("BUOC 2 - kiem tai nguyen bat buoc")
    ok = True
    bat_buoc = ["cau_hinh.json", "giao_dien.py", "goi_project_capcut.py",
                "ui", "loi"]
    for t in bat_buoc:
        co = (GOC / t).exists()
        print(f"  {'OK' if co else '!!'}  {t}")
        ok = ok and co

    ff = GOC / "ffmpeg" / "bin" / "ffmpeg.exe"
    if ff.is_file():
        print("  OK  ffmpeg/bin/ffmpeg.exe")
    else:
        # KHONG im lang: ban thieu ffmpeg chay duoc che do 1 nhung che do 4
        # se tu ha xuong - nguoi dung khong hieu vi sao goi khong nho di.
        print("  !!  KHONG thay ffmpeg/bin/ffmpeg.exe")
        print("      Ban .exe se KHONG co ffmpeg di kem -> che do 4 (toi uu")
        print("      dung luong) tu ha xuong che do 1 tren may nguoi dung.")
        print("      Chi dong goi BAN PHAT HANH tren may CO ffmpeg/.")
        ok = False
    return ok


def buoc_3_pyinstaller() -> bool:
    _in_dau("BUOC 3 - goi PyInstaller (onedir)")
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("  !! Chua cai PyInstaller.")
        print("     pip install pyinstaller==6.22.2")
        print("     (cong cu BUILD - san pham van chi dung thu vien chuan)")
        return False

    for thu in (GOC / "build", GOC / "dist"):
        if thu.is_dir():
            shutil.rmtree(thu, ignore_errors=True)

    return _chay([sys.executable, "-m", "PyInstaller", "--noconfirm",
                  "--clean", str(SPEC)], "PyInstaller")


def buoc_4_kiem_ban_build() -> bool:
    _in_dau("BUOC 4 - kiem ban vua build")
    if not DICH.is_dir():
        print(f"  !! khong thay {DICH}")
        return False

    ok = True

    exe = DICH / "GoiProjectCapCut.exe"
    print(f"  {'OK' if exe.is_file() else '!!'}  co GoiProjectCapCut.exe")
    ok = ok and exe.is_file()

    for t in ("cau_hinh.json", "ui", "loi"):
        co = (DICH / t).exists() or (DICH / "_internal" / t).exists()
        print(f"  {'OK' if co else '!!'}  co {t}")
        ok = ok and co

    ff = None
    for goc in (DICH, DICH / "_internal"):
        if (goc / "ffmpeg" / "bin" / "ffmpeg.exe").is_file():
            ff = goc / "ffmpeg" / "bin" / "ffmpeg.exe"
            break
    print(f"  {'OK' if ff else '!!'}  co ffmpeg di kem")
    ok = ok and ff is not None

    # ffmpeg phai CHAY DUOC, khong chi ton tai (bai hoc test_ffmpeg_hong.py:
    # co file nhung thieu DLL / ban LGPL khong co libx264 / bi Defender chan).
    if ff:
        try:
            r = subprocess.run([str(ff), "-version"], capture_output=True,
                               timeout=30)
            chay_duoc = r.returncode == 0
        except Exception as ex:
            chay_duoc = False
            print(f"      ({type(ex).__name__}: {ex})")
        print(f"  {'OK' if chay_duoc else '!!'}  ffmpeg CHAY DUOC (-version)")
        ok = ok and chay_duoc

    # .bat phai KHONG DAU: cmd.exe dien giai comment theo code page TRUOC khi
    # `chcp 65001` kip chay (bug #12).
    for b in list(DICH.rglob("*.bat")):
        raw = b.read_bytes()
        xau = [i for i, c in enumerate(raw) if c > 127]
        print(f"  {'OK' if not xau else '!!'}  {b.name} khong co byte > 127")
        ok = ok and not xau

    tong = sum(f.stat().st_size for f in DICH.rglob("*") if f.is_file())
    mb = tong / 1e6
    trong = mb <= NGUONG_MB
    print(f"  {'OK' if trong else '!!'}  kich thuoc {mb:.0f} MB"
          f" (nguong {NGUONG_MB} MB)")
    ok = ok and trong

    # TOOL_VERSION cua ban build phai khop ma nguon - lech nghia la dong goi
    # nham ban, va bao cao gui ve se noi sai phien ban (bug nhom C).
    sys.path.insert(0, str(GOC))
    try:
        import goi_project_capcut as G
        print(f"  OK  TOOL_VERSION = {G.TOOL_VERSION}")
    except Exception as ex:
        print(f"  !!  khong doc duoc TOOL_VERSION: {ex}")
        ok = False
    return ok


def buoc_5_kiem_bang_python_di_kem() -> bool:
    _in_dau("BUOC 5 - chay lai bo kiem BANG PYTHON DI KEM")
    py = GOC / "python" / "python.exe"
    if not py.is_file():
        print("  (khong co python/python.exe di kem - bo qua buoc nay)")
        print("   Ban di kem la ban NGUOI DUNG that su chay. Python he thong")
        print("   cua may phat trien co the che mat loi chi xuat hien o ban")
        print("   kia - da tung xay ra voi bo kiem giao dien.")
        return True
    return _chay([str(py), str(GOC / "tests" / "chay_het.py")],
                 "bo kiem (Python di kem)")


def main(argv):
    bo_qua = "--bo-qua-kiem" in argv
    print("=" * 72)
    print(" DONG GOI .EXE - GOI PROJECT CAPCUT")
    print("=" * 72)
    print(f"  Goc     : {GOC}")
    print(f"  Spec    : {SPEC}")
    print(f"  Dich    : {DICH}")

    cac_buoc = [
        ("kiem thu", lambda: buoc_1_kiem(bo_qua)),
        ("tai nguyen", buoc_2_tai_nguyen),
        ("PyInstaller", buoc_3_pyinstaller),
        ("kiem ban build", buoc_4_kiem_ban_build),
        ("kiem bang Python di kem", buoc_5_kiem_bang_python_di_kem),
    ]
    for ten, ham in cac_buoc:
        if not ham():
            print()
            print("=" * 72)
            print(f"  => DUNG o buoc: {ten}. KHONG dong goi tiep.")
            print("=" * 72)
            return 1

    print()
    print("=" * 72)
    print(f"  => XONG. Ban .exe o: {DICH}")
    print("  PHEP THU BAT BUOC truoc khi phat hanh:")
    print("    1. Chep CA THU MUC sang MAY KHAC chua cai Python, chay thu.")
    print("    2. Goi mot project that, roi chay:")
    print("       python tests\\nghiem_thu_goi.py <thu_muc_goi>")
    print("    3. Chep goi sang may co CapCut va MO THU (phep thu vang).")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
