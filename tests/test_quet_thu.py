# -*- coding: utf-8 -*-
"""`ui/quet_thu.py` + hai cột mới của bảng hàng đợi.

Ba điều quan trọng nhất:
  1. Quét thử KHÔNG ghi một byte nào ra đĩa
  2. Công thức chế độ 4 phải KHỚP TỪNG CHỮ với `_main_than()` — lệch là số
     liệu xem trước nói dối, mà người dùng quyết định dựa trên số đó
  3. Định dạng dung lượng dùng GB THẬP PHÂN (1e9) giống phần còn lại của
     tool — hai cách đọc trong cùng một cửa sổ là báo cáo không nhất quán
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.hang_doi import Muc, co, lau        # noqa: E402
from ui.quet_thu import quet_thu            # noqa: E402

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


class GiaG:
    """`goi_project_capcut` giả: trả sẵn `refs` và `need_copy`."""

    def __init__(self, refs, need_copy, nem=None):
        self._refs = refs
        self._need = need_copy
        self._nem = nem

    def collect_refs(self, draft_dir, nen_dung=None):
        if self._nem:
            raise self._nem
        return self._refs, self._need, [], 1


print("=" * 70)
print(" `ui/quet_thu.py` — xem trước số liệu, KHÔNG ghi gì")
print("=" * 70)

# ------------------------------------------------- 1. công thức chế độ 4
print("\n1. CÔNG THỨC chế độ 4 phải khớp `_main_than()`")
tmp = Path(tempfile.mkdtemp(prefix="qt_"))
try:
    # 3 file có thật: A + B dùng trên timeline, C chỉ ở kho
    p = {}
    for ten, kb in (("A", 10), ("B", 20), ("C", 40)):
        f = tmp / f"{ten}.mp4"
        f.write_bytes(b"x" * (kb * 1000))
        p[ten] = str(f)
    refs = {
        p["A"]: {"roles": {"content"}},
        p["B"]: {"roles": {"content", "registry"}},
        p["C"]: {"roles": {"registry"}},          # chỉ ở kho -> chế độ 4 bỏ
    }
    need = set(p.values())
    G = GiaG(refs, need)

    m = Muc(str(tmp), r"D:\khong_ghi", tuy_chon={"trim": True})
    kq = quet_thu(m, G)
    check("bật tối ưu -> chỉ gom file 'content'",
          kq.so_file_gom == 2 and kq.so_bo_qua == 1,
          f"gom={kq.so_file_gom} bỏ={kq.so_bo_qua}")
    check("dung lượng gom đúng (10+20 KB)",
          kq.byte_gom == 30_000, kq.byte_gom)
    check("dung lượng bỏ đúng (40 KB)",
          kq.byte_bo_qua == 40_000, kq.byte_bo_qua)

    m2 = Muc(str(tmp), r"D:\khong_ghi",
             tuy_chon={"trim": False, "scale": False, "cleanup": False})
    kq2 = quet_thu(m2, G)
    check("TẮT tối ưu -> gom HẾT, không bỏ gì",
          kq2.so_file_gom == 3 and kq2.so_bo_qua == 0,
          f"gom={kq2.so_file_gom} bỏ={kq2.so_bo_qua}")

    # File có trong refs nhưng KHÔNG trong need_copy -> đã nằm sẵn đúng chỗ
    G3 = GiaG(refs, {p["A"]})
    m3 = Muc(str(tmp), r"D:\khong_ghi", tuy_chon={"trim": True})
    kq3 = quet_thu(m3, G3)
    check("lọc trên `need_copy` chứ KHÔNG trên toàn bộ `refs`",
          kq3.so_file_gom == 1,
          f"gom={kq3.so_file_gom} — nếu ra 2 là đang lọc nhầm trên refs")

    # ------------------------------------------------- 2. file thiếu
    print("\n2. FILE THIẾU")
    refs4 = dict(refs)
    refs4[str(tmp / "mat_tieu.mp4")] = {"roles": {"content"}}
    G4 = GiaG(refs4, set(refs4))
    m4 = Muc(str(tmp), r"D:\khong_ghi", tuy_chon={"trim": True})
    kq4 = quet_thu(m4, G4)
    check("đếm đúng file không tìm thấy",
          len(kq4.thieu) == 1, kq4.thieu)
    check("file thiếu KHÔNG bị tính vào số gom",
          kq4.so_file_gom == 2, kq4.so_file_gom)
    check("dòng nhật ký có nhắc số file thiếu",
          any("KHÔNG tìm thấy" in d for d in kq4.cac_dong()), kq4.cac_dong())

    # ------------------------------------------------- 3. không ghi gì
    print("\n3. KHÔNG được ghi một byte nào ra đĩa")
    dich = tmp / "dich_khong_duoc_tao"
    m5 = Muc(str(tmp), str(dich), tuy_chon={"trim": True})
    quet_thu(m5, G)
    check("thư mục đích KHÔNG bị tạo", not dich.exists())

    # ------------------------------------------------- 4. ghi vào Muc
    print("\n4. GHI số liệu vào `Muc` để bảng hiện cột")
    check("`byte_goc` được ghi", m.byte_goc == 30_000, m.byte_goc)
    check("`so_file` được ghi", m.so_file == 2, m.so_file)
    check("cột Dung lượng hiện số", m.mo_ta_dung_luong() == "30,00 KB",
          m.mo_ta_dung_luong())

    # ------------------------------------------------- 5. lỗi
    print("\n5. LỖI không được ném ra ngoài")
    G6 = GiaG(refs, need, nem=OSError("ổ mạng rớt phiên"))
    m6 = Muc(str(tmp), r"D:\khong_ghi")
    kq6 = quet_thu(m6, G6)
    check("lỗi vào `kq.loi`, không ném", kq6.dat is False, kq6.loi)
    check("mô tả lỗi giữ nguyên thông điệp gốc",
          "rớt phiên" in kq6.loi, kq6.loi)
    check("dòng nhật ký nói rõ THẤT BẠI",
          any("THẤT BẠI" in d for d in kq6.cac_dong()), kq6.cac_dong())

    # ------------------------------------------------- 6. dừng giữa chừng
    print("\n6. DỪNG giữa chừng")
    m7 = Muc(str(tmp), r"D:\khong_ghi", tuy_chon={"trim": True})
    kq7 = quet_thu(m7, G, nen_dung=lambda: True)
    check("dừng -> không kết luận bừa", kq7.dat is False, kq7.loi)
finally:
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

# ------------------------------------------------- 7. định dạng
print("\n7. ĐỊNH DẠNG hai cột mới")
check("GB thập phân giống phần còn lại của tool (1e9)",
      co(101_350_000_000) == "101,35 GB", co(101_350_000_000))
check("dấu PHẨY thập phân kiểu Việt Nam",
      "," in co(4_300_000_000), co(4_300_000_000))
check("byte nhỏ không đổi đơn vị", co(512) == "512 B", co(512))
check("None -> gạch ngang, KHÔNG phải '0'", co(None) == "—", co(None))

check("giây", lau(45) == "45s", lau(45))
check("phút+giây", lau(750) == "12m30s", lau(750))
check("giờ+phút", lau(5400) == "1h30m", lau(5400))
check("None -> gạch ngang", lau(None) == "—", lau(None))

print("\n8. `Muc` phân biệt CHƯA BIẾT với BẰNG KHÔNG")
m = Muc(r"D:\a", r"D:\b")
check("chưa quét -> '—'", m.mo_ta_dung_luong() == "—")
m.byte_goc = 0
check("đã quét, bằng 0 -> '0 B' (KHÁC '—')",
      m.mo_ta_dung_luong() == "0 B", m.mo_ta_dung_luong())
m.byte_goc, m.byte_dich = 18_400_000_000, 4_300_000_000
check("gói xong -> hiện cả thật và gốc",
      m.mo_ta_dung_luong() == "4,30 GB / 18,40 GB", m.mo_ta_dung_luong())

print()
print("=" * 70)
print(f"KET QUA: {pas} PASS / {fail} FAIL")
print("=" * 70)
sys.exit(1 if fail else 0)
