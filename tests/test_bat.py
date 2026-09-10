# -*- coding: utf-8 -*-
"""File .bat la DIEM VAO DUY NHAT cua may con - phai chiu duoc may thieu Python.

Ba canh chac chan xay ra khi phat cho 15-20 nguoi tu chep thu muc:
  1. May chua cai Python        -> `'python' is not recognized`, nguoi dung bo cuoc
  2. Cai roi nhung quen tich "Add to PATH" -> `python` khong co, nhung `py` thi co
  3. Windows co san ban GIA LAP trong WindowsApps -> bam vao mo Microsoft Store

Bo kiem CHAY THAT file .bat qua cmd.exe voi PATH bi dung, khong chi doc noi dung.
"""
from __future__ import annotations

import os
import shutil
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


BAT = ("goi_project_capcut.bat", "xem_tien_trinh.bat", "GIAO_DIEN.bat")


def test_dinh_dang():
    print("=" * 72)
    print("Dinh dang file .bat (bug #8: non-ASCII vo theo code page)")
    print("=" * 72)
    for ten in BAT:
        b = (ROOT / ten).read_bytes()
        xau = [x for x in b if x > 127]
        check(f"{ten}: ASCII thuan", not xau,
              f"{len(xau)} byte non-ASCII -> se vo thanh ky tu la tren may khac"
              " co code page khac (bug #8)")
        check(f"{ten}: dung CRLF", b.count(b"\r\n") > 0 and
              b.count(b"\n") == b.count(b"\r\n"),
              f"CRLF={b.count(bytes([13, 10]))}, LF tong={b.count(bytes([10]))}"
              "\n-> .bat dang Unix (LF) khong phai dang chuan Windows")
        check(f"{ten}: co chcp truoc moi lenh khac", b.find(b"chcp") < 80,
              "chcp phai o dau (bug #8)")


def chay(duong, env=None, cwd=None, vao=None):
    """Chay mot file .bat DUNG NHU EXPLORER: goi THANG, khong qua `cmd /c`.

    Quan trong: `cmd /c <duong dan>` bi chinh cmd.exe tach lenh o dau `&` TRUOC
    KHI .bat chay. Dung cach do de kiem se bao mot loi KHONG CO THAT (da mac mot
    lan: tuong .bat vo voi thu muc `thu muc & co dau va`, hoa ra goi thang thi
    chay binh thuong). Nguoi dung bam dup trong Explorer -> khong di qua duong do.
    """
    r = subprocess.run([str(duong)],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=180,
                       env=env, cwd=str(cwd or Path(duong).parent),
                       input=vao, stdin=None if vao else subprocess.DEVNULL)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def chay_bat(ten, path_moi, cwd=None):
    """Chay .bat voi PATH da dung. Tra (ma_thoat, dau_ra)."""
    env = dict(os.environ)
    env["PATH"] = path_moi
    return chay(ROOT / ten, env=env, cwd=cwd or ROOT)


