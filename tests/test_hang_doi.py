# -*- coding: utf-8 -*-
"""HANG DOI - chay `main()` NHIEU LAN trong CUNG mot tien trinh.

O che do dong lenh va giao dien mot project, moi lan goi la mot TIEN TRINH moi
nen trang thai toan cuc chet theo tien trinh. Hang doi nhieu project thi KHONG:
project sau thua huong moi thu cua project truoc.

Bo kiem nay chot ba dieu:
  1. `xoa_cache_ton_tai()` that su xoa, va KHONG duoc la code chet
  2. Cache khong dinh giua hai lan chay (ca hai chieu)
  3. Canh gac duoc tat sau moi lan chay - khong tich luy
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

import goi_project_capcut as G      # noqa: E402
import toi_uu_dung_luong as TU      # noqa: E402

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


print("=" * 68)
print(" HANG DOI - goi main() nhieu lan trong cung mot tien trinh")
print("=" * 68)

# ------------------------------------------------------- cache dinh hai chieu
print("\nCACHE `_exists` KHONG duoc dinh giua hai lan chay")
tmp = Path(tempfile.mkdtemp(prefix="hang_doi_"))
try:
    f = tmp / "canh1.mp4"

    # Chieu 1: hoi khi CHUA co -> tao that -> hoi lai
    TU.xoa_cache_ton_tai()
    check("file chua tao -> False", TU._exists(f) is False)
    f.write_bytes(b"day la file that")
    check("VAN False khi chua xoa cache (dung nhu thiet ke)",
          TU._exists(f) is False)
    TU.xoa_cache_ton_tai()
    check("sau khi xoa cache -> True (thay file that)",
          TU._exists(f) is True,
          "cache van dinh -> project sau se bao THIEU FILE oan")

    # Chieu 2: hoi khi CO -> xoa that -> hoi lai
    g = tmp / "canh2.mp4"
    g.write_bytes(b"x")
    TU.xoa_cache_ton_tai()
    check("file co that -> True", TU._exists(g) is True)
    g.unlink()
    TU.xoa_cache_ton_tai()
    check("sau khi XOA file va xoa cache -> False",
          TU._exists(g) is False,
          "cache dinh chieu nguoc -> tool tuong file con, copy se that bai")
finally:
    for x in tmp.glob("*"):
        try:
            x.unlink()
        except OSError:
            pass
    try:
        tmp.rmdir()
    except OSError:
        pass

# ------------------------------------------------- xoa that su, khong rong tuech
print("\n`xoa_cache_ton_tai()` phai THAT SU xoa")
TU._EXIST_CACHE[os.path.normcase("D:\\gia\\lap.mp4")] = True
truoc = len(TU._EXIST_CACHE)
TU.xoa_cache_ton_tai()
check("cache rong sau khi goi",
      len(TU._EXIST_CACHE) == 0 and truoc > 0,
      f"truoc {truoc}, sau {len(TU._EXIST_CACHE)}")

# ------------------------------------------------- khong duoc la code chet
print("\nKHONG duoc la CODE CHET (bay o bug.md #52)")
src = (ROOT / "goi_project_capcut.py").read_text(encoding="utf-8")
check("`xoa_cache_ton_tai()` co nguoi goi",
      "xoa_cache_ton_tai()" in src,
      "dinh nghia ma khong ai goi = bug van song")


def than_ham(ten):
    """Cat than mot ham tu `def <ten>(` toi `def` ke tiep o cot 0.

    KHONG cat cung so ky tu: mot bo kiem cat 1200 ky tu se hong ngay khi ai do
    them mot doan chu thich - va no bao FAIL cho mot ly do HOAN TOAN khac cai
    no dinh kiem. Da dinh dung bay nay khi viet chinh bo kiem nay.
    """
    i = src.index(f"def {ten}(")
    j = src.index("\ndef ", i + 1)
    return src[i:j]


than_main = than_ham("main")
check("goi NGAY trong than `main()`, khong phai cho khac",
      "xoa_cache_ton_tai()" in than_main,
      "phai goi o main() - noi MOI lan chay deu di qua")
check("cung xoa ca cache probe",
      "xoa_cache_probe()" in than_main)

# ------------------------------------------------- canh gac khong tich luy
print("\nCANH GAC phai duoc tat sau moi lan chay")
check("`main()` bọc `_main_than()` trong try/finally",
      "finally:" in than_main,
      "13 duong return trong than -> khong co finally la canh gac song mai")
check("`finally` co goi .dung()", ".dung()" in than_main)
check("viec xoa cache KHONG duoc lam hong lan chay",
      "except Exception:" in than_main,
      "thieu module toi uu thi che do 1 van phai chay duoc")

# ------------------------------------------------- loi probe don sach
print("\nLOI PROBE phai don sach giua cac lan")
TU._LOI_PROBE.append(("gia.mp4", "loi gia"))
r1 = TU.lay_loi_probe()
r2 = TU.lay_loi_probe()
check("lan doc thu nhat co du lieu", len(r1) == 1, f"{r1}")
check("lan doc thu hai da sach", len(r2) == 0,
      f"{r2} -> project sau se thay loi cua project truoc")

print()
print("=" * 68)
print(f"KET QUA: {pas} PASS / {fail} FAIL")
print("=" * 68)
sys.exit(1 if fail else 0)
