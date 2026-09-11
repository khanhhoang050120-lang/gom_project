# -*- coding: utf-8 -*-
r"""Nghiem thu mot GOI da xuat - viet DOC LAP, khong import gi cua tool.

    python tests\nghiem_thu_goi.py <thu_muc_goi>

Vi sao phai DOC LAP:
  Moi bo kiem E2E hien co deu hoi "tool bao dung so file chua?" - tuc la de
  TOOL TU CHAM BAI MINH. Neu tool hieu sai dinh dang CapCut, no se ghi sai
  theo dung cai hieu sai do, roi tu kiem lai bang chinh ham da hieu sai, va
  bao DAT. Checklist trong bug.md noi thang: "Verifier nghiem thu nen viet
  DOC LAP, khong import ham cua tool - dung lai chinh ham bi loi thi loi
  khong bao gio lo".

  File nay hoi mot cau KHAC HAN: "mot chuong trinh khac, khong biet gi ve
  tool, co mo duoc goi nay khong?"

Bon tieu chi (dung thu CapCut quan tam):
  V-1  KHONG con duong dan TUYET DOI trong bat ky .json nao cua goi.
       Duong tuyet doi = tro ve may cu = clip mat khi sang may khac. Day la
       LY DO TON TAI cua ca cong cu.
  V-2  100% tham chieu phan giai duoc toi file CO THAT, kich thuoc > 0.
       Khong thi CapCut hien clip trang.
  V-3  De quy du MOI CAP subdraft.
  V-4  Moi .json parse duoc sau khi tool ghi lai (khong hong encoding/BOM).

Khong dung thu vien ngoai. Khong import `goi_project_capcut`, `chung`,
`toi_uu_dung_luong` - CO Y.

GIOI HAN da biet, noi that thay vi giau:
  File nay kiem duoc "goi co TU CHUA khong" - no KHONG kiem duoc ngu nghia
  rieng cua CapCut (vi du CapCut doi mot khoa metadata ma tool vo tinh xoa,
  hay tu choi mot codec ma ffprobe chap nhan). Chi nguoi that mo bang CapCut
  that moi bat duoc nhung thu do. Xem muc "phep thu vang" trong ke hoach.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Duoi media coi la "tham chieu can kiem". Danh sach nay lay tu quan sat
# draft that, KHONG lay tu hang so cua tool (doc lap).
DUOI_MEDIA = {
    ".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm", ".m4v",
    ".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg",
    ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff",
}

# Khoa CHAC CHAN chua duong dan. Mot chuoi ket thuc bang ".mp4" CHUA CHAC la
# duong dan - `material_name`, `materialName`, `extra_info` chi la nhan
# (checklist bug.md, bug #24). Loc theo TEN KHOA la cach dung.
KHOA_DUONG_DAN = {
    "path", "file_Path", "source_path", "reverse_path",
    "intensifies_path", "audio_path", "video_path", "cover_path",
    "matting_path", "material_path",
}

# Tham chieu trong nhung file nay hong cung khong anh huong video xuat ra -
# chung la cache do CapCut tu sinh. Do tren project that: 2325/2366 tham
# chieu hong deu thuoc nhom nay.
FILE_CACHE = ("mini_draft", "draft_agency_", "template-", "attachment_")


def _lp(p: str) -> str:
    """Ban DOC LAP cua long-path prefix - CO Y khong import `chung._lp`.

    Neu tool va verifier dung chung mot ham thi mot loi trong ham do se lam
    ca hai cung mu. Ban nay viet lai tu dau theo dung tai lieu Windows.
    """
    if os.name != "nt":
        return p
    s = str(p)
    if s.startswith("\\\\?\\") or s.startswith("\\\\.\\"):
        return s
    ap = os.path.abspath(s)
    if ap.startswith("\\\\"):
        return "\\\\?\\UNC\\" + ap[2:]
    return "\\\\?\\" + ap


def _co_ve_duong_dan(s: str) -> bool:
    if not isinstance(s, str) or not s:
        return False
    return Path(s.replace("\\", "/")).suffix.lower() in DUOI_MEDIA


def _tuyet_doi(s: str) -> bool:
    """Duong dan TUYET DOI kieu Windows hoac UNC.

    `##_draftpath_placeholder_..._##/x.mp4` KHONG phai tuyet doi - do la
    placeholder, CapCut tu giai theo draft root.
    """
    t = s.strip()
    if t.startswith("##"):
        return False
    if t.startswith("\\\\") or t.startswith("//"):
        return True
    return len(t) >= 2 and t[1] == ":" and t[0].isalpha()


def _la_draft_root(d: Path) -> bool:
    return (d / "draft_meta_info.json").is_file() or \
           (d / "sub_draft_config.json").is_file()


def _goc_gan_nhat(f: Path, goi: Path) -> Path:
    """Draft root GAN NHAT tinh nguoc len tu file chua tham chieu.

    Quy tac nay da duoc do tren 8650 duong dan that cua 5 draft: giai theo
    root gan nhat dung 99,9%, con giai theo thu muc chua file chi 85,1%.
    """
    d = f.parent
    while True:
        if _la_draft_root(d):
            return d
        if d == goi or d.parent == d:
            return goi
        d = d.parent


def _duyet(o, khoa_cha=None):
    """Sinh (khoa, chuoi) cho moi chuoi nam duoi mot KHOA duong dan."""
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, str):
                if k in KHOA_DUONG_DAN and _co_ve_duong_dan(v):
                    yield k, v
            else:
                yield from _duyet(v, k)
    elif isinstance(o, (list, tuple)):
        for v in o:
            if isinstance(v, str):
                if khoa_cha in KHOA_DUONG_DAN and _co_ve_duong_dan(v):
                    yield khoa_cha, v
            else:
                yield from _duyet(v, khoa_cha)


class KetQua:
    def __init__(self):
        self.so_json = 0
        self.json_hong = []          # (file, loi)          -> V-4
        self.tuyet_doi = []          # (file, khoa, gt)     -> V-1
        self.khong_phan_giai = []    # (file, khoa, gt)     -> V-2
        self.rong = []               # (file, khoa, gt)     -> V-2
        self.ok = 0
        self.cache_bo_qua = 0
        self.draft_root = []         # -> V-3

    @property
    def tong_tham_chieu(self):
        return (self.ok + len(self.tuyet_doi) + len(self.khong_phan_giai)
                + len(self.rong))

    def dat(self):
        return not (self.json_hong or self.tuyet_doi
                    or self.khong_phan_giai or self.rong)


def nghiem_thu(goi: Path) -> KetQua:
    kq = KetQua()
    goi = Path(goi)

    for thu, _dirs, teps in os.walk(_lp(str(goi))):
        thu_p = Path(thu.replace("\\\\?\\UNC\\", "\\\\").replace("\\\\?\\", ""))
        if _la_draft_root(thu_p):
            kq.draft_root.append(thu_p)
        for t in teps:
            if not t.lower().endswith(".json"):
                continue
            f = thu_p / t
            kq.so_json += 1
            la_cache = any(x in t for x in FILE_CACHE)

            try:
                with open(_lp(str(f)), "r", encoding="utf-8") as fh:
                    du_lieu = json.load(fh)
            except Exception as ex:                       # V-4
                if not la_cache:
                    kq.json_hong.append((f, f"{type(ex).__name__}: {ex}"))
                continue

            goc = _goc_gan_nhat(f, goi)
            for khoa, gt in _duyet(du_lieu):
                if la_cache:
                    kq.cache_bo_qua += 1
                    continue

                if _tuyet_doi(gt):                        # V-1
                    kq.tuyet_doi.append((f, khoa, gt))
                    continue

                # Giai placeholder va duong tuong doi theo draft root gan nhat
                s = gt.strip()
                if s.startswith("##"):
                    phan = s.split("_##", 1)
                    s = phan[1] if len(phan) == 2 else s
                s = s.lstrip("/\\")
                if s.startswith("./"):
                    s = s[2:]
                dich = goc / s.replace("/", os.sep)

                try:
                    if not os.path.isfile(_lp(str(dich))):
                        kq.khong_phan_giai.append((f, khoa, gt))
                    elif os.path.getsize(_lp(str(dich))) == 0:
                        kq.rong.append((f, khoa, gt))
                    else:
                        kq.ok += 1
                except OSError as ex:
                    kq.khong_phan_giai.append((f, khoa, f"{gt}  [{ex}]"))
    return kq


def in_bao_cao(kq: KetQua, goi: Path) -> None:
    print("=" * 72)
    print(f" NGHIEM THU GOI: {goi}")
    print("=" * 72)
    print(f"  File .json quet duoc      : {kq.so_json}")
    print(f"  Draft root tim thay       : {len(kq.draft_root)}   (V-3)")
    print(f"  Tham chieu media kiem     : {kq.tong_tham_chieu}")
    print(f"  Bo qua (file cache CapCut): {kq.cache_bo_qua}")
    print()
    print(f"  V-1  duong dan TUYET DOI con sot : {len(kq.tuyet_doi)}")
    print(f"  V-2  khong phan giai duoc        : {len(kq.khong_phan_giai)}")
    print(f"  V-2  file rong (0 byte)          : {len(kq.rong)}")
    print(f"  V-4  .json khong parse duoc      : {len(kq.json_hong)}")

    for nhan, ds in (("V-1 TUYET DOI", kq.tuyet_doi),
                     ("V-2 KHONG PHAN GIAI", kq.khong_phan_giai),
                     ("V-2 RONG", kq.rong)):
        if ds:
            print(f"\n  --- {nhan} ({len(ds)}) ---")
            for f, khoa, gt in ds[:15]:
                print(f"    {f.name} :: {khoa}")
                print(f"       {gt[:100]}")
            if len(ds) > 15:
                print(f"    ... va {len(ds) - 15} cho nua")
    if kq.json_hong:
        print(f"\n  --- V-4 JSON HONG ({len(kq.json_hong)}) ---")
        for f, loi in kq.json_hong[:15]:
            print(f"    {f.name}: {loi}")

    print()
    if kq.dat():
        print("  => GOI TU CHUA. Moi tham chieu deu phan giai duoc"
              " bang duong dan tuong doi.")
    else:
        print("  => GOI CHUA TU CHUA - xem cac muc o tren.")


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    goi = Path(argv[1])
    if not goi.is_dir():
        print(f"KHONG thay thu muc: {goi}")
        return 2
    kq = nghiem_thu(goi)
    in_bao_cao(kq, goi)

    # Quet 0 tham chieu -> KHONG duoc tra 0 (checklist bug.md #36).
    if kq.tong_tham_chieu == 0:
        return 1
    return 0 if kq.dat() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
