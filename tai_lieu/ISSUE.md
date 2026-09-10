# ISSUE — việc đang mở

Mẫu: `### [ID] Tiêu đề` → Ngày · Trạng thái · Bối cảnh · Bước tiếp theo.

---

### ISSUE-001 Bản thiết kế UI/UX
**Ngày:** 2026-09-10 · **Trạng thái: XONG (bản 1.0)**
Đã khảo sát `giao_dien.py` (987 dòng) và viết `SPEC_UI_UX.md`. Bao gồm bản đồ 2 màn hình, bố cục, máy trạng thái nút, 8 quy tắc kỹ thuật đã trả giá để biết, 10 phép kiểm đầu vào, 7 thiếu sót cần bổ sung (UX-01..07).
**Bước tiếp theo:** chủ dự án duyệt spec; đặc biệt là mục §9 (7 thiếu sót) — cái nào làm, cái nào bỏ.

### ISSUE-002 Bản đồ module để tách God Component
**Ngày:** 2026-09-10 · **Trạng thái: XONG (bản 1.0)**
Đã khảo sát toàn bộ 5564 dòng và viết `KIEN_TRUC.md`. Kết luận: God Component thật sự chỉ có **hai** — `_main_than()` (913 dòng, 12 pha) và class `GiaoDien` (750 dòng). `canh_gac.py` và `chung.py` **không cần tách**.
**Bước tiếp theo:** chủ dự án duyệt cấu trúc đích và thứ tự tách 9 bước ở §7.

### ISSUE-003 CI/CD và auto-update
**Ngày:** 2026-09-10 · **Trạng thái:** MỞ — kiểu đóng gói đã chốt bằng số đo

**Đã chốt:**
- Đóng gói **.exe** bằng **PyInstaller 6.22.2** (đã dựng thử thành công cả hai kiểu).
- Kiểu **onedir** (một thư mục), không phải onefile — đo được onedir nhanh **2,7 lần** (93,6 ms vs 252,6 ms) và ổn định hơn hẳn (biên độ 9 ms vs 202 ms). Chi tiết `PERF.md` §P-01.

**Còn chưa quyết:** cách so phiên bản (GitHub Releases API?), có ký số không (R-11), cập nhật xong có cần khởi động lại không.

**Bước tiếp theo:** thiết kế cơ chế cập nhật onedir chống dở dang (R-14) — tải về thư mục tạm, kiểm đủ file, rồi đổi tên nguyên khối, giữ bản cũ để quay về.

### ISSUE-004 Việc dở từ 2026-08-21
**Ngày:** 2026-09-10 · **Trạng thái: ĐÓNG — đã xong từ trước**

Ghi nhớ cũ nói `bug.md` #96 và watchdog #25 còn dở. **Đã kiểm lại, không còn dở.**

Đo ngày 2026-09-10:
- `python tests\kiem_nhat_ky.py` → 100 mục, số hiệu liên tục không trùng, **không mục nào còn nhãn "chưa cài"**, nhãn khớp code.
- `python tests\chay_het.py` → **22/22 ĐẠT** trong 78.9s, gồm cả `CANH GAC phat hien treo NAS ma khong bao dong gia`.

**Bài học:** ghi nhớ phản ánh thời điểm viết, không phải hiện tại. Phải kiểm lại bằng công cụ trước khi đi sửa theo một ghi chú cũ — đúng tinh thần cảnh báo nhãn lạc hậu "nguy hiểm theo cả hai chiều" trong `CLAUDE.md`.

### ISSUE-005 `__file__` sẽ sai khi đóng gói .exe — lời giải ĐÃ CÓ nhưng chưa dùng chung
**Ngày:** 2026-09-10 · **Trạng thái:** MỞ · **Ưu tiên: CAO** · Liên quan R-08

Đo được: `__file__` dùng ở **9 chỗ trong 6 file**:

| File | Dòng | Dùng làm gì |
|---|---|---|
| `giao_dien.py` | 32 | `_GOC` — nơi ghi log, nơi so với folder xuất |
| `goi_project_capcut.py` | 75, 132, 732, 879 | thư mục gốc, đọc `cau_hinh.json`, ... |
| `tu_kiem_lan_dau.py` | 26 | `GOC` — nơi ghi dấu tự kiểm |
| `toi_uu_dung_luong.py` | 63 | tìm ffmpeg |
| `xem_tien_trinh.py` | 18 | `sys.path` |

