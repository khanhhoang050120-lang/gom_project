# -*- coding: utf-8 -*-
"""Quet THIEU cay thu muc phai DUNG LAI, khong duoc coi la "quet xong".

LOI GOC: `iter_json_files()` dung `os.walk(...)` KHONG co `onerror=`. Mac dinh
cua `os.walk` la NUOT IM LANG moi loi liet ke thu muc.

Chuoi hau qua o `cleanup_unused()` - MAT DU LIEU THAT:
  1. NAS rot phien SMB (WinError 71 - NAS o day hay bi khi tai nang) -> mot nhanh
     thu muc khong liet ke duoc
  2. `os.walk` bo qua im lang -> JSON trong nhanh do khong bao gio duoc doc
  3. media chung tham chieu KHONG nam trong `refd`
  4. chot an toan `duoc_xoa_mo_coi = not loi_doc` VO HIEU: khong JSON nao "doc
     loi", chung chua he duoc LIET KE
  5. media bi XOA THAT, roi bao cao noi "DU"

Bo kiem nay VA `os.scandir` (thu ma `os.walk` that su goi) chu KHONG stub
`iter_json_files` - nho vay no van dung ke ca khi ai do viet lai ham do.
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

import chung as C   # noqa: E402

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


class ScandirHong:
    """Context manager: `os.scandir` nem WinError 71 cho thu muc co ten chua `moc`."""

    def __init__(self, moc):
        self.moc = moc
        self.that = os.scandir
        self.so_lan = 0

    def __enter__(self):
        that, moc = self.that, self.moc

        def gia(path="."):
            if moc.lower() in str(path).lower():
                self.so_lan += 1
                raise OSError(
                    71, "No more connections can be made to this remote computer",
                    str(path))
            return that(path)

        os.scandir = gia
        return self

    def __exit__(self, *a):
        os.scandir = self.that
        return False


def dung_goi(tmp):
    """Goi toi gian: 2 nhanh JSON + media duoc nhanh thu hai tham chieu."""
    out = tmp / "GOI"
    (out / "materials" / "video").mkdir(parents=True)
    (out / "subdraft" / "NHANH_XA" / "materials").mkdir(parents=True)

    media = out / "materials" / "video" / "canh.mp4"
    media.write_bytes(b"MEDIA" * 200)

    # JSON o goc: KHONG nhac toi media
    (out / "draft_content.json").write_text(
        '{"materials":{"videos":[]},"tracks":[]}', encoding="utf-8")
    # JSON o nhanh xa: CHINH NO tham chieu media
    (out / "subdraft" / "NHANH_XA" / "draft_content.json").write_text(
        '{"materials":{"videos":[{"id":"a","path":'
        '"##_draftpath_placeholder_X_##/materials/video/canh.mp4"}]},"tracks":[]}',
        encoding="utf-8")
    return out, media


def test_nem_khi_quet_thieu():
    print("=" * 72)
    print("iter_json_files: quet thieu -> NEM, khong tra ve ket qua thieu")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="quet_thieu_"))
    try:
        out, media = dung_goi(tmp)

        binh_thuong = C.iter_json_files(out)
        check("binh thuong: thay du 2 file .json", len(binh_thuong) == 2,
              f"thay {len(binh_thuong)}: {[p.name for p in binh_thuong]}")

        with ScandirHong("NHANH_XA") as h:
            try:
                kq = C.iter_json_files(out)
                da_nem = False
            except OSError as ex:
                da_nem = True
                loi = str(ex)
            check("quet thieu -> NEM OSError (khong im lang)", da_nem,
                  f"tra ve {len(kq)} file thay vi nem"
                  if not da_nem else "")
            if da_nem:
                check("thong bao noi ro hau qua", "xoa nham" in loi.lower(),
                      f"loi = {loi}")
            check("scandir gia da that su duoc goi", h.so_lan > 0,
                  "phep thu khong cham toi nhanh do -> vo nghia")

        # Truyen list vao thi KHONG nem, ma ghi loi
        with ScandirHong("NHANH_XA"):
            loi_list = []
            kq2 = C.iter_json_files(out, loi=loi_list)
            check("truyen loi= -> khong nem, van chay tiep", isinstance(kq2, list))
            check("nhung co ghi lai loi", len(loi_list) >= 1, f"loi = {loi_list}")
            check("va ket qua THIEU that (bang chung loi la co that)",
                  len(kq2) < len(binh_thuong),
                  f"{len(kq2)} vs {len(binh_thuong)} - neu bang nhau thi phep thu"
                  " chua cham dung nhanh")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cleanup_khong_xoa_nham():
    print()
    print("=" * 72)
    print("cleanup_unused: quet thieu -> CAM xoa file mo coi (khong mat du lieu)")
    print("=" * 72)
    import toi_uu_dung_luong as TU
    tmp = Path(tempfile.mkdtemp(prefix="cleanup_thieu_"))
    try:
        out, media = dung_goi(tmp)
        check("truoc khi don: media con", media.is_file())

        ghi = []
        with ScandirHong("NHANH_XA") as h:
            TU.cleanup_unused(out, log=ghi.append)
        check("scandir gia da duoc goi", h.so_lan > 0)
        check("MEDIA VAN CON (khong bi xoa nham)", media.is_file(),
              "media bi xoa vi JSON tham chieu no nam trong nhanh khong quet duoc"
              "\n-> day dung la kich ban mat du lieu that")
        check("co noi ra ly do bo qua viec xoa",
              any("BO QUA viec xoa" in x for x in ghi), f"log = {ghi}")

        # Doi chung: khong ep loi thi media VAN phai con (vi co JSON tham chieu)
        ghi2 = []
        TU.cleanup_unused(out, log=ghi2.append)
        check("chay binh thuong: media co tham chieu -> van con", media.is_file())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_refd_rong():
    print()
    print("=" * 72)
    print("refd RONG -> cam xoa (bang chung duong, khong chi 'vang mat loi')")
    print("=" * 72)
    import toi_uu_dung_luong as TU
    tmp = Path(tempfile.mkdtemp(prefix="refd_rong_"))
    try:
        out = tmp / "GOI"
        (out / "materials" / "video").mkdir(parents=True)
        media = out / "materials" / "video" / "canh.mp4"
        media.write_bytes(b"MEDIA" * 200)
        # KHONG co file JSON nao -> refd rong, va cung khong co loi doc nao
        ghi = []
        TU.cleanup_unused(out, log=ghi.append)
        check("khong JSON nao -> KHONG xoa sach materials/", media.is_file(),
              "refd rong ma van xoa theo no = xoa sach media")
        check("co noi ro ly do",
              any("KHONG tim thay tham chieu" in x for x in ghi), f"log = {ghi}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cac_phep_dem_khong_noi_doi():
    """Quet thieu -> phep dem phai NEM/BAO, khong duoc bao con so dep."""
    print()
    print("=" * 72)
    print("Cac phep dem khac: quet thieu -> khong duoc bao con so SAI")
    print("=" * 72)
    import goi_project_capcut as G
    import toi_uu_dung_luong as TU
    tmp = Path(tempfile.mkdtemp(prefix="dem_thieu_"))
    try:
        out, media = dung_goi(tmp)

        # 1. scan_long_paths: bo sot nhanh -> se bao "0 duong dan qua dai" SAI
        binh_thuong = G.scan_long_paths(out)
        check("scan_long_paths chay binh thuong duoc", isinstance(binh_thuong, list))
        with ScandirHong("NHANH_XA") as h:
            try:
                G.scan_long_paths(out)
                nem = False
            except OSError:
                nem = True
        check("scan_long_paths: quet thieu -> NEM (khong bao '0' gia)", nem,
              "bao '0 duong dan qua dai' khi chua quet het = canh bao bien mat"
              " dung luc can no")
        check("scandir gia da duoc goi", h.so_lan > 0)

        # 2. kiem_ban_goc_thua: la mot PHEP NGHIEM THU -> noi doi con te hon khong co
        with ScandirHong("NHANH_XA") as h2:
            try:
                TU.kiem_ban_goc_thua(out, log=lambda *x: None)
                nem2 = False
            except OSError:
                nem2 = True
        check("kiem_ban_goc_thua: quet thieu -> NEM", nem2,
              "phep nghiem thu bao 'khong thua' khi chua quet het = noi doi")
        check("scandir gia da duoc goi (2)", h2.so_lan > 0)

        # 3. cleanup: vong xoa hong theo huong AN TOAN, nhung con so phai trung thuc
        ghi = []
        with ScandirHong("NHANH_XA"):
            kq = TU.cleanup_unused(out, log=ghi.append)
        check("cleanup van tra ve du 4 phan", isinstance(kq, tuple) and len(kq) == 4,
              f"kq = {kq!r}")
        check("cleanup khong im lang ve viec quet thieu",
              any("khong duyet duoc" in str(x).lower() for x in ghi)
              or any("khong duyet duoc" in str(a) + str(b)
                     for a, b in (kq[2] or [])),
              f"log = {ghi}\n  fails = {kq[2] if isinstance(kq, tuple) else '?'}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    test_nem_khi_quet_thieu()
    test_cleanup_khong_xoa_nham()
    test_refd_rong()
    test_cac_phep_dem_khong_noi_doi()
    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
