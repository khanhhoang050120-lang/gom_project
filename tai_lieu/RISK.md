# RISK — rủi ro đã nhận diện

Cập nhật 2026-09-10 sau khảo sát `giao_dien.py` và `goi_project_capcut.py`.

| ID | Rủi ro | Mức | Giảm thiểu | Trạng thái |
|---|---|---|---|---|
| R-01 | Refactor chống God Component làm **mất/hỏng tính năng đang chạy** | Cao | Tách từng mảnh theo thứ tự rủi ro tăng dần (`KIEN_TRUC.md` §7), chạy `tests\chay_het.py` sau mỗi mảnh; tách và sửa lỗi là hai commit khác nhau | Đang theo dõi |
| R-02 | **Auto-update chạy khi đang gói dở** một project → hỏng dữ liệu người dùng | Cao | Chặn cập nhật khi có tiến trình đang chạy | Chưa xử lý |
| R-03 | Cập nhật lỗi làm app **không mở được nữa**, 40–50 người tắc việc | Cao | Cần cơ chế rollback / giữ bản cũ | Chưa xử lý |
| R-04 | Phát hành rộng → gặp **path lạ**: UNC, ổ mạng, long path, tên có dấu | Cao | Dùng chung một hàm `_lp()` cho mọi thao tác filesystem; test UNC bằng loopback `\\localhost\C$\...` | Có biện pháp sẵn |
| R-05 | CI trên runner sạch **đỏ oan** vì thiếu ổ mạng/NAS/ffmpeg | Trung bình | Test phụ thuộc môi trường phải tự bỏ qua **có báo lý do** | Chưa xử lý |
| R-06 | Người dùng không rành kỹ thuật **hiểu nhầm báo cáo "thiếu file"** — có những thiếu vốn có sẵn trong draft gốc | Trung bình | UI phân biệt rõ "thiếu do gói" và "thiếu sẵn từ draft gốc" (UX-02) | Chưa xử lý |
| R-07 | Nuốt lỗi âm thầm → báo "đã xong" sai | Cao | Cấm `except: pass`; đếm mọi thất bại và đưa vào báo cáo | Có quy tắc sẵn |
| R-08 | **`__file__` sai khi đóng gói .exe** — `_GOC = Path(__file__).resolve().parent` xuất hiện ở `giao_dien.py` và `tu_kiem_lan_dau.py`; gói một-file thì nó trỏ vào thư mục temp | **Cao** | Tách thành `loi/phien_ban.py` với một hàm xác định thư mục gốc xử lý cả hai trường hợp. Là **bước 1** trong thứ tự tách | Chưa xử lý |
| R-09 | **Không ghi được cạnh .exe** — `_LOI_GIAO_DIEN.log` và dấu tự kiểm ghi cùng chỗ với chương trình; cài vào `Program Files` là mất quyền ghi | **Cao** | Chọn nơi ghi theo người dùng (`%LOCALAPPDATA%`), không ghi cạnh .exe. Mất log là mất **đúng thứ cần khi hỗ trợ từ xa** | Chưa xử lý |
| R-10 | **Mất mạng / GitHub bị chặn** làm app không khởi động được | Cao | Kiểm tra cập nhật là việc phụ, chạy nền, **thất bại im lặng** — không phải cửa ải khởi động | Chưa xử lý |
| R-11 | **SmartScreen cảnh báo** .exe không ký số → 40–50 lần hoang mang | Trung bình | Cân nhắc ký số; nếu không thì phải có hướng dẫn kèm bản phát hành | Chưa quyết |
| R-12 | Tách 12 pha của `_main_than()` sinh ra **object trạng thái khổng lồ** — God Component đội lốt khác | Trung bình | Trước bước 8, lập bảng "biến nào sống qua pha nào" và ghi vào `KIEN_TRUC.md` | Chưa xử lý |
| R-13 | ~~Gói một-file khởi động chậm~~ | — | **ĐÃ ĐO 2026-09-10:** onefile 252,6 ms vs onedir 93,6 ms (chậm 2,7 lần, biên độ 202 ms vs 9 ms). Chọn **onedir** | **Đã xử lý** |
| R-14 | **Auto-update onedir thay nhiều file** → cập nhật dở dang làm hỏng bản cài | Cao | Hệ quả của quyết định onedir. Tải về thư mục tạm, kiểm đủ file, rồi mới đổi tên nguyên khối; giữ bản cũ để quay về (gắn với R-03) | Chưa xử lý |

## Ghi chú

- **R-13 đã đóng** bằng số đo thật (`PERF.md` §P-01). Quyết định onedir lại **sinh ra R-14** — đây là đánh đổi có ý thức, không phải sơ suất: onedir đổi "auto-update phức tạp hơn một lần trong code" lấy "nhanh hơn 159 ms mỗi lần mở trên mọi máy".
- R-08 và R-09 **chỉ phát sinh vì quyết định đóng gói .exe**. Cả hai đều thuộc loại "hỏng im lặng" — không có exception, người dùng chỉ thấy phần mềm cư xử lạ. Đây đúng họ lỗi mà `bug.md` cảnh báo nhiều nhất.
- R-08 được xếp làm **bước tách đầu tiên** vì nó vừa an toàn (code mới) vừa bắt buộc phải có trước khi đóng gói.
