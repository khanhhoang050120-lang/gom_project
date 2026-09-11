# -*- coding: utf-8 -*-
"""Ban RENDER NGUOC (`reverse_path`) phai duoc NEN, khong duoc gom nguyen ban.

CapCut sinh file nay khi ap hieu ung tua nguoc. No CHI duoc tro toi qua khoa
`materials.videos[].reverse_path`, KHONG BAO GIO qua `path` - nen moi vong lap
chi doc `path` deu mu truoc no.

Do that tren may nay: 21 project co reverse_path, 34 file, tong 147 GB. Rieng
DS3_007 co mot ban 9,45 GB, chiem gan nua goi 22 GB.

Hai dieu PHAI dung, va deu de sai:
  1. Ket qua ma lai ghi vao `reverse_path`, KHONG duoc ghi de `path`
     (ghi nham -> clip xuoi tro vao ban NGUOC, hinh chay nguoc)
  2. `duration`/`width`/`height` cua material KHONG duoc dong toi
     (chung mo ta ban XUOI; ban nguoc chi la file dan xuat di kem)
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import toi_uu_dung_luong as TU   # noqa: E402

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


def main():
    ffmpeg, ffprobe = TU.ff_paths(ROOT)
    if not ffmpeg:
        print("BO QUA: khong tim thay ffmpeg/ffprobe - bo kiem nay can ma hoa media that")
        return 2

    from draft_gia import tao_draft_gia
    import chay_tool

    tmp = Path(tempfile.mkdtemp(prefix="reverse_"))
    try:
        print("=" * 72)
        print("Ban render nguoc phai duoc dua vao ma lai")
        print("=" * 72)
        mo_ta = tao_draft_gia(tmp, ffmpeg, ffprobe, co_reverse=True)
        draft = Path(mo_ta["draft_dir"])
        out = tmp / "GOI"

        # --- Kiem o tang collect_jobs: co sinh job cho reverse_path khong ---
        jf = draft / "draft_content.json"
        content = json.loads(jf.read_text(encoding="utf-8"))
        opts = {"trim": True, "scale": True, "cleanup": True, "recompress": True,
                "crf": 28, "preset": "ultrafast", "workers": 2}
        jobs, bo_qua = TU.collect_jobs(content, jf, draft, draft, out, {}, opts, set())
        rev_jobs = [j for j in jobs if j.get("khoa_ghi") == "reverse_path"]
        print(f"  tong {len(jobs)} job | {len(rev_jobs)} job cho ban nguoc")
        check("co sinh job cho reverse_path", len(rev_jobs) == 1,
              f"{len(rev_jobs)} job - truoc khi sua la 0 (vong lap chi doc `path`)")
        if rev_jobs:
            j = rev_jobs[0]
            check("job nguoc tro dung file nguon",
                  "canh2_reverse" in Path(j["src"]).name, f"src = {j['src']}")
            check("job nguoc KHONG cat gon", not j["trim"])
            check("job nguoc KHONG ha phan giai", not j["scale"],
                  "khong biet doan nao duoc dung tren ban nguoc -> chi duoc nen")
            check("job nguoc CO nen bitrate", j["recompress"])

        # --- KHONG duoc gay tac dung phu ---
        # Ban va chi duoc dong toi project CO reverse_path, va chi khi bat
        # `recompress`. Neu sai, no se lam hong 21 project khac tren may nay.
        print()
        print("=" * 72)
        print("Khong gay tac dung phu cho project KHONG co reverse_path")
        print("=" * 72)
        mo_ta0 = tao_draft_gia(tmp / "khong_rev", ffmpeg, ffprobe, co_reverse=False)
        d0 = Path(mo_ta0["draft_dir"])
        jf0 = d0 / "draft_content.json"
        c0 = json.loads(jf0.read_text(encoding="utf-8"))
        jobs0, _b0 = TU.collect_jobs(c0, jf0, d0, d0, tmp / "OUT0", {}, opts, set())
        rev0 = [j for j in jobs0 if j.get("khoa_ghi") == "reverse_path"]
        check("draft khong co reverse_path -> khong sinh job nguoc", not rev0,
              f"{len(rev0)} job thua -> se ma lai mot file khong ton tai")
        check("van sinh job cho cac clip binh thuong", len(jobs0) > 0,
              "ban va lam hong duong chay cu")

        # Ton trong cau hinh: tat `recompress` thi khong duoc tu y nen ban nguoc
        opts_tat = dict(opts, recompress=False)
        jobs_t, _bt = TU.collect_jobs(content, jf, draft, draft, out, {},
                                      opts_tat, set())
        rev_t = [j for j in jobs_t if j.get("khoa_ghi") == "reverse_path"]
        check("tat recompress -> khong nen ban nguoc", not rev_t,
              f"{len(rev_t)} job - phai ton trong cau hinh nguoi dung")

        # --- Chay that ca pha toi uu ---
        print()
        print("=" * 72)
        print("Chay that: ket qua phai ghi dung khoa")
        print("=" * 72)
        (tmp / "_rong").mkdir(exist_ok=True)
        G = chay_tool.nap_tool()
        ma, van, _ls = chay_tool.chay(G, draft, out, che_do="4",
                                      thu_muc_do=str(tmp / "_rong"))
        check("tool chay xong khong loi", ma in (None, 0),
              f"ma thoat = {ma}" + chr(10) + van[-600:])

        kq = json.loads((out / "draft_content.json").read_text(encoding="utf-8"))
        mrev = [m for m in (kq.get("materials") or {}).get("videos") or []
                if m.get("id") == "mrev"]
        check("material co reverse_path van con", len(mrev) == 1)
        if mrev:
            m = mrev[0]
            rp = str(m.get("reverse_path") or "")
            p = str(m.get("path") or "")
            print(f"  path        : {p[:78]}")
            print(f"  reverse_path: {rp[:78]}")
            check("reverse_path DA duoc tro sang ban _opt",
                  "_opt" in rp,
                  f"reverse_path = {rp}\n-> chua duoc nen, van la ban goc")
            check("path KHONG bi ghi de bang ban nguoc",
                  "canh2_reverse" not in p,
                  f"path = {p}\n-> clip XUOI dang tro vao ban NGUOC, hinh se chay nguoc")
            check("path va reverse_path la HAI file khac nhau", p != rp,
                  f"ca hai deu = {p}")

            # File dich phai co that trong goi
            duoi = rp.split("_##/")[-1] if "_##/" in rp else rp
            dich = out / duoi.replace("/", "\\")
            check("file ban nguoc co that trong goi", TU.G.isfile_safe(dich),
                  f"{dich}")
            if TU.G.isfile_safe(dich):
                goc_sz = (Path(mo_ta["goc"]) / "FOOTAGE" / "canh2_reverse.mp4").stat().st_size \
                    if (Path(mo_ta["goc"]) / "FOOTAGE" / "canh2_reverse.mp4").is_file() else 0
                moi_sz = dich.stat().st_size
                print(f"  ban goc {goc_sz / 1024:.0f} KB -> ban nen {moi_sz / 1024:.0f} KB")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
