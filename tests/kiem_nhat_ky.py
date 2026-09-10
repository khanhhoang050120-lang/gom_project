# -*- coding: utf-8 -*-
"""Kiem tinh toan ven cua `bug.md` - chay TRUOC khi bat dau viec moi.

Ba viec, deu rut ra tu kinh nghiem dau don:

  1. SO HIEU khong trung, khong thieu.
     Muc 42 ghi lai canh: sua loi trung so bang mot ket qua `grep` tu DAU PHIEN,
     trong khi file da duoc them muc moi giua chung -> thao tac "sua loi" lai tao
     ra ba cap trung moi. Khi co NHIEU PHIEN LAM VIEC cung luc tren cung repo,
     day la loi gan nhu chac chan se xay ra neu khong co may kiem.

  2. Liet ke cac muc con danh dau CHUA CAI.
     Muc 32 ghi ro: "Ghi 'cach sua (chua cai)' vao nhat ky KHONG phai la da sua."
     Nhung nhan nay cung co the LAC HAU theo chieu nguoc lai - da cai roi ma quen
     doi nhan - khien phien sau tuong bug con song va di sua lai lan hai.

  3. Doi chieu nhan voi CODE THAT: neu muc ghi "chua cai" nhung dau van cua ban
     va da co trong code (hoac nguoc lai) thi bao ra de nguoi doc kiem lai.

Chay:  python tests\\kiem_nhat_ky.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
NHAT_KY = GOC / "bug.md"

# (so muc, dau van nhan biet trong code, file chua no) - de doi chieu nhan/code.
# Chi liet ke nhung muc co dau van RO RANG; khong co thi bo qua, khong doan.
DAU_VAN = {
    29: ("def _load_opt_index(", "toi_uu_dung_luong.py"),
    30: ("_saved_srcs", "toi_uu_dung_luong.py"),
    35: ("MAX_DUR_DIFF_S", "toi_uu_dung_luong.py"),
    # 38: CHUA CAI - chua biet dau van se la gi, KHONG duoc doan mot chuoi roi
    #     coi la doi chieu duoc; dau van bia ra se sinh ket luan "OK" gia.
    #     Muc nay da nam trong danh sach "chua cai" o phan 2 nen khong lot.
    40: ("if _is_under(out_dir, draft_dir):", "goi_project_capcut.py"),
    41: ("verify_loi", "goi_project_capcut.py"),
    43: ("info_src = probe(ffprobe, job[", "toi_uu_dung_luong.py"),
    # Ban va #44 sau do duoc SIET them (xem muc ve quet thieu): tu "vang mat loi"
    # thanh BANG CHUNG DUONG `bool(refd)`. Dau van bat phan bat bien la ten bien
    # + `not loi_doc`, de con sieu them lan nua van khong bao lech gia.
    44: ("duoc_xoa_mo_coi = bool(refd) and not loi_doc", "toi_uu_dung_luong.py"),
    45: ("rel.split(os.sep)", "toi_uu_dung_luong.py"),
    46: ("DON DEP - file KHONG xoa duoc", "goi_project_capcut.py"),
    47: ("def isdir_safe(", "chung.py"),          # E1: da chuyen sang tang tien ich
    # 48: ban va goc (`os.path.samefile`) da bi E1 XOA cung voi `_find_main_module()`.
    #     Gio kiem theo trang thai MOI: `toi_uu` import thang tang tien ich, khong
    #     con buoc tra cuu module nao de bi danh lua.
    48: ("import chung as G", "toi_uu_dung_luong.py"),
}

CHUA_CAI = re.compile(r"(chưa cài|CHƯA CÀI|CẦN CÀI|chua cai)", re.I)
DA_CAI = re.compile(r"ĐÃ CÀI", re.I)


def doc_muc(s):
    """Tra list (so, tieu_de, than_bai)."""
    vt = [(m.start(), int(m.group(1)), m.group(2))
          for m in re.finditer(r"^### (\d+)\. (.*)$", s, re.M)]
    ra = []
    for i, (pos, so, tieu) in enumerate(vt):
        het = vt[i + 1][0] if i + 1 < len(vt) else len(s)
        ra.append((so, tieu, s[pos:het]))
    return ra


def main():
    if not NHAT_KY.is_file():
        print(f"KHONG THAY {NHAT_KY}")
        return 2
    s = NHAT_KY.read_text(encoding="utf-8")
    muc = doc_muc(s)
    so = [m[0] for m in muc]
    loi = 0

    print("=" * 72)
    print(" KIEM TINH TOAN VEN bug.md")
    print("=" * 72)
    print(f"  Tong so muc: {len(muc)}   |   so hieu lon nhat: {max(so) if so else 0}")

    # --- 1. So hieu ---
    trung = sorted(x for x in set(so) if so.count(x) > 1)
    thieu = sorted(set(range(1, max(so) + 1)) - set(so)) if so else []
    if trung:
        loi += 1
        print(f"\n  !! TRUNG SO: {trung}")
        for n, tieu, _ in muc:
            if n in trung:
                print(f"       #{n}  {tieu[:80]}")
        print("       -> Doi so cac muc trung. So ke tiep con trong la"
              f" {max(so) + 1}.")
    else:
        print("  OK  khong co so hieu trung")
    if thieu:
        loi += 1
        print(f"\n  !! THIEU SO: {thieu}")
    else:
        print("  OK  day so lien tuc, khong thieu")

    # --- 2. Muc con CHUA CAI ---
    con_song = []
    for n, tieu, than in muc:
        for dong in than.splitlines():
            if dong.lstrip().startswith("- **Cách sửa") and CHUA_CAI.search(dong) \
                    and not DA_CAI.search(dong):
                con_song.append((n, tieu))
                break
    print()
    if con_song:
        print(f"  >> {len(con_song)} MUC CON DANH DAU 'CHUA CAI'"
              " - bug van dang SONG trong code:")
        for n, tieu in con_song:
            print(f"       #{n}  {tieu[:80]}")
        print("       -> Doc ky truoc khi chay pha nang; day la loi da biet.")
    else:
        print("  OK  khong muc nao con danh dau 'chua cai'")

    # --- 3. Doi chieu nhan voi code that ---
    print()
    lech = []
    for n, tieu, than in muc:
        if n not in DAU_VAN:
            continue
        dau, tep = DAU_VAN[n]
        duong = GOC / tep
        co_trong_code = duong.is_file() and dau in duong.read_text(encoding="utf-8")
        nhan_chua_cai = any(
            d.lstrip().startswith("- **Cách sửa") and CHUA_CAI.search(d)
            and not DA_CAI.search(d) for d in than.splitlines())
        if co_trong_code and nhan_chua_cai:
            lech.append(f"#{n}: nhan noi CHUA CAI nhung code DA co '{dau}'")
        if not co_trong_code and not nhan_chua_cai:
            lech.append(f"#{n}: nhan noi da cai nhung code KHONG thay '{dau}'")
    if lech:
        loi += 1
        print(f"  !! {len(lech)} MUC LECH giua NHAN va CODE:")
        for d in lech:
            print(f"       {d}")
        print("       -> Nhan lac hau nguy hiem ca hai chieu: phien sau se sua lai"
              " viec da xong, hoac tuong bug da chet trong khi no con song.")
    else:
        print("  OK  nhan va code khop nhau (tren cac muc co dau van doi chieu)")

    print()
    print("=" * 72)
    if loi:
        print(f"  => CO {loi} VAN DE CAN XU LY.")
        return 1
    print("  => NHAT KY TOAN VEN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
