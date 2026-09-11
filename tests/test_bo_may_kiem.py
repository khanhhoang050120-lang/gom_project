# -*- coding: utf-8 -*-
"""Kiem chinh BO MAY KIEM THU - `tests/chay_het.py`.

Vi sao can bo kiem nay:
  `chay_het.py` la thu duy nhat quyet dinh "tat ca dat hay chua". No noi doi
  thi MOI bo kiem con lai deu vo nghia - bang xanh ma san pham hong. Day chinh
  la nhom C trong bug.md (bao cao sai / "da xong" khi chua xong) ap len chinh
  cong cu dung de chong nhom C.

Ban cu co HAI khiem khuyet, ca hai deu im lang:
  1. In cung chuoi "BO QUA (thieu ffmpeg)" cho MOI ma thoat 2 - tuc la DOAN
     nguyen nhan. Bo kiem con co the bo qua vi khong co NAS, khong co pythonw,
     khong co man hinh tuong tac. Doan sai nguyen nhan la nhom D (bao dong gia
     / chan doan sai).
  2. KHONG co nguong so bo duoc phep bo qua. Mot ngay nao do ca 41 bo cung bo
     qua ma bang tong ket van khong do.

Cach kiem: dung mot ban `chay_het.py` trong thu muc TAM voi cac bo kiem GIA tu
khai ly do rieng, roi doc dau ra + ma thoat. Khong dung toi repo that.

"Mot co che chua tung do la mot co che chua duoc chung minh" - nen o day co ca
phep kiem chieu DO (vuot nguong -> ma thoat 1) lan chieu XANH (trong nguong ->
ma thoat 0).
"""
import os, subprocess, sys, tempfile, shutil
from pathlib import Path

# Tu suy ra vi tri repo. KHONG hardcode va KHONG nhan qua argv/shell:
# backslash bi nuot la nhom loi A trong bug.md (#9, #34).
ROOT = Path(__file__).resolve().parent.parent
pas = fail = 0
def check(ten, dk, ct=""):
    global pas, fail
    if dk: pas += 1; print(f"  PASS  {ten}")
    else:  fail += 1; print(f"  FAIL  {ten}" + (f"  | {ct}" if ct else ""))

