# SPEC UI/UX — GÓI PROJECT CAPCUT

> **Trạng thái:** Bản 1.0 — dựng từ khảo sát `giao_dien.py` (987 dòng) ngày 2026-09-10.
> **Đây là nguồn chân lý.** Mọi việc làm giao diện bám theo tài liệu này.
> Muốn đổi giao diện → **sửa spec trước, code sau**.

## 0. Bối cảnh

- Người dùng: **40–50 người**, phần lớn không rành kỹ thuật (dựng video, không phải lập trình).
- Phát hành: **đóng gói .exe**, chạy như phần mềm desktop Windows.
- Ưu tiên chủ dự án nêu rõ: **tính ổn định và tốc độ**.
- Ngôn ngữ hiển thị: tiếng Việt **CÓ DẤU** (đổi 2026-09-10 — xem §7).

---

## 1. Nguyên tắc kiến trúc UI — BẤT KHẢ XÂM PHẠM

Đây là quyết định thiết kế quan trọng nhất của phần mềm, đã có sẵn trong code và **phải giữ**:

> **Giao diện KHÔNG viết lại bất kỳ logic nào.**
> Nó *lái* `goi_project_capcut.main()` — hàm đã chạy thật trên 10 project và được 25 bộ kiểm bảo vệ — bằng cách:
> - thay `builtins.input` bằng hàm trả lời **theo NỘI DUNG câu hỏi** (lấy từ form),
> - hướng `sys.stdout` vào ô Nhật ký.

**Vì sao phải giữ:** giao diện và dòng lệnh **không thể lệch hành vi** — chúng là MỘT. Nếu tách UI ra tự gọi từng hàm con, mọi bản vá logic sau này phải sửa hai nơi, và hai nơi sẽ trôi khỏi nhau.

**Hệ quả cho việc tách module:** được phép tách *cách trình bày*, **không** được phép biến UI thành nơi tự điều phối luồng gói.

### 1.1 Trả lời theo NỘI DUNG, không theo THỨ TỰ

Số bước hỏi **thay đổi tuỳ tình huống** (bước "dò theo tên" chỉ hiện khi có file thiếu). Một danh sách trả lời cứng theo thứ tự sẽ lệch một nhịp — đây là bẫy đã ghi ở `bug.md` #10. Bảng ánh xạ hiện tại:

| Câu hỏi chứa | Trả lời |
|---|---|
| `nhap so` | `P` |
| `duong dan folder draft` | đường dẫn mục 1 |
| `duong dan thu muc me` | thư mục cha của mục 1 |
| `folder xuat ra` | đường dẫn mục 2 |
| `chon 1 hoac 4` | `4` nếu có tối ưu nào bật, `1` nếu không |
| `thu muc` + `de do` | danh sách mục 3 |
| `tien hanh` | **dừng chờ người dùng bấm nút** |
| `enter de dong` | chuỗi rỗng |
| *không khớp* | **ném lỗi**, tuyệt đối không đoán bừa |

**Không đoán bừa:** một câu hỏi lạ mà trả lời sai có thể xoá nhầm dữ liệu.

### 1.2 Chốt chống lặp vô hạn

Tool hỏi lại cùng một câu khi câu trả lời không đúng. Ở dòng lệnh người thật sẽ sửa; ở GUI ta trả lời y hệt → **vòng lặp vô hạn, giao diện treo cứng, RAM tăng liên tục**. Ngưỡng hiện tại: **lặp quá 3 lần → ném lỗi có thông điệp giải thích**.

---

## 2. Bản đồ màn hình

```
Khởi động
   │
   ├── chưa có dấu tự kiểm phiên bản này ──► [MH-0] Cửa sổ tự kiểm (một lần)
   │                                              │
   │                                              ├─ tất cả ĐẠT ─► tự đóng sau 0,7s
   │                                              ├─ có vấn đề ─► [Vẫn mở giao diện] / [Thoát]
   │                                              └─ Thoát ─► kết thúc
   │
   └──────────────────────────────────────► [MH-1] Cửa sổ chính
```

`CuaSoTuKiem` chỉ hiện khi **chưa có dấu kiểm của đúng phiên bản này**. Kiểm xong ghi dấu → các lần sau vào thẳng giao diện, tiết kiệm ~3,2 giây phép thử ffmpeg. Dấu kiểm gắn với `TOOL_VERSION` — **nâng phiên bản là tự kiểm lại**, điều này quan trọng khi có auto-update.

---

## 3. [MH-0] Cửa sổ tự kiểm lần đầu

**Tiêu đề:** `Kiem tra lan dau...` · **Không cho đổi kích thước.**

