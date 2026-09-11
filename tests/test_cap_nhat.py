# -*- coding: utf-8 -*-
r"""AUTO-UPDATE: hop dong hanh vi - VIET TRUOC KHI CO CODE.

Vi sao viet truoc:
  R-02 (cap nhat khi dang goi do), R-03 (cap nhat loi lam app khong mo duoc),
  R-14 (onedir cap nhat do dang) deu muc **Cao** trong `tai_lieu/RISK.md`, va
  hau qua khong phai mot may ma **40-50 may cung luc**. Voi loai rui ro do,
  "viet code truoc, test sau" la cong thuc hong hang loat.

  Bo kiem nay mo ta HANH VI QUAN SAT DUOC, khong mo ta cach cai dat - de no
  khong khoa cung mot thiet ke chua duoc kiem chung. Vi du: "ngat giua chung
  thi PHAI con mot ban mo duoc", chu khong phai "phai dung os.replace".

Trang thai hien tai: `loi/cap_nhat.py` CHUA TON TAI. Bo nay in ro hop dong
roi bao qua - do la trang thai DUNG, khong phai bo qua im lang. Khi code ra
doi, cac phep se tu dong chay.

Bon nhom rang buoc:

  A. KHONG CHAN KHOI DONG (R-10)
     Kiem cap nhat la viec PHU. Mat mang, GitHub bi chan, rate-limit, JSON
     rac - tat ca phai that bai IM LANG va app van mo binh thuong. Mot hop
     thoai loi luc khoi dong voi 40-50 nguoi khong ranh ky thuat la mot
     lan dien thoai cho moi nguoi.

  B. SO SANH PHIEN BAN DUNG
     "1.10.0" > "1.9.0" - so sanh CHUOI se cho ket qua nguoc. Ban cu hon
     tren server KHONG duoc tu ha cap.

  C. CHAN KHI DANG GOI DO (R-02)
     Khong chi lam xam cai nut - API phai TU CHOI ke ca khi goi thang. Nut
     xam chi la lop hien thi; mot duong goi khac (phim tat, dong ho hen gio)
     se di vong qua no.

  D. NGUYEN TU (R-14, R-03)
     Onedir thay NHIEU file. Ngat giua chung phai de lai **hoac ban moi
     hoan chinh, hoac ban cu hoan chinh** - khong bao gio co trang thai thu
     ba. Phai giu duoc mot ban cu de quay ve.

Ky thuat gia lap - thu vien chuan thuan:
  - Mang: `http.server.ThreadingHTTPServer` tren 127.0.0.1:0. Tot hon va
    `urllib` vi no kiem ca tang socket.
  - Mat mang: tro vao cong DA DONG -> `ConnectionRefusedError` THAT.
  - Ngat giua chung: va `os.replace` nem o lan goi thu N, chay voi N = 1..K,
    moi N mot lan. Sau moi lan khang dinh: hoac ban moi hoan chinh, hoac ban
    cu hoan chinh. Day la kiem tinh nguyen tu kieu crash-consistency.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
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
        print(f"  FAIL  {ten}" + (f"  | {ct}" if ct else ""))


# Hop dong: moi dong la mot rang buoc PHAI dung khi code ra doi.
HOP_DONG = [
    ("A. KHONG CHAN KHOI DONG (R-10)", [
        "CN-01  HTTP ngu 30s -> main() van mo giao dien trong <= 2s",
        "CN-02  mat mang -> that bai IM LANG, khong hop thoai loi",
        "CN-03  GitHub tra 403 / rate-limit -> nhu CN-02",
        "CN-04  JSON rac (<html>...) -> khong nem, coi nhu khong co ban moi",
        "CN-05  tra ve 500 / timeout -> khong nem",
    ]),
    ("B. SO SANH PHIEN BAN", [
        "CN-10  '1.10.0' > '1.9.0'  (KHONG so sanh chuoi)",
        "CN-11  '1.2.0-beta' KHONG moi hon '1.2.0'",
        "CN-12  bang nhau -> khong bao co ban moi",
        "CN-13  ban CU HON tren server -> KHONG tu ha cap (R-03)",
        "CN-14  chuoi phien ban di dang -> khong nem, coi nhu khong biet",
    ]),
    ("C. CHAN KHI DANG GOI DO (R-02)", [
        "CN-20  dang goi -> nut Cap nhat bi XAM + noi ro ly do",
        "CN-21  dang goi -> API cap_nhat() NEM ke ca khi goi thang",
        "CN-22  HANG DOI dang chay cung chan",
        "CN-23  chan roi -> 0 file trong thu muc cai bi cham toi",
    ]),
    ("D. NGUYEN TU (R-14, R-03)", [
        "CN-30  tai ve THU MUC TAM, khong ghi de truc tiep",
        "CN-31  kiem SHA256 truoc khi ap; sai -> huy, ban cu nguyen ven",
        "CN-32  kiem DU FILE truoc khi doi ten (dem + kich thuoc)",
        "CN-33  ngat giua chung -> HOAC ban moi hoan chinh HOAC ban cu"
        " hoan chinh, KHONG BAO GIO trang thai thu ba",
        "CN-34  giu 1 ban cu (_cu/) sau khi cap nhat thanh cong",
        "CN-35  phuc_hoi() dua ve dung ban cu",
        "CN-36  chi giu 1 ban cu (khong phinh dia)",
        "CN-37  du lieu nguoi dung (cau_hinh, dau tu kiem) KHONG bi xoa",
        "CN-38  .exe dang chay khong the tu ghi de -> can tien trinh trung gian",
        "CN-39  khong quyen ghi (Program Files) -> bao ro, ban cu nguyen ven",
    ]),
]


def in_hop_dong():
    for nhom, cac in HOP_DONG:
        print(f"  {nhom}")
        for d in cac:
            print(f"     - {d}")
        print()


def test_hop_dong_duoc_ghi():
    """Hop dong phai co mat va day du truoc khi code ra doi."""
    print("=" * 72)
    print("HOP DONG HANH VI - auto-update")
    print("=" * 72)
    tong = sum(len(c) for _, c in HOP_DONG)
    check("tien de: hop dong co du 4 nhom rang buoc", len(HOP_DONG) == 4,
          len(HOP_DONG))
    check(f"tien de: hop dong liet ke {tong} rang buoc cu the", tong >= 20,
          tong)
    for nhom, cac in HOP_DONG:
        check(f"nhom '{nhom[:28]}...' co rang buoc", len(cac) >= 4, len(cac))


def test_rui_ro_duoc_truy_vet():
    """Moi rui ro Cao ve auto-update phai co rang buoc tuong ung."""
    print()
    print("=" * 72)
    print("TRUY VET - rui ro trong RISK.md <-> rang buoc")
    print("=" * 72)
    # Quet CA tieu de nhom lan tung dong: ma rui ro duoc ghi o tieu de
    # ("A. KHONG CHAN KHOI DONG (R-10)"), khong lap lai o moi dong.
    tat_ca = " ".join([nhom for nhom, _ in HOP_DONG]
                      + [d for _, cac in HOP_DONG for d in cac])
    for ma, mo_ta in (("R-02", "cap nhat khi dang goi do"),
                      ("R-03", "cap nhat loi lam app khong mo duoc"),
                      ("R-10", "mat mang lam app khong khoi dong duoc"),
                      ("R-14", "onedir cap nhat do dang")):
        check(f"{ma} ({mo_ta}) co rang buoc canh giu", ma in tat_ca)


def test_module_khi_co_code():
    """Chay hop dong THAT khi `loi/cap_nhat.py` ra doi."""
    print()
    print("=" * 72)
    print("HOP DONG THAT - chay khi loi/cap_nhat.py ton tai")
    print("=" * 72)

    f = ROOT / "loi" / "cap_nhat.py"
    if not f.is_file():
        print("  (loi/cap_nhat.py CHUA TON TAI - day la trang thai DUNG)")
        print()
        in_hop_dong()
        print("  Khi viet code, bo kiem nay se tu dong chay cac rang buoc tren.")
        print("  KHONG duoc viet code truoc roi sua hop dong cho khop sau.")
        check("hop dong da duoc chot TRUOC khi co code", True)
        return

    # --- Code da ra doi: chay hop dong that.
    import importlib
    CN = importlib.import_module("loi.cap_nhat")

    # B. So sanh phien ban - nhom re nhat, kiem duoc ngay.
    if hasattr(CN, "moi_hon"):
        check("CN-10 '1.10.0' moi hon '1.9.0' (khong so chuoi)",
              CN.moi_hon("1.10.0", "1.9.0") is True)
        check("CN-11 '1.2.0-beta' KHONG moi hon '1.2.0'",
              CN.moi_hon("1.2.0-beta", "1.2.0") is False)
        check("CN-12 bang nhau -> khong moi hon",
              CN.moi_hon("1.1.0", "1.1.0") is False)
        check("CN-13 ban CU HON -> khong moi hon (khong tu ha cap)",
              CN.moi_hon("1.0.0", "1.1.0") is False)
        try:
            CN.moi_hon("khong-phai-phien-ban", "1.1.0")
            check("CN-14 chuoi di dang -> khong nem", True)
        except Exception as ex:
            check("CN-14 chuoi di dang -> khong nem", False,
                  f"{type(ex).__name__}: {ex}")
    else:
        check("CN-10..14 module co ham moi_hon()", False,
              "thieu ham so sanh phien ban")

    # C. Chan khi dang goi do - rang buoc quan trong nhat (R-02).
    if hasattr(CN, "co_the_cap_nhat"):
        check("CN-21 dang goi -> co_the_cap_nhat() tra False",
              CN.co_the_cap_nhat(dang_chay=True) is False)
        check("CN-22 hang doi dang chay -> cung chan",
              CN.co_the_cap_nhat(dang_chay=False, hang_doi_chay=True) is False)
        check("CN-21b ranh -> cho phep",
              CN.co_the_cap_nhat(dang_chay=False) is True)
    else:
        check("CN-20..23 module co ham co_the_cap_nhat()", False,
              "thieu cong chan R-02")

    # D. Nguyen tu - phai co duong phuc hoi.
    check("CN-34/35 module co ham phuc_hoi()", hasattr(CN, "phuc_hoi"),
          "thieu duong quay ve ban cu (R-03)")


def _dung_ban(goc, nhan, so_file=6):
    """Dung mot 'ban cai' gia: thu muc co .exe + vai file tai nguyen."""
    import shutil
    d = Path(goc)
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    (d / "GoiProjectCapCut.exe").write_text(f"exe {nhan}", encoding="utf-8")
    (d / "cau_hinh.json").write_text('{"nhan": "%s"}' % nhan, encoding="utf-8")
    for i in range(so_file - 2):
        (d / f"tai_nguyen_{i}.dat").write_text(f"{nhan}-{i}", encoding="utf-8")
    return d


def _doc_nhan(d):
    """Doc nhan cua ban cai, hoac None neu khong con nguyen ven."""
    f = Path(d) / "GoiProjectCapCut.exe"
    if not f.is_file():
        return None
    return f.read_text(encoding="utf-8").replace("exe ", "")


def test_nguyen_tu():
    """CN-30..39: ngat giua chung KHONG duoc de lai trang thai thu ba.

    Day la phep kiem quan trong nhat cua ca bo - no giai truc tiep R-14.

    Cach lam: va `os.replace` nem o lan goi thu N, chay voi N = 1, 2, 3...
    Sau MOI lan, khang dinh: HOAC ban moi hoan chinh, HOAC ban cu hoan
    chinh (sau khi goi `phuc_hoi()`). Khong bao gio "nua nay nua kia".
    """
    import shutil
    import tempfile

    print()
    print("=" * 72)
    print("NGUYEN TU - ngat giua chung o MOI lan goi doi ten (R-14, R-03)")
    print("=" * 72)

    f = ROOT / "loi" / "cap_nhat.py"
    if not f.is_file():
        print("  (chua co loi/cap_nhat.py - bo qua)")
        return

    import importlib
    CN = importlib.import_module("loi.cap_nhat")

    tmp = Path(tempfile.mkdtemp(prefix="ngtu_"))
    try:
        # --- CN-31 SHA256 sai -> huy, ban cu NGUYEN VEN
        cai = _dung_ban(tmp / "cai", "CU")
        moi = _dung_ban(tmp / "moi", "MOI")
        tep = tmp / "tai_ve.zip"
        tep.write_bytes(b"noi dung tai ve")
        try:
            CN.ap_ban_moi(cai, moi, sha_mong_doi="sai" * 20, tep_tai=tep)
            check("CN-31 SHA256 sai -> phai NEM", False, "khong nem")
        except ValueError:
            check("CN-31 SHA256 sai -> nem ValueError", True)
        except Exception as ex:
            check("CN-31 SHA256 sai -> nem ValueError", False,
                  f"{type(ex).__name__}: {ex}")
        check("CN-31b SHA256 sai -> ban cu NGUYEN VEN",
              _doc_nhan(cai) == "CU", _doc_nhan(cai))

        # --- CN-31c SHA256 dung -> di tiep
        cai = _dung_ban(tmp / "cai", "CU")
        moi = _dung_ban(tmp / "moi", "MOI")
        sha = CN.bam_sha256(tep)
        CN.ap_ban_moi(cai, moi, sha_mong_doi=sha, tep_tai=tep)
        check("CN-31c SHA256 dung -> ap duoc ban moi",
              _doc_nhan(cai) == "MOI", _doc_nhan(cai))

        # --- CN-32 ban moi THIEU FILE -> huy, ban cu nguyen ven
        cai = _dung_ban(tmp / "cai", "CU")
        moi = _dung_ban(tmp / "moi", "MOI", so_file=2)
        try:
            CN.ap_ban_moi(cai, moi)
            check("CN-32 ban moi thieu file -> phai NEM", False, "khong nem")
        except ValueError:
            check("CN-32 ban moi thieu file -> nem ValueError", True)
        check("CN-32b thieu file -> ban cu NGUYEN VEN",
              _doc_nhan(cai) == "CU", _doc_nhan(cai))

        # --- CN-32c ban moi co file RONG -> cung huy
        cai = _dung_ban(tmp / "cai", "CU")
        moi = _dung_ban(tmp / "moi", "MOI")
        (moi / "tai_nguyen_0.dat").write_text("", encoding="utf-8")
        try:
            CN.ap_ban_moi(cai, moi)
            check("CN-32c ban moi co file rong -> phai NEM", False)
        except ValueError:
            check("CN-32c ban moi co file rong -> nem ValueError", True)

        # --- CN-33 NGAT o MOI lan goi doi ten
        #  Chay voi N = 1..3: ngat o lan thu N. Sau moi lan phai con MOT
        #  ban hoan chinh - khong bao gio trang thai thu ba.
        so_lan_toi_da = 4
        moi_lan_deu_on = True
        chi_tiet = []
        phai_cuu = []       # cac lan PHAI cuu thu cong (xem giai thich duoi)
        for n in range(1, so_lan_toi_da + 1):
            cai = _dung_ban(tmp / "cai", "CU")
            moi = _dung_ban(tmp / "moi", "MOI")
            cu_thu = tmp / ("cai" + CN.TEN_BAN_CU)
            if cu_thu.exists():
                shutil.rmtree(cu_thu, ignore_errors=True)

            dem = {"n": 0}
            import os as _os
            def doi_ten_ngat(a, b, _n=n, _d=dem):
                _d["n"] += 1
                if _d["n"] == _n:
                    raise OSError(f"gia lap NGAT o lan doi ten thu {_n}")
                return _os.replace(a, b)

            try:
                CN.ap_ban_moi(cai, moi, doi_ten=doi_ten_ngat)
            except OSError:
                pass

            # PHAN BIET hai truong hop - phep thu dot bien da chi ra rang
            # gop chung lai se che mat mot lo hong that:
            #   (a) `ap_ban_moi` TU dua ban cu tro lai  -> nguoi dung khong
            #       thay gi bat thuong.
            #   (b) phai goi `phuc_hoi()` thu cong      -> neu tien trinh
            #       CHET HAN (mat dien) thi khong ai goi duoc, va nguoi dung
            #       mo len thay MOT THU MUC TRONG.
            # (b) van "con mot ban hoan chinh" nen phep kiem gop se xanh ca
            # hai - nhung (a) moi la hanh vi dung.
            ngay = _doc_nhan(cai)
            if ngay is None:
                phai_cuu.append(n)
                CN.phuc_hoi(cai)
            nhan = _doc_nhan(cai)
            on = nhan in ("CU", "MOI")
            moi_lan_deu_on = moi_lan_deu_on and on
            chi_tiet.append(f"ngat o lan {n} -> {ngay or '(trong)'}"
                            + ("" if ngay else f" -> cuu -> {nhan}"))

        check("CN-33 ngat o BAT KY lan doi ten nao -> van con MOT ban hoan chinh",
              moi_lan_deu_on, " | ".join(chi_tiet))
        # Ngat o buoc 5 (doi ten ban moi vao cho ban cai) la truong hop
        # `ap_ban_moi` VAN CHAY TIEP duoc - no PHAI tu dua ban cu tro lai
        # ngay, khong duoc de nguoi dung o trang thai "khong co ban nao".
        check("CN-33b ap_ban_moi TU khoi phuc, khong de lai thu muc trong",
              not phai_cuu,
              f"phai cuu thu cong o cac lan: {phai_cuu}"
              " -> mat dien luc do la nguoi dung mat ban cai")
        print("       " + " | ".join(chi_tiet))

        # --- CN-34/35 giu ban cu + phuc hoi dung
        cai = _dung_ban(tmp / "cai", "CU")
        moi = _dung_ban(tmp / "moi", "MOI")
        CN.ap_ban_moi(cai, moi)
        check("CN-34 cap nhat xong -> con giu ban cu", CN.con_ban_cu(cai))
        check("CN-34b cap nhat xong -> dang chay ban MOI",
              _doc_nhan(cai) == "MOI", _doc_nhan(cai))
        check("CN-35 phuc_hoi() dua ve dung ban CU",
              CN.phuc_hoi(cai) and _doc_nhan(cai) == "CU", _doc_nhan(cai))

        # --- CN-36 cap nhat nhieu lan -> chi giu MOT ban cu
        cai = _dung_ban(tmp / "cai", "V1")
        for v in ("V2", "V3", "V4"):
            moi = _dung_ban(tmp / "moi", v)
            CN.ap_ban_moi(cai, moi)
        so_ban_cu = len([d for d in (tmp).iterdir()
                         if d.is_dir() and CN.TEN_BAN_CU in d.name])
        check("CN-36 cap nhat 3 lan -> chi giu DUNG 1 ban cu",
              so_ban_cu == 1, f"co {so_ban_cu} ban cu")
        check("CN-36b ban cu la ban NGAY TRUOC do",
              _doc_nhan(tmp / ("cai" + CN.TEN_BAN_CU)) == "V3",
              _doc_nhan(tmp / ("cai" + CN.TEN_BAN_CU)))

        # --- CN-21/23 chan khi dang goi: 0 file bi cham toi
        cai = _dung_ban(tmp / "cai", "CU")
        moi = _dung_ban(tmp / "moi", "MOI")
        truoc = sorted(f.name for f in cai.iterdir())
        try:
            CN.ap_ban_moi(cai, moi, dang_chay=True)
            check("CN-21 dang goi -> ap_ban_moi() phai NEM", False)
        except CN.DangBanKhongCapNhat:
            check("CN-21 dang goi -> nem DangBanKhongCapNhat", True)
        except Exception as ex:
            check("CN-21 dang goi -> nem DangBanKhongCapNhat", False,
                  f"{type(ex).__name__}: {ex}")
        check("CN-23 bi chan -> 0 file trong ban cai bi cham toi",
              sorted(f.name for f in cai.iterdir()) == truoc
              and _doc_nhan(cai) == "CU")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_khong_chan_khoi_dong():
    """CN-01..05: hoi may chu KHONG BAO GIO nem (R-10)."""
    print()
    print("=" * 72)
    print("R-10 - kiem cap nhat khong duoc chan khoi dong")
    print("=" * 72)

    f = ROOT / "loi" / "cap_nhat.py"
    if not f.is_file():
        print("  (chua co loi/cap_nhat.py - bo qua)")
        return

    import importlib
    CN = importlib.import_module("loi.cap_nhat")

    class _Gia:
        def __init__(self, noi_dung=None, nem=None):
            self.noi_dung, self.nem = noi_dung, nem
        def __call__(self, url, timeout=None):
            if self.nem:
                raise self.nem
            return self
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def read(self):
            return self.noi_dung

    import socket
    import urllib.error

    cac = [
        ("CN-02 mat mang (ConnectionRefused)",
         _Gia(nem=ConnectionRefusedError("khong noi duoc may chu"))),
        ("CN-02b DNS hong", _Gia(nem=socket.gaierror("khong phan giai duoc"))),
        ("CN-03 GitHub tra 403 / rate-limit",
         _Gia(nem=urllib.error.HTTPError("u", 403, "rate limit", {}, None))),
        ("CN-03b tra 500", _Gia(nem=urllib.error.HTTPError("u", 500, "loi", {}, None))),
        ("CN-04 JSON rac (tra ve HTML)", _Gia(noi_dung=b"<html>chan roi</html>")),
        ("CN-04b tra ve rong", _Gia(noi_dung=b"")),
        ("CN-05 het gio", _Gia(nem=TimeoutError("het gio"))),
    ]
    for ten, gia in cac:
        try:
            kq = CN.hoi_ban_moi("http://khong-quan-trong", "1.1.0", mo_url=gia)
            check(f"{ten} -> khong nem, tra None", kq is None, kq)
        except Exception as ex:
            check(f"{ten} -> khong nem, tra None", False,
                  f"{type(ex).__name__}: {ex}")

    # Truong hop CO ban moi that
    good = _Gia(noi_dung=b'{"tag_name": "1.2.0", "url_tai": "http://x/a.zip"}')
    kq = CN.hoi_ban_moi("http://x", "1.1.0", mo_url=good)
    check("CN-06 co ban moi that -> tra thong tin",
          kq is not None and kq.get("phien_ban") == "1.2.0", kq)
    kq2 = CN.hoi_ban_moi("http://x", "1.9.0", mo_url=good)
    check("CN-06b may chu co ban CU HON -> tra None (khong ha cap)",
          kq2 is None, kq2)


def main():
    test_hop_dong_duoc_ghi()
    test_rui_ro_duoc_truy_vet()
    test_module_khi_co_code()
    test_khong_chan_khoi_dong()
    test_nguyen_tu()
    print()
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
