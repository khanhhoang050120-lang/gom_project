# -*- coding: utf-8 -*-
"""E2E HANG DOI - gom NHIEU project that trong MOT tien trinh.

Day la phep thu tren duong that cho huong C. Bo kiem don vi (`test_hang_doi_ui`)
dung ham gia; bo nay goi `main()` THAT tren draft gia.

Chot ba dieu quan trong nhat:
  1. Ba project deu ra goi DAY DU - khong cai nao thieu file vi cache dinh
  2. Mot muc LOI khong chan cac muc con lai
  3. Chi so do tren KET QUA THUC TE o dich, khong tin dong "Xong."
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# PHAI co dong nay de nap `draft_gia`: ban Python di kem dung `._pth` nen no
# KHONG tu them thu muc cua script vao sys.path. Thieu -> chay duoc bang Python
# he thong nhung VO tren ban giai nen. `test_dung_do.py` co phep kiem chot dieu
# nay, va no doi DUNG chuoi duoi day.
sys.path.insert(0, str(HERE))

import goi_project_capcut as G          # noqa: E402
import toi_uu_dung_luong as TU          # noqa: E402
from draft_gia import tao_draft_gia     # noqa: E402
from ui.chay_hang_doi import chay_mot_project   # noqa: E402
from ui.hang_doi import LOI, XONG, HangDoi, Muc  # noqa: E402

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


def dem_media(out):
    """Do KET QUA THUC TE o dich - khong tin dong 'Xong.' tren man hinh."""
    if not Path(out).is_dir():
        return 0, 0
    media = [p for p in Path(out).rglob("materials/*")
             if p.is_file() and p.suffix.lower() in
             (".mp4", ".wav", ".png", ".jpg")]
    return len(media), sum(p.stat().st_size for p in media)


print("=" * 68)
print(" E2E HANG DOI - gom nhieu project that trong mot tien trinh")
print("=" * 68)

ff, fp = TU.ff_paths(ROOT)
if not ff:
    print("  BO QUA: khong co ffmpeg di kem")
    sys.exit(2)

tmp = Path(tempfile.mkdtemp(prefix="hd_e2e_"))
try:
    # --- Ba project rieng biet ---
    print("\n  Dang tao 3 draft gia...")
    duong = []
    for i in (1, 2, 3):
        lv = tmp / f"lv{i}"
        lv.mkdir()
        mo_ta = tao_draft_gia(lv, ff, fp)
        duong.append((mo_ta["draft_dir"], tmp / f"goi{i}"))

    TC = {"trim": False, "scale": False, "cleanup": False, "do": ""}
    h = HangDoi(chay_mot=lambda m, nd: chay_mot_project(m, nd, G))
    for i, (d, o) in enumerate(duong, 1):
        h.them(Muc(d, o, tuy_chon=TC, ten=f"P{i}"))

    print("  Dang chay hang doi (3 project)...")
    h.chay()

    print("\nKET QUA")
    so = [dem_media(o) for _, o in duong]
    for i, (n, b) in enumerate(so, 1):
        print(f"    P{i}: {n} file, {b / 1024:.0f} KB, {h.muc[i-1].trang_thai}")

    check("ca 3 muc deu XONG",
          all(m.trang_thai == XONG for m in h.muc),
          [(m.ten, m.trang_thai, m.thong_bao) for m in h.muc])
    check("ca 3 goi deu CO file (do o dich, khong tin 'Xong.')",
          all(n > 0 for n, _ in so), so)
    check("ba goi ra SO FILE GIONG NHAU",
          so[0][0] == so[1][0] == so[2][0],
          f"{[n for n, _ in so]} -> cache lan truoc con dinh sang lan sau")
    check("ba goi ra DUNG LUONG giong nhau",
          so[0][1] == so[1][1] == so[2][1], [b for _, b in so])
    check("moi muc co nhat ky RIENG",
          all(len(m.nhat_ky) > 5 for m in h.muc),
          [len(m.nhat_ky) for m in h.muc])
    check("nhat ky khong lan sang nhau",
          h.muc[0].nhat_ky != h.muc[1].nhat_ky)
    check("tong ket dung",
          h.mo_ta_tong_ket() == "3/3 xong", h.mo_ta_tong_ket())

    # ------------------------------------------- mot muc LOI khong chan muc khac
    print("\nMOT MUC LOI khong duoc chan cac muc con lai")
    lv = tmp / "lv_hong"
    lv.mkdir()
    hong = tao_draft_gia(lv, ff, fp)

    h2 = HangDoi(chay_mot=lambda m, nd: chay_mot_project(m, nd, G))
    # Muc 1: duong dan draft KHONG TON TAI -> phai loi
    h2.them(Muc(tmp / "khong_he_co", tmp / "goi_x", tuy_chon=TC, ten="HONG"))
    # Muc 2: hop le -> phai xong
    h2.them(Muc(hong["draft_dir"], tmp / "goi_ok", tuy_chon=TC, ten="OK"))
    h2.chay()

    for m in h2.muc:
        print(f"    {m.ten}: {m.trang_thai} - {m.thong_bao[:60]}")

    check("muc hong -> LOI", h2.muc[0].trang_thai == LOI,
          f"{h2.muc[0].trang_thai}: {h2.muc[0].thong_bao}")
    check("muc sau VAN chay va XONG", h2.muc[1].trang_thai == XONG,
          f"{h2.muc[1].trang_thai}: {h2.muc[1].thong_bao}")
    n_ok, _ = dem_media(tmp / "goi_ok")
    check("goi cua muc sau CO file that", n_ok > 0, n_ok)
    check("tong ket dem ca loi",
          "1 lỗi" in h2.mo_ta_tong_ket(), h2.mo_ta_tong_ket())

    # ------------------------------------------- tra lai builtins.input
    print("\nTRA LAI trang thai toan cuc")
    import builtins
    check("builtins.input da duoc tra lai",
          builtins.input is not None and "TraLoi" not in type(builtins.input).__name__,
          type(builtins.input).__name__)
    check("sys.stdout da duoc tra lai",
          type(sys.stdout).__name__ != "Ong", type(sys.stdout).__name__)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print()
print("=" * 68)
print(f"KET QUA: {pas} PASS / {fail} FAIL")
print("=" * 68)
sys.exit(1 if fail else 0)
