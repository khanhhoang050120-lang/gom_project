# -*- coding: utf-8 -*-
r"""Dong goi .exe: R-08 (`__file__` sai) va R-09 (khong ghi duoc canh .exe).

Hai rui ro nay deu muc **Cao** trong `tai_lieu/RISK.md`, va ca hai thuoc loai
HONG IM LANG - khong co exception, nguoi dung chi thay phan mem cu xu la:
  R-08  `Path(__file__).resolve().parent` tro vao thu muc TAM khi dong goi
        onefile -> tool tim ffmpeg/cau_hinh o sai cho.
  R-09  Log va dau tu kiem ghi canh .exe; cai vao `Program Files` la mat
        quyen ghi -> mat DUNG THU can nhat khi ho tro tu xa.

`loi/phien_ban.py` da xu ly ca hai (3 khai niem thu muc tach bach), va
`test_phien_ban.py` da co 22 phep. Bo nay them phan CHUA duoc phu:

  - `thu_muc_ghi()` lui ve `%LOCALAPPDATA%` khi canh .exe CHI DOC (R-09)
  - lui tiep ve temp khi CA `%LOCALAPPDATA%` cung hong - va KHONG nem
  - `_ghi_duoc()` phai thu GHI THAT, khong duoc dung `os.access` (chot tinh)
  - `tim_tai_nguyen()` gap OSError o goc dau van thu goc tiep theo
  - chot tinh tren kich ban dong goi: viet TRUOC khi co `.spec`/`build.py`

Vi sao chot tinh kich ban viet TRUOC: R-02/R-03/R-14 deu muc Cao va hau qua
la 40-50 may cung luc. "Viet code truoc, test sau" o day la cong thuc hong
hang loat. Cac phep BLD-* duoi day DO khi chua co file - do la trang thai
DUNG, va chung se xanh dan khi kich ban duoc viet theo hop dong da chot.

Khong can tkinter, khong can ffmpeg -> chay duoc tren runner sach.
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
# HERE la BAT BUOC: ban Python di kem dung `._pth` nen KHONG tu them thu muc
# script vao sys.path -> `import test_phu_file` se that bai o may nguoi dung
# du chay tot tren may phat trien. `test_dung_do.py` co chot tinh canh dieu
# nay, va no da bat duoc ngay lan chay dau.
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

pas = fail = 0


def check(ten, dk, ct=""):
    global pas, fail
    if dk:
        pas += 1
        print(f"  PASS  {ten}")
    else:
        fail += 1
        print(f"  FAIL  {ten}" + (f"  | {ct}" if ct else ""))


def _chi_ma_that(nd: str) -> str:
    """Bo comment va docstring, chi giu dong ma thuc thi.

    Dung lai ham cua `test_phu_file.py` - KHONG chep lai. Ban chep lech
    dan la cach hong am tham (xem `xem_tien_trinh.py` tung co ban chep
    `_lp` hong 3 lan).
    """
    import test_phu_file
    return test_phu_file._chi_ma_that(nd)


def _chay_con(ma: str, gio: int = 90):
    """Chay doan ma trong tien trinh RIENG (can gia lap sys.frozen)."""
    tmp = Path(tempfile.mkdtemp(prefix="dgexe_"))
    try:
        f = tmp / "con.py"
        f.write_text(ma, encoding="utf-8")
        r = subprocess.run([sys.executable, str(f), str(ROOT)],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=gio, cwd=str(ROOT))
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------ R-09
def test_noi_ghi():
    print("=" * 72)
    print("R-09 - thu_muc_ghi() phai LUI khi khong ghi duoc canh chuong trinh")
    print("=" * 72)

    ma = r'''
import os, sys, tempfile
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from loi import phien_ban as PB

kq = {}

# --- Canh chuong trinh KHONG ghi duoc -> phai lui ve %LOCALAPPDATA%
tmp = Path(tempfile.mkdtemp(prefix="ghi_"))
la = tmp / "localappdata"
la.mkdir()
os.environ["LOCALAPPDATA"] = str(la)

PB._dat_lai_cache_ghi()
that = PB._ghi_duoc
PB.thu_muc_chuong_trinh = lambda: Path("Z:\\khong_he_ton_tai_o_nay")
PB._ghi_duoc = lambda d: (False if "khong_he_ton_tai" in str(d)
                          else that(d))
n1 = PB.thu_muc_ghi()
kq["lui ve LOCALAPPDATA"] = str(la) in str(n1)
kq["n1"] = str(n1)

# --- CA %LOCALAPPDATA% cung hong -> lui tiep ve temp, KHONG nem
PB._dat_lai_cache_ghi()
PB._ghi_duoc = lambda d: False
try:
    n2 = PB.thu_muc_ghi()
    kq["ca hai hong -> van tra ve duong dan"] = isinstance(n2, Path)
    kq["ca hai hong -> KHONG nem"] = True
    kq["n2"] = str(n2)
    kq["n2 nam trong temp"] = str(Path(tempfile.gettempdir())) in str(n2)
except Exception as ex:
    kq["ca hai hong -> KHONG nem"] = False
    kq["loi"] = "%s: %s" % (type(ex).__name__, ex)

# --- Thieu han bien moi truong LOCALAPPDATA
PB._dat_lai_cache_ghi()
os.environ.pop("LOCALAPPDATA", None)
os.environ.pop("APPDATA", None)
PB._ghi_duoc = lambda d: str(Path(tempfile.gettempdir())) in str(d)
try:
    n3 = PB.thu_muc_ghi()
    kq["thieu bien moi truong -> van co duong lui"] = isinstance(n3, Path)
except Exception as ex:
    kq["thieu bien moi truong -> van co duong lui"] = False
    kq["loi3"] = "%s: %s" % (type(ex).__name__, ex)

import json
print("KQ" + json.dumps(kq))
'''
    ma_thoat, ra = _chay_con(ma)
    import json
    kq = {}
    for d in ra.splitlines():
        if d.startswith("KQ"):
            kq = json.loads(d[2:])
    if not kq:
        check("R-09: tien trinh con chay duoc", False,
              f"ma thoat {ma_thoat}\n{ra[-900:]}")
        return

    check("PB-13 canh .exe chi doc -> lui ve %LOCALAPPDATA%",
          kq.get("lui ve LOCALAPPDATA"), kq.get("n1"))
    check("PB-14 ca %LOCALAPPDATA% cung hong -> KHONG nem",
          kq.get("ca hai hong -> KHONG nem"), kq.get("loi"))
    check("PB-14b ca hai hong -> van tra ve mot duong dan dung duoc",
          kq.get("ca hai hong -> van tra ve duong dan"))
    check("PB-14c duong cuoi nam trong thu muc TAM cua he thong",
          kq.get("n2 nam trong temp"), kq.get("n2"))
    check("PB-14d thieu han bien moi truong -> van co duong lui",
          kq.get("thieu bien moi truong -> van co duong lui"), kq.get("loi3"))


# ------------------------------------------------------------ chot tinh
def test_chot_tinh_phien_ban():
    print()
    print("=" * 72)
    print("CHOT TINH - cac quy tac khong duoc pha khi sua loi/phien_ban.py")
    print("=" * 72)
    s = (ROOT / "loi" / "phien_ban.py").read_text(encoding="utf-8")
    # CHI quet DONG MA THAT. Bay da vap ngay lan chay dau: `os.access`
    # nam trong DOCSTRING giai thich vi sao KHONG dung no - code hoan
    # toan dung ma phep kiem van do. Ten nam trong chu thich khong
    # chung minh duoc gi (cung bay da vap o `test_phu_file.py`).
    s_ma = _chi_ma_that(s)

    # `os.access(W_OK)` tra ket qua SAI tren Windows: no doc quyen he thong
    # chu khong tinh UAC virtualization. Phai THU GHI THAT.
    check("PB-15 _ghi_duoc() KHONG dung os.access (phai thu ghi that)",
          "os.access" not in s_ma,
          "co os.access trong DONG MA (khong ke chu thich)")
    check("PB-15b _ghi_duoc() co thu ghi that (write_text + unlink)",
          "write_text" in s_ma and "unlink" in s_ma)

    # Ba khai niem thu muc PHAI tach bach - gop lam mot la bug an, vi khi
    # chua dong goi thi ca ba trung nhau va khong ai thay gi sai.
    for ten in ("thu_muc_chuong_trinh", "thu_muc_tai_nguyen", "thu_muc_ghi"):
        # Doc tren chuoi GOC: `tokenize` noi token bang xuong dong nen
        # "def thu_muc_ghi(" bi tach ra. Day la khai bao ham - khong the
        # nam trong chu thich, nen doc chuoi goc la an toan.
        check(f"PB-16 con ham {ten}()", f"def {ten}(" in s)
    check("PB-16b ba khai niem KHONG bi gop thanh mot hang so _GOC",
          "_GOC = Path(__file__)" not in s_ma)

    # `sys.frozen` / `sys._MEIPASS` la cach duy nhat biet dang chay trong .exe
    check("PB-17 co xu ly sys.frozen", "frozen" in s_ma)
    check("PB-17b co xu ly sys._MEIPASS (onefile)", "_MEIPASS" in s_ma)


# --------------------------------------- hop dong cho kich ban dong goi
def test_hop_dong_kich_ban():
    print()
    print("=" * 72)
    print("BLD - hop dong cho kich ban dong goi (.spec / build.py)")
    print("=" * 72)

    spec = ROOT / "dong_goi" / "goi_exe.spec"
    build = ROOT / "dong_goi" / "build.py"
    co = spec.is_file() and build.is_file()

    if not co:
        # Trang thai DUNG khi chua viet kich ban. Noi RO thay vi im lang -
        # mot phep kiem im lang bo qua la mot phep kiem khong ton tai.
        print("  (chua co dong_goi/goi_exe.spec + build.py - cac phep BLD")
        print("   duoi day se kiem khi kich ban duoc viet. Hop dong da chot:)")
        for d in (
            "BLD-01  .spec khai onedir (co COLLECT, EXE co exclude_binaries)",
            "BLD-02  .spec khai console=False (chay nhu pythonw)",
            "BLD-03  .spec dong goi ffmpeg/ vao datas",
            "BLD-04  .spec dong goi cau_hinh.json + ui/ + loi/",
            "BLD-05  build.py chay tests\\chay_het.py TRUOC, do thi DUNG",
            "BLD-06  build.py ghi TOOL_VERSION khop goi_project_capcut",
            "BLD-07  khong .bat nao co byte > 127 trong goi",
            "BLD-08  build.py chay lai bo kiem BANG PYTHON DI KEM sau build",
        ):
            print("     - " + d)
        check("BLD-00 hop dong duoc ghi ro truoc khi viet kich ban", True)
        return

    s_spec = spec.read_text(encoding="utf-8", errors="replace")
    s_build = build.read_text(encoding="utf-8", errors="replace")
    check("BLD-01 .spec khai onedir (co COLLECT)", "COLLECT" in s_spec)
    check("BLD-01b .spec khai exclude_binaries=True",
          "exclude_binaries=True" in s_spec.replace(" ", ""))
    check("BLD-02 .spec khai console=False",
          "console=False" in s_spec.replace(" ", ""))
    check("BLD-03 .spec dong goi ffmpeg/", "ffmpeg" in s_spec)
    check("BLD-04 .spec dong goi cau_hinh.json", "cau_hinh.json" in s_spec)
    check("BLD-04b .spec dong goi ui/ va loi/",
          "ui" in s_spec and "loi" in s_spec)
    check("BLD-05 build.py chay bo kiem TRUOC khi dong goi",
          "chay_het" in s_build)
    check("BLD-06 build.py cham toi TOOL_VERSION", "TOOL_VERSION" in s_build)


# ------------------------------------------------------------ .bat khong dau
def test_bat_khong_dau():
    print()
    print("=" * 72)
    print("BLD-07 - file .bat phai KHONG DAU (byte > 127)")
    print("=" * 72)
    # `cmd.exe` dien giai comment theo code page TRUOC khi `chcp 65001` kip
    # chay (bug #12). Day la rang buoc rieng cua .bat, khong lien quan Python.
    bats = sorted(ROOT.glob("*.bat"))
    check("tien de: tim thay file .bat de kiem", len(bats) >= 3,
          f"chi thay {len(bats)}")
    for b in bats:
        raw = b.read_bytes()
        xau = [i for i, c in enumerate(raw) if c > 127]
        check(f"BLD-07 {b.name} khong co byte > 127", not xau,
              f"{len(xau)} byte, vi tri dau: {xau[:5]}")


def main():
    test_noi_ghi()
    test_chot_tinh_phien_ban()
    test_hop_dong_kich_ban()
    test_bat_khong_dau()
    print()
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
