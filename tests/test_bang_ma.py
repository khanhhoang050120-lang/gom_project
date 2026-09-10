# -*- coding: utf-8 -*-
"""BANG MA: doc dau ra tien trinh con phai bang UTF-8, khong theo bang ma cua may.

LOI GOC (tim ra khi ra soat cho muc tieu "chay dung tren may con"):
  `subprocess.run(..., text=True)` KHONG kem `encoding=` se giai ma dau ra bang
  `locale.getpreferredencoding()`, tuc BANG MA ANSI CUA MAY. ffmpeg/ffprobe tren
  Windows luon xuat UTF-8.
     - May phat trien: ACP 65001 (UTF-8) -> trung nhau -> KHONG BAO GIO thay loi.
     - May con Windows tieng Viet: ACP 1258 -> giai ma SAI.
  Hau qua: `_probe_that()` khong parse duoc JSON -> tra None -> tool tuong "khong
  do duoc video" -> bo clip, im lang. Nguoi dung tuong footage cua minh hong.

Day la lop loi may cha KHONG THE TU PHAT HIEN. Vi vay ngoai phep thu hanh vi,
bo kiem nay con co mot CHOT TINH quet AST toan bo project.
"""
from __future__ import annotations

import ast
import subprocess
import sys
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


# --------------------------------------------------------------------------
# CHOT TINH: khong file .py nao duoc doc text tu tien trinh con ma thieu encoding=
# --------------------------------------------------------------------------
HAM_TIEN_TRINH = {"run", "Popen", "check_output", "call", "check_call"}


def quet_mot_file(tep: Path):
    """Tra list (dong, mo_ta) cac loi goi subprocess doc text ma thieu encoding."""
    try:
        cay = ast.parse(tep.read_text(encoding="utf-8"))
    except SyntaxError as ex:
        return [(0, f"LOI CU PHAP: {ex}")]
    xau = []
    for nut in ast.walk(cay):
        if not isinstance(nut, ast.Call):
            continue
        f = nut.func
        ten = None
        if isinstance(f, ast.Attribute):
            ten = f.attr
        elif isinstance(f, ast.Name):
            ten = f.id
        if ten not in HAM_TIEN_TRINH:
            continue
        kw = {k.arg for k in nut.keywords if k.arg}
        # Chi quan tam khi dang doc dang TEXT
        doc_text = ("text" in kw or "universal_newlines" in kw
                    or "encoding" in kw or "errors" in kw)
        if not doc_text:
            continue          # doc bytes -> khong co van de giai ma
        if "encoding" not in kw:
            xau.append((nut.lineno,
                        f"{ten}(...) doc text ma THIEU encoding="))
    return xau


def test_chot_tinh():
    print("=" * 72)
    print("CHOT TINH: moi subprocess doc text phai co encoding=")
    print("=" * 72)
    cac_tep = sorted(ROOT.glob("*.py")) + sorted((ROOT / "tests").glob("*.py"))
    tong_xau = []
    for tep in cac_tep:
        for dong, mo_ta in quet_mot_file(tep):
            tong_xau.append(f"{tep.relative_to(ROOT)}:{dong}  {mo_ta}")
    print(f"  da quet {len(cac_tep)} file .py")
    check("khong file nao doc text tu tien trinh con ma thieu encoding=",
          not tong_xau,
          "\n".join(tong_xau)
          + "\n  -> may phat trien (ACP 65001) se KHONG bao gio thay loi nay;"
            "\n     may con (ACP 1258/1252) se giai ma sai va bo clip im lang.")


