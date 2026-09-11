# -*- coding: utf-8 -*-
r"""Kiem chung NGUOC cho cong CI: pha code that -> bo kiem PHAI do.

KHONG phai bo kiem thuong quy. Chay bang tay truoc khi tin vao CI:

    python tests\cong_cu\kiem_chung_nguoc.py

Vi sao ton tai:
  "Mot CI chua tung do la mot CI chua duoc chung minh." Mot workflow xanh
  chi chung to no CHAY duoc, khong chung to no BAT duoc loi. Neu `chay_het.py`
  bi hong (vi du luon tra 0), CI van xanh mai mai va khong ai biet.

Khac gi `cong_cu/dot_bien.py`:
  - `dot_bien.py` pha MOT module, hoi "bo kiem cua module do co lo hong khong".
  - File nay pha NHIEU module khac nhau o cac tang khac nhau, hoi "toan bo
    cong CI co bat duoc khong, va co bat DUNG CHO khong".

Moi phep deu ghi ro bo kiem MONG DOI se do. Neu do nhung do SAI bo, do cung
la mot phat hien - nghia la phep kiem dang bat vi ly do khac voi ta tuong.

KHOI PHUC: moi file goc duoc ghi lai trong `finally`. Neu tien trinh bi giet
giua chung, kiem `git status` TRUOC khi lam tiep - da tung xay ra that.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# (mo ta, file bi pha, chuoi cu, chuoi moi, bo kiem MONG DOI do)
CAC_PHEP = [
    ("tang duong dan: _lp() bo prefix UNC",
     "chung.py",
     'return "\\\\\\\\?\\\\UNC\\\\" + ap[2:]',
     'return ap',
     "test_duong_dan.py"),

    ("tang duong dan: _lp() tra nguyen, khong them prefix",
     "chung.py",
     'return "\\\\\\\\?\\\\" + ap',
     'return ap',
     "test_duong_dan.py"),

    ("cau noi: tra loi bua cho cau hoi la thay vi nem",
     "ui/cau_noi.py",
     "raise RuntimeError(",
     "return '1'  # ",
     "test_cau_noi.py"),

    ("kiem dau vao: bo chan duong dan drive-relative 'D:'",
     "ui/kiem_dau_vao.py",
     "def kiem_out(",
     "def kiem_out_DA_TAT(",
     "test_kiem_dau_vao.py"),

    ("hang doi: mot muc LOI lam dung ca hang doi",
     "ui/hang_doi.py",
     "except BaseException as ex:",
     "except ValueError as ex:",
     "test_hang_doi_ui.py"),

    ("cua so hang doi: bo gioi han 200 tin moi nhip",
     "ui/cua_so_hang_doi.py",
     "for _ in range(200):",
     "while True:",
     "test_cua_so_hang_doi.py"),

    # Phep quan trong nhat: pha viec VIET LAI duong dan - loi duy nhat lam
    # goi mat tac dung hoan toan (mo tren may khac se thieu clip). Verifier
    # DOC LAP phai bat duoc, chu khong phai bo kiem dung ham cua chinh tool.
    ("viet lai duong dan: deep_rewrite_strings khong thay gi",
     "chung.py",
     "                if nv is not None and nv != v:",
     "                if False:",
     "test_e2e.py"),

    # Moc phai DUY NHAT trong file. `"scale": bool(self.v_scale.get()),`
    # xuat hien o CA `_bat_dau()` lan `_mo_hang_doi()`, nen replace(...,1)
    # se pha nham cho dau tien va dot bien "song sot" mot cach gia tao.
    ("duong ghep: khong chup tuy chon muc 4 sang hang doi",
     "giao_dien.py",
     '            "cleanup": bool(self.v_clean.get()),' + chr(10) +
     '            "do": self._lam_sach_ds_duong_dan(self.v_do.get()),',
     '            "cleanup": True,' + chr(10) + '            "do": "",',
     "test_duong_ghep_ui.py"),

    ("duong ghep: mo lan hai tao them cua so thu hai",
     "giao_dien.py",
     '                    self._cs_hd.root.lift()\n                    return',
     '                    pass',
     "test_duong_ghep_ui.py"),

    ("hai luong: dung mot co huy chung cho ca hai pha",
     "giao_dien.py",
     "        self.co_huy_quet = threading.Event()",
     "        self.co_huy_quet = self.co_huy",
     "test_duong_ghep_ui.py"),

    # --- Auto-update: 4 rui ro muc Cao, hau qua 40-50 may cung luc.
    # Dot bien phai DOI HANH VI. Ban dau dung `str(so_a) != str(so_b)` -
    # van dung nen no la dot bien TUONG DUONG, khong do duoc gi. Pha dung
    # cho: so sanh CHUOI thay vi so sanh TUNG SO ("1.10.0" < "1.9.0").
    ("cap nhat: so sanh phien ban bang CHUOI (1.10.0 < 1.9.0)",
     "loi/cap_nhat.py",
     "        return so_a > so_b",
     "        return str(so_a) > str(so_b)",
     "test_cap_nhat.py"),

    ("cap nhat: khong chan khi dang goi do (R-02)",
     "loi/cap_nhat.py",
     "    return not (dang_chay or hang_doi_chay)",
     "    return True",
     "test_cap_nhat.py"),

    ("cap nhat: hoi may chu NEM ra ngoai khi mat mang (R-10)",
     "loi/cap_nhat.py",
     "    except Exception:",
     "    except KeyboardInterrupt:",
     "test_cap_nhat.py"),

    ("cap nhat: bo kiem DU FILE truoc khi doi ten (R-14)",
     "loi/cap_nhat.py",
     "    if not du_file(moi):",
     "    if False:",
     "test_cap_nhat.py"),

    ("cap nhat: khong dua ban cu tro lai khi buoc 5 hong (R-03)",
     "loi/cap_nhat.py",
     "            doi_ten(str(cu), str(cai))",
     "            pass",
     "test_cap_nhat.py"),

    ("bo may kiem: chay_het.py luon bao thanh cong",
     "tests/chay_het.py",
     "    if hong:",
     "    if False:",
     "test_bo_may_kiem.py"),
]


def chay_bo(tep: str, gio: int = 420):
    t0 = time.monotonic()
    try:
        r = subprocess.run([sys.executable, "-u", str(ROOT / "tests" / tep)],
                           cwd=str(ROOT), timeout=gio, capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        return r.returncode, (r.stdout or ""), time.monotonic() - t0
    except subprocess.TimeoutExpired:
        return "QUA GIO", "", time.monotonic() - t0


def main():
    print("=" * 72)
    print(" KIEM CHUNG NGUOC - pha code that, bo kiem PHAI do")
    print("=" * 72)

    bat = sot = 0
    for mo_ta, tep, cu, moi, bo in CAC_PHEP:
        f = ROOT / tep
        goc = f.read_bytes()
        if cu.encode("utf-8") not in goc:
            print(f"\n  ?? BO QUA  {mo_ta}")
            print(f"       khong tim thay moc trong {tep}")
            print(f"       (ma nguon da doi? Kiem lai phep nay.)")
            continue

        print(f"\n  >> {mo_ta}")
        print(f"     pha {tep}, mong doi {bo} DO")
        try:
            f.write_bytes(goc.replace(cu.encode("utf-8"), moi.encode("utf-8"), 1))
            ma, ra, giay = chay_bo(bo)
            do = [d.strip() for d in ra.splitlines()
                  if d.strip().startswith("FAIL")]
            if ma == 0:
                sot += 1
                print(f"     !! KHONG BAT DUOC ({giay:.1f}s) - bo kiem VAN XANH")
                print(f"        => cong CI co lo hong o tang nay")
            else:
                bat += 1
                print(f"     OK bat duoc ({giay:.1f}s, ma {ma})")
                if do:
                    print(f"        {do[0][:88]}")
        finally:
            f.write_bytes(goc)

    tong = bat + sot
    print()
    print("=" * 72)
    print(f"  Bat duoc: {bat}/{tong}")
    if sot:
        print(f"  => {sot} cho PHA MA KHONG AI BIET. Day la lo hong that su")
        print("     cua cong CI, khong phai loi cua phep kiem chung nguoc.")
        return 1
    print("  => Cong CI da duoc CHUNG MINH: pha o dau cung bi bat.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
