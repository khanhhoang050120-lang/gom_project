# -*- coding: utf-8 -*-
"""A7 - kiem bo bat 'ket qua bi CUT' trong encode_job().

Dung media THAT do ffmpeg sinh ra, khong gia lap. Hai kich ban:
  (1) NGUON DAY DU, ket qua bi cut  -> PHAI bao that bai  (dung y do bug #35)
  (2) NGUON VON DA NGAN hon so 'duration' ghi trong JSON draft goc
      -> KHONG duoc bao that bai, vi day la loi CO SAN cua draft goc.
      bug #35 ghi nhan 16 file .aac dang nay trong DS1_090.
"""
import importlib.util, os, shutil, sys, tempfile
from pathlib import Path

BS = chr(92)
# Suy ra tu vi tri file nay -> chep tool sang may khac van chay
ROOT = Path(__file__).resolve().parent.parent
# E1: goi_project_capcut.py gio `import chung`, nen thu muc tool PHAI nam
# trong sys.path TRUOC khi nap module bang spec_from_file_location - neu
# khong se ModuleNotFoundError: No module named 'chung'.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("goi_project_capcut", ROOT / "goi_project_capcut.py")
G = importlib.util.module_from_spec(spec); sys.modules["goi_project_capcut"] = G
spec.loader.exec_module(G)
TU = G.import_toi_uu()

US = TU.US
ffmpeg, ffprobe = TU.ff_paths()
assert ffmpeg and ffprobe, "khong tim thay ffmpeg"

pas = fail = 0


def check(ten, dk, chi_tiet=""):
    global pas, fail
    if dk:
        pas += 1; print(f"  PASS  {ten}")
    else:
        fail += 1; print(f"  FAIL  {ten}   {chi_tiet}")


def tao_video(path, giay):
    """Sinh video that dai `giay` giay."""
    TU._run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
             "-f", "lavfi", "-i", f"testsrc2=size=320x240:rate=25:duration={giay}",
             "-f", "lavfi", "-i", f"sine=frequency=440:duration={giay}",
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30",
             "-c:a", "aac", "-shortest", str(path)], 120)
    return path


work = Path(tempfile.mkdtemp(prefix="a7_"))
tmpd = work / "tmp"; tmpd.mkdir()
dest = work / "out"; dest.mkdir()

