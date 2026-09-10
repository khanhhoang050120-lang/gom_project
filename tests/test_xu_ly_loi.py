# -*- coding: utf-8 -*-
"""Trinh XU LY LOI khong duoc tu chet.

Ca hai file co the chay duoc deu ket thuc bang:
    except Exception:
        traceback.print_exc()
        input("Enter de dong...")     <-- cho nay
`input()` nem EOFError khi stdin da dong. Khi do nguoi dung thay HAI traceback
chong nhau, va loi THAT o tren bi day len khuat man hinh.

Xay ra that khi: chay qua bo lap lich, qua duong ong, hoac stdin bi chuyen huong.
Phat hien luc mo phong may con (giai nen zip roi bam .bat voi stdin gioi han).
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

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


def chay_khong_stdin(tep):
    """Chay mot file .py voi stdin DA DONG -> moi input() se nem EOFError."""
    r = subprocess.run([sys.executable, "-u", str(ROOT / tep)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=180, cwd=str(ROOT),
                       stdin=subprocess.DEVNULL)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    print("=" * 72)
    print("stdin da dong -> KHONG duoc in hai traceback chong nhau")
    print("=" * 72)

    for tep in ("xem_tien_trinh.py", "goi_project_capcut.py"):
        _ma, ra = chay_khong_stdin(tep)
        n_tb = ra.count("Traceback (most recent call last)")
        n_eof = ra.count("EOFError")
        print(f"\n  {tep}: {n_tb} traceback, {n_eof} EOFError")
        check(f"{tep}: KHONG co traceback chong nhau", n_tb <= 1,
              f"{n_tb} traceback -> trinh xu ly loi tu chet, che mat loi that")
        check(f"{tep}: khong nem EOFError tu `Enter de dong`",
              "in input(\"Enter de dong" not in ra
              and ra.count("Enter de dong") <= 1,
              f"dau ra (cuoi):\n{ra[-260:]}")

    print()
    print("=" * 72)
    print("Ca hai file deu boc `Enter de dong...`")
    print("=" * 72)
    for tep in ("xem_tien_trinh.py", "goi_project_capcut.py"):
        src = (ROOT / tep).read_text(encoding="utf-8")
        i = src.find('input("Enter de dong')
        check(f"{tep}: co boc try/except quanh `Enter de dong`",
              i > 0 and "EOFError" in src[max(0, i - 400):i + 200],
              "phai bat EOFError, neu khong trinh xu ly loi se tu chet")

    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
