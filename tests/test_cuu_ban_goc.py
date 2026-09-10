# -*- coding: utf-8 -*-
"""File bi BO QUA copytree vi "se duoc thay" nhung KHONG duoc thay -> phai CUU ve.

Loi that, tim ra tren project that DS3_003:
  `A_hyperrealistic_octopus_...87kyy.mp4` (7,02 MB) co trong nguon, KHONG co trong
  goi, bi 6 file JSON tro toi ke ca `draft_content.json`. May cha van mo duoc vi
  path cu con tren o dia; MAY CON MAT HINH.

Co che: `skip_media` la DU DOAN lap truoc khi ma lai ("file nay se duoc thay nen
khoi copy"). Ba nhanh lam du doan sai - `no_gain`, ma lai that bai, bi loai - deu
ket luan "giu ban goc", nhung ban goc chua he duoc copy vao goi.

Bo kiem nay chot: do tren KET QUA THAT o dich, khong tin du doan.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

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


def dung_canh(tmp):
    """draft_dir co 3 file media; out_dir RONG (mo phong da bi copytree bo qua)."""
    draft = tmp / "DRAFT"
    out = tmp / "OUT"
    (draft / "materials" / "video").mkdir(parents=True, exist_ok=True)
    (draft / "subdraft" / "GUID1" / "materials" / "video").mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)

    a = draft / "materials" / "video" / "a.mp4"
    b = draft / "subdraft" / "GUID1" / "materials" / "video" / "b.mp4"
    c = draft / "materials" / "video" / "c.mp4"
    for p, noi_dung in ((a, b"AAAA" * 900), (b, b"BBBB" * 900), (c, b"CCCC" * 900)):
        p.write_bytes(noi_dung)
    return draft, out, a, b, c


def test_cuu(G):
    print("=" * 72)
    print("File bi bo qua ma KHONG duoc thay -> phai duoc CUU ve goi")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="cuu_goc_"))
    try:
        draft, out, a, b, c = dung_canh(tmp)
        nc = lambda p: os.path.normcase(os.path.abspath(str(p)))  # noqa: E731
        skip = {nc(a), nc(b), nc(c)}

        # `c` DUNG LA da duoc thay -> co ban _opt trong opt_by_src
        opt_stat = {"opt_by_src": {(nc(out), nc(c)): str(out / "materials" / "c_opt_1.mp4")},
                    "fail": []}

        cuu = G.cuu_ban_goc_bi_bo_qua(out, draft, skip, opt_stat, log=lambda *x: None)

        # a va b KHONG duoc thay -> phai duoc cuu ve dung vi tri tuong doi
        dich_a = out / "materials" / "video" / "a.mp4"
        dich_b = out / "subdraft" / "GUID1" / "materials" / "video" / "b.mp4"
        dich_c = out / "materials" / "video" / "c.mp4"

        check("cuu file o materials/video/", dich_a.is_file(),
              f"khong thay {dich_a}")
        check("cuu file long trong subdraft (giu dung cay thu muc)", dich_b.is_file(),
              f"khong thay {dich_b}\n-> subdraft long nhieu tang la cho de sai nhat")
        check("KHONG cuu file da duoc thay that", not dich_c.is_file(),
              "file da co ban _opt ma van bi chep ve -> goi phinh, ban goc thua")
        check("noi dung file cuu ve dung nguyen ven",
              dich_a.is_file() and dich_a.read_bytes() == a.read_bytes())
        check("tra ve dung so file da cuu", len(cuu) == 2, f"cuu = {cuu}")

        # Chay lai: da co san thi khong chep lai
        cuu2 = G.cuu_ban_goc_bi_bo_qua(out, draft, skip, opt_stat, log=lambda *x: None)
        check("chay lai khong chep lai file da co", not cuu2, f"cuu2 = {cuu2}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_khong_nuot_loi(G):
    print()
    print("=" * 72)
    print("Cuu THAT BAI thi phai bao ra, khong duoc im lang")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="cuu_loi_"))
    try:
        draft, out, a, b, c = dung_canh(tmp)
        nc = lambda p: os.path.normcase(os.path.abspath(str(p)))  # noqa: E731
        opt_stat = {"opt_by_src": {}, "fail": []}

        # Ep copy that bai: xoa file nguon di sau khi da dua vao skip_media
        a.unlink()
        ghi = []
        G.cuu_ban_goc_bi_bo_qua(out, draft, {nc(a)}, opt_stat, log=ghi.append)

        check("bao ra khi cuu that bai", any("CUU KHONG DUOC" in x for x in ghi),
              f"log = {ghi}")
        check("dua vao duong bao cao (opt_stat['fail'])", len(opt_stat["fail"]) == 1,
              f"fail = {opt_stat['fail']}\n-> im lang o day = file mat o may con"
              " ma khong ai biet")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_da_noi_day_du(G):
    print()
    print("=" * 72)
    print("Da NOI vao main() va vao bao cao (khong phai code chet)")
    print("=" * 72)
    src = (ROOT / "goi_project_capcut.py").read_text(encoding="utf-8")
    check("main() co goi cuu_ban_goc_bi_bo_qua",
          "cuu_ban_goc = cuu_ban_goc_bi_bo_qua(" in src,
          "dinh nghia ma khong ai goi = code chet (bay muc #52)")
    check("truyen dung skip_media",
          "skip_media, opt_stat)" in src.replace("\n", " ").replace("  ", " "),
          "phai truyen chinh tap du doan da dung cho copytree")
    check("ket qua di vao bao cao",
          'sect("DA CUU ban goc bi bo qua nham' in src,
          "cuu duoc ma khong ghi vao bao cao thi nguoi dung khong biet da co su co")
    check("bien khai bao o tang ngoai cua main (che do 1 khong duoc NameError)",
          "cuu_ban_goc = []" in src,
          "khai trong `if opts:` se lam che do 1 nem NameError - dung lop loi #64")


def main():
    import chay_tool
    G = chay_tool.nap_tool()
    test_cuu(G)
    test_khong_nuot_loi(G)
    test_da_noi_day_du(G)
    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
