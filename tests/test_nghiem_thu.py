# -*- coding: utf-8 -*-
r"""Kiem chinh VERIFIER (`tests/nghiem_thu_goi.py`).

Vi sao can bo kiem nay:
  Verifier bao "DAT" chua chung minh duoc gi. Mot verifier luon tra DAT cung
  bao DAT tren moi goi - va no nguy hiem hon la khong co verifier nao, vi no
  tao cam giac an toan gia.

  Checklist bug.md: "Bo kiem phai FAIL khi khong co du lieu: ket luan 'dat'
  bat buoc kem 'da kiem N thu' voi N > 0. Quet 0 file ma bao PASS la loi
  nang hon bao FAIL sai" (bug #36).

Cach kiem: dung cac goi CO Y HONG theo tung kieu khac nhau, verifier PHAI do
dung cai no phai do. Va mot goi lanh lan, verifier phai xanh.

Khong can ffmpeg - cac goi o day dung bang JSON + file rong/khong rong, chu
khong can media that. Chay duoc tren runner sach.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import nghiem_thu_goi as NT

pas = fail = 0


def check(ten, dk, ct=""):
    global pas, fail
    if dk:
        pas += 1
        print(f"  PASS  {ten}")
    else:
        fail += 1
        print(f"  FAIL  {ten}" + (f"  | {ct}" if ct else ""))


def _ghi(p: Path, o):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8")


def _tao_goi_lanh(goc: Path) -> Path:
    """Mot goi TU CHUA dung chuan: moi tham chieu deu tuong doi + co that."""
    goi = goc / "goi"
    mat = goi / "materials" / "video"
    mat.mkdir(parents=True)
    (mat / "a.mp4").write_bytes(b"x" * 100)
    (mat / "b.mp4").write_bytes(b"y" * 100)

    _ghi(goi / "draft_meta_info.json", {
        "draft_materials": [{"type": 0, "value": [
            {"id": "r1", "file_Path": "./materials/video/a.mp4"},
            {"id": "r2", "file_Path": "./materials/video/b.mp4"},
        ]}]})
    _ghi(goi / "draft_content.json", {
        "materials": {"videos": [
            {"id": "m1", "path":
             "##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##"
             "/materials/video/a.mp4"},
            {"id": "m2", "path":
             "##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##"
             "/materials/video/b.mp4"},
        ]}})
    return goi


def _sao(goc: Path, ten: str) -> Path:
    """Ban sao cua goi lanh de di pha."""
    nguon = _tao_goi_lanh(goc / ten)
    return nguon


def main():
    tmp = Path(tempfile.mkdtemp(prefix="kiem_vf_"))
    try:
        # ---- TIEN DE: goi LANH phai xanh. Khong co phep nay thi moi phep
        # duoi vo nghia - mot verifier luon do cung "bat duoc" het.
        lanh = _sao(tmp, "lanh")
        kq = NT.nghiem_thu(lanh)
        check("TIEN DE: goi LANH -> verifier bao DAT", kq.dat(),
              f"tuyet_doi={len(kq.tuyet_doi)} khong_pg={len(kq.khong_phan_giai)}"
              f" rong={len(kq.rong)} json_hong={len(kq.json_hong)}")
        check("TIEN DE: goi LANH -> co kiem THAT SU (N > 0)",
              kq.tong_tham_chieu >= 4, f"chi kiem {kq.tong_tham_chieu}")
        check("TIEN DE: tim duoc draft root (V-3)",
              len(kq.draft_root) >= 1, len(kq.draft_root))

        # ---- HONG 1 (V-1): con duong dan TUYET DOI
        g1 = _sao(tmp, "hong1")
        d = json.loads((g1 / "draft_content.json").read_text(encoding="utf-8"))
        d["materials"]["videos"][0]["path"] = r"D:\may_cu\footage\a.mp4"
        _ghi(g1 / "draft_content.json", d)
        k1 = NT.nghiem_thu(g1)
        check("HONG V-1: duong dan tuyet doi -> verifier DO", not k1.dat())
        check("HONG V-1: bat DUNG loai (tuyet_doi)", len(k1.tuyet_doi) == 1,
              f"tuyet_doi={len(k1.tuyet_doi)}")

        # ---- HONG 1b (V-1): duong dan UNC
        g1b = _sao(tmp, "hong1b")
        d = json.loads((g1b / "draft_content.json").read_text(encoding="utf-8"))
        d["materials"]["videos"][0]["path"] = r"\\192.168.1.214\e\footage\a.mp4"
        _ghi(g1b / "draft_content.json", d)
        k1b = NT.nghiem_thu(g1b)
        check("HONG V-1: duong dan UNC -> verifier DO", not k1b.dat())
        check("HONG V-1: UNC bat dung loai", len(k1b.tuyet_doi) == 1,
              f"tuyet_doi={len(k1b.tuyet_doi)}")

        # ---- HONG 2 (V-2): tham chieu tro toi file KHONG CO
        g2 = _sao(tmp, "hong2")
        (g2 / "materials" / "video" / "a.mp4").unlink()
        k2 = NT.nghiem_thu(g2)
        check("HONG V-2: file bi thieu -> verifier DO", not k2.dat())
        check("HONG V-2: bat DUNG loai (khong_phan_giai)",
              len(k2.khong_phan_giai) == 2,
              f"khong_pg={len(k2.khong_phan_giai)}")

        # ---- HONG 3 (V-2): file co nhung RONG (0 byte)
        g3 = _sao(tmp, "hong3")
        (g3 / "materials" / "video" / "b.mp4").write_bytes(b"")
        k3 = NT.nghiem_thu(g3)
        check("HONG V-2: file 0 byte -> verifier DO", not k3.dat())
        check("HONG V-2: bat DUNG loai (rong)", len(k3.rong) == 2,
              f"rong={len(k3.rong)}")

        # ---- HONG 4 (V-4): JSON hong sau khi ghi lai
        g4 = _sao(tmp, "hong4")
        (g4 / "draft_content.json").write_text("{ khong phai json hop le",
                                               encoding="utf-8")
        k4 = NT.nghiem_thu(g4)
        check("HONG V-4: JSON khong parse duoc -> verifier DO", not k4.dat())
        check("HONG V-4: bat DUNG loai (json_hong)", len(k4.json_hong) == 1,
              f"json_hong={len(k4.json_hong)}")

        # ---- Goi RONG: khong co tham chieu nao -> KHONG duoc ket luan DAT
        rong = tmp / "rong" / "goi"
        rong.mkdir(parents=True)
        _ghi(rong / "draft_meta_info.json", {"draft_materials": []})
        kr = NT.nghiem_thu(rong)
        check("GOI RONG: kiem duoc 0 tham chieu", kr.tong_tham_chieu == 0)
        ma = NT.main(["x", str(rong)])
        check("GOI RONG: main() tra ma KHAC 0 (khong ket luan bua)", ma != 0,
              f"ma={ma}")

        # ---- File CACHE hong khong duoc tinh la loi (chong bao dong gia)
        gc = _sao(tmp, "cache")
        _ghi(gc / "mini_draft.json", {"materials": {"videos": [
            {"id": "c1", "path": r"D:\may_cu\cache\x.mp4"}]}})
        kc = NT.nghiem_thu(gc)
        check("CACHE: tham chieu hong trong mini_draft KHONG lam do",
              kc.dat(), f"tuyet_doi={len(kc.tuyet_doi)}")
        check("CACHE: van dem duoc so tham chieu da bo qua",
              kc.cache_bo_qua >= 1, kc.cache_bo_qua)

        # ---- Nhan KHONG phai duong dan thi khong duoc bat nham
        gn = _sao(tmp, "nhan")
        d = json.loads((gn / "draft_content.json").read_text(encoding="utf-8"))
        d["materials"]["videos"][0]["material_name"] = "canh dep.mp4"
        d["materials"]["videos"][0]["extra_info"] = r"D:\ghi_chu\abc.mp4"
        _ghi(gn / "draft_content.json", d)
        kn = NT.nghiem_thu(gn)
        check("NHAN: material_name/extra_info KHONG bi coi la duong dan",
              kn.dat(), f"tuyet_doi={[x[1] for x in kn.tuyet_doi]}")

        # ---- Phep thu DI CHUYEN: doi cho goi roi nghiem thu lai
        di = tmp / "di_chuyen"
        shutil.copytree(lanh, di / "cho_moi")
        kd = NT.nghiem_thu(di / "cho_moi")
        check("DI CHUYEN: chep goi sang cho khac -> VAN dat", kd.dat())
        check("DI CHUYEN: van kiem dung so tham chieu",
              kd.tong_tham_chieu == kq.tong_tham_chieu,
              f"{kd.tong_tham_chieu} vs {kq.tong_tham_chieu}")

        # ---- Verifier phai DOC LAP: khong duoc import module cua tool
        ma_nguon = (HERE / "nghiem_thu_goi.py").read_text(encoding="utf-8")
        cam = ("import goi_project_capcut", "import chung",
               "import toi_uu_dung_luong", "from chung import",
               "from goi_project_capcut import")
        lo = [c for c in cam if c in ma_nguon]
        check("DOC LAP: verifier KHONG import module nao cua tool",
              not lo, f"co import: {lo}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
