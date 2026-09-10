# -*- coding: utf-8 -*-
"""D5 + D6(nhom UNC) - bo kiem TANG DUONG DAN.

Nhom loi tai pham NHIEU NHAT trong lich su du an - sau lan o sau vi tri khac nhau:

  #1   `_lp()` tao prefix long-path SAI cho UNC -> WinError 123, hong MOI copy
  #2   file local cung fail vi DICH nam duoi UNC out_dir bi mangle
  #7   vong copytree khong dung `_lp` -> fail long-path
  #9   stdin redirect nuot backslash -> output nam SAI O
  #23  `Path("d:")` la path TUONG DOI theo o -> noi am tham vao cwd
  #34  argv cung nuot backslash (mo rong #9)

MOI path o day duoc dung bang `chr(92)` BEN TRONG file Python - khong bao gio
di qua shell, vi chinh viec di qua shell la nguyen nhan cua #9 va #34.
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

import chung as C          # noqa: E402

BS = chr(92)
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


def test_lp_hinh_dang():
    print("=" * 72)
    print("#1 - hinh dang prefix long-path phai DUNG cho tung loai path")
    print("=" * 72)

    unc = BS * 2 + BS.join(["may", "share", "thu muc", "a.mp4"])
    ra = C._lp(unc)
    print(f"  UNC vao : {unc!r}")
    print(f"  UNC ra  : {ra!r}")
    check("UNC -> prefix \\\\?\\UNC\\ (KHONG phai \\\\?\\\\\\)",
          ra == BS * 2 + "?" + BS + "UNC" + BS + BS.join(["may", "share", "thu muc", "a.mp4"]),
          "sai prefix UNC = WinError 123 -> hong MOI copy/getsize/isfile toi o mang")
    check("khong sinh ba backslash lien tiep", BS * 3 not in ra, f"ra = {ra!r}")

    o = BS.join(["D:", "thu muc", "a.mp4"])
    ra2 = C._lp(o)
    check("o co chu cai -> prefix \\\\?\\D:\\",
          ra2 == BS * 2 + "?" + BS + o, f"ra = {ra2!r}")

    print()
    print("=" * 72)
    print("_lp() phai IDEMPOTENT - goi hai lan khong duoc hong")
    print("=" * 72)
    for ten, p in (("UNC", unc), ("o dia", o)):
        m1 = C._lp(p)
        m2 = C._lp(m1)
        check(f"{ten}: _lp(_lp(x)) == _lp(x)", m1 == m2, f"{m1!r} vs {m2!r}")
    dev = BS * 2 + "." + BS + "PhysicalDrive0"
    check("path device \\\\.\\ giu nguyen", C._lp(dev) == dev, f"ra = {C._lp(dev)!r}")

    print()
    print("=" * 72)
    print("#23 - 'D:' KHONG phai goc o dia (drive-relative)")
    print("=" * 72)
    ra3 = C._lp("D:")
    print(f"  _lp('D:') = {ra3!r}")
    # KHONG kiem `len > 7`: `_lp('D:')` giai ra THU MUC HIEN HANH CUA O D, dung
    # theo nghia cua Windows. Neu tien trinh dang o o C thi thu muc hien hanh cua
    # D la GOC -> ket qua la `\\?\D:\` (dung 7 ky tu) va van HOAN TOAN DUNG.
    # Ky vong `len > 7` chi tinh co dung khi chay tu o D, va da lam bo kiem do
    # khi chay ban giai nen tu `C:\...\Temp`.
    # Tinh chat THAT SU can (bug #23): khong duoc DE NGUYEN chuoi `D:`, phai ra
    # duong dan TUYET DOI co tien to long-path.
    check("'D:' duoc dua ve path TUYET DOI",
          ra3.startswith(BS * 2 + "?" + BS + "D:" + BS),
          "de nguyen 'D:' thi Windows noi vao thu muc hien hanh -> goi ra SAI CHO")
    check("_unlp(_lp(x)) tra lai path thuong",
          not C._unlp(C._lp(o)).startswith(BS * 2 + "?"), f"{C._unlp(C._lp(o))!r}")


def test_duong_dan_dai():
    print()
    print("=" * 72)
    print("#7 - thao tac THAT tren duong dan > 260 ky tu")
    print("=" * 72)
    goc = Path(tempfile.mkdtemp(prefix="dai_"))
    try:
        # Dung cay thu muc that su dai
        sau = goc
        while len(str(sau)) < 300:
            sau = sau / ("thu_muc_ten_that_dai_de_vuot_gioi_han_260_ky_tu")
        Path(C._lp(sau)).mkdir(parents=True, exist_ok=True)
        tep = sau / "a.mp4"
        Path(C._lp(tep)).write_bytes(b"x" * 128)
        print(f"  do dai duong dan: {len(str(tep))} ky tu")

        check("tao duoc file o duong dan dai (qua _lp)", C.isfile_safe(tep))
        check("isfile_safe() thay file", C.isfile_safe(tep) is True)
        check("isdir_safe() thay thu muc", C.isdir_safe(sau) is True)

        # Doi chieu: KHONG qua _lp thi hong - chung minh _lp la thu thuc su cuu
        try:
            khong_lp = os.path.isfile(str(tep))
        except OSError:
            khong_lp = False
        print(f"  os.path.isfile KHONG qua _lp -> {khong_lp}")
        check("neu KHONG qua _lp thi khong thay file (chung minh _lp co tac dung)",
              khong_lp is False,
              "may nay co the da bat LongPathsEnabled -> phep doi chieu mat y nghia")

        # iter_json_files phai di duoc vao duong dan dai
        Path(C._lp(sau / "draft_content.json")).write_text("{}", encoding="utf-8")
        Path(C._lp(goc / "draft_meta_info.json")).write_text("{}", encoding="utf-8")
        thay = [p.name for p in C.iter_json_files(goc)]
        check("iter_json_files() di duoc vao duong dan dai",
              "draft_content.json" in thay, f"thay: {thay}")
    finally:
        try:
            shutil.rmtree(C._lp(goc), ignore_errors=True)
        except Exception:
            pass


def test_unc_loopback():
    print()
    print("=" * 72)
    print("UNC that bang loopback \\\\localhost\\C$ (checklist bug.md)")
    print("=" * 72)
    goc_unc = BS * 2 + BS.join(["localhost", "C$"])
    if not C.isdir_safe(goc_unc):
        print("  (khong truy cap duoc admin share C$ -> bo qua phan nay)")
        return
    tmp_unc = Path(goc_unc) / "Windows" / "Temp"
    if not C.isdir_safe(tmp_unc):
        print("  (khong vao duoc C$/Windows/Temp -> bo qua)")
        return
    thu = tmp_unc / "kiem_unc_goi_capcut"
    try:
        Path(C._lp(thu)).mkdir(parents=True, exist_ok=True)
        tep = thu / "a.mp4"
        Path(C._lp(tep)).write_bytes(b"y" * 64)
        check("ghi/doc duoc file qua UNC loopback", C.isfile_safe(tep))
        check("_is_under() dung tren UNC", C._is_under(tep, thu))
        check("_rel_posix() dung tren UNC",
              C._rel_posix(tep, thu) == "a.mp4", C._rel_posix(tep, thu))
        check("la_o_mang() nhan ra UNC loopback", C.la_o_mang(thu))
    finally:
        try:
            shutil.rmtree(C._lp(thu), ignore_errors=True)
        except Exception:
            pass


def test_dau_tieng_viet():
    print()
    print("=" * 72)
    print("Duong dan co dau tieng Viet + khoang trang")
    print("=" * 72)
    goc = Path(tempfile.mkdtemp(prefix="tv_"))
    try:
        thu = goc / "Dự án Biển Sâu 2026" / "cảnh quay gốc"
        Path(C._lp(thu)).mkdir(parents=True, exist_ok=True)
        tep = thu / "cá mập trắng.mp4"
        Path(C._lp(tep)).write_bytes(b"z" * 32)
        check("tao/doc duoc file co dau tieng Viet", C.isfile_safe(tep))
        check("_is_under() dung", C._is_under(tep, goc))
        check("_rel_posix() giu nguyen dau",
              C._rel_posix(tep, thu) == "cá mập trắng.mp4",
              C._rel_posix(tep, thu))
        check("_np() khong lam hong dau",
              "cá mập trắng.mp4" in C._np(str(tep)))
    finally:
        shutil.rmtree(C._lp(goc), ignore_errors=True)


def test_is_under_bien():
    print()
    print("=" * 72)
    print("#2 - _is_under() o cac ca bien (chan/khong chan phai dung)")
    print("=" * 72)
    a = BS.join(["D:", "GOI"])
    cac = [
        (BS.join(["D:", "GOI"]), True, "trung khit"),
        (BS.join(["D:", "GOI", "x"]), True, "nam trong"),
        (BS.join(["D:", "GOI_PORTABLE"]), False, "tien to trung nhung KHAC thu muc"),
        (BS.join(["D:", "goi", "X"]), True, "khong phan biet hoa thuong"),
        (BS.join(["E:", "GOI"]), False, "khac o dia"),
        (BS * 2 + BS.join(["may", "GOI"]), False, "UNC vs o dia"),
    ]
    for p, mong, vi in cac:
        check(f"{vi}: {p} -> {mong}", C._is_under(p, a) is mong)


def main():
    test_lp_hinh_dang()
    test_duong_dan_dai()
    test_unc_loopback()
    test_dau_tieng_viet()
    test_is_under_bien()
    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
