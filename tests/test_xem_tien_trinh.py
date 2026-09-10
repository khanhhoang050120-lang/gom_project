# -*- coding: utf-8 -*-
"""Bo kiem cho `xem_tien_trinh.py` - file TRUOC DAY khong he co bo kiem nao.

Vi sao co file nay: E1 gop hai ban chep cua `_fmt_time()` lam mot, nhung hai ban
do KHONG GIONG NHAU - ban cua `xem_tien_trinh.py` co guard `sec is None`, ban cua
`goi_project_capcut.py` thi khong. E1 lay nham ban chua duoc va, khien
`xem_tien_trinh.py` chet bang TypeError NGAY nhip hien thi dau tien. Bang tong ket
van bao "TAT CA DAT" vi khong bo kiem nao dong toi file do.

Bai hoc: mot file khong co bo kiem thi moi bang tong ket xanh deu la xanh GIA
o phan do.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import chung as C          # noqa: E402

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


def test_fmt_time():
    print("=" * 72)
    print("_fmt_time() phai chiu duoc MOI sentinel ma cac cho goi dung")
    print("=" * 72)
    # Hai cho goi dung sentinel KHAC NHAU cho "chua biet":
    #   goi_project_capcut.py -> -1
    #   xem_tien_trinh.py     -> None
    # Ban dung chung phai chiu duoc CA HAI.
    check("None -> '?'  (xem_tien_trinh dung sentinel nay)",
          C._fmt_time(None) == "?",
          "day chinh la loi E1 gay ra: ban gop mat guard None")
    check("-1 -> '?'  (goi_project_capcut dung sentinel nay)",
          C._fmt_time(-1) == "?")
    check("NaN -> '?'", C._fmt_time(float("nan")) == "?")
    for giay, mong in ((0, "0s"), (45, "45s"), (192, "3m12s"), (3725, "1h02m")):
        check(f"{giay} -> {mong!r}", C._fmt_time(giay) == mong,
              f"ra {C._fmt_time(giay)!r}")


def chay_vong_do(thu_muc, tra_loi, giay=6):
    """Chay `xem_tien_trinh.py` nhu TIEN TRINH CON. Tra (loi, van_ban).

    KHONG chay trong luong: `contextlib.redirect_stdout` doi `sys.stdout` cua CA
    TIEN TRINH, khong phai rieng luong. Vong theo doi la vong VO HAN nen luong do
    khong bao gio thoat khoi context manager -> stdout bi chuyen huong vinh vien
    va moi dong in sau do bien mat. Da vap dung loi nay khi viet bo kiem nay.
    """
    dau_vao = "\n".join(tra_loi) + "\n"
    try:
        r = subprocess.run(
            [sys.executable, "-u", str(ROOT / "xem_tien_trinh.py")],
            cwd=str(ROOT), input=dau_vao,
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=giay)
        ra, err = (r.stdout or ""), (r.stderr or "")
    except subprocess.TimeoutExpired as e:
        # Vong theo doi la vong VO HAN - het gio la BINH THUONG, khong phai loi.
        # Lay output do dang de van kiem duoc noi dung da in ra.
        ra = e.stdout.decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = e.stderr.decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
    loi = None
    if "Traceback" in ra + err:
        loi = (ra + err).split("Traceback", 1)[1][:400]
    return loi, ra


def test_chay_that():
    print()
    print("=" * 72)
    print("CHAY THAT vong theo doi - ca hai nhanh")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="xtt_"))
    try:
        (tmp / "materials").mkdir()
        (tmp / "materials" / "a.mp4").write_bytes(b"x" * 4096)

        # Nhanh 1: CO nhap tong GB du kien -> di qua duong tinh ETA (dung None)
        loi, ra = chay_vong_do(tmp, [str(tmp), "10"])
        check("nhanh CO tong GB: khong nem loi", loi is None, f"loi = {loi}")
        check("nhanh CO tong GB: co ve thanh tien do", "%" in ra, ra[-300:])
        check("nhanh CO tong GB: hien '?' khi chua tinh duoc ETA",
              "~?" in ra, ra[-300:])

        # Nhanh 2: KHONG nhap tong GB -> duong khac
        loi2, ra2 = chay_vong_do(tmp, [str(tmp), ""])
        check("nhanh KHONG tong GB: khong nem loi", loi2 is None, f"loi = {loi2}")
        check("nhanh KHONG tong GB: van in duoc so lieu",
              "GB" in ra2 or "file" in ra2, ra2[-300:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_dung_chung_lp():
    print()
    print("=" * 72)
    print("Dung CHUNG `_lp` voi tool chinh - khong con ban chep")
    print("=" * 72)
    import xem_tien_trinh as X
    check("_lp la cua chung.py", X._lp.__module__ == "chung",
          f"dang la {X._lp.__module__}")
    check("_fmt_time la cua chung.py", X._fmt_time.__module__ == "chung",
          f"dang la {X._fmt_time.__module__}")
    src = (ROOT / "xem_tien_trinh.py").read_text(encoding="utf-8")
    check("khong con dinh nghia rieng _lp", "def _lp(" not in src)
    check("khong con dinh nghia rieng _fmt_time", "def _fmt_time(" not in src)


def test_do_dung_luong():
    print()
    print("=" * 72)
    print("dir_size_and_count() dem dung, ke ca duong dan dai")
    print("=" * 72)
    import xem_tien_trinh as X
    tmp = Path(tempfile.mkdtemp(prefix="xtt2_"))
    try:
        (tmp / "a.mp4").write_bytes(b"x" * 1000)
        sau = tmp / "b"
        while len(str(sau)) < 290:
            sau = sau / "thu_muc_dai_de_vuot_gioi_han_260"
        Path(C._lp(sau)).mkdir(parents=True, exist_ok=True)
        Path(C._lp(sau / "c.mp4")).write_bytes(b"y" * 2000)

        tong, so = X.dir_size_and_count(tmp)
        print(f"  do duoc: {so} file, {tong} byte")
        check("dem du ca file o duong dan > 260 ky tu", so == 2,
              f"chi thay {so} file -> co the dang thieu _lp")
        check("tong dung luong dung", tong == 3000, f"tong = {tong}")
    finally:
        shutil.rmtree(C._lp(tmp), ignore_errors=True)


def main():
    test_fmt_time()
    test_dung_chung_lp()
    test_do_dung_luong()
    test_chay_that()
    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
