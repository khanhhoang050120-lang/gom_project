# -*- coding: utf-8 -*-
"""bug #104 - phan biet lech DO GOI voi lech VON CO trong draft goc.

Trieu chung that (DS1_124): goi co THIEU=0, COPY THAT BAI=0, 1092 clip xu ly
0 that bai, giam 94 GB - nhung ket luan lai la "CON THIEU" chi vi 3 segment
bi bao "BI LECH sau khi cat gon". Ba dong do la CUNG MOT material lap o 3 file,
va no DA LECH SAN trong draft goc (+0.100s) truoc khi goi.

Bo kiem nay chot ba dieu:
  1. Lech VON CO -> vao `lech_san`, KHONG chan ket luan
  2. Lech DO GOI gay ra -> van vao `bad`, van chan
  3. CAI BAY NGUONG: `_lech_san_o_goc` phai dung nguong THAP HON
     `verify_optimize`, khong thi ban va vo dung (lech goc dung bang 100_000us
     vua LOT qua phep kiem `> d + 100_000`)
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import toi_uu_dung_luong as TU   # noqa: E402

US = 1_000_000
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


def lam_draft(thu_muc, duration_us, start_us, dung_us, mid="M1"):
    """Tao mot draft toi gian co DUNG mot material va mot segment."""
    thu_muc.mkdir(parents=True, exist_ok=True)
    noi_dung = {
        "materials": {
            "videos": [{"id": mid, "duration": duration_us,
                        "path": "##_draftpath_placeholder_X_##/materials/a.mp4"}],
            "audios": [],
        },
        "tracks": [{"segments": [{
            "material_id": mid,
            "source_timerange": {"start": start_us, "duration": dung_us},
        }]}],
    }
    (thu_muc / "draft_content.json").write_text(
        json.dumps(noi_dung), encoding="utf-8")
    # `iter_json_files` can mot goc draft nhan ra duoc
    (thu_muc / "draft_meta_info.json").write_text(
        json.dumps({"draft_materials": []}), encoding="utf-8")
    return thu_muc


print("=" * 70)
print(" bug #104 - lech VON CO vs lech DO GOI")
print("=" * 70)

# ---------------------------------------------------- 1. lech von co
print("\n1. LECH VON CO trong draft goc -> khong duoc chan ket luan")
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    # Draft goc: 30.700s, dung 5.600 -> 30.800  => lech DUNG BANG 100_000us
    goc = lam_draft(td / "goc", 30_700_000, 5_600_000, 25_200_000)
    # Ban goi sau cat gon: duration = do dai ban _opt (25.592s),
    # doan dung giu nguyen 25.200s, offset ve 0.500 => lech 108_000us
    out = lam_draft(td / "out", 25_592_000, 500_000, 25_200_000)

    bad, san = TU.verify_optimize(out)
    check("khong truyen draft_dir -> bi coi la LOI (hanh vi cu)",
          len(bad) == 1 and len(san) == 0, f"bad={len(bad)} san={len(san)}")

    bad, san = TU.verify_optimize(out, goc)
    check("co truyen draft_dir -> chuyen sang 'lech von co'",
          len(bad) == 0 and len(san) == 1, f"bad={len(bad)} san={len(san)}")
    check("mo ta noi ro DA LECH SAN",
          san and "LECH SAN" in san[0][2], san[0][2] if san else "")

# ---------------------------------------------------- 2. lech DO GOI
print("\n2. Lech DO GOI gay ra -> VAN phai chan")
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    # Draft goc SACH: dung 0 -> 25.000 trong clip dai 30.000 => khong lech
    goc = lam_draft(td / "goc", 30_000_000, 0, 25_000_000)
    # Ban goi: doan dung vuot han ra ngoai => LOI THAT
    out = lam_draft(td / "out", 20_000_000, 0, 25_000_000)

    bad, san = TU.verify_optimize(out, goc)
    check("lech that -> vao `bad`, KHONG duoc tha",
          len(bad) == 1 and len(san) == 0, f"bad={len(bad)} san={len(san)}")
    check("mo ta KHONG noi 'da lech san'",
          bad and "LECH SAN" not in bad[0][2], bad[0][2] if bad else "")

# ---------------------------------------------------- 3. cai bay nguong
print("\n3. CAI BAY NGUONG (ban va dau tien vo dung vi cho nay)")
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    # Lech DUNG BANG 100_000us - vua LOT qua `> d + 100_000`
    goc = lam_draft(td / "goc", 30_700_000, 5_600_000, 25_200_000)
    tap = TU._lech_san_o_goc(goc)
    check("nhan ra material lech DUNG BANG nguong 100_000us",
          "M1" in tap,
          f"tim duoc {tap} - neu rong thi ban va VO DUNG")

    # Draft that su sach thi khong duoc bao nham
    sach = lam_draft(td / "sach", 30_000_000, 0, 25_000_000)
    check("draft SACH -> khong bao nham cai nao",
          len(TU._lech_san_o_goc(sach)) == 0, TU._lech_san_o_goc(sach))

# ---------------------------------------------------- 4. bien
print("\n4. Truong hop bien")
check("draft_dir = None -> tra tap rong, khong nem",
      TU._lech_san_o_goc(None) == set())
with tempfile.TemporaryDirectory() as td:
    check("thu muc khong ton tai -> khong nem",
          isinstance(TU._lech_san_o_goc(Path(td) / "khong_co"), set))

print()
print("=" * 70)
print(f"KET QUA: {pas} PASS / {fail} FAIL")
print("=" * 70)
sys.exit(1 if fail else 0)
