# -*- coding: utf-8 -*-
"""ffmpeg CO FILE nhung KHONG CHAY DUOC -> phai bao NGAY, khong de cho 15 phut.

`ff_paths()` chi kiem file co ton tai. Tren may con, `ffmpeg.exe` co the nam day
du do ma van vo dung:
  - thieu DLL (ban build khac, hoac chep thieu thu muc bin/)
  - ban LGPL toi gian KHONG co encoder `libx264` -> ma lai clip nao cung hong
  - bi Windows Defender / chinh sach may chan

Neu khong phat hien som, nguoi dung cho 15-30 phut roi nhan ve hang tram loi va
KET LUAN NHAM la footage cua ho hong.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import toi_uu_dung_luong as TU   # noqa: E402

pas = fail = 0


def check(ten, dk, chi_tiet=""):
    global pas, fail
    if dk:
        pas += 1
        print(f"  PASS  {ten}")
    else:
        fail += 1
        print(f"  FAIL  {ten}")
        for d in str(chi_tiet).splitlines():
            print(f"           {d}")


class KetQua:
    def __init__(self, ma=0, out="", err=""):
        self.returncode, self.stdout, self.stderr = ma, out, err


def voi_run_gia(ham):
    """Doi tam TU._run - tra lai nguyen ven du co loi."""
    that = TU._run
    TU._run = ham
    try:
        return TU.kiem_ffmpeg_chay_duoc("ffmpeg.exe", "ffprobe.exe")
    finally:
        TU._run = that


def main():
    print("=" * 72)
    print("ffmpeg co file nhung khong chay duoc -> bao NGAY luc khoi dong")
    print("=" * 72)

    # 1. May THAT (ffmpeg di kem) phai qua duoc
    ffmpeg, ffprobe = TU.ff_paths(ROOT)
    if ffmpeg:
        ok, vi = TU.kiem_ffmpeg_chay_duoc(ffmpeg, ffprobe)
        check("ffmpeg di kem tool: qua duoc phep thu", ok, f"ly do: {vi}")
    else:
        print("  (khong co ffmpeg di kem -> bo qua phep thu duong thuan)")

    # 2. Khong co duong dan
    ok, vi = TU.kiem_ffmpeg_chay_duoc(None, None)
    check("khong co ffmpeg -> bao khong dung duoc", not ok and vi, f"vi = {vi!r}")

    # 3. Thieu DLL: chay len la nem OSError (Windows: WinError 126)
    def thieu_dll(cmd, timeout):
        raise OSError(126, "The specified module could not be found")

    ok, vi = voi_run_gia(thieu_dll)
    check("thieu DLL -> bat duoc", not ok, f"vi = {vi!r}")
    check("noi ro nghi ngo DLL / bi chan",
          "DLL" in vi or "chan" in vi.lower(), f"vi = {vi!r}")

    # 4. Chay duoc nhung tra ma loi
    ok, vi = voi_run_gia(lambda c, t: KetQua(1, "", "khong khoi dong duoc"))
    check("tra ma loi -> bat duoc", not ok, f"vi = {vi!r}")
    check("co kem ma loi trong thong bao", "1" in vi, f"vi = {vi!r}")

    # 5. Ban LGPL toi gian: chay tot nhung KHONG co libx264
    def khong_x264(cmd, timeout):
        if "-encoders" in cmd:
            return KetQua(0, " V..... mpeg4  MPEG-4 part 2\n V..... libvpx  VP8\n", "")
        return KetQua(0, "ffmpeg version 7.0-lgpl\n", "")

    ok, vi = voi_run_gia(khong_x264)
    check("thieu libx264 -> bat duoc", not ok, f"vi = {vi!r}")
    check("noi ro thieu libx264", "libx264" in vi, f"vi = {vi!r}")
    check("chi cho nguoi dung cach sua", "essentials" in vi or "full" in vi,
          f"vi = {vi!r}\n-> bao loi ma khong noi phai lam gi thi nguoi dung"
          " khong phai lap trinh vien se bi ket")

    # 6. Co libx264 -> phai qua
    def co_x264(cmd, timeout):
        if "-encoders" in cmd:
            return KetQua(0, " V..... libx264  H.264 / AVC\n", "")
        return KetQua(0, "ffmpeg version 8.1.2\n", "")

    ok, vi = voi_run_gia(co_x264)
    check("co libx264 -> qua", ok, f"vi = {vi!r}")

    # 7. Da noi vao main() (khong phai code chet - bay muc #52)
    src = (ROOT / "goi_project_capcut.py").read_text(encoding="utf-8")
    check("main() co goi kiem_ffmpeg_chay_duoc",
          "kiem_ffmpeg_chay_duoc(" in src,
          "dinh nghia ma khong ai goi = code chet")
    check("that bai thi QUAY VE che do nguyen ban, khong chay tiep",
          "ffmpeg = ffprobe = None" in src,
          "phai ha xuong che do 1 chu khong duoc vao pha ma lai voi ffmpeg hong")

    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