| Thành phần | Nội dung |
|---|---|
| Tiêu đề đậm | "Dang kiem tra bo cong cu (chi lam MOT LAN)" — Segoe UI 10 bold |
| Phụ đề xám `#555` | "Cac lan sau se vao thang giao dien." |
| Thanh tiến trình | dài 420px, `maximum = len(TK.CAC_BUOC)` |
| Nhãn bước | `[i/tong] <tên bước>` |
| Ô nhật ký | ScrolledText 9 dòng × 62, Consolas 9, `wrap="word"`, chỉ đọc |
| Hàng nút | trống khi đang chạy |

**Trạng thái kết thúc:**

- **Tất cả ĐẠT** → ghi dấu → nhãn "Tat ca DAT. Dang mo giao dien..." → tự đóng sau 700ms.
  - Ghi dấu thất bại **không được chặn** người dùng — chỉ nghĩa là lần sau kiểm lại (tốn 5 giây), không phải lỗi nghiêm trọng.
- **Có vấn đề** → nhãn "CO VAN DE - xem chi tiet o tren." + hiện 2 nút: `Van mo giao dien` và `Thoat`.

Mỗi bước ghi `[OK]` hoặc `[HONG]` kèm tên; hỏng thì in chi tiết thụt lề 6 dấu cách.

---

## 4. [MH-1] Cửa sổ chính

**Tiêu đề:** `Goi Project CapCut -> Ban tu chua`

**Kích thước:** rộng `895`, cao `min(775, max(560, chiều_cao_màn_hình - 120))`, tối thiểu `760×560`.
> Laptop 1366×768 chỉ còn ~728px vùng làm việc; đặt cứng 775 làm **mất 3–4 dòng CUỐI của Nhật ký** — đúng những dòng mới nhất (câu xác nhận và đường dẫn đích). Phải co theo màn hình thật.

### Bố cục dọc (padding ngoài 8)

```
┌─ 1) Chon project (folder draft CapCut) ──────────────────┐
│  [Listbox 6 dòng ─────────────────────────] [scrollbar]  │
│  (Quet thu muc me...) (Lam moi danh sach mac dinh)       │
│  Hoac DAN thang duong dan folder draft vao o duoi...     │
│  [Entry ──────────────────────────────────]  (Chon...)   │
└──────────────────────────────────────────────────────────┘
┌─ 2) Folder XUAT RA (ban tu chua) ────────────────────────┐
│  [Entry ──────────────────────────────────]  (Chon...)   │
└──────────────────────────────────────────────────────────┘
┌─ 3) Neu thieu file - do theo TEN o dau ──────────────────┐
│  [Entry ─────────────────────────] (Them thu muc...)     │
│  O phat hien: C:; D:                                     │
│  O MANG va USB KHONG duoc quet tu dong. (màu #7a4a00)    │
└──────────────────────────────────────────────────────────┘
┌─ 4) Toi uu dung luong ───────────────────────────────────┐
│  [x] Cat gon footage dai  [x] Ha 4K/nen  [x] Bo file rác │
└──────────────────────────────────────────────────────────┘
 (1) QUET) (Dung do) (2) TIEN HANH COPY)   Trạng thái: ...
 Nhat ky
┌──────────────────────────────────────────────────────────┐
│  ScrolledText 16 dòng, Consolas 9, wrap="char", chỉ đọc  │  ← giãn
└──────────────────────────────────────────────────────────┘
```

### 4.1 Chi tiết từng khối

**Khối 1 — Chọn project**
- Listbox `height=6`, `exportselection=False` (**bắt buộc**: không thì chọn ở ô khác sẽ xoá lựa chọn ở đây).
- Nút `Quet thu muc me...` chạy nền, có **Event huỷ RIÊNG** `co_huy_quet` — tuyệt đối không dùng lại `co_huy` của pha gói (xem §6.2).
- Ô Entry cho phép **dán thẳng** đường dẫn (Ctrl+V hoặc menu chuột phải).

**Khối 2 — Folder xuất ra**
- Nhãn phải nói rõ có thể dán đường dẫn, không chỉ bấm Chọn.

**Khối 3 — Dò theo tên**
- Nhiều thư mục cách nhau bằng **dấu chấm phẩy `;`**.
- Ví dụ ổ phát hiện nối bằng `"; "` — **không phải `", "`**: đây là ví dụ duy nhất người dùng nhìn thấy, mà bộ đọc lại tách bằng `;`. In dấu phẩy là dạy họ gõ sai rồi cả chuỗi thành MỘT đường dẫn rác, im lặng.
- Bỏ trống = chỉ quét ổ trong máy.
- Cảnh báo màu nâu `#7a4a00`: ổ mạng và USB không được quét tự động.

