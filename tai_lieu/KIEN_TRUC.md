# KIẾN TRÚC — bản đồ module & kế hoạch tách God Component

> **Trạng thái:** Bản 1.0 — khảo sát ngày 2026-09-10.
> Nguyên tắc chủ dự án: chia nhỏ code thành module/component/folder là **"nguyên tắc sống còn"**, **"yếu tố đặc biệt cần phải tuân thủ"**.

---

## 1. Hiện trạng đo được

Đo bằng `wc -l`, ngày 2026-09-10:

| File | Dòng | Đánh giá |
|---|---|---|
| `goi_project_capcut.py` | 1895 | **God Component** — chứa một hàm 913 dòng |
| `toi_uu_dung_luong.py` | 1401 | **Rất lớn** — nhưng ranh giới rõ, dễ tách |
| `giao_dien.py` | 987 | **God Component** — một class 750 dòng |
| `canh_gac.py` | 534 | Lớn nhưng **tự chứa, một trách nhiệm** — không cần tách |
| `chung.py` | 462 | **Đã tách tốt** — thư viện tiện ích dùng chung |
| `tu_kiem_lan_dau.py` | 173 | OK |
| `xem_tien_trinh.py` | 112 | OK |
| **Tổng** | **5564** | |

### Nhận định quan trọng

**Không phải file nào lớn cũng là God Component.** `canh_gac.py` (534 dòng) làm đúng **một việc** — canh gác tiến trình treo — và tự chứa; tách nó ra chỉ tạo thêm file mà không giảm độ phức tạp. `chung.py` cũng vậy: nó *là* kết quả của một lần tách tốt.

Vấn đề thật nằm ở **hai chỗ**, đều là "một đơn vị code ôm nhiều trách nhiệm không liên quan":

1. `_main_than()` — **913 dòng, 12 pha tuần tự** trong một hàm.
2. `GiaoDien` — **750 dòng, một class** ôm cả dựng layout, kiểm đầu vào, điều phối thread, dịch câu hỏi, bơm hàng đợi.

---

## 2. Sơ đồ phụ thuộc hiện tại

```
                       ┌──────────────┐
                       │  chung.py    │  ← nền: path an toàn, JSON, cấu hình, ổ đĩa
                       └──────┬───────┘
                              │ (mọi module đều dùng)
        ┌─────────────────────┼──────────────────────┐
        │                     │                      │
┌───────▼────────┐  ┌─────────▼─────────┐  ┌─────────▼────────┐
│ toi_uu_dung_   │  │ goi_project_      │  │ canh_gac.py      │
│ luong.py       │◄─┤ capcut.py         ├─►│ (đo treo)        │
│ (ffmpeg)       │  │  = main() + thân  │  └──────────────────┘
└────────────────┘  └─────────┬─────────┘
                              │ lái qua builtins.input + sys.stdout
                    ┌─────────▼─────────┐   ┌──────────────────┐
                    │  giao_dien.py     ├──►│ tu_kiem_lan_dau  │
                    └───────────────────┘   └──────────────────┘

                    xem_tien_trinh.py  (độc lập, chỉ đo thư mục)
```

**Ràng buộc bất khả xâm phạm:** mũi tên `giao_dien → goi_project_capcut` là **lái qua `builtins.input`**, không phải gọi hàm con. Xem `SPEC_UI_UX.md` §1. Tách module **không được** biến nó thành lời gọi hàm trực tiếp.

---

## 3. Mổ xẻ `_main_than()` — 913 dòng, 12 pha

Đọc từ code (số dòng tương đối trong hàm):

