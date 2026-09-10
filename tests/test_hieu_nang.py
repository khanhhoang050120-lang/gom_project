# -*- coding: utf-8 -*-
"""Giai doan 5 - hai thu THAT SU dang sua (do bang so, khong doan).

  1. `mo_ta_moi_truong()` - tinh MOT LAN, khong goi WMI lai, co duong lui
  2. `probe()` co bo nho dem - va bo dem phai NHAN RA file da bi ghi de

Kem hai phep kiem chong hoi quy quan trong:
  - khong con lenh goi `platform.*` truc tiep tren duong khoi dong
  - `xoa_cache_probe()` KHONG duoc la code chet (dinh nghia ma khong ai goi -
    dung cai bay da ghi o muc #52)
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import chung as C                      # noqa: E402
import toi_uu_dung_luong as TU         # noqa: E402

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


def test_moi_truong():
    print("=" * 72)
    print("mo_ta_moi_truong() - tinh mot lan, khong goi WMI lai")
    print("=" * 72)
    C._MOI_TRUONG = None                     # ep tinh lai tu dau
    t0 = time.perf_counter()
    a = C.mo_ta_moi_truong()
    lan_dau = time.perf_counter() - t0
    t0 = time.perf_counter()
    for _ in range(200):
        b = C.mo_ta_moi_truong()
    lan_sau = (time.perf_counter() - t0) / 200
    print(f"  lan dau : {lan_dau * 1000:7.2f} ms")
    print(f"  lan sau : {lan_sau * 1000:7.4f} ms (trung binh 200 lan)")

    check("tra ve (python, he_dieu_hanh)",
          isinstance(a, tuple) and len(a) == 2 and all(a), f"a = {a}")
    check("goi lai cho ket qua Y HET", a == b, f"{a} vs {b}")
    check("goi lai gan nhu mien phi (da dem)",
          lan_sau * 1000 < 0.05, f"{lan_sau * 1000:.4f} ms - co ve chua dem")

    # Duong lui: platform hong thi van phai tra ve duoc, khong duoc nem loi
    import platform as _pl
    that = _pl.system
    _pl.system = lambda: (_ for _ in ()).throw(OSError("[ep loi] WMI khong tra loi"))
    C._MOI_TRUONG = None
    try:
        c = C.mo_ta_moi_truong()
    finally:
        _pl.system = that
        C._MOI_TRUONG = None
    check("platform hong -> van tra ve duoc (co duong lui)",
          isinstance(c, tuple) and len(c) == 2 and all(c), f"c = {c}")
    # Duong lui phai dua tren sys.platform (khong cham WMI). Phan `| ACP nnn`
    # duoc noi them sau la mot loi goi ctypes re, khong lien quan WMI.
    check("duong lui khong cham WMI", c[1].startswith(sys.platform),
          f"c[1] = {c[1]!r} - phai bat dau bang sys.platform = {sys.platform!r}")
    check("van kem BANG MA de bao cao truy duoc", "ACP" in c[1],
          f"c[1] = {c[1]!r}")


def test_khong_con_platform():
    print()
    print("=" * 72)
    print("Khong con goi platform.* truc tiep tren duong khoi dong")
    print("=" * 72)
    for ten in ("goi_project_capcut.py", "toi_uu_dung_luong.py", "xem_tien_trinh.py"):
        src = (ROOT / ten).read_text(encoding="utf-8")
        xau = [d.strip() for d in src.splitlines()
               if "platform." in d and "sys.platform" not in d
               and not d.strip().startswith("#")]
        check(f"{ten}: khong goi platform.* truc tiep", not xau,
              "\n".join(xau[:5]) + "\n  -> phai dung mo_ta_moi_truong() de khoi"
              " goi WMI lai (co the treo tren may bi siet quyen)")


def test_cache_probe():
    print()
    print("=" * 72)
    print("probe() co bo nho dem - va NHAN RA file da bi ghi de")
    print("=" * 72)
    ffmpeg, ffprobe = TU.ff_paths(ROOT)
    if not ffmpeg:
        print("  (khong co ffmpeg -> bo qua)")
        return
    from draft_gia import tao_video
    tmp = Path(tempfile.mkdtemp(prefix="cache_probe_"))
    try:
        tep = tao_video(ffmpeg, tmp / "a.mp4", 3)
        TU.xoa_cache_probe()

        dem = [0]
        that = TU._probe_that

        def dem_probe(*a, **k):
            dem[0] += 1
            return that(*a, **k)

        TU._probe_that = dem_probe
        try:
            i1 = TU.probe(ffprobe, tep)
            i2 = TU.probe(ffprobe, tep)
            i3 = TU.probe(ffprobe, tep)
            print(f"  3 lan goi probe cung file -> {dem[0]} lan chay ffprobe that")
            check("chi chay ffprobe MOT lan cho 3 lan hoi", dem[0] == 1,
                  f"chay {dem[0]} lan")
            check("ket qua giong nhau", i1 == i2 == i3)

            # GHI DE file bang mot clip DAI HON -> bo dem PHAI nhan ra
            truoc = dem[0]
            time.sleep(1.1)                 # vuot do phan giai mtime 1 giay
            tao_video(ffmpeg, tep, 6)
            i4 = TU.probe(ffprobe, tep)
            print(f"  sau khi ghi de -> them {dem[0] - truoc} lan chay ffprobe")
            check("file bi ghi de -> probe LAI, khong dung ket qua cu",
                  dem[0] > truoc,
                  "bo dem chi theo duong dan se tra so lieu cua file da chet")
            check("do dai moi khac do dai cu",
                  i4 is not None and i1 is not None and i4[2] != i1[2],
                  f"cu = {i1[2] if i1 else None}, moi = {i4[2] if i4 else None}")

            # Xoa dem thi phai chay lai
            truoc = dem[0]
            TU.xoa_cache_probe()
            TU.probe(ffprobe, tep)
            check("xoa_cache_probe() that su xoa", dem[0] > truoc)
        finally:
            TU._probe_that = that
            TU.xoa_cache_probe()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_khong_code_chet():
    print()
    print("=" * 72)
    print("xoa_cache_probe() khong duoc la CODE CHET (bay o muc #52)")
    print("=" * 72)
    src = (ROOT / "toi_uu_dung_luong.py").read_text(encoding="utf-8")
    so_lan = src.count("xoa_cache_probe")
    print(f"  xuat hien {so_lan} lan trong toi_uu_dung_luong.py")
    check("co it nhat mot CHO GOI (khong chi dinh nghia)", so_lan >= 2,
          "chi co dinh nghia ma khong ai goi = code chet, dung cai bay muc #52")
    check("duoc goi o dau optimize_package()",
          "xoa_cache_probe()" in src.split("def optimize_package")[1][:900],
          "phai xoa dem o dau moi pha: mtime chi chinh xac toi giay, file ghi de"
          " trong cung mot giay voi cung kich thuoc se cho khoa y het")


def main():
    test_moi_truong()
    test_khong_con_platform()
    test_cache_probe()
    test_khong_code_chet()
    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
