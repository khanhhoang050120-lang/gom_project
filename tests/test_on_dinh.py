# -*- coding: utf-8 -*-
"""Giai doan 3 - ON DINH KHI CHAY DAI.

  - `_save_opt_index()` chay duoc trong khi cac thread khac dang CHEN vao dict
    (khong con RuntimeError "dictionary changed size during iteration")
  - Ghi so cache la ATOMIC: bi giet giua chung khong lam hong file cu
  - Loi ghi so dinh ky duoc DEM, khong nuot
  - `fixed_drives()` KHONG cham vao o mang (khong treo) va khong tra o mang
  - `la_o_mang()` nhan dien dung UNC / o da anh xa
  - `cau_hinh.json`: thieu file / hong / khoa la deu khong lam chet tool
  - So luong ma hoa tu ha xuong khi dich la o mang (bug #25)
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

pas = fail = 0
BS = chr(92)


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


def test_race(TU):
    print("=" * 72)
    print("Ghi so cache trong khi thread khac dang chen vao dict")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="race_"))
    try:
        cache, key_names = {}, {}
        for i in range(4000):
            k = (f"src{i}", 0, 1000, 0)
            cache[k] = Path(tmp) / f"d{i}.mp4"
            key_names[(f"base{i}", k)] = cache[k]

        dung = threading.Event()
        loi = []

        def chen(bat_dau):
            # Chen CO GIOI HAN: neu chen vo han thi dict phinh khong ngung, moi lan
            # ghi lai cham hon lan truoc va bo kiem chay hang phut. Muc dich o day
            # la tao TRANH CHAP, khong phai do suc chiu tai.
            i = bat_dau
            while not dung.is_set() and i < bat_dau + 40000:
                k = (f"them{i}", 0, 1000, 0)
                cache[k] = Path(tmp) / f"t{i}.mp4"
                key_names[(f"b{i}", k)] = cache[k]
                i += 4
                if i % 400 == 0:
                    time.sleep(0)          # nhuong luot -> tang co hoi chen giua

        ths = [threading.Thread(target=chen, args=(j,), daemon=True) for j in range(4)]
        for t in ths:
            t.start()
        try:
            for _ in range(60):
                try:
                    TU._save_opt_index(tmp, cache, key_names, log=lambda *a: None)
                except RuntimeError as ex:
                    loi.append(str(ex))
        finally:
            dung.set()
            for t in ths:
                t.join(timeout=2)

        print(f"  60 lan ghi trong khi 4 thread dang chen -> {len(loi)} lan nem RuntimeError")
        check("khong lan nao nem RuntimeError khi duyet dict",
              not loi,
              f"vi du: {loi[0] if loi else ''}"
              "  <- day chinh la loi giet thread nhip dap")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_atomic(TU):
    print()
    print("=" * 72)
    print("Ghi so cache phai ATOMIC - khong de lai file dang do")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="atom_"))
    try:
        cache = {("s", 0, 1, 0): tmp / "x.mp4"}
        TU._save_opt_index(tmp, cache, {}, log=lambda *a: None)
        so = TU._opt_index_path(tmp)
        check("so cache duoc tao", so.is_file())
        cu = so.read_bytes()

        # Ep loi giua chung: json.dump nem loi -> file DICH phai con nguyen ban cu
        dump_that = json.dump

        def dump_no(*a, **k):
            raise OSError("[ep loi] o dia het cho giua chung")

        json.dump = dump_no
        try:
            TU._save_opt_index(tmp, cache, {}, log=lambda *a: None)
        finally:
            json.dump = dump_that

        check("ban cu VAN NGUYEN VEN sau khi ghi that bai",
              so.is_file() and so.read_bytes() == cu,
              "ghi de truc tiep se lam mat sach so cache - dung tham hoa #29")
        con_tam = [p.name for p in tmp.iterdir() if p.name.endswith(".tmp")]
        check("khong de lai file tam", not con_tam, f"con: {con_tam}")

        # File hong thi _load_opt_index phai tra rong, khong ném loi
        so.write_bytes(b"{ khong phai json ")
        c, kn = TU._load_opt_index(tmp, log=lambda *a: None)
        check("so cache hong -> nap ra rong, khong nem loi", c == {} and kn == {})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_o_dia(G):
    # E1: cac hang so loai o (_O_MANG...) gio nam o tang tien ich `chung`.
    # `goi_project_capcut` chi import nhung ten no THUC SU dung, nen phai hoi
    # dung nguon thay vi doi no re-export moi thu.
    import chung
    print()
    print("=" * 72)
    print("Nhan dien o dia - khong duoc cham vao o mang (chong treo #25/#28)")
    print("=" * 72)
    t0 = time.monotonic()
    o = G.fixed_drives()
    mat = time.monotonic() - t0
    print(f"  fixed_drives() = {[str(x) for x in o]}  ({mat:.3f}s)")
    check("fixed_drives() nhanh (khong cham thiet bi)", mat < 2.0, f"mat {mat:.2f}s")
    check("fixed_drives() KHONG tra ve o mang",
          all(chung._loai_o(str(x)[0]) != chung._O_MANG for x in o),
          "quet o mang de tim file la vo ich va mat hang gio (bug #27)")

    check("UNC duoc nhan la o mang",
          G.la_o_mang(BS * 2 + BS.join(["may", "share", "x"])))
    check("o C: khong bi nham la o mang", not G.la_o_mang("C:" + BS))
    check("path UNC da qua _lp van nhan ra",
          G.la_o_mang(G._lp(BS * 2 + BS.join(["may", "share", "x"]))))


def test_cau_hinh(G):
    print()
    print("=" * 72)
    print("cau_hinh.json - thieu / hong / khoa la deu khong lam chet tool")
    print("=" * 72)
    ch = G.doc_cau_hinh(log=lambda *a: None)
    check("doc duoc cau hinh", isinstance(ch, dict) and "crf" in ch)
    check("co du cac khoa mac dinh",
          all(k in ch for k in G.CAU_HINH_MAC_DINH), f"ch = {sorted(ch)}")

    # So luong ma hoa theo dich
    n_mang = G.chon_so_luong(dict(G.CAU_HINH_MAC_DINH),
                             BS * 2 + BS.join(["nas", "share", "goi"]),
                             log=lambda *a: None)
    n_cuc_bo = G.chon_so_luong(dict(G.CAU_HINH_MAC_DINH), "C:" + BS + "goi",
                               log=lambda *a: None)
    print(f"  dich o MANG   -> {n_mang} luong")
    print(f"  dich CUC BO   -> {n_cuc_bo} luong")
    check("dich o mang thi so luong THAP hon", n_mang < n_cuc_bo,
          f"{n_mang} vs {n_cuc_bo}")
    check("dich o mang mac dinh la 2", n_mang == 2)

    ep = dict(G.CAU_HINH_MAC_DINH, workers=7)
    check("workers dat cung thi duoc ton trong",
          G.chon_so_luong(ep, "C:" + BS, log=lambda *a: None) == 7)
    xau = dict(G.CAU_HINH_MAC_DINH, workers="ba")
    check("workers sai kieu -> quay ve tu chon, khong chet",
          G.chon_so_luong(xau, "C:" + BS, log=lambda *a: None) >= 1)

    # Khoa '_...' la CHU THICH cua file mau, khong duoc bao nhu loi cau hinh.
    # Do tren lan chay THAT: tool in "! cau_hinh.json co khoa khong nhan ra
    # (bo qua): _crf, _huong_dan, ..." -> nguoi dung moi doc dau '!' se tuong
    # minh go sai va di sua mot thu von dung.
    # doc_cau_hinh() doc file NAM CANH TOOL (`Path(__file__).parent`). Khong duoc
    # ghi de file cau_hinh.json THAT de thu: mot ban chay production co the dang
    # doc no. Thay vao do doi tam `G.__file__` -> ham se tim trong thu muc tam.
    tmp = Path(tempfile.mkdtemp(prefix="cau_hinh_"))
    file_that = G.__file__
    try:
        (tmp / G.CAU_HINH_NAME).write_text(json.dumps({
            "_huong_dan": "chu thich", "_crf": "giai thich", "crf": 19,
            "khoa_la_that": 1,
        }), encoding="utf-8")
        G.__file__ = str(tmp / "gia.py")
        ghi = []
        ch2 = G.doc_cau_hinh(log=ghi.append)
        van = " ".join(ghi)
        check("van doc duoc gia tri that ben canh chu thich",
              ch2.get("crf") == 19, f"crf = {ch2.get('crf')}")
        check("KHONG bao khoa '_' nhu loi",
              "_crf" not in van and "_huong_dan" not in van,
              f"log = {van!r}\n-> chu thich cua chinh file mau bi bao la sai")
        check("VAN bao khoa la that su go nham",
              "khoa_la_that" in van,
              f"log = {van!r}\n-> im lang qua muc: go sai khoa that ma khong ai biet")
    finally:
        G.__file__ = file_that
        shutil.rmtree(tmp, ignore_errors=True)
    # Kiem chung da tra lai dung: doc lai file THAT phai ra mac dinh cua no
    check("da tra lai G.__file__ (khong ro ri sang phep kiem khac)",
          G.doc_cau_hinh(log=lambda *a: None).get("crf")
          == G.CAU_HINH_MAC_DINH["crf"],
          "cau hinh that khong doc lai duoc -> phep kiem nay lam ban trang thai")


def main():
    global pas, fail
    import chay_tool
    G = chay_tool.nap_tool()
    import toi_uu_dung_luong as TU
    test_race(TU)
    test_atomic(TU)
    test_o_dia(G)
    test_cau_hinh(G)
    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
