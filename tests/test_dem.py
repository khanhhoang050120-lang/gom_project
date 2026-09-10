# -*- coding: utf-8 -*-
"""Giai doan 2 - BAO CAO TRUNG THUC: bo dem phai khop viec THAT SU da lam.

  - `st["added"]` phai bang TONG KICH THUOC THAT cua cac file `_opt` tren dia,
    khong duoc nhan doi vi job `dup`.
  - `st["ok"]` phai bang so lan ffmpeg THAT SU chay.
  - Material bi loai khoi viec ma lai phai co mat trong `st["bo_qua"]` kem ly do.

Goc cua viec dem trung: `main()` luon ghi CA `draft_content.json` LAN
`draft_info.json` voi cung noi dung, ma ca hai deu nam trong CONTENT_NAMES ->
moi material sinh them mot job `dup`.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from draft_gia import tao_draft_gia, GUID      # noqa: E402

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


def kich_thuoc_opt(out):
    """Tong kich thuoc THAT cua moi file *_opt*.mp4 tren dia."""
    tong, so = 0, 0
    for dp, _d, fs in os.walk(out):
        for f in fs:
            if "_opt" in f.lower() and f.lower().endswith(".mp4"):
                tong += os.path.getsize(Path(dp) / f)
                so += 1
    return tong, so


def main():
    global pas, fail
    import toi_uu_dung_luong as TU

    ffmpeg, ffprobe = TU.ff_paths(HERE.parent)
    if not ffmpeg:
        print("KHONG tim thay ffmpeg -> bo qua")
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="dem_"))
    try:
        print("=" * 72)
        print("Bo dem sau khi ma lai - khong duoc nhan doi vi job `dup`")
        print("=" * 72)
        mo_ta = tao_draft_gia(tmp, ffmpeg, ffprobe, co_subdraft=False)
        draft = mo_ta["draft_dir"]
        out = tmp / "GOI"
        shutil.copytree(draft, out)

        # Dem so lan ffmpeg THAT SU chay
        so_lan_ma = [0]
        encode_that = TU.encode_job

        def dem_ma(*a, **k):
            so_lan_ma[0] += 1
            return encode_that(*a, **k)

        TU.encode_job = dem_ma
        try:
            opts = {"trim": True, "scale": False, "recompress": True, "cleanup": False,
                    "crf": 32, "preset": "ultrafast", "workers": 1,
                    "trim_min_save": 1024}      # nguong thap de fixture nho van cat
            st = TU.optimize_package(out, draft, {}, GUID, opts, ffmpeg, ffprobe,
                                     log=lambda *a: None)
        finally:
            TU.encode_job = encode_that

        tong_that, so_file = kich_thuoc_opt(out)
        print(f"  ffmpeg chay      : {so_lan_ma[0]} lan")
        print(f"  file _opt tren dia: {so_file} file, tong {tong_that} byte")
        print(f"  st['added']      : {st['added']} byte")
        print(f"  st['ok']         : {st['ok']}")
        print(f"  st['reused']     : {st.get('reused')}")
        print()

        check("st['added'] khop kich thuoc THAT tren dia",
              st["added"] == tong_that,
              f"lech {st['added'] - tong_that} byte"
              f" (ty le {st['added'] / tong_that:.2f}x)" if tong_that else "")
        check("st['added'] KHONG bi nhan doi",
              tong_that == 0 or st["added"] < tong_that * 1.5,
              f"added={st['added']} vs that={tong_that}")
        check("st['ok'] khong vuot so lan ffmpeg chay",
              st["ok"] <= so_lan_ma[0],
              f"ok={st['ok']} nhung ffmpeg chi chay {so_lan_ma[0]} lan")
        check("khong bo dem nao am", all(
            st[k] >= 0 for k in ("added", "ok", "trim", "scale", "recompress")))

        print()
        print("=" * 72)
        print("Material bi loai khoi viec ma lai phai co ly do trong bao cao")
        print("=" * 72)
        check("st co khoa 'bo_qua'", "bo_qua" in st, f"cac khoa: {sorted(st)}")
        if "bo_qua" in st:
            check("bo_qua la danh sach (nguon, ly_do)",
                  all(isinstance(x, tuple) and len(x) == 2 for x in st["bo_qua"]),
                  f"bo_qua = {st['bo_qua'][:3]}")

        # Doan dai hon MAX_SPAN_US phai bi loai VA duoc ghi ly do
        print()
        print("=" * 72)
        print("Clip dai hon nguong -> phai vao 'bo_qua' kem ly do, khong im lang")
        print("=" * 72)
        nguong_cu = TU.MAX_SPAN_US
        TU.MAX_SPAN_US = 1_000_000          # ha xuong 1 giay -> moi clip deu "qua dai"
        try:
            out2 = tmp / "GOI2"
            shutil.copytree(draft, out2)
            st2 = TU.optimize_package(out2, draft, {}, GUID, opts, ffmpeg, ffprobe,
                                      log=lambda *a: None)
        finally:
            TU.MAX_SPAN_US = nguong_cu
        ly_do = [b for _a, b in st2.get("bo_qua", [])]
        check("co material bi loai vi qua dai", any("qua dai" in b or "vuot muc" in b
                                                    for b in ly_do),
              f"cac ly do: {ly_do[:5]}")
        check("khong ma lai clip nao khi moi clip deu vuot nguong",
              st2["ok"] == 0, f"ok = {st2['ok']}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