**Khối 4 — Tối ưu dung lượng** — 3 checkbox, **mặc định đều BẬT**:
1. Cắt gọn footage dài (giữ đoạn dùng + đệm ~×3)
2. Hạ 4K / nén bitrate khung (H.264, giữ nét theo zoom)
3. Bỏ file không dùng / mồ côi / lịch sử

**Hàng nút điều khiển** — `1) QUET` · `Dung do` · `2) TIEN HANH COPY` · nhãn trạng thái.

**Nhật ký** — `wrap="char"` chứ **không** `"none"`: không có thanh cuộn ngang nên dòng dài (vd `Se gom ... vao <đường dẫn đích>`) bị cắt mất đuôi, **giấu luôn tên folder đích** ngay tại màn hình xác nhận.

---

## 5. Máy trạng thái nút bấm

| Trạng thái | 1) QUET | Dung do | 2) TIEN HANH | Nhãn trạng thái |
|---|---|---|---|---|
| Sẵn sàng | bật | tắt | tắt | `San sang.` |
| Đang quét thư mục mẹ | tắt | bật | tắt | `Dang quet...` |
| Đang quét (pha gói) | tắt | bật | tắt | `Dang quet...` |
| Chờ xác nhận | tắt | bật | **bật** | `Da quet xong - xem Nhat ky roi bam 2) TIEN HANH COPY` |
| Đang copy/tối ưu | tắt | bật* | tắt | `Dang copy / toi uu...` |
| Đã huỷ | bật | tắt | tắt | `Da huy - chua copy gi ca.` |
| Có lỗi | bật | tắt | tắt | `CO LOI - xem Nhat ky.` |
| Xong | bật | tắt | tắt | `Xong.` |

\* Bấm `Dung do` sau khi đã bắt đầu copy → hiện hộp thoại giải thích **không dừng giữa chừng được**, kèm cảnh báo quan trọng: lần sau **không chạy lại vào chính thư mục xuất ra đó** (tool copy lại từ đầu VÀ tạo bản trùng `canh1_1.mp4...`, gói phình gấp đôi, lần cũ thành rác).

### 5.1 BA trạng thái, không phải hai

Chốt sai `if cho_tien_hanh.is_set() or tra_loi_tien_hanh:` gộp "đã bấm COPY" với "vừa bấm HUỶ" làm một → bấm lần hai sau khi huỷ lại hiện "Da bat dau copy roi", **nói dối trắng trợn khi chưa copy một byte nào**. Phải kiểm `tra_loi_tien_hanh == "y"`.

### 5.2 "Xong." sau khi huỷ là báo cáo sai

Kết thúc bằng `Xong.` sau một cú huỷ thì **không phân biệt được với một lần chạy thành công** (đo thật: 5/5 lần nhãn cuối là "Xong."). Phải phân nhánh theo `co_huy.is_set()`. Hai nhánh `except` giữ NGUYÊN — **lỗi thật phải thắng nhánh huỷ**, không được bị che thành "đã huỷ".

---

## 6. Quy tắc kỹ thuật UI — đã trả giá để biết

### 6.1 tkinter không an toàn đa luồng
- `main()` chạy ở **thread riêng**; mọi cập nhật giao diện đi qua `queue` + `after()` trên thread chính.
- **Chụp toàn bộ giá trị form NGAY tại thread chính** trước khi khởi thread (`self.chup`). Gọi `.get()` của BooleanVar từ thread phụ ném `RuntimeError: main thread is not in main loop`.
- Tuyệt đối không truyền lambda đọc biến tkinter làm `nen_dung`. Dùng `threading.Event.is_set` (bound method của đối tượng C, đọc từ thread phụ an toàn, ~41–48 ns/lần, **không bao giờ ném**).

### 6.2 Hai pha, hai cờ huỷ riêng
`_bat_dau()` có `co_huy.clear()`. Kịch bản thường ngày — bấm "Quet thu muc me...", thấy lâu nên bấm "Dung do", rồi bấm "1) QUET" — sẽ **xoá đúng cái cờ mà thread quét đang đọc** → nó **hồi sinh**, quét tiếp đến hết cây rồi đè lên danh sách mới. Phải có `co_huy_quet` riêng.

Thêm **số phiên quét** (`phien_quet`): kết quả phiên cũ về muộn phải bị bỏ.

### 6.3 Thứ tự đặt cờ khi huỷ
Đặt `co_huy` **TRƯỚC** `cho_tien_hanh`. Nếu ngược lại, thread phụ đang chờ ở `_tra_loi` sẽ tỉnh dậy và `main()` trả về **trước khi** `_chay` nhìn thấy cờ huỷ → nhãn cuối lại thành "Xong.".

