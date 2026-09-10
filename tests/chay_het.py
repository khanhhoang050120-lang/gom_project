# -*- coding: utf-8 -*-
"""Chay TAT CA bo kiem cua tool. Khong can NAS, khong can footage that.

    python tests\\chay_het.py

Ma thoat 0 = tat ca dat. Khac 0 = co bo kiem that bai (in ro bo nao).

Nguyen tac (checklist bug.md):
  - Moi bo kiem chay trong TIEN TRINH RIENG. Mot bo treo hoac chet khong duoc
    lam mat ket qua cua cac bo khac.
  - KHONG truyen duong dan qua shell/argv - cac bo kiem tu suy ra vi tri.
  - Bo kiem nao khong chay duoc (thieu ffmpeg...) phai bao RO, khong duoc im
    lang bo qua roi bao "tat ca dat".
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (ten hien thi, ten file, gioi han giay)
BO_KIEM = [
    ("NHAT KY  bug.md: so hieu + muc con 'chua cai'", "kiem_nhat_ky.py", 60),
    ("DUONG DAN  UNC / long-path / tieng Viet (nhom #1,2,7,23,34)", "test_duong_dan.py", 240),
    ("A0 + A1  chan ghi de goc / bo tu kiem khong noi doi", "test_a0_a1.py", 120),
    ("A7       bat ket qua ma lai bi cut", "test_a7.py", 300),
    ("A2..A6   don dep khong xoa nham / tu choi module gia", "test_don_dep.py", 180),
    ("DEM      bo dem khop viec that su da lam", "test_dem.py", 300),
    ("#38      mot nguon nhieu ban _opt / ban goc thua", "test_ban_goc_thua.py", 300),
    ("#104     lech VON CO trong draft goc vs lech DO GOI", "test_lech_von_co.py", 60),
    ("ON DINH  race / ghi atomic / o mang / cau hinh", "test_on_dinh.py", 240),
    ("DONG GOI E2 ffmpeg di kem / G1 kiem tien de", "test_dong_goi.py", 300),
    ("PHIEN BAN thu muc goc + noi ghi khi dong goi .exe", "test_phien_ban.py", 60),
    ("CAU NOI  bang dich cau hoi -> dap an (khong can tkinter)", "test_cau_noi.py", 60),
    ("KIEM DAU VAO  10 phep kiem muc 1-4 (khong can tkinter)", "test_kiem_dau_vao.py", 60),
    ("HANG DOI  goi main() nhieu lan trong mot tien trinh", "test_hang_doi.py", 60),
    ("HANG DOI UI  dieu phoi nhieu project (khong can tkinter)", "test_hang_doi_ui.py", 60),
    ("HANG DOI LOG  ghi log ra ngoai + gioi han nhat ky", "test_hang_doi_log.py", 60),
    ("NUOT LOI ep copy/link that bai (nhom #4,5,11,17,20)", "test_nuot_loi.py", 400),
    ("XEM TIEN TRINH  _fmt_time / do dung luong / chay that", "test_xem_tien_trinh.py", 200),
    ("HIEU NANG  moi truong dem / cache probe", "test_hieu_nang.py", 200),
    ("TAI LIEU BAN_GIAO.md phai khop code that", "test_tai_lieu.py", 60),
    ("CUU BAN GOC bi bo qua ma khong duoc thay", "test_cuu_ban_goc.py", 120),
    ("BANG MA  doc dau ra ffmpeg bang UTF-8 (may con ACP 1258)", "test_bang_ma.py", 200),
    ("QUET THIEU  NAS rot phien -> khong duoc xoa nham media", "test_quet_thieu.py", 120),
    ("FFMPEG HONG  co file nhung khong chay duoc", "test_ffmpeg_hong.py", 120),
    ("BAT      diem vao may con: thieu Python / thieu file", "test_bat.py", 300),
    ("DEPENDENCY chi dung thu vien chuan (dieu kien ban giao)", "test_khong_dependency.py", 60),
    ("PATH DAI  loi khuyen phai LAM DUOC, khong noi cho co", "test_path_dai.py", 60),
    ("LIEN KET CUNG  file trong draft khong duoc chep hai lan", "test_lien_ket_cung.py", 120),
    ("REVERSE  ban render nguoc phai duoc nen", "test_reverse.py", 600),
    ("NHIP DAP  noi ro dang ma clip nao khi im lang", "test_nhip_dap.py", 60),
    ("XU LY LOI  trinh bao loi khong duoc tu chet", "test_xu_ly_loi.py", 240),
    ("GIAO DIEN  lai duoc tool that, khong viet lai logic", "test_giao_dien.py", 600),
    ("LAN DAU   tu kiem mot lan + an console", "test_lan_dau.py", 300),
    ("DUNG DO  nut huy phai that tha (moc huy + bao cao + nhan)",
     "test_dung_do.py", 300),
    ("CANH GAC phat hien treo NAS ma khong bao dong gia",
     "test_canh_gac.py", 300),
    ("E2E      luong that tren draft gia + ep loi", "test_e2e.py", 600),
    ("HANG DOI E2E  gom nhieu project that trong mot tien trinh",
     "test_hang_doi_e2e.py", 900),
]


def main():
    print("=" * 72)
    print(" CHAY TAT CA BO KIEM - GOI PROJECT CAPCUT")
    print("=" * 72)
    ket_qua = []
    t0 = time.monotonic()

    for ten, tep, gioi_han in BO_KIEM:
        duong = HERE / tep
        if not duong.is_file():
            ket_qua.append((ten, "THIEU FILE", 0.0))
            print(f"\n!! KHONG THAY {tep} - bo kiem nay KHONG duoc chay")
            continue
        print(f"\n{'-' * 72}\n>> {ten}\n{'-' * 72}")
        t1 = time.monotonic()
        try:
            r = subprocess.run([sys.executable, "-u", str(duong)],
                               cwd=str(HERE.parent), timeout=gioi_han,
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            ra = r.stdout or ""
            # Chi in dong ket qua + cac dong FAIL, tranh ngap man hinh
            for d in ra.splitlines():
                if d.strip().startswith("FAIL") or "KET QUA" in d:
                    print("   " + d.strip())
            if r.returncode != 0 and r.stderr:
                print("   stderr:", r.stderr.strip()[-500:])
            trang_thai = "DAT" if r.returncode == 0 else (
                "BO QUA (thieu ffmpeg)" if r.returncode == 2 else "THAT BAI")
        except subprocess.TimeoutExpired:
            trang_thai = f"QUA GIO (>{gioi_han}s)"
            print(f"   !! Bo kiem chay qua {gioi_han}s -> bi dung."
                  " Rat co the dang quet o mang (xem bug #27).")
        except Exception as ex:
            trang_thai = f"LOI CHAY: {type(ex).__name__}: {ex}"
        ket_qua.append((ten, trang_thai, time.monotonic() - t1))

    print()
    print("=" * 72)
    print(" TONG KET")
    print("=" * 72)
    for ten, tt, giay in ket_qua:
        print(f"  {tt:22s} {giay:6.1f}s   {ten}")

    hong = [t for _, t, _ in ket_qua if t != "DAT"]
    print()
    print(f"  Tong thoi gian: {time.monotonic() - t0:.1f}s")
    if hong:
        print(f"  => CO {len(hong)} BO KIEM KHONG DAT - xem o tren.")
        return 1
    print("  => TAT CA DAT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
