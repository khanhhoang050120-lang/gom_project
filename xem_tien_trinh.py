#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Theo doi tien trinh copy cua mot lan GOI PROJECT dang chay.

Do dung luong thu muc dich (materials/) tang len theo thoi gian -> tinh %, toc do, ETA.
Dung khi ban lo mat log cua lan chay (VD chay nen), muon biet con bao lau.

Chay:  bam dup xem_tien_trinh.bat   (hoac: python xem_tien_trinh.py)
Roi dan duong dan folder XUAT RA (folder chua 'materials'), va tong GB du kien (Enter = tu do).
"""
import os, sys, time
from pathlib import Path

# E1: dung CHUNG `_lp` va `_fmt_time` voi tool chinh.
# Truoc day file nay tu CHEP lai ca hai. Ma `_lp()` da phai sua it nhat ba lan
# (#1 prefix UNC sai, #23 'D:' la drive-relative, #34 backslash bi nuot) - moi lan
# sua ban goc ma quen ban chep la file nay hong AM THAM tren duong dan UNC/dai.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from chung import _lp, _fmt_time  # noqa: E402

try:
    from loi.bang_ma import ep_utf8 as _ep_utf8   # noqa: E402
    _ep_utf8()
except Exception:
    pass


def dir_size_and_count(root: Path):
    """Tong byte + so file trong root (de quy). Bo qua loi le.

    `os.walk` khong co `onerror=` o day la CO Y: day chi la cua so theo doi tien
    do, chi doc, khong quyet dinh gi. Mot con so hoi lech khong hai ai, con dung
    lai giua chung thi mat luon cong cu theo doi. Moi cho khac trong tool DEU phai
    co `onerror=` (xem chu thich o `iter_json_files`)."""
    tot, cnt = 0, 0
    for dp, _, fs in os.walk(_lp(root)):
        for f in fs:
            try:
                tot += os.path.getsize(os.path.join(dp, f))
                cnt += 1
            except OSError:
                pass
    return tot, cnt


def main():
    print("=" * 60)
    print(" XEM TIEN TRINH COPY (do dung luong folder dich)")
    print("=" * 60)
    out = input("\nDan duong dan folder XUAT RA (chua 'materials'): ").strip().strip('"')
    out_dir = Path(out)
    # Do CA folder xuat ra, KHONG chi <out>/materials: tu khi ho tro du an con,
    # media nam rai o nhieu noi (<out>/materials VA subdraft/<GUID>/materials/...).
    # Chi do rieng <out>/materials se dem THIEU rat nhieu.
    if out_dir.name.lower() == "materials":
        mat = out_dir                      # nguoi dung tro thang vao materials
    else:
        mat = out_dir
        if not (out_dir / "materials").is_dir():
            print(f"  ! Chua thay {out_dir / 'materials'} - se van do"
                  f" (co the folder chua tao xong).")
        else:
            print("  (do TOAN BO folder xuat ra - gom ca materials cua cac du an con)")
    tot_gb_in = input("Tong GB du kien [Enter = khong biet, chi hien da copy]: ").strip()
    try:
        tot_bytes = float(tot_gb_in) * 1e9 if tot_gb_in else None
    except ValueError:
        tot_bytes = None

    print("\nDang do... (Ctrl+C de dung)\n")
    t0 = time.monotonic()
    b0 = None
    try:
        while True:
            b, c = dir_size_and_count(mat)
            if b0 is None:
                b0, tstart = b, time.monotonic()
            el = max(time.monotonic() - tstart, 1e-6)
            speed = (b - b0) / el                      # bytes/s ke tu luc bat dau do
            if tot_bytes:
                pct = b / tot_bytes * 100
                remain = (tot_bytes - b) / speed if speed > 0 else None
                filled = min(int(pct / 5), 20)
                bar = "#" * filled + "-" * (20 - filled)
                line = (f"\r  [{bar}] {pct:5.1f}%  {c} file  "
                        f"{b/1e9:6.2f}/{tot_bytes/1e9:.2f} GB  "
                        f"{speed/1e6:5.1f} MB/s  con ~{_fmt_time(remain)}   ")
            else:
                line = (f"\r  {c} file  {b/1e9:6.2f} GB da copy  "
                        f"{speed/1e6:5.1f} MB/s   ")
            print(line, end="", flush=True)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n\nDa dung xem. (Tien trinh copy that van chay o cua so kia.)")


def _giu_cua_so():
    """Giu cua so mo de nguoi dung doc duoc loi - nhung KHONG duoc tu chet.

    `input()` nem EOFError khi stdin da dong (chay qua bo lap lich, qua duong
    ong, hoac bi chuyen huong). Truoc day loi do lam CHINH TRINH XU LY LOI chet,
    in ra HAI traceback chong nhau va che mat loi that o tren.
    """
    try:
        input("Enter de dong...")
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDa dung.")
    except Exception:
        import traceback
        traceback.print_exc()
        _giu_cua_so()
