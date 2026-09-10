# `tai_lieu/` — Tri thức xây dựng hệ thống

Folder này ghi lại những gì học được **trong quá trình build** phần mềm GÓI PROJECT CAPCUT,
để các phiên làm việc sau không lặp lại sai lầm cũ.

## Phân biệt với `bug.md`

| Nơi ghi | Ghi cái gì |
|---|---|
| `bug.md` (gốc repo) | **Lỗi runtime của tool** khi chạy thật: path Windows, nuốt lỗi, encoding .bat... Có quy trình đánh số riêng, xem `CLAUDE.md`. |
| `tai_lieu/` (folder này) | **Tri thức xây dựng**: quyết định kiến trúc, xung đột khi refactor, rủi ro phát hành, spec UI/UX, số đo hiệu năng, checklist. |

Đừng trộn lẫn. `bug.md` đã 327KB; nhét thêm tri thức kiến trúc vào đó thì không ai tìm ra.

## Các file

| File | Nội dung |
|---|---|
| `SPEC_UI_UX.md` | Bản thiết kế UI/UX — **nguồn chân lý** cho mọi việc làm giao diện. Phải đọc trước khi code UI. |
| `KIEN_TRUC.md` | Sơ đồ module, ranh giới trách nhiệm, quy ước chia file. Chống God Component. |
| `ISSUE.md` | Việc đang mở, đang vướng, chưa xong. |
| `CONFLICT.md` | Xung đột: giữa các session, giữa module, giữa yêu cầu mâu thuẫn. |
| `RISK.md` | Rủi ro đã nhận diện + cách giảm thiểu. |
| `PERF.md` | Số đo hiệu năng thật (không đoán). |
| `CHECK.md` | Checklist trước khi phát hành / trước khi báo "xong". |
| `CI_CD.md` | GitHub Actions, quy trình release, cơ chế auto-update. |

## Quy tắc ghi

1. Gặp bug/conflict/rủi ro khi build → **ghi ngay**, không đợi được nhắc.
2. Mỗi mục có: ngày, triệu chứng/bối cảnh, nguyên nhân, cách xử lý, bài học.
3. Khẳng định nào là **số đo thật** thì ghi rõ đo bằng cách nào; khẳng định nào là **phỏng đoán** thì ghi rõ là phỏng đoán.
4. Trạng thái phải cập nhật hai chiều: việc xong rồi phải đổi nhãn, đừng để nhãn "chưa làm" nằm lại (bài học từ `bug.md` #42).
