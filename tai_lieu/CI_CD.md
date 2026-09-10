# CI/CD, ĐÓNG GÓI & AUTO-UPDATE

> **Trạng thái: CHƯA TRIỂN KHAI** — ghi nhận yêu cầu 2026-09-10.

## 1. Yêu cầu gốc từ chủ dự án

1. Code đưa lên GitHub, dùng **GitHub Actions**.
2. Khi publish bản mới (tính năng mới hoặc sửa lỗi) → **CI/CD chạy kiểm thử**.
3. Phía người dùng: hiện **thông báo có bản cập nhật mới**; bấm cập nhật là tự cập nhật.
4. Quy mô: **40–50 người dùng**. Ưu tiên **tính ổn định và tốc độ**.

## 2. QUYẾT ĐỊNH — Đóng gói .exe

**Chốt ngày 2026-09-10:** phát hành dạng **.exe**, chạy như một phần mềm desktop Windows.

Lý do chủ dự án nêu: 40–50 người dùng, cần ổn định và tốc độ.

### Hệ quả của quyết định này

| Hệ quả | Chi tiết |
|---|---|
| Không có console | Chạy dạng windowed như `pythonw` hiện tại → stderr là **hố đen**. Ba lưới an toàn ở `SPEC_UI_UX.md` §6.8 trở thành **thiết yếu**, không còn là phòng xa |
| `__file__` không còn đáng tin | `_GOC = Path(__file__).resolve().parent` **sẽ sai**. Xem R-08 |
| Không ghi được cạnh .exe | Nếu cài vào `Program Files`, log và dấu tự kiểm không ghi được. Xem R-09 |
| ffmpeg phải đi kèm | Folder `ffmpeg/` phải nằm trong gói phát hành |
| Tự kiểm gắn phiên bản | Dấu kiểm gắn `TOOL_VERSION` → mỗi bản cập nhật tự kiểm lại một lần. **Đúng ý đồ, giữ nguyên** |
| Khởi động chậm hơn | Gói một-file phải giải nén vào temp mỗi lần chạy. Xem §3 |

## 3. Chưa quyết — cần đo trước khi chọn

### 3.1 Một-file hay một-thư mục? — ĐÃ ĐO, CHỌN MỘT-THƯ-MỤC (onedir)

**Đo ngày 2026-09-10** (PyInstaller 6.22.2, chi tiết đầy đủ ở `PERF.md` §P-01):

| | onefile (1 file .exe) | **onedir (một thư mục)** |
|---|---|---|
| Khởi động (trung vị, 10 lần) | 252,6 ms | **93,6 ms** |
| Biên độ | 244–**447** ms | **90–99 ms** |
| Dung lượng | 83 MB | 225 MB |
| Ghi ra ổ mỗi lần mở | **221 MB vào temp** | không ghi gì |
| `__file__` | trỏ vào temp | trỏ vào thư mục cài |

**onedir nhanh hơn 2,7 lần** và ổn định hơn hẳn (biên độ 9 ms so với 202 ms). Cả hai ưu tiên chủ dự án nêu đích danh — **ổn định và tốc độ** — đều nghiêng về onedir.

Điểm bất ngờ đã kiểm chứng: ffmpeg 195 MB **không** làm onefile chậm thêm (nhờ Windows file cache), **nhưng nó vẫn được giải nén thật** — đọc `sys._MEIPASS` cho thấy 988 file, 221 MB, đường dẫn khác nhau mỗi lần chạy. Phép đo lặp 10 lần là kịch bản thuận lợi nhất; máy nguội và ổ HDD chỉ làm onefile tệ hơn.

**Đánh đổi phải chấp nhận:** auto-update onedir phức tạp hơn (thay nhiều file, phải chống dở dang). Nhưng đó là việc làm một lần trong code, còn cái giá của onefile là 159 ms **mỗi lần mở, trên mọi máy**.

**Lợi ích kèm theo:** onedir cho phép cập nhật **chỉ phần code** (~30 MB) thay vì tải lại cả 225 MB — đáng kể với 40–50 người. Cần đo P-02 để xác nhận.

### 3.2 Các điểm khác chưa quyết

- [x] ~~Công cụ đóng gói~~ → **PyInstaller 6.22.2**, đã dựng thử thành công cả hai kiểu. Ràng buộc "chỉ thư viện chuẩn" trong `CLAUDE.md` áp cho **code chạy**, không áp cho công cụ build — nhưng vẫn cần chủ dự án xác nhận.
- [ ] Cách kiểm tra phiên bản: GitHub Releases API? So sánh bằng gì?
- [ ] Cập nhật xong có cần khởi động lại không?
- [ ] Có ký số (code signing) không? Không ký thì **SmartScreen sẽ cảnh báo** — với 40–50 người dùng đây là 40–50 lần hoang mang và gọi hỏi.

## 4. Ràng buộc bắt buộc của auto-update

Ba điều dưới đây **không được thoả hiệp**, đều là rủi ro cao:

1. **Không bao giờ cập nhật khi đang gói dở một project** (R-02). Một lần gói chạy rất lâu; cập nhật giữa chừng làm hỏng dữ liệu người dùng. Phải kiểm trạng thái trước khi cho phép cập nhật — liên quan bài học "kiểm tiến trình trước khi xoá".
2. **Phải rollback được** (R-03). Bản cập nhật lỗi làm app không mở được nữa thì 40–50 người tắc việc và không ai tự sửa được.
3. **Mất mạng không được làm app chết** (R-10). Máy không có mạng, hoặc GitHub bị chặn, app vẫn phải chạy bình thường. Kiểm tra cập nhật là việc **phụ, chạy nền, thất bại im lặng** — không phải cửa ải khởi động.

## 5. Cổng kiểm thử trong CI

**Tối thiểu:**
- `python tests\chay_het.py` — bộ kiểm hiện có
- `python tests\kiem_nhat_ky.py` — kiểm tính toàn vẹn `bug.md`

**Nên thêm khi đã tách module** (theo `KIEN_TRUC.md`):
- Test cho `ui/cau_noi.py` — bảng dịch câu hỏi → đáp án. Đây là phần rủi ro cao nhất của UI và là phần **duy nhất trong UI test được không cần tkinter**.
- Test cho `ui/kiem_dau_vao.py` — 10 phép kiểm ở `SPEC_UI_UX.md` §8.

## 6. Lưu ý riêng của repo này khi dựng CI

- Test path Windows dễ bị **nuốt backslash** khi chạy qua bash/`python -c` → trong CI gọi **file test Python trực tiếp**, không nhúng đường dẫn vào lệnh shell.
- Runner GitHub là máy sạch: **không có ổ mạng F:/Y:/Z:, không có NAS `\\192.168.1.214\e`**. Test nào phụ thuộc ổ mạng phải **tự bỏ qua có báo lý do**, không được làm CI đỏ oan (R-05).
- Test UNC dùng loopback `\\localhost\C$\...` — cách này chạy được trên runner Windows.
- Runner Windows **không có ffmpeg sẵn**. Test nào cần ffmpeg phải tự bỏ qua hoặc dùng file mẫu cực nhỏ.