def test_chot_tinh_biet_bat():
    """Chot tinh nay phai THAT SU bat duoc - thu tren doan code co loi."""
    print()
    print("=" * 72)
    print("Chot tinh co that su bat duoc khong (thu tren code co loi co y)")
    print("=" * 72)
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="chotma_"))
    try:
        xau = tmp / "xau.py"
        xau.write_text(
            "import subprocess\n"
            "def a():\n"
            "    return subprocess.run(['x'], capture_output=True, text=True)\n",
            encoding="utf-8")
        r = quet_mot_file(xau)
        check("bat duoc `text=True` thieu encoding", len(r) == 1, f"r = {r}")

        tot = tmp / "tot.py"
        tot.write_text(
            "import subprocess\n"
            "def a():\n"
            "    return subprocess.run(['x'], capture_output=True,\n"
            "                          encoding='utf-8', errors='replace')\n"
            "def b():\n"
            "    return subprocess.run(['y'], capture_output=True)\n",
            encoding="utf-8")
        r2 = quet_mot_file(tot)
        check("KHONG bao nham khi da co encoding= / khi doc bytes", not r2,
              f"r2 = {r2}")
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------
# HANH VI: gia lap may con bang cach ep bang ma sai
# --------------------------------------------------------------------------
def test_hanh_vi():
    print()
    print("=" * 72)
    print("Hanh vi: dau ra UTF-8 cua ffprobe phai doc dung du may dung ACP nao")
    print("=" * 72)
    import toi_uu_dung_luong as TU

    ffmpeg, ffprobe = TU.ff_paths(ROOT)
    if not ffmpeg:
        print("  (khong co ffmpeg -> BO QUA phan hanh vi)")
        return

    import shutil
    import tempfile
    from draft_gia import tao_video
    # Thu muc co DAU TIENG VIET: day la cho ffprobe se nhac lai ten file trong
    # dau ra, va la diem kich hoat that tren may nguoi dung.
    tmp = Path(tempfile.mkdtemp(prefix="bangma_"))
    thu_muc = tmp / "Dự án Đèn lồng ờ ề"
    try:
        thu_muc.mkdir(parents=True, exist_ok=True)
        tep = tao_video(ffmpeg, thu_muc / "canh.mp4", 2)
        TU.xoa_cache_probe()
        info = TU.probe(ffprobe, tep)
        check("do duoc clip nam trong thu muc co dau tieng Viet",
              info is not None and info[0] > 0 and info[2] > 0,
              f"info = {info}\n-> None hoac 0x0 nghia la khong do duoc;"
              " tren may con dieu nay lam clip bi bo im lang")

        # Ep _run doc bang cp1258 (mo phong may con) - phai KHONG lam sap
        that = TU._run

        def run_may_con(cmd, timeout):
            return subprocess.run(
                cmd, capture_output=True, timeout=timeout,
                encoding="cp1258", errors="strict",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

        TU._run = run_may_con
        TU.xoa_cache_probe()
        try:
            info2 = TU.probe(ffprobe, tep)
            print(f"  (mo phong may con ACP 1258 -> probe tra: "
                  f"{'do duoc' if info2 else 'KHONG do duoc'})")
        except Exception as ex:
            info2 = None
            print(f"  (mo phong may con ACP 1258 -> nem {type(ex).__name__})")
        finally:
            TU._run = that
            TU.xoa_cache_probe()

        # Du ket qua the nao, ban THAT (co encoding=utf-8) phai luon do duoc
        info3 = TU.probe(ffprobe, tep)
        check("ban that (encoding=utf-8) luon do duoc, khong phu thuoc ACP may",
              info3 is not None and info3[2] > 0, f"info3 = {info3}")
        TU.xoa_cache_probe()

        # Probe that bai phai de lai VET, khong im lang
        loi_truoc = TU.lay_loi_probe()
        TU.probe(ffprobe, thu_muc / "khong_ton_tai.mp4")
        loi_sau = TU.lay_loi_probe()
        check("probe that bai de lai vet (khong nuot im lang)",
              len(loi_sau) > len(loi_truoc) or len(loi_sau) >= 1,
              f"truoc={len(loi_truoc)} sau={len(loi_sau)}"
              "\n-> im lang o day = clip bi bo ma khong ai biet vi sao")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_bao_cao_lo_acp():
    print()
    print("=" * 72)
    print("Bao cao phai lo BANG MA cua may (de truy duoc khi may con gui ve)")
    print("=" * 72)
    import chung as C
    C._MOI_TRUONG = None
    py, he = C.mo_ta_moi_truong()
    print(f"  moi truong: Python {py} | {he}")
    check("chuoi moi truong co ACP", "ACP" in he,
          f"he = {he!r}\n-> khong co ACP thi bao cao tu may con khong cho biet"
          " ho co cung bang ma voi may phat trien khong")


def main():
    test_chot_tinh()
    test_chot_tinh_biet_bat()
    test_hanh_vi()
    test_bao_cao_lo_acp()
    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
