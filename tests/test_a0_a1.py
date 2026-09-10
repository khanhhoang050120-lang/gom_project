# -*- coding: utf-8 -*-
"""Kiem chung A0 (chan out_dir nam trong draft_dir) + A1 (bo kiem chet -> phai bao THAT BAI).

QUAN TRONG (bug.md #9/#22/#34): KHONG truyen path qua shell/argv - backslash bi nuot.
Moi path dung o day deu dung chr(92) hoac Path() ben TRONG file Python nay.
"""
import os, sys, importlib.util
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
G = importlib.util.module_from_spec(spec)
sys.modules["goi_project_capcut"] = G
spec.loader.exec_module(G)

pas = fail = 0


def check(ten, dieu_kien, chi_tiet=""):
    global pas, fail
    if dieu_kien:
        pas += 1
        print(f"  PASS  {ten}")
    else:
        fail += 1
        print(f"  FAIL  {ten}   {chi_tiet}")


print("=" * 68)
print("A0 - phep so sanh _is_under dung lam chan (khong can tao file that)")
print("=" * 68)

draft = Path(BS.join(["D:", "CapCut", "Projects", "DS1_090"]))

# 1. Trung y het -> phai chan
check("out_dir TRUNG draft_dir bi chan",
      G._is_under(draft, draft))

# 2. Nam trong -> phai chan
check("out_dir NAM TRONG draft_dir bi chan",
      G._is_under(draft / "PORTABLE", draft))

# 3. Nam sau nhieu tang -> phai chan
check("out_dir long sau 3 tang bi chan",
      G._is_under(draft / "a" / "b" / "PORTABLE", draft))

# 4. Chieu nguoc: draft nam trong out -> phai chan
out_ngoai = Path(BS.join(["D:", "CapCut"]))
check("draft_dir NAM TRONG out_dir bi chan (chieu nguoc)",
      G._is_under(draft, out_ngoai))

# 5. Anh em ngang hang -> KHONG duoc chan
check("thu muc anh em KHONG bi chan",
      not G._is_under(draft.parent / "DS1_090_PORTABLE", draft),
      "day la duong dung nhat, chan nham la hong tinh nang")

# 6. Ten co tien to trung -> KHONG duoc chan (bay chuoi con)
check("ten co tien to trung KHONG bi chan",
      not G._is_under(Path(str(draft) + "_PORTABLE"), draft),
      "DS1_090_PORTABLE khong nam trong DS1_090")

# 7. Khac o dia -> KHONG chan
check("khac o dia KHONG bi chan",
      not G._is_under(Path(BS.join(["E:", "GOI"])), draft))

# 8. Khong phan biet hoa thuong (Windows)
check("khong phan biet HOA/thuong",
      G._is_under(Path(BS.join(["d:", "capcut", "projects", "DS1_090", "X"])), draft))

# 9. UNC: cung share -> chan
unc = Path(BS * 2 + BS.join(["192.168.1.213", "padoma 8", "DS1_090"]))
check("UNC: out nam trong draft UNC bi chan",
      G._is_under(unc / "PORTABLE", unc))

# 10. UNC: khac server -> khong chan
unc2 = Path(BS * 2 + BS.join(["192.168.1.214", "share", "GOI"]))
check("UNC: khac server KHONG bi chan",
      not G._is_under(unc2, unc))

print()
print("=" * 68)
print("A0 - dua ve tuyet doi (bug #23: 'D:' la drive-relative)")
print("=" * 68)

# 'D:' khong phai goc o dia. abspath phai bien no thanh mot path tuyet doi that.
kq = os.path.abspath(G._unlp(Path("D:")))
check("'D:' duoc dua ve tuyet doi",
      len(kq) > 2 and kq[1] == ":" and kq[2] == BS,
      f"ket qua = {kq!r}")

kq2 = os.path.abspath(G._unlp(Path("goi_moi")))
check("path tuong doi duoc dua ve tuyet doi",
      os.path.isabs(kq2), f"ket qua = {kq2!r}")

