# PERF — số đo hiệu năng

> Chỉ ghi **số đo thật**. Phỏng đoán phải ghi rõ là phỏng đoán.
> Mỗi mục cần: ngày, môi trường, cách đo, kết quả.

## P-01 — Thời gian khởi động .exe: onefile vs onedir ✅ ĐÃ ĐO

**Ngày:** 2026-09-10 · **Máy:** Windows 11 Home 26200, Python 3.14.6, PyInstaller 6.22.2
**Cách đo:** app tkinter tối giản (`tk.Tk()` + `ttk.Style().theme_use("vista")`), đo từ dòng import đầu tiên tới lúc **cửa sổ thật sự hiện ra** (`update_idletasks()` rồi đọc `perf_counter`), ghi ra file. Chạy 10 lần mỗi kiểu.

### Kết quả

| Kiểu đóng gói | n | Trung vị | Min | Max | Dung lượng |
|---|---|---|---|---|---|
| **onedir + ffmpeg** | 10 | **93,6 ms** | 89,9 | 99,1 | 225 MB (thư mục) |
| **onefile + ffmpeg** | 10 | **252,6 ms** | 244,4 | **446,7** | 83 MB (1 file) |
| onedir trần (không ffmpeg) | 6 | 93,1 ms | 89,9 | 93,9 | 31 MB |
| onefile trần (không ffmpeg) | 6 | 266,2 ms | 246,1 | 287,9 | 13 MB |
| *Python thường (mốc nền)* | 5 | *76,5 ms* | 74,9 | 81,6 | — |

### Kết luận

**onedir nhanh hơn onefile ~2,7 lần** (93,6 ms vs 252,6 ms). Chênh lệch **~159 ms mỗi lần mở**.

onedir gần như không tốn thêm gì so với Python thường (93,6 vs 76,5 ms = +17 ms). Toàn bộ phần chậm của onefile là chi phí giải nén, không phải chi phí đóng gói.

### Phát hiện quan trọng: ffmpeg 195 MB KHÔNG làm onefile chậm thêm

Trái với dự đoán ban đầu (ghi ở bản trước của tài liệu này), thêm 195 MB ffmpeg **không** làm onefile chậm hơn: 252,6 ms (có ffmpeg) so với 266,2 ms (không có) — chênh lệch nằm trong nhiễu đo.

**Nhưng nó VẪN được giải nén thật.** Kiểm chứng bằng một bản build riêng đọc `sys._MEIPASS`:

```
frozen=True
MEIPASS=C:\Users\Padoma1\AppData\Local\Temp\_MEI000075842
so file giai nen=988  tong=221.0 MB
ffmpeg co trong MEIPASS=True   kich thuoc=97.2 MB
```

Chạy 3 lần liên tiếp cho **3 đường dẫn `_MEI...` khác nhau**, và sau khi thoát **không còn thư mục `_MEI*` nào sót lại** — tức mỗi lần chạy đều bung 221 MB ra temp rồi dọn đi.

Lý do vẫn nhanh: Windows file cache giữ nội dung trong RAM giữa các lần chạy liên tiếp. **Đây chính là điều làm con số này nguy hiểm** — phép đo lặp lại 10 lần là kịch bản thuận lợi nhất, không phải kịch bản thật.

### Bằng chứng cho thấy biến động có thật

Trong 10 lần đo onefile+ffmpeg có **một lần vọt lên 446,7 ms** (gấp 1,8 lần trung vị), trong khi onedir cực kỳ ổn định (89,9–99,1 ms, biên độ chỉ 9 ms).

Với 40–50 máy, đủ loại ổ cứng và phần mềm diệt virus, **biên độ mới là thứ người dùng cảm nhận**, không phải trung vị.

### Khuyến nghị: chọn onedir

| Tiêu chí | Nghiêng về |
|---|---|
| Tốc độ khởi động (ưu tiên của chủ dự án) | **onedir** — nhanh 2,7 lần |
| Ổn định (ưu tiên của chủ dự án) | **onedir** — biên độ 9 ms vs 202 ms |
| Ghi 221 MB ra ổ mỗi lần mở | **onedir** — không ghi gì |
| Phần mềm diệt virus | **onedir** — onefile bung .exe ra temp mỗi lần, dễ bị quét/chặn |
| Auto-update | onedir thay nhiều file, cần cẩn thận dở dang; onefile thay 1 file |
| Gọn khi bàn giao | onefile — 83 MB vs 225 MB |

Hai ưu tiên chủ dự án nêu đích danh — **ổn định và tốc độ** — đều nghiêng về onedir. Điểm yếu duy nhất của onedir là auto-update phức tạp hơn, nhưng đó là việc làm một lần trong code, còn cái giá của onefile là 159 ms **mỗi lần mở, trên mọi máy, mãi mãi**.

### Điều đã đo nhưng CHƯA đo

- Chưa đo **cold start thật** (máy vừa bật, cache nguội). Số onefile ở trên là kịch bản thuận lợi nhất; thực tế trên máy nguội sẽ **tệ hơn**, không tốt hơn.
- Chưa đo trên **ổ HDD** (máy đo dùng SSD). Chênh lệch onefile/onedir sẽ **giãn ra** trên HDD vì onefile phải ghi 221 MB.
- Chưa đo với **phần mềm diệt virus quét chủ động**.

