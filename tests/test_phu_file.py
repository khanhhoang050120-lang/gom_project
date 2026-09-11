# -*- coding: utf-8 -*-
"""Chot tinh E-03: moi file ma nguon dang ke phai co it nhat MOT bo kiem cham toi.

Vi sao can:
  Du an co ~690 phep kiem - mat do rat cao. Nhung mat do KHONG bang PHU DEU.
  Mot module 553 dong viet gan day nhat co the khong co bo kiem nao cham toi,
  trong khi no chua san `except Exception: pass` va nhieu cai bay tkinter da
  tung vap. Nhung loi do da sua - nhung khong co gi giu cho chung khoi quay
  lai.

  Bai hoc da ghi trong `test_xem_tien_trinh.py`: "mot file khong co bo kiem
  thi moi bang tong ket xanh deu la xanh GIA o phan do". Va `test_dung_do.py`
  da chung minh bang phep thu dot bien: pha `index_by_names` cho luon tra {}
  ma 27/27 bo kiem van DAT.

Cach kiem: quet ma nguon cac bo kiem tim dau vet NAP MODULE (import, ten file
trong spec_from_file_location, duong dan dang chuoi). Khong chay bo kiem nao,
nen luon chay duoc o moi noi - ke ca runner sach khong ffmpeg/NAS/tkinter.

HAI cai bay da vap khi viet chinh bo nay - ghi lai de khong ai go bo:
  1. Bo gom ca `tests/*.py` vao chuoi tim kiem, MA CHINH DOCSTRING cua no
     nhac ten file dang thieu test de giai thich van de. Ket qua: file khong
     co bo kiem nao van "duoc cham toi". Chot tinh phat hien lo hong TU BIT
     MAT CHINH MINH. Vi vay phai loai chinh file nay ra.
  2. Ten file nam trong COMMENT khong chung minh duoc gi. Phai loc comment va
     docstring, chi doc dong ma thuc thi.

Han che da biet (noi that thay vi giau):
  Bo nay kiem "co ai CHAM toi file khong", KHONG kiem "cham co ky khong". Mot
  file duoc nap nhung chi goi mot ham tam thuong van qua duoc. Do la ly do
  E-05 (mutation testing) ton tai song song - no tra loi cau hoi con lai.
"""
from __future__ import annotations

import io
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"

# Nguong dong: duoi muc nay thi mot file thuong chi la vo mong / hang so.
NGUONG_DONG = 150

# File duoc mien, kem LY DO cu the. Khong duoc mien ma khong noi vi sao -
# mien bua de lay bang xanh chinh la nhom C trong bug.md.
MIEN = {
    "goi_project_capcut.py": "diem vao, duoc phu qua E2E + hau het bo kiem",
}

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

    Dung `tokenize` chu khong regex: mot dau '#' ben trong chuoi khong phai
    comment, va regex se cat nham.
    """
    giu = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(nd).readline):
            if tok.type == tokenize.COMMENT:
                continue
            if tok.type == tokenize.STRING:
                dau = tok.line.lstrip()[:4]
                if dau.startswith(('"""', "'''")) or dau[1:].startswith(('"""', "'''")):
                    continue      # docstring / chuoi tai lieu dung rieng dong
            giu.append(tok.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return nd                 # khong phan tich duoc thi giu nguyen, khong nuot
    return "\n".join(giu)


def _dem_dong(p: Path) -> int:
    return len(p.read_text(encoding="utf-8", errors="replace").splitlines())


def _file_nguon() -> list[Path]:
    """Moi .py cua du an, tru tests/, python/ (ban nhung) va __pycache__."""
    ra = []
    for p in ROOT.rglob("*.py"):
        cac = set(p.parts)
        if "tests" in cac or "python" in cac or "__pycache__" in cac:
            continue
        if p.name == "__init__.py":
            continue
        ra.append(p)
    return sorted(ra)


def main():
    nguon = _file_nguon()
    check("tien de: tim thay it nhat 8 file nguon", len(nguon) >= 8,
          f"chi thay {len(nguon)}")

    # Gom ma nguon bo kiem, BO CHINH FILE NAY ra (bay so 1 o docstring dau
    # file), va chi giu DONG MA THAT (bay so 2).
    toi = Path(__file__).resolve()
    ma_test = "\n".join(
        _chi_ma_that(p.read_text(encoding="utf-8", errors="replace"))
        for p in TESTS.glob("*.py")
        if p.resolve() != toi)
    check("tien de: doc duoc ma nguon bo kiem", len(ma_test) > 10000,
          f"chi doc duoc {len(ma_test)} ky tu")

    ho = []          # file dang ke ma khong ai cham
    da_kiem = 0
    for p in nguon:
        dong = _dem_dong(p)
        if dong < NGUONG_DONG or p.name in MIEN:
            continue
        da_kiem += 1
        ten = p.name                       # "cua_so_hang_doi.py"
        goc = p.stem                       # "cua_so_hang_doi"
        # Ba cach mot bo kiem co the nap module nay:
        cham = (ten in ma_test                            # spec_from_file_location
                or f"import {goc}" in ma_test             # import truc tiep
                or f"{p.parent.name}.{goc}" in ma_test)   # ui.cua_so_hang_doi
        if not cham:
            ho.append(f"{p.relative_to(ROOT)} ({dong} dong)")

    check(f"tien de: co kiem that (da xet {da_kiem} file >= {NGUONG_DONG} dong)",
          da_kiem >= 5, f"chi xet {da_kiem}")
    check(f"moi file >= {NGUONG_DONG} dong deu co bo kiem cham toi",
          not ho, "HO: " + " | ".join(ho))

    check("moi file duoc mien deu ghi ro ly do",
          all(bool(v.strip()) for v in MIEN.values()))

    print()
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
