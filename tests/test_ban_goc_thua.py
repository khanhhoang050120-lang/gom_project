# -*- coding: utf-8 -*-
"""#38 - MOT nguon sinh NHIEU ban `_opt`: so dang ky phai duoc tro lai het,
va phai co phep nghiem thu tu dong bat duoc ban goc con bi giu song vo ich.

Bug #38 giu lai 10,46 GB tren goi that va CHI lo ra khi co nguoi thay dung luong
cuoi vo ly (29,82 GB cho 32,8 phut timeline). Bo kiem nay bien viec truy tay do
thanh phep dem tu dong.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from draft_gia import tao_draft_gia, GUID      # noqa: E402

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


def liet_ke_opt(out):
    ra = []
    for dp, _d, fs in os.walk(out):
        for f in fs:
            if "_opt" in f.lower() and f.lower().endswith(".mp4"):
                ra.append(Path(dp) / f)
    return ra


def main():
    global pas, fail
    import toi_uu_dung_luong as TU

    ffmpeg, ffprobe = TU.ff_paths(HERE.parent)
    if not ffmpeg:
        print("BO QUA: khong tim thay ffmpeg/ffprobe - bo kiem nay can ma hoa media that")
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="goc_thua_"))
    try:
        print("=" * 72)
        print("#38 - mot nguon dung o 3 material -> sinh nhieu ban _opt")
        print("=" * 72)
        mo_ta = tao_draft_gia(tmp, ffmpeg, ffprobe, co_subdraft=False,
                              nhieu_doan=True)
        draft = mo_ta["draft_dir"]
        out = tmp / "GOI"
        shutil.copytree(draft, out)

        # Dua mot BAN SAO cua footage goc vao trong goi - dung nhu khi plan_package
        # da copy ban goc truoc khi pha toi uu thay no.
        kho = out / "materials" / "video"
        kho.mkdir(parents=True, exist_ok=True)
        ban_goc_trong_goi = kho / "canh1.mp4"
        shutil.copy2(mo_ta["media_ngoai"][0], ban_goc_trong_goi)
        co_ban_dau = os.path.getsize(ban_goc_trong_goi)

        opts = {"trim": True, "scale": False, "recompress": True, "cleanup": True,
                "crf": 32, "preset": "ultrafast", "workers": 1,
                "trim_min_save": 1024}
        st = TU.optimize_package(out, draft, {}, GUID, opts, ffmpeg, ffprobe,
                                 log=lambda *a: None)

        ds_opt = liet_ke_opt(out)
        print(f"  so ban _opt sinh ra : {len(ds_opt)}")
        print(f"  st['repointed']     : {st.get('repointed')}")
        check("mot nguon sinh NHIEU ban _opt (dung tinh huong bug #38)",
              len(ds_opt) >= 2,
              f"chi co {len(ds_opt)} ban - fixture chua tai hien duoc tinh huong")

        print()
        print("=" * 72)
        print("Phep nghiem thu tu dong: bat ban goc con bi giu song vo ich")
        print("=" * 72)
        thua = TU.kiem_ban_goc_thua(out, log=lambda *a: None)
        ten_thua = {Path(p).name.lower() for p, _ in thua}
        print(f"  ban goc thua: {[(Path(p).name, f'{s/1e6:.1f} MB') for p, s in thua]}")
        check("phat hien duoc ban goc khong file noi dung nao dung",
              "canh1.mp4" in ten_thua,
              "day la file 'chi so dang ky giu song' - dung co che bug #38")
        check("KHONG bao nham ban _opt la thua",
              not any("_opt" in n for n in ten_thua),
              f"ten_thua = {ten_thua}")

        # Don dep xong thi ban goc phai bien mat (khong con ai tro toi)
        TU.cleanup_unused(out, log=lambda *a: None)
        con = ban_goc_trong_goi.is_file()
        print()
        print("=" * 72)
        print("Sau khi don dep: ban goc trong goi phai bi bo")
        print("=" * 72)
        check("ban goc da duoc don khoi goi",
              not con,
              f"van con {ban_goc_trong_goi} ({co_ban_dau/1e6:.1f} MB)"
              " -> so dang ky van giu no song (bug #38 chua duoc chua het)")

        print()
        print("=" * 72)
        print("Chieu nguoc: goi sach thi phep nghiem thu KHONG duoc bao dong gia")
        print("=" * 72)
        tmp2 = Path(tempfile.mkdtemp(prefix="sach_", dir=str(tmp)))
        mo_ta2 = tao_draft_gia(tmp2, ffmpeg, ffprobe, co_subdraft=False)
        out2 = tmp2 / "GOI"
        shutil.copytree(mo_ta2["draft_dir"], out2)
        thua2 = TU.kiem_ban_goc_thua(out2, log=lambda *a: None)
        # co_san.mp4 nam trong draft va DUOC content dung -> khong duoc coi la thua
        check("media dang duoc content dung KHONG bi bao la thua",
              not any(Path(p).name.lower() == "co_san.mp4" for p, _ in thua2),
              f"thua2 = {[Path(p).name for p, _ in thua2]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