try:
    print("=" * 70)
    print("Kich ban 1: NGUON DAY DU 10s, job doi 10s -> phai THANH CONG")
    print("=" * 70)
    src_du = tao_video(work / "nguon_day_du.mp4", 10)
    do_that = TU.probe(ffprobe, src_du)[2] / US
    print(f"  (nguon that: {do_that:.2f}s)")

    job_ok = {"key": ("k1", 0, 10 * US, 0), "src": src_du, "dest": dest / "a_opt.mp4",
              "lo": 0, "span": 10 * US, "trim": False, "scale": False,
              "target_w": 0, "size": os.path.getsize(src_du), "recompress": True}
    ok, err = TU.encode_job(ffmpeg, job_ok, tmpd, 28, "ultrafast", ffprobe=ffprobe)
    check("nguon du + doi dung -> thanh cong", ok, f"err={err!r}")

    print()
    print("=" * 70)
    print("Kich ban 2: NGUON DAY DU 10s nhung job doi 30s (gia lap ket qua cut)")
    print("=" * 70)
    # Nguon chi co 10s ma job doi 30s => ffmpeg ra 10s => lech 20s.
    # Day CHINH LA hinh dang cua truong hop 'nguon von da ngan hon JSON'.
    job_ngan = {"key": ("k2", 0, 30 * US, 0), "src": src_du, "dest": dest / "b_opt.mp4",
                "lo": 0, "span": 30 * US, "trim": False, "scale": False,
                "target_w": 0, "size": os.path.getsize(src_du), "recompress": True}
    ok2, err2 = TU.encode_job(ffmpeg, job_ngan, tmpd, 28, "ultrafast", ffprobe=ffprobe)
    print(f"  ket qua: ok={ok2}  err={err2!r}")
    check("nguon VON DA NGAN khong bi bao 'BI CUT' oan",
          ok2,
          "-> DAY LA LO HONG: file .aac ngan san trong draft goc se bi bao that bai oan"
          " (bug #35 ghi nhan 16 file dang nay trong DS1_090)")

    print()
    print("=" * 70)
    print("Kich ban 3: CAT GON that - nguon 10s, lay doan 2s->5s (span 3s)")
    print("=" * 70)
    job_trim = {"key": ("k3", 2 * US, 3 * US, 0), "src": src_du, "dest": dest / "c_opt.mp4",
                "lo": 2 * US, "span": 3 * US, "trim": True, "scale": False,
                "target_w": 0, "size": os.path.getsize(src_du), "recompress": False}
    ok3, err3 = TU.encode_job(ffmpeg, job_trim, tmpd, 28, "ultrafast", ffprobe=ffprobe)
    check("cat gon dung pham vi -> thanh cong", ok3, f"err={err3!r}")
    if ok3:
        d3 = TU.probe(ffprobe, job_trim["dest"])[2] / US
        check("do dai ban cat ~3s", abs(d3 - 3.0) <= 0.6, f"do duoc {d3:.2f}s")

    print()
    print("=" * 70)
    print("Kich ban 4: DUNG canh bug #35 - NGUON DU DAI nhung DAU RA bi cut")
    print("=" * 70)
    # Khong the bat ffmpeg tu sinh file cut theo y muon, nen EP LOI o tang do:
    # bat probe() bao file tam chi dai 1,70s trong khi nguon van 10s (giong het
    # so lieu that cua bug #35: 12,47s -> 1,70s). Day la fault injection - kiem
    # chinh QUYET DINH cua code, khong phai kiem ffmpeg.
    probe_that = TU.probe

    def probe_ep_loi(fp, path, timeout=120):
        info = probe_that(fp, path, timeout)
        if info and str(path).endswith(".mp4") and BS + "tmp" + BS in str(path):
            return (info[0], info[1], int(1.70 * US), info[3])   # gia lam file cut
        return info

    job_cut = {"key": ("k4", 0, 12 * US, 0), "src": src_du, "dest": dest / "d_opt.mp4",
               "lo": 0, "span": 12 * US, "trim": True, "scale": False,
               "target_w": 0, "size": os.path.getsize(src_du), "recompress": False}
    TU.probe = probe_ep_loi
    try:
        ok4, err4 = TU.encode_job(ffmpeg, job_cut, tmpd, 28, "ultrafast", ffprobe=ffprobe)
    finally:
        TU.probe = probe_that
    print(f"  ket qua: ok={ok4}  err={err4!r}")
    check("dau ra bi cut trong khi nguon du dai -> BI BAT",
          (not ok4) and "CUT" in (err4 or ""),
          f"err={err4!r}  <- day la kich ban that cua bug #35")
    check("job that bai thi KHONG tao file dich",
          not G.isfile_safe(job_cut["dest"]),
          "bug #35: khong duoc de lai file hong cho cache/dup nhan ban")

    print()
    print("=" * 70)
    print("Kich ban 5: khong doc duoc NGUON -> mac dinh CHUA XONG (phai that bai)")
    print("=" * 70)

    def probe_mu_nguon(fp, path, timeout=120):
        info = probe_that(fp, path, timeout)
        if info and BS + "tmp" + BS in str(path):
            return (info[0], info[1], int(1.70 * US), info[3])
        if str(path) == str(src_du):
            return None                      # gia lam khong doc duoc nguon
        return info

    job5 = dict(job_cut, dest=dest / "e_opt.mp4")
    TU.probe = probe_mu_nguon
    try:
        ok5, err5 = TU.encode_job(ffmpeg, job5, tmpd, 28, "ultrafast", ffprobe=ffprobe)
    finally:
        TU.probe = probe_that
    print(f"  ket qua: ok={ok5}  err={err5!r}")
    check("khong phan biet duoc thi PHAI bao that bai",
          not ok5,
          "checklist bug.md: mac dinh CHUA XONG cho toi khi chung minh duoc")

finally:
    shutil.rmtree(work, ignore_errors=True)

print()
print("=" * 70)
print(f"KET QUA: {pas} PASS / {fail} FAIL")
print("=" * 70)
sys.exit(1 if fail else 0)
