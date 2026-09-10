# -*- coding: utf-8 -*-
"""Duong dan > 260 ky tu: loi khuyen phai LAM DUOC, khong duoc noi cho co.

Do tren project that DS3_006: CapCut tai anh tu CMS va dung nguyen chuoi base64
lam TEN FILE - 205 ky tu. Rieng phan tuong doi trong goi da 280 ky tu, tuc vuot
260 TRUOC CA KHI cong thu muc dich.

Voi file do, loi khuyen cu - "hay dat folder XUAT RA o duong dan NGAN hon
(vd D:\\GOI\\<ten>)" - la loi khuyen KHONG THE LAM DUOC: `D:\\` chi 3 ky tu,
3 + 280 van la 283. Nguoi dung se chuyen goi sang cho khac, chay lai 20 phut,
roi thay canh bao Y HET. Bao cao noi mot viec vo ich con te hon khong noi.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

B = chr(92)
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


# Ten file THAT lay tu DS3_006: CapCut dung nguyen chuoi base64 lam ten file.
# Giu DUNG do dai thuc te (205 ky tu) - do la con so quyet dinh ket qua phan loai.
TEN_DAI = ("eyJidWNrZXQiOiJmcm9udGllci1jbXMiLCJrZXkiOiIyMDI1LTEw"
           + ("x" * (205 - 52 - 5)) + ".webp")
assert len(TEN_DAI) == 205, len(TEN_DAI)


def main():
    import chay_tool
    G = chay_tool.nap_tool()

    print("=" * 72)
    print("Phan loai duong dan dai: rut ngan dich CUU DUOC hay KHONG")
    print("=" * 72)

    dich = "D:" + B + "GOI" + B + "DS3_006"          # 14 ky tu
    # (a) dai vi DICH dai -> rut ngan dich cuu duoc
    ngan_rel = "materials" + B + ("a" * 200) + ".mp4"
    # (b) dai vi TEN FILE -> rut ngan dich vo ich.
    # Dung DUNG cau truc that cua DS3_006: subdraft/<GUID 36>/materials/<ten 205>
    dai_rel = ("subdraft" + B + "6AEBA9FF-195F-4cf3-AFC0-F1476C65B2E8"
               + B + "materials" + B + TEN_DAI)
    # Phai vuot 255 thi dat o `D:\` (3 ky tu) moi con vuot 260 - do la dinh nghia
    # cua nhom "khong cuu duoc". Chot lai de test khong am tham do sai thu.
    assert 3 + 1 + len(dai_rel) > 259, len(dai_rel)

    dich_dai = B * 2 + "192.168.1.214" + B + "e" + B + "PROJECT NHAN BAN" \
        + B + "DEEP SEA 3" + B + "DS3_006"
    p_a = dich_dai + B + ngan_rel
    p_b = dich_dai + B + dai_rel

    rut, khong, toi_da = G.phan_loai_path_dai([p_a, p_b], dich_dai)

    print(f"  dich = {len(dich_dai)} ky tu")
    print(f"  (a) tong {len(p_a)} ky tu | phan trong goi {len(ngan_rel)}")
    print(f"  (b) tong {len(p_b)} ky tu | phan trong goi {len(dai_rel)}")
    print(f"  -> dich toi da cho phep: {toi_da} ky tu")

    check("(a) dai vi DICH -> xep vao nhom rut ngan duoc",
          any(p == p_a for p, _ in rut),
          f"rut = {[len(p) for p, _ in rut]}, khong = {[len(p) for p, _ in khong]}")
    check("(b) dai vi TEN FILE -> xep vao nhom KHONG cuu duoc",
          any(p == p_b for p, _ in khong),
          "neu xep nham vao 'rut ngan duoc', nguoi dung se chuyen goi va chay lai"
          " 20 phut de roi thay canh bao Y HET")
    check("moi duong dan deu duoc phan loai", len(rut) + len(khong) == 2)
    check("nguong dich toi da tinh tu phan trong goi DAI NHAT",
          toi_da == 259 - 1 - max(len(ngan_rel), len(dai_rel)),
          f"toi_da = {toi_da}")
    check("nguong am khi khong cach nao cuu duoc", toi_da < 0,
          f"toi_da = {toi_da} - phan trong goi da {len(dai_rel)} ky tu nen"
          " KHONG co thu muc dich nao du ngan")

    # Chi co loai (a): nguong phai duong va hop ly
    rut2, khong2, toi_da2 = G.phan_loai_path_dai([p_a], dich_dai)
    check("chi co loai rut ngan duoc -> khong bao nham loai kia", not khong2)
    check("nguong duong khi cuu duoc", toi_da2 > 0, f"toi_da2 = {toi_da2}")

    print()
    print("=" * 72)
    print("Bao cao / man hinh phai noi dung hai loai")
    print("=" * 72)
    src = (ROOT / "goi_project_capcut.py").read_text(encoding="utf-8")
    check("co goi phan_loai_path_dai (khong phai code chet)",
          src.count("phan_loai_path_dai(") >= 3,
          "phai duoc goi o CA bao cao lan man hinh")
    check("bao cao co muc rieng cho loai KHONG cuu duoc",
          "RUT NGAN THU MUC DICH KHONG CUU DUOC" in src)
    check("man hinh noi ro ten file qua dai la nguyen nhan",
          "TEN FILE do CapCut sinh qua dai" in src)
    check("khong con loi khuyen cu ap dung cho MOI truong hop",
          "Nen xuat ra duong dan NGAN hon (vd D:" not in src,
          "loi khuyen cu ap dung cho ca file ma no khong cuu duoc")

    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
