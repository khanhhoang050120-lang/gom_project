# RISK — rủi ro đã nhận diện

Cập nhật 2026-09-10 sau khảo sát `giao_dien.py` và `goi_project_capcut.py`.

| ID | Rủi ro | Mức | Giảm thiểu | Trạng thái |
|---|---|---|---|---|
| R-01 | Refactor chống God Component làm **mất/hỏng tính năng đang chạy** | Cao | Tách từng mảnh theo thứ tự rủi ro tăng dần (`KIEN_TRUC.md` §7), chạy `tests\chay_het.py` sau mỗi mảnh; tách và sửa lỗi là hai commit khác nhau | Đang theo dõi |
| R-02 | **Auto-update chạy khi đang gói dở** | Cao | `loi/cap_nhat.py::co_the_cap_nhat()` chặn ở **tầng API** (không chỉ làm xám nút — nút xám là lớp hiển thị, phím tắt/đồng hồ hẹn giờ đi vòng qua). Hàng đợi chạy cũng chặn. Kiểm: 0 file bị chạm khi bị chặn | **Đã xử lý** (ISSUE-015) |
| R-03 | Cập nhật lỗi làm app **không mở được nữa** | Cao | Giữ đúng 1 bản cũ (`_ban_cu/`) + `phuc_hoi()`. Bước 5 hỏng → **tự** đưa bản cũ về ngay, không để người dùng ở trạng thái "không có bản nào". Không tự hạ cấp khi server có bản cũ hơn | **Đã xử lý** (ISSUE-015) |
| R-04 | Phát hành rộng → gặp **path lạ**: UNC, ổ mạng, long path, tên có dấu | Cao | Dùng chung một hàm `_lp()` cho mọi thao tác filesystem; test UNC bằng loopback `\\localhost\C$\...` | Có biện pháp sẵn |
| R-05 | CI trên runner sạch **đỏ oan** vì thiếu ổ mạng/NAS/ffmpeg | Cao | **ĐÃ XẢY RA THẬT 2026-09-11** — xem `bug.md` #107. Phép đo trước đó ("44/44 ĐẠT, 0 bỏ qua") **SAI**: nó chỉ giấu thư mục `ffmpeg/` mà máy đo **có ffmpeg trong PATH**. Đo lại bằng cách chặn **cả hai đường**: đúng **7 bộ bỏ qua**, 0 thất bại. Đã sửa 4 bộ đỏ + đặt `MAX_BO_QUA=7` | **Đã xử lý** (bug #107) |
| R-06 | Người dùng không rành kỹ thuật **hiểu nhầm báo cáo "thiếu file"** — có những thiếu vốn có sẵn trong draft gốc | Trung bình | UI phân biệt rõ "thiếu do gói" và "thiếu sẵn từ draft gốc" (UX-02) | Chưa xử lý |
| R-07 | Nuốt lỗi âm thầm → báo "đã xong" sai | Cao | Cấm `except: pass`; đếm mọi thất bại và đưa vào báo cáo. **2026-09-11:** thêm `tests/cong_cu/kiem_chung_nguoc.py` — phá code thật ở 8 tầng, bộ kiểm phải đỏ đúng chỗ (**8/8**). Một cổng CI chưa từng đỏ là một cổng chưa được chứng minh | Có quy tắc + **đã chứng minh** |
| R-08 | **`__file__` sai khi đóng gói .exe** | **Cao** | `loi/phien_ban.py` tách 3 khái niệm thư mục, xử lý `sys.frozen` + `sys._MEIPASS`. Chốt tĩnh canh không bị gộp lại thành một `_GOC` | **Đã xử lý** (ISSUE-014) |
| R-09 | **Không ghi được cạnh .exe** | **Cao** | `thu_muc_ghi()` lùi 3 tầng: cạnh .exe → `%LOCALAPPDATA%` → temp, **không bao giờ ném**. `_ghi_duoc()` thử **ghi thật** (không `os.access` — sai trên Windows vì không tính UAC virtualization) | **Đã xử lý** (ISSUE-014) |
| R-10 | **Mất mạng / GitHub bị chặn** làm app không khởi động được | Cao | `hoi_ban_moi()` nuốt **mọi** ngoại lệ, trả `None`. Kiểm 9 kịch bản: mất mạng, DNS hỏng, 403, 500, JSON rác, rỗng, hết giờ | **Đã xử lý** (ISSUE-015) |
| R-11 | **SmartScreen cảnh báo** .exe không ký số → 40–50 lần hoang mang | Trung bình | Cân nhắc ký số; nếu không thì phải có hướng dẫn kèm bản phát hành | Chưa quyết |
| R-12 | Tách 12 pha của `_main_than()` sinh ra **object trạng thái khổng lồ** — God Component đội lốt khác | Trung bình | Trước bước 8, lập bảng "biến nào sống qua pha nào" và ghi vào `KIEN_TRUC.md` | Chưa xử lý |
| R-13 | ~~Gói một-file khởi động chậm~~ | — | **ĐÃ ĐO 2026-09-10:** onefile 252,6 ms vs onedir 93,6 ms (chậm 2,7 lần, biên độ 202 ms vs 9 ms). Chọn **onedir** | **Đã xử lý** |
| R-14 | **Auto-update onedir thay nhiều file** → cập nhật dở dang | Cao | Kiểm SHA256 + đủ file **trước** khi đổi tên; cả hai bước đều là **đổi tên thư mục** (nguyên tử ở mức hệ thống tệp). **Đo thật:** ngắt ở mọi lần đổi tên → `CU / CU / MOI / MOI`, không bao giờ có trạng thái thứ ba | **Đã xử lý** (ISSUE-015) |

