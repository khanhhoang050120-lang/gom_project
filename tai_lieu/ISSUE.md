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
**Ngày:** 2026-09-10 · **Trạng thái: ĐÓNG — đã sửa**

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

**Đã sửa:** thêm `xoa_cache_ton_tai()` và gọi ở đầu mỗi lần `main()` chạy. Rẻ, nhưng **bắt buộc phải làm trước** khi dựng hàng đợi. Có `tests/test_hieu_nang.py` đã canh `xoa_cache_probe()` không được thành code chết — nên thêm phép canh tương tự cho hàm mới.

**Điểm cộng đã kiểm:** cảnh gác (`canh_gac.CanhGac`) **không** có vấn đề này — `main()` bọc `_main_than()` trong `try/finally` và luôn tắt cảnh gác kể cả khi thân hàm có 13 đường `return`. Ghi chú trong code nói rõ vỏ bọc này sinh ra chính vì "ở chế độ GIAO DIEN thì `main()` trả về mà tiến trình VẪN SỐNG". Tức là người viết đã lường trước việc chạy nhiều lần trong một tiến trình — chỉ sót `_EXIST_CACHE`.

### ISSUE-008 Hàng đợi nhiều project (hướng C) — đã dựng, CHƯA commit
**Ngày:** 2026-09-10 · **Trạng thái:** XONG — **để nguyên không commit** theo yêu cầu chủ dự án

| Module | Dòng | Phép kiểm |
|---|---|---|
| `ui/hang_doi.py` | 212 | 30 (đơn vị) |
| `ui/chay_hang_doi.py` | 109 | qua E2E |
| `ui/cua_so_hang_doi.py` | 289 | qua E2E |
| `tests/test_hang_doi_e2e.py` | — | 13 (gom thật) |

**Giữ đúng nguyên tắc SPEC §1:** `ui/chay_hang_doi.py` gọi `G.main()` **đúng một lần** cho mỗi project, lái qua `builtins.input` giống hệt giao diện chính. Không tự gọi hàm con nào.

**Một bug tự tìm ra khi làm:** `_ve_chi_tiet()` giữ bản sao `self._chon`, mà bản sao đó chỉ cập nhật lúc người dùng bấm → khung phải đứng im dù mục đang chạy. Sửa bằng cách bỏ bản sao, đọc thẳng từ Listbox mỗi lần cần. **Không có bản sao thì không có chuyện bản sao lệch với bản thật.**

**Vào giao diện chính:** nút `Hang doi nhieu project...` ở hàng điều khiển, mở một `tk.Toplevel` riêng — luồng một-project giữ nguyên không đổi. Bấm lần hai thì nâng cửa sổ cũ lên chứ không tạo trùng.

**Còn lại cho lần sau:** CI/CD GitHub Actions và auto-update (ISSUE-003), 7 thiếu sót UX ở `SPEC_UI_UX.md` §9.

### ISSUE-009 Bộ máy kiểm thử tự nói dối — Giai đoạn 0 của kế hoạch kiểm thử
**Ngày:** 2026-09-11 · **Trạng thái:** ĐÃ SỬA

**Bối cảnh:** bắt đầu triển khai kế hoạch kiểm thử toàn hệ thống trước khi phát hành cho 40–50 người dùng. Trước khi viết bất kỳ test mới nào, khảo sát chính `tests/chay_het.py` — thứ duy nhất quyết định "tất cả đạt hay chưa". Nếu nó nói dối thì mọi bộ kiểm còn lại đều vô nghĩa.

**Bốn khiếm khuyết tìm được, cả bốn đều im lặng:**

| # | Khiếm khuyết | Hậu quả | Nhóm bug.md |
|---|---|---|---|
| 1 | In cứng chuỗi `"BO QUA (thieu ffmpeg)"` cho **mọi** mã thoát 2 — tức là **đoán** nguyên nhân | Bộ kiểm bỏ qua vì thiếu NAS / thiếu `pythonw` / không có màn hình tương tác đều bị gán nhãn sai | **D** (báo động giả / chẩn đoán sai) |
| 2 | **Không có ngưỡng** số bộ được phép bỏ qua | Một ngày cả 41 bộ cùng bỏ qua mà bảng tổng kết vẫn không đỏ | **C** (báo cáo sai) |
| 3 | **9 bộ kiểm** in tổng kết theo khuôn `PASS 27   FAIL 0`, trong khi `chay_het.py` lọc dòng bằng `"KET QUA" in d` | **113 phép kiểm chạy thật nhưng VÔ HÌNH** trên bảng tổng kết | **C** |
| 4 | `test_hang_doi_e2e.py` in `"KET QUA"` trống làm tiêu đề bảng số liệu, dòng tổng kết thật lại theo khuôn cũ | Bảng tổng hiện dòng `KET QUA` cụt, không số liệu | **C** |

Đây là nhóm C áp lên **chính công cụ dùng để chống nhóm C**.

