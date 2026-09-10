# -*- coding: utf-8 -*-
"""Nhip dap phai noi DANG LAM GI, khong chi "chua xong them clip nao".

Do that tren DS3_094: mot clip YouTube dai 25 phut 18 giay (`-t 1517.633`) chiem
gan NUA thoi gian ca job. Nhip dap im lang 15 phut lien, chi lap lai
    [nhip dap] 5/6 clip  (28.1 phut)  (chua xong them clip nao)
Nguoi dung may con doc dong do 15 lan se ket luan tool TREO va End Task - dung
thu tung lam hong draft cua chinh nguoi dung (xem dau bug.md).

Toi da phai do bang `wmic` (CPU time +363s/40s thuc) moi biet ffmpeg dang chay
that. Nguoi dung khong lam duoc dieu do.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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


def main():
    src = (ROOT / "toi_uu_dung_luong.py").read_text(encoding="utf-8")

    print("=" * 72)
    print("Nhip dap phai noi ro dang ma clip nao")
    print("=" * 72)

    check("co theo doi clip DANG ma", "dang_lam = {}" in src,
          "khong co bang theo doi -> nhip dap khong biet gi de noi")
    check("ghi vao bang TRUOC khi ma", "dang_lam[id(j)] =" in src)
    check("xoa khoi bang trong `finally`",
          re.search(r"finally:\s*\n\s*dang_lam\.pop", src) is not None,
          "ma lai that bai ma khong xoa -> bang phinh mai, bao clip da xong"
          " la 'dang ma'")
    check("nhip dap in ten clip dang ma", "dang ma:" in src)
    check("in ca THOI GIAN da chay cua clip do", "da chay" in src,
          "biet ten ma khong biet da chay bao lau thi van khong ket luan duoc")
    check("in do dai DOAN dang ma", "doan" in src and "_span" in src,
          "clip 25 phut ma lau la binh thuong - phai cho nguoi dung thay do dai")
    check("noi ro khi KHONG clip nao dang ma",
          "khong clip nao dang ma" in src,
          "truong hop nay moi la dang ngo (dang doi I/O hoac that su treo)")

    print()
    print("=" * 72)
    print("An toan da luong")
    print("=" * 72)
    check("dung dict (an toan cho gan/xoa giua cac thread)",
          "dang_lam = {}" in src and "dang_lam.pop(id(j), None)" in src,
          "khong duoc dung list voi index - hai thread se dam nhau")
    check("doc bang qua ban SAO trong nhip dap",
          "list(dang_lam.values())" in src,
          "duyet truc tiep dict trong khi thread khac xoa -> RuntimeError"
          " 'dictionary changed size during iteration' (dung bug da gap)")
    check("gioi han so dong in", "[:3]" in src,
          "chay 8 luong ma in het thi nhip dap thanh bao lu")

    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