**Điều đáng chú ý:** `toi_uu_dung_luong.py:45-71` (`_cac_goc_ffmpeg`) **đã xử lý đúng** trường hợp này — nó kiểm `sys.frozen` và `sys._MEIPASS`, có ghi chú "E2" giải thích rõ hậu quả. Nhưng lời giải đó **chỉ áp dụng cho việc tìm ffmpeg**, 8 chỗ còn lại vẫn dùng `__file__` trần.

**Bước tiếp theo:** nâng logic của `_cac_goc_ffmpeg` thành hàm dùng chung trong `loi/phien_ban.py`, rồi chuyển 8 chỗ còn lại sang dùng nó. Đây là **bước 1** trong thứ tự tách ở `KIEN_TRUC.md` §7 — vừa an toàn vừa bắt buộc phải có trước khi đóng gói.

### ISSUE-006 Log và dấu tự kiểm ghi cạnh chương trình
**Ngày:** 2026-09-10 · **Trạng thái:** MỞ · **Ưu tiên: CAO** · Liên quan R-09

`_LOI_GIAO_DIEN.log` (`giao_dien.py:47`) và dấu tự kiểm (`tu_kiem_lan_dau.py:48,61`) đều ghi cạnh chương trình. Cài vào `Program Files` là mất quyền ghi.

Hậu quả nặng ở chỗ: mất `_LOI_GIAO_DIEN.log` là **mất đúng thứ cần khi hỗ trợ từ xa** — nó là lưới an toàn cuối cùng cho lỗi im lặng dưới chế độ không console.

**Bước tiếp theo:** chọn nơi ghi theo người dùng (`%LOCALAPPDATA%`), làm cùng lúc với ISSUE-005 vì cùng đụng một hàm.

### ISSUE-007 `_EXIST_CACHE` dính giữa các lần chạy `main()` — chặn hướng C
**Ngày:** 2026-09-10 · **Trạng thái:** MỞ · **Ưu tiên: CAO nếu chọn hướng C**

Phát hiện khi đánh giá hướng C (hàng đợi nhiều project). **Đo thực nghiệm**, không suy luận:

```
Lan 1 - file chua tao : _exists() = False   (dung)
        [tao file that]
Lan 2 - file DA co that: _exists() = False   (SAI - cache dinh)

file co that      : _exists() = True
sau khi XOA file  : _exists() = True        (SAI - cache dinh chieu nguoc)
```

`toi_uu_dung_luong.py:258` `_EXIST_CACHE` là dict toàn cục **không có ai xoá**. So sánh:

| Cache | Có hàm xoá? | Ai gọi |
|---|---|---|
| `_PROBE_CACHE` | ✅ `xoa_cache_probe()` | `optimize_package()` dòng 778 |
| `_LOI_PROBE` | ✅ `lay_loi_probe()` tự dọn | dòng 1040 |
| **`_EXIST_CACHE`** | ❌ **không có** | — |

**Vì sao hiện tại không sao:** ở chế độ dòng lệnh và GUI hiện tại, mỗi lần gói là **một tiến trình mới** — cache chết theo tiến trình.

**Vì sao hướng C sẽ hỏng:** hàng đợi gọi `main()` nhiều lần trong **cùng một tiến trình**. Project sau thừa hưởng cache của project trước → báo **thiếu file oan** (file đã có mà bảo không), hoặc **copy thất bại** (file đã xoá mà bảo còn). Cả hai đều là lỗi im lặng — đúng họ lỗi nguy hiểm nhất mà `bug.md` cảnh báo.

**Cách sửa:** thêm `xoa_cache_ton_tai()` và gọi ở đầu mỗi lần `main()` chạy. Rẻ, nhưng **bắt buộc phải làm trước** khi dựng hàng đợi. Có `tests/test_hieu_nang.py` đã canh `xoa_cache_probe()` không được thành code chết — nên thêm phép canh tương tự cho hàm mới.

**Điểm cộng đã kiểm:** cảnh gác (`canh_gac.CanhGac`) **không** có vấn đề này — `main()` bọc `_main_than()` trong `try/finally` và luôn tắt cảnh gác kể cả khi thân hàm có 13 đường `return`. Ghi chú trong code nói rõ vỏ bọc này sinh ra chính vì "ở chế độ GIAO DIEN thì `main()` trả về mà tiến trình VẪN SỐNG". Tức là người viết đã lường trước việc chạy nhiều lần trong một tiến trình — chỉ sót `_EXIST_CACHE`.