**Đã sửa:**
- `chay_het.py`: đọc dòng `BO QUA: <lý do>` do **chính bộ kiểm tự khai**; bộ nào câm miệng thì bị nêu đích danh. Thêm `MAX_BO_QUA` (mặc định 2, đặt `MAX_BO_QUA=0` cho CI đầy đủ) — vượt ngưỡng thì **mã thoát 1**, không được kết luận "TAT CA DAT". Thêm ghi `$GITHUB_STEP_SUMMARY` cho CI.
- 9 bộ + `test_e2e.py` + `test_hang_doi_e2e.py`: thống nhất khuôn `KET QUA: N PASS / M FAIL`. `test_e2e.py` nay khai lý do bỏ qua thay vì im lặng `return 2`.

**Ba bộ kiểm mới canh giữ, để khiếm khuyết không quay lại:**

| Bộ | Canh gì |
|---|---|
| `tests/test_bo_may_kiem.py` (9 phép) | Kiểm chứng **ngược** chính `chay_het.py`: dựng bộ kiểm giả trong thư mục tạm, khẳng định cả chiều **đỏ** (vượt ngưỡng → mã thoát 1) lẫn chiều **xanh** (trong ngưỡng → 0), và lý do phải do bộ kiểm tự khai |
| `tests/test_khuon_mau_bo_kiem.py` (6 phép) | Không bộ mồ côi · không mục ma · mọi bộ in được `KET QUA:` · khuôn thống nhất |
| `tests/test_phu_file.py` (5 phép) | E-03: mọi `.py` ≥150 dòng phải có ≥1 bộ kiểm chạm tới |

**Hai cái bẫy vấp ngay khi viết `test_phu_file.py`** — ghi lại vì cùng họ với các lỗi đắt giá nhất của dự án:
1. Bộ này gom cả `tests/*.py` vào chuỗi tìm kiếm, mà **chính docstring của nó** nhắc tên file đang thiếu test để giải thích vấn đề. Kết quả: file không có bộ kiểm nào vẫn "được chạm tới" → **chốt tĩnh phát hiện lỗ hổng tự bịt mắt chính mình**, xanh 5/5 một cách vô nghĩa. Sửa: loại chính nó khỏi tập quét.
2. Tên file nằm trong **comment** không chứng minh được gì. Phải lọc comment/docstring bằng `tokenize` (không dùng regex — dấu `#` trong chuỗi không phải comment) và chỉ đọc dòng mã thực thi.

Đây đúng là điều mà phép thử đột biến ở `test_dung_do.py` đã dạy: **một bộ kiểm xanh chưa chứng minh được gì cho tới khi biết nó đỏ trong trường hợp nào.**

**Kết quả đo được:**
- Trước: `39/39 DAT` trong 83,1s — nhưng 113 phép kiểm vô hình và một file 553 dòng không ai canh.
- Sau: `42 bộ`, trong đó `PHU FILE` **ĐỎ** và nêu đích danh `ui/cua_so_hang_doi.py (553 dòng)`.

Bảng chuyển từ xanh sang đỏ **không phải vì có gì hỏng thêm**, mà vì bộ máy kiểm thử giờ mới nói thật. Lỗ hổng đã tồn tại suốt; trước đây chỉ là không ai tố cáo.

**Bước tiếp theo:** Giai đoạn 1 — viết `tests/test_cua_so_hang_doi.py` để đóng lỗ hổng mà `PHU FILE` vừa phơi bày.

### ISSUE-010 Lỗ hổng test lớn nhất — `ui/cua_so_hang_doi.py` (Giai đoạn 1)
**Ngày:** 2026-09-11 · **Trạng thái:** ĐÃ ĐÓNG

**Bối cảnh:** `tests/test_phu_file.py` (chốt tĩnh E-03 dựng ở ISSUE-009) nêu đích danh `ui/cua_so_hang_doi.py` — 553 dòng, 27 method — là file mã nguồn **duy nhất** từ 150 dòng trở lên không có bộ kiểm nào chạm tới. Nó lại là lớp giao diện viết gần đây nhất, và chính trong mã nguồn đã ghi lại **ba cái bẫy đã vấp**: đệ quy vô hạn khi thêm mục đầu tiên (dòng 66), `selection_set` nằm ngoài vùng khoá (dòng 318), biến phải khởi tạo trước `try` (dòng 489). Ba lỗi đó đã sửa — nhưng không có gì giữ chúng khỏi quay lại.

**Đã làm:** `tests/test_cua_so_hang_doi.py` — **57 phép kiểm**, chia **4 cụm**, mỗi cụm một tiến trình riêng.

