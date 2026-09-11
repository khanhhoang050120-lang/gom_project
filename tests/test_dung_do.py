# -*- coding: utf-8 -*-
"""Nut "Dung do" phai THAT SU dung, va phai NOI THAT ve viec da dung.

Vi sao dang mot bo kiem rieng:
  Truoc khi co file nay, vung `index_by_names` KHONG co mot phep kiem nao. Da
  do bang PHEP THU DOT BIEN: pha han `index_by_names` cho no LUON tra `{}` ->
  27/27 bo kiem van DAT, 526 PASS / 0 FAIL. Pha dong bao cao cho no luon noi
  doi -> 27/27 van DAT. Thoat vong quet sau dung 1 thu muc -> 27/27 van DAT.
  Bo kiem xanh o vung khong ai kiem chinh la mot chung nhan gia.

Hai loai loi phai chan, VA CHUNG KHAC NHAU:
  1. Nut khong dung duoc viec  -> nguoi dung cho vo ich (do that: 25,8 giay).
  2. Dung roi nhung BAO CAO trinh bay cuoc do bi cat ngang y het mot cuoc do
     da xong -> nguoi dung di tim mot file van con nam nguyen tren o cua ho.
     Day dung la bug #92, va no rat de tai pham ngay trong ban vá cua chinh no.

Do bang SO DEM chu khong bang DONG HO: dong ho se chop tat tren may khac.
"""
from __future__ import annotations

import builtins
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# HERE cung PHAI co: ban Python di kem chay voi file `._pth`, ma khi co `._pth`
# thi Python KHONG tu them thu muc cua script vao sys.path. Thieu dong nay thi
# `from draft_gia import ...` chay duoc bang Python he thong nhung VO ngay tren
# ban giai nen tu zip - dung noi nguoi dung se chay.
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

pas = fail = 0


def check(ten, dk, ct=""):
    global pas, fail
    if dk:
        pas += 1
        print(f"  PASS  {ten}")
    else:
        fail += 1
        print(f"  FAIL  {ten}")
        for d in str(ct).splitlines():
            print(f"           {d}")


def cay_thu(goc: Path, n=400):
    """Cay thu muc du sau de huy con kip xay ra o giua."""
    for i in range(n):
        (goc / f"t{i:04d}" / "con").mkdir(parents=True, exist_ok=True)
    return n


# ---------------------------------------------------------------- T1
def t1_moc_huy_that_su_cat_duoc():
    print()
    print("=" * 72)
    print("T1  moc huy CAT DUOC vong quet (do bang SO THU MUC, khong bang giay)")
    print("=" * 72)
    import goi_project_capcut as G

    tmp = Path(tempfile.mkdtemp(prefix="dungdo_t1_"))
    try:
        cay_thu(tmp, 400)

        # Khong huy -> quet het
        tk_het = {}
        G.index_by_names([tmp], {"khong_ton_tai_dau_ca.mp4"}, thong_ke=tk_het)
        check("khong huy thi quet het cay", tk_het["quet"] > 400,
              f"chi quet {tk_het.get('quet')} thu muc - cay thu qua nho?")
        check("khong huy thi da_dung = False", tk_het["da_dung"] is False)

        # Huy sau dung 5 thu muc
        dem = [0]

        def nen_dung():
            dem[0] += 1
            return dem[0] > 5

        tk_huy = {}
        G.index_by_names([tmp], {"khong_ton_tai_dau_ca.mp4"},
                         nen_dung=nen_dung, thong_ke=tk_huy)
        check("huy thi da_dung = True", tk_huy["da_dung"] is True)
        check("huy thi DUNG NGAY, khong quet het",
              tk_huy["quet"] < 20 < tk_het["quet"],
              f"quet {tk_huy.get('quet')} thu muc sau khi bao dung"
              f" (khong huy: {tk_het.get('quet')})")
        print(f"    khong huy: {tk_het['quet']} thu muc"
              f" | huy sau 5: {tk_huy['quet']} thu muc")

        # Huy NGAY TU DAU, truoc ca isdir_safe cua root dau tien
        tk_0 = {}
        G.index_by_names([tmp], {"x.mp4"}, nen_dung=lambda: True, thong_ke=tk_0)
        check("huy tu truoc khi cham root nao", tk_0["quet"] == 0
              and tk_0["da_dung"] is True, str(tk_0))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------- T2
