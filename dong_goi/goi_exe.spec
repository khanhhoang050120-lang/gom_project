# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec - GOI PROJECT CAPCUT, kieu ONEDIR.

    python dong_goi\build.py        (dung cach nay, dung goi pyinstaller thang)

Vi sao ONEDIR chu khong onefile - da DO THAT 2026-09-10 (tai_lieu/PERF.md P-01):

  |              | onedir   | onefile  |
  |--------------|----------|----------|
  | khoi dong    | 93,6 ms  | 252,6 ms |  (trung vi 10 lan, nhanh 2,7 lan)
  | bien do      | 9 ms     | 202 ms   |  (onefile giat that thuong)
  | dung luong   | 225 MB   | 83 MB    |
  | ghi ra temp  | khong    | 988 file / 221 MB MOI LAN MO |

  Onefile bung 221 MB ra thu muc tam moi lan chay - vua cham vua ban. Doi lai
  onedir lam auto-update phuc tap hon (R-14: phai doi ten nguyen khoi chu
  khong thay mot file). Day la danh doi CO Y THUC.

console=False: chay nhu `pythonw`, khong hien cua so den. Keo theo mot he qua
QUAN TRONG - stderr la HO DEN, nen ba luoi an toan o SPEC_UI_UX muc 6.8 cang
bat buoc: `_KhongDau` thay stdout, `report_callback_exception`, va try/except
boc toan bo `main()`.

`ffmpeg/` va `python/` bi .gitignore (195 MB + runtime) nen KHONG co tren
runner CI. Kich ban build phai bao RO khi thieu chu khong lang le dong goi
mot ban khong chay duoc.
"""

import os
from pathlib import Path

GOC = Path(os.getcwd())

# --- Tai nguyen di kem ---------------------------------------------------
# (nguon, thu muc dich trong goi). Dich "." = ngang hang voi .exe.
datas = [
    (str(GOC / "cau_hinh.json"), "."),
    (str(GOC / "ui"), "ui"),
    (str(GOC / "loi"), "loi"),
    (str(GOC / "BAN_GIAO.md"), "."),
    (str(GOC / "HUONG_DAN_GOI_PROJECT.md"), "."),
]

# ffmpeg: CO thi dong goi, KHONG co thi bao ro. Tuyet doi khong im lang -
# mot ban .exe thieu ffmpeg van chay duoc che do 1 nhung che do 4 se hong,
# va nguoi dung khong hieu vi sao.
_ff = GOC / "ffmpeg"
if _ff.is_dir():
    datas.append((str(_ff), "ffmpeg"))
else:
    print("!! CANH BAO: khong thay thu muc ffmpeg/ - ban .exe se KHONG co")
    print("   ffmpeg di kem. Che do 4 (toi uu dung luong) se tu ha xuong")
    print("   che do 1. Chi dong goi ban phat hanh tren may CO ffmpeg/.")


a = Analysis(
    [str(GOC / "giao_dien.py")],
    pathex=[str(GOC)],
    binaries=[],
    datas=datas,
    # Cac module duoc nap LUOI (import ben trong ham) nen PyInstaller khong
    # tu thay. Thieu chung thi .exe chay duoc toi luc nguoi dung bam nut moi
    # no ImportError - dung loai hong im lang ma bug.md canh bao nhieu nhat.
    hiddenimports=[
        "goi_project_capcut",
        "toi_uu_dung_luong",
        "chung",
        "canh_gac",
        "tu_kiem_lan_dau",
        "xem_tien_trinh",
        "ui.cau_noi",
        "ui.hang_doi",
        "ui.chay_hang_doi",
        "ui.cua_so_hang_doi",
        "ui.kiem_dau_vao",
        "ui.quet_thu",
        "loi.phien_ban",
        "loi.bang_ma",
        "tkinter",
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.scrolledtext",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Khong dung - loai bot cho nhe. Du an chi dung THU VIEN CHUAN.
        "numpy", "pandas", "matplotlib", "PIL", "pytest", "setuptools",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,          # <- ONEDIR (onefile se la False)
    name="GoiProjectCapCut",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                      # UPX hay bi Defender bao nham - khong dung
    console=False,                  # <- chay nhu pythonw, khong cua so den
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(                     # <- ONEDIR
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="GoiProjectCapCut",
)
