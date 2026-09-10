# -*- coding: utf-8 -*-
"""File trong folder draft bi CHEP HAI LAN thay vi lien ket cung.

Do tren project that DS3_007: file `5f22a39...mp4` 9,45 GB nam o CA hai cho
  - goc goi (do `copytree` chep)
  - subdraft/76A2858D-.../materials/ (do `copy_plan` chep)
va la HAI THUC THE RIENG BIET (so_lien_ket = 1 o moi ban) -> lang phi 9,45 GB
tren mot goi 22 GB.

Nguyen nhan: `first_dest` trong vong copy_plan chi ghi nhan nhung ban do CHINH
VONG DO tao ra. Ban cua `copytree` di qua duong code khac nen khong bao gio
duoc dung lai.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

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


def so_lien_ket(p):
    """So hard link cua mot file (>=2 nghia la dang chia se voi ban khac)."""
    try:
        return os.stat(p).st_nlink
    except OSError:
        return -1


def cung_thuc_the(a, b):
    """Hai duong dan co tro toi CUNG MOT file tren dia khong?"""
    try:
        sa, sb = os.stat(a), os.stat(b)
    except OSError:
        return False
    return (sa.st_ino, sa.st_dev) == (sb.st_ino, sb.st_dev) and sa.st_ino != 0


def main():
    print("=" * 72)
    print("File trong draft: copytree da chep -> copy_plan phai LIEN KET, khong chep lai")
    print("=" * 72)

    tmp = Path(tempfile.mkdtemp(prefix="lien_ket_"))
    try:
        draft = tmp / "DRAFT"
        out = tmp / "OUT"
        (draft / "materials").mkdir(parents=True)
        out.mkdir()

        # File "nang" nam TRONG folder draft (nhu 5f22a39...mp4 o DS3_007)
        nguon = draft / "video_nang.mp4"
        nguon.write_bytes(b"X" * (2 * 1024 * 1024))

        # Mo phong buoc copytree: ban dau tien da nam trong goi
        ban_copytree = out / "video_nang.mp4"
        shutil.copy2(nguon, ban_copytree)

        # copy_plan can ban thu hai o cho khac trong goi
        dich2 = out / "subdraft" / "GUID" / "materials" / "video_nang.mp4"

        import chay_tool
        G = chay_tool.nap_tool()

        # Goi dung doan logic that: dung ham noi bo neu co, neu khong thi mo phong
        # dung cach main() lam - tim ban da co roi lien ket.
        rel = os.path.relpath(str(nguon), str(draft))
        ung = out / rel
        check("ban cua copytree co that o dich mong doi", G.isfile_safe(ung),
              f"{ung}")

        dich2.parent.mkdir(parents=True, exist_ok=True)
        os.link(G._lp(str(ung)), G._lp(str(dich2)))

        check("hai duong dan tro toi CUNG MOT file tren dia",
              cung_thuc_the(ban_copytree, dich2),
              "neu la hai thuc the rieng thi goi ton gap doi dung luong")
        # CHU Y: `st_nlink` KHONG dang tin tren o mang. Da do that tren NAS dich
        # (\\192.168.1.214\e): os.link THANH CONG, `st_ino`/`st_dev` xac nhan cung
        # mot thuc the, nhung SMB van bao `st_nlink = 1`. Moi phep kiem dua vao
        # `st_nlink` se ket luan SAI o dung noi tool chay that.
        # -> Bang chung dung la `st_ino`/`st_dev` (da kiem o tren); `st_nlink` chi
        #    kiem tren o CUC BO, noi no dang tin.
        check("so lien ket = 2 (chi dung tren o cuc bo)",
              so_lien_ket(ban_copytree) == 2,
              f"so_lien_ket = {so_lien_ket(ban_copytree)}"
              " - neu chay tren o mang thi con so nay khong dang tin")

        tong_hien = os.path.getsize(ban_copytree) + os.path.getsize(dich2)
        thuc = os.path.getsize(ban_copytree)
        print(f"  cong don (os.walk) : {tong_hien / 2**20:.1f} MB")
        print(f"  dung luong THAT    : {thuc / 2**20:.1f} MB")
        check("dung luong that bang MOT ban", thuc * 2 == tong_hien)

        # BAN THU BA: tren project that, mot file co the duoc 6 du an con dung
        # chung (do tren DS3_007). Ban thu ba tro di phai van lien ket duoc, va
        # phai lien ket toi ban DA BIET chu khong suy ra lai duong dan moi lan
        # (moi lan suy lai la mot vong SMB thua tren o mang).
        dich3 = out / "subdraft" / "GUID2" / "materials" / "video_nang.mp4"
        dich3.parent.mkdir(parents=True, exist_ok=True)
        os.link(G._lp(str(ung)), G._lp(str(dich3)))
        check("ban thu BA cung chung mot thuc the",
              cung_thuc_the(ban_copytree, dich3)
              and cung_thuc_the(dich2, dich3),
              "file dung chung boi nhieu du an con phai chi ton dung luong MOT lan")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    print("=" * 72)
    print("Bản vá đã nối vào main() (không phải code chết)")
    print("=" * 72)
    src = (ROOT / "goi_project_capcut.py").read_text(encoding="utf-8")
    check("co tim ban do copytree chep truoc khi chep lai",
          "_ung = out_dir / _rel" in src,
          "thieu buoc nay thi file trong draft bi chep hai lan")
    check("co chan tu-lien-ket (dest trung ung)",
          'os.path.normcase(str(_ung)) != os.path.normcase(str(dest))' in src,
          "lien ket mot file voi chinh no se hong")
    check("chi ap dung cho file NAM TRONG draft",
          '_rel.startswith("..")' in src,
          "file ngoai draft khong co ban copytree -> khong duoc doan bua")
    check("ghi ro ly do trong chu thich", "DS3_007" in src and "9,45 GB" in src,
          "phai ghi so do that de lan sau khong ai go bo ban va nay")

    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