# UNC phai giu nguyen 2 backslash sau khi abspath
kq3 = os.path.abspath(G._unlp(unc))
check("UNC giu nguyen 2 backslash dau sau abspath",
      kq3.startswith(BS * 2), f"repr = {kq3!r}")

print()
print("=" * 68)
print("A1 - bo kiem chet PHAI lam ket luan thanh CHUA XONG")
print("=" * 68)


def tinh_ok(verify_loi, **kw):
    """Mo phong dung bieu thuc ok trong main() sau khi sua."""
    misses_hard = kw.get("misses_hard", [])
    copy_fail = kw.get("copy_fail", [])
    skipped_items = kw.get("skipped_items", [])
    bad_hard = kw.get("bad_hard", [])
    unresolved_hard = kw.get("unresolved_hard", {})
    rewrite_fail = kw.get("rewrite_fail", [])
    json_fail = kw.get("json_fail", [])
    json_fail2 = kw.get("json_fail2", [])
    opt_bad = kw.get("opt_bad", [])
    return not (misses_hard or copy_fail or skipped_items or bad_hard
                or unresolved_hard or rewrite_fail or json_fail or json_fail2
                or opt_bad or verify_loi)


check("moi thu sach + khong loi kiem -> ok = True",
      tinh_ok([]) is True)

check("moi thu sach NHUNG verify_package chet -> ok = False",
      tinh_ok(["verify_package: OSError: mat ket noi"]) is False,
      "day chinh la bug: truoc khi sua no tra True va in 'Ban tu chua DU'")

check("verify_optimize chet -> ok = False",
      tinh_ok(["verify_optimize: RuntimeError: x"]) is False)

check("scan_long_paths chet -> ok = False",
      tinh_ok(["scan_long_paths: OSError: y"]) is False)

check("nhieu bo kiem cung chet -> ok = False",
      tinh_ok(["a: 1", "b: 2", "c: 3"]) is False)

check("co loi that VA bo kiem chet -> van ok = False",
      tinh_ok(["a: 1"], misses_hard=["f.mp4"]) is False)

print()
print("=" * 68)
print("Kiem ma nguon: khong con cho nao nuot loi kiem roi di tiep")
print("=" * 68)

src = (ROOT / "goi_project_capcut.py").read_text(encoding="utf-8")

check("verify_loi duoc khai bao truoc khoi kiem toi uu",
      # Bam Y NGHIA chu khong chuoi cu the: chuoi cu
      # `"opt_bad = TU.verify_optimize"` da hong ngay khi ham doi sang tra 2
      # gia tri (bug #104), va bo kiem bao FAIL vi mot ly do khac han cai no
      # dinh kiem.
      src.index("verify_loi = []") < src.index("TU.verify_optimize("),
      "neu khai bao sau se NameError khi che do 4 bi loi")

check("verify_loi nam trong bieu thuc ok",
      "or opt_bad or verify_loi)" in src)

check("bao cao co muc BO TU KIEM THAT BAI",
      "BO TU KIEM THAT BAI" in src)

# Kiem DUNG cau thong bao cu, khong grep chung chung "(bo qua)": chuoi do con
# xuat hien o cho HOP LE khac (khoa la trong cau_hinh.json thi dung la bo qua).
# Phep kiem qua rong se bao dong gia moi khi them tinh nang - dung ho #31/#53.
check("khong con thong bao 'Tu kiem loi (bo qua)'",
      "Tu kiem loi (bo qua)" not in src,
      "cau nay ham y bo kiem chet thi bo qua duoc - da phai doi")
check("thay bang thong bao noi ro that bai",
      "TU KIEM THAT BAI" in src)

check("so cache duoc GIU LAI khi chua tu kiem duoc",
      "GIU LAI so cache" in src)

check("TOOL_VERSION co trong ma nguon", "TOOL_VERSION" in src)
check("bao cao ghi phien ban tool", 'f"Tool: goi_project_capcut {TOOL_VERSION}"' in src
      or "Tool: goi_project_capcut {TOOL_VERSION}" in src)

print()
print("=" * 68)
print(f"KET QUA: {pas} PASS / {fail} FAIL")
print("=" * 68)
sys.exit(1 if fail else 0)