## Ghi chú

- **R-13 đã đóng** bằng số đo thật (`PERF.md` §P-01). Quyết định onedir lại **sinh ra R-14** — đây là đánh đổi có ý thức, không phải sơ suất: onedir đổi "auto-update phức tạp hơn một lần trong code" lấy "nhanh hơn 159 ms mỗi lần mở trên mọi máy".
- R-08 và R-09 **chỉ phát sinh vì quyết định đóng gói .exe**. Cả hai đều thuộc loại "hỏng im lặng" — không có exception, người dùng chỉ thấy phần mềm cư xử lạ. Đây đúng họ lỗi mà `bug.md` cảnh báo nhiều nhất.
- R-08 được xếp làm **bước tách đầu tiên** vì nó vừa an toàn (code mới) vừa bắt buộc phải có trước khi đóng gói.

- **R-05 đóng lần hai, sau khi lần đầu đóng nhầm.** Phép đo đầu tiên kết luận *"44/44 ĐẠT, 0 bỏ qua khi không có ffmpeg"* và CI được đặt `MAX_BO_QUA=0` theo đó. Lần chạy CI thật đầu tiên: **4 bộ đỏ, 6 bộ bỏ qua**. Nguyên nhân: phép đo cũ chỉ giấu thư mục `ffmpeg/`, mà máy đo **có ffmpeg trong PATH** — `ff_paths()` vẫn tìm thấy.
- **Bài học:** giấu MỘT nguồn tài nguyên là chưa đủ để mô phỏng máy sạch. Muốn mô phỏng máy thiếu thứ gì, phải chặn **mọi đường** nó có thể đến — nếu không, con số sai sẽ đi thẳng vào cấu hình CI và chỉ lộ ra khi người dùng thấy CI đỏ. Kết luận đúng vẫn giữ: **một job, không cần cài ffmpeg trong CI** — chỉ khác là 7 bộ bỏ qua chứ không phải 0.
- **Một rủi ro mới nhận ra khi làm GĐ4:** mọi bộ kiểm E2E cũ đều dùng hàm của chính tool để nghiệm thu kết quả của tool — tool tự chấm bài mình. Đã bù bằng `tests/nghiem_thu_goi.py` (verifier độc lập, ISSUE-012). Nhưng nó vẫn **không** kiểm được ngữ nghĩa riêng của CapCut; chỉ người thật mở bằng CapCut thật mới bắt được. Đây là khoảng trống **còn lại**, không phải đã đóng.
