# -*- coding: utf-8 -*-
"""D6 (nhom NUOT LOI) - ep tung kieu that bai, khang dinh bao cao PHAI noi that.

Nhom nay gay hau qua nang nhat vi nguoi dung TIN vao ket luan sai:

  #4   ghi JSON voi path goc khi copy fail -> ban xuat KHONG tu chua
  #5   bao "Ban tu chua DU" SAI du khong copy duoc file nao
  #11  bo sot du an con -> thieu media nhung van bao "DU"
  #17  lien ket cung hong roi AM THAM copy that - khong dem, khong bao
  #20  bo qua copy ban goc ma khong tro lai het -> thieu file

Cach kiem: EP LOI o dung diem do, roi doc `_BAO_CAO_THIEU.txt`.
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

from draft_gia import tao_draft_gia          # noqa: E402
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


def doc_bao_cao(out):
    p = Path(out) / "_BAO_CAO_THIEU.txt"
    import chung as C
    if not C.isfile_safe(p):
        return None
    return Path(C._lp(p)).read_text(encoding="utf-8", errors="replace")


def test_copy_that_bai(ffmpeg, ffprobe):
    """#4 + #5 - copy media that bai thi TUYET DOI khong duoc bao 'DU'."""
    print("=" * 72)
    print("#4/#5 - EP copy media that bai -> khong duoc ket luan 'DU'")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="nuot4_"))
    try:
        mo_ta = tao_draft_gia(tmp, ffmpeg, ffprobe, co_subdraft=False)
        out = tmp / "GOI"
        G = chay_tool.nap_tool()

        that = shutil.copy2
        so_lan = [0]

        def copy_hong(src, dst, *a, **k):
            # Chi pha media, khong pha file JSON -> mo phong dung canh "dia day
            # giua chung" chu khong phai hong toan bo
            if str(src).lower().endswith((".mp4", ".m4a")):
                so_lan[0] += 1
                raise OSError("[ep loi] khong con cho trong tren o dich")
            return that(src, dst, *a, **k)

        shutil.copy2 = copy_hong
        try:
            ma, ra, _ = chay_tool.chay(G, mo_ta["draft_dir"], out, che_do="1")
        finally:
            shutil.copy2 = that

        print(f"  da ep hong {so_lan[0]} lan copy media")
        check("co ep duoc loi copy", so_lan[0] > 0,
              "neu bang 0 thi bo kiem nay khong chung minh duoc gi")
        bc = doc_bao_cao(out)
        check("van ghi duoc bao cao", bc is not None)
        if bc:
            check("#5: KHONG duoc ket luan 'Khong thieu'",
                  "Khong thieu" not in bc,
                  "\n".join(bc.splitlines()[:26]))
            check("bao cao co muc COPY THAT BAI",
                  "COPY THAT BAI" in bc or "copy" in bc.lower(),
                  "\n".join(bc.splitlines()[:26]))
        check("console canh bao chua du",
              "CHUA du" in ra or "CANH BAO" in ra, ra[-500:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_ghi_json_khi_copy_fail(ffmpeg, ffprobe):
    """#4 - khong duoc viet lai path sang dich khi file dich CHUA CO."""
    print()
    print("=" * 72)
    print("#4 - copy fail thi KHONG duoc viet lai tham chieu sang dich rong")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="nuot4b_"))
    try:
        mo_ta = tao_draft_gia(tmp, ffmpeg, ffprobe, co_subdraft=False)
        out = tmp / "GOI"
        G = chay_tool.nap_tool()
        import chung as C

        that = shutil.copy2

        def copy_hong(src, dst, *a, **k):
            if str(src).lower().endswith(".mp4"):
                raise OSError("[ep loi] mat ket noi")
            return that(src, dst, *a, **k)

        shutil.copy2 = copy_hong
        try:
            chay_tool.chay(G, mo_ta["draft_dir"], out, che_do="1")
        finally:
            shutil.copy2 = that

        # Moi tham chieu da viet lai PHAI tro toi file CO THAT
        hong = []
        for jf in C.iter_json_files(out):
            try:
                obj, _ = C.read_json_loose(jf)
            except Exception:
                continue

            def cb(k, v, _b=C.draft_root_of(jf, out)):
                if not isinstance(v, str) or not v:
                    return
                if Path(v.replace("\\", "/")).suffix.lower() not in C.VIDEO_AUDIO_EXT:
                    return
                if v.startswith("##"):
                    i = v.find("_##")
                    if i == -1:
                        return
                    duoi = v[i + 3:].lstrip("/\\")
                elif v.startswith("./"):
                    duoi = v[2:].lstrip("/\\")
                else:
                    return
                dich = Path(_b) / duoi.replace("/", os.sep)
                if not C.isfile_safe(dich):
                    hong.append(f"{jf.name}: {v}")

            C.deep_walk_strings(obj, cb)
        check("khong tham chieu nao tro toi file KHONG ton tai",
              not hong,
              "day chinh la bug #4: viet lai path du copy that bai\n"
              + "\n".join(hong[:8]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_du_an_con(ffmpeg, ffprobe):
    """#11 - media cua du an con phai duoc gom, khong duoc bao 'DU' khi thieu."""
    print()
    print("=" * 72)
    print("#11 - media cua DU AN CON phai duoc gom day du")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="nuot11_"))
    try:
        mo_ta = tao_draft_gia(tmp, ffmpeg, ffprobe, co_subdraft=True)
        out = tmp / "GOI"
        G = chay_tool.nap_tool()
        chay_tool.chay(G, mo_ta["draft_dir"], out, che_do="1")

        import chung as C
        ten_trong_goi = set()
        for dp, _d, fs in os.walk(C._lp(out)):
            for f in fs:
                ten_trong_goi.add(f.lower())

        # File cua du an con (ca ban nhung inline lan thu muc that)
        can = ["canh_du_an_con.mp4", "trong_sub.mp4"]
        thieu = [t for t in can if t not in ten_trong_goi]
        print(f"  media du an con trong goi: {[t for t in can if t in ten_trong_goi]}")
        check("gom du media cua du an con", not thieu,
              f"thieu: {thieu}  <- day la bug #11: bo sot subdraft nhung van bao DU")

        bc = doc_bao_cao(out)
        if bc:
            check("bao cao co nhac du an con",
                  "DU AN CON" in bc, "\n".join(bc.splitlines()[:6]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_lien_ket_cung(ffmpeg, ffprobe):
    """#17 - os.link hong thi khong duoc AM THAM copy that ma khong dem."""
    print()
    print("=" * 72)
    print("#17 - lien ket cung hong -> phai co duong quay ve, khong mat file")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="nuot17_"))
    try:
        # `dung_chung_footage`: CUNG mot nguon phai di toi HAI thu muc materials/
        # (cha + du an con). Do la truong hop DUY NHAT kich hoat os.link. Khong co
        # no thi bo kiem nay dau MA KHONG KIEM DUOC GI - dung kieu "bao cao sai"
        # ma ca du an dang chong.
        mo_ta = tao_draft_gia(tmp, ffmpeg, ffprobe, co_subdraft=True,
                              dung_chung_footage=True)
        out = tmp / "GOI"
        G = chay_tool.nap_tool()

        link_that = os.link
        so_lan = [0]

        def link_hong(*a, **k):
            so_lan[0] += 1
            raise OSError("[ep loi] o dich khong ho tro lien ket cung (SMB)")

        os.link = link_hong
        try:
            chay_tool.chay(G, mo_ta["draft_dir"], out, che_do="1")
        finally:
            os.link = link_that

        print(f"  so lan os.link bi ep hong: {so_lan[0]}")
        check("CO kich hoat duong lien ket cung (neu 0 thi bo kiem vo nghia)",
              so_lan[0] > 0,
              "os.link khong duoc goi lan nao -> phep kiem duoi day dau RONG,"
              " khong chung minh duoc gi ve bug #17")
        bc = doc_bao_cao(out)
        check("van ra duoc bao cao", bc is not None)
        if bc and so_lan[0] > 0:
            check("goi VAN du du lien ket cung hong (co duong quay ve copy that)",
                  "Khong thieu" in bc,
                  "lien ket cung hong khong duoc lam mat file - phai copy that\n"
                  + "\n".join(bc.splitlines()[:26]))
            # File phai co THAT o ca hai noi, khong phai chi mot ban lien ket
            import chung as C
            dem = 0
            for dp, _d, fs in os.walk(C._lp(out)):
                dem += sum(1 for f in fs if f.lower() == "canh1.mp4")
            print(f"  so ban canh1.mp4 trong goi: {dem}")
            check("file duoc dung chung co mat o CA HAI thu muc materials/",
                  dem >= 2, f"chi thay {dem} ban")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    import toi_uu_dung_luong as TU
    ffmpeg, ffprobe = TU.ff_paths(ROOT)
    if not ffmpeg:
        print("KHONG tim thay ffmpeg -> bo qua")
        return 2
    test_copy_that_bai(ffmpeg, ffprobe)
    test_ghi_json_khi_copy_fail(ffmpeg, ffprobe)
    test_du_an_con(ffmpeg, ffprobe)
    test_lien_ket_cung(ffmpeg, ffprobe)
    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