### 6.4 `redirect_stdout` không theo thread
`contextlib.redirect_stdout` **không** hoạt động theo thread (đã ghi `bug.md`). Phải thay `sys.stdout` trực tiếp một lần cho cả phiên chạy và **trả lại trong `finally`**.

### 6.5 Nhịp đập hàng đợi phải có giới hạn
Thread phụ đẩy được ~2 triệu dòng/giây, giao diện nuốt ~19 nghìn/giây → `while True` **không bao giờ** gặp `queue.Empty` → `after()` không được đặt lại → **mainloop CHẾT, nút X cũng vô hiệu**. Giới hạn **300 mục mỗi nhịp** (chu kỳ 80ms): lũ dòng chỉ làm chậm, không treo.

Đặt lại `after` phải nằm trong `finally` — nếu nằm cuối thân hàm, một exception làm nhịp đập dừng hẳn, im lặng, giao diện đóng băng mãi mãi. Nhưng phải kiểm `winfo_exists()` trước.

### 6.6 `master=` là BẮT BUỘC cho mọi Variable
Thiếu `master=`, biến bám vào `tkinter._default_root`. Nếu có một root Tk khác ra đời trước (ví dụ do `ttk.Style()` gọi khi chưa có Tk nào) thì biến nằm ở **interpreter Tcl KHÁC** với Entry → ô luôn TRỐNG dù `.set()` đã chạy, `.get()` luôn rỗng dù người dùng đã gõ. **Không exception, không log.**

### 6.7 Không gọi `ttk.Style()` trước khi có `tk.Tk()`
`ttk.Style()` → `_get_default_root()` → `if _default_root is None: root = Tk()` — nó **tự tạo một cửa sổ Tk thật**. Hậu quả: (1) ô nhập chết cả hai chiều như §6.6; (2) `mainloop()` của cửa sổ tự kiểm **không bao giờ trả về** → lần chạy đầu treo hẳn. Luôn truyền master: `ttk.Style(root)`.

### 6.8 Ba lưới an toàn cho lỗi im lặng
Dưới `pythonw.exe` **không có console**, stderr là hố đen — triệu chứng là "bấm nút không làm gì cả".
1. `sys.stdout is None` → gán `_KhongDau` ghi ra `_LOI_GIAO_DIEN.log`.
2. `root.report_callback_exception` → ghi Nhật ký + messagebox.
3. `try/except` bọc toàn bộ `main()` → messagebox "Không mở được giao diện".

`<Destroy>` phải bind để huỷ nhịp đập kể cả khi cửa sổ bị `destroy()` trực tiếp (bộ kiểm, hoặc lưới báo lỗi) — nếu không Tcl in `invalid command name` ra stderr, dưới pythonw rơi thẳng vào log, làm người dùng **tưởng có lỗi thật**.

---

## 7. Quy ước hiển thị

| Hạng mục | Quy ước |
|---|---|
| Theme | `vista` (bọc try/except, thất bại thì dùng mặc định) |
| Phông nhật ký | Consolas 9 |
| Phông nhấn mạnh | Segoe UI 10 bold |
| Màu phụ đề | `#555` |
| Màu cảnh báo | `#7a4a00` |
| Ngôn ngữ | **Tiếng Việt CÓ DẤU** |

> **Đổi 2026-09-10:** ràng buộc "không dấu" cũ nói phải giữ *"cho tới khi chứng minh được toàn tuyến an toàn"*. Đã đo và chứng minh xong.

**Bốn đường chữ đi ra, kết quả KHÁC NHAU:**

| Đường ra | Kết quả |
|---|---|
| Nhãn tkinter (Tcl) | An toàn — không qua stdout |
| Ô Nhật ký của giao diện | An toàn — chuỗi Python thuần |
| File báo cáo (`encoding="utf-8"`) | An toàn |
| Console chế độ dòng lệnh | **CHẾT** với cp1258 / cp1252 |

Ba đường an toàn sẵn; chỉ đường thứ tư cần vá. Đã sửa bằng `loi/bang_ma.py` — `ep_utf8()` gọi ở đầu cả ba điểm vào, trước dòng `print` đầu tiên. Chi tiết: `bug.md` #105.