def t2_thong_ke_lay_so_that():
    """`quet` phai la so THUC, khong lay tu bo dem tien do (%3000)."""
    print()
    print("=" * 72)
    print("T2  so thu muc bao cao phai la SO THAT (khong lam tron xuong 3000)")
    print("=" * 72)
    import goi_project_capcut as G

    tmp = Path(tempfile.mkdtemp(prefix="dungdo_t2_"))
    try:
        n = cay_thu(tmp, 250)          # 250*2 + 1 = 501 thu muc, < 3000
        goi = [0]

        def prog(*a):
            goi[0] += 1

        tk = {}
        G.index_by_names([tmp], {"khong_co.mp4"}, on_progress=prog, thong_ke=tk)
        print(f"    on_progress duoc goi {goi[0]} lan"
              f" | thong_ke ghi {tk['quet']} thu muc")
        check("on_progress KHONG he duoc goi (duoi nguong 3000)", goi[0] == 0,
              "cay thu qua lon - phep kiem nay mat y nghia")
        check("nhung thong_ke VAN ghi dung so that", tk["quet"] > n,
              f"quet={tk.get('quet')}, cay co {n*2+1} thu muc."
              " Neu = 0 thi bao cao se noi 'CHUA DO O DAU CA' - noi doi.")
        check("ghi lai danh sach goc da dung", tk.get("goc") == [str(tmp)],
              str(tk.get("goc")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------- T3
def t3_tuong_thich_nguoc():
    """Goi kieu cu (khong nen_dung/thong_ke) phai y het truoc."""
    print()
    print("=" * 72)
    print("T3  goi kieu CU van chay y het (duong dong lenh khong duoc doi)")
    print("=" * 72)
    import goi_project_capcut as G

    tmp = Path(tempfile.mkdtemp(prefix="dungdo_t3_"))
    try:
        (tmp / "a" / "b").mkdir(parents=True)
        (tmp / "a" / "b" / "canh1.mp4").write_bytes(b"x")
        muon = {"canh1.mp4"}
        cach = [
            ("2 positional", lambda: G.index_by_names([tmp], muon)),
            ("on_progress=", lambda: G.index_by_names([tmp], muon,
                                                      on_progress=lambda *a: None)),
            ("on_error=", lambda: G.index_by_names([tmp], muon,
                                                   on_error=lambda ls: None)),
            ("nen_dung=None", lambda: G.index_by_names([tmp], muon,
                                                       nen_dung=None)),
        ]
        for ten, f in cach:
            idx = f()
            check(f"{ten}: van tim thay file", "canh1.mp4" in idx, str(idx))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------- T4
def t4_bao_cao_khong_noi_doi():
    """Sau khi huy, KHONG duoc in cac chuoi ket luan dut khoat."""
    print()
    print("=" * 72)
    print("T4  bao cao sau khi huy KHONG duoc noi doi (bug #92)")
    print("=" * 72)
    src = (ROOT / "goi_project_capcut.py").read_text(encoding="utf-8")

    check("co khoi rieng cho truong hop bi dung giua chung",
          '_tk_do.get("da_dung")' in src,
          "khong co khoi nay thi mot cuoc do bi cat ngang se duoc trinh bay y"
          " het mot cuoc do da xong - dung bug #92")
    check("khoi do noi ro DAY KHONG PHAI ket luan 'khong tim thay'",
          "KHONG phai ket" in src and "khong tim thay" in src, "")
    check("dong THIEU lay so tu thong_ke, KHONG tu bo dem tien do",
          '_tk_do["quet"]' in src and "_da_quet[0]" not in src,
          "`_da_quet` lay so tu on_progress (moi 3000 thu muc) nen sai san")
    check("con giu guard #92 cho truong hop chua do o dau ca",
          "CHUA DO O DAU CA" in src, "")
    check("moi duong huy deu return TRUOC khi ghi bao cao",
          src.count("_thoat_huy(") >= 6,
          f"chi thay {src.count('_thoat_huy(')} cho - thieu pha nao do")
    co = "_nen_dung = (tuy_chon or {})" in src
    check("co doc nen_dung tu tuy_chon", co,
          "khong doc thi nut Dung do cam hoan toan")
    check("doc nen_dung o DAU main(), khong trong nhanh che do 4",
          co and src.index("_nen_dung = (tuy_chon or {})")
          < src.index('if input("Chon 1 hoac 4'),
          "doc trong nhanh che do 4 -> nut CAM o che do nguyen ban")


# ---------------------------------------------------------------- T5
def t5_huy_giua_pha_quet_json():
    """`collect_refs` phai nem `_DaHuy`, khong tra ve ket qua mot phan."""
    print()
    print("=" * 72)
    print("T5  huy giua pha quet JSON -> NEM, khong tra ve mot phan")
    print("=" * 72)
    import goi_project_capcut as G
    from draft_gia import tao_draft_gia
    import toi_uu_dung_luong as TU

    ffmpeg, ffprobe = TU.ff_paths(ROOT)
    if not ffmpeg:
        print("  (khong co ffmpeg -> bo qua)")
        return
    tmp = Path(tempfile.mkdtemp(prefix="dungdo_t5_"))
    try:
        mo = tao_draft_gia(tmp, ffmpeg, ffprobe)
        draft = Path(mo["draft_dir"])

        r = G.collect_refs(draft)          # khong huy: chay binh thuong
        check("khong huy thi collect_refs tra ve du 4 phan", len(r) == 4)

        try:
            G.collect_refs(draft, nen_dung=lambda: True)
            check("huy thi collect_refs NEM _DaHuy", False,
                  "no tra ve binh thuong -> ket qua MOT PHAN se duoc dung tiep,"
                  " va `cleanup_unused` co the XOA THAT file dang dung")
        except G._DaHuy as ex:
            check("huy thi collect_refs NEM _DaHuy", True)
            check("loi noi ro dang o buoc nao", "json" in str(ex).lower(),
                  str(ex))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------- T6
def t6_giao_dien_nut_va_nhan():
    print()
    print("=" * 72)
    print("T6  giao dien: nut va nhan phai noi dung su that")
    print("=" * 72)
    try:
        import tkinter as tk
        r = tk.Tk()
        r.destroy()
    except Exception as ex:
        print(f"  (khong co tkinter -> bo qua: {ex})")
        return
    import tkinter as tk
    import giao_dien

    root = tk.Tk()
    root.withdraw()
    try:
        g = giao_dien.GiaoDien(root)
        check("co co_huy va la threading.Event",
              isinstance(g.co_huy, threading.Event))
        check("`nen_dung` truyen di la is_set (khong bao gio nem)",
              "self.co_huy.is_set" in
              (ROOT / "giao_dien.py").read_text(encoding="utf-8"),
              "truyen lambda doc bien tkinter se nem tu thread phu")

        # Bam Dung do khi CHUA bam COPY
        g.tra_loi_tien_hanh = None
        g.co_huy.clear()
        g.cho_tien_hanh.clear()
        hop = []
        giao_dien.messagebox.showinfo = lambda *a, **k: hop.append(a[0] if a else "?")
        g._dung_do()
        check("bam Dung -> co_huy duoc dat", g.co_huy.is_set())
        check("bam Dung -> KHONG hien hop thoai 'Da bat dau copy roi'", not hop,
              f"hien {hop} - noi doi, chua copy byte nao")
        check("bam Dung -> nut tu xam", str(g.nut_dung["state"]) == "disabled",
              f"state={g.nut_dung['state']}")
        check("bam Dung -> nhan nut doi thanh 'Dang dung...'",
              "dừng" in str(g.nut_dung["text"]).lower(), str(g.nut_dung["text"]))
        check("bam Dung -> tra loi 'n' cho cau hoi Tien hanh",
              g.tra_loi_tien_hanh == "n")

        # Bam lan hai: im lang, KHONG hien hop thoai sai
        hop.clear()
        g._dung_do()
        check("bam lan HAI: im lang, khong hop thoai noi doi", not hop, str(hop))

        # Sau khi huy, tin "cho_tien_hanh" KHONG duoc bat lai nut COPY
        g.nut_copy.config(state="disabled")
        g.hd.put(("cho_tien_hanh", None))
        g._rut_hang_doi()
        root.update()
        check("sau khi huy, nut COPY KHONG duoc bat lai",
              str(g.nut_copy["state"]) == "disabled",
              "moi nguoi VUA HUY di bam TIEN HANH COPY la giao goi thieu file")

        # `_bat_dau` phai xoa co - neu khong, lan chay thu hai ngat ngay
        g.co_huy.set()
        g.v_draft.set("")
        giao_dien.messagebox.showwarning = lambda *a, **k: None
        g._bat_dau()               # se dung vi thieu duong dan, nhung...
        check("KHONG xoa co qua som khi dau vao sai", g.co_huy.is_set(),
              "chua den doan chay thi chua duoc dong den co")
    finally:
        try:
            root.destroy()
        except Exception:
            pass


# ---------------------------------------------------------------- T7
def t7_nhan_ket_thuc():
    """Ket thuc sau mot cu HUY khong duoc mang nhan cua lan chay THANH CONG."""
    print()
    print("=" * 72)
    print("T7  nhan ket thuc: 'Da huy' chu khong phai 'Xong.'")
    print("=" * 72)
    src = (ROOT / "giao_dien.py").read_text(encoding="utf-8")
    check("nhan ket thuc phu thuoc co huy",
          'if self.co_huy.is_set() else "Xong."' in src,
          "ket thuc bang 'Xong.' sau khi huy la mot dang bao cao sai 'da xong'")
    check("co nhan rieng cho duong huy",
          "Đã huỷ — chưa copy gì cả." in src, "")
    check("hai nhanh except GIU NGUYEN (loi that phai thang nhanh huy)",
          'self.hd.put(("xong", "CÓ LỖI — xem Nhật ký."))' in src,
          "boc `finally` bang co huy se che mat loi that")
    check("nut Dung do duoc tra lai nhan khi xong",
          'self.nut_dung.config(state="disabled", text="Dừng dò")' in src, "")


# ---------------------------------------------------------------- T8
def t8_moi_file_test_deu_duoc_dang_ky():
    """Mot bo kiem khong nam trong BO_KIEM thi khong bao gio chay."""
    print()
    print("=" * 72)
    print("T8  moi file tests/test_*.py deu phai co trong BO_KIEM")
    print("=" * 72)
    # DOC BO_KIEM THAT chu khong grep chuoi: mot dong bi comment ra van con
    # nguyen ten file trong ma nguon, nen grep se bao "co dang ky" trong khi bo
    # kiem do KHONG BAO GIO chay. Phep thu dot bien da bat duoc dung loi nay
    # trong chinh phien ban dau cua phep kiem nay.
    import importlib.util
    dc = importlib.util.spec_from_file_location("_ch", HERE / "chay_het.py")
    m = importlib.util.module_from_spec(dc)
    dc.loader.exec_module(m)
    da_dk = {t[1] for t in m.BO_KIEM}
    co = {p.name for p in HERE.glob("test_*.py")}
    thieu = sorted(co - da_dk)
    check(f"da quet {len(co)} file test", len(co) > 0)
    check(f"BO_KIEM doc duoc {len(da_dk)} muc", len(da_dk) >= len(co),
          f"BO_KIEM chi co {len(da_dk)} muc cho {len(co)} file test")
    # Moi file test PHAI tu them HERE vao sys.path: ban Python di kem co `._pth`
    # nen khong tu them thu muc script. Thieu -> chay duoc o repo, VO tren ban
    # giai nen. Da vap dung loi nay khi viet chinh file nay.
    import ast
    trong_tests = {q.stem for q in HERE.glob("*.py")}
    quen = []
    for f in sorted(co):
        van = (HERE / f).read_text(encoding="utf-8")
        # Doc bang AST chu khong grep: `test_khong_dependency.py` co NHAC ten
        # `chay_tool`/`draft_gia` trong mot danh sach chuoi chu khong he import
        # chung - grep se bao dong gia.
        nap = set()
        for nut in ast.walk(ast.parse(van)):
            if isinstance(nut, ast.Import):
                nap |= {a.name.split(".")[0] for a in nut.names}
            elif isinstance(nut, ast.ImportFrom) and nut.level == 0 and nut.module:
                nap.add(nut.module.split(".")[0])
        if (nap & trong_tests) and "sys.path.insert(0, str(HERE))" not in van:
            quen.append(f"{f} (nap {sorted(nap & trong_tests)})")
    check("moi bo kiem nap module trong tests/ deu them HERE vao sys.path",
          not quen,
          f"{quen} -> chay duoc bang Python he thong nhung VO tren ban giai nen"
          " (Python di kem dung `._pth` nen khong tu them thu muc script)")
    check("khong file test nao bi bo quen", not thieu,
          f"{thieu} khong nam trong BO_KIEM -> KHONG BAO GIO chay."
          " Dung con benh 'cho duy nhat nguoi dung di qua lai la cho khong ai"
          " kiem', o mot tang khac.")


def t9_chay_that_va_doc_dau_ra():
    """CHAY THAT `main()` roi HUY giua pha do - doc dau ra bang mat.

    T4 chi doc MA NGUON. Phep thu dot bien da chung minh la khong du: doi khoi
    do thanh `if False and _tk_do.get("da_dung"):` thi chuoi van con nguyen va
    T4 van xanh, trong khi bao cao da noi doi tro lai. Chi co chay that moi bat
    duoc. Day cung la ly do #92 lot qua 27 bo kiem lan truoc.
    """
    print()
    print("=" * 72)
    print("T9  CHAY THAT roi huy - dau ra phai noi that (kiem hanh vi)")
    print("=" * 72)
    import goi_project_capcut as G
    import toi_uu_dung_luong as TU
    from draft_gia import tao_draft_gia
    import chay_tool

    ffmpeg, ffprobe = TU.ff_paths(ROOT)
    if not ffmpeg:
        print("  (khong co ffmpeg -> bo qua)")
        return

    tmp = Path(tempfile.mkdtemp(prefix="dungdo_t9_"))
    try:
        mo = tao_draft_gia(tmp, ffmpeg, ffprobe)
        draft = Path(mo["draft_dir"])

        # Day mot media NGOAI (duoc tham chieu bang duong dan tuyet doi) sang
        # cho khac -> Pass 1 khong thay -> BUOC DO THEO TEN phai chay.
        # Day file trong `materials/` la VO ICH: no van nam dung cho trong goi.
        an = tmp / "AN_GIAU"
        an.mkdir()
        da_day = 0
        for q in mo["media_ngoai"]:
            q = Path(q)
            if q.is_file():
                shutil.move(str(q), str(an / q.name))
                da_day += 1
                break
        check("da day duoc 1 media ra cho khac (de buoc do phai chay)",
              da_day == 1,
              "khong day duoc thi phep kiem nay VO NGHIA - khong co gi de do")
        if da_day != 1:
            return

        # Cay thu muc du lon de huy kip xay ra o GIUA
        kho = tmp / "CAY"
        for i in range(300):
            (kho / f"t{i:04d}").mkdir(parents=True)

        dem = [0]

        def nen_dung():
            dem[0] += 1
            return dem[0] > 30          # huy sau ~30 thu muc

        out = tmp / "GOI_RA"
        tra_loi = chay_tool.tao_bo_tra_loi(draft, out, che_do="1",
                                              tien_hanh=True,
                                              thu_muc_do=str(kho))
        cu_in = builtins.input
        builtins.input = tra_loi
        bo_dem = io.StringIO()
        try:
            with redirect_stdout(bo_dem):
                G.main(tuy_chon={"nen_dung": nen_dung})
        finally:
            builtins.input = cu_in
        ra = bo_dem.getvalue()

        check("co vao buoc DO THEO TEN", "DO THEO TEN" in ra.upper(),
              "khong vao buoc do thi phep kiem nay khong kiem duoc gi"
              f"\n{ra[-800:]}")
        check("NOI RO la da dung giua chung",
              "DA DUNG BUOC DO THEO TEN" in ra, ra[-1200:])
        check("noi ro day KHONG phai ket luan 'khong tim thay'",
              "KHONG phai ket luan" in ra, ra[-1200:])
        check("KHONG in dong THIEU dut khoat (bug #92)",
              "--- THIEU (da do" not in ra,
              "trinh bay mot cuoc do bi cat ngang y het mot cuoc do da xong"
              f"\n{ra[-1200:]}")
        check("KHONG do oan 'CHUA DO O DAU CA'",
              "CHUA DO O DAU CA" not in ra, ra[-1200:])
        check("noi ro CHUA COPY GI CA", "CHUA COPY GI CA" in ra, ra[-800:])
        check("KHONG tao thu muc xuat ra", not out.exists(),
              f"{out} da duoc tao - duong huy phai return truoc do")
        check("KHONG ghi file bao cao (khong co gi de noi doi)",
              not (out / "_BAO_CAO_THIEU.txt").exists())

        # Doi chung: KHONG huy thi phai in dong THIEU binh thuong
        dem2 = [0]
        out2 = tmp / "GOI_RA_2"
        tra_loi2 = chay_tool.tao_bo_tra_loi(draft, out2, che_do="1",
                                               tien_hanh=False,
                                               thu_muc_do=str(kho))
        builtins.input = tra_loi2
        bo_dem2 = io.StringIO()
        try:
            with redirect_stdout(bo_dem2):
                G.main(tuy_chon={"nen_dung": lambda: False})
        finally:
            builtins.input = cu_in
        ra2 = bo_dem2.getvalue()
        check("DOI CHUNG: khong huy -> KHONG in 'DA DUNG BUOC DO'",
              "DA DUNG BUOC DO THEO TEN" not in ra2, ra2[-600:])
        check("DOI CHUNG: khong huy -> co in dong THIEU voi so thu muc THAT",
              "--- THIEU (da do HET" in ra2, ra2[-900:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    t1_moc_huy_that_su_cat_duoc()
    t2_thong_ke_lay_so_that()
    t3_tuong_thich_nguoc()
    t4_bao_cao_khong_noi_doi()
    t5_huy_giua_pha_quet_json()
    t6_giao_dien_nut_va_nhan()
    t7_nhan_ket_thuc()
    t8_moi_file_test_deu_duoc_dang_ky()
    t9_chay_that_va_doc_dau_ra()
    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
