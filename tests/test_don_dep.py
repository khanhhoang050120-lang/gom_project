# -*- coding: utf-8 -*-
"""A2 / A3 / A4 / A6 - pha don dep khong duoc xoa nham, va module gia phai bi tu choi.

  A2  file JSON khong doc duoc  -> CAM xoa file "mo coi" (khong biet no con dung khong)
  A3  pham vi xoa phai tinh TUONG DOI so voi out_dir, so theo THANH PHAN thu muc
      (goi nam duoi mot thu muc ten "materials_2026" khong duoc bien ca goi thanh kho)
  A4  danh sach xoa-khong-duoc va JSON-hong phai duoc tra ve cho bao cao
  A6  _find_main_module() khong duoc nhan bua mot module GIA
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import chay_tool                              # noqa: E402

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


def _ghi(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def dung_goi(out, ten_media="dung_that.mp4", noi_dung=b"x" * 2048):
    """Dung mot 'ban xuat' toi gian: 1 JSON tro toi 1 media trong materials/."""
    (out / "materials" / "video").mkdir(parents=True, exist_ok=True)
    media = out / "materials" / "video" / ten_media
    media.write_bytes(noi_dung)
    _ghi(out / "draft_meta_info.json", {"draft_materials": []})
    _ghi(out / "draft_content.json", {
        "materials": {"videos": [{"id": "m1", "duration": 1000000,
                                  "path": f"./materials/video/{ten_media}"}]},
        "tracks": [],
    })
    return media


# ==========================================================================
def test_a2_json_hong(TU):
    print("=" * 72)
    print("A2 - file JSON khong doc duoc -> CAM xoa file mo coi")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="a2_"))
    try:
        out = tmp / "GOI"
        media = dung_goi(out)

        # File JSON HONG: media ma no dang dung se khong vao duoc danh sach "con dung"
        (out / "hong.json").write_bytes(b"{ day khong phai json hop le ")
        mo_coi = out / "materials" / "video" / "chi_hong_json_biet.mp4"
        mo_coi.write_bytes(b"y" * 4096)

        kq = TU.cleanup_unused(out, log=lambda *a: None)
        check("cleanup tra ve du 4 phan (co danh sach JSON hong)",
              len(kq) >= 4, f"tra ve {len(kq)} phan")
        check("A2: KHONG xoa file mo coi khi con JSON doc khong duoc",
              mo_coi.is_file(),
              "DAY LA BUG: mot JSON hong lam media that su dang dung bi xoa am tham")
        check("media duoc tham chieu binh thuong van con", media.is_file())
        if len(kq) >= 4:
            check("A4: danh sach JSON hong duoc tra ve cho bao cao",
                  len(kq[3]) == 1, f"loi_doc = {kq[3]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
def test_a2_sach_thi_van_xoa(TU):
    print()
    print("=" * 72)
    print("A2 (chieu nguoc) - khong co JSON hong thi VAN phai don duoc file mo coi")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="a2b_"))
    try:
        out = tmp / "GOI"
        media = dung_goi(out)
        mo_coi = out / "materials" / "video" / "that_su_mo_coi.mp4"
        mo_coi.write_bytes(b"z" * 4096)

        kq = TU.cleanup_unused(out, log=lambda *a: None)
        check("file mo coi that su bi don", not mo_coi.is_file(),
              "sua A2 khong duoc lam mat tinh nang don dep")
        check("file dang duoc dung KHONG bi dong toi", media.is_file())
        check("dem dung 1 file da bo", kq[0] == 1, f"kq[0] = {kq[0]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
def test_a3_ten_thu_muc(TU):
    print()
    print("=" * 72)
    print("A3 - goi nam duoi thu muc ten 'materials_2026' -> khong duoc coi ca goi la kho")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="a3_"))
    try:
        # Day chinh la cai bay: TO TIEN cua out_dir co ten bat dau bang "materials"
        out = tmp / "materials_2026" / "GOI_PORTABLE"
        dung_goi(out)

        # File media nam NGOAI materials/ (vd trong Resources/) - KHONG duoc dong toi
        res = out / "Resources" / "videoAlg"
        res.mkdir(parents=True, exist_ok=True)
        ngoai = res / "cache_khong_ai_tham_chieu.mp4"
        ngoai.write_bytes(b"w" * 4096)

        TU.cleanup_unused(out, log=lambda *a: None)
        check("A3: file ngoai materials/ KHONG bi xoa du to tien ten 'materials_2026'",
              ngoai.is_file(),
              "DAY LA BUG: so chuoi con tren duong dan tuyet doi lam pham vi xoa"
              " nuot ca ban xuat")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
def test_a3_van_don_dung_cho(TU):
    print()
    print("=" * 72)
    print("A3 (chieu nguoc) - file mo coi TRONG materials/ van phai bi don")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="a3b_"))
    try:
        out = tmp / "materials_2026" / "GOI_PORTABLE"
        dung_goi(out)
        mo_coi = out / "materials" / "video" / "mo_coi.mp4"
        mo_coi.write_bytes(b"q" * 4096)
        TU.cleanup_unused(out, log=lambda *a: None)
        check("file mo coi trong materials/ van bi don",
              not mo_coi.is_file(), "sua A3 khong duoc lam mat tinh nang")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
def test_a3_doi_chieu_logic_cu():
    """Ghi lai BANG CHUNG rang logic cu that su sai - test chi co gia tri neu no
    that bai tren ban cu."""
    print()
    print("=" * 72)
    print("A3 - doi chieu logic CU vs MOI (bang chung bug co that)")
    print("=" * 72)
    BS = chr(92)
    out = BS.join(["d:", "tmp", "materials_2026", "GOI_PORTABLE"])
    for rel_mong, duoi in (("Resources" + BS + "videoAlg", False),
                           ("materials" + BS + "video", True),
                           (".", False)):
        d = out if rel_mong == "." else BS.join([out, rel_mong])
        cu = (os.sep + "materials") in (d.lower() + os.sep)
        rel = os.path.relpath(d, out)
        moi = "materials" in [x.lower() for x in rel.split(os.sep) if x]
        check(f"'{rel}': logic moi = {duoi}", moi is duoi)
        if not duoi:
            check(f"'{rel}': logic CU sai (tra True)", cu is True,
                  "neu ban cu cung tra False thi test nay khong chung minh duoc gi")


def test_a6_module_gia():
    print()
    print("=" * 72)
    print("A6 - _find_main_module() phai TU CHOI module gia")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="a6_"))
    try:
        # Script gia lam '__main__' co du 2 ten ma ban kiem cu tin tuong
        bay = tmp / "bay.py"
        bay.write_text(
            "import sys\n"
            f"sys.path.insert(0, r{str(HERE.parent)!r})\n"
            "def _lp(p): return 'GIA:' + str(p)\n"
            "def draft_root_of(*a, **k): return None\n"
            "import toi_uu_dung_luong as T\n"
            "print('MODULE_G =', T.G.__name__)\n"
            "print('LP =', T.G._lp('x'))\n",
            encoding="utf-8")
        r = subprocess.run([sys.executable, "-u", str(bay)], cwd=str(tmp),
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
        ra = (r.stdout or "") + (r.stderr or "")
        check("khong nhan module GIA lam G",
              "GIA:x" not in ra,
              f"output:\n{ra.strip()[:400]}")
        # Sau E1, `toi_uu` khong con di TIM module chinh nua ma `import chung as G`.
        # Cai bay nay gio khong con TON TAI VE MAT CAU TRUC - khong co buoc tra cuu
        # nao de danh lua. Van giu bo kiem lam LUOI CHONG HOI QUY: neu lan sau ai do
        # dung lai co che tim-module thi no lai co the bi lua.
        check("G tro thang vao tang tien ich `chung`",
              "MODULE_G = chung" in ra,
              f"output:\n{ra.strip()[:400]}")
        check("khong con co che tim-module de bi lua",
              "_find_main_module" not in
              (Path(HERE.parent / "toi_uu_dung_luong.py").read_text(encoding="utf-8")),
              "E1 da xoa `_find_main_module()`; neu no quay lai thi bay #48 song lai")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    sys.path.insert(0, str(HERE.parent))
    import toi_uu_dung_luong as TU
    test_a2_json_hong(TU)
    test_a2_sach_thi_van_xoa(TU)
    test_a3_ten_thu_muc(TU)
    test_a3_van_don_dung_cho(TU)
    test_a3_doi_chieu_logic_cu()
    test_a6_module_gia()
    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