| # | Pha | Dòng | Trách nhiệm |
|---|---|---|---|
| 1 | Mốc huỷ | 8–33 | thiết lập cơ chế huỷ |
| 2 | Canh gác | 35–58 | khởi động watchdog |
| 3 | Báo "dự án con" | 73–99 | thông báo người dùng |
| 4 | Chặn 1: đưa về tuyệt đối | 100–105 | kiểm đầu vào (bug #23) |
| 5 | Chặn 2: đích không trùng/nằm trong gốc | 106–126 | kiểm đầu vào |
| 6 | Chọn chế độ gói | 127–164 | hỏi người dùng |
| 7 | Liệt kê media (quét đệ quy JSON) | 165–212 | thu thập |
| 8 | Resolve: theo path → theo tên | 213–348 | **dò tìm — 135 dòng** |
| 9 | Tính trước file bị thay (nếu bật tối ưu) | 349–387 | lập kế hoạch |
| 10 | Copy folder draft + ghi 3 JSON gốc | 388–430 | copy |
| 11 | Tối ưu dung lượng | 431–464 | gọi `toi_uu_dung_luong` |
| 12 | Kế hoạch viết lại JSON | 465–483 | lập kế hoạch |
| 13 | Copy media (dedupe bằng hard link) | 484–562 | copy |
| 14 | Áp dụng viết lại (chỉ khi file đích CÓ THẬT) | 563–597 | viết |
| 15 | Bỏ file thừa | 598–652 | dọn |
| 16 | **Tự kiểm trên bản xuất** | 653–896 | **kiểm chứng — 243 dòng** |

Hai khối lớn nhất — **dò theo tên (135 dòng)** và **tự kiểm bản xuất (243 dòng)** — chiếm 41% thân hàm và có ranh giới rất rõ.

---

## 4. Cấu trúc module đích

```
loi/                       ← lõi nghiệp vụ, KHÔNG biết gì về giao diện
    __init__.py
    duong_dan.py           ← từ chung.py: _lp, _unlp, _np, isfile_safe, isdir_safe...
    json_io.py             ← từ chung.py: read/write_json_loose, deep_walk/rewrite
    cau_hinh.py            ← từ chung.py: doc_cau_hinh, CAU_HINH_MAC_DINH
    o_dia.py               ← từ chung.py: fixed_drives, la_o_mang, mo_ta_moi_truong
    phien_ban.py           ← MỚI: TOOL_VERSION + xác định thư mục gốc (quan trọng cho .exe)

goi/                       ← luồng gói, tách từ _main_than()
    __init__.py
    tim_draft.py           ← capcut_roots, is_draft_dir, scan_drafts_recursive,
                             scan_subprojects, list_drafts, choose_draft
    thu_thap.py            ← collect_refs, _new_path_forms, _pick_form
    do_theo_ten.py         ← index_by_names + pha 8 (135 dòng)
    ke_hoach.py            ← plan_package
    thuc_thi.py            ← pha 10, 13, 14 (copy + viết lại)
    kiem_chung.py          ← verify_package + pha 16 (243 dòng)
    duong_dan_dai.py       ← scan_long_paths, phan_loai_path_dai
    dieu_phoi.py           ← _main_than() rút gọn: chỉ GỌI các pha theo thứ tự

toi_uu/                    ← tách từ toi_uu_dung_luong.py
    __init__.py
    ffmpeg_cli.py          ← ff_paths, _run, kiem_ffmpeg_chay_duoc, ff_version, probe
    quyet_dinh.py          ← collect_jobs, plan_replacements (LOGIC quyết định cắt/hạ)
    ma_lai.py              ← encode_job
    chi_muc.py             ← _load/_save_opt_index
    don_dep.py             ← cleanup_unused, kiem_ban_goc_thua, prune_registry
    so_do.py               ← repoint_registry
    kiem_chung.py          ← verify_optimize

ui/                        ← tách từ giao_dien.py
    __init__.py
    ung_dung.py            ← main(), _dat_theme, khởi tạo root
    cua_so_chinh.py        ← lắp ráp các khối, giữ trạng thái — MỎNG
    khoi/
        khoi_chon_project.py
        khoi_folder_xuat.py
        khoi_do_theo_ten.py
        khoi_toi_uu.py
        khoi_dieu_khien.py     ← 3 nút + nhãn trạng thái
        khoi_nhat_ky.py
    tu_kiem.py             ← CuaSoTuKiem
    cau_noi.py             ← Ong + _tra_loi  ← TIM CỦA KIẾN TRÚC, xem §5
    kiem_dau_vao.py        ← 10 phép kiểm ở SPEC §8
    bom_hang_doi.py        ← _rut_hang_doi
    tien_ich_tk.py         ← menu chuột phải, _cuon_ve_cuoi, _chon_thu_muc

capnhat/                   ← MỚI, cho yêu cầu auto-update
    __init__.py
    kiem_phien_ban.py
    tai_ve.py
    cai_dat.py

canh_gac.py                ← GIỮ NGUYÊN, đã tự chứa
tu_kiem_lan_dau.py         ← GIỮ NGUYÊN
xem_tien_trinh.py          ← GIỮ NGUYÊN
tests/
tai_lieu/
```

---

## 5. `ui/cau_noi.py` — module quan trọng nhất

Chứa `Ong` (chuyển `sys.stdout` thành dòng hàng đợi) và `_tra_loi` (dịch câu hỏi thành đáp án từ form). **Đây là toàn bộ khớp nối giữa giao diện và lõi.**

Tách riêng vì ba lý do:

1. Nó là nơi **dễ sai nhất** và hậu quả nặng nhất — trả lời sai một câu hỏi lạ có thể xoá nhầm dữ liệu.
2. Nó là nơi **duy nhất** cần sửa khi lõi thêm/bớt câu hỏi. Nằm lẫn trong class 750 dòng thì không ai tìm ra.
3. Nó **kiểm thử được không cần tkinter** — đưa vào một bản chụp form, đưa vào một câu hỏi, so đáp án. Hiện tại muốn test phải dựng cả cửa sổ.

Điểm 3 là lý do mạnh nhất: nó biến phần rủi ro cao nhất của UI thành phần **duy nhất trong UI có thể test tự động trong CI**.

---

## 6. Quy ước bắt buộc

1. Thêm tính năng → **tạo module mới**, KHÔNG nối thêm vào file lớn sẵn có.
2. Buộc phải sửa trong file lớn → cân nhắc tách phần liên quan **trước** khi sửa.
3. Tách theo **trách nhiệm**, không theo dung lượng. Một file 500 dòng làm đúng một việc thì để yên (`canh_gac.py`).
4. `loi/` và `goi/` **không được import gì từ `ui/`**. Chiều phụ thuộc chỉ đi một hướng.
5. Chỉ dùng **thư viện chuẩn Python** (theo `CLAUDE.md`).
6. **Tách tới đâu, test tới đó** — chạy `python tests\chay_het.py` trước và sau mỗi lần tách.

---

## 7. Thứ tự tách — từ an toàn nhất đến rủi ro nhất

Chủ dự án yêu cầu **mọi tính năng phải chạy ổn định như ban đầu**. Vì vậy tách theo thứ tự rủi ro tăng dần, mỗi bước xong là verify:

| Bước | Việc | Rủi ro | Vì sao xếp ở đây |
|---|---|---|---|
| 1 | ~~`loi/phien_ban.py`~~ | — | ✅ **XONG 2026-09-10** — 22 phép kiểm, sửa luôn R-08 + R-09 |
| 2 | ~~Tách `chung.py` → `loi/`~~ | — | **ĐÃ BỎ 2026-09-10** — xem §7.1 |
| 3 | Tách `toi_uu_dung_luong.py` → `toi_uu/` | Thấp–TB | Ranh giới rõ (ffmpeg / quyết định / dọn dẹp) |
| 4 | ~~Tách `ui/cau_noi.py` + `ui/kiem_dau_vao.py`~~ | — | ✅ **XONG 2026-09-10** — 27 + 34 phép kiểm, chạy 0,1s không cần tkinter |
| 5 | Tách `ui/khoi/*` | Trung bình | Cẩn thận `master=` (SPEC §6.6) |
| 6 | Tách pha 16 → `goi/kiem_chung.py` | Trung bình | 243 dòng, ranh giới rõ nhất trong `_main_than` |
| 7 | Tách pha 8 → `goi/do_theo_ten.py` | Trung bình | 135 dòng |
| 8 | Tách các pha còn lại → `goi/` | **Cao** | Nhiều trạng thái chung; làm cuối cùng |
| 9 | Thêm `capnhat/` | Thấp | Code mới |

**Bước 8 là nguy hiểm nhất.** 12 pha trong `_main_than` chia sẻ rất nhiều biến trung gian; tách vội sẽ sinh ra hàng chục tham số hoặc một object trạng thái khổng lồ — God Component đội lốt khác. Trước khi làm bước 8 phải **lập bảng biến nào sống qua những pha nào**, và bảng đó ghi vào tài liệu này.

---

### 7.1 Vì sao BỎ bước tách `chung.py` (quyết định 2026-09-10)

Kế hoạch ban đầu định tách `chung.py` (462 dòng) thành `loi/duong_dan.py`, `loi/json_io.py`, `loi/cau_hinh.py`, `loi/o_dia.py`. **Đã bỏ sau khi đọc kỹ file.**

Lý do:

1. **`chung.py` chính là kết quả của một lần tách tốt.** Docstring của nó ghi rõ nó sinh ra để diệt ba vấn đề cùng lúc: phụ thuộc vòng tròn giữa `goi_project_capcut.py` và `toi_uu_dung_luong.py`, bản chép `_lp()` trong `xem_tien_trinh.py` (hàm đã phải sửa 3 lần — #1, #23, #34 — bản chép không sửa theo là hỏng âm thầm trên UNC), và hack trả `sys.modules` (#48).

2. **Nó đã có quy tắc tự giữ mình:** *"file này chỉ chứa hàm THUẦN và hằng số. KHÔNG chứa trạng thái, KHÔNG import ngược lên hai file kia."* Một file 462 dòng có kỷ luật rõ như vậy không phải God Component.

3. **Chi phí tách rất cao, lợi ích gần bằng không.** `chung.py` được import ở **15 chỗ**, trong đó **8 file test**. Tách ra là chạm hết 15 chỗ, đổi lấy việc chia một file đang gọn gàng thành bốn file nhỏ.

4. **Rủi ro thật:** `_lp()` là hàm nhạy cảm nhất của cả tool (long-path, UNC). Di chuyển nó là đúng loại thay đổi mà `bug.md` cảnh báo nhiều nhất.

**Bài học rút ra cho các bước sau:** *"chia nhỏ module"* không có nghĩa là *"mọi file đều phải nhỏ"*. Tiêu chí là **một file có ôm nhiều trách nhiệm không liên quan hay không** — `chung.py` và `canh_gac.py` đều không. Hai God Component thật sự vẫn là `_main_than()` và `GiaoDien`.

## 8. Ràng buộc không được vi phạm khi refactor

- **Không** phá nguyên tắc `SPEC_UI_UX.md` §1: UI lái `main()` qua `builtins.input`, không gọi hàm con.
- **Không** refactor cả file lớn trong một lần. Tách từng mảnh, mỗi mảnh verify.
- **Không** đổi hành vi trong lúc tách. Tách và sửa lỗi là **hai lần commit khác nhau** — trộn vào nhau thì khi test đỏ không biết tại cái nào.
- Kiến trúc đẹp mà mất tính năng là **thất bại**.


---

## 9. Đã làm — giai đoạn A (2026-09-10)

| Module | Dòng | Test | Ghi chú |
|---|---|---|---|
| `loi/phien_ban.py` | 198 | 22 | Thư mục gốc/tài nguyên/ghi khi đóng gói .exe. Sửa R-08, R-09 |
| `ui/cau_noi.py` | 136 | 27 | `Ong` + `TraLoi` — toàn bộ khớp nối UI↔lõi |
| `ui/kiem_dau_vao.py` | 157 | 34 | 10 phép kiểm SPEC §8, tách quyết định khỏi hiển thị |

`giao_dien.py`: **987 → 920 dòng**. Con số giảm không lớn, nhưng **thứ chuyển đi là phần rủi ro cao nhất**: khối kiểm trong `_bat_dau()` gọn từ 4661 xuống 1506 ký tự, và 61 phép kiểm mới chạy trong **0,2 giây không cần tkinter** — trước đây muốn kiểm những thứ này phải dựng cả cửa sổ Tk.

**Ba khái niệm thư mục** giờ tách bạch (trước đây gộp làm một `_GOC`):

| Hàm | Trả về | Dùng để |
|---|---|---|
| `thu_muc_chuong_trinh()` | nơi chứa .exe | so với folder XUẤT RA |
| `thu_muc_tai_nguyen()` | nơi chứa file đi kèm | đọc ffmpeg, cau_hinh.json |
| `thu_muc_ghi()` | nơi ghi được | log, dấu tự kiểm |

Khi chưa đóng gói cả ba trùng nhau — đó là lý do bug này ẩn được tới giờ.

**Hai bug phát sinh trong lúc làm**, đã ghi `bug.md` #101 và #102. Cả hai đều do bộ kiểm bắt được chứ không phải đọc code ra — bằng chứng cho quy tắc "chạy test trước và sau mỗi khối việc".

---

## 10. Đã làm — giai đoạn C: hàng đợi nhiều project (2026-09-10)

**Chưa commit** theo yêu cầu chủ dự án.

| Module | Dòng | Trách nhiệm |
|---|---|---|
| `ui/hang_doi.py` | 212 | Trạng thái + điều phối. Không biết gì về tkinter lẫn `main()` |
| `ui/chay_hang_doi.py` | 109 | Chỗ **duy nhất** chạm vào lõi — gọi `G.main()` một lần/project |
| `ui/cua_so_hang_doi.py` | 289 | Chỉ dựng giao diện, không quyết định gì |

Ba lớp tách bạch nên `HangDoi` kiểm được bằng hàm giả (30 phép kiểm, không cần tkinter, không cần gom thật), còn `chay_hang_doi` kiểm bằng E2E gom thật (13 phép kiểm).

### Nguyên tắc §1 được giữ thế nào

`ui/chay_hang_doi.py` gọi `G.main()` **đúng một lần** cho mỗi project, lái qua `builtins.input` bằng chính `TraLoi` mà giao diện chính dùng. Khác biệt duy nhất: `cho_tien_hanh` là một Event giả luôn ở trạng thái đã đầy, vì cả hàng đợi đã được duyệt một lần trước khi chạy — không có người ngồi bấm "TIẾN HÀNH COPY" cho từng project.

Nếu lớp này tự gọi `collect_refs`, `plan_package`... thì mọi bản vá logic sau này phải sửa hai nơi, và hai nơi sẽ trôi khỏi nhau. Đó đúng là cái bẫy mà §1 sinh ra để tránh.

### Điều kiện tiên quyết đã phải sửa trước

`_EXIST_CACHE` dính giữa các lần chạy (`bug.md` #103). Ở chế độ một-project mỗi lần gói là một tiến trình mới nên không ai thấy; hàng đợi gọi `main()` nhiều lần trong cùng tiến trình thì project sau thừa hưởng cache project trước.

**Bài học chung:** *"mỗi lần chạy là một tiến trình mới"* là giả định ngầm, không phải sự thật vĩnh viễn. Trước khi thêm tính năng chạy-nhiều-lần, phải liệt kê hết biến toàn cục và hỏi từng cái *"ai xoá mày?"*.
