# -*- coding: utf-8 -*-
"""bug #105 - tieng Viet CO DAU phai in duoc tren may ACP 1258.

May phat trien co ACP 65001 nen `print("Cắt gọn")` khong bao gio loi.
May con Windows tieng Viet mac dinh ACP 1258 -> UnicodeEncodeError, CHET
ca tien trinh. Day dung loai loi ma bug.md #68 canh bao: "may phat trien
trung nhau nen KHONG BAO GIO lo loi".

Bo kiem nay PHAI chay trong TIEN TRINH CON voi PYTHONIOENCODING=cp1258.
Chay trong chinh tien trinh nay la vo nghia - no se luon PASS tren may
phat trien va khong bao gio bat duoc gi.
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

from loi.bang_ma import ep_utf8, mo_ta_bang_ma   # noqa: E402

pas = fail = 0
CHU = "Cắt gọn footage dài — Hạ 4K/nén bitrate — Bỏ file mồ côi"


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


def chay_con(than, cp=None):
    """Chay mot doan Python trong tien trinh con, co the ep bang ma."""
    tmp = Path(tempfile.mkdtemp(prefix="tv_"))
    try:
        f = tmp / "t.py"
        f.write_text("# -*- coding: utf-8 -*-\n" + than, encoding="utf-8")
        e = dict(os.environ)
        if cp:
            e["PYTHONIOENCODING"] = cp
        else:
            e.pop("PYTHONIOENCODING", None)
        # PHAI ep sys.path: ban Python di kem dung `._pth`
        e["PYTHONPATH"] = str(ROOT)
        r = subprocess.run([sys.executable, str(f)], capture_output=True,
                           env=e, timeout=120)
        return r.returncode, r.stdout.decode("utf-8", "replace").strip(), \
            r.stderr.decode("utf-8", "replace").strip()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


print("=" * 70)
print(" bug #105 - tieng Viet co dau tren may ACP 1258")
print("=" * 70)
print(f"  May nay: {mo_ta_bang_ma()}")

# ------------------------------------------------- 1. chung minh loi CO THAT
print("\n1. CHUNG MINH loi co that (khong ep -> chet)")
ma, ra, loi = chay_con(f"print({CHU!r})", cp="cp1258")
check("khong ep bang ma -> CHET tren cp1258",
      ma != 0 and "UnicodeEncodeError" in loi,
      f"rc={ma}, stderr={loi[-100:]}")
check("loi dung la 'charmap codec can't encode'",
      "charmap" in loi and "encode" in loi, loi[-120:])

# ------------------------------------------------- 2. ep_utf8() sua duoc
print("\n2. `ep_utf8()` sua duoc loi do")
than = ("import sys\n"
        "from loi.bang_ma import ep_utf8\n"
        "ep_utf8()\n"
        f"print({CHU!r})\n")
for cp in ("cp1258", "cp1252", "cp1251", None):
    ma, ra, loi = chay_con(than, cp=cp)
    nhan = cp or "(mac dinh)"
    check(f"{nhan:12s} -> in dung, khong chet",
          ma == 0 and ra == CHU,
          f"rc={ma}, ra={ra[:50]!r}, stderr={loi[-90:]}")

# ------------------------------------------------- 3. cac diem vao that
print("\n3. CAC DIEM VAO that da ep chua")
for ten in ("goi_project_capcut", "giao_dien", "xem_tien_trinh"):
    src = (ROOT / f"{ten}.py").read_text(encoding="utf-8")
    check(f"{ten}.py co goi ep_utf8()",
          "ep_utf8" in src,
          "thieu -> may con se chet khi in chu co dau")

# `goi_project_capcut` phai ep TRUOC dong `print` dau tien
src = (ROOT / "goi_project_capcut.py").read_text(encoding="utf-8")
i_ep = src.find("_ep_utf8()")
i_print = src.find("\n    print(")
check("ep TRUOC dong print dau tien",
      0 < i_ep < i_print,
      f"vi tri ep={i_ep}, print dau={i_print}")

# ------------------------------------------------- 4. khong duoc nem
print("\n4. `ep_utf8()` KHONG duoc nem trong moi truong hop")
than2 = ("import sys\n"
         "sys.stdout = None\n"          # gia lap pythonw
         "sys.stderr = None\n"
         "from loi.bang_ma import ep_utf8\n"
         "ep_utf8()\n"
         "sys.stdout = sys.__stdout__\n"
         "print('khong nem')\n")
ma, ra, loi = chay_con(than2)
check("stdout=None (pythonw) -> khong nem",
      ma == 0 and "khong nem" in ra, f"rc={ma}, {loi[-90:]}")

than3 = ("import sys\n"
         "class Gia:\n"
         "    def write(self, s): return len(s)\n"
         "    def flush(self): pass\n"
         "sys.stdout = Gia()\n"          # lop gia khong co reconfigure
         "from loi.bang_ma import ep_utf8\n"
         "ep_utf8()\n"
         "sys.stdout = sys.__stdout__\n"
         "print('van chay')\n")
ma, ra, loi = chay_con(than3)
check("stdout la lop gia (khong co reconfigure) -> khong nem",
      ma == 0 and "van chay" in ra, f"rc={ma}, {loi[-90:]}")

# ------------------------------------------------- 5. goi hai lan
print("\n5. Goi nhieu lan")
check("goi lai tra True, khong nem", ep_utf8() is True)
check("bat_buoc=True cung khong nem", ep_utf8(bat_buoc=True) is True)

print()
print("=" * 70)
print(f"  PASS {pas}   FAIL {fail}")
print("=" * 70)
sys.exit(1 if fail else 0)
