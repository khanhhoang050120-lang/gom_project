# -*- coding: utf-8 -*-
"""`loi/phien_ban.py` - xac dinh thu muc goc va noi ghi khi DA DONG GOI .exe.

Vi sao bo kiem nay ton tai: `Path(__file__).resolve().parent` dung khi chay
bang Python thuong nhung SAI khi dong goi, va sai IM LANG. Bo kiem gia lap ca
hai kieu dong goi (onefile / onedir) bang cach dat `sys.frozen` + `sys._MEIPASS`
roi kiem tung ham tra ve dung cai gi.

Ba khai niem PHAI khac nhau khi dong goi - lan lon la sinh bug:
  thu_muc_chuong_trinh()  -> noi chua .exe
  thu_muc_tai_nguyen()    -> noi chua file di kem (co the la thu muc tam)
  thu_muc_ghi()           -> noi GHI duoc
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from loi import phien_ban as PB   # noqa: E402

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


class GiaDongGoi:
    """Gia lap ban da dong goi. Tra lai NGUYEN TRANG khi thoat - neu khong,
    cac bo kiem chay sau se thay `sys.frozen` con sot va hanh xu la."""

    def __init__(self, exe_dir, meipass=None):
        self.exe_dir = Path(exe_dir)
        self.meipass = meipass
        self._cu = {}

    def __enter__(self):
        self._cu["frozen"] = getattr(sys, "frozen", None)
        self._cu["mei"] = getattr(sys, "_MEIPASS", None)
        self._cu["exe"] = sys.executable
        sys.frozen = True
        sys.executable = str(self.exe_dir / "GoiProjectCapCut.exe")
        if self.meipass:
            sys._MEIPASS = str(self.meipass)
        elif hasattr(sys, "_MEIPASS"):
            del sys._MEIPASS
        PB._dat_lai_cache_ghi()
        return self

    def __exit__(self, *a):
        if self._cu["frozen"] is None:
            if hasattr(sys, "frozen"):
                del sys.frozen
        else:
            sys.frozen = self._cu["frozen"]
        if self._cu["mei"] is None:
            if hasattr(sys, "_MEIPASS"):
                del sys._MEIPASS
        else:
            sys._MEIPASS = self._cu["mei"]
        sys.executable = self._cu["exe"]
        PB._dat_lai_cache_ghi()
        return False


print("=" * 64)
print(" `loi/phien_ban.py` - thu muc goc khi dong goi .exe")
print("=" * 64)

# ---------------------------------------------------------------- chua dong goi
print("\nCHUA DONG GOI (chay bang Python thuong)")
check("da_dong_goi() = False", PB.da_dong_goi() is False)
check("thu_muc_chuong_trinh() = goc repo",
      PB.thu_muc_chuong_trinh() == ROOT,
      f"tra ve {PB.thu_muc_chuong_trinh()}, mong {ROOT}")
check("thu_muc_tai_nguyen() = goc repo", PB.thu_muc_tai_nguyen() == ROOT)
check("tim duoc chung.py", PB.tim_tai_nguyen("chung.py") is not None)
if (ROOT / "ffmpeg" / "bin" / "ffmpeg.exe").is_file():
    check("tim duoc ffmpeg/bin/ffmpeg.exe",
          PB.tim_tai_nguyen("ffmpeg/bin/ffmpeg.exe") is not None)
else:
    # Runner CI sach: thu muc ffmpeg/ bi .gitignore. Noi ro thay vi do oan.
    print("  (bo qua 'tim duoc ffmpeg': khong co ffmpeg/ - runner sach)")
check("file khong co -> None (khong nem)",
      PB.tim_tai_nguyen("khong_he_co_file_nay.xyz") is None)

# ---------------------------------------------------------------- onedir
print("\nDA DONG GOI - onedir (khong co _MEIPASS)")
with tempfile.TemporaryDirectory() as td:
    exe_dir = Path(td) / "app"
    (exe_dir / "ffmpeg" / "bin").mkdir(parents=True)
    (exe_dir / "ffmpeg" / "bin" / "ffmpeg.exe").write_bytes(b"gia")
    with GiaDongGoi(exe_dir):
        check("da_dong_goi() = True", PB.da_dong_goi() is True)
        check("thu_muc_chuong_trinh() = thu muc .exe",
              PB.thu_muc_chuong_trinh() == exe_dir.resolve(),
              f"tra ve {PB.thu_muc_chuong_trinh()}, mong {exe_dir.resolve()}")
        check("tim_tai_nguyen thay ffmpeg canh .exe",
              PB.tim_tai_nguyen("ffmpeg/bin/ffmpeg.exe") is not None)
        check("thu_muc_ghi() = canh .exe (ghi duoc)",
              PB.thu_muc_ghi() == exe_dir.resolve(),
              f"tra ve {PB.thu_muc_ghi()}")

# ---------------------------------------------------------------- onefile
print("\nDA DONG GOI - onefile (co _MEIPASS, tai nguyen o thu muc tam)")
with tempfile.TemporaryDirectory() as td:
    exe_dir = Path(td) / "app"
    exe_dir.mkdir(parents=True)
    mei = Path(td) / "_MEI12345"
    (mei / "ffmpeg" / "bin").mkdir(parents=True)
    (mei / "ffmpeg" / "bin" / "ffmpeg.exe").write_bytes(b"gia")
    with GiaDongGoi(exe_dir, meipass=mei):
        check("thu_muc_chuong_trinh() = thu muc .exe, KHONG phai _MEIPASS",
              PB.thu_muc_chuong_trinh() == exe_dir.resolve(),
              f"tra ve {PB.thu_muc_chuong_trinh()}")
        check("thu_muc_tai_nguyen() = _MEIPASS",
              PB.thu_muc_tai_nguyen() == mei,
              f"tra ve {PB.thu_muc_tai_nguyen()}")
        check("hai cai tren PHAI khac nhau",
              PB.thu_muc_chuong_trinh() != PB.thu_muc_tai_nguyen())
        check("tim_tai_nguyen thay ffmpeg trong _MEIPASS",
              PB.tim_tai_nguyen("ffmpeg/bin/ffmpeg.exe") is not None)
        goc = PB.cac_thu_muc_tai_nguyen()
        check("cac_thu_muc_tai_nguyen() co CA .exe LAN _MEIPASS",
              exe_dir.resolve() in goc and mei in goc,
              f"tra ve {goc}")

# ------------------------------------------------- khong ghi duoc canh chuong trinh
print("\nKHONG GHI DUOC canh .exe (mo phong cai vao Program Files)")
with tempfile.TemporaryDirectory() as td:
    exe_dir = Path(td) / "khong_ton_tai" / "sau" / "nua"
    with GiaDongGoi(exe_dir):
        # `_ghi_duoc` se thu mkdir; de chac chan that bai, tro vao mot duong dan
        # KHONG HOP LE tren Windows (ky tu cam).
        pass
    exe_xau = Path(td) / 'ten<cam>|:'
    with GiaDongGoi(exe_xau):
        nghi = PB.thu_muc_ghi()
        check("lui ve mot thu muc GHI DUOC",
              nghi is not None and PB._ghi_duoc(nghi),
              f"tra ve {nghi}")
        check("KHONG tra ve thu muc .exe hong",
              PB.thu_muc_chuong_trinh() != nghi)
        la_appdata = "LOCALAPPDATA" in os.environ and str(nghi).startswith(
            os.environ["LOCALAPPDATA"])
        la_temp = str(nghi).startswith(tempfile.gettempdir())
        check("lui ve %LOCALAPPDATA% hoac thu muc tam",
              la_appdata or la_temp, f"tra ve {nghi}")

# ---------------------------------------------------------------- don dep trang thai
print("\nSAU KHI THOAT gia lap")
check("sys.frozen da duoc tra lai", not getattr(sys, "frozen", False))
check("sys._MEIPASS da duoc tra lai", not hasattr(sys, "_MEIPASS"))
check("thu_muc_chuong_trinh() ve lai goc repo",
      PB.thu_muc_chuong_trinh() == ROOT)

# ---------------------------------------------------------------- mo ta
print("\nMO TA NOI CHAY (de ho tro tu xa)")
mt = PB.mo_ta_noi_chay()
check("co noi dung, co nhac duong dan", bool(mt) and str(ROOT) in mt, mt)

print()
print("=" * 64)
print(f"KET QUA: {pas} PASS / {fail} FAIL")
print("=" * 64)
sys.exit(1 if fail else 0)