**Ràng buộc còn lại — file `.bat` vẫn phải KHÔNG DẤU.** `cmd.exe` diễn giải comment theo code page trước khi `chcp 65001` kịp chạy (`bug.md` #12). Đây là ràng buộc riêng của `.bat`, không liên quan tới Python.

---

## 8. Kiểm đầu vào — thứ tự và mức độ

Kiểm theo thứ tự này trong `_bat_dau()`, mỗi kiểm có **mức độ** riêng:

| # | Kiểm | Mức | Ghi chú |
|---|---|---|---|
| 1 | Đang chạy / đang quét? | **chặn im lặng** | hai thread cùng ghi hàng đợi = trạng thái vô nghĩa |
| 2 | Mục 1 trống? | cảnh báo | |
| 3 | Mục 1 có tồn tại? | chặn | Dùng `isdir_safe`, **không** `Path.is_dir()` — thư mục sau 260 ký tự bị báo "không tồn tại" → chặn oan project hợp lệ |
| 4 | Mục 1 có `draft_content.json`? | **chặn + hướng dẫn** | Chọn nhầm THƯ MỤC MẸ là thao tác tự nhiên nhất; trước đây làm tool hỏi lại vô hạn, giao diện treo cứng, chỉ End Task mới thoát |
| 5 | Mục 2 trống? | cảnh báo | |
| 6 | Mục 2 tuyệt đối thật? | **chặn** | `"D:"` KHÔNG phải gốc ổ — Windows nối vào thư mục làm việc, đổ cả gói thẳng vào thư mục công cụ, VÀ tool vẫn báo "XONG" (bug #23). Phải **báo to**, không được tự sửa bằng `abspath()` |
| 7 | Mục 2 là chính thư mục công cụ? | chặn | |
| 8 | Mục 2 trỏ vào một FILE? | chặn | |
| 9 | Thư mục mục 3 không tồn tại? | **cảnh báo, hỏi tiếp** | Không chặn: một USB vừa rút không nên chặn hai thư mục còn lại |
| 10 | Không bật tối ưu nào? | hỏi xác nhận | Nói rõ copy nguyên bản an toàn nhất nhưng nặng hơn nhiều |

---

## 9. Thiếu sót của bản hiện tại — việc cho bản .exe

Khảo sát cho thấy các khoảng trống sau. **Chưa cái nào được làm:**

| ID | Thiếu | Vì sao cần cho 40–50 người dùng |
|---|---|---|
| UX-01 | **Không có thanh tiến trình %** ở màn hình chính — chỉ có dòng log trôi | Gói chạy rất lâu; người dùng không biết còn bao lâu, dễ tưởng treo và tắt ngang |
| UX-02 | **Không phân biệt "thiếu do gói" và "thiếu sẵn từ draft gốc"** | Rủi ro R-06. Người không rành sẽ hoảng vì thứ vốn đã hỏng từ trước |
| UX-03 | **Không có khu vực thông báo cập nhật** | Yêu cầu số 2 của chủ dự án |
| UX-04 | **Không có nút mở thư mục kết quả** sau khi xong | Thao tác kế tiếp hiển nhiên nhất |
| UX-05 | **Nhật ký chỉ có một luồng chữ**, lỗi lẫn với tiến trình | Nên tách/tô màu dòng `!` |
| UX-06 | **Không lưu lựa chọn lần trước** (thư mục xuất, danh sách dò) | 40–50 người gõ lại mỗi lần |
| UX-07 | **Không có màn hình "Giới thiệu"** hiện phiên bản | Cần cho hỗ trợ từ xa: "bạn đang dùng bản nào?" |

**Quy tắc khi làm các mục trên:** thêm vào *lớp trình bày*, **không** được phá nguyên tắc §1.

---

## 10. Ràng buộc cho việc đóng gói .exe

Quyết định 2026-09-10: **đóng gói .exe**, ưu tiên ổn định và tốc độ.

- Phải chạy dạng **không console** (như `pythonw` hiện tại) → ba lưới an toàn §6.8 **càng quan trọng hơn**, vì stderr vẫn là hố đen.
- `_GOC = Path(__file__).resolve().parent` **sẽ sai** khi đóng gói (file nằm trong archive) → cần tách thành một hàm xác định thư mục gốc, xử lý cả trường hợp đóng gói. Đây là **rủi ro thật, chưa xử lý** — ghi ở `tai_lieu/RISK.md`.
- `_LOI_GIAO_DIEN.log` và dấu tự kiểm ghi cạnh .exe có thể **không có quyền ghi** (Program Files) → cần chọn nơi ghi khác.
- Dấu tự kiểm gắn `TOOL_VERSION` → mỗi bản cập nhật tự kiểm lại một lần. Đúng ý đồ, **giữ**.
- `ffmpeg` trong folder `ffmpeg/` phải đi kèm gói.

Chi tiết đóng gói: `tai_lieu/CI_CD.md`.
