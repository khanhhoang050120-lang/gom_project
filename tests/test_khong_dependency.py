# -*- coding: utf-8 -*-
"""Tool PHAI chi dung thu vien chuan Python - kiem tu dong, khong tin loi noi.

Vi sao dang mot bo kiem rieng:
  Quy trinh ban giao cho may con dua tren mot khang dinh: "khong co thu vien ngoai
  nao can cai". Neu sau nay ai them mot `import requests` thi:
    - may cha van chay tot (may cha co san goi do)
    - MAY CON vo ngay khi khoi dong, voi loi ModuleNotFoundError kho hieu
    - 15-20 nguoi khong phai lap trinh vien khong biet phai lam gi
  Bien khang dinh do thanh MOT PHEP KIEM la cach duy nhat de no khong lac hau.

Cung kiem luon phien ban Python toi thieu: tool tuyen bo can >= 3.8, nen KHONG
duoc dung cu phap / API chi co o ban moi hon.
"""
from __future__ import annotations

import ast
import sys
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


# Module cua chinh tool - khong phai thu vien ngoai.
# TU SUY RA tu file co that, KHONG go tay: danh sach go tay da lac hau BA lan
# (them `tu_kiem_lan_dau`, roi `canh_gac`...). Moi lan lac hau la mot bo kiem
# bao dong gia, ma bo kiem keu oan thi som muon cung bi tat di.
def _cac_module_noi_bo():
    goc = Path(__file__).resolve().parent.parent
    ten = {p.stem for p in goc.glob("*.py")}
    ten |= {p.stem for p in Path(__file__).resolve().parent.glob("*.py")}
    # PACKAGE con (thu muc co `__init__.py`) cung la module noi bo. Thieu dong
    # nay thi `from loi import phien_ban` bi bao la "thu vien ngoai" - bo kiem
    # keu oan, ma bo kiem keu oan thi som muon cung bi tat di.
    for d in goc.iterdir():
        try:
            if d.is_dir() and (d / "__init__.py").is_file():
                ten.add(d.name)
        except OSError:
            continue
    return ten


NOI_BO = _cac_module_noi_bo()

# API / cu phap chi co tu ban nao. Tool tuyen bo >= 3.8.
CAN_BAN_MOI = {
    "removeprefix": (3, 9), "removesuffix": (3, 9),
    "stdlib_module_names": (3, 10),
    "pairwise": (3, 10),
    "exceptiongroup": (3, 11),
    "batched": (3, 12),
}


def cac_file_tool():
    """Chi file THUOC TOOL - khong tinh tests/ (tests khong di kem may con).

    Gom ca file trong PACKAGE con (`loi/`, `goi/`, `ui/`...): chung di kem may
    con nen cung phai tuan dieu kien "chi thu vien chuan".
    """
    ra = list(ROOT.glob("*.py"))
    for d in sorted(ROOT.iterdir()):
        try:
            if d.is_dir() and (d / "__init__.py").is_file():
                ra.extend(sorted(d.glob("*.py")))
        except OSError:
            continue
    return sorted(ra)


def main():
    print("=" * 72)
    print("Tool chi dung THU VIEN CHUAN (dieu kien de may con khong phai cai gi)")
    print("=" * 72)

    chuan = set(sys.stdlib_module_names)
    ngoai = {}
    for p in cac_file_tool():
        try:
            cay = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError as ex:
            check(f"{p.name}: cu phap doc duoc", False, str(ex))
            continue
        for n in ast.walk(cay):
            if isinstance(n, ast.Import):
                ten = [a.name.split(".")[0] for a in n.names]
            elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
                ten = [n.module.split(".")[0]]
            else:
                continue
            for t in ten:
                if t not in chuan and t not in NOI_BO:
                    ngoai.setdefault(t, set()).add(p.name)

    print(f"  da quet {len(cac_file_tool())} file .py cua tool")
    check("KHONG co thu vien ngoai chuan nao", not ngoai,
          "\n".join(f"`{k}` trong {sorted(v)}" for k, v in ngoai.items())
          + "\n-> may con se vo bang ModuleNotFoundError ngay khi khoi dong."
          "\n   Hoac bo goi nay, hoac phai them buoc cai dat vao quy trinh"
          " ban giao VA vao BAN_GIAO.md.")

    print()
    print("=" * 72)
    print("Khong dung API chi co o Python moi hon 3.8")
    print("=" * 72)
    toi_thieu = (3, 8)
    vi_pham = []
    for p in cac_file_tool():
        van = p.read_text(encoding="utf-8")
        for ten_api, can in CAN_BAN_MOI.items():
            if can <= toi_thieu:
                continue
            if f".{ten_api}" in van or f"{ten_api}(" in van:
                # bo qua neu nam trong chuoi/comment giai thich - kiem tho nhung
                # tot hon khong kiem gi; co FAIL thi nguoi doc se tu xac minh
                vi_pham.append(f"{p.name}: `{ten_api}` can Python {can[0]}.{can[1]}")
    check(f"khong dung API vuot qua Python {toi_thieu[0]}.{toi_thieu[1]}",
          not vi_pham, "\n".join(vi_pham))

    # Nguong tool TUYEN BO phai khop nguong no KIEM
    van_main = (ROOT / "goi_project_capcut.py").read_text(encoding="utf-8")
    check("tool tu kiem phien ban Python luc khoi dong",
          "sys.version_info < (3, 8)" in van_main,
          "phai co kiem tien de, neu khong may con Python cu se vo giua chung")
    check("BAN_GIAO.md ghi dung nguong 3.8",
          "3.8" in (ROOT / "BAN_GIAO.md").read_text(encoding="utf-8"),
          "tai lieu phai noi dung nguong that")

    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
