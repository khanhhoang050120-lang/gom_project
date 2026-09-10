# CLAUDE.md — Chỉ dẫn cho Claude trong project này

Dự án: công cụ **GÓI PROJECT CAPCUT** — Python thuần, chạy trên Windows, gom media của một draft CapCut vào 1 folder tự chứa để bàn giao/nhân bản. Luồng hoạt động: xem `HUONG_DAN_GOI_PROJECT.md`.

## ⚠️ QUY TẮC BẮT BUỘC VỀ `bug.md`

**`bug.md` là nhật ký lỗi đã từng gặp trong project này. Nó là nguồn tri thức chống lặp lại lỗi cũ.**

1. **TRƯỚC KHI viết hoặc sửa BẤT KỲ code nào** trong project này (đặc biệt `goi_project_capcut.py`, `xem_tien_trinh.py`, hay bất kỳ file `.py`/`.bat` nào), **PHẢI đọc `bug.md`** — nhất là phần **"Checklist nhanh"** ở cuối — để không tái phạm các lỗi đã biết (xử lý path UNC/long-path Windows, nuốt lỗi âm thầm, báo cáo sai "đã xong", encoding `.bat`, v.v.).

2. **NGAY SAU KHI sửa xong một bug/lỗi mới** (dù tự phát hiện hay do người dùng báo), **PHẢI TỰ ĐỘNG thêm một mục mới vào `bug.md`** — KHÔNG chờ người dùng nhắc. Dùng đúng mẫu trong `bug.md` (Triệu chứng → Nguyên nhân gốc → Cách sửa → Cách kiểm chứng → Bài học). Đánh số tăng dần, thêm vào phần "## Nhật ký lỗi".

3. Nếu phát hiện một lỗi tiềm ẩn cùng loại với lỗi đã có trong `bug.md` nhưng ở vị trí khác, vẫn ghi thành mục mới và tham chiếu tới mục gốc.

4. Đây là **quy tắc thường trực** — áp dụng ở MỌI session sau, không chỉ session hiện tại.

5. **TRƯỚC khi thêm mục mới, chạy `python tests\kiem_nhat_ky.py`.** Nó làm ba việc: kiểm số hiệu không trùng/không thiếu, liệt kê các mục còn đánh dấu **"chưa cài"** (bug vẫn đang sống trong code), và đối chiếu nhãn với code thật.
   - **Số hiệu của mục mới phải đọc NGAY LÚC GHI**, không dùng kết quả `grep` từ đầu session — file có thể đã được session khác thêm mục giữa chừng. Đây là bug #42, và nó đã tái diễn một lần nữa ngay sau đó.
   - Nhãn **"chưa cài"** lạc hậu nguy hiểm theo **cả hai chiều**: quên đổi nhãn sau khi cài khiến session sau đi sửa lại việc đã xong; còn nhãn nói đã cài trong khi chưa thì bug sống tiếp mà không ai ngờ.

## Khi có NHIỀU SESSION cùng làm trên repo này

Chuyện này đã xảy ra và đã gây va chạm thật. Quy tắc:

- **Đọc lại file ngay trước khi sửa**, đừng tin nội dung đã đọc lúc đầu session. Đã có trường hợp `encode_job()` được session khác vá xong trong lúc session này còn đang phân tích.
- **Chạy `python tests\chay_het.py` trước và sau mỗi khối việc.** Bộ kiểm phát hiện va chạm nhanh hơn đọc mắt thường.
- Nếu một mục `bug.md` mô tả bug bạn định sửa, **kiểm trong code xem đã có ai cài chưa** trước khi viết lại từ đầu.

## Nguyên tắc kỹ thuật cốt lõi (tóm tắt từ bug.md)

- **Path Windows:** long-path prefix phải đúng — UNC → `\\?\UNC\server\...`, drive → `\\?\D:\...`. Dùng CÙNG một hàm `_lp()` cho MỌI thao tác filesystem. Test UNC bằng loopback `\\localhost\C$\...`.
- **Xử lý lỗi:** không `except: pass` che lỗi; đếm mọi thất bại và đưa vào báo cáo. Chỉ số "xong/thiếu" đo trên KẾT QUẢ THỰC TẾ ở đích, không trên trạng thái trung gian.
- **Kiểm chứng:** sửa xong phải chạy test/E2E thật (unit test + luồng chính + case lỗi), không chỉ đọc code. Cẩn thận backslash bị nuốt khi test path Windows qua bash/`python -c` — ưu tiên file test Python hoặc `chr(92)`.

## Chỉ dùng thư viện chuẩn của Python (không thêm dependency ngoài) trừ khi người dùng đồng ý.

## Định hướng sản phẩm (từ 2026-09-10) — QUY TẮC THƯỜNG TRỰC

Đây **không còn là script nội bộ** mà là **phần mềm phát hành cho nhiều người dùng**, đưa lên GitHub.

1. **UI/UX phải có bản thiết kế TRƯỚC khi code.** Bản thiết kế nằm ở `tai_lieu/SPEC_UI_UX.md`. Mọi lần làm giao diện sau này **bám theo bản thiết kế đó**, không tự ứng biến. Nếu thiết kế cần đổi thì sửa spec trước, code sau.
2. **CI/CD bằng GitHub Actions + auto-update.** Publish bản mới → CI chạy kiểm thử → app phía người dùng báo "có bản cập nhật mới", bấm là tự cập nhật. Chi tiết và các điểm chưa quyết: `tai_lieu/CI_CD.md`.
3. **Mọi tính năng hiện có phải chạy ổn định như ban đầu.** Kiến trúc đẹp mà mất tính năng là thất bại. Không refactor cả file lớn một lần — tách từng mảnh, mỗi mảnh xong chạy `python tests\chay_het.py` để verify.

## KHÔNG ĐƯỢC TẠO "GOD COMPONENT"

Chủ dự án gọi việc chia nhỏ code thành module/component/folder là **"nguyên tắc sống còn"** và **"yếu tố đặc biệt cần phải tuân thủ"**.

- Thêm tính năng → **tạo module mới**, KHÔNG nối thêm vào file lớn sẵn có.
- Buộc phải sửa trong file lớn → cân nhắc tách phần liên quan ra trước.
- Tách theo **trách nhiệm**, không theo dung lượng.
- Hiện trạng cần xử lý: `goi_project_capcut.py` (88KB), `toi_uu_dung_luong.py` (68KB), `giao_dien.py` (45KB). Bản đồ module: `tai_lieu/KIEN_TRUC.md`.

## Folder `tai_lieu/` — tri thức xây dựng hệ thống

Gặp **bug, conflict, issue, risk, spec, perf** trong quá trình build → **ghi ngay** vào file `.md` tương ứng trong `tai_lieu/`, KHÔNG chờ người dùng nhắc.

- `tai_lieu/` = tri thức **xây dựng** (kiến trúc, xung đột refactor, rủi ro phát hành, spec UI/UX, số đo hiệu năng, checklist).
- `bug.md` = nhật ký **lỗi runtime** của tool, giữ nguyên quy trình đánh số đã nêu ở trên.
- Đừng trộn lẫn hai nơi. Xem `tai_lieu/README.md`.
- Trước khi báo "xong": chạy qua `tai_lieu/CHECK.md`.