Cả ba đều chỉ làm onefile tệ thêm, nên **không đảo ngược được kết luận**.

---

## Nhật ký đo khác

### 2026-09-10 — Bộ kiểm đầy đủ
**Cách đo:** `python tests\chay_het.py` trên máy dự án.
**Kết quả:** **22/22 ĐẠT**, tổng **78,9 giây**.

Các bộ tốn nhiều thời gian nhất:

| Bộ kiểm | Thời gian |
|---|---|
| ỔN ĐỊNH (race / ghi atomic / ổ mạng / cấu hình) | 16,0s |
| XEM TIẾN TRÌNH | 12,1s |
| GIAO DIỆN (lái được tool thật) | 8,6s |
| E2E (luồng thật trên draft giả + ép lỗi) | 6,6s |
| REVERSE (bản render ngược) | 5,7s |
| NUỐT LỖI | 5,0s |

**Ý nghĩa cho CI:** 79 giây hoàn toàn chấp nhận được. Không cần chia nhỏ hay chạy song song ở giai đoạn này.

### 2026-09-10 — Dung lượng ffmpeg đi kèm
`ffmpeg.exe` 98 MB + `ffprobe.exe` 97 MB = **195 MB**. Đây là phần lớn nhất của gói phát hành.


### 2026-09-10 — Gói THẬT hai project DEEP SEA 5 (chạy song song)

**Môi trường:** nguồn NAS `.213` + ổ D:, đích NAS `.214` (SMB), CPU 12 nhân, mỗi project 2 luồng ffmpeg (tool tự hạ vì đích là ổ mạng).

| | DS1_118 (luồng chính) | DS1_124 (hàng đợi) |
|---|---|---|
| Tham chiếu | 534 | 825 |
| Chế độ 4 bỏ đi | 68 file, 87,88 GB | 229 file |
| Gom thật | 459 file, 101 GB | — |
| **Gói cuối cùng** | **4,3 GB** | **5,0 GB** |
| Giảm được | **97,83 GB** | **94,42 GB** |
| Clip xử lý | 725/1394 (cắt 189, hạ 123, nén 509) | 1092 |
| Clip thất bại | **0** | **0** |
| Thiếu / copy lỗi | **0 / 0** | **0 / 0** |
| Thời gian tối ưu | 29m26s | ~50 phút |

**Tỷ lệ nén thực tế: 101 GB → 4,3 GB ≈ 96%** — cao hơn nhiều so với con số ước lượng 70% tôi dùng ban đầu. Ước lượng cũ quá bi quan.

**Chạy song song không tranh chấp:** 12 nhân, mỗi project 2 luồng mã hoá. Tổng thời gian gần bằng project chậm hơn chứ không phải tổng hai project.

**Tốc độ copy qua SMB:** 5–35 MB/s lúc đầu, tăng lên 140–220 MB/s ở đoạn cuối (liên kết cứng cho file dùng chung — DS1_118 có 130 file, DS1_124 có 258 file dùng chung).

**Bài học cho ước lượng dung lượng:** đừng đo tổng mọi tham chiếu. Chế độ 4 chỉ gom file có role `content` (dùng thật trên timeline) — ở đây là 101 GB trên tổng 176 GB tham chiếu, rồi nén tiếp còn 4,3 GB.

---

## Số đã biết từ trước (chưa đo lại trong giai đoạn này)

| Hạng mục | Số | Nguồn |
|---|---|---|
| Tự kiểm lần đầu — phép thử ffmpeg | ~3,2 giây | ghi chú trong `giao_dien.py` |
| Thread phụ đẩy log | ~2 triệu dòng/giây | ghi chú `_rut_hang_doi` |
| Giao diện nuốt log | ~19 nghìn dòng/giây | ghi chú `_rut_hang_doi` |
| `threading.Event.is_set` | 41–48 ns/lần | ghi chú `GiaoDien.__init__` |
| Dung lượng còn lại trên NAS đích | ~570 GB (2026-08-19) | ghi nhớ |

Chênh lệch **2 triệu vs 19 nghìn dòng/giây** chính là lý do phải giới hạn 300 mục mỗi nhịp — xem `SPEC_UI_UX.md` §6.5.

---

## Cần đo, chưa đo

| ID | Cần đo | Vì sao |
|---|---|---|
| ~~P-01~~ | ~~Khởi động onefile vs onedir~~ | ✅ **Đã đo 2026-09-10** — onedir thắng, xem trên |
| P-02 | Dung lượng bản cập nhật khi chỉ đổi code (không đổi ffmpeg) | onedir cho phép cập nhật **chỉ phần code** (~30 MB) thay vì tải lại cả 225 MB. Ảnh hưởng lớn tới 40–50 người |
| ~~P-03~~ | ~~Thời gian gói một project thật~~ | ✅ **Đã đo 2026-09-10** — DS1_118: 30 phút cho 725 clip; DS1_124: ~50 phút cho 1092 clip. Khoảng **22–24 clip/phút** với 2 luồng mã hoá |
| P-04 | Cold start onedir trên HDD | Kiểm chứng con số 93 ms có giữ được trên máy yếu không |