tmp = Path(tempfile.mkdtemp(prefix="kc_boqua_"))
try:
    kt = tmp / "tests"; kt.mkdir()
    shutil.copy2(ROOT / "tests" / "chay_het.py", kt / "chay_het.py")
    # Sinh N bo kiem gia, moi bo tu khai ly do rieng biet.
    for i in range(4):
        (kt / f"test_gia{i}.py").write_text(
            "print('KET QUA: 0 PASS / 0 FAIL')\n"
            f"print('BO QUA: ly do rieng so {i} - khong co NAS')\n"
            "import sys; sys.exit(2)\n", encoding="utf-8")
    (kt / "test_that.py").write_text(
        "print('KET QUA: 1 PASS / 0 FAIL')\n", encoding="utf-8")

    ds = ",\n".join([f'    ("gia {i}", "test_gia{i}.py", 30)' for i in range(4)])
    noi_dung = (kt / "chay_het.py").read_text(encoding="utf-8")
    dau = noi_dung.split("BO_KIEM = [")[0]
    # thay nguyen khoi BO_KIEM
    sau = noi_dung[noi_dung.index("]\n", noi_dung.index("BO_KIEM = [")) + 2:]
    moi = dau + "BO_KIEM = [\n" + ds + ',\n    ("that", "test_that.py", 30),\n]\n' + sau
    (kt / "chay_het.py").write_text(moi, encoding="utf-8")

    def chay(max_bo_qua):
        env = dict(os.environ); env["MAX_BO_QUA"] = str(max_bo_qua)
        r = subprocess.run([sys.executable, "-u", str(kt / "chay_het.py")],
                           cwd=str(tmp), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env, timeout=120)
        return r.returncode, (r.stdout or "")

    # TIEN DE phai duoc khang dinh: khong co bo gia nao thi moi phep duoi
    # deu "dat" mot cach vo nghia (checklist bug.md: bo kiem phai FAIL
    # khi khong co du lieu).
    so_gia = len(list(kt.glob("test_gia*.py")))
    check("tien de: da dung duoc 4 bo kiem gia", so_gia == 4, f"co {so_gia}")

    ma2, ra2 = chay(2)
    check("4 bo bo qua > nguong 2 -> ma thoat 1 (KHONG duoc bao 'TAT CA DAT')",
          ma2 == 1, f"ma thoat={ma2}")
    check("noi ro vuot nguong", "vuot nguong" in ra2)
    check("van nhan ra bo THAT su dat", "DAT" in ra2)

    ma9, ra9 = chay(9)
    check("nguong 9 -> trong nguong -> ma thoat 0", ma9 == 0, f"ma thoat={ma9}")
    check("van noi ro co 4 bo bo qua", "4 bo bo qua" in ra9 or "BO QUA 4 bo" in ra9)

    # Ly do phai la CUA CHINH bo kiem, khong phai chuoi doan bua.
    check("in ly do THAT cua tung bo (khong doan 'thieu ffmpeg')",
          all(f"ly do rieng so {i}" in ra9 for i in range(4)),
          "thieu it nhat mot ly do")
    # Y dinh that: dau ra KHONG duoc gan nhan doan bua cho bo bo qua vi ly do
    # khac. (Chu thich trong ma nguon giai thich lich su thi khong sao.)
    check("dau ra KHONG gan nhan doan bua 'thieu ffmpeg' cho bo bo qua",
          "thieu ffmpeg" not in ra9, "ly do phai do bo kiem tu khai")

    # Bo kiem khong khai ly do thi phai bi NOI ra, khong duoc im lang.
    (kt / "test_cam.py").write_text(
        "print('KET QUA: 0 PASS / 0 FAIL')\nimport sys; sys.exit(2)\n", encoding="utf-8")
    nd = (kt / "chay_het.py").read_text(encoding="utf-8")
    nd = nd.replace('    ("that", "test_that.py", 30),',
                    '    ("cam", "test_cam.py", 30),\n    ("that", "test_that.py", 30),')
    (kt / "chay_het.py").write_text(nd, encoding="utf-8")
    _m, rac = chay(9)
    check("bo kiem CAM MIENG bi bao ro la khong khai ly do",
          "KHONG khai ly do" in rac)

    # ---- Nhanh THAT BAI. Phep kiem nay sinh ra tu kiem chung nguoc
    # (`tests/cong_cu/kiem_chung_nguoc.py`): pha `if hong:` thanh `if False:`
    # trong chay_het.py ma bo kiem nay VAN XANH. Ly do: moi bo gia o tren deu
    # DAT hoac BO QUA, khong bo nao THAT BAI - nen nhanh "co bo khong dat"
    # chua bao gio duoc chay. Mot nhanh khong duoc kiem la mot nhanh co the
    # hong am tham, va day dung la nhanh QUAN TRONG NHAT cua ca cong CI.
    (kt / "test_hong.py").write_text(
        "print('KET QUA: 0 PASS / 1 FAIL')\n"
        "print('FAIL  phep kiem gia nay co y that bai')\n"
        "import sys; sys.exit(1)\n", encoding="utf-8")
    nd = (kt / "chay_het.py").read_text(encoding="utf-8")
    nd = nd.replace('    ("that", "test_that.py", 30),',
                    '    ("hong", "test_hong.py", 30),\n'
                    '    ("that", "test_that.py", 30),')
    (kt / "chay_het.py").write_text(nd, encoding="utf-8")

    ma_h, ra_h = chay(9)
    check("mot bo THAT BAI -> chay_het tra ma thoat 1",
          ma_h == 1, f"ma thoat={ma_h}")
    check("mot bo THAT BAI -> KHONG duoc in 'TAT CA DAT'",
          "TAT CA DAT" not in ra_h,
          "van bao tat ca dat du co bo that bai")
    check("mot bo THAT BAI -> noi ro SO BO khong dat",
          "1 BO KIEM KHONG DAT" in ra_h, ra_h[-400:])
    check("bo THAT BAI khong bi dem nham thanh BO QUA",
          "THAT BAI" in ra_h, ra_h[-400:])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print()
print(f"KET QUA: {pas} PASS / {fail} FAIL")
sys.exit(1 if fail else 0)
