# CHECKLIST

## Trước khi báo "xong" bất kỳ việc gì

- [ ] Đã chạy `python tests\chay_het.py` — và **đọc kết quả thật**, không đoán.
- [ ] Đã chạy thử luồng chính bằng tay (không chỉ đọc code).
- [ ] Đã thử ít nhất một case lỗi.
- [ ] Chỉ số "xong/thiếu" đo trên **kết quả thực tế ở đích**, không trên trạng thái trung gian.
- [ ] Nếu vừa sửa bug runtime → đã thêm mục vào `bug.md` (đọc số hiệu **ngay lúc ghi**, không dùng `grep` cũ từ đầu session).
- [ ] Nếu vừa gặp vướng khi build → đã ghi vào file tương ứng trong `tai_lieu/`.
- [ ] Việc nào chưa xong thì **nói rõ là chưa xong**.

## Trước khi phát hành một bản mới

- [ ] Toàn bộ tính năng cũ vẫn chạy như trước (yêu cầu số 3 của chủ dự án).
- [ ] CI xanh.
- [ ] Giao diện khớp `SPEC_UI_UX.md`.
- [ ] Không file nào phình lại thành God Component — đối chiếu `KIEN_TRUC.md`.
- [ ] Đã thử luồng auto-update trên máy sạch.
- [ ] Nhãn trạng thái trong `bug.md` và `tai_lieu/` đã cập nhật đúng **cả hai chiều**.
