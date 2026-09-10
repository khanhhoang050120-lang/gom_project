# CONFLICT — xung đột đã gặp

Ghi lại xung đột giữa các session, giữa module, hoặc giữa các yêu cầu mâu thuẫn nhau.

---

### CONFLICT-001 (đã biết, phòng ngừa) Nhiều session cùng sửa một file
**Ngày ghi:** 2026-09-10 · **Nguồn:** `CLAUDE.md`, đã xảy ra thật.
`encode_job()` từng được một session khác vá xong trong lúc session này còn đang phân tích.
**Phòng ngừa:** đọc lại file **ngay trước khi sửa**; chạy `tests\chay_het.py` trước và sau mỗi khối việc; trước khi sửa theo mô tả trong `bug.md`, kiểm code xem đã có ai cài chưa.

### CONFLICT-002 (đã biết, phòng ngừa) Số hiệu `bug.md` bị trùng
**Ngày ghi:** 2026-09-10 · **Nguồn:** `bug.md` #42, đã tái diễn.
Dùng số hiệu `grep` từ đầu session → trùng với mục session khác vừa thêm.
**Phòng ngừa:** chạy `python tests\kiem_nhat_ky.py` và đọc số hiệu **ngay tại thời điểm ghi**.
