# -*- coding: utf-8 -*-
"""E2 + G1 - san sang de CHEP SANG MAY KHAC.

  E2  `ff_paths()` tim dung ban ffmpeg DI KEM, ke ca khi da dong goi (PyInstaller)
  G1  Thieu dieu kien thi bao NGAY khi khoi dong, khong chet giua chung sau khi
      da hoi xong het cau hoi
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

pas = fail = 0


def check(ten, dk, chi_tiet=""):
    global pas, fail
    if dk:
        pas += 1
        print(f"  PASS  {ten}")
    else:
        fail += 1
        print(f"  FAIL  {ten}")
        if chi_tiet:
            for d in str(chi_tiet).splitlines():
                print(f"           {d}")


def chep_tool(dich, bo_qua=()):
    """Chep tool sang thu muc khac (mo phong nguoi dung chep di dung), co the
    CO Y bo sot mot so file de kiem duong bao loi."""
    dich.mkdir(parents=True, exist_ok=True)
    for ten in ("chung.py", "goi_project_capcut.py", "toi_uu_dung_luong.py",
                "xem_tien_trinh.py", "cau_hinh.json"):
        if ten in bo_qua:
            continue
        if (ROOT / ten).is_file():
            shutil.copy2(ROOT / ten, dich / ten)
    # PACKAGE con: nguoi dung chep tool di la chep CA THU MUC, nen ban mo phong
    # cung phai chep. Thieu `loi/` thi `goi_project_capcut` nap khong duoc va
    # bo kiem se do vi mot ly do KHAC han cai no dinh kiem.
    for goi in ("loi", "ui"):
        if goi in bo_qua:
            continue
        nguon = ROOT / goi
        if nguon.is_dir():
            shutil.copytree(nguon, dich / goi,
                            ignore=shutil.ignore_patterns("__pycache__"),
                            dirs_exist_ok=True)
    return dich


def chay_tool_o(thu_muc, dau_vao="q\n"):
    """Chay goi_project_capcut.py trong thu muc do, tra (ma, output).

    PHAI ep `sys.path` chi con `thu_muc`, khong duoc de mac dinh.

    Ly do: ke tu khi dong goi Python EMBEDDABLE vao `<tool>/python/`, file
    `python314._pth` co dong `..` -> thu muc tool THAT luon nam tren sys.path
    cua interpreter do, bat ke chay tu dau. Khi do canh "chep thieu chung.py"
    KHONG dung duoc: ban sao tam thieu file, nhung Python van tim thay ban goc
    o thu muc that -> tool khoi dong binh thuong va phep kiem do nham.
    (Voi may con thi `..` = ban sao CUA HO nen hanh vi van dung; day thuan tuy
    la van de dung canh trong bo kiem.)

    `runpy.run_path` giu dung `__file__` - khac `exec(open(...).read())` se lam
    hong moi cho tool dung `Path(__file__)`.
    """
    # GIU thu vien chuan, chi LOAI thu muc tool that. Dat sys.path = [thu_muc]
    # tran se xoa ca stdlib -> `runpy` khong nap noi `pkgutil` (da mac mot lan).
    ma = (
        "import sys, os, runpy\n"
        f"_goc = os.path.normcase({str(ROOT)!r})\n"
        "sys.path[:] = [p for p in sys.path"
        " if os.path.normcase(os.path.abspath(p)) != _goc]\n"
        f"sys.path.insert(0, {str(thu_muc)!r})\n"
        f"runpy.run_path({str(thu_muc / 'goi_project_capcut.py')!r},"
        " run_name='__main__')\n"
    )
    r = subprocess.run([sys.executable, "-u", "-c", ma],
                       cwd=str(thu_muc), input=dau_vao,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=120)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def test_ff_paths(TU):
    print("=" * 72)
    print("E2 - ff_paths() uu tien ban ffmpeg DI KEM tool")
    print("=" * 72)
    ff, fp = TU.ff_paths()
    di_kem = ROOT / "ffmpeg" / "bin" / "ffmpeg.exe"
    if di_kem.is_file():
        check("tim duoc ffmpeg", bool(ff), "may nay khong co ffmpeg?")
        if ff:
            check("dung ban DI KEM tool, khong phai ban trong PATH",
                  os.path.normcase(ff) == os.path.normcase(str(di_kem)),
                  f"dang dung: {ff}")
    else:
        # Runner CI sach khong co thu muc ffmpeg/ (bi .gitignore vi 195 MB).
        # Phep kiem "phai dung ban DI KEM" khong con y nghia o do - nhung
        # KHONG duoc im lang bo qua (R-05 + nhom D trong bug.md).
        print("  (bo qua 'uu tien ban di kem': khong co ffmpeg/bin/ffmpeg.exe"
              " - runner sach)")

    # Danh sach goc tim kiem phai co thu muc chua .exe khi da dong goi
    goc_thuong = [str(x) for x in TU._cac_goc_ffmpeg()]
    print(f"  goc tim (chua dong goi): {goc_thuong}")
    check("chua dong goi -> tim canh file .py", any(
        os.path.normcase(g) == os.path.normcase(str(ROOT)) for g in goc_thuong))

    # Gia lam da dong goi bang PyInstaller
    tmp = Path(tempfile.mkdtemp(prefix="frozen_"))
    try:
        cu_frozen = getattr(sys, "frozen", None)
        cu_mei = getattr(sys, "_MEIPASS", None)
        cu_exe = sys.executable
        sys.frozen = True
        sys._MEIPASS = str(tmp / "giai_nen_tam")
        sys.executable = str(tmp / "GoiProject.exe")
        try:
            goc_dg = [os.path.normcase(str(x)) for x in TU._cac_goc_ffmpeg()]
        finally:
            sys.executable = cu_exe
            if cu_frozen is None:
                del sys.frozen
            else:
                sys.frozen = cu_frozen
            if cu_mei is None:
                del sys._MEIPASS
            else:
                sys._MEIPASS = cu_mei
        print(f"  goc tim (gia lam da dong goi): {goc_dg}")
        # So voi ban DA `.resolve()`: `_cac_goc_ffmpeg()` goi `.resolve()`, ma
        # tren runner GitHub thu muc TEMP la ten NGAN 8.3 (`RUNNER~1`) nen
        # `.resolve()` bung ra ten dai (`runneradmin`) - hai ben lech nhau va
        # bo kiem DO OAN. Tren may phat trien hai ben trung nhau nen khong lo.
        check("da dong goi -> co tim thu muc chua file .exe",
              os.path.normcase(str(Path(tmp).resolve())) in goc_dg,
              "neu thieu, ban ffmpeg di kem se khong duoc tim thay va tool lang le"
              " dung mot ffmpeg KHAC trong PATH")
        check("da dong goi -> co tim ca thu muc giai nen tam",
              os.path.normcase(str((tmp / "giai_nen_tam").resolve())) in goc_dg)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_g1_du_file():
    print()
    print("=" * 72)
    print("G1 - chep DU file thi chay binh thuong")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="g1_du_"))
    try:
        chep_tool(tmp / "TOOL")
        ma, ra = chay_tool_o(tmp / "TOOL")
        check("khoi dong duoc", "GOI PROJECT CAPCUT" in ra, ra[-400:])
        check("KHONG bao thieu dieu kien", "KHONG THE CHAY" not in ra, ra[-400:])
        check("hien so hieu phien ban", "Phien ban" in ra, ra[:300])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_g1_thieu_file():
    print()
    print("=" * 72)
    print("G1 - chep THIEU file thi phai bao NGAY, khong chet giua chung")
    print("=" * 72)
    for thieu in ("toi_uu_dung_luong.py", "chung.py"):
        tmp = Path(tempfile.mkdtemp(prefix="g1_thieu_"))
        try:
            chep_tool(tmp / "TOOL", bo_qua=(thieu,))
            ma, ra = chay_tool_o(tmp / "TOOL")
            print(f"  --- bo sot {thieu} ---")
            co_bao = "KHONG THE CHAY" in ra or thieu in ra
            check(f"bo sot {thieu}: co bao loi ro rang", co_bao, ra[-500:])
            check(f"bo sot {thieu}: co huong dan chep lai ca thu muc",
                  "chep LAI CA THU MUC" in ra or "ModuleNotFoundError" in ra,
                  ra[-400:])
            # Khong duoc hoi bat ky cau nao truoc khi bao loi
            check(f"bo sot {thieu}: KHONG hoi cau nao truoc khi bao loi",
                  "CHON PROJECT" not in ra,
                  "phai chan NGAY, khong duoc de nguoi dung tra loi xong roi moi chet")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def test_g1_ham():
    print()
    print("=" * 72)
    print("G1 - kiem_tien_de() tren cai dat that phai sach")
    print("=" * 72)
    import chay_tool
    G = chay_tool.nap_tool()
    loi = G.kiem_tien_de()
    check("cai dat hien tai khong loi", not loi, "\n".join(loi))


def main():
    import toi_uu_dung_luong as TU
    test_ff_paths(TU)
    test_g1_ham()
    test_g1_du_file()
    test_g1_thieu_file()
    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