def test_ky_tu_dac_biet():
    """Thu muc co ky tu dac biet - `)` la ca THAT SU xay ra."""
    print()
    print("=" * 72)
    print("Thu muc co ky tu dac biet trong ten")
    print("=" * 72)
    can = ["goi_project_capcut.bat", "goi_project_capcut.py", "chung.py",
           "toi_uu_dung_luong.py", "xem_tien_trinh.py", "cau_hinh.json"]
    # `goi_project_capcut (1)` chinh la ten Windows TU DAT khi giai nen zip lan
    # thu hai vao cung cho - dung luong ban giao cua du an nay.
    for ten_tm in ("goi_project_capcut (1)", "Nguyen Van A", "thu muc-binh_thuong"):
        tmp = Path(tempfile.mkdtemp(prefix="ky_tu_"))
        try:
            d = tmp / ten_tm
            d.mkdir(parents=True)
            for f in can:
                shutil.copy2(ROOT / f, d / f)

            _ma, ra = chay(d / "goi_project_capcut.bat", vao="Q\n")
            check(f"{ten_tm!r}: tool khoi dong duoc",
                  "GOI PROJECT CAPCUT" in ra.upper(),
                  f"dau ra:\n{ra[:300]}")

            # Thieu file .py -> phai vao dung nhanh bao loi
            (d / "goi_project_capcut.py").unlink()
            _ma2, ra2 = chay(d / "goi_project_capcut.bat")
            check(f"{ten_tm!r}: thieu file .py -> bao dung",
                  "thieu file" in ra2.lower(), f"dau ra:\n{ra2[:300]}")
            check(f"{ten_tm!r}: khong loi cu phap batch",
                  "unexpected at this time" not in ra2.lower(),
                  f"dau `)` trong duong dan dong khoi `if (...)` som"
                  f"\ndau ra:\n{ra2[:300]}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def test_khong_co_python():
    print()
    print("=" * 72)
    print("May KHONG co Python -> phai chi ro cach sua, khong de nguoi dung mo mit")
    print("=" * 72)
    # PATH chi con `system32`. Co y KHONG co `C:\Windows` (noi `py.exe` nam) va
    # khong co WindowsApps -> ca `py` lan `python` deu khong tim thay.
    #
    # KHONG dung shim `py.cmd`: goi mot .cmd tu .bat MA KHONG CO `call` se
    # chuyen han quyen dieu khien va KET THUC .bat cha - bay kinh dien cua
    # batch. Luc do .bat khong in gi ca va phep kiem hieu nham la no im lang.
    he_thong = os.environ.get("SystemRoot", r"C:\Windows")
    ma, ra = chay_bat("goi_project_capcut.bat", f"{he_thong}\\system32")

    check("khong nem loi kho hieu cua cmd",
          "is not recognized" not in ra and "khong phai la lenh" not in ra.lower(),
          f"dau ra:\n{ra[:400]}")

    # KE TU KHI dong goi Python EMBEDDABLE vao `python\`, may KHONG co Python
    # van chay duoc - do la MUC DICH cua viec dong kem. Ky vong cu ("phai bao
    # thieu Python") da lac hau. Nhung duong bao loi VAN phai con nguyen cho
    # truong hop ban di kem bi thieu/hong (canh o `test_thieu_ca_hai`).
    co_embed = (ROOT / "python" / "python.exe").is_file()
    if co_embed:
        check("co ban Python di kem -> VAN chay duoc du may khong co Python",
              "GOI PROJECT CAPCUT" in ra.upper(),
              f"day la MUC DICH cua viec dong kem Python\ndau ra:\n{ra[:400]}")
    else:
        check("khong co ban di kem -> phai bao ro thieu Python",
              "chua co Python" in ra, f"dau ra:\n{ra[:400]}")
        check("chi dia chi tai ve", "python.org" in ra, f"dau ra:\n{ra[:400]}")


def test_thieu_ca_hai():
    """KHONG co ban di kem VA may cung khong co Python -> phai huong dan RO."""
    print()
    print("=" * 72)
    print("Thieu CA HAI (khong co python\\ va may khong co Python)")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="thieu_ca_hai_"))
    try:
        d = tmp / "TOOL"
        d.mkdir()
        for f in ("goi_project_capcut.bat", "goi_project_capcut.py", "chung.py",
                  "toi_uu_dung_luong.py", "xem_tien_trinh.py", "cau_hinh.json"):
            shutil.copy2(ROOT / f, d / f)
        env = dict(os.environ)
        he_thong = os.environ.get("SystemRoot", r"C:\Windows")
        env["PATH"] = f"{he_thong}\\system32"
        _ma, ra = chay(d / "goi_project_capcut.bat", env=env, cwd=d)

        check("noi ro la thieu Python", "chua co Python" in ra, f"dau ra:\n{ra[:400]}")
        check("chi dia chi tai ve", "python.org" in ra, f"dau ra:\n{ra[:400]}")
        check("nhac tich 'Add python.exe to PATH'", "Add python.exe to PATH" in ra,
              "day la buoc nguoi dung hay quen nhat")
        check("canh bao ban gia lap Microsoft Store", "Microsoft Store" in ra,
              "bam dup ma mo Store la trai nghiem gay bo cuoc")
        check("khong chay tiep vao tool",
              "GOI PROJECT CAPCUT" not in ra.upper() or "chua co Python" in ra,
              "phai dung han, khong duoc chay tiep")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_thieu_file_py():
    print()
    print("=" * 72)
    print("Chep thieu file .py -> bao ro, khong nem loi Python")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="bat_thieu_"))
    try:
        shutil.copy2(ROOT / "goi_project_capcut.bat", tmp / "goi_project_capcut.bat")
        _ma, ra = chay(tmp / "goi_project_capcut.bat", cwd=tmp)
        check("bao ro thieu file", "thieu file" in ra.lower(), f"dau ra:\n{ra[:400]}")
        check("chi ro phai chep CA THU MUC", "CA THU MUC" in ra,
              "nguoi dung hay chep moi file .bat roi tuong da xong")
        check("khong nem traceback Python", "Traceback" not in ra,
              f"dau ra:\n{ra[:400]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_duong_thuan():
    print()
    print("=" * 72)
    print("May BINH THUONG -> tool phai khoi dong duoc")
    print("=" * 72)
    # Tra loi 'Q' de tool thoat ngay o menu chon project
    r = subprocess.run(["cmd", "/c", str(ROOT / "goi_project_capcut.bat")],
                       capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=180,
                       cwd=str(ROOT), input="Q\n")
    ra = (r.stdout or "") + (r.stderr or "")
    check("tool khoi dong duoc", "GOI PROJECT CAPCUT" in ra.upper(),
          f"dau ra:\n{ra[:500]}")
    check("in ra so hieu phien ban", "Phien ban" in ra, f"dau ra:\n{ra[:500]}")
    check("khong co traceback", "Traceback" not in ra, f"dau ra:\n{ra[:600]}")



def test_chan_doan_thieu_file():
    """Thieu file .py KHONG duoc bao thanh "may chua co Python" (bug #89, #90).

    Ban dau ca ba file .bat deu kiem Python TRUOC, bang `import sys,chung`.
    Thieu `chung.py` lam phep kiem ban di kem truot; tren may khong co Python
    he thong thi ca ba ung vien deu truot, va .bat ket luan "may nay chua co
    Python 3.8 tro len". Nguoi dung tai Python, cai, tich "Add to PATH", quay
    lai - van hong y nhu cu, va gio thi ho tin la da loai tru duoc Python.

    Chan doan sai te hon khong chan doan.
    """
    print()
    print("=" * 72)
    print("Thieu file .py -> phai bao THIEU FILE, khong do oan cho Python")
    print("=" * 72)
    he_thong = os.environ.get("SystemRoot", r"C:\Windows")
    for ten_bat, diem_vao in (("goi_project_capcut.bat", "goi_project_capcut.py"),
                              ("xem_tien_trinh.bat", "xem_tien_trinh.py"),
                              ("GIAO_DIEN.bat", "giao_dien.py")):
        van_bat = (ROOT / ten_bat).read_text("ascii", "replace")
        check(f"{ten_bat}: kiem file TRUOC khi cham den Python",
              van_bat.index('set "THIEU="')
              < van_bat.index("python" + chr(92) + "python.exe"),
              "kiem Python truoc -> thieu file .py bi bao nham thanh loi Python")

        tmp = Path(tempfile.mkdtemp(prefix="chan_doan_"))
        try:
            d = tmp / "TOOL"
            d.mkdir()
            shutil.copy2(ROOT / ten_bat, d / ten_bat)
            shutil.copy2(ROOT / diem_vao, d / diem_vao)
            # `chung.py` CO Y khong chep - day la thu dang dung

            # Ghi ra FILE chu khong pipe: GIAO_DIEN.bat co the `start` mot tien
            # trinh tach roi, va tien trinh do thua ke dau pipe -> `run()` se
            # cho den khi giao dien dong (bug #88).
            log = tmp / "log.txt"
            env = dict(os.environ)
            env["PATH"] = f"{he_thong}{chr(92)}system32"
            with open(log, "w", encoding="utf-8", errors="replace") as fh:
                subprocess.run([str(d / ten_bat)], stdout=fh,
                               stderr=subprocess.STDOUT,
                               stdin=subprocess.DEVNULL, timeout=180,
                               env=env, cwd=str(d))
            ra = log.read_text(encoding="utf-8", errors="replace")

            check(f"{ten_bat}: bao dung la THIEU FILE",
                  "THIEU FILE" in ra.upper(), ra[:400])
            check(f"{ten_bat}: goi ten file thieu", "chung.py" in ra, ra[:400])
            check(f"{ten_bat}: KHONG do oan cho Python",
                  "chua co Python" not in ra,
                  "chan doan sai -> nguoi dung cai Python roi van hong\n"
                  + ra[:400])
            check(f"{ten_bat}: chi ro cach sua", "CA THU MUC" in ra
                  or "GIAI NEN LAI" in ra.upper(), ra[:400])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def main():
    test_dinh_dang()
    test_duong_thuan()
    test_khong_co_python()
    test_thieu_file_py()
    test_ky_tu_dac_biet()
    test_thieu_ca_hai()
    test_chan_doan_thieu_file()
    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
