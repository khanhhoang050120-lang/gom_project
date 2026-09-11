# -*- coding: utf-8 -*-
"""Chot tinh: moi bo kiem phai DUOC CHAY va phai NOI duoc ket qua.

Sinh ra tu mot phat hien cu the: 9 bo kiem (test_cau_noi, test_kiem_dau_vao,
test_hang_doi_ui, test_phien_ban, test_quet_thu, test_lech_von_co,
test_hang_doi, test_hang_doi_log, test_tieng_viet) in dong tong ket theo khuon
  "  PASS 27   FAIL 0"
trong khi `chay_het.py` loc dau ra bang `"KET QUA" in d`. Ket qua: 113 phep
kiem chay that nhung VO HINH tren bang tong ket - khong ai biet chung co chay
hay khong, va neu mot bo trong so do hong thi dong FAIL van hien nhung so
lieu tong thi khong.

Day dung la nhom C trong bug.md: bao cao khong khop viec that su da lam.

Ba dieu duoc chot o day - tat ca deu la chot TINH, chay trong mili giay:
  1. Moi `tests/test_*.py` deu co mat trong `BO_KIEM` (khong co bo mo coi).
  2. Moi muc trong `BO_KIEM` deu tro toi file co that (khong co muc ma).
  3. Moi bo kiem deu in duoc chuoi `KET QUA:` dung khuon `chay_het.py` loc.

Khong chay bo kiem nao - chi doc ma nguon. Vi vay bo nay luon chay duoc o moi
noi, ke ca runner sach khong co ffmpeg/NAS/tkinter.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"

pas = fail = 0


def check(ten, dk, ct=""):
    global pas, fail
    if dk:
        pas += 1
        print(f"  PASS  {ten}")
    else:
        fail += 1
        print(f"  FAIL  {ten}" + (f"  | {ct}" if ct else ""))


def _doc_bo_kiem() -> list[str]:
    """Doc danh sach ten file trong BO_KIEM cua chay_het.py.

    Doc bang REGEX tren ma nguon chu khong `import` - import se chay ca file
    va lam bo kiem nay phu thuoc vao thu no dang kiem.
    """
    s = (TESTS / "chay_het.py").read_text(encoding="utf-8")
    khoi = s[s.index("BO_KIEM = ["):]
    khoi = khoi[: khoi.index("\n]")]
    return re.findall(r'"([A-Za-z0-9_]+\.py)"', khoi)


def main():
    # ---- TIEN DE: khong co du lieu thi moi ket luan duoi deu vo nghia.
    tep_test = sorted(p.name for p in TESTS.glob("test_*.py"))
    trong_bo = _doc_bo_kiem()
    check("tien de: tim thay it nhat 20 file test_*.py", len(tep_test) >= 20,
          f"chi thay {len(tep_test)}")
    check("tien de: doc duoc it nhat 20 muc trong BO_KIEM", len(trong_bo) >= 20,
          f"chi doc duoc {len(trong_bo)}")

    # ---- 1. Khong co bo kiem MO COI (co file nhung khong ai chay).
    mo_coi = [t for t in tep_test if t not in trong_bo]
    check("khong co bo kiem mo coi (file co nhung khong nam trong BO_KIEM)",
          not mo_coi, "mo coi: " + ", ".join(mo_coi))

    # ---- 2. Khong co muc MA (dang ky nhung file khong ton tai).
    thieu = [t for t in trong_bo if not (TESTS / t).is_file()]
    check("khong co muc ma trong BO_KIEM (dang ky ma khong co file)",
          not thieu, "thieu: " + ", ".join(thieu))

    # ---- 3. Moi bo kiem phai in duoc chuoi `KET QUA:`.
    #  `chay_het.py` loc dau ra bang `"KET QUA" in d`; bo nao khong in thi ket
    #  qua cua no vo hinh tren bang tong ket.
    cam_mieng = []
    for t in tep_test:
        nd = (TESTS / t).read_text(encoding="utf-8", errors="replace")
        if "KET QUA" not in nd:
            cam_mieng.append(t)
    check("moi bo kiem deu in chuoi 'KET QUA:' (khong bo nao vo hinh)",
          not cam_mieng, "cam mieng: " + ", ".join(cam_mieng))

    # ---- 4. Khuon phai dung het: "KET QUA: N PASS / M FAIL".
    #  Chi canh bao khi LECH khuon, vi chay_het chi can chuoi con "KET QUA".
    #  Nhung khuon thong nhat giup doc bang tong ket nhanh hon nhieu.
    khuon = re.compile(r"KET QUA: \{?\w*\}? ?PASS / \{?\w*\}? ?FAIL")
    lech = []
    for t in tep_test:
        nd = (TESTS / t).read_text(encoding="utf-8", errors="replace")
        if "KET QUA" in nd and not khuon.search(nd):
            lech.append(t)
    check("moi bo kiem dung dung khuon 'KET QUA: N PASS / M FAIL'",
          not lech, "lech khuon: " + ", ".join(lech))

    print()
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
