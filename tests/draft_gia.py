# -*- coding: utf-8 -*-
"""D1 - BO SINH DRAFT GIA de chay test ma KHONG can NAS, khong can footage that.

Dung mot draft CapCut GIA nhung theo dung CAU TRUC THAT, gom du cac cai bay ma
nhat ky bug.md da tung vap:

  - footage nam NGOAI folder draft (truong hop thuong gap nhat - bug #26)
  - media da nam SAN trong draft, tro bang placeholder  ##_draftpath_placeholder_<GUID>_##/
  - so dang ky `draft_materials` trong draft_meta_info.json, dang `./materials/...`
  - DU AN CON (subdraft): vua la thu muc that co draft_meta_info.json rieng,
    vua duoc NHUNG INLINE trong materials.drafts[].draft   (bug #11)
  - mot tham chieu "anh bia" (khong anh huong video xuat ra)  -> is_cosmetic
  - tuy chon: mot tham chieu toi file KHONG TON TAI  -> duong "THIEU"

Media that su duoc sinh bang ffmpeg (testsrc2), moi file vai chuc KB, chay vai giay.

Cach dung:
    from draft_gia import tao_draft_gia
    mo_ta = tao_draft_gia(thu_muc_lam_viec, ffmpeg, ffprobe)
    draft_dir = mo_ta["draft_dir"]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# GUID cua CapCut - hang so, giong nhau o moi project (xem bug.md checklist)
GUID = "0E685133-18CE-45ED-8CB8-2904A212EC80"
GUID_SUB = "1A2B3C4D-5E6F-4708-9A0B-1C2D3E4F5A6B"
# Tang 2 va tang 3 - do that tren DS3_094: 17 subdraft, du an con LONG TRONG
# du an con (DS3_094 -> 70B22A70 -> F9A37AFD -> D644F99A).
GUID_SUB2 = "2B3C4D5E-6F70-4819-AB1C-2D3E4F5A6B7C"
GUID_SUB3 = "3C4D5E6F-7081-492A-BC2D-3E4F5A6B7C8D"
US = 1_000_000


def _chay(cmd, timeout=180):
    # `encoding="utf-8"` BAT BUOC - xem chu thich o `_run()` trong
    # toi_uu_dung_luong.py. Thieu no thi chinh bo kiem se hong tren may con co
    # bang ma ANSI khac 65001, tuc la bo kiem mu dung cho no can soi nhat.
    return subprocess.run(cmd, capture_output=True, timeout=timeout,
                          encoding="utf-8", errors="replace",
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def _lp(p):
    """Ban rut gon cua _lp() - test cung phai qua long-path, khong duoc mien tru."""
    if os.name != "nt":
        return str(p)
    s = str(p)
    if s.startswith("\\\\?\\") or s.startswith("\\\\.\\"):
        return s
    ap = os.path.abspath(s)
    if ap.startswith("\\\\?\\") or ap.startswith("\\\\.\\"):
        return ap
    if ap.startswith("\\\\"):
        return "\\\\?\\UNC\\" + ap[2:]
    return "\\\\?\\" + ap


def tao_video(ffmpeg, path, giay, w=640, h=480):
    """Sinh mot video THAT dai `giay` giay. Tra duong dan."""
    Path(_lp(Path(path).parent)).mkdir(parents=True, exist_ok=True)
    r = _chay([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
               "-f", "lavfi", "-i", f"testsrc2=size={w}x{h}:rate=24:duration={giay}",
               "-f", "lavfi", "-i", f"sine=frequency=330:duration={giay}",
               "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "64k",
               "-shortest", _lp(path)])
    if r.returncode != 0 or not Path(_lp(path)).is_file():
        raise RuntimeError(f"khong sinh duoc video {path}: {r.stderr[-300:]}")
    return Path(path)


def tao_audio(ffmpeg, path, giay):
    """Sinh mot file am thanh THAT."""
    Path(_lp(Path(path).parent)).mkdir(parents=True, exist_ok=True)
    r = _chay([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
               "-f", "lavfi", "-i", f"sine=frequency=440:duration={giay}",
               "-c:a", "aac", "-b:a", "64k", _lp(path)])
    if r.returncode != 0 or not Path(_lp(path)).is_file():
        raise RuntimeError(f"khong sinh duoc audio {path}: {r.stderr[-300:]}")
    return Path(path)


def tao_anh(ffmpeg, path):
    """Sinh mot anh bia (thieu no thi KHONG mat hinh video)."""
    Path(_lp(Path(path).parent)).mkdir(parents=True, exist_ok=True)
    r = _chay([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
               "-f", "lavfi", "-i", "color=c=blue:size=160x90:duration=1",
               "-frames:v", "1", _lp(path)])
    if r.returncode != 0:
        raise RuntimeError(f"khong sinh duoc anh {path}: {r.stderr[-300:]}")
    return Path(path)


def _do_dai(ffprobe, path):
    r = _chay([ffprobe, "-v", "error", "-print_format", "json",
               "-show_format", _lp(path)])
    if r.returncode != 0:
        raise RuntimeError(f"ffprobe loi tren {path}: {r.stderr[-200:]}")
    d = json.loads(r.stdout or "{}")
    return int(float((d.get("format") or {}).get("duration") or 0) * US)


def _ghi_json(path, obj):
    Path(_lp(Path(path).parent)).mkdir(parents=True, exist_ok=True)
    Path(_lp(path)).write_text(json.dumps(obj, ensure_ascii=False, indent=1),
                               encoding="utf-8")


def tao_draft_gia(goc, ffmpeg, ffprobe, *, co_subdraft=True, co_file_thieu=False,
                  co_anh_bia=True, nhieu_doan=False, dung_chung_footage=False,
                  co_reverse=False):
    """Dung mot draft CapCut gia day du. Tra dict mo ta de test doi chieu.

    goc            : thu muc lam viec (se tao FOOTAGE/ va DRAFT/ ben trong)
    co_subdraft    : co du an con long nhau hay khong
    co_file_thieu  : them mot tham chieu toi file KHONG ton tai (test duong "THIEU")
    co_anh_bia     : them tham chieu anh bia (test phan loai "khong anh huong")
    """
    goc = Path(goc)
    footage = goc / "FOOTAGE"          # NGOAI draft - dung nhu thuc te
    draft = goc / "DRAFT"
    (draft / "materials" / "video").mkdir(parents=True, exist_ok=True)

    # --- Media that ---
    canh1 = tao_video(ffmpeg, footage / "canh1.mp4", 10)      # dung 1 doan giua
    canh2 = tao_video(ffmpeg, footage / "canh2.mp4", 6)       # dung ca clip
    nhac = tao_audio(ffmpeg, footage / "nhac.m4a", 4)
    co_san = tao_video(ffmpeg, draft / "materials" / "video" / "co_san.mp4", 3)

    # Ban RENDER NGUOC (reverse_path): CapCut sinh ra khi ap hieu ung tua nguoc.
    # Co y de NGOAI draft va lam DAI hon ban xuoi de thay ro no co duoc nen khong.
    rev_file = (tao_video(ffmpeg, footage / "canh2_reverse.mp4", 8)
                if co_reverse else None)

    d1, d2, d3, d4 = (_do_dai(ffprobe, p) for p in (canh1, canh2, nhac, co_san))

    ph = f"##_draftpath_placeholder_{GUID}_##"

    # --- Du an con: thu muc THAT + blob NHUNG INLINE (bug #11) ---
    sub_dir = draft / "subdraft" / GUID_SUB
    sub_blob = None
    sub_media = None
    sub_ngoai = None
    if co_subdraft:
        # (a) Thu muc subdraft THAT: no co draft_meta_info.json rieng nen CHINH NO
        #     la mot draft root -> placeholder ben trong giai theo GOC CUA NO.
        sub_media = tao_video(ffmpeg, sub_dir / "materials" / "video" / "trong_sub.mp4", 5)
        d5 = _do_dai(ffprobe, sub_media)
        _vid_sub = [
            {"id": "sm1", "duration": d5, "width": 640, "height": 480,
             "path": f"##_draftpath_placeholder_{GUID}_##/materials/video/trong_sub.mp4",
             "material_name": "trong_sub.mp4"}]
        _seg_sub = [{"material_id": "sm1", "clip": {"scale": {"x": 1.0}},
                     "source_timerange": {"start": 0, "duration": d5}}]
        if dung_chung_footage:
            # CUNG mot file nguon duoc dung o CA draft cha LAN du an con -> khi gom,
            # no phai di toi HAI thu muc materials/ khac nhau. Do la truong hop DUY
            # NHAT kich hoat duong LIEN KET CUNG (os.link) - can de kiem bug #17.
            _vid_sub.append({"id": "sm_chung", "duration": d1, "width": 640,
                             "height": 480, "path": str(canh1),
                             "material_name": "canh1.mp4"})
            _seg_sub.append({"material_id": "sm_chung", "clip": {"scale": {"x": 1.0}},
                             "source_timerange": {"start": 0, "duration": d1}})
        _ghi_json(sub_dir / "draft_content.json", {
            "canvas_config": {"width": 1920, "height": 1080},
            "materials": {"videos": _vid_sub, "audios": []},
            "tracks": [{"segments": _seg_sub}],
        })
        _ghi_json(sub_dir / "draft_meta_info.json", {"draft_materials": [
            {"type": 0, "value": [
                {"id": "sr1", "file_Path": "./materials/video/trong_sub.mp4",
                 "metetype": "video"},
            ]},
        ]})

        # (a2) TANG 2 va TANG 3: du an con LONG TRONG du an con, roi clip ghep
        #      long trong do nua. Do that tren DS3_094: 17 subdraft, du 3 tang
        #      (DS3_094 -> 70B22A70 -> F9A37AFD -> D644F99A).
        #      Truoc khi them, draft gia chi co MOT tang -> ca 23 bo kiem chua
        #      bao gio cham toi tang 2/3, trong khi CA SAU project that deu co.
        sub2 = sub_dir / "subdraft" / GUID_SUB2
        media2 = tao_video(ffmpeg, sub2 / "materials" / "video" / "tang2.mp4", 4)
        dd2 = _do_dai(ffprobe, media2)
        # PHAI co it nhat MOT duong dan TUYET DOI o tang sau, tro toi footage NGOAI
        # draft. Neu moi tham chieu deu la placeholder thi khong co gi de viet lai,
        # va phep kiem "khong con duong dan tuyet doi" se xanh mot cach VO NGHIA -
        # da mac dung bay do mot lan: gai loi cho iter_json_files bo qua subdraft
        # long ma bo kiem VAN XANH, vi chang co gi de phat hien.
        ngoai2 = tao_video(ffmpeg, footage / "tang2_ngoai.mp4", 4)
        dd2n = _do_dai(ffprobe, ngoai2)
        _ghi_json(sub2 / "draft_content.json", {
            "canvas_config": {"width": 1920, "height": 1080},
            "materials": {"videos": [
                {"id": "s2m1", "duration": dd2, "width": 640, "height": 480,
                 "path": f"##_draftpath_placeholder_{GUID}_##/materials/video/tang2.mp4",
                 "material_name": "tang2.mp4"},
                {"id": "s2m2", "duration": dd2n, "width": 640, "height": 480,
                 "path": str(ngoai2),          # TUYET DOI - phai duoc viet lai
                 "material_name": "tang2_ngoai.mp4"}], "audios": []},
            "tracks": [{"segments": [
                {"material_id": "s2m1", "clip": {"scale": {"x": 1.0}},
                 "source_timerange": {"start": 0, "duration": dd2}},
                {"material_id": "s2m2", "clip": {"scale": {"x": 1.0}},
                 "source_timerange": {"start": 0, "duration": dd2n}}]}],
        })
        _ghi_json(sub2 / "draft_meta_info.json", {"draft_materials": [
            {"type": 0, "value": [
                {"id": "sr2", "file_Path": "./materials/video/tang2.mp4",
                 "metetype": "video"}]}]})

        # TANG 3: clip ghep (co sub_draft_config.json, KHONG co draft_meta_info)
        sub3 = sub2 / "subdraft" / GUID_SUB3
        media3 = tao_video(ffmpeg, sub3 / "materials" / "video" / "tang3.mp4", 3)
        dd3 = _do_dai(ffprobe, media3)
        ngoai3 = tao_video(ffmpeg, footage / "tang3_ngoai.mp4", 3)
        dd3n = _do_dai(ffprobe, ngoai3)
        _ghi_json(sub3 / "draft_content.json", {
            "canvas_config": {"width": 1920, "height": 1080},
            "materials": {"videos": [
                {"id": "s3m1", "duration": dd3, "width": 640, "height": 480,
                 "path": f"##_draftpath_placeholder_{GUID}_##/materials/video/tang3.mp4",
                 "material_name": "tang3.mp4"},
                # TUYET DOI o tang SAU NHAT - day moi la thu bo kiem can quan sat
                {"id": "s3m2", "duration": dd3n, "width": 640, "height": 480,
                 "path": str(ngoai3),
                 "material_name": "tang3_ngoai.mp4"}], "audios": []},
            "tracks": [{"segments": [
                {"material_id": "s3m1", "clip": {"scale": {"x": 1.0}},
                 "source_timerange": {"start": 0, "duration": dd3}},
                {"material_id": "s3m2", "clip": {"scale": {"x": 1.0}},
                 "source_timerange": {"start": 0, "duration": dd3n}}]}],
        })
        _ghi_json(sub3 / "sub_draft_config.json", {"type": "combination"})

        # (b) Blob NHUNG INLINE trong draft_content.json cua draft CHA (bug #11).
        #     Blob nay nam TRONG file cua draft cha, nen placeholder o day se giai
        #     theo goc CUA CHA - khong tro duoc vao subdraft/. Vi vay du an con nhap
        #     tu ngoai dung PATH TUYET DOI toi footage goc cua no, dung nhu thuc te.
        sub_ngoai = tao_video(ffmpeg, footage / "canh_du_an_con.mp4", 5)
        d6 = _do_dai(ffprobe, sub_ngoai)
        sub_blob = {
            "canvas_config": {"width": 1920, "height": 1080},
            "materials": {
                "videos": [{"id": "sm2", "duration": d6, "width": 640, "height": 480,
                            "path": str(sub_ngoai),
                            "material_name": "canh_du_an_con.mp4"}],
                "audios": [],
            },
            "tracks": [{"segments": [
                {"material_id": "sm2", "clip": {"scale": {"x": 1.0}},
                 "source_timerange": {"start": 0, "duration": d6}},
            ]}],
        }

    # --- Noi dung draft cha ---
    videos = [
        # (1) footage NGOAI draft, path TUYET DOI, chi dung doan 2s -> 5s
        {"id": "m1", "path": str(canh1), "duration": d1, "width": 640, "height": 480,
         "material_name": "canh1.mp4"},
        # (2) footage NGOAI draft, dung CA clip
        {"id": "m2", "path": str(canh2), "duration": d2, "width": 640, "height": 480,
         "material_name": "canh2.mp4"},
        # (3) da nam SAN trong draft, tro bang PLACEHOLDER
        {"id": "m3", "path": f"{ph}/materials/video/co_san.mp4", "duration": d4,
         "width": 640, "height": 480, "material_name": "co_san.mp4"},
    ]
    if nhieu_doan:
        # BUG #38: CUNG mot file nguon duoc dung o NHIEU material voi cac doan cat
        # khac nhau -> sinh NHIEU ban `_opt`. Day dung la tinh huong ma bang tra
        # "1 nguon -> 1 dich" bi hong.
        videos.append({"id": "m1b", "path": str(canh1), "duration": d1,
                       "width": 640, "height": 480, "material_name": "canh1.mp4"})
        videos.append({"id": "m1c", "path": str(canh1), "duration": d1,
                       "width": 640, "height": 480, "material_name": "canh1.mp4"})
    if co_reverse:
        # CapCut sinh file nay khi ap hieu ung TUA NGUOC. No chi duoc tro toi qua
        # khoa `reverse_path`, KHONG BAO GIO qua `path` - nen moi vong lap chi doc
        # `path` deu mu truoc no. Do that: 21 project tren may co 34 file nhu vay,
        # tong 147 GB, deu duoc gom nguyen ban khong nen (xem bug.md).
        videos.append({"id": "mrev", "path": str(canh2), "duration": d2,
                       "width": 640, "height": 480,
                       "material_name": "canh2.mp4",
                       "reverse_path": str(rev_file)})
    if co_file_thieu:
        videos.append({"id": "m9", "path": str(footage / "khong_he_ton_tai.mp4"),
                       "duration": 5 * US, "width": 640, "height": 480,
                       "material_name": "khong_he_ton_tai.mp4"})

    audios = [{"id": "a1", "path": str(nhac), "duration": d3,
               "material_name": "nhac.m4a"}]

    segments = [
        # CAT GON duoc: clip 10s nhung chi dung 2s -> 5s
        {"material_id": "m1", "clip": {"scale": {"x": 1.0}},
         "source_timerange": {"start": 2 * US, "duration": 3 * US}},
        {"material_id": "m2", "clip": {"scale": {"x": 1.0}},
         "source_timerange": {"start": 0, "duration": d2}},
        {"material_id": "m3", "clip": {"scale": {"x": 1.0}},
         "source_timerange": {"start": 0, "duration": d4}},
        {"material_id": "a1", "source_timerange": {"start": 0, "duration": d3}},
    ]
    if nhieu_doan:
        segments.append({"material_id": "m1b", "clip": {"scale": {"x": 1.0}},
                         "source_timerange": {"start": int(6.0 * US),
                                              "duration": int(2.0 * US)}})
        segments.append({"material_id": "m1c", "clip": {"scale": {"x": 1.0}},
                         "source_timerange": {"start": int(0.2 * US),
                                              "duration": int(1.0 * US)}})
    if co_file_thieu:
        segments.append({"material_id": "m9", "clip": {"scale": {"x": 1.0}},
                         "source_timerange": {"start": 0, "duration": 5 * US}})

    content = {
        "canvas_config": {"width": 1920, "height": 1080},
        "materials": {"videos": videos, "audios": audios,
                      "drafts": ([{"draft": sub_blob}] if sub_blob else [])},
        "tracks": [{"segments": segments}],
    }
    if co_anh_bia:
        # Khoa co chu "cover" -> is_cosmetic() phai xep loai KHONG anh huong
        bia = tao_anh(ffmpeg, footage / "draft_cover.jpg")
        content["cover_path"] = str(bia)

    # CapCut co the co ca hai file; tool doc file nao ton tai truoc
    _ghi_json(draft / "draft_content.json", content)
    _ghi_json(draft / "draft_info.json", content)

    # --- So dang ky cua draft cha ---
    dk = [
        {"id": "r1", "file_Path": str(canh1), "metetype": "video"},
        {"id": "r2", "file_Path": str(canh2), "metetype": "video"},
        {"id": "r3", "file_Path": "./materials/video/co_san.mp4", "metetype": "video"},
        {"id": "r4", "file_Path": str(nhac), "metetype": "music"},
    ]
    if co_file_thieu:
        # Muc CHET trong so dang ky: tro toi file khong he ton tai.
        # CHI them khi test yeu cau - draft "binh thuong" phai sach hoan toan,
        # neu khong moi phep kiem "khong con tham chieu ra ngoai" deu do oan.
        dk.append({"id": "r9", "file_Path": str(footage / "kho_khong_dung.mp4"),
                   "metetype": "video"})
    _ghi_json(draft / "draft_meta_info.json", {"draft_materials": [{"type": 0, "value": dk}]})

    return {
        "goc": goc,
        "draft_dir": draft,
        "footage_dir": footage,
        "sub_dir": sub_dir if co_subdraft else None,
        "guid": GUID,
        "media_ngoai": [canh1, canh2, nhac] + ([sub_ngoai] if sub_ngoai else []),
        "media_trong": [co_san] + ([sub_media] if sub_media else []),
        "do_dai": {"canh1": d1, "canh2": d2, "nhac": d3, "co_san": d4},
        # so media THAT SU anh huong video xuat ra (khong tinh anh bia)
        "so_media_can_gom": 3 + (1 if co_subdraft else 0) + 1,
        "co_file_thieu": co_file_thieu,
    }


if __name__ == "__main__":
    import shutil
    import tempfile
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import toi_uu_dung_luong as TU

    ffmpeg, ffprobe = TU.ff_paths(Path(__file__).resolve().parent.parent)
    if not ffmpeg:
        print("KHONG tim thay ffmpeg -> khong chay duoc")
        sys.exit(2)
    tmp = Path(tempfile.mkdtemp(prefix="draft_gia_"))
    try:
        mo_ta = tao_draft_gia(tmp, ffmpeg, ffprobe, co_file_thieu=True)
        print("Da dung draft gia tai:", mo_ta["draft_dir"])
        for p in sorted(Path(tmp).rglob("*")):
            if p.is_file():
                print(f"   {p.relative_to(tmp)}  ({p.stat().st_size} byte)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