| Cụm | Phủ |
|---|---|
| 1 — dựng cửa sổ + form | thêm mục không đệ quy · thiếu ô 1/ô 2 → cảnh báo · **sửa/bỏ mục ĐANG CHẠY bị từ chối** · đổi cấu hình xoá số liệu quét cũ · nối `;` không phải `,` · đổi `/`→`\` · `fixed_drives` ném vẫn dựng được |
| 2 — nhịp đập `_rut_tin` | giới hạn 200 tin/nhịp · **lỗi khi vẽ không giết nhịp đập vĩnh viễn** · lỗi ở dòng đầu không gây `NameError` trong `finally` · `<Destroy>` của widget con không huỷ nhịp · tạo/huỷ 3 lần stderr sạch |
| 3 — quét thử | `G=None` báo rõ không ném · ô 1 trống → cảnh báo · **chạy ở thread phụ, thread chính vẫn đập nhịp** · chống bấm chồng · **mục tạm không lọt vào hàng đợi** |
| 4 — trạng thái nút | **không nói "Xong." khi còn mục chờ** · `v_tomtat` khớp `mo_ta_tong_ket()` thật · đang chạy → nút Lưu xám, Dừng sáng · **đóng cửa sổ khi đang chạy phải hỏi trước** |

**Tách hạ tầng dùng chung:** `tests/tien_ich_tk.py` — `_GIU_TK`/`_nho` (chống `Tcl_AsyncDelete`), `co_tkinter`, `chay_con`, `thoat_an_toan`, `dem_pass_fail`. Trước đó các kỹ thuật này chỉ nằm trong `test_giao_dien.py`; bộ kiểm thứ hai chép lại nguyên khối sẽ vừa vi phạm nguyên tắc chống God Component, vừa có nguy cơ bản chép lệch dần — đúng cách mà bản chép `_lp` trong `xem_tien_trinh.py` đã hỏng âm thầm ba lần.

#### Phép thử đột biến — và bài học đắt nhất của giai đoạn này

57/57 xanh **ngay lần chạy đầu**. Kế hoạch đã ghi sẵn: *"nếu xanh hết ngay lần đầu → nghi test rỗng, review lại"*. Nên chạy `tests/cong_cu/dot_bien.py` (mới): **12 đột biến, 10 bị giết (83%), 2 sống sót.**

**Một trong hai con sống sót là lỗ hổng THẬT trong bộ kiểm** — và nó phơi bày đúng hình thái nguy hiểm nhất:

> Phép kiểm "thêm mục không đệ quy vô hạn" đếm số lần gọi `_ve_bang`/`_chon_muc` bằng cách gán `cs._chon_muc = <hàm đếm>` **sau khi** dựng cửa sổ. Nhưng dòng 134 làm `self.bang.bind("<<TreeviewSelect>>", self._chon_muc)` — Tk **chụp lại bound method ngay lúc dựng**. Gán sau đó thì Tk vẫn gọi bản gốc, bộ đếm luôn bằng 0, và phép kiểm đo một thứ **không bao giờ xảy ra**. Bản gốc và bản đã phá cho kết quả **giống hệt nhau**.

Đây đúng hình thái đã ghi ở `test_giao_dien.py:1536` (test long-path chạy trên đường dẫn không tồn tại → bản vá và bản chưa vá giống nhau). **Sửa:** vá vào **lớp** trước khi dựng cửa sổ, và thêm phép khẳng định tiền đề `HDUI-03c` — *`<<TreeviewSelect>>` thật sự gọi `_chon_muc`* — để lần sau nếu phép đo lại mất kết nối với thứ nó đo thì bộ kiểm đỏ ngay.

**Hai con sống sót cuối cùng là ĐỘT BIẾN TƯƠNG ĐƯƠNG, không phải lỗ hổng** — đã điều tra từng con bằng thực nghiệm, không đoán:

1. *Bỏ khởi tạo biến trước `try`*: `finally` có `try/except Exception` bọc bên trong nên `NameError` bị nuốt ngay tại chỗ, không quan sát được từ ngoài.
2. *Bỏ khoá `_dang_ve` quanh `selection_set`*: đệ quy **đã được chặn ở gốc** — `_chon_muc` không còn gọi `_ve_tat_ca()` (dòng 413-417) nên vòng lặp không còn tồn tại. Khoá ở dòng 320 là lớp phòng thủ **thứ hai, dư thừa**. Đo thật cả hai bản: `ve_bang=3/4, chon_muc=3/6` — giống hệt.

Kết luận đã ghi vào docstring của `test_cua_so_hang_doi.py` để người sau không mất công "sửa" một phép kiểm không hỏng. Nếu sau này `_chon_muc` được sửa để gọi lại `_ve_tat_ca()`, khoá dòng 320 trở lại thành phòng thủ thứ nhất và đột biến số 2 sẽ bị giết ngay.

**Một sự cố quy trình đáng ghi:** trong lúc điều tra, một đột biến **còn sót lại trong `ui/cua_so_hang_doi.py`** vì tiến trình bị ngắt giữa chừng trước khi `finally` kịp khôi phục. Phát hiện bằng `git diff` và khôi phục bằng `git checkout --`. Đã ghi cảnh báo vào docstring của công cụ: **luôn `git diff` sau khi chạy đột biến**.

**Kết quả đo được:**

| Mốc | Số bộ | Kết quả |
|---|---|---|
| Trước ISSUE-009 | 39 | `TAT CA DAT` 83,1s — nhưng 113 phép kiểm vô hình, 553 dòng không ai canh |
| Sau ISSUE-009 | 42 | **ĐỎ** — `PHU FILE` nêu đích danh lỗ hổng |
| Sau ISSUE-010 | **43** | `TAT CA DAT` 81,8s — xanh **thật**: lỗ hổng đã đóng, E-03 đạt |

**Bước tiếp theo:** Giai đoạn 2 — CI GitHub Actions.

### ISSUE-011 CI GitHub Actions — Giai đoạn 2
**Ngày:** 2026-09-11 · **Trạng thái:** ĐÃ DỰNG (chưa chạy thật trên GitHub — repo chưa push)

**Đóng một phần ISSUE-003.** Phần auto-update vẫn còn MỞ.

#### Phát hiện quan trọng: CI đơn giản hơn kế hoạch rất nhiều

Kế hoạch ban đầu dự kiến **ba workflow** (kiểm nhanh / kiểm đầy đủ / phát hành) và phải **cache 195 MB ffmpeg** cho CI. Trước khi viết, tôi đo thực nghiệm: giấu thư mục `ffmpeg/` đi rồi chạy lại toàn bộ.

**Kết quả: 43/43 bộ ĐẠT, 0 bỏ qua, 79 giây** — sau khi sửa 3 bộ (xem dưới).

Các bộ E2E tự tìm ffmpeg và có đường lui đàng hoàng. Vậy **không cần tách workflow, không cần cài ffmpeg trong CI**. Một job, một file, 20 phút timeout. Thêm bước cài ffmpeg chỉ làm chậm và thêm một điểm hỏng.

> Bài học: **đo trước khi thiết kế.** Kế hoạch dựa trên `grep "ffmpeg"` cho ra 20 file "phụ thuộc ffmpeg"; đo thật thì chỉ 3 file thật sự cần, và cả 3 chỉ cần ở vài phép kiểm lẻ.

#### Ba bộ thất bại trên runner sạch — và cách sửa

| Bộ | Phép kiểm hỏng | Vì sao |
|---|---|---|
| `test_dong_goi.py` | "dùng bản ffmpeg ĐI KÈM, không phải bản trong PATH" | Đòi `ffmpeg/bin/ffmpeg.exe` tồn tại |
| `test_phien_ban.py` | "tìm được `ffmpeg/bin/ffmpeg.exe`" | Như trên |
| `test_lan_dau.py` | "tự kiểm ĐẠT trên bản thật" | Tự kiểm có bước "kiểm đủ file sau khi giải nén" — đòi ffmpeg |

Cả ba thất bại với **mã 1 (THẤT BẠI)** chứ không phải mã 2 (bỏ qua có lý do) → CI sẽ **đỏ oan**, đúng rủi ro **R-05**.

**Cách sửa — giữ nguyên sức mạnh trên máy dev:** bọc điều kiện `(ROOT/"ffmpeg"/"bin"/"ffmpeg.exe").is_file()` quanh **đúng phép kiểm cần ffmpeg**, không phải cả bộ. Khi thiếu thì in dòng nói rõ đang bỏ qua cái gì và vì sao. `test_lan_dau.py` còn nêu đích danh **bước nào hỏng** (`['Kiem du file sau khi giai nen']`) thay vì im lặng.

Kiểm chứng **cả hai chiều** — số phép kiểm không hề giảm trên máy dev:

| Bộ | Có ffmpeg | Không ffmpeg |
|---|---|---|
| `test_dong_goi` | 15 PASS (trước: 14+1 FAIL) | 13 PASS, nói rõ bỏ qua gì |
| `test_phien_ban` | 22 PASS (trước: 21+1 FAIL) | 21 PASS, nói rõ |
| `test_lan_dau` | 38 PASS (trước: 36+2 FAIL) | 38 PASS, nêu bước hỏng |

**Một lỗi của chính tôi khi sửa:** đoán khoá dict là `x["ten"]` trong khi `tu_kiem_lan_dau.py:180` dùng `x["buoc"]` → `KeyError` chỉ nổ trên nhánh không-ffmpeg. Bắt được vì đã kiểm chứng **cả hai chiều** thay vì chỉ chiều thuận. Nếu chỉ chạy trên máy dev (có ffmpeg) thì lỗi này sẽ ngủ yên tới khi CI chạy thật.

#### `.github/workflows/kiem_nhanh.yml`

- `windows-latest` **only**. Chạy Linux sẽ đỏ hàng loạt vì backslash và `_lp()` — R-05.
- Matrix Python **3.14** (bản đi kèm repo, bản người dùng chạy) và **3.8** (ngưỡng tối thiểu tuyên bố ở `BAN_GIAO.md`). Đã quét AST xác nhận không dùng cú pháp/API nào mới hơn 3.8.
- **`MAX_BO_QUA: "0"`** — trên runner sạch hiện không bộ nào được phép bỏ qua. Nếu một ngày có bộ bắt đầu bỏ qua, CI đỏ và bắt phải giải thích, thay vì lặng lẽ tụt số bộ chạy thật.
- `concurrency` huỷ lần chạy cũ khi có push mới; upload `_BAO_CAO_THIEU.txt` + `_LOI_GIAO_DIEN.log` khi thất bại.

#### Kiểm chứng ngược — cổng CI đã được CHỨNG MINH

*Một CI chưa từng đỏ là một CI chưa được chứng minh.* Công cụ mới `tests/cong_cu/kiem_chung_nguoc.py` phá code thật ở **7 tầng khác nhau** rồi khẳng định bộ kiểm mong đợi phải đỏ:

| Phá gì | Bộ phải đỏ | Kết quả |
|---|---|---|
| `_lp()` bỏ prefix UNC | `test_duong_dan` | ✓ bắt |
| `_lp()` không thêm prefix | `test_duong_dan` | ✓ bắt |
| `TraLoi` đoán bừa câu hỏi lạ | `test_cau_noi` | ✓ bắt |
| Bỏ chặn `"D:"` drive-relative | `test_kiem_dau_vao` | ✓ bắt |
| Một mục LỖI làm dừng cả hàng đợi | `test_hang_doi_ui` | ✓ bắt |
| Bỏ giới hạn 200 tin/nhịp | `test_cua_so_hang_doi` | ✓ bắt |
| **`chay_het.py` luôn báo thành công** | `test_bo_may_kiem` | **✗ KHÔNG BẮT ĐƯỢC** |

**Lỗ hổng thật, và ở chỗ nguy hiểm nhất.** `test_bo_may_kiem.py` copy `chay_het.py` sang thư mục tạm rồi chạy các bộ kiểm **giả** — nhưng mọi bộ giả đều ĐẠT hoặc BỎ QUA, **không bộ nào THẤT BẠI**. Nên nhánh `if hong:` — nhánh quan trọng nhất của cả cổng CI — chưa bao giờ được chạy.

Đã thêm 4 phép kiểm cho nhánh đó (bộ giả cố ý thất bại → mã thoát phải là 1, không được in "TAT CA DAT", phải nói rõ số bộ không đạt, không được đếm nhầm thành BỎ QUA). Sau khi thêm: **7/7 bắt được**.

**Một tác dụng phụ đã sửa:** công cụ khôi phục file bằng `write_text()` làm đổi line-ending (LF↔CRLF) → `git diff` báo cả file "đã đổi" dù nội dung y hệt, gây nhiễu khi soát về sau. Chuyển sang `read_bytes()`/`write_bytes()`. Đã kiểm: trạng thái `git status` trước và sau khi chạy công cụ **giống hệt nhau**.

#### Trạng thái sau GĐ2

- 43/43 ĐẠT trên máy dev (80,9s) và với `MAX_BO_QUA=0` (81,9s).
- 43/43 ĐẠT trên runner sạch mô phỏng (không ffmpeg).
- Cổng CI đã chứng minh bắt được lỗi ở 7 tầng.
- **Còn lại:** workflow chưa chạy thật trên GitHub vì repo chưa push. Đây là điều duy nhất chưa kiểm chứng được tại chỗ — phải xác nhận sau lần push đầu.

**Bước tiếp theo:** Giai đoạn 4 (verifier độc lập) — theo thứ tự ưu tiên của kế hoạch, nó đứng trước GĐ3 vì trả lời câu hỏi "gói này có dùng được không?".

### ISSUE-012 Verifier độc lập — bù cho "phép thử vàng" (Giai đoạn 4)
**Ngày:** 2026-09-11 · **Trạng thái:** ĐÃ DỰNG · **Tiêu chí E-11 đạt**

**Vấn đề gốc:** mọi bộ kiểm E2E hiện có đều hỏi *"tool báo đúng số file chưa?"* — tức là **để tool tự chấm bài mình**. `test_e2e.py` dùng `G.iter_json_files`, `G.deep_walk_strings`, `G.is_real_abs` — hàm của chính tool. Nếu tool hiểu sai định dạng CapCut, nó sẽ ghi sai theo đúng cái hiểu sai đó, rồi tự kiểm lại bằng chính hàm đã hiểu sai, và báo ĐẠT.

Checklist `bug.md` nói thẳng: *"Verifier nghiệm thu nên viết ĐỘC LẬP, không import hàm của tool — dùng lại chính hàm bị lỗi thì lỗi không bao giờ lộ."* Và vì không có CapCut để chạy "phép thử vàng", đây là thứ **duy nhất** trả lời được câu *"gói này có dùng được không?"*

#### `tests/nghiem_thu_goi.py` — 4 tiêu chí

Viết **từ đầu, không import `goi_project_capcut` / `chung` / `toi_uu_dung_luong`** — kể cả `_lp()` cũng viết lại bản riêng, vì dùng chung một hàm thì một lỗi trong hàm đó làm **cả hai cùng mù**.

| Tiêu chí | Nội dung | Vì sao CapCut quan tâm |
|---|---|---|
| **V-1** | 0 đường dẫn tuyệt đối sót trong mọi `.json` | Đường tuyệt đối = trỏ về máy cũ = clip mất khi sang máy khác. **Lý do tồn tại của cả tool** |
| **V-2** | 100% tham chiếu phân giải được, kích thước > 0 | Clip trắng trong CapCut |
| **V-3** | Đệ quy đủ mọi cấp subdraft | Media subdraft bị bỏ sót |
| **V-4** | Mọi `.json` parse được sau khi tool ghi lại | CapCut từ chối mở draft JSON hỏng |

Có xử lý đúng ba thứ tinh tế của định dạng CapCut, **suy ra độc lập từ tài liệu chứ không chép hằng số của tool**: lọc theo **tên khoá** (`path`, `file_Path`, `source_path`…) chứ không theo đuôi file — vì `material_name`/`extra_info` chỉ là nhãn (bug #24); giải placeholder theo **draft root gần nhất tính ngược lên** (đo trên 8650 đường dẫn thật: đúng 99,9% so với 85,1%); bỏ qua tham chiếu trong file cache CapCut tự sinh (`mini_draft`, `draft_agency_*`) để không báo động giả.

#### `tests/test_nghiem_thu.py` — kiểm chính verifier (21 phép)

*Verifier báo ĐẠT chưa chứng minh được gì.* Một verifier luôn trả ĐẠT cũng báo ĐẠT trên mọi gói — và nguy hiểm **hơn** là không có verifier, vì nó tạo cảm giác an toàn giả.

Dựng **5 kiểu gói cố ý hỏng**, verifier phải đỏ **đúng loại**: đường dẫn tuyệt đối Windows · đường dẫn UNC · file bị thiếu · file 0 byte · JSON hỏng. Cộng 3 phép chống **báo động giả**: tham chiếu hỏng trong `mini_draft` không được làm đỏ · `material_name`/`extra_info` không bị coi là đường dẫn · gói lành phải xanh. Và 1 chốt tĩnh: verifier **không được import** module nào của tool.

Thêm phép "gói rỗng": quét 0 tham chiếu thì **không được kết luận ĐẠT** (bug #36 — *quét 0 file mà báo PASS là lỗi nặng hơn báo FAIL sai*). Đã sửa cả **thứ tự in**: bản đầu in "GOI TU CHUA" rồi mới cảnh báo chưa kiểm được gì — người đọc chỉ nhớ dòng kết luận đầu tiên.

#### Gắn vào E2E + phép thử DI CHUYỂN

`test_e2e.py` từ 34 → **42 phép**: 6 phép V-1..V-4 chạy **song song** với các phép cũ (không thay thế — hai góc nhìn độc lập tốt hơn một), cộng 2 phép **di chuyển gói**: copy sang chỗ khác rồi nghiệm thu lại.

Mở gói tại chỗ cũ **không chứng minh được gì** — đường dẫn tuyệt đối cũ vẫn resolve được trên chính máy đó (checklist `bug.md`). Phép di chuyển mô phỏng đúng kịch bản bàn giao thật, không cần CapCut.

#### Bằng chứng E-11 có giá trị thật

Thêm vào `kiem_chung_nguoc.py` phép quan trọng nhất: **phá `deep_rewrite_strings` trong `chung.py`** (bỏ hẳn việc viết lại đường dẫn — lỗi duy nhất làm gói mất tác dụng hoàn toàn). Kết quả: verifier độc lập **bắt được**:

```
FAIL  V-1 khong con duong dan TUYET DOI trong goi
FAIL  DI CHUYEN: goi van TU CHUA sau khi doi cho
```

Kiểm chứng ngược nay **8/8**.

#### Sự cố quy trình — và bài học lặp lại lần thứ tư

1. **`git checkout -- tests/test_e2e.py`** để khôi phục trước khi vá lại đã **xoá luôn hai sửa của GĐ0** (khuôn `KET QUA:` và khai lý do `BO QUA:`). Phát hiện bằng `grep` ngay sau đó và khôi phục. Bài học: `git checkout` khôi phục về **HEAD**, không phải về "trạng thái vài phút trước".
2. **Heredoc bash nuốt một lớp escape `\n`** — hỏng 3 lần liên tiếp khi vá chuỗi Python có `\n` bên trong. Checklist `bug.md` đã cảnh báo đúng chuyện này (*"cẩn thận khi test path Windows qua bash — dùng file test Python"*), tôi vẫn vấp. Từ đó chuyển hẳn sang viết script vào scratchpad.
3. **`shutil.copy('/tmp/chung_goc.py', ...)` từ Python thất bại** vì `/tmp` của Git Bash không phải đường dẫn Windows — làm `chung.py` **đứng nguyên ở trạng thái bị phá** một lúc. Khôi phục bằng `git checkout`. Nhắc lại quy tắc: sau mọi phép phá code, **luôn `git status` trước khi làm tiếp**.

#### Trạng thái

- **44/44 ĐẠT**, 80,3s. File nguồn sạch.
- E-11 đạt: 0 đường dẫn tuyệt đối sót, 100% tham chiếu phân giải được, kể cả sau khi di chuyển gói.
- **Vẫn còn thiếu (nói rõ thay vì giấu):** verifier kiểm được *"gói có tự chứa không"*, **không** kiểm được ngữ nghĩa riêng của CapCut (CapCut đòi một khoá metadata tool vô tình xoá; từ chối codec mà ffprobe chấp nhận). Chỉ người thật mở bằng CapCut thật mới bắt được — **`UAT-G*` không thể bỏ**, nhưng nhờ verifier nó chỉ cần chạy 1 lần/release thay vì mỗi lần sửa code.

### ISSUE-013 Đường ghép UI + hai luồng song song (Giai đoạn 3)
**Ngày:** 2026-09-11 · **Trạng thái:** ĐÃ ĐÓNG

Hai lỗ hổng nằm ở **chỗ nối** chứ không trong một module nào — nên các bộ kiểm đơn lẻ không chạm tới.

**`tests/test_duong_ghep_ui.py` — 26 phép, 2 cụm:**

| Cụm | Phủ |
|---|---|
| Đường ghép `_mo_hang_doi()` | Chụp tùy chọn mục 4 **trên thread chính** · là `Toplevel` riêng, cửa sổ chính vẫn sống · `G`/`fixed_drives` được **truyền vào** · bấm lần hai thì `lift()` không tạo cửa thứ hai · đóng rồi mở lại được · **thiếu `ui/` → `showerror` hướng dẫn, không traceback** |
| Hai luồng song song | Mở hàng đợi **trong lúc** cửa sổ chính đang QUÉT · thread chính vẫn đập nhịp khi **cả hai** đang chạy · **hai cờ huỷ độc lập** (dừng bên này không chạm bên kia) · `sys.stdout` được trả lại, không bị `Ong` nào giữ · hai nơi dùng **hai kho nhật ký khác nhau** |

**Kết quả quan trọng:** lo ngại ban đầu (hai `Ong` tranh nhau `sys.stdout` → nhật ký lẫn nhau) **không xảy ra** — kiến trúc hiện tại đã tách đúng. Không cần thêm phép kiểm thứ 11 vào SPEC §8 như kế hoạch đề phòng.

**Một bài học về phép đột biến:** phép "không chụp tùy chọn mục 4" **sống sót giả tạo**. Mốc `"scale": bool(self.v_scale.get()),` xuất hiện ở **cả hai** chỗ (`_bat_dau` dòng 571 và `_mo_hang_doi` dòng 663), mà `replace(cu, moi, 1)` thay chỗ **đầu tiên** → phá nhầm `_bat_dau`, trong khi phép kiểm canh `_mo_hang_doi`. Đột biến chưa bao giờ chạm vào chỗ cần phá. **Mốc đột biến phải DUY NHẤT trong file** — nếu không, lấy thêm ngữ cảnh cho tới khi duy nhất.

---

### ISSUE-014 Đóng gói .exe — R-08, R-09 (Giai đoạn 5)
**Ngày:** 2026-09-11 · **Trạng thái:** ĐÃ DỰNG (chưa build thật — PyInstaller chưa cài)

**`tests/test_dong_goi_exe.py` — 26 phép.** Bổ sung phần `test_phien_ban.py` chưa phủ:

- **R-09:** `thu_muc_ghi()` lùi về `%LOCALAPPDATA%` khi cạnh .exe chỉ đọc; lùi tiếp về temp khi **cả** `%LOCALAPPDATA%` cũng hỏng; thiếu hẳn biến môi trường vẫn có đường lui — và **không bao giờ ném**.
- **Chốt tĩnh:** `_ghi_duoc()` phải thử **ghi thật** (không `os.access` — nó trả kết quả sai trên Windows vì không tính UAC virtualization); ba khái niệm thư mục không được gộp thành một `_GOC`.
- **BLD-07:** mọi `.bat` không có byte > 127 (`cmd.exe` diễn giải comment theo code page **trước khi** `chcp 65001` kịp chạy — bug #12).

**`dong_goi/goi_exe.spec` + `dong_goi/build.py`** — viết **sau** khi hợp đồng BLD-01..08 đã chốt. `build.py` chạy 5 bước, dừng ngay tại bước đầu tiên hỏng: chạy bộ kiểm **trước** khi đóng gói → kiểm tài nguyên (thiếu `ffmpeg/` thì **nói rõ** thay vì lặng lẽ đóng gói bản mà chế độ 4 không chạy) → PyInstaller → kiểm bản build (ffmpeg phải **chạy được** chứ không chỉ tồn tại) → chạy lại bộ kiểm **bằng Python đi kèm**.

Đã chạy thử: `build.py` dừng ở bước 3 với thông báo rõ ràng vì PyInstaller chưa cài. **Cần chủ dự án duyệt** trước khi cài (mục #1 trong kế hoạch: PyInstaller là dependency *build*, không phải *chạy*).

**Chốt tĩnh có sẵn đã bắt được lỗi của tôi:** `test_dung_do.py` canh "mọi bộ kiểm nạp module trong `tests/` phải thêm `HERE` vào `sys.path`" — bộ mới của tôi thiếu dòng đó. Bản Python đi kèm dùng `._pth` nên không tự thêm thư mục script; lỗi này sẽ chỉ nổ **trên máy người dùng**.

---

### ISSUE-015 Auto-update — R-02, R-03, R-10, R-14 (Giai đoạn 6)
**Ngày:** 2026-09-11 · **Trạng thái:** ĐÃ DỰNG · **Tiêu chí E-09 đạt**

**Quy trình: test viết TRƯỚC, code viết SAU.** Với 4 rủi ro mức Cao và hậu quả 40–50 máy cùng lúc, "code trước test sau" là công thức hỏng hàng loạt.

`tests/test_cap_nhat.py` chốt hợp đồng **24 ràng buộc / 4 nhóm** khi `loi/cap_nhat.py` chưa tồn tại, in ra đầy đủ và tự khai là "trạng thái ĐÚNG" — không phải bỏ qua im lặng. Hợp đồng mô tả **hành vi quan sát được** ("ngắt giữa chừng phải còn một bản mở được"), không mô tả cách cài đặt — để không khoá cứng một thiết kế chưa kiểm chứng.

**`loi/cap_nhat.py`** viết sau, thoả hợp đồng. **43 phép kiểm, 43 đạt.**

| Nhóm | Kết quả |
|---|---|
| **R-10** không chặn khởi động | 9 phép: mất mạng · DNS hỏng · 403/rate-limit · 500 · JSON rác · rỗng · hết giờ → **tất cả trả `None`, không ném**. Có bản mới thật thì trả đúng; server có bản **cũ hơn** → `None` (không tự hạ cấp) |
| **So sánh phiên bản** | `1.10.0 > 1.9.0` (không so chuỗi) · `1.2.0-beta` không mới hơn `1.2.0` · chuỗi dị dạng không ném |
| **R-02** chặn khi đang gói | Chặn ở **tầng API** chứ không chỉ làm xám nút · hàng đợi chạy cũng chặn · **0 file bị chạm tới** khi bị chặn |
| **R-14/R-03** nguyên tử | SHA256 sai → huỷ, bản cũ nguyên vẹn · thiếu file / file rỗng → huỷ · giữ đúng **1** bản cũ · `phuc_hoi()` về đúng bản cũ |

**Bằng chứng trực tiếp cho R-14** — ngắt ở **mọi** lần đổi tên:

```
ngat o lan 1 -> CU | ngat o lan 2 -> CU | ngat o lan 3 -> MOI | ngat o lan 4 -> MOI
```

Không bao giờ có trạng thái thứ ba. Cơ chế: cả hai bước đều là **đổi tên thư mục** — nguyên tử ở mức hệ thống tệp.

#### Phép thử đột biến bắt được một lỗ hổng thật

Thêm 5 phép đột biến cho auto-update: **2 sống sót**, điều tra từng cái bằng thực nghiệm:

- **"So sánh chuỗi"** — đột biến **tương đương**: `str((1,10,0)) != str((1,9,0))` vẫn khác nhau nên `!=` vẫn đúng. Đã đổi mốc sang `return so_a > so_b` → bắt được.
- **"Không đưa bản cũ trở lại khi bước 5 hỏng"** — **lỗ hổng thật**. Bản gốc: ngắt lần 2 → `ap_ban_moi` **tự** đưa bản cũ về, người dùng không thấy gì bất thường. Bản phá: ngắt lần 2 → thư mục **trống**, phải gọi `phuc_hoi()` thủ công. Bộ kiểm cũ gọi `phuc_hoi()` ngay nên **che mất khác biệt** — cả hai đều "còn một bản hoàn chỉnh".

  Khác biệt này quan trọng: nếu tiến trình **chết hẳn** (mất điện) thì không ai gọi `phuc_hoi()` được, và người dùng mở lên thấy **một thư mục trống**. Đã thêm **CN-33b** phân biệt "tự khôi phục" với "phải cứu thủ công".

Kiểm chứng ngược nay **16/16**.

---

### Trạng thái chung sau 6 giai đoạn (0,1,2,3,4,5,6)

| | |
|---|---|
| Bộ kiểm | **47** (ban đầu 39) |
| Máy dev | 47/47 ĐẠT, 83,7s |
| Runner sạch (không ffmpeg) | **47/47 ĐẠT, 0 bỏ qua** |
| Kiểm chứng ngược | **16/16** — phá ở 16 tầng đều bị bắt |
| Tiêu chí đạt | E-01, E-02, E-03, E-09, E-11 |

**Còn lại:** workflow chưa chạy thật trên GitHub (chưa push) · chưa build .exe thật (PyInstaller cần duyệt) · `UAT-*` cần máy thật và người thật · phép thử vàng cần người có CapCut.
