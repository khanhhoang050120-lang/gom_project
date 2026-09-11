# bug.md — Nhật ký lỗi & bài học (đọc TRƯỚC khi viết/sửa code)

> **Quy ước bắt buộc cho Claude:**
> 1. **TRƯỚC khi viết hoặc sửa code trong project này**, ĐỌC hết file này để tránh lặp lại các lỗi đã biết.
> 2. **MỖI KHI gặp một bug/lỗi mới** (dù tự phát hiện hay do người dùng báo), sau khi sửa xong phải **TỰ ĐỘNG thêm một mục mới** vào file này theo đúng mẫu ở dưới — không cần người dùng nhắc.
> 3. Thêm mục mới vào phần "## Nhật ký lỗi", đánh số tăng dần, ghi rõ **triệu chứng → nguyên nhân gốc → cách sửa → bài học tránh lặp lại**.
> 4. Ưu tiên phần **Checklist nhanh** ở cuối khi viết code mới.

Dự án: công cụ **GÓI PROJECT CAPCUT** (Python thuần, chạy trên Windows, gom media của draft CapCut vào 1 folder tự chứa để bàn giao/nhân bản). Chi tiết luồng xem `HUONG_DAN_GOI_PROJECT.md`.

---

## Mẫu để thêm bug mới

```markdown
### N. <Tiêu đề ngắn gọn của bug>
- **Ngày:** YYYY-MM-DD
- **Mức độ:** Critical | High | Medium | Low
- **Vị trí:** <file>:<hàm/dòng>
- **Triệu chứng:** <người dùng/log thấy gì>
- **Nguyên nhân gốc:** <tại sao xảy ra, giải thích rõ>
- **Cách sửa:** <đã sửa thế nào>
- **Cách phát hiện / kiểm chứng:** <test gì để chắc chắn đã fix>
- **Bài học (để tránh lặp lại):** <quy tắc rút ra khi viết code sau này>
```

---

## Nhật ký lỗi

### 1. `_lp()` tạo prefix long-path SAI cho đường dẫn UNC (ổ mạng) → WinError 123, hỏng MỌI copy
- **Ngày:** 2026-07-06
- **Mức độ:** 🔴 Critical (đây là bug gốc gây ra toàn bộ sự cố "project thiếu file")
- **Vị trí:** `goi_project_capcut.py` → `_lp()`
- **Triệu chứng:** Khi xuất project ra thư mục mạng UNC (`\\192.168.1.214\e\...`), MỌI file copy fail với
  `[WinError 123] The filename, directory name, or volume label syntax is incorrect` — kể cả file local chắc chắn tồn tại (VD `D:\...\Voices\1.mp3`). Kết quả: `materials/` rỗng, CapCut đòi relink.
- **Nguyên nhân gốc:** Trên Windows, prefix extended-length khác nhau giữa 2 loại path:
  - Path có ổ: `D:\a\b` → `\\?\D:\a\b` (chỉ thêm `\\?\`)
  - Path UNC: `\\server\share\a` → `\\?\UNC\server\share\a` (**thay** 2 backslash đầu bằng `\\?\UNC\`)

  Code cũ thêm `\\?\` một cách vô điều kiện → với UNC ra `\\?\\\server\...` (SAI cú pháp) → WinError 123.
  Vì **đích** copy nằm dưới folder UNC nên MỌI file (kể cả nguồn local hợp lệ) đều fail — thông báo lỗi chỉ in path nguồn nên gây hiểu nhầm "file nguồn thiếu".
- **Cách sửa:** Viết lại `_lp()` phân biệt UNC vs drive, có nhánh `\\?\UNC\` cho UNC, và idempotent với path đã có prefix `\\?\` hoặc `\\.\`.
- **Cách phát hiện / kiểm chứng:** Unit test `_lp()` với 4 case (UNC, drive, đã-prefix drive, đã-prefix UNC) → PASS. E2E chạy thật ra đích UNC loopback `\\localhost\C$\...` → media copy OK, JSON rewrite OK. Dùng `\\localhost\C$\...` để test UNC mà không cần NAS thật.
- **Bài học (để tránh lặp lại):**
  - Bất cứ khi nào thêm prefix `\\?\` cho long-path trên Windows, PHẢI xử lý UNC riêng: `\\?\UNC\` + phần sau 2 backslash. Không bao giờ nối thẳng `\\?\` vào path bắt đầu bằng `\\`.
  - Hàm chuẩn hoá path phải **idempotent** (gọi 2 lần không hỏng).
  - Khi thấy WinError 123 hàng loạt → nghĩ ngay tới **đích** (destination) sai cú pháp, không chỉ nguồn.

### 2. File local cũng fail vì ĐÍCH nằm dưới UNC out_dir bị mangle
- **Ngày:** 2026-07-06
- **Mức độ:** 🔴 Critical (cùng gốc với #1)
- **Vị trí:** `goi_project_capcut.py` → `shutil.copy2(_lp(src), _lp(mat_dir/name))`; `os.path.getsize(_lp(sp))`
- **Triệu chứng:** File nguồn local hợp lệ (`D:\...\1.mp3`) vẫn báo "Copy loi ... WinError 123".
- **Nguyên nhân gốc:** `shutil.copy2` nhận 2 path; nguồn `\\?\D:\...` hợp lệ nhưng **đích** `_lp(mat_dir/name)` với `out_dir` là UNC → mangle → fail. Lỗi in ra chỉ path nguồn nên tưởng nguồn hỏng.
- **Cách sửa:** Fix `_lp()` (mục #1) sửa luôn cả nguồn lẫn đích.
- **Bài học:** Thông báo lỗi copy nên in **cả** nguồn và đích để chẩn đoán đúng. Một hàm path dùng chung hỏng thì mọi call site hỏng theo — sửa tận gốc, không vá từng chỗ.

### 3. `isfile_safe()` / `getsize()` nuốt lỗi UNC → misclassify "THIẾU" + size sai
- **Ngày:** 2026-07-06
- **Mức độ:** 🟠 High
- **Vị trí:** `goi_project_capcut.py` → `isfile_safe()`, vòng tính `total`
- **Triệu chứng:** File UNC tồn tại thật bị coi là "THIẾU"; tổng dung lượng "~X GB" bị đếm thiếu.
- **Nguyên nhân gốc:** `isfile_safe` bọc `try/except OSError: return False`, `getsize` bọc `except OSError: pass`. Với path UNC mangle (do `_lp` cũ), `os.path.isfile` trả False / `getsize` raise → bị nuốt âm thầm → sai.
- **Cách sửa:** Fix `_lp()` (mục #1) làm các call site này đúng trở lại — không cần sửa riêng.
- **Bài học:** `except: pass` / `return False` che giấu lỗi cú pháp path. Khi một hàm "an toàn" trả kết quả vô lý (file có thật mà báo không có), nghi ngờ path bị chuẩn hoá sai chứ đừng tin kết quả.

### 4. Ghi JSON với path gốc (chưa rewrite) khi copy fail → output KHÔNG tự chứa
- **Ngày:** 2026-07-06
- **Mức độ:** 🔴 Critical
- **Vị trí:** `goi_project_capcut.py` → vòng copy media + rewrite path + `write_json_loose`
- **Triệu chứng:** `draft_content.json`/`draft_meta_info.json` xuất ra vẫn trỏ tới ổ ngoài (E:/D:...) trong khi `materials/` rỗng → mở CapCut đòi relink.
- **Nguyên nhân gốc:** `name_for[oldp]` chỉ được set SAU khi `copy2` thành công. Copy fail hết → `name_for` rỗng → các vòng rewrite (`if path in name_for`) không đổi gì → JSON giữ path gốc. Nhưng `draft_meta_info.json` vẫn bị ghi `draft_fold_path = out_dir` → mâu thuẫn, draft hỏng.
- **Cách sửa:** Thêm đếm `copy_fail`; cảnh báo rõ; báo cáo phản ánh copy fail (xem #5). Khi `_lp` được fix thì copy thành công nên rewrite đúng.
- **Bài học:** Nếu một side-effect (copy) fail thì các bước phụ thuộc (rewrite path, ghi JSON "đã xong") KHÔNG được âm thầm tiếp tục như thể thành công. Fail phải nhìn thấy được.

### 5. `_BAO_CAO_THIEU.txt` báo "Ban tu chua DU" SAI dù không copy được file nào
- **Ngày:** 2026-07-06
- **Mức độ:** 🔴 Critical (nguy hiểm: người dùng tưởng đã xong)
- **Vị trí:** `goi_project_capcut.py` → phần ghi `_BAO_CAO_THIEU.txt`
- **Triệu chứng:** Copy fail toàn bộ nhưng báo cáo ghi `THIEU: 0` và "Khong thieu. Ban tu chua DU".
- **Nguyên nhân gốc:** `THIEU` = `len(misses)`, mà `misses` tính TRƯỚC khi copy (chỉ đếm file không resolve được ở máy nguồn). Trên máy có footage, mọi thứ resolve → `misses=0`. Copy fail chỉ `print`, không đếm. Lớp verify thứ 2 (`verify_local_media`) cũng bị lừa: vì path không rewrite nên nó check path gốc — path gốc tồn tại trên máy nguồn → `ref_missing=0`. ⇒ Báo "DU" sai.
- **Cách sửa:** Thêm `copy_fail` và `skipped_items`; đưa vào báo cáo như THIẾU thật; chỉ ghi "DU" khi `not (misses or copy_fail or skipped_items or ref_missing)`; console in "CON THIEU" khi có lỗi.
- **Cách phát hiện / kiểm chứng:** Test buộc `copy2` raise WinError 123 → báo cáo KHÔNG còn "DU", có mục "COPY THAT BAI" liệt kê file hỏng.
- **Bài học:** Chỉ số "thành công/thiếu" phải đo TRÊN KẾT QUẢ THỰC TẾ (file có mặt ở đích), không phải trên trạng thái trung gian trước khi hành động. "Tự kiểm" mà kiểm nhầm nguồn thay vì đích thì vô dụng. Mặc định phải là "chưa xong" cho tới khi chứng minh được đã xong.

### 6. `verify_local_media` false-negative 2 chiều (kiểm nhầm nguồn/đích)
- **Ngày:** 2026-07-06
- **Mức độ:** 🟠 High
- **Vị trí:** `goi_project_capcut.py` → `verify_local_media()`, `_out_media_path()`
- **Triệu chứng:** (a) Với out_dir UNC, file đã copy thành công vẫn bị báo missing (vì `_lp` mangle path kiểm tra). (b) Khi rewrite bị skip do copy fail, path gốc còn tồn tại trên máy nguồn nên bị báo "present" sai.
- **Nguyên nhân gốc:** `isfile_safe` dùng `_lp` mangle (chiều a); `_out_media_path` trả `Path(p)` cho path tuyệt đối còn sót, giả định nó "đã tính trong misses" — sai với path copy-fail (chiều b).
- **Cách sửa:** Fix `_lp` (chiều a). Chiều b được che phủ bởi cơ chế đếm `copy_fail` ở #5.
- **Bài học:** Verify phải kiểm đúng **vị trí đích thực tế** của file, không dựa vào side-effect (`name_for`) hay sự tồn tại của path nguồn.

### 7. Vòng copytree folder draft KHÔNG dùng `_lp` → fail long-path & bất đối xứng UNC
- **Ngày:** 2026-07-06
- **Mức độ:** 🟠 High
- **Vị trí:** `goi_project_capcut.py` → vòng copy folder draft (`copytree`/`copy2`)
- **Triệu chứng:** Path nguồn dài >260 ký tự trong folder draft có thể fail (WinError 3/206) nếu máy chưa bật long-path. Bất đối xứng nguy hiểm: vòng này copy được voice `./materials/*.mp3` (path thường ngắn) trong khi vòng media (dùng `_lp` cũ hỏng) fail hết → output nửa vời.
- **Cách sửa:** Bọc `_lp(item)`, `_lp(dest)` (đã fix UNC) cho cả `copytree` và `copy2`; đếm `skipped_items` đưa vào báo cáo.
- **Bài học:** Áp dụng cùng một chuẩn hoá path cho MỌI thao tác filesystem trong code, không để chỗ dùng chỗ không → hành vi bất đối xứng khó lần. Chỉ được bọc `_lp` SAU khi `_lp` đã đúng UNC (nếu không sẽ phá luôn UNC đang chạy ổn).

### 8. File `.bat` báo `'ày' is not recognized...` do comment tiếng Việt có dấu
- **Ngày:** 2026-07-06
- **Mức độ:** 🟢 Low (vô hại nhưng gây hoang mang)
- **Vị trí:** `goi_project_capcut.bat`
- **Triệu chứng:** 3 dòng lỗi đầu log: `'ày' is not recognized as an internal or external command`.
- **Nguyên nhân gốc:** Comment `REM` tiếng Việt CÓ DẤU đặt TRƯỚC `chcp 65001` → `cmd.exe` diễn giải với code page sai → phần sau khoảng trắng bị coi là lệnh.
- **Cách sửa:** Đặt `chcp 65001 >nul` ngay sau `@echo off`, và đổi comment sang tiếng Việt KHÔNG DẤU.
- **Bài học:** Trong file `.bat`: đặt `chcp` lên đầu; giữ comment ASCII/không dấu. Ký tự non-ASCII trong `.bat` rất dễ vỡ theo code page.

### 9. Nạp câu trả lời qua STDIN REDIRECT nuốt backslash đầu của UNC → output nằm SAI Ổ (D: local thay vì NAS)
- **Ngày:** 2026-07-06
- **Mức độ:** 🔴 Critical (suýt bàn giao bản nằm sai chỗ, tưởng đã lên NAS)
- **Vị trí:** Cách VẬN HÀNH tool (chạy tự động `python goi_project_capcut.py < answers.txt`), KHÔNG phải bug trong code tool.
- **Triệu chứng:** Chạy tool với đích `\\192.168.1.214\e\...\DS1_056` nhưng log lại in `Se copy ... vao \192.168.1.214\...` (chỉ MỘT backslash). 327 file copy "thành công" nhưng nằm ở `D:\192.168.1.214\e\...` (ổ D: local), NAS thì rỗng. Báo cáo ghi "XONG" nên tưởng đã lên NAS.
- **Nguyên nhân gốc:** Khi đưa đường dẫn UNC `\\server\...` qua **file answers + stdin redirect** (đặc biệt khi file answers tạo/nhìn qua shell), một backslash đầu bị nuốt → tool nhận `\server\...` (1 backslash). `os.path.abspath('\192.168.1.214\...')` coi đó là **đường dẫn TƯƠNG ĐỐI trên ổ hiện tại** (cwd = `D:\tools_goi_project_capcut`) → nối thành `D:\192.168.1.214\...`. Tool copy đúng vào chỗ nó nhận, nên không có lỗi — chỉ là SAI ĐÍCH.
- **Cách sửa:** KHÔNG truyền path UNC qua stdin redirect nữa. Dùng **Python wrapper**: gán path bằng biến Python (`chr(92)` cho backslash), monkeypatch `builtins.input` để trả lời — backslash không bao giờ bị shell/redirect đụng vào. Đồng thời trả lời input **theo NỘI DUNG câu hỏi** (prompt) chứ không theo list cứng, vì số bước thay đổi tùy có file thiếu hay không (bug #10).
- **Cách phát hiện / kiểm chứng:** Sau khi chạy, PHẢI verify output nằm ĐÚNG trên NAS (đếm `materials/` qua `_lp` UNC), KHÔNG tin dòng "XONG". So khớp `draft_fold_path` với đích mong muốn.
- **Bài học:**
  - Backslash trong path Windows bị nuốt không chỉ khi test (`python -c`) mà cả khi **nạp input tự động qua stdin/shell** — hậu quả có thể là **output nằm sai ổ mà không có lỗi nào báo**.
  - Path UNC có 1 backslash đầu (thay vì 2) → `abspath` biến thành path tương đối trên cwd → âm thầm sai. LUÔN kiểm dòng "Se copy ... vao <đích>" xem có đúng 2 backslash không.
  - Truyền path cho tiến trình con qua **biến trong ngôn ngữ** (Python wrapper), không qua text/stdin đi qua shell.
  - Sau MỌI lần chạy tự động: verify output ở đích thật, không tin thông báo "xong".

### 10. Số bước input động (bước "dò theo tên" chỉ hiện khi có file thiếu) → answers cứng bị lệch → EOFError / Da huy
- **Ngày:** 2026-07-06
- **Mức độ:** 🟠 High (chạy tự động fail giữa chừng)
- **Vị trí:** Cách vận hành tool (nạp answers cố định).
- **Triệu chứng:** (a) Với project CÓ file thiếu: tool hỏi thêm `"Thu muc/o de do"` → answers thừa 1 bước, dòng `y` không tới `Tien hanh?` → `EOFError`. (b) Với project KHÔNG thiếu: dòng Enter thừa lại bị dùng làm câu trả lời `Tien hanh?` → tool `Da huy`.
- **Nguyên nhân gốc:** Bước "dò theo tên" (`Thu muc/o de do`) CHỈ xuất hiện khi Pass 1 có file `chua thay`. Số lần `input()` vì thế thay đổi giữa các project → một list answers cứng luôn lệch ở một trong hai hướng.
- **Cách sửa:** Trả lời input **theo nội dung prompt** (đọc chuỗi câu hỏi và quyết định), không theo thứ tự cứng. Xem `smart_input` trong wrapper.
- **Bài học:** Khi tự động hóa một CLI tương tác, đừng giả định số bước cố định — map câu trả lời theo NỘI DUNG câu hỏi. Nhánh hỏi có điều kiện (chỉ hiện khi có lỗi/thiếu) là cái bẫy kinh điển.

### 11. Bỏ SÓT TOÀN BỘ "Dự án con" (subdraft) → gói thiếu media nhưng vẫn báo "Bản tự chứa ĐỦ"
- **Ngày:** 2026-08-13
- **Mức độ:** 🔴 Critical (bàn giao bản hỏng mà không hay biết — cùng họ với #5)
- **Vị trí:** `goi_project_capcut.py` → `content_path_list()`, phần rewrite path, `verify_local_media()`
- **Triệu chứng:** Project dùng tính năng **Dự án con** của CapCut (nhập project khác vào để gộp). Tool chạy xong báo `=> KHONG THIEU. Ban tu chua DU.` nhưng khi bàn giao sang máy khác, CapCut đòi relink đúng ở các clip dự án con → đoạn đó đen/mất tiếng khi xuất video. Mở trên chính máy gốc thì KHÔNG thấy lỗi.
- **Nguyên nhân gốc:** CapCut lưu dự án con ở `subdraft/<GUID>/` — mỗi cái là **một draft đầy đủ có `draft_content.json` riêng**, path media TUYỆT ĐỐI, và **lồng nhiều tầng** (đo được tới 4 tầng). Nội dung đó còn được **nhúng inline** vào `materials.drafts[].draft` của draft cha. Tool cũ:
  1. `content_path_list()` chỉ đọc `materials.videos` + `materials.audios` ở TOP LEVEL → không hề đọc `materials.drafts`;
  2. chỉ ghi lại 3 file JSON ở gốc → mọi JSON trong `subdraft/` được `copytree` nguyên văn, path tuyệt đối giữ nguyên;
  3. `verify_local_media()` cũng chỉ duyệt đúng 2 nguồn trên → không phát hiện được gì.

  Đo trên kho project thật: **53 project có dự án con thì 50 project bị bỏ sót media**; riêng `DS1_105_V3` bỏ sót 2230 file (~349 GB), `DS1_090_Tool` 381 file (~218 GB).
- **Cách sửa:** Viết lại theo hướng **đệ quy toàn gói**:
  - `collect_refs()` quét MỌI file `.json` trong draft (mọi tầng `subdraft/`) + `materials.drafts[].draft` nhúng inline;
  - `plan_package()` + `deep_rewrite_strings()` viết lại path trong CHÍNH file khai báo nó, không chỉ 3 file gốc;
  - `verify_package()` tự kiểm ĐỆ QUY trên bản xuất: còn path tuyệt đối, hoặc path tương đối trỏ tới file không có thật → báo hỏng;
  - file dùng chung bởi nhiều dự án con dùng **hard link** (fallback copy nếu ổ đích không hỗ trợ) để không nhân đôi dung lượng.
- **Cách phát hiện / kiểm chứng:**
  - Viết **verifier ĐỘC LẬP** (không import code tool — tránh sai giống nhau thì không phát hiện): quét mọi JSON trong gói, FAIL nếu còn path tuyệt đối hoặc path tương đối trỏ tới file không tồn tại.
  - A/B trên `DS3 - BÀI 6`: bản cũ **FAIL** (6 path tuyệt đối, 8 tham chiếu trỏ ngược về máy gốc) → bản mới **PASS** (0/0/0, 282 tham chiếu giải được).
  - Case khó `Intro Text` (61 JSON, 11 draft root, subdraft sâu 2 tầng): PASS.
  - **Mô phỏng bàn giao:** ĐỔI TÊN folder gói rồi verify lại → vẫn PASS (chứng minh gói độc lập vị trí).
  - Case lỗi: ép `shutil.copy2` fail xen kẽ → báo cáo ghi "CON THIEU", KHÔNG viết lại path cho file fail. Ép `os.link` luôn lỗi → fallback copy, vẫn xong.
- **Bài học (để tránh lặp lại):**
  - **"Phép thử vàng" cũ (mở bằng CapCut trên MÁY GỐC) là bằng chứng GIẢ** — path tuyệt đối vẫn resolve được trên chính máy đó. Muốn chứng minh tự chứa thì phải ĐỔI CHỖ folder / sang máy khác rồi mới kiểm.
  - Định dạng của CapCut là **cây draft lồng nhau**, không phải 1 draft phẳng. Bất kỳ xử lý nào (gom, verify, đổi path) đều phải ĐỆ QUY, không được chỉ nhìn file ở gốc.
  - Lớp tự kiểm phải quét ĐÚNG cái mà nó tuyên bố: đã nói "bản tự chứa ĐỦ" thì phải kiểm mọi tham chiếu trong mọi file, không chỉ 2 danh sách quen thuộc. Cùng bài học #5 nhưng ở phạm vi rộng hơn.
  - Verifier dùng để nghiệm thu nên viết **độc lập với code được kiểm** — nếu dùng lại chính hàm của tool thì lỗi logic chung sẽ không lộ ra.

### 12. Hiểu sai GỐC giải `##_draftpath_placeholder_..._##` → viết lại path sai cho file trong `Timelines/`
- **Ngày:** 2026-08-13
- **Mức độ:** 🟠 High (tự gây ra trong lúc sửa #11, bị chính lớp verify mới bắt được)
- **Vị trí:** `goi_project_capcut.py` → `draft_root_of()` (trước đó dùng thẳng `json_file.parent`)
- **Triệu chứng:** Sau khi sửa #11, E2E trên `DS3 - BÀI 6` báo **72 tham chiếu HỎNG**, toàn bộ nằm trong `Timelines/<GUID>/draft_content.json`, kiểu `##_..._##/materials/video/x.mp4` bị coi là trỏ tới file không tồn tại.
- **Nguyên nhân gốc:** Ban đầu tôi kết luận (từ 4 file mẫu) rằng placeholder giải theo **thư mục chứa chính file JSON**. Đúng với `subdraft/X/` (vì `subdraft/X` chính là draft root) nhưng SAI với `Timelines/Y/` — `Timelines/Y` KHÔNG phải draft root, placeholder ở đó giải theo **draft bao ngoài**. Mẫu 4 file quá nhỏ nên không lộ ra sự khác biệt.
- **Cách sửa:** Thêm `draft_root_of(json_file, top)` — lấy **tổ tiên GẦN NHẤT có `draft_meta_info.json` hoặc `sub_draft_config.json`** (không bao giờ đi cao hơn gốc gói), có cache theo thư mục. Dùng CHUNG hàm này cho cả 3 pha: `collect_refs`, `plan_package`, `verify_package` và pha áp dụng rewrite.
- **Cách phát hiện / kiểm chứng:** Viết script đo 3 giả thuyết trên **8650 đường dẫn placeholder thật của 5 project**:
  - tổ tiên gần nhất là draft root: **8643/8650 = 99.9%** ✅
  - thư mục chứa file JSON: 7364 = 85.1%
  - luôn là draft cha: 4610 = 53.3%

  (7 ca còn lại là tham chiếu vốn đã hỏng sẵn trong draft gốc.) Thêm unit test riêng cho `Timelines/T1 → draft cha` và `subdraft/S1/Timelines/T2 → S1`.
- **Bài học (để tránh lặp lại):**
  - **Đừng khái quát quy tắc từ vài mẫu.** 4 file mẫu cho ra quy tắc sai 15%; phải đo trên hàng nghìn mẫu thật rồi mới chốt, và phải so ÍT NHẤT 2 giả thuyết cạnh tranh chứ không chỉ xác nhận cái mình đang tin.
  - Trong cây draft CapCut, "draft root" được nhận biết bằng sự có mặt của `draft_meta_info.json` / `sub_draft_config.json` — KHÔNG phải cứ thư mục nào có `draft_content.json` cũng là root (`Timelines/<GUID>/` có `draft_content.json` nhưng không phải root).
  - Lớp tự kiểm mạnh có giá trị gấp đôi: nó bắt lỗi của chính người đang sửa bug, ngay trong lần chạy đầu tiên.

### 13. `import toi_uu_dung_luong` chết `ModuleNotFoundError` khi tool được gọi từ thư mục khác
- **Ngày:** 2026-08-13
- **Mức độ:** 🟠 High (tính năng mục 4 không chạy được, tool thoát ngay)
- **Vị trí:** `goi_project_capcut.py` → chỗ `import toi_uu_dung_luong as TU`
- **Triệu chứng:** Chọn chế độ **4 (Tối ưu dung lượng)** → tool in traceback `ModuleNotFoundError: No module named 'toi_uu_dung_luong'` rồi dừng, dù file đó nằm ngay cạnh `goi_project_capcut.py`.
- **Nguyên nhân gốc:** Python chỉ tự thêm thư mục của **script khởi động** vào `sys.path[0]`. Khi chạy `python goi_project_capcut.py` từ đúng thư mục thì may mắn đúng, nhưng khi tool được nạp từ nơi khác (wrapper tự động dùng `runpy`, shortcut có "Start in" khác, gọi bằng đường dẫn tuyệt đối từ thư mục khác) thì `sys.path[0]` là thư mục KHÁC → không tìm thấy module nằm cạnh nó.
- **Cách sửa:** Thêm `import_toi_uu()` — chèn `Path(__file__).resolve().parent` vào `sys.path` TRƯỚC khi import. Module `toi_uu_dung_luong.py` cũng có `_find_main_module()` để lấy lại module chính từ `sys.modules` (tránh nạp lại file lần 2 khi tool đang mang tên `__main__`).
- **Cách phát hiện / kiểm chứng:** Chạy tool qua wrapper `runpy` từ thư mục scratchpad → trước khi sửa: `ModuleNotFoundError`; sau khi sửa: chạy hết luồng bình thường.
- **Bài học (để tránh lặp lại):** Đừng dựa vào thư mục làm việc hay `sys.path` mặc định để tìm file đi kèm. Với module cạnh script, luôn tự chèn `Path(__file__).parent` vào `sys.path`. Và khi module phụ cần dùng lại hàm của script chính, phải lấy qua `sys.modules` — vì script chạy trực tiếp mang tên `__main__`, `import <ten_file>` sẽ nạp lại thành **module thứ hai** chứ không phải cái đang chạy.

### 14. Tối ưu dung lượng xong nhưng gói LẠI TO HƠN — sổ đăng ký giữ file gốc "sống"
- **Ngày:** 2026-08-13
- **Mức độ:** 🔴 Critical (tính năng phản tác dụng, mà báo cáo vẫn khoe "giảm 5.27 GB")
- **Vị trí:** `toi_uu_dung_luong.py` → `optimize_package()` / `cleanup_unused()`
- **Triệu chứng:** Chạy mục 4 trên `DS3 - BÀI 6`: console báo `Giam duoc ~5.27 GB`, nhưng đo thực tế gói **1,00 GB** trong khi gói không tối ưu chỉ **0,95 GB** — tối ưu xong lại **to hơn 5%**.
- **Nguyên nhân gốc:** Tối ưu chỉ sửa `materials.videos[].path` trong `draft_content.json` sang bản đã cắt/nén. Nhưng **sổ đăng ký `draft_materials[].file_Path` trong `draft_meta_info.json` vẫn trỏ vào file GỐC**. `cleanup_unused()` coi "có JSON tham chiếu = đang dùng" nên không dám xoá file gốc ⇒ gói chứa **cả hai bản** (gốc + bản tối ưu). Chỉ số `saved` lại tính theo *lý thuyết* (kích thước nguồn − kích thước bản mã lại) chứ không đo trên gói thật, nên vẫn báo "giảm" — đúng kiểu sai lầm của bug #5.
- **Cách sửa:** Thêm `repoint_registry()` chạy SAU khi mã lại xong: dò mọi `file_Path` trong `draft_meta_info.json` của từng draft root, cái nào trỏ tới file gốc đã có bản tối ưu thì đổi sang `./materials/<ban_toi_uu>`. Khi đó file gốc thành mồ côi và `cleanup_unused()` mới xoá được.
- **Cách phát hiện / kiểm chứng:** ĐO DUNG LƯỢNG THẬT của cả 2 thư mục xuất ra rồi so sánh, chứ không đọc con số tool tự báo. Sau khi sửa: 0,60 GB so với 0,95 GB = **giảm 37%**; số mục sổ đăng ký được trỏ lại: 6; số file thừa bị bỏ tăng từ 9 lên 15.
- **Bài học (để tránh lặp lại):**
  - Trong CapCut, **một file media được giữ sống bởi NHIỀU nơi** (content materials + sổ đăng ký + sub-draft). Muốn bỏ được một file thì phải cắt HẾT mọi đường tham chiếu tới nó, không chỉ cái rõ ràng nhất.
  - Chỉ số "tiết kiệm được bao nhiêu" phải đo trên **dung lượng thư mục đích thực tế**, không tính theo lý thuyết từng file. Lặp lại đúng bài học #5 ở một hình thức khác: đo kết quả thật, không đo ý định.

### 15. Đẩy 34 GB lên NAS rồi ĐỌC NGƯỢC QUA MẠNG để mã lại — rồi xoá đi
- **Ngày:** 2026-08-13
- **Mức độ:** 🟠 High (không sai kết quả, nhưng biến việc 1 tiếng thành nhiều tiếng)
- **Vị trí:** `goi_project_capcut.py` → thứ tự các pha trong `main()`; `toi_uu_dung_luong.py` → `resolve_material_file()`
- **Triệu chứng:** Chạy mục 4 cho `DS1_105_V2` với đích là NAS `\\192.168.1.214\...`: tool copy nguyên folder draft **34 GB** lên NAS trước, sau đó ffmpeg đọc chính các file đó **qua mạng** để mã lại, rồi cuối cùng `cleanup` xoá chúng đi. Đo được tốc độ ghi NAS chỉ **11 MB/s** ⇒ riêng bước copy vô ích đã ~52 phút, chưa kể decode file 8K (5 GB/file) qua SMB.
- **Nguyên nhân gốc:** Hai chỗ:
  1. `copytree` chạy TRƯỚC pha tối ưu và copy mọi thứ, kể cả media chắc chắn sẽ bị thay bằng bản cắt gọn.
  2. `resolve_material_file()` ưu tiên bản **trong gói** (trên NAS) thay vì bản gốc **trên máy này**, nên ffmpeg đọc qua mạng.
- **Cách sửa:** Thêm `plan_replacements()` chạy TRƯỚC `copytree` để biết file nào chắc chắn bị thay, rồi truyền `ignore=` cho `copytree` để không copy chúng. Đồng thời đảo thứ tự trong `resolve_material_file()`: **ưu tiên bản gốc trên máy này**, chỉ lùi về bản trong gói khi không còn lựa chọn.
- **Cách phát hiện / kiểm chứng:** Đo tốc độ ghi thật ra NAS bằng cách quét dung lượng thư mục đích 2 lần cách nhau 20 giây (được 11 MB/s), và đo dung lượng folder draft nguồn (34 GB) để tính ra thời gian lãng phí. Sau khi sửa, tool báo trước: `6 file trong draft se duoc thay ... KHONG copy ban goc (~0.43 GB)`.
- **Bài học (để tránh lặp lại):** Khi đích là **ổ mạng**, mọi byte ghi thừa đều đắt gấp nhiều lần. Phải quyết định "cái gì thực sự cần copy" TRƯỚC khi copy, và mọi thao tác đọc nặng (decode/encode) phải nhắm vào **bản trên máy nội bộ**. Trước khi chạy một việc dài ra ổ mạng, hãy ĐO tốc độ ghi thực tế rồi mới ước lượng thời gian.

### 16. Bỏ qua copy bản gốc làm optimizer MẤT NGUỒN ĐỌC + sổ đăng ký treo 6 tham chiếu
- **Ngày:** 2026-08-13
- **Mức độ:** 🔴 Critical (tối ưu im lặng không làm gì; gói thiếu file mà suýt không ai biết)
- **Vị trí:** `toi_uu_dung_luong.py` → `resolve_material_file()`, `repoint_registry()`
- **Triệu chứng:** Ngay sau khi thêm bản vá của #15, chạy lại thì:
  (a) `Xong toi uu sau 0s: 0/0 clip` — tối ưu **không làm gì cả**, âm thầm;
  (b) sửa xong (a) thì lại ra `! CANH BAO: 6 tham chieu HONG`, cả 6 đều là `./materials/video/...` trong `draft_meta_info.json`.
- **Nguyên nhân gốc:**
  (a) Phần lớn path trong draft là **placeholder trỏ vào chính gói** (`##..._##/materials/video/x.mp4`), không phải path tuyệt đối. Nhánh xử lý placeholder chỉ tìm trong gói — mà ta vừa cố ý KHÔNG copy file đó lên gói nữa ⇒ trả `None` ⇒ không sinh việc nào. Bản vá tăng tốc đã tự cắt mất đầu vào của chính nó.
  (b) `repoint_registry()` gọi `resolve_material_file(fp, base, base, out_dir, {})` — truyền **`base` vào chỗ tham số `draft_dir`**. Với path tương đối, hàm dựng path gốc sai ⇒ không khớp được với bảng `opt_by_src` ⇒ trỏ lại **0 mục** ⇒ 6 file gốc đã bị bỏ qua vẫn bị sổ đăng ký trỏ tới ⇒ tham chiếu treo.
- **Cách sửa:** (a) Nhánh placeholder/`./` phải **lùi về draft gốc**: ánh xạ `base` (trong gói) sang thư mục tương ứng trong `draft_dir` rồi tìm ở đó trước. (b) Truyền đúng `draft_dir` thật vào `repoint_registry()`.
- **Cách phát hiện / kiểm chứng:** Lớp tự kiểm đệ quy (`verify_package`) bắt được (b) ngay lần chạy đầu và chỉ đích danh 6 dòng trong `draft_meta_info.json`. Sau khi sửa: `So dang ky: da tro 6 muc`, `KHONG THIEU`, gói 0,60 GB so với 0,95 GB (**giảm 37%**), verifier độc lập PASS, so khung hình SSIM 10/10 khớp.
- **Bài học (để tránh lặp lại):**
  - **Tối ưu tốc độ có thể phá vỡ tính đúng đắn của bước sau.** Khi thêm một bước "bỏ bớt việc", phải rà lại mọi bước phía sau xem chúng còn tìm thấy thứ chúng cần không.
  - "Làm được 0 việc" KHÔNG phải là thành công — cần coi `0/0 clip` là tín hiệu đáng ngờ, không phải là "chạy êm".
  - Hàm nhiều tham số đường dẫn cùng kiểu (`base`, `draft_dir`, `out_dir`) rất dễ truyền nhầm mà **không hề báo lỗi**, chỉ lặng lẽ trả `None`. Khi một hàm resolve trả `None` hàng loạt, hãy nghi ngờ **thứ tự tham số** trước tiên.

### 17. Liên kết cứng ÂM THẦM rơi về copy thật trên ổ mạng → file mã lại bị nhân đôi nhiều lần
- **Ngày:** 2026-08-13
- **Mức độ:** 🟠 High (không sai kết quả, nhưng gói phình ~15–20% và tốn thêm thời gian truyền)
- **Vị trí:** `toi_uu_dung_luong.py` → `collect_jobs()` (đặt tên file đích), `optimize_package()` (nhánh `os.link`)
- **Triệu chứng:** Đang chạy gói ra NAS, kiểm giữa chừng thấy **855 file `_opt.mp4` đều có `st_nlink = 1`** — tức không có file nào là liên kết cứng. 157/207 tên gốc bị tạo nhiều bản (có cái 6 bản), tốn 3,54 GB trong khi phần thật sự khác nhau ít hơn nhiều.
- **Nguyên nhân gốc:** Mỗi **material** được cấp một tên file đích riêng (`x_opt.mp4`, `x_opt_1.mp4`...), kể cả khi hai material có **cùng nguồn + cùng điểm cắt + cùng bề rộng**. Để chống trùng, code dựa vào `os.link` (liên kết cứng). Nhưng **SMB/ổ mạng không hỗ trợ hard link** → `os.link` ném lỗi → nhánh `except` lặng lẽ quay về `shutil.copy2` → thành bản sao thật. Trên ổ local thì hard link che mất vấn đề, nên test ở local KHÔNG phát hiện được.
- **Cách sửa:** Đổi cách đặt tên: thêm bảng `key_names {(draft_root, khoá): đường_dẫn_đích}` dùng chung xuyên suốt các file content. Hai material cùng khoá `(nguồn, điểm cắt, độ dài, bề rộng)` sẽ **trỏ vào CÙNG một file đích**, đánh dấu `dup=True` và bỏ qua bước mã lại. Không còn phụ thuộc hệ thống tệp có hỗ trợ hard link hay không.
- **Cách phát hiện / kiểm chứng:** Đọc `st_nlink` của file trên đích thay vì tin rằng `os.link` đã chạy. Đo A/B trên `DS3 - BÀI 6`: file mã lại **49 → 15** (giảm 69%), cả gói **645 → 520 MB** (giảm 19%). Verifier độc lập PASS, so khung hình SSIM 10/10 khớp, 22 unit test pass.
- **Bài học (để tránh lặp lại):**
  - **Đừng chống trùng lặp bằng tính năng của hệ thống tệp.** `os.link`, symlink, reflink đều có thể không có trên đích (SMB, exFAT, FAT32). Hãy chống trùng ở **tầng logic** (đặt tên theo nội dung/khoá) để đúng ở mọi nơi.
  - Fallback trong `except` mà không đếm/không báo sẽ **giấu mất** việc tối ưu đã thất bại — đúng họ với bug #3. Nếu dùng fallback, phải đếm và đưa vào báo cáo.
  - Test trên ổ local KHÔNG chứng minh được hành vi trên ổ mạng. Với tính năng nhạy cảm về hệ thống tệp, phải kiểm ngay trên đích thật (hoặc loopback UNC `\\localhost\C$\...`).

### 18. Gom cả footage CHỈ nằm trong kho/cache (không dùng trên timeline) → bản xuất phình 8 lần
- **Ngày:** 2026-08-14
- **Mức độ:** 🔴 Critical (kế hoạch copy 511 GB, ETA 12–21 giờ, sắp làm đầy NAS)
- **Vị trí:** `goi_project_capcut.py` → `collect_refs()` / `plan_package()`
- **Triệu chứng:** Chạy chế độ 4 cho `DS1_105_V2` (timeline 38 phút). Sau pha mã lại, tool báo cần copy **4723 file / 511,46 GB**, ETA **12h–21h**, trong khi NAS chỉ còn 213 GB. Chạy tiếp chắc chắn đầy đĩa rồi hỏng.
- **Nguyên nhân gốc:** `collect_refs()` quét **mọi** file `.json` và coi mọi đường dẫn media là "phải gom". Nhưng các file `.json` trong draft có **vai trò khác nhau**:
  - `draft_content.json` / `draft_info.json` = **timeline thật** → thiếu là mất hình;
  - `draft_meta_info.json` = **kho media** hiện trong CapCut → có thể trỏ tới footage đã import rồi bỏ;
  - `mini_draft.json`, `draft_agency_*.json` = **cache/lịch sử** của CapCut.

  Đo trên project thật: **2555 file (350,10 GB) CHỈ xuất hiện ở kho/cache**, tức footage không hề nằm trên timeline. Gom chúng là vô nghĩa.
- **Cách sửa:** Thêm `json_role(name)` trả về `content` / `registry` / `cache`. Ở chế độ 4, chỉ gom media được **ít nhất một file `content`** tham chiếu (`gather_only`). `plan_package()` nhận `gather_only` và bỏ qua đường dẫn ngoài tập đó. Thêm `prune_registry()` dọn các mục sổ đăng ký trỏ tới footage không gom, để CapCut không hiện kho đầy file thiếu. Lớp tự kiểm coi tham chiếu trong file `cache` là cảnh báo, không chặn kết luận.
- **Cách phát hiện / kiểm chứng:** Đo trực tiếp: `3253 file / 400,99 GB` → `698 file / 50,89 GB` (bỏ 350,10 GB). Ba bộ test hồi quy PASS; trên project nhỏ bộ lọc là no-op (0 file bị bỏ) nên không gây hồi quy.
- **Bài học (để tránh lặp lại):**
  - **Không phải mọi tham chiếu đều bình đẳng.** Trước khi gom, phải hỏi "tham chiếu này có làm nên khung hình không?" — file cache/lịch sử của phần mềm không phải dữ liệu người dùng.
  - Khi một chỉ số vượt xa mức hợp lý (511 GB cho timeline 38 phút), **đó là dấu hiệu lỗi, không phải dữ kiện cần giải thích**. Tôi đã mất một lượt chạy vì đi biện minh cho con số thay vì nghi ngờ nó.
  - Phải **ước lượng và đối chiếu với thực tế trước khi chạy** thao tác dài/tốn tài nguyên, không chờ pha copy mới phát hiện.

### 19. Làm thiếu một nửa yêu cầu: có "hạ 4K" nhưng KHÔNG có "nén bitrate" → gói 151 GB thay vì 7 GB
- **Ngày:** 2026-08-14
- **Mức độ:** 🔴 Critical (sai lệch ~20 lần so với kết quả đúng)
- **Vị trí:** `toi_uu_dung_luong.py` → `collect_jobs()`
- **Triệu chứng:** Sau khi sửa #18, kế hoạch copy vẫn là **1586 file / 150,87 GB** cho một timeline 38 phút. Người dùng phản đối đúng: "151 GB là quá lớn so với timeline của bài đó".
- **Nguyên nhân gốc:** Yêu cầu là *"Hạ 4K / nén bitrate khung (H.264)"* — **hai việc**. Code chỉ tạo việc mã lại khi `do_trim` hoặc `do_scale`. Clip đã là 1080p và được dùng gần trọn thì **không thoả cả hai** → copy nguyên bản ở bitrate gốc (~11,5 Mbps của footage mua). Phần "nén bitrate" chưa từng được cài.
- **Cách sửa:** Thêm `do_recompress`: mã lại H.264 CRF 21 cho **mọi** material có mặt trên timeline, không phụ thuộc cắt/hạ phân giải. Kèm **van an toàn**: nếu kết quả không nhỏ hơn ít nhất 8% (và không phải job cắt gọn) thì xoá kết quả, giữ bản gốc — tối ưu không bao giờ làm file to ra.
- **Cách phát hiện / kiểm chứng:**
  - Project nhỏ `DS3 - BÀI 6`: chế độ 1 = 1024,8 MB → chế độ 4 = **265,2 MB (−74%)**; verifier độc lập PASS; so khung hình SSIM 10/10 khớp.
  - Dự báo bằng **mã thử 6 clip thật** của project lớn: bitrate ra trung bình 4,09 Mbps → **~7,3 GB** thay vì 151 GB. Một clip nguồn 951,6 MB dùng 3,7 s cho ra 0,81 MB.
- **Bài học (để tránh lặp lại):**
  - **Tách yêu cầu thành từng gạch đầu dòng rồi đánh dấu từng cái.** "Hạ 4K / nén bitrate" là hai việc; làm một cái rồi tưởng xong cả câu là lỗi đọc yêu cầu, không phải lỗi kỹ thuật.
  - Luôn có **phép thử vô lý** cho kết quả: dung lượng gói nên tỉ lệ với *thời lượng timeline × bitrate mục tiêu*. Lệch một bậc độ lớn thì dừng lại và truy, đừng giải thích.
  - Với thao tác nặng, hãy **mã thử vài mẫu thật để dự báo** trước khi chạy toàn bộ — rẻ hơn nhiều so với chạy hỏng rồi làm lại.

### 20. Bỏ qua không copy bản gốc nhưng KHÔNG trỏ lại hết tham chiếu → thiếu 41 file trong bản xuất
- **Ngày:** 2026-08-14
- **Mức độ:** 🟠 High (bản xuất thiếu media, tool tự bắt được nhưng phải sửa tay)
- **Vị trí:** `toi_uu_dung_luong.py` → `make_copy_ignore()` / bước trỏ lại tham chiếu
- **Triệu chứng:** Chạy xong `DS1_105_V2`, tool báo `CON THIEU` với **2426 tham chiếu hỏng**. Truy ra: 41 file kiểu `materials/b030_....mp4` **có trong draft gốc nhưng không có trong bản xuất**.
- **Nguyên nhân gốc:** Để tiết kiệm đường truyền, `plan_replacements()` lập danh sách file sẽ bị thay bằng bản nén rồi cho `copytree` **bỏ qua** chúng. Nhưng việc trỏ lại tham chiếu chỉ phủ được đường dẫn **tuyệt đối** (sổ đăng ký + cache). Các tham chiếu vốn đã ở dạng **tương đối** (`##_ph_##/materials/b030_....mp4`) trong file khác thì không được trỏ lại → trỏ vào file đã bị bỏ qua, không còn ở đâu cả.
- **Cách sửa:** Thêm bước **bù lại** sau khi tự kiểm: tham chiếu tương đối nào trỏ tới `<gói>/x/y` mà không có file, trong khi draft gốc có `<draft>/x/y` thì copy bù từ draft gốc. Đã bù 41 file (0,04 GB).
- **Cách phát hiện / kiểm chứng:** Đối chiếu từng đường dẫn thiếu với draft gốc: **41 bù được / 2325 không có ở đâu cả**. Sau khi bù, tự kiểm còn **0 tham chiếu hỏng do tool gây ra**.
- **Bài học (để tránh lặp lại):** Khi cố ý **không copy** một file, phải chứng minh **MỌI** tham chiếu tới nó đã được trỏ đi chỗ khác — kể cả tham chiếu đã ở dạng tương đối. An toàn hơn là luôn có bước **bù lại cuối cùng**: cái gì còn thiếu mà nguồn có thì copy bù, thay vì tin rằng đã trỏ hết.

### 21. Tự kiểm tính cả tham chiếu VỐN ĐÃ HỎNG trong draft gốc → báo "CÒN THIẾU" gây hoang mang
- **Ngày:** 2026-08-14
- **Mức độ:** 🟡 Medium (báo động giả, che mất lỗi thật)
- **Vị trí:** `goi_project_capcut.py` → `verify_package()`
- **Triệu chứng:** Sau khi bù 41 file thật sự thiếu, tool vẫn báo hàng nghìn "tham chiếu hỏng" → không phân biệt được cái nào đáng lo.
- **Nguyên nhân gốc:** `verify_package()` chỉ hỏi "file này có trên đĩa không?" mà không hỏi "**nó có trên đĩa ở máy gốc không?**". Đo thực tế: **2325/2366** tham chiếu hỏng là `Resources/videoAlg/...` — **cache do CapCut tự sinh**, đã thiếu sẵn trong draft gốc và CapCut tự tạo lại khi cần.
- **Cách sửa:** `verify_package(out_dir, draft_dir)` — tham chiếu nào cũng thiếu ở draft gốc thì xếp loại "hỏng SẴN từ draft gốc", không chặn kết luận. Chỉ tham chiếu **ta làm hỏng** mới tính là lỗi.
- **Cách phát hiện / kiểm chứng:** Sau khi sửa: `Tham chieu HONG do TA gay ra: 0 | hong san/anh bia: 6315`.
- **Bài học (để tránh lặp lại):** Lớp tự kiểm phải trả lời đúng câu hỏi **"ta có làm hỏng gì không"**, chứ không phải "mọi thứ có hoàn hảo không". Muốn vậy phải **so với trạng thái ban đầu** (draft gốc), nếu không sẽ chôn lỗi thật giữa hàng nghìn báo động giả.

### 22. Bộ kiểm khung hình bỏ sót blob dự án con + lại dính bẫy backslash qua shell
- **Ngày:** 2026-08-14
- **Mức độ:** 🟡 Medium (không sai sản phẩm, nhưng suýt bàn giao mà KHÔNG có bằng chứng)
- **Vị trí:** `scratchpad/verify_trim_frames.py`
- **Triệu chứng:** Chạy kiểm khung hình trên bản xuất thật → `So material bi cat co the kiem duoc: 0` → **không kết luận được gì**.
- **Nguyên nhân gốc:** Hai lỗi chồng nhau:
  1. Bộ kiểm chỉ đọc `materials.videos` ở **tầng ngoài cùng**, không duyệt blob dự án con nhúng inline (`materials.drafts[].draft`) — mà phần lớn clip bị cắt nằm ở đó. Sửa cách đọc: **0 → 681 ứng viên**.
  2. Truyền đường dẫn UNC qua **đối số dòng lệnh bash** → backslash bị nuốt → không tìm thấy gói. Đây là **tái phạm bug #9**, chỉ khác là qua `argv` thay vì stdin.
- **Cách sửa:** Duyệt inline blob bằng `iter_draft_objs()`; đặt đường dẫn bằng `chr(92)` ngay trong file Python + `assert` kiểm đủ 2 backslash đầu.
- **Cách phát hiện / kiểm chứng:** Sau khi sửa: 681 ứng viên, lấy mẫu 14 → **14 KHỚP / 0 LỆCH**, gồm cả clip dịch 4595 s từ file nguồn 8,75 giờ.
- **Bài học (để tránh lặp lại):**
  - **"Kiểm được 0 mẫu" KHÔNG phải là đạt** — phải coi như thất bại và đi tìm nguyên nhân. Suýt nữa tôi bàn giao mà không có bằng chứng nào.
  - Bẫy backslash không chỉ ở stdin (#9) mà ở **mọi lối đi qua shell**, kể cả `argv`. Quy tắc chung: path Windows/UNC đặt bằng biến trong Python, kèm `assert` xác nhận.

### 23. `Path("d:")` là path TƯƠNG ĐỐI theo ổ → wrapper nối vào cwd, lặp thư mục, `FileNotFoundError`
- **Ngày:** 2026-08-14
- **Mức độ:** 🟡 Medium (chạy tự động chết ngay bước đầu, không sai sản phẩm)
- **Vị trí:** `scratchpad/run_ds1_100.py` → `TOOL_DIR = Path(r"d:") / "tools_goi_project_capcut"`
- **Triệu chứng:** Wrapper chạy chế độ 4 cho `DS1_100` thoát ngay sau 0,0 phút với
  `FileNotFoundError: 'D:\tools_goi_project_capcut\tools_goi_project_capcut\goi_project_capcut.py'`
  — tên thư mục bị **lặp 2 lần**.
- **Nguyên nhân gốc:** Trên Windows, `"d:"` (không có backslash sau) là **drive-relative path**: nó nghĩa là "thư mục hiện hành TRÊN ổ D:", không phải gốc ổ D:. Vì cwd lúc đó đã là `D:\tools_goi_project_capcut`, `Path("d:") / "tools_goi_project_capcut"` cho ra `d:tools_goi_project_capcut` → khi resolve thành `D:\tools_goi_project_capcut\tools_goi_project_capcut`. Đây là **cùng họ với bug #9**: một chi tiết cú pháp path Windows biến path tuyệt đối thành tương đối một cách âm thầm.
- **Cách sửa:** Viết đủ gốc ổ: `Path("D:" + chr(92) + "tools_goi_project_capcut")`. Giữ nguyên quy ước dùng `chr(92)` cho backslash.
- **Cách phát hiện / kiểm chứng:** Thêm bước tự kiểm trước khi chạy: `assert os.path.isdir(...)` cho draft + folder cha của đích, và in ra path đã dựng để đọc bằng mắt. Sau khi sửa: `ast.parse` OK, 7/7 test prompt PASS, `Test-Path` script tool = True, chạy lại vào đúng luồng.
- **Bài học (để tránh lặp lại):**
  - `"D:"` ≠ `"D:\"` trên Windows. Path tuyệt đối phải có backslash sau dấu hai chấm; thiếu nó thì `Path`/`abspath` nối âm thầm vào cwd — **không có lỗi nào báo**, giống hệt bẫy UNC 1-backslash ở #9.
  - Wrapper tự động cũng phải `assert` mọi path nó dựng (cả nguồn lẫn ĐÍCH và cả path tới script được gọi), không chỉ path UNC.

### 24. Ước lượng thời gian SAI 2,5 lần vì đếm cả file "dùng chung" (không hề mã lại)
- **Ngày:** 2026-08-14
- **Mức độ:** 🟡 Medium (không sai sản phẩm, nhưng báo sai tiến độ cho người dùng — họ lên kế hoạch theo con số đó)
- **Vị trí:** Cách VẬN HÀNH/theo dõi tool (script đo tiến độ trong scratchpad), không phải bug trong code tool.
- **Triệu chứng:** Khi chạy `DS1_076`, tôi đo tiến độ bằng cách đếm số file `_opt` xuất hiện trên NAS trong 60 giây → ra **5,9 clip/phút** → báo người dùng "còn ~2 tiếng". Ngay sau đó bộ đếm CHÍNH THỨC của tool in `...25/454 clip (18,5 phut)` = **1,35 clip/phút** → thực tế **~5 tiếng**. Sai gần 2,5 lần, theo hướng lạc quan.
- **Nguyên nhân gốc:** `collect_jobs()` gán `dup=True` cho các material có cùng khoá `(nguồn, điểm cắt, độ dài, bề rộng)` — chúng **dùng chung một file đích**, chỉ được copy/link chứ **KHÔNG chạy ffmpeg** (xem #17). Trên project này: 1406 job nhưng chỉ **915 job thật sự mã lại**, 491 job là `dup`. Đếm file `_opt` trên đĩa là đếm CẢ hai loại, mà loại `dup` xuất hiện gần như tức thì → tốc độ đo được bị thổi phồng. Tệ hơn: các file `dup` thường xuất hiện thành cụm ở đầu, nên cửa sổ đo 60 giây rơi đúng vào đoạn "nhanh giả".
- **Cách sửa:** Lấy tiến độ từ **bộ đếm của chính tool** (`...N/M clip`, chỉ đếm `todo` = job thật sự phải mã) thay vì đếm hiện vật trên đĩa. Nếu buộc phải đo ngoài, phải trừ số job `dup` ra khỏi mẫu số, và đo trên cửa sổ đủ dài (≥5 phút) để không rơi trúng cụm nhanh giả.
- **Cách phát hiện / kiểm chứng:** So hai nguồn số liệu độc lập: bộ đếm tool (25/454 trong 18,5 phút) vs đếm file trên NAS (5,9 clip/phút). Lệch 4,4 lần → nguồn nào cũng phải giải thích được. Kiểm `os.cpu_count()` + `LoadPercentage` xác nhận CPU đã 93% (6 nhân, 6 ffmpeg) ⇒ không phải máy rảnh mà tool chạy chậm, tức con số chậm mới là con số đúng.
- **Bài học (để tránh lặp lại):**
  - **Không phải đơn vị công việc nào cũng tốn công như nhau.** Khi một pha có "việc thật" và "việc ăn theo" (dup/cache/link), đo tiến độ phải đếm ĐÚNG loại tốn thời gian, nếu không sẽ ước lượng lạc quan một cách có hệ thống.
  - **Ưu tiên bộ đếm của chính tiến trình** hơn là suy ra từ hiện vật bên ngoài (file trên đĩa). Tool biết nó còn bao nhiêu việc; đĩa thì không.
  - Khi hai phép đo lệch nhau vài lần, **con số bi quan thường là con số đúng** — vì các nguồn sai (đếm nhầm, cache, cụm nhanh giả) hầu như luôn làm kết quả có vẻ nhanh hơn thực tế.
  - Cùng họ với #19: đã trót đưa ra một con số cho người dùng thì phải **đính chính ngay khi có số đo tốt hơn**, không im lặng để họ lên kế hoạch sai.

### 25. Tool TREO VĨNH VIỄN giữa 2 file content khi đọc/ghi qua NAS — không timeout, không lỗi, không dấu hiệu
- **Ngày:** 2026-08-14
- **Mức độ:** 🔴 Critical (mất 2 tiếng chạy mà không có bất kỳ thông báo nào; người dùng tưởng đang chạy)
- **Vị trí:** `toi_uu_dung_luong.py` → `optimize_package()`, khoảng giữa 2 lần lặp `content_files` (sau khi ghi xong file content 1, trước khi log file content 2).
- **Triệu chứng:** Chạy chế độ 4 cho `DS1_076` (đích NAS `.214`, 76% footage nguồn trên NAS `.213`). Mã xong `454/454 clip (124,5 phút)` của `draft_content.json` rồi **đứng im hoàn toàn 20+ phút**: log không thêm dòng nào, tiến trình vẫn "còn sống" nên nhìn qua tưởng đang chạy.
- **Cách nhận biết chắc chắn (đo, không đoán):** Trong 90 giây liên tiếp, tiến trình có `ReadTransferCount` **+0,00 MB**, `WriteTransferCount` **+0,00 MB**, CPU **+0,02 giây**, `ThreadCount = 1`, **0 tiến trình con ffmpeg**. Tổng CPU cả đời chỉ 2,7 giây. Đối chiếu `ParentProcessId` của mọi `ffmpeg.exe` đang chạy → tất cả thuộc tiến trình KHÁC, không cái nào thuộc tiến trình này.
- **Nguyên nhân gốc:** Một lời gọi filesystem tới ổ mạng **không bao giờ trả về**. Ứng viên: `G.iter_json_files(out_dir)` / `read_json_loose` / `write_json_loose` / `os.listdir(base/'materials')` chạy trên đích UNC. SMB có thể **treo vô hạn** khi server quá tải hoặc phiên bị rớt — Python KHÔNG có timeout mặc định cho I/O filesystem, nên `os.*` sẽ chờ mãi mãi. Yếu tố kích hoạt: lúc đó có **3 tiến trình gói CapCut + 2 tiến trình autoedit** cùng kéo/đẩy dữ liệu qua cùng 2 NAS.
- **Cách sửa — ĐÃ CÀI ngày 2026-08-14** (trong `optimize_package()`): (a) log một dòng **TRƯỚC** mỗi file content (`[i/N] dang mo <file>`) chứ không chỉ sau khi đã đếm được job, để biết treo ở đâu; (b) **heartbeat 60 giây** chạy trên thread daemon riêng, in `[nhip dap] n/N clip (x phut)` và ghi rõ `(chua xong them clip nao)` khi số job đứng yên — nhờ đó "im lặng" phân biệt được với "đang chạy chậm". (c) watchdog tự huỷ: chưa cài, vẫn cần người vận hành quyết định.
- **Cách khắc phục tại chỗ:** Giết tiến trình rồi chạy lại. **Không mất công sức đã bỏ ra**: 454 file `_opt` (2,26 GB) đã nằm trên đích, lần chạy sau dùng lại nhờ `key_names`/`cache` + `copytree(dirs_exist_ok=True)`.
- **Bài học (để tránh lặp lại):**
  - **"Tiến trình còn sống" KHÔNG có nghĩa là "đang chạy".** Muốn biết nó có làm việc thật không thì phải đo `ReadTransferCount`/`WriteTransferCount`/CPU-time theo thời gian, và đếm tiến trình con. Đây là biến thể của bài học #16 ("làm được 0 việc không phải là thành công") ở tầng vận hành.
  - Khi thấy nhiều `ffmpeg.exe` đang chạy, **PHẢI kiểm `ParentProcessId`** trước khi kết luận "tool của ta đang bận" — trên máy chạy nhiều project song song, rất dễ nhận nhầm ffmpeg của tiến trình khác làm của mình (tôi đã kết luận sai đúng một lần vì bỏ qua bước này).
  - **Mọi pha dài chạy trên ổ mạng phải có heartbeat.** Một pha có thể im lặng hàng chục phút thì không phân biệt được "chậm" với "chết" — và người dùng sẽ chờ vô ích.
  - Chạy **nhiều tác vụ nặng cùng lúc trên cùng NAS** làm tăng mạnh rủi ro treo SMB, không chỉ làm chậm. Nếu buộc phải chạy song song thì càng cần heartbeat + watchdog.

- **Bổ sung 2026-08-14 (sau 2 lần BÁO ĐỘNG GIẢ ở lần chạy 2):** watchdog dựa vào *"log không đổi >15 phút"* và *"ảnh chụp thấy 0 ffmpeg"* đều **SAI**:
  - Log chỉ in mỗi 25 clip → gặp cụm file lớn thì im lặng 20+ phút là BÌNH THƯỜNG.
  - `Get-Process ffmpeg` là **ảnh chụp tức thời**, rất dễ rơi đúng khe giữa 2 clip → thấy 0 tiến trình dù đang chạy đều.
  - Tiến trình cha có `ReadTransferCount/WriteTransferCount = 0` cũng KHÔNG chứng minh treo: nó chỉ điều phối, mọi I/O nặng nằm ở **tiến trình con ffmpeg**, không tính vào bộ đếm của cha.

  **Tín hiệu ĐÁNG TIN duy nhất: tiến triển của FILE TẠM** trong `%TEMP%\capcut_opt_*`. Đo 2 lần cách nhau 60–90 giây rồi đếm: file *biến mất* (mã xong, chuyển đi) + file *tăng kích thước* + file *mới xuất hiện*. Tổng > 0 ⇒ đang chạy. Chỉ khi cả 3 đều bằng 0 liên tục **>12 phút** mới kết luận treo.

  Đối chiếu: lần treo THẬT (ở trên) thư mục tạm **rỗng 0 file** suốt 90 giây; lần báo nhầm có 4 file, trong đó 2 file xong-chuyển-đi và 2 file đang lớn dần. Khác nhau rõ rệt. Script `scratchpad/canh_bao_treo.py` cài đúng logic này.

### 26. Sổ đăng ký/cache giữ path GỐC → lên kế hoạch copy 102 GB bản gốc đã được thay bằng bản nén
- **Ngày:** 2026-08-14
- **Mức độ:** 🔴 Critical (suýt đẩy ~100 GB lên NAS 8 MB/s ≈ 3,5 giờ vô ích)
- **Vị trí:** `goi_project_capcut.py` → `plan_package()` (thứ tự so với `repoint_registry`); `toi_uu_dung_luong.py` → `optimize_package()` (không trả bảng ánh xạ)
- **Triệu chứng:** Chạy chế độ 4 cho `DS1_085` (footage nằm ở NAS `.213` và nhiều ổ D: khác). Tool in `0 file trong draft se duoc thay bang ban cat gon/nen -> KHONG copy ban goc (~0.00 GB)` rồi báo `Se gom toi da 300 file (~99.74 GB)` và bắt đầu copy. Đo tốc độ ghi NAS thật = **8,0 MB/s** ⇒ riêng bước copy này ~3,5 giờ, trong khi kết quả đúng chỉ ~5 GB.
- **Nguyên nhân gốc:** Hai tầng chồng nhau, cùng họ với #14 và #16:
  1. `plan_replacements()` (chạy trước, để bảo `copytree` bỏ qua) chỉ nhận file thoả `_is_under(k, draft_dir)`. Nhưng ở project này **270/306 media nằm NGOÀI folder draft** ⇒ trả về 0. Bản thân điều này KHÔNG sai (copytree chỉ copy nội dung draft), nhưng dòng log "0 file" khiến ta tưởng tối ưu không hoạt động.
  2. Lỗi thật: **`plan_package()` chạy TRƯỚC `repoint_registry()`**. Pha tối ưu chỉ đổi `materials.videos[].path` trong file `content`; **sổ đăng ký `draft_meta_info.json` và các file cache vẫn giữ path GỐC**. `plan_package` thấy path gốc đó, không biết chúng đã có bản `_opt.mp4`, nên lập kế hoạch copy đầy đủ bản gốc.
- **Cách sửa:** `optimize_package()` trả thêm `st["opt_by_src"]` (bảng `(draft_root, file_gốc) → bản_tối_ưu`). `plan_package()` nhận tham số `opt_by_src`, thêm nhánh (0): path nào đã có bản tối ưu thì **trỏ thẳng sang bản đó**, không copy bản gốc — tra theo cả khoá `(root, src)` lẫn riêng `src` (vì sổ đăng ký của root này có thể trỏ tới file được tối ưu ở root khác). Sửa luôn dòng log để "0 file" không bị hiểu nhầm.
- **Cách phát hiện / kiểm chứng:** Dựng sân chơi chỉ copy 112 file `.json` (không copy media) rồi **giả lập pha tối ưu** + xây `opt_by_src` như thật, đo `plan_package` hai lần:
  - không truyền `opt_by_src`: **355 file / 102,33 GB**
  - có truyền: **139 file / 0,47 GB** ⇒ giảm 101,85 GB.

  Đối chiếu độc lập bằng cách phân loại media theo vai trò: bắt buộc copy = audio (47 file, 0,21 GB) + video không tối ưu (52, 0,06 GB) + ảnh (83, 0,07 GB) = **0,28 GB**; phần bỏ được = 166 file video có bản tối ưu = **99,42 GB**. Hai phép đo độc lập cho cùng kết luận.
- **Bài học (để tránh lặp lại):**
  - **Thứ tự các pha là một phần của tính đúng đắn.** Một bước "dọn dẹp/trỏ lại" chạy SAU bước "lên kế hoạch" thì kế hoạch không bao giờ thấy được kết quả dọn dẹp. Khi thêm pha mới, phải vẽ lại thứ tự và hỏi "pha nào đọc dữ liệu mà pha sau mới sửa?".
  - Lặp lại bài học #14 lần thứ hai: trong CapCut **một file được giữ sống bởi nhiều nơi** (content + sổ đăng ký + cache). Lần #14 hậu quả là gói to hơn; lần này là copy 100 GB qua mạng. Hễ đụng tới "thay thế/bỏ file", phải liệt kê ĐỦ mọi nơi tham chiếu tới nó.
  - Dòng log `0 file ...` là **tín hiệu phải dừng lại kiểm tra**, đúng như #16 đã ghi. Lần này nó cứu được 3,5 giờ: thấy `0` mâu thuẫn với dự báo "617 clip cần mã lại" nên dừng trước khi ghi ra NAS. Xem thêm mục #27 (cùng lần chạy).
  - Khi một chỉ số vô lý (99,74 GB cho timeline 39 phút), **đo lại bằng một con đường độc lập** thay vì tin con số tool in ra (lặp #18, #19).

### 27. Dò file thiếu quét cạn cả ổ mạng 22 TB để tìm file người dùng đã cố ý xoá
- **Ngày:** 2026-08-14
- **Mức độ:** 🟡 Medium (không sai kết quả, nhưng treo hàng giờ ở bước phụ)
- **Vị trí:** Cách vận hành (`index_by_names` + câu hỏi "Thu muc/o de do [Enter = tat ca o]")
- **Triệu chứng:** Pass 1 resolve 297/301 file; 4 file còn lại đưa sang bước "dò theo tên". Trả lời Enter (= tất cả ổ) khiến tool quét `Y:` (9 TB) và `Z:` (13,4 TB) — đều là ổ mạng SMB. Sau 417.000 thư mục vẫn `thay 1/2`, ước tính còn nhiều giờ, trong khi file còn lại là bản nhạc bản quyền người dùng **cố ý xoá** nên không bao giờ tìm thấy.
- **Nguyên nhân gốc:** `index_by_names` chỉ dừng sớm khi tìm ĐỦ. Với file chắc chắn không tồn tại, nó buộc phải quét cạn mọi ổ được liệt kê. `fixed_drives()` liệt kê cả ổ mạng đã map (Y:, Z:) mà không phân biệt local/mạng, và không cảnh báo dung lượng.
- **Cách sửa (vận hành):** Trả lời câu hỏi bằng danh sách ổ CỤ THỂ (`C:\ ; D:\`) thay vì Enter, sau khi đã xác minh Pass 1 phủ hết footage thật. Kết quả: resolve **300/301** (tốt hơn cả lần quét toàn bộ) trong vài phút.
- **Cách phát hiện / kiểm chứng:** So `Get-PSDrive` để biết ổ nào là ổ mạng (`DisplayRoot` có giá trị) và dung lượng; đối chiếu với danh sách nguồn footage thật (108 file trên `\\192.168.1.213`, đều resolve đúng ở Pass 1 nên không cần dò).
- **Bài học (để tránh lặp lại):**
  - Trước khi trả lời "quét tất cả ổ", hãy **xem có ổ mạng nào trong danh sách không** — quét TB qua SMB đắt hơn nhiều bậc so với ổ local.
  - Bước dò chỉ có ích cho file **đã bị relink/di chuyển**. File người dùng chủ động xoá sẽ khiến nó quét cạn vô ích ⇒ nên hỏi người dùng trước khi bỏ ra hàng giờ.
  - Cải tiến nên làm cho tool: cảnh báo khi danh sách dò gồm ổ mạng, và cho phép bỏ qua từng file thiếu đã biết.

### 28. TREO lần hai — lần này ở `plan_replacements()`, pha "tính trước" hỏi hàng nghìn file qua NAS
- **Ngày:** 2026-08-14
- **Mức độ:** 🔴 Critical (treo chết, mất ~25 phút mỗi lần chạy, không có dấu hiệu)
- **Vị trí:** `toi_uu_dung_luong.py` → `plan_replacements()` / `resolve_material_file()`
- **Triệu chứng:** Sau khi sửa #26, chạy lại `DS1_085`. Log dừng ở `--- THIEU ---` rồi **im lặng hoàn toàn**. Đo tiến trình: trong **75 giây** liên tiếp `ReadTransferCount +0,00 MB`, `WriteTransferCount +0,00 MB`, `ReadOperationCount +0`, `CPU +0,00s`, `ThreadCount = 1`. Trên máy có 4 `ffmpeg.exe` đang chạy nhưng `ParentProcessId` của chúng là tiến trình KHÁC — không phải của tool (đúng cái bẫy nhận nhầm mà #25 đã cảnh báo).
- **Nguyên nhân gốc:** Cùng gốc với #25 nhưng ở **pha khác**: `plan_replacements()` duyệt mọi file content rồi gọi `resolve_material_file()` cho từng material — mỗi lần lại `isfile_safe()` một đường dẫn trên NAS `.213`. Với 967 material (nhiều file bị hỏi lặp lại hàng chục lần) thì đó là hàng nghìn round-trip SMB. Khi NAS nghẽn (máy đang chạy nhiều tác vụ nặng song song), một lời gọi `os.path.isfile` **không bao giờ trả về** — Python không có timeout cho I/O filesystem. Heartbeat đã cài ở #25 nằm trong `optimize_package()`, chạy SAU pha này nên không bảo vệ được.
- **Cách sửa:** Ba lớp:
  1. **Bộ nhớ đệm `_EXIST_CACHE`** cho `isfile_safe` (hàm `_exists()`): cùng một đường dẫn chỉ hỏi ổ mạng đúng một lần thay vì hàng chục lần.
  2. **Heartbeat 30 giây** cho `plan_replacements` (tách thân hàm ra `_plan_replacements_body` để bọc được), in `[nhip dap] da xet N file content` và ghi rõ `(DUNG YEN - co the dang cho o mang)` khi số liệu đứng yên.
  3. **Bỏ hẳn pha này khi không cần**: đếm trước bằng `resolved` (dữ liệu đã có sẵn, không tốn I/O) xem có media nào nằm TRONG folder draft không; nếu không có thì `plan_replacements` chắc chắn trả về rỗng ⇒ không chạy. Ở `DS1_085`, cả 300 file đều nằm ngoài draft nên pha này bị bỏ hoàn toàn.
- **Cách phát hiện / kiểm chứng:** Đo `ReadTransferCount`/`WriteTransferCount`/`CPU` trong 20s rồi 75s (không kết luận từ một phép đo ngắn); kiểm `ParentProcessId` của mọi `ffmpeg.exe` để loại trừ nhầm lẫn.
- **Bài học (để tránh lặp lại):**
  - **Sửa một chỗ treo không sửa được các chỗ khác cùng loại.** #25 vá `optimize_package`, nhưng nguyên nhân gốc (I/O đồng bộ không timeout trên SMB) tồn tại ở MỌI pha đụng ổ mạng. Khi gặp lỗi hạ tầng như vậy, phải rà **tất cả** các pha cùng đặc điểm, chứ không chỉ chỗ vừa cháy.
  - **Cách rẻ nhất để không treo là không gọi.** Trước khi bỏ hàng chục phút I/O mạng, hãy hỏi "pha này có thể trả về gì khác rỗng không?" — nếu dữ liệu sẵn có đủ để trả lời thì bỏ hẳn pha đó.
  - Hỏi đi hỏi lại cùng một đường dẫn qua mạng là **lỗi hiệu năng nghiêm trọng**, không phải chi tiết nhỏ: cache một dòng cắt hàng nghìn round-trip.
  - **Đo I/O của tiến trình CHA là chưa đủ trong pha mã lại.** Khi ffmpeg đang chạy, tiến trình Python cha có `Read/Write/CPU = +0` suốt nhiều phút vì nó chỉ ngồi chờ tiến trình con — nhìn qua giống hệt treo chết. Muốn kết luận đúng phải đo **CPU cộng dồn của các tiến trình con `ffmpeg.exe` có `ParentProcessId` = PID tool** (đo được +4,91s/30s ⇒ đang chạy thật). Vì vậy nhãn `(chua xong them clip nao)` chỉ nên coi là *gợi ý kiểm tra*, không phải kết luận treo.

### 49. Verifier nghiệm thu báo động giả: coi `material_name` là đường dẫn + không biết `##_subdraft_placeholder_..._##`
> *(Mục này trước đây bị đánh nhầm số **24**, trùng với mục 24 ở trên. Đổi thành 49 ngày 2026-08-18 (số 38 đã bị mục khác dùng) — xem mục 42.)*
- **Ngày:** 2026-08-14
- **Mức độ:** 🟡 Medium (không sai sản phẩm, nhưng suýt kết luận nhầm là gói HỎNG)
- **Vị trí:** `scratchpad/verify_doc_lap.py` → `is_media_path()` / `scan()`
- **Triệu chứng:** Verify bản xuất `DS1_100` sau khi ĐỔI TÊN gói (phép thử vàng) → báo **628 đường dẫn tuyệt đối** và **2605 tham chiếu "content" HỎNG**. Nhìn qua tưởng gói hỏng nặng, không bàn giao được.
- **Nguyên nhân gốc:** Hai lỗi trong chính bộ kiểm (không phải trong tool):
  1. Bộ kiểm nhận MỌI chuỗi kết thúc bằng đuôi media là "đường dẫn". Nhưng CapCut có nhiều khoá chỉ là **TÊN HIỂN THỊ**, không phải path: `material_name`, `materialName`, `extra_info`. Chúng chứa `abc.mp4` nên bị tính là "path tương đối hỏng". Lọc lại chỉ theo khoá path thật (`path`, `file_Path`, `source_path`) thì 2605 → **192**.
  2. Bộ kiểm chỉ biết `##_draftpath_placeholder_<GUID>_##`, KHÔNG biết dạng thứ hai **`##_subdraft_placeholder_<GUID>_##`**. 192 tham chiếu còn lại dùng dạng này nên không giải được.
  Ngoài ra 615/628 path tuyệt đối nằm ở file vai trò `cache` (`mini_draft.json`, `draft_agency_config.json`) — CapCut tự sinh lại, không làm nên khung hình.
- **Cách sửa:** Phân loại theo **vai trò file** (`json_role`) + **chỉ xét khoá đường dẫn thật** + hiểu cả 2 dạng placeholder. Quan trọng nhất: **so với DRAFT GỐC** thay vì hỏi "có hoàn hảo không" (đúng bài học #21).
- **Cách phát hiện / kiểm chứng:** Đối chiếu song song gốc ↔ gói, chỉ file `content` + khoá path thật:
  `DRAFT GOC: giai duoc 2011 | HONG 186` — `BAN XUAT: giai duoc 2538 | HONG 186` → **tham chiếu hỏng do TA gây ra = 0**. 186 ca hỏng là `##_subdraft_placeholder_536E1D01..._##/materials/seg_*.wav`, GUID đó KHÔNG tồn tại ở cả máy gốc lẫn gói ⇒ rác có sẵn. Bản xuất còn giải được NHIỀU HƠN gốc (2538 > 2011) vì media rải nhiều ổ đã được gom về.
- **Bài học (để tránh lặp lại):**
  - Trong JSON của CapCut, **đuôi file KHÔNG đủ để kết luận một chuỗi là đường dẫn**. Phải lọc theo TÊN KHOÁ; `material_name`/`extra_info` chỉ là nhãn hiển thị.
  - Có **hai** dạng placeholder: `##_draftpath_placeholder_..._##` (gốc = draft root) và `##_subdraft_placeholder_..._##`. Bộ kiểm thiếu một dạng sẽ báo động giả hàng loạt.
  - Bộ kiểm nghiệm thu cũng là code — **nó cũng có bug**. Khi nó báo con số vô lý (2605 hỏng mà tool bảo 0), hãy nghi ngờ bộ kiểm trước, và LUÔN kết luận bằng cách **so với trạng thái gốc**, không so với sự hoàn hảo tuyệt đối.

### 39. Kết luận "đoạn cắt BỊ LỆCH" từ SSIM thấp — thực ra là giới hạn của phép đo trên footage chuyển động nhanh
> *(Mục này trước đây bị đánh nhầm số **25**, trùng với mục 25 ở trên. Đổi thành 39 ngày 2026-08-18 — xem mục 42.)*
- **Ngày:** 2026-08-14
- **Mức độ:** 🟡 Medium (báo động giả, suýt kết luận sản phẩm hỏng và chạy lại 2,5 giờ)
- **Vị trí:** `scratchpad/kiem_khung_hinh.py` (bộ kiểm, không phải tool)
- **Triệu chứng:** So khung hình 10 mẫu trên bản xuất `DS1_100`: 9 KHỚP, riêng clip `9.mp4` báo **SSIM 0,690 → "LECH!"**. Kiểm lại với offset chính xác còn tệ hơn: 3/3 mẫu SSIM 0,29–0,66.
- **Nguyên nhân gốc:** Hai tầng, cả hai đều ở BỘ ĐO:
  1. Script dò offset bằng cách quét bước thô (`(dài_gốc − dài_mới)/40 ≈ 0,36 s`) nên chọn `lo≈2,2 s` thay vì `2,066666 s` — lệch 0,13 s.
  2. Ngay cả với offset ĐÚNG, SSIM vẫn thấp vì so **3840x2160 với 2112x1188** trên cảnh cá heo bơi rất nhanh: mất chi tiết + lệch một phần giây làm SSIM tụt mạnh.
  **Phép kiểm soát quyết định:** so CHÍNH file gốc với CHÍNH NÓ lệch 0,17 s → **SSIM chỉ 0,5553** (lệch 0,5 s → 0,4734). Trong khi bản cắt so với gốc đạt **0,6579 — CAO HƠN ngưỡng nhiễu đó** ⇒ bản cắt khớp tốt hơn mức mà phương pháp đo có thể phân giải.
- **Cách sửa:** Không sửa tool (tool đúng). Kết luận dựa vào **số học của `source_timerange`**: gốc `start=2,566666s` → gói `start=0,5s`, `duration` GIỮ NGUYÊN `6,533334s`, `lo=2,066666s` = đúng vùng cắt trừ đệm 0,5 s. Khi dùng SSIM, phải kèm **phép kiểm soát** (gốc-vs-gốc lệch cùng khoảng) để biết ngưỡng nhiễu.
- **Cách phát hiện / kiểm chứng:** 9/10 mẫu khác đạt SSIM 0,962–0,994 (cảnh chậm) — chứng tỏ phương pháp đúng nói chung, chỉ hỏng ở cảnh chuyển động nhanh. Tool cũng tự kiểm `OK: moi doan dung deu nam trong pham vi clip`.
- **Bài học (để tránh lặp lại):**
  - **SSIM tuyệt đối không có ý nghĩa nếu không có mốc so sánh.** Luôn chạy phép kiểm soát "gốc vs gốc lệch Δt" để biết SSIM bao nhiêu là "khớp" cho CHÍNH clip đó. Cảnh tĩnh 0,99; cảnh động có thể chỉ 0,55 dù đúng hoàn toàn.
  - Khi dò offset bằng cách quét, **bước quét phải mịn hơn 1 khung hình**, nếu không sai số của bộ đo lớn hơn thứ cần đo.
  - Ưu tiên bằng chứng **số học chính xác** (`source_timerange`) hơn bằng chứng **thống kê mờ** (SSIM). Dùng SSIM để phát hiện sai lớn, không dùng để phán quyết sai nhỏ.
  - Lặp lại #24: khi bộ kiểm báo lỗi mà tool bảo OK, hãy nghi ngờ BỘ KIỂM trước khi kết luận sản phẩm hỏng.

### 29. Cache mã lại KHÔNG sống qua các lần chạy → chạy lại là mã lại TỪ ĐẦU, sinh bộ file trùng
- **Ngày:** 2026-08-14
- **Mức độ:** 🟠 High (không sai sản phẩm nhờ `cleanup_unused`, nhưng lãng phí ~2 giờ CPU và làm gói phình gấp 3 giữa chừng)
- **Vị trí:** `toi_uu_dung_luong.py` → `optimize_package()`: `cache = {}` và `key_names = {}` khởi tạo rỗng mỗi lần gọi.
- **Triệu chứng:** `DS1_076` chạy lần 1 mã xong 454 clip (2,26 GB `_opt` đã nằm trên đích) rồi bị treo (#25/#28) → giết tiến trình → chạy lại. Sau khi lần 2 xong file content 1, số file `_opt` trên đích **tăng gấp đôi: 454 → 907 (2,26 → 4,52 GB)**, và cuối pha mã lại lên tới **1367 file / 6,80 GB** trong khi gói thật chỉ ~2,3 GB.
- **Nguyên nhân gốc:** `cache` (key → dest đã mã) và `key_names` chỉ tồn tại **trong bộ nhớ của MỘT lần chạy**. Lần chạy mới bắt đầu với cache rỗng và **không hề quét đĩa** để nhận ra "clip này đã có bản `_opt` rồi". Tên đích `x_opt.mp4` đã bị bộ cũ chiếm nên `_uniq_name()` cấp tên mới `x_opt_1.mp4` → mã lại từ đầu, tạo bộ thứ hai song song với bộ cũ.
- **Hệ quả thực tế:** bộ cũ thành mồ côi (không JSON nào trỏ tới) và được `cleanup_unused()` dọn ở cuối, nên **gói bàn giao vẫn ĐÚNG**. Cái mất là thời gian: mã lại 454 clip = ~113 phút CPU hoàn toàn vô ích, cộng dung lượng đỉnh gấp 3 trên NAS (rủi ro đầy đĩa nếu project lớn).
- **Cách sửa — ĐÃ CÀI (xem mục 32; xác minh lại 2026-08-18: `_load_opt_index()` có trong code):** đầu `optimize_package()` **nạp cache từ đĩa**: quét `<base>/materials/*_opt*.mp4` sẵn có, dùng `ffprobe` lấy `duration`/`width` rồi đối chiếu với khoá `(nguồn, điểm cắt, độ dài, bề rộng)`; khớp thì nạp thẳng vào `cache`/`key_names` và bỏ qua mã lại. Hoặc đơn giản hơn: ghi một file `_opt_index.json` cạnh `materials/` ánh xạ khoá → tên file, đọc lại ở lần chạy sau.
- **Cách phát hiện / kiểm chứng:** ĐẾM file `_opt` trên đích trước và sau khi chạy lại. Nếu tăng gần gấp đôi thay vì giữ nguyên ⇒ cache không được dùng lại. (Tôi đã sai khi **khẳng định với người dùng** rằng "chạy lại sẽ dùng lại 454 file đã mã" mà không kiểm chứng — thực tế ngược lại.)
- **Bài học (để tránh lặp lại):**
  - **Cache trong RAM không phải là khả năng phục hồi.** Với pha chạy hàng giờ trên ổ mạng — nơi treo/giết tiến trình là chuyện thường (#25, #28) — trạng thái phải nằm trên ĐĨA thì việc "chạy lại" mới rẻ.
  - Đừng hứa "chạy lại sẽ dùng lại kết quả cũ" **trước khi kiểm chứng bằng số đếm thật**. Cùng bài học #24: nói theo suy luận về code thay vì theo phép đo là nguồn gốc của việc báo sai cho người dùng.
  - Dấu hiệu nhận biết sớm: dung lượng đích **tăng vượt mức hợp lý** giữa chừng (6,80 GB cho gói ~2,3 GB). Áp dụng đúng "phép thử vô lý" của #18/#19 cho cả trạng thái TRUNG GIAN, không chỉ kết quả cuối.

### 30. Bộ đếm `nen bitrate` LUÔN = 0 và `Giam duoc` = 1817 GB (nguồn chỉ có 146 GB) — hai chỉ số vô nghĩa trong báo cáo
- **Ngày:** 2026-08-14
- **Mức độ:** 🟡 Medium (sản phẩm ĐÚNG; nhưng báo cáo sai làm người đọc không biết tính năng có chạy không — suýt kết luận nhầm là lặp lại #19)
- **Vị trí:** `toi_uu_dung_luong.py` → `collect_jobs()` (không đặt khoá `recompress` vào job) và `optimize_package()` (dòng `st["recompress"] += 1 if j.get("recompress") ...`, `st["saved"] += max(0, j["size"] - new_size)`).
- **Triệu chứng:** Chạy xong `DS1_076`: `nen bitrate 0` dù chế độ 4 bật `recompress: True`, và `Giam duoc ~1817.16 GB` trong khi **toàn bộ footage nguồn chỉ 146,10 GB** — giảm nhiều hơn cả thứ đang có.
- **Nguyên nhân gốc:** Hai lỗi đếm độc lập:
  1. `collect_jobs()` chỉ dùng `do_recompress` làm **biến cục bộ** để quyết định có tạo job hay không, KHÔNG ghi `"recompress": do_recompress` vào dict job. `optimize_package()` lại đọc `j.get("recompress")` ⇒ luôn `None` ⇒ bộ đếm mãi bằng 0.
  2. `st["saved"]` cộng `j["size"] - new_size` cho **mọi job**, kể cả 1411 job `dup`/`reused` dùng chung một file nguồn. Một file 7,5 GB được 20 material tham chiếu sẽ được cộng "tiết kiệm" 20 lần ⇒ tổng vượt xa dung lượng nguồn thật.
- **Cách sửa — ĐÃ CÀI (xem mục 32; xác minh lại 2026-08-18: `_saved_srcs` và `"recompress"` có trong code):** (1) thêm `"recompress": do_recompress` vào dict job trong `collect_jobs()`; (2) `saved` phải cộng theo **file nguồn duy nhất** (`set` các `src` đã xử lý), hoặc bỏ hẳn và chỉ báo **dung lượng thư mục đích đo thật** — đúng bài học #14.
- **Cách phát hiện / kiểm chứng:** Áp "phép thử vô lý" (#18/#19): `saved` > tổng dung lượng nguồn là bất khả thi ⇒ chắc chắn lỗi đếm. Kiểm tính năng nén có chạy thật không thì **đo sản phẩm**, không đọc bộ đếm: gói cuối **5,08 GB** từ nguồn **146,10 GB** (giảm 96,5%), `phan ma lai chiem 9.19 GB` — con số hợp lý cho timeline 44 phút ⇒ nén bitrate CÓ chạy. Khác hẳn #19 (khi đó tính năng thật sự chưa được cài và gói ra 151 GB).
- **Bài học (để tránh lặp lại):**
  - **Bộ đếm bằng 0 không chứng minh tính năng không chạy, và số "tiết kiệm" to không chứng minh nó chạy tốt.** Muốn biết sự thật thì đo **dung lượng thư mục đích thật** (#14) — mọi chỉ số nội bộ chỉ là giả thuyết.
  - Khi có job `dup`/`reused`, MỌI phép cộng dồn theo job đều có nguy cơ đếm trùng. Cộng theo **thực thể duy nhất** (file nguồn), không theo lượt tham chiếu. Cùng họ #24 (đếm nhầm vì trộn hai loại đơn vị công việc).
  - Chỉ số trong báo cáo bàn giao mà sai một bậc độ lớn sẽ **phá niềm tin vào cả báo cáo** — kể cả khi sản phẩm hoàn toàn đúng.

### 31. Verifier độc lập báo FAIL 948 path tuyệt đối — thực ra toàn bộ nằm trong file CACHE
- **Ngày:** 2026-08-14
- **Mức độ:** 🟡 Medium (báo động giả ở khâu nghiệm thu; suýt kết luận gói hỏng và chạy lại vô ích)
- **Vị trí:** `scratchpad/verifier_doclap.py` → nhánh `if is_abs_media(v)`.
- **Triệu chứng:** Sau khi tool báo `KHONG THIEU. Ban tu chua DU`, verifier độc lập báo **FAIL: 948 path TUYET DOI con lai**.
- **Nguyên nhân gốc:** Verifier xếp MỌI path tuyệt đối là lỗi chặn, trong khi nó **đã có** biến `is_cache` để phân loại nhưng chỉ dùng cho nhánh "file không tồn tại", quên áp cho nhánh path tuyệt đối. Đếm theo file cho thấy 100% nằm ở `draft_agency_config.json` (839), `mini_draft.json` (458), `draft_agency_info.json` (16) — **toàn file cache**, 0 cái trong `draft_content.json`/`draft_info.json`.
- **Cách sửa:** `(cache_broken if _c else abs_left).append(...)` — path tuyệt đối trong file cache là cảnh báo, không chặn. Sau khi sửa: **PASS, 0 path tuyệt đối, 0 tham chiếu hỏng do tool**.
- **Cách phát hiện / kiểm chứng:** Trước khi tin kết luận FAIL, **đếm lỗi theo TỪNG FILE và tra vai trò của file đó** (`json_role`). Nếu 100% lỗi rơi vào file cache thì vấn đề nằm ở bộ kiểm, không ở sản phẩm.
- **Bài học (để tránh lặp lại):**
  - Bài học #18/#21 (phân biệt content/registry/cache) phải áp cho **CẢ verifier nghiệm thu**, không chỉ cho tool. Verifier viết độc lập rất dễ quên đúng cái luật mà tool đã học được qua nhiều bug.
  - Khi verifier và tool mâu thuẫn, **đừng vội tin bên nào** — hãy phân rã con số lỗi theo nhóm (file nào, vai trò gì). Ở đây phân rã lộ ngay ra 100% là cache.
  - Lặp lại #24: bộ kiểm báo lỗi mà tool bảo OK thì nghi ngờ BỘ KIỂM trước.

### 32. Cài phần "chưa cài" của #29 và #30 — cache mã lại sống qua các lần chạy + hai bộ đếm sai
- **Ngày:** 2026-08-18
- **Mức độ:** 🟠 High (lãng phí hàng giờ CPU khi chạy lại + rủi ro đầy đĩa đích; báo cáo sai số liệu)
- **Vị trí:** `toi_uu_dung_luong.py` → `_load_opt_index()` / `_save_opt_index()` / `optimize_package()` / `collect_jobs()`; `goi_project_capcut.py` → chỗ dọn sau `verify_optimize()`.
- **Triệu chứng:** Mục #29 và #30 trong nhật ký này đều ghi **"Cách sửa (chưa cài)"** — tức là bug đã được phân tích nhưng code chưa hề được sửa. Hậu quả còn nguyên: (a) chạy lại sau khi bị treo/giết là **mã lại từ đầu**, sinh bộ file `_opt` trùng (454 → 907 → 1367 file); (b) `nen bitrate` luôn `0` và `Giam duoc` vượt cả dung lượng nguồn (1817 GB / 146 GB).
- **Nguyên nhân gốc:**
  1. **#29:** `cache` và `key_names` khởi tạo rỗng mỗi lần gọi `optimize_package()`, chỉ sống trong RAM. Không có bước nào đọc đĩa để biết "clip này đã mã rồi".
  2. **#30a:** `collect_jobs()` dùng `do_recompress` làm biến cục bộ, KHÔNG ghi `"recompress"` vào dict job, trong khi `optimize_package()` lại đọc `j.get("recompress")` ⇒ luôn `None`.
  3. **#30b:** `st["saved"]` cộng theo **mỗi job**, kể cả job `dup`/`reused` trỏ chung một file nguồn ⇒ một file 7,5 GB được 20 material dùng bị cộng 20 lần.
- **Cách sửa:**
  1. Thêm `_load_opt_index()` / `_save_opt_index()` ghi `_opt_index.json` ở gốc bản xuất, ánh xạ `key = (src_normcase, lo, span, target_w)` → file đích. Nạp ở đầu `optimize_package()`; **chỉ nhận mục có file đích CÒN TỒN TẠI THẬT** (mất file ⇒ coi như chưa làm, đúng nguyên tắc "mặc định CHƯA XONG"). Index hỏng/không đọc được thì trả rỗng chứ không làm chết tiến trình.
  2. Ghi index **định kỳ trong heartbeat (60 s)** và sau mỗi pha mã của từng file content ⇒ bị giết giữa chừng chỉ mất tối đa ~60 giây công, không mất cả pha.
  3. Xoá `_opt_index.json` sau khi `verify_optimize()` ĐẠT (nó chỉ phục vụ việc chạy lại, không được lẫn vào gói bàn giao). `cleanup_unused()` không đụng tới nó vì chỉ dọn media trong `materials/`.
  4. Thêm `"recompress": do_recompress` vào dict job; `st["saved"]` cộng theo `set` file nguồn duy nhất (`_saved_srcs`).
- **Cách phát hiện / kiểm chứng:** Unit test `scratchpad/test_cache.py` — 14 phép kiểm PASS: round-trip ghi/đọc, khoá giữ nguyên `int` sau JSON (không thành `str`), mục mất file đích bị loại, index hỏng không ném lỗi, **UNC loopback `\\localhost\C$\...`**, path có dấu tiếng Việt/khoảng trắng. Kiểm chứng thật khi chạy: đếm file `_opt` trên đích trước/sau khi chạy lại — phải GIỮ NGUYÊN, không tăng gần gấp đôi.
- **Bài học (để tránh lặp lại):**
  - **Ghi "cách sửa (chưa cài)" vào nhật ký KHÔNG phải là đã sửa.** Mục nào còn "chưa cài" thì bug vẫn đang sống trong code — lần chạy sau phải quét lại nhật ký tìm các mục này trước khi bắt đầu pha nặng, đừng tin rằng "đã có trong bug.md nghĩa là đã xong".
  - Trạng thái của pha chạy hàng giờ trên ổ mạng phải nằm trên **ĐĨA** và được ghi **định kỳ**, không chỉ ghi ở cuối — vì cái hay xảy ra nhất chính là không bao giờ tới được cuối.
  - Cache phục hồi phải **đối chiếu với hiện vật thật** (file còn không), không tin sổ sách suông.

### 33. Bộ kiểm khung hình báo `khop=?` ở clip đã HẠ 4K — SSIM từ chối so hai ảnh khác kích thước
- **Ngày:** 2026-08-18
- **Mức độ:** 🟡 Medium (báo động giả ở khâu nghiệm thu — suýt kết luận "cắt gọn bị lệch" trong khi sản phẩm hoàn toàn đúng)
- **Vị trí:** `scratchpad/kiem_khung_hinh.py` → `ssim()`
- **Triệu chứng:** Chạy kiểm 4 mẫu cắt gọn trên `DS1_090`: 2 mẫu ra `khop=?  NGHI NGO`, 2 mẫu còn lại bình thường (0,99 / 0,91). Kết luận `CO 2 mau dang NGHI NGO`.
- **Nguyên nhân gốc:** Đúng 2 mẫu lỗi là clip **đã bị hạ 4K** (nguồn 3840×2160 → bản tối ưu 2112×1188). Bộ lọc `ssim` của ffmpeg **bắt buộc hai đầu vào cùng kích thước**; khác size thì nó không xuất packet nào và báo `Nothing was written into output file... Conversion failed!`. Regex tìm `All:` không thấy gì ⇒ trả `None` ⇒ in ra `?`. Tức là **phép đo không chạy được**, chứ không phải khung hình lệch — hai chuyện hoàn toàn khác nhau nhưng cùng hiện ra là "NGHI NGO".
- **Cách sửa:** Thêm `size_of(png)` (dùng ffprobe) rồi dựng lavfi `[0:v]scale=W:H,setsar=1[ref];[1:v]setsar=1[cmp];[ref][cmp]ssim` — scale khung GỐC về đúng kích thước khung ĐÍCH trước khi so. Sau khi sửa: 6/6 mẫu đều có số và đều **khớp cao hơn đối chứng** (vd 0,9722 so với đối chứng 0,2264).
- **Cách phát hiện / kiểm chứng:** In `stderr` của ffmpeg thay vì chỉ nhìn giá trị trả về — dòng `Conversion failed!` lộ ngay nguyên nhân. Đối chiếu kích thước hai khung bằng ffprobe: `3840,2160` với `2112,1188`.
- **Bài học (để tránh lặp lại):**
  - **Phân biệt "phép đo thất bại" với "phép đo cho kết quả xấu".** Giá trị `None`/`?` phải được báo là *không đo được* và điều tra riêng, TUYỆT ĐỐI không gộp chung vào nhóm "nghi ngờ" — nếu không sẽ đi sửa sản phẩm đang đúng. Cùng họ bài học #31 (nghi BỘ KIỂM trước khi nghi sản phẩm).
  - Khi bộ kiểm gọi công cụ ngoài (ffmpeg), **luôn giữ và in stderr khi parse thất bại**; nuốt stderr là dạng khác của `except: pass` (checklist "không nuốt lỗi âm thầm").
  - Tính năng "hạ 4K" làm đổi kích thước khung ⇒ mọi phép so khung hình về sau đều phải chuẩn hoá kích thước trước.

### 34. Truyền path UNC qua `argv` cũng bị nuốt backslash — không chỉ stdin redirect (mở rộng #9)
- **Ngày:** 2026-08-18
- **Mức độ:** 🟠 High (bộ kiểm im lặng báo "không thấy file" trong khi file có thật — dễ tưởng pha chạy chưa xong)
- **Vị trí:** `scratchpad/kiem_khung_hinh.py` → `main()` / `lp()` (script kiểm, không phải tool chính)
- **Triệu chứng:** Chạy `python kiem_khung_hinh.py "\\192.168.1.214\e\...\DS1_090"` → in `Khong thay _opt_index.json`, dù file đó chắc chắn tồn tại (vừa đọc được bằng script khác vài phút trước).
- **Nguyên nhân gốc:** Bug #9 ghi nhận việc nuốt backslash khi nạp qua **stdin redirect**, nên tôi tưởng truyền qua **tham số dòng lệnh** thì an toàn. Thực tế shell cũng nuốt: `\\192.168...` tới `sys.argv` chỉ còn `\192.168...`. Một backslash đầu ⇒ Windows hiểu là **drive-relative** ⇒ `os.path.abspath()` nối vào ổ hiện hành, ra `\\?\C:\192.168.1.214\e\...` — sai ổ hoàn toàn, đúng cùng cơ chế bug #23.
- **Cách sửa:** Thêm `fix_unc(p)`: nếu chuỗi bắt đầu bằng ĐÚNG MỘT `\` (và ký tự kế không phải `?`/`.`) thì khôi phục thành `\\`. Gọi `fix_unc()` cả ở `lp()` lẫn khi đọc `sys.argv[1]`. Test 4 ca: UNC nguyên vẹn giữ nguyên, UNC bị nuốt được khôi phục, path ổ đĩa không bị đụng, `lp()` ra `\\?\UNC\...` đúng.
- **Cách phát hiện / kiểm chứng:** In `repr()` của path ở 3 mức (argv → join → sau `lp()`). `repr()` lộ ngay số backslash thật; `print()` thường thì không.
- **Bài học (để tránh lặp lại):**
  - Bài học #9 phải mở rộng: **MỌI kênh chuỗi đi qua shell đều có thể nuốt backslash** — stdin, argv, biến môi trường. An toàn nhất vẫn là dựng path bằng `chr(92)` **bên trong** file Python, không truyền qua shell.
  - Khi một script báo "không thấy file" mà bạn tin là có, việc đầu tiên là **in `repr()` đường dẫn đã chuẩn hoá**, đừng vội nghĩ tiến trình chạy chưa tới.
  - Quy tắc này áp cho **cả script kiểm tạm** trong `scratchpad/`, không chỉ tool chính — bộ kiểm sai làm mất niềm tin y hệt sản phẩm sai.

### 35. File mã lại bị CỤT âm thầm (12,47 s → 1,70 s) — tool nhận là thành công, mất ~10 giây hình
- **Ngày:** 2026-08-18
- **Mức độ:** 🔴 Critical (mất hình trong bản bàn giao mà mọi bộ đếm đều báo "thành công")
- **Vị trí:** `toi_uu_dung_luong.py` → `encode_job()` (không kiểm độ dài kết quả) và `optimize_package()` (chỉ kiểm `info[2] > 0`).
- **Triệu chứng:** Gói `DS1_090` chạy xong báo `2545/2546 clip` thành công, nhưng bộ tự kiểm lại báo `2 segment BI LECH`. Truy ra: material `E5F60CD6` có timeline đòi đoạn 5,60→17,07 s (11,47 s) trong khi file `_opt.mp4` **chỉ dài 1,70 s** — thiếu ~9,8 giây hình. Material `6612AFF5` thiếu 1,01 s tương tự.
- **Nguyên nhân gốc:** `encode_job()` chỉ coi là thành công khi `returncode == 0` và file đích tồn tại. Nó **KHÔNG so độ dài thực tế của file kết quả với `span` đã yêu cầu**. Khi ffmpeg bị ngắt giữa chừng lúc ghi/copy qua SMB (hoặc ghi ra file cụt), returncode vẫn có thể là 0 và file vẫn tồn tại ⇒ tool ghi nhận thành công, cập nhật JSON, và bản cụt được **nhân bản sang mọi `materials/` khác** qua cache/`dup` (mỗi clip có 3 bản sao). Kiểm chứng: chạy LẠI đúng lệnh ffmpeg đó cho ra 12,48 s hoàn toàn bình thường ⇒ lệnh đúng, kết quả lần đầu bị cụt.
- **Cách sửa — ĐÃ CÀI vào code ngày 2026-08-18** (`MAX_DUR_DIFF_S`, `ffprobe` được truyền xuống `encode_job()`). Biên của phép kiểm này ban đầu sai, đã sửa ở **mục 43**. Nội dung gốc:
  1. Trong `encode_job()`, sau khi ffmpeg xong: `ffprobe` file tạm, nếu `abs(dur - span/US) > 0.6 s` thì **trả về thất bại** kèm lý do "ket qua bi cut", để tool giữ bản gốc thay vì nhận bản hỏng.
  2. Việc sửa file `.mp4` là **chưa đủ**: trường `duration` trong JSON vẫn giữ số cũ (1,70 s) và CapCut đọc chính trường đó ⇒ phải cập nhật `duration` cho khớp file thật ở **mọi** file content tham chiếu tới nó (ở đây là 6 material trong 3 file JSON).
- **Cách phát hiện / kiểm chứng:** Viết `quet_toan_bo_lech.py` — `ffprobe` **toàn bộ** 797 media của gói rồi so với đoạn timeline đòi hỏi. Trước khi sửa: 18 segment thiếu hình. Sau khi sửa: 16, và **cả 16 đều là file `.aac` vốn đã ngắn sẵn trong draft GỐC** (kiểm bằng cách ffprobe chính nguồn trong draft gốc: `Boom.aac` đòi 7,47 s nhưng file chỉ 3,01 s — y hệt ở cả hai bên) ⇒ 0 lỗi do tool. Verifier độc lập: `Segment LECH: 6 → 0`.
- **Bài học (để tránh lặp lại):**
  - **`returncode == 0` + file tồn tại KHÔNG chứng minh mã lại thành công.** Với media, tiêu chí đúng là **độ dài kết quả khớp yêu cầu**. Đây là biến thể của bài học #5/#14: đo trên KẾT QUẢ THỰC TẾ, không đo trên trạng thái trung gian.
  - Lỗi ở một clip bị **nhân lên nhiều lần** bởi chính cơ chế cache/`dup` (1 clip hỏng → 3 bản sao hỏng). Kiểm sai sót phải quét TOÀN BỘ gói, không chỉ nơi phát sinh.
  - Sửa file media mà quên sửa **siêu dữ liệu mô tả nó** (`duration` trong JSON) thì coi như chưa sửa — CapCut tin JSON chứ không tin file.
  - Bộ tự kiểm `verify_optimize()` đã làm đúng việc của nó: nó là thứ duy nhất phát hiện ra lỗi này. Giữ và tin các lớp tự kiểm, kể cả khi mọi bộ đếm khác đều xanh.

### 36. Verifier báo "PASS" khi quét 0 file — đường dẫn UNC bị nuốt backslash qua argv
- **Ngày:** 2026-08-18
- **Mức độ:** 🟠 High (kết luận "ĐẠT" hoàn toàn vô căn cứ — nguy hiểm hơn cả báo FAIL sai)
- **Vị trí:** `scratchpad/verifier_doclap.py` → `main()`
- **Triệu chứng:** Chạy verifier trên gói đã xong, in ra `File .json da quet: 0`, `Tham chieu HONG: 0`, và **`KET LUAN: PASS - ban tu chua DU`**.
- **Nguyên nhân gốc:** Hai lỗi cộng lại: (1) đường dẫn UNC truyền qua `argv` bị shell nuốt một backslash (đúng #34 — tôi đã sửa cho `kiem_khung_hinh.py` nhưng **quên áp cho verifier**); (2) logic kết luận `ok = not abs_left and not broken and not seg_bad` — khi không quét được file nào thì cả ba danh sách đều rỗng ⇒ ra PASS. Tức là **"không đo được" bị tính thành "đạt"**.
- **Cách sửa:** Thêm `fix_unc()` cho cả `lp()` lẫn `sys.argv`; và thêm chốt chặn: `if n_json == 0: return 2` với thông báo rõ "KHONG QUET DUOC FILE NAO -> duong dan sai, KHONG phai 'dat'". Sau khi sửa: quét được 229 file JSON / 9546 tham chiếu.
- **Cách phát hiện / kiểm chứng:** Con số `0 file da quet` là dấu hiệu tự tố cáo — một gói 1841 file không thể có 0 file JSON. Luôn in **số lượng đã kiểm** cạnh kết luận.
- **Bài học (để tránh lặp lại):**
  - **Mọi bộ kiểm PHẢI thất bại khi không có dữ liệu**, không được mặc định "đạt". Kết luận xanh phải đi kèm bằng chứng "đã kiểm N thứ" với N > 0; N = 0 là FAIL.
  - Sửa một lỗi ở một script thì phải **rà các script anh em cùng loại** — tôi sửa #34 cho bộ so khung hình nhưng để nguyên verifier, và chính verifier mới là thứ đưa ra kết luận bàn giao.
  - Lặp lại bài học #33: phân biệt "phép đo thất bại" với "kết quả tốt". Lần này hậu quả ngược dấu và nguy hiểm hơn — báo ĐẠT cho thứ chưa hề kiểm.

### 37. `WinError 71` khi đọc NAS làm phép đo trả 0 — suýt kết luận "0 đường dẫn quá dài"
- **Ngày:** 2026-08-18
- **Mức độ:** 🟡 Medium (báo cáo sai cho người dùng; đã tự phát hiện và đính chính ngay)
- **Vị trí:** script kiểm tạm trong `scratchpad/` (đếm path > 260 ký tự)
- **Triệu chứng:** Verifier báo `Path > 260 ky tu: 30`, nhưng script đếm riêng lại ra `0`, kèm `Tong file: 0`. Tôi đã kịp báo "0 đường dẫn dài" trước khi kiểm lại.
- **Nguyên nhân gốc:** NAS `.214` đạt giới hạn phiên SMB → `os.listdir`/`os.walk` ném `[WinError 71] No more connections can be made to this remote computer`. `os.walk` **nuốt lỗi mặc định** (`onerror=None`) nên trả về rỗng lặng lẽ ⇒ "không có file nào" bị hiểu nhầm thành "không có file nào vi phạm".
- **Cách sửa:** Luôn truyền `os.walk(..., onerror=...)` để lỗi nổi lên, và **so số file quét được với kỳ vọng** trước khi kết luận. Con số đúng là 30 (từ lần verifier chạy khi NAS còn truy cập được).
- **Cách phát hiện / kiểm chứng:** In tổng số file đã duyệt cạnh mọi con số thống kê. `Tong file: 0` trên một gói 1841 file là bất khả thi ⇒ phép đo hỏng.
- **Bài học (để tránh lặp lại):**
  - `os.walk` mặc định **im lặng khi lỗi** — trên ổ mạng điều này biến sự cố kết nối thành "thư mục rỗng". Cùng họ #36: thiếu dữ liệu phải là FAIL, không phải "sạch".
  - Ổ mạng có thể **đột ngột từ chối kết nối** (WinError 71) ngay cả khi ping và port 445 vẫn thông — kiểm tra "còn sống" không đủ để kết luận "còn dùng được".
  - Khi hai phép đo mâu thuẫn (30 với 0), **điều tra trước khi báo**, đừng chọn con số dễ chịu hơn.

### 40. Thư mục XUẤT RA được phép nằm TRONG project gốc → tool ghi đè và xoá dữ liệu gốc trong khi vẫn in "project GỐC KHÔNG bị thay đổi"
- **Ngày:** 2026-08-18
- **Mức độ:** 🔴 Critical (mất dữ liệu GỐC — không phục hồi được bằng cách chạy lại)
- **Vị trí:** `goi_project_capcut.py` → `main()`, ngay sau câu hỏi "Folder XUAT RA".
- **Triệu chứng:** Chưa xảy ra thật; phát hiện khi rà soát trước lúc phát hành cho 15–20 người. Nếu người dùng dán nhầm chính đường dẫn project vào ô "Folder XUAT RA", tool chạy trót lọt và báo thành công, nhưng draft gốc đã bị sửa.
- **Nguyên nhân gốc:** Từ chỗ nhận `out_dir` (input) tới chỗ `out_dir.mkdir(...)` không có **bất kỳ phép kiểm nào**. `_is_under()` đã tồn tại sẵn trong file nhưng chỉ được dùng cho việc khác. Hệ quả dây chuyền khi `out_dir` nằm trong `draft_dir`:
  1. Bước ghi 3 file JSON gốc **đè thẳng** lên `draft_content.json` / `draft_meta_info.json` của bản gốc;
  2. Chế độ 4 mã lại media rồi `cleanup_unused()` gọi `os.remove` xoá media "mồ côi" **ngay trong project gốc**;
  3. Tool vẫn in "project GOC KHONG bi thay doi" vì câu đó là chuỗi tĩnh, không phải kết luận đo được.
  Chiều ngược lại (`draft_dir` nằm trong `out_dir`) cũng hỏng: pha dọn dẹp quét cả project gốc.
- **Cách sửa:** Thêm **hai** chặn ngay sau khi nhận input, trước mọi thao tác filesystem:
  1. `out_dir = Path(os.path.abspath(_unlp(out_dir)))` — đưa về tuyệt đối trước đã, vì `"D:"` là drive-relative và path tương đối sẽ làm phép so sánh vô nghĩa (đây cũng là chống tái phát #23 ngay tại cửa vào);
  2. `if _is_under(out_dir, draft_dir)` → in rõ hai đường dẫn + hậu quả rồi `return`;
  3. `if _is_under(draft_dir, out_dir)` → tương tự cho chiều ngược lại.
- **Cách phát hiện / kiểm chứng:** `scratchpad/test_a0_a1.py` — 13 phép kiểm PASS: trùng khít, lồng 1 tầng, lồng 3 tầng, chiều ngược, **thư mục anh em KHÔNG bị chặn nhầm** (đây là đường dùng đúng nhất, chặn nhầm là hỏng tính năng), **tên có tiền tố trùng** (`DS1_090_PORTABLE` không nằm trong `DS1_090` — bẫy so khớp chuỗi con), khác ổ đĩa, không phân biệt hoa/thường, **UNC cùng share** và **UNC khác server**. Cộng 3 phép kiểm `abspath`: `"D:"`, path tương đối, và UNC giữ nguyên 2 backslash đầu.
- **Bài học (để tránh lặp lại):**
  - **Mọi giá trị người dùng gõ vào phải được chuẩn hoá và kiểm ngay tại cửa vào**, không phải ở chỗ dùng. Đường dẫn đích đi qua hàng chục hàm phía sau; kiểm ở cuối là quá muộn.
  - Câu trấn an in ra màn hình ("project GỐC KHÔNG bị thay đổi") mà **không** đo từ trạng thái thật thì chính nó là một dạng báo cáo sai — cùng họ với #5 và #21.
  - Khi số người dùng tăng, những đường "không ai dại gì làm thế" trở thành **chắc chắn sẽ có người làm**. Rà lại các cửa vào theo giả định đó trước khi phát hành.

### 41. Bộ tự kiểm NÉM LỖI thì tool kết luận "Bản tự chứa ĐỦ" — phép đo thất bại bị hiểu thành phép đo đạt
- **Ngày:** 2026-08-18
- **Mức độ:** 🔴 Critical (báo cáo sai ở đúng chỗ người dùng tin nhất; dẫn tới xoá footage gốc)
- **Vị trí:** `goi_project_capcut.py` → `main()`: chỗ gọi `verify_package()`, `verify_optimize()`, `scan_long_paths()`.
- **Triệu chứng:** Ba khối `try/except` bắt lỗi của ba bộ kiểm rồi **gán về rỗng và đi tiếp**:
  - `except Exception as ex: bad = []` → `bad_hard` rỗng → `ok = True` → báo cáo ghi **"Khong thieu. Ban tu chua DU"** dù chưa hề tự kiểm lần nào;
  - `verify_optimize()` ném lỗi → `opt_bad` giữ nguyên `[]` → rơi vào nhánh `else` in **"OK: moi doan dung deu nam trong pham vi clip"** *và* `os.remove` luôn `_opt_index.json` — tức vừa báo đạt vừa phá sổ cache phục hồi của #29/#32;
  - `scan_long_paths()` ném lỗi → `long_paths = []` → báo cáo im lặng về đường dẫn dài.
- **Nguyên nhân gốc:** Nhầm lẫn giữa **"không có lỗi"** và **"không biết có lỗi hay không"**. Danh sách rỗng được dùng cho cả hai trạng thái, trong khi chúng đối lập nhau. Đây đúng bài học #33 (phân biệt *phép đo thất bại* với *kết quả xấu*) nhưng lần này ở lớp nghiệm thu cuối cùng — nơi hậu quả nặng nhất.
- **Cách sửa:** Thêm danh sách `verify_loi` khai báo **trước** khối kiểm tối ưu (nếu khai báo sau sẽ `NameError` ở chế độ 4):
  1. Mỗi `except` ghi `f"{ten_bo_kiem}: {type(ex).__name__}: {ex}"` vào `verify_loi` và in "TU KIEM THAT BAI (khong the ket luan DU)";
  2. `verify_loi` được đưa **vào biểu thức `ok`** — bộ kiểm chết thì không còn bằng chứng nào để tuyên "ĐỦ";
  3. Báo cáo có mục riêng `BO TU KIEM THAT BAI` và một câu kết luận thay thế: "CHUA KET LUAN DUOC…";
  4. `verify_optimize` thất bại thì **giữ lại** `_opt_index.json` thay vì xoá, để lần chạy sau còn đường phục hồi;
  5. Console in cảnh báo mức NẶNG.
- **Cách phát hiện / kiểm chứng:** `scratchpad/test_a0_a1.py` — 13 phép kiểm PASS, gồm bảng chân trị của `ok` cho từng bộ kiểm chết (riêng lẻ và đồng thời), và các phép kiểm trên mã nguồn: `verify_loi` khai báo trước điểm dùng, có mặt trong biểu thức `ok`, báo cáo có mục mới, **không còn chuỗi `"(bo qua)"`** (chữ "bỏ qua" chính là dấu vết của tư duy sai), và sổ cache được giữ lại.
- **Bài học (để tránh lặp lại):**
  - **Danh sách rỗng không được mang hai nghĩa.** "Kiểm xong, sạch" và "chưa kiểm được" phải là hai biến khác nhau. Nếu chỉ có một biến thì mặc định luôn phải là CHƯA XONG.
  - Khi viết `except` quanh một **bộ kiểm**, hãy tự hỏi: nuốt lỗi ở đây khiến kết luận nghiêng về phía nào? Nếu nghiêng về "đạt" thì đó là bug, không phải xử lý lỗi.
  - Chữ "bỏ qua" trong thông báo lỗi là một mùi mã (code smell) đáng grep: `(bo qua)`, `skip`, `ignore` — mỗi chỗ đều đáng hỏi lại xem có làm sai lệch kết luận không.

### 42. `bug.md` trùng số hiệu — và lần sửa đầu tiên lại đâm vào các mục vừa được thêm
- **Ngày:** 2026-08-18
- **Mức độ:** 🟡 Medium (không ảnh hưởng code, nhưng làm hỏng khả năng truy nguyên khi nhiều người cùng dùng)
- **Vị trí:** `bug.md` — mục "24." và "25." lặp lại ở phần sau của nhật ký.
- **Triệu chứng:** Nhật ký có hai mục mang số **24** và hai mục mang số **25**. Khi ai đó nói "gặp lại lỗi #25" thì không xác định được họ nói mục nào — mục *treo NAS* hay mục *SSIM báo lệch*, hai chuyện hoàn toàn khác nhau. Vấn đề này lộ ra khi lập kế hoạch ánh xạ mỗi mục nhật ký thành một test hồi quy: tên test phải tham chiếu số hiệu.
- **Nguyên nhân gốc:** Hai mục được thêm trong một phiên làm việc khác, đánh số theo trí nhớ thay vì đọc số lớn nhất đang có trong file.
- **Cách sửa:** Đổi hai mục trùng thành **38** và **39**, giữ nguyên toàn bộ nội dung, thêm dòng chú thích số cũ ngay dưới tiêu đề để các tham chiếu cũ vẫn tra ngược được.
- **LẦN SỬA ĐẦU TIÊN ĐÃ SAI — và đây mới là phần đáng giá nhất của mục này:** thoạt đầu hai mục được đổi thành **35** và **36**, dựa trên một lần `grep` chạy từ **đầu phiên làm việc**, lúc đó số lớn nhất là 34. Nhưng giữa lúc grep và lúc sửa, file đã được thêm ba mục mới (**35**, **36**, **37**) từ công việc khác. Kết quả: thao tác *sửa lỗi trùng số* lại **tạo ra ba cặp trùng mới** (35, 36, 37). Phát hiện ngay vì có chạy phép kiểm dãy số sau khi sửa; nếu chỉ sửa xong rồi tin là xong thì nhật ký đã hỏng nặng hơn trước.
- **Cách phát hiện / kiểm chứng:** Phép kiểm bằng máy, chạy **mỗi lần** thêm/sửa mục:
  ```python
  import re
  nums = [int(m.group(1)) for m in re.finditer(r'^### (\d+)\.', open('bug.md', encoding='utf-8').read(), re.M)]
  assert not [n for n in set(nums) if nums.count(n) > 1], "TRUNG SO"
  assert not set(range(1, max(nums) + 1)) - set(nums), "THIEU SO"
  ```
  Sau khi sửa: 42 mục, dãy 1–42, không trùng, không thiếu.
- **Bài học (để tránh lặp lại):**
  - **Đọc lại ngay trước khi ghi, đừng dùng kết quả đọc từ đầu phiên.** File dùng chung có thể đã đổi giữa lúc đọc và lúc ghi — nhất là khi phiên làm việc kéo dài hoặc có nhiều tiến trình cùng chạy. Đây là phiên bản "trên tài liệu" của đúng bài học #32 (*cache phục hồi phải đối chiếu với hiện vật thật, không tin sổ sách suông*).
  - **Thao tác sửa lỗi cũng phải được kiểm như mọi thay đổi khác.** Ở đây chính bước dọn dẹp lại sinh ra lỗi nặng hơn; chỉ có phép kiểm tự động sau khi sửa mới bắt được.
  - Trước khi thêm mục, **grep lấy số lớn nhất ngay tại thời điểm đó** thay vì nhớ.
  - Sổ ghi chép cũng là một sản phẩm và cũng có bug — mà bug của sổ thì làm mất niềm tin vào mọi thứ ghi trong đó.


### 43. Bộ bắt "kết quả bị CỤT" của #35 báo động giả với file nguồn vốn đã ngắn hơn metadata
- **Ngày:** 2026-08-18
- **Mức độ:** 🟠 High (báo động giả hàng loạt làm che mất lỗi thật, và file bị báo lỗi thì không bao giờ được nén)
- **Vị trí:** `toi_uu_dung_luong.py` → `encode_job()`, khối kiểm độ dài thêm vào khi cài #35.
- **Triệu chứng:** Bản cài đầu tiên của #35 dùng `if abs(got - want) > MAX_DUR_DIFF_S`. Với một material mà draft gốc khai `duration = 7,47 s` nhưng file thật chỉ dài 3,01 s, ffmpeg mã ra đúng 3,01 s, và tool kết luận **"ket qua BI CUT"** rồi giữ bản gốc. Chính mục #35 đã ghi nhận gói `DS1_090` có **16 file `.aac` dạng này** ⇒ mỗi lần chạy sẽ sinh 16 dòng thất bại sai.
- **Nguyên nhân gốc:** `span` được tính từ `dur = m.get("duration")` — tức **con số trong JSON của draft gốc**, không phải độ dài thật của file. Khi hai thứ đó lệch nhau, phép so `độ dài kết quả` với `span` đo nhầm thứ: nó đang đo *"JSON có nói thật không"* chứ không phải *"ta có làm hỏng file không"*. Đây đúng họ bài học #21 và #31 — nhận tội thay cho cái hỏng **có sẵn** trong draft gốc. Ngoài ra `abs()` còn từ chối cả kết quả **dài hơn** yêu cầu, trong khi dài hơn thì không mất hình.
- **Cách sửa:**
  1. Chỉ bắt **chiều NGẮN**: `if got < want - MAX_DUR_DIFF_S`. Dài hơn là vô hại.
  2. Ở nhánh nghi ngờ, **probe chính file NGUỒN** rồi tính `co_san = (dur_nguon - lo)`. Nếu `got >= min(want, co_san) - MAX_DUR_DIFF_S` thì nguồn vốn đã ngắn ⇒ **chấp nhận**, không phải lỗi của tool. Vòng probe này chỉ chạy ở nhánh nghi ngờ nên đường chạy bình thường **không tốn thêm một vòng I/O nào qua mạng**.
  3. Không đọc được nguồn ⇒ không phân biệt được ⇒ **giữ nguyên kết luận thất bại** (mặc định CHƯA XONG).
  Lợi ích phụ: khi chấp nhận, `m["duration"] = new_dur` ở `optimize_package()` ghi lại đúng độ dài thật ⇒ JSON được **sửa cho khớp file**, thay vì giữ mãi con số sai của draft gốc.
- **Cách phát hiện / kiểm chứng:** `scratchpad/test_a7.py` — 7 phép kiểm PASS trên **media thật do ffmpeg sinh**, không giả lập:
  1. nguồn đủ + đòi đúng → thành công;
  2. **nguồn thật 10 s nhưng job đòi 30 s → KHÔNG được báo "BI CUT"** (đây chính là ca đã FAIL trước khi sửa, bằng chứng bug có thật);
  3. cắt gọn 2 s→5 s → thành công và dài đúng ~3 s;
  4. **đúng cảnh #35**: nguồn đủ 10 s nhưng đầu ra bị cụt còn 1,70 s → **bị bắt** (ép lỗi bằng cách vá `probe()` để trả số của file tạm, vì không thể bắt ffmpeg tự sinh file cụt theo ý muốn — đây là kiểm chính *quyết định của code*, không phải kiểm ffmpeg);
  5. không đọc được nguồn → vẫn báo thất bại.
- **Bài học (để tránh lặp lại):**
  - **Trước khi kết tội, hỏi "tội này của ai".** Một phép kiểm so kết quả với *con số do dữ liệu đầu vào khai báo* sẽ đổ lỗi cho mình mỗi khi đầu vào khai sai. Muốn biết mình có làm hỏng không thì phải so với **hiện vật nguồn**, không so với siêu dữ liệu mô tả nguồn.
  - **`abs()` trong một phép kiểm an toàn thường là dấu hiệu chưa nghĩ kỹ**: hai chiều lệch hiếm khi có cùng hậu quả. Ở đây ngắn = mất hình, dài = vô hại.
  - Chi phí của phép kiểm bổ sung có thể dồn hết vào **nhánh hiếm**: probe nguồn chỉ khi nghi ngờ thì đường chạy chính không mất gì. Đừng vì sợ tốn I/O mà bỏ luôn phép phân biệt.
  - Cài xong một bản vá **chưa phải là xong** — bản vá cũng cần bộ kiểm riêng. Bản vá #35 đúng ý đồ nhưng sai biên, và chỉ lộ ra khi chạy test có ca "nguồn vốn ngắn".


### 38. `repoint_registry()` bỏ sót footage sinh ra NHIỀU bản `_opt` → giữ lại 10,46 GB bản gốc vô ích (bug #14 tái phát một phần)
- **Ngày:** 2026-08-18
- **Mức độ:** 🟠 High (gói phình thêm 35% mà không ai dùng tới phần đó; sản phẩm vẫn ĐÚNG)
- **Vị trí:** `toi_uu_dung_luong.py` → `repoint_registry()`, dòng `by_src.setdefault(srckey, dest)`.
- **Triệu chứng:** Gói `DS1_090` xong ra **29,82 GB** cho timeline 32,8 phút (~121 Mbps — vô lý). Phân tích: **37 video gốc chưa mã lại chiếm 10,61 GB**, trong đó **9 file lớn (10,46 GB) KHÔNG có file nội dung nào trỏ tới**, chỉ còn `draft_meta_info.json` (sổ đăng ký) giữ chúng "sống" nên `cleanup_unused()` không dám xoá. Ví dụ: `slow-motion-underwater-of-a-great-white-shark` giữ bản gốc **2064 MB** trong khi timeline chỉ dùng 4 đoạn cắt tổng **46 MB**.
- **Nguyên nhân gốc:** `repoint_registry()` dựng bảng tra `by_src` theo **file nguồn → MỘT đích duy nhất** (`setdefault`). Nhưng một file nguồn thường sinh ra **nhiều bản `_opt` khác nhau** (mỗi đoạn cắt một file — clip YouTube sinh tới 24 bản). Khi đó `setdefault` chỉ giữ bản đầu tiên, và với các file mà `resolve_material_file()` giải ra đường dẫn khác với khoá đã lưu thì **không khớp** ⇒ mục sổ đăng ký giữ nguyên đường dẫn gốc ⇒ file gốc không bao giờ thành mồ côi. Đây chính là cơ chế của **bug #14**, chỉ khác là lần này chỉ sót ở nhóm "một nguồn → nhiều đích".
- **Cách sửa — ĐÃ CÀI ngày 2026-08-18** (`opt_all_by_src` + `day_du_nhat` trong `repoint_registry()`, và `resolved` được truyền xuống thay vì `{}`; kèm hàm nghiệm thu `kiem_ban_goc_thua()` — xem mục 54). Nội dung phân tích ban đầu: với file nguồn có nhiều bản `_opt`, mục sổ đăng ký nên (a) trỏ tới bản `_opt` **dài nhất/đầy đủ nhất**, hoặc (b) bị `prune_registry()` loại bỏ hẳn — vì mục sổ đăng ký chỉ phục vụ **thư viện media** của CapCut, không phải timeline. Sau đó `cleanup_unused()` mới xoá được bản gốc. **Không được xoá file khi mục sổ đăng ký vẫn trỏ tới nó** — sẽ sinh mục hỏng trong thư viện, đúng thứ người dùng muốn tránh.
- **Cách phát hiện / kiểm chứng:** Áp "phép thử vô lý" (#18/#19) cho dung lượng cuối: 29,82 GB cho 32,8 phút timeline là sai một bậc độ lớn. Truy bằng cách phân loại toàn bộ file trong gói thành `_opt` / gốc / khác, rồi với nhóm gốc kiểm **KHOÁ ĐƯỜNG DẪN THẬT** (không phải tên file — bẫy #24) xem file nội dung nào trỏ tới. Kết quả: 28 file (0,15 GB) do content dùng thật, **9 file (10,46 GB) chỉ có sổ đăng ký trỏ tới**.
- **Bài học (để tránh lặp lại):**
  - Ánh xạ **1 nguồn → 1 đích** là giả định sai với tính năng cắt gọn: một footage được dùng ở nhiều đoạn sẽ sinh nhiều bản. Mọi bảng tra kiểu `setdefault(src, dest)` trong pha tối ưu đều cần xét lại.
  - Bài học #14 chưa đóng hoàn toàn: phải kiểm **"còn bản gốc nào bị giữ sống bởi sổ đăng ký không"** như một bước nghiệm thu thường trực, không chỉ tin `cleanup_unused()` đã chạy.
  - Khi đánh giá "file có được dùng không", phải giải **khoá đường dẫn** rồi so đường dẫn tuyệt đối — so theo TÊN FILE cho ra kết quả sai hoàn toàn (lần đầu tôi đếm nhầm thành "37 file đều cần giữ").

### 44. `cleanup_unused()` nuốt lỗi đọc JSON rồi XOÁ chính media mà file JSON đó đang dùng
- **Ngày:** 2026-08-18
- **Mức độ:** 🔴 Critical (mất hình/tiếng trong gói bàn giao, âm thầm, không đếm, không báo)
- **Vị trí:** `toi_uu_dung_luong.py` → `cleanup_unused()`
- **Triệu chứng:** Chưa gặp trên gói thật; phát hiện khi rà soát trước lúc phát hành. Một file `.json` trong bản xuất parse lỗi (ghi dở, hỏng, encoding lạ) sẽ khiến media nó tham chiếu **biến mất** khỏi gói.
- **Nguyên nhân gốc:** Vòng thu thập tham chiếu có `except Exception: continue`. File JSON không đọc được thì các tham chiếu của nó **không vào tập `refd`**. Ngay sau đó vòng xoá coi mọi media trong `materials/` không có trong `refd` là **mồ côi** và `os.remove`. Tức là *"tôi không đọc được nên tôi không biết"* bị diễn dịch thành *"không ai dùng"*. Cùng họ #41: thiếu thông tin bị hiểu thành thông tin phủ định.
- **Cách sửa:** Ghi mọi lỗi đọc vào `loi_doc`. Nếu `loi_doc` khác rỗng thì **cấm xoá file mồ côi** (`duoc_xoa_mo_coi = not loi_doc`) — vẫn dọn `*.bak`/`*.tmp` vì chúng an toàn trong mọi trường hợp. In cảnh báo, và trả `loi_doc` về cho `main()` đưa vào báo cáo.
- **Cách phát hiện / kiểm chứng:** `tests/test_don_dep.py` — dựng bản xuất tối giản, thả vào một file `hong.json` không parse được, khẳng định media mồ côi **vẫn còn**. Kèm phép kiểm **chiều ngược**: không có JSON hỏng thì file mồ côi **vẫn phải bị dọn** (sửa an toàn không được làm mất tính năng).
- **Bài học (để tránh lặp lại):** Trước khi **xoá** bất cứ thứ gì dựa trên một tập "đang được dùng", phải hỏi: *tập đó có đầy đủ không?* Nếu quá trình dựng tập có bất kỳ bước nào thất bại thì tập đó **không đủ tư cách** làm căn cứ xoá. Thao tác huỷ hoại chỉ được chạy trên bằng chứng HOÀN CHỈNH.

### 45. Phạm vi xoá của `cleanup_unused()` khớp CHUỖI CON — gói nằm dưới thư mục tên `materials*` thì cả gói thành "kho"
- **Ngày:** 2026-08-18
- **Mức độ:** 🔴 Critical (xoá media ở mọi nơi trong bản xuất, kể cả `Resources/`)
- **Vị trí:** `toi_uu_dung_luong.py` → `cleanup_unused()`, biến `in_materials`.
- **Triệu chứng:** Nếu người dùng xuất ra `D:\materials_2026\GOI_PORTABLE` (hoặc share NAS tên `materials...`), phạm vi "chỉ đụng tới `materials/`" mở rộng ra **toàn bộ cây thư mục** của gói.
- **Nguyên nhân gốc:** `in_materials = (os.sep + "materials") in (plain.lower() + os.sep)` kiểm **chuỗi con trên đường dẫn TUYỆT ĐỐI**, tức tính cả phần **tổ tiên nằm NGOÀI `out_dir`**. Đo thật: với gói ở `d:\tmp\materials_2026\GOI_PORTABLE`, logic cũ trả `True` cho `Resources\videoAlg` **và cho cả thư mục gốc của gói** — nghĩa là mọi media trong gói đều thành ứng viên bị xoá.
- **Cách sửa:** Tính `rel = os.path.relpath(plain, out_dir)` rồi so theo **thành phần thư mục**: `"materials" in [x.lower() for x in rel.split(os.sep) if x]`. Bắt `ValueError` (khác ổ đĩa) thành "không nằm trong gói".
- **Cách phát hiện / kiểm chứng:** `tests/test_don_dep.py` — đặt gói dưới `materials_2026/`, khẳng định file trong `Resources/videoAlg` **còn nguyên**, còn file mồ côi trong `materials/` **vẫn bị dọn**. Thêm phép **đối chiếu logic cũ vs mới** in bảng `True/False` cho 3 đường dẫn, để chứng minh test thật sự thất bại trên bản cũ.
- **Bài học (để tránh lặp lại):**
  - **Kiểm tên thư mục thì phải tách thành phần, không dùng `in` trên chuỗi.** `"materials" in path` khớp cả `materials_2026`, `my_materials`, và bất kỳ tổ tiên nào.
  - Phạm vi của một thao tác **xoá** phải luôn tính **tương đối so với gốc mình quản**, không bao giờ trên đường dẫn tuyệt đối — phần tổ tiên là thứ người dùng đặt tên, ta không kiểm soát được.
  - Một test chỉ có giá trị khi nó **thất bại trên bản chưa sửa**. Nên ghi luôn phép đối chiếu cũ/mới vào test.

### 46. `main()` vứt danh sách "xoá không được" của `cleanup_unused()`
- **Ngày:** 2026-08-18
- **Mức độ:** 🟠 High (thất bại có thật nhưng không bao giờ đến mắt người dùng)
- **Vị trí:** `goi_project_capcut.py` → `main()`, chỗ `opt_clean = TU.cleanup_unused(out_dir)`.
- **Triệu chứng:** `cleanup_unused()` trả về 3 giá trị, `main()` chỉ dùng `opt_clean[0]` và `opt_clean[1]`. Giá trị thứ ba — danh sách file **xoá không được** (file đang bị khoá, hết quyền, SMB rớt) — bị bỏ đi hoàn toàn.
- **Nguyên nhân gốc:** Hàm được mở rộng để trả thêm thông tin nhưng chỗ gọi không được cập nhật theo. Vi phạm thẳng checklist *"đếm mọi thất bại và đưa vào báo cáo"*.
- **Cách sửa:** Thêm hai mục vào báo cáo: `DON DEP - file KHONG xoa duoc` và `DON DEP - file JSON KHONG doc duoc`. Dùng `len(opt_clean) > 3` để không vỡ nếu còn chỗ gọi dùng dạng 3 giá trị.
- **Cách phát hiện / kiểm chứng:** `tests/test_don_dep.py` khẳng định `cleanup_unused()` trả **đủ 4 phần** và `loi_doc` có đúng 1 mục khi có 1 file JSON hỏng.
- **Bài học (để tránh lặp lại):** Khi thêm giá trị trả về cho một hàm, **grep hết chỗ gọi ngay trong cùng lần sửa**. Một giá trị trả về không ai đọc thì tệ hơn là không có — nó tạo cảm giác đã xử lý trong khi thông tin rơi vào hư không.

### 47. Còn thao tác filesystem không qua `_lp()` — trong đó có `mkdir` thư mục XUẤT RA và `os.walk` khi dò theo tên
- **Ngày:** 2026-08-18
- **Mức độ:** 🟠 High (chết giữa chừng sau khi đã hỏi xong; và báo "THIẾU" oan cho file vẫn còn đó)
- **Vị trí:** `goi_project_capcut.py` → `main()` (`out_dir.mkdir`), `index_by_names()`, `scan_drafts_recursive()`, `is_draft_dir()`.
- **Triệu chứng:** (a) Đích do người dùng gõ vượt 260 ký tự → `out_dir.mkdir(parents=True)` ném `FileNotFoundError [WinError 3]` **sau khi** người dùng đã trả lời hết câu hỏi và bấm `y` — mất toàn bộ phần hỏi đáp, thông báo lỗi không nói lên nguyên nhân. (b) Bước "dò theo tên" dùng `os.walk` trần: file nằm sau đường dẫn dài **không bao giờ được tìm thấy** → báo THIẾU oan.
- **Nguyên nhân gốc:** Mở rộng lần thứ năm của #1/#7/#23: `_lp()` được áp cho phần lớn thao tác nhưng vẫn sót ở **cửa vào của luồng** — đúng chỗ dễ dài nhất, vì đó là đường dẫn người dùng gõ. Riêng `os.walk` còn nuốt lỗi: `onerror=None` mặc định làm cả một nhánh cây biến mất im lặng.
- **Cách sửa:** Thêm `isdir_safe()` (song sinh của `isfile_safe()`); `Path(_lp(out_dir)).mkdir(...)`; `os.walk(_lp(root), onerror=...)` rồi `_unlp(dp)` trước khi ghép đường dẫn hoặc **đếm số thành phần** — nếu không, prefix `\\\\?\` làm phép tính độ sâu bị lệch và cắt nhầm nhánh; `is_draft_dir()` dùng `isfile_safe()`.
- **Cách phát hiện / kiểm chứng:** `grep -n "os.walk(" | grep -v "_lp("` phải ra rỗng. Bộ E2E chạy toàn bộ luồng trên draft giả vẫn đạt 24/24 sau khi sửa.
- **Bài học (để tránh lặp lại):**
  - Chỗ nguy hiểm nhất luôn là **đường dẫn người dùng vừa gõ vào**, không phải đường dẫn nội bộ. Rà `_lp()` phải bắt đầu từ cửa vào.
  - `os.walk` có **hai** cái bẫy chứ không phải một: thiếu `_lp` (bỏ sót đường dẫn dài) và `onerror=None` (nuốt lỗi cả nhánh). Sửa một cái mà quên cái kia thì vẫn mất file âm thầm.
  - Sau khi bọc `_lp`, phải soát lại **mọi phép tính dựa trên hình dạng chuỗi path** (đếm `parts`, cắt tiền tố, so sánh) — prefix extended-length làm chúng lệch.

### 48. `_find_main_module()` nhận bừa module GIẢ chỉ vì trùng hai tên thuộc tính
- **Ngày:** 2026-08-18
- **Mức độ:** 🟠 High (mọi thao tác đường dẫn chạy bằng hàm giả, không một cảnh báo nào)
- **Vị trí:** `toi_uu_dung_luong.py` → `_find_main_module()`
- **Triệu chứng:** Một script chạy dưới tên `__main__` chỉ cần định nghĩa `_lp` và `draft_root_of` rồi `import toi_uu_dung_luong` là bị nhận nhầm làm module chính. Đã dựng thử script 4 dòng: `T.G._lp("x")` trả về `GIA:x`, thoát mã 0, không cảnh báo.
- **Nguyên nhân gốc:** Phép kiểm là duck-typing trên **hai cái tên**, không hề xác minh **danh tính file**. Không phải giả định xa vời: chính `bug.md` khuyến khích viết **verifier độc lập**, mà loại script đó rất tự nhiên sẽ tự định nghĩa `_lp` — vì `_lp` chính là thứ đã gây #1, #23, #34.
- **Cách sửa:** So bằng `os.path.samefile(m.__file__, <thư mục của file này>/goi_project_capcut.py)`. Bỏ qua module không có `__file__`, bắt `OSError`.
- **Cách phát hiện / kiểm chứng:** `tests/test_don_dep.py` chạy đúng script bẫy đó trong tiến trình riêng và khẳng định `GIA:x` **không** xuất hiện, đồng thời `T.G` vẫn là module thật. Kèm kiểm 3 kịch bản khởi động (`import`, chạy trực tiếp, `python -m`) không bị vỡ.
- **Bài học (để tránh lặp lại):** Duck-typing hợp lý khi chọn **hành vi**, nhưng sai khi xác minh **danh tính**. Câu hỏi ở đây là *"có đúng file đó không"* — và câu đó chỉ trả lời được bằng `samefile`, không bằng `hasattr`. Mục này sẽ biến mất khi tách `chung.py` (E1) vì lúc đó không còn phải đi tìm module nào cả. **Cập nhật 2026-08-18: E1 đã làm xong** — `_find_main_module()` bị xoá hẳn, `toi_uu_dung_luong.py` chỉ còn `import chung as G`. Bản vá `os.path.samefile` không còn trong code nữa vì **không còn bước tra cứu nào để đánh lừa**. Bộ kiểm `tests/test_don_dep.py` vẫn giữ kịch bản bẫy làm lưới chống hồi quy: nếu lần sau ai đó dựng lại cơ chế tìm-module thì bẫy này sống lại.


### 50. Nhãn "chưa cài" trong nhật ký lạc hậu theo CẢ HAI CHIỀU — và va chạm giữa hai session cùng sửa repo
- **Ngày:** 2026-08-18
- **Mức độ:** 🟠 High (làm mất phương hướng: sửa lại việc đã xong, hoặc tưởng bug đã chết trong khi nó còn sống)
- **Vị trí:** `bug.md` — các mục #29, #30, #35; và quy trình làm việc nói chung.
- **Triệu chứng:** Ba mục vẫn ghi `Cách sửa (chưa cài)` / `CẦN CÀI vào code` trong khi bản vá **đã nằm trong code từ trước**. Cùng lúc, mục #38 ghi `CHƯA CÀI` và điều đó **là thật**. Nhìn vào nhật ký không phân biệt được hai loại. Ngoài ra, trong đúng phiên làm việc này, `bug.md` bị session khác sửa **hai lần** giữa chừng, và `toi_uu_dung_luong.py` được session khác vá `encode_job()` xong trong lúc phiên này còn đang phân tích chính hàm đó.
- **Nguyên nhân gốc:**
  1. Nhãn trạng thái được viết **một lần lúc phát hiện bug** rồi không ai quay lại cập nhật khi cài xong. Mục #32 đã dạy "ghi *chưa cài* không phải là đã sửa", nhưng bài học đó chỉ đi **một chiều** — không ai nghĩ tới chiều ngược lại: *đã cài rồi mà nhãn vẫn nói chưa*.
  2. Không có **máy kiểm** nào đối chiếu nhãn với code. Mọi thứ dựa vào trí nhớ, mà trí nhớ thì không sống sót qua ranh giới session.
  3. Nhiều session cùng ghi vào một file không có cơ chế phát hiện va chạm nào ngoài mắt người.
- **Cách sửa — ĐÃ CÀI:**
  1. Sửa nhãn của #29, #30, #35 thành `ĐÃ CÀI` kèm ngày và dấu văn xác minh được trong code.
  2. Thêm `tests/kiem_nhat_ky.py`: kiểm số hiệu (trùng/thiếu), liệt kê mục còn `chưa cài`, và **đối chiếu nhãn với code thật** qua bảng dấu văn. Mục nào chưa cài thì **không đặt dấu văn bịa** — dấu văn bịa sẽ sinh kết luận "OK" giả.
  3. Đưa bộ kiểm này vào `tests/chay_het.py` chạy **đầu tiên**.
  4. Thêm mục 5 và mục "Khi có NHIỀU SESSION cùng làm" vào `CLAUDE.md`.
- **Cách phát hiện / kiểm chứng:** `python tests\kiem_nhat_ky.py` — sau khi sửa: 49 mục, dãy 1–49 liền mạch, đúng **một** mục còn `chưa cài` (#38, bug thật), và nhãn khớp code trên toàn bộ mục có dấu văn đối chiếu.
- **Bài học (để tránh lặp lại):**
  - **Mọi nhãn trạng thái viết bằng tay đều sẽ lạc hậu.** Cách duy nhất giữ nó đúng là có máy đối chiếu nhãn với hiện vật — y hệt bài học #32 (*cache phục hồi phải đối chiếu với file thật, không tin sổ sách suông*), nhưng lần này hiện vật là **mã nguồn**.
  - Khi nhiều session cùng sửa một repo, **đọc lại ngay trước khi ghi** là bắt buộc, không phải cẩn thận thừa. Ba lần va chạm trong một phiên đều bị bắt bởi phép kiểm chạy **sau khi** sửa — nếu chỉ sửa rồi tin là xong thì cả ba đã lọt.
  - Một bài học đúng vẫn có thể **thiếu một chiều**. #32 dạy "chưa cài ≠ đã sửa" nhưng không ai nghĩ tới "đã sửa mà nhãn vẫn nói chưa". Khi rút bài học, nên tự hỏi chiều ngược lại có sai được không.


### 51. Mọi bộ đếm của pha tối ưu bị NHÂN ĐÔI — vì `main()` luôn ghi cả `draft_content.json` lẫn `draft_info.json`
- **Ngày:** 2026-08-18
- **Mức độ:** 🟠 High (mọi con số báo cáo cho người dùng đều sai gấp đôi)
- **Vị trí:** `toi_uu_dung_luong.py` → `optimize_package()`, khối cộng dồn `st[...]`.
- **Triệu chứng:** Đo bằng E2E: một lần gọi ffmpeg **thật** ra file 1.394.322 byte, nhưng `st["added"] = 2.788.644` — đúng **2,0 lần**. Dòng tổng kết in `2/2 clip, nén bitrate 2` trong khi chỉ có **1** clip được mã.
- **Nguyên nhân gốc:** `main()` **luôn** ghi cả `draft_content.json` lẫn `draft_info.json` với **cùng nội dung**, mà cả hai đều nằm trong `CONTENT_NAMES` ⇒ `optimize_package()` duyệt cả hai ⇒ mỗi material sinh thêm một job `dup`. Job `dup` không gọi ffmpeg lần nào và không thêm một byte nào vào đĩa, nhưng vẫn đi qua vòng áp dụng JSON và vẫn được cộng vào bộ đếm. Bản vá #32 (cho #30) chỉ rào **`saved`** bằng `_saved_srcs`, bỏ sót `added`/`ok`/`trim`/`scale`/`recompress` — dù bài học của chính #30 đã viết: *"khi có job dup, MỌI phép cộng dồn theo job đều có nguy cơ đếm trùng"*.
- **Cách sửa:** Bọc toàn bộ khối cộng dồn trong `if not j.get("dup"):`. Riêng `changed` vẫn tăng cho job `dup` vì JSON của file content thứ hai **thật sự** có thay đổi và phải được ghi.
- **Cách phát hiện / kiểm chứng:** `tests/test_dem.py` — đếm số lần `encode_job` thật sự chạy (bằng cách bọc hàm), rồi so `st["added"]` với **tổng kích thước thật của mọi file `_opt` trên đĩa**. Sau khi sửa: ffmpeg chạy 3 lần, 3 file trên đĩa tổng 1.911.272 byte, `st["added"] = 1.911.272` — khớp chính xác.
- **Bài học (để tránh lặp lại):**
  - Khi một bài học nói *"mọi X đều có nguy cơ Y"*, phải **rà hết mọi X ngay lần đó**, đừng vá đúng cái X đang cháy. Bản vá #32 sửa 1 trong 6 bộ đếm rồi coi như xong.
  - Cách kiểm bộ đếm đáng tin nhất là **đối chiếu với hiện vật trên đĩa**, không phải đọc lại logic cộng dồn. Cùng nguyên tắc đã dùng cho cache (#32) và cho độ dài file (#35).

### 52. Material bị loại khỏi việc mã lại một cách IM LẶNG — `st["skipped_big"]` khai báo nhưng không bao giờ tăng
- **Ngày:** 2026-08-18
- **Mức độ:** 🟡 Medium (người dùng không bao giờ hiểu vì sao clip dài nhất của họ không được nén)
- **Vị trí:** `toi_uu_dung_luong.py` → `collect_jobs()`
- **Triệu chứng:** `st["skipped_big"]` được khởi tạo ở đầu `optimize_package()` và `grep` toàn project chỉ ra **đúng một** kết quả — nó không bao giờ được tăng. Clip có `span > MAX_SPAN_US` (30 phút) bị loại bằng `continue` trần: không đếm, không in, không vào `_BAO_CAO_THIEU.txt`. Cùng kiểu còn hai chỗ nữa: không tìm thấy nguồn, và `getsize` lỗi.
- **Nguyên nhân gốc:** `continue` là cách rẻ nhất để bỏ qua một phần tử, và không có gì nhắc người viết rằng "bỏ qua" cũng là một **kết quả cần báo cáo**. Bộ đếm được khai báo sẵn nhưng khâu nối vào bị quên — không ai phát hiện vì không có phép kiểm nào đòi hỏi tổng số material phải khớp.
- **Cách sửa:** Thêm danh sách `bo_qua` trong `collect_jobs()`, ghi `(nguồn, lý_do)` ở cả ba chỗ. Đổi `collect_jobs()` trả về `(jobs, bo_qua)`, gom vào `st["bo_qua"]`, và in thành mục riêng trong báo cáo: *"TOI UU - clip KHONG dua vao ma lai (giu nguyen ban goc)"*.
- **Cách phát hiện / kiểm chứng:** `tests/test_dem.py` hạ `MAX_SPAN_US` xuống 1 giây để mọi clip đều vượt ngưỡng, rồi khẳng định `st["bo_qua"]` có lý do chứa "vượt mức" và `st["ok"] == 0`.
- **Bài học (để tránh lặp lại):**
  - **Một bộ đếm khai báo mà không bao giờ tăng là dấu hiệu của một nhánh bị bỏ quên.** Nên grep các khoá của `st` xem khoá nào chỉ xuất hiện một lần — đó là danh sách nhánh chưa nối.
  - `continue` trần trong vòng lặp xử lý dữ liệu người dùng gần như luôn cần đi kèm một dòng ghi nhận. "Bỏ qua" là quyết định, và mọi quyết định của tool đều phải giải thích được.

### 53. `json_fail` không phân biệt vai trò file — một file cache hỏng sẵn khiến tool VĨNH VIỄN báo "CÒN THIẾU"
- **Ngày:** 2026-08-18
- **Mức độ:** 🟡 Medium (báo động giả theo chiều ngược lại — làm mất niềm tin vào lớp tự kiểm)
- **Vị trí:** `goi_project_capcut.py` → biểu thức `ok` và mục báo cáo `FILE .json DOC LOI`.
- **Triệu chứng:** `json_fail` và `json_fail2` gộp mọi file `.json` đọc lỗi vào một rổ rồi đưa thẳng vào biểu thức kết luận. Nếu draft gốc có sẵn một file **cache** hỏng (`mini_draft.json`, `draft_agency_*.json`), tool sẽ kết luận "CÒN THIẾU" ở **mọi lần chạy**, và người dùng không có cách nào làm cho nó sạch.
- **Nguyên nhân gốc:** Chính tool đã có `json_role()` phân biệt content / registry / cache, và `verify_package()` đã dùng nó để hạ cấp tham chiếu hỏng trong cache (bài học #21, #31). Nhưng `json_fail` được viết ở một chỗ khác và **không hưởng bài học đó** — đúng kiểu "bài học chỉ áp cho một nhánh".
- **Cách sửa:** Thêm `json_fail_hard()` lọc theo `json_role()`. Biểu thức `ok` chỉ tính loại **có ảnh hưởng** (content + registry). Báo cáo tách hai mục: *"CO anh huong"* và *"cache doc loi (KHONG anh huong video xuat ra)"* — vẫn hiện đầy đủ để không giấu thông tin, nhưng không còn chặn kết luận.
- **Cách phát hiện / kiểm chứng:** Gọi trực tiếp `json_fail_hard()` với 4 mẫu: `draft_content.json` và `subdraft/X/draft_meta_info.json` → **có** ảnh hưởng; `mini_draft.json` và `Resources\draft_agency_1.json` → **không**.
- **Bài học (để tránh lặp lại):**
  - Khi rút được một luật phân loại (ở đây là `json_role`), phải **grep xem còn chỗ nào đang quyết định mà chưa dùng luật đó**. Bài học #31 đã dạy điều này cho verifier, nhưng `json_fail` vẫn lọt.
  - **Báo động giả và bỏ sót đều là lỗi**, và báo động giả dai dẳng còn nguy hiểm hơn ở chỗ nó dạy người dùng bỏ qua cảnh báo. Với 15–20 người dùng thì một cảnh báo không bao giờ tắt được sẽ bị mặc định là "bình thường".


### 54. Cài phần "chưa cài" của #38 — sổ đăng ký trỏ lại được bản `_opt` đầy đủ nhất, kèm phép nghiệm thu tự động
- **Ngày:** 2026-08-18
- **Mức độ:** 🟠 High (gói phình thêm 35% — 10,46 GB trên `DS1_090` — mà không ai dùng tới phần đó)
- **Vị trí:** `toi_uu_dung_luong.py` → `optimize_package()` (bảng `opt_all_by_src`), `repoint_registry()`, và hàm mới `kiem_ban_goc_thua()`; `goi_project_capcut.py` → `main()` + báo cáo.
- **Triệu chứng:** Mục #38 ghi rõ `Cách sửa (CHƯA CÀI — cần làm)` — tức bug vẫn đang sống. Hậu quả còn nguyên: 9 file gốc (10,46 GB) chỉ còn sổ đăng ký trỏ tới nên `cleanup_unused()` không dám xoá.
- **Nguyên nhân gốc:** Hai chỗ độc lập nhau, phải sửa cả hai:
  1. `opt_by_src` dùng `setdefault` nên chỉ giữ **bản `_opt` đầu tiên** của mỗi nguồn. Nhưng một file nguồn dùng ở nhiều material sẽ sinh **nhiều bản** (fixture tái hiện: 1 nguồn → **5 bản**).
  2. `repoint_registry()` gọi `resolve_material_file(..., {})` với dict rỗng, trong khi `collect_jobs()` gọi với `resolved` thật. File nào được "dò theo tên" sẽ giải ra đường dẫn **khác** với khoá đã lưu ⇒ tra không khớp ⇒ mục sổ đăng ký giữ nguyên path gốc.
- **Cách sửa:**
  1. Thêm `opt_all_by_src` (`defaultdict(list)`) ghi **mọi** bản `_opt` của từng nguồn, song song với `opt_by_src` — **không đổi hình dạng** `opt_by_src` vì `plan_package()` đang phụ thuộc vào nó.
  2. Trong `repoint_registry()`, dựng `day_du_nhat`: với mỗi nguồn, chọn bản `_opt` có **kích thước lớn nhất**. Sổ đăng ký chỉ phục vụ **thư viện media** của CapCut (không phải timeline) nên trỏ vào bản đầy đủ nhất là đúng ngữ nghĩa. Thứ tự tra: khoá chính xác `(base, src)` → `by_src` → `day_du_nhat`.
  3. Truyền `resolved` xuống `repoint_registry()` để giải đường dẫn **y hệt** `collect_jobs()`.
  4. Thêm `kiem_ban_goc_thua(out_dir)`: quét gói, tìm media **không phải `_opt`** mà **không file `content` nào** trỏ tới, trả `(đường_dẫn, số_byte)` sắp giảm dần. Gọi trong `main()` ngay sau `cleanup_unused()`, in ra console và ghi mục riêng trong báo cáo. Bọc `try/except` ghi vào `verify_loi` (mục 41) — phép nghiệm thu chết thì không được coi là "sạch".
- **Cách phát hiện / kiểm chứng:** `tests/test_ban_goc_thua.py` — thêm tuỳ chọn `nhieu_doan` vào bộ sinh draft giả để **một nguồn dùng ở 3 material** với các đoạn cắt khác nhau. Kết quả: sinh **5 bản `_opt`**, `repointed = 8`, `kiem_ban_goc_thua()` phát hiện đúng bản gốc thừa, và **sau `cleanup_unused()` bản gốc biến mất khỏi gói**. Kèm hai phép kiểm chống báo động giả: không được coi bản `_opt` là thừa, và trên gói chưa tối ưu thì media đang được content dùng **không** bị gắn cờ.
- **Bài học (để tránh lặp lại):**
  - **Hai hàm cùng giải một đường dẫn thì phải nhận cùng tham số.** `collect_jobs()` có `resolved`, `repoint_registry()` thì không — chỉ khác một chỗ đó là đủ để hai bên cho ra khoá khác nhau và bảng tra trượt hoàn toàn. Khi có hai lời gọi cùng một hàm giải, nên so đối số của chúng như một bước rà soát.
  - **Đừng đổi hình dạng một cấu trúc đang được hàm khác dùng** chỉ để thêm thông tin — thêm cấu trúc song song rẻ hơn và không gây hồi quy. `opt_by_src` vẫn nguyên cho `plan_package()`.
  - **Biến phân tích thủ công thành phép đếm tự động.** Bug #38 được tìm ra bằng cách phân loại tay toàn bộ file rồi tra khoá đường dẫn. Việc đó giờ là `kiem_ban_goc_thua()` chạy mỗi lần — đúng tinh thần "phép thử vô lý" của #18/#19, nhưng không phụ thuộc vào việc có ai để ý dung lượng cuối hay không.


### 55. `_save_opt_index()` duyệt dict trong khi thread mã hoá đang ghi → `RuntimeError` giết chết thread nhịp đập
- **Ngày:** 2026-08-18
- **Mức độ:** 🟠 High (mất CẢ nhịp đập chống treo lẫn cơ chế ghi cache định kỳ — hai lớp phòng thủ đắt giá nhất)
- **Vị trí:** `toi_uu_dung_luong.py` → `_save_opt_index()`, hai vòng `for ... in (dict).items()`.
- **Triệu chứng:** Hiếm nhưng phá hoại: thread nhịp đập gọi `_save_opt_index()` mỗi 60 giây, trong khi các worker đang chèn khoá mới vào chính `cache` / `key_names`. Python ném `RuntimeError: dictionary changed size during iteration`. Lỗi này thoát khỏi `_save_opt_index()`, thoát tiếp khỏi `_heartbeat()` (không có `try/except`) ⇒ **thread nhịp đập chết âm thầm**. Từ đó mất luôn nhịp đập chống treo (#25) và việc ghi sổ cache định kỳ (#29), mà không một dòng thông báo nào.
- **Nguyên nhân gốc:** Hai vòng duyệt nằm **ngoài** khối `try` (khối đó chỉ bao `json.dump`). Người viết bảo vệ đúng thao tác ghi file nhưng không nghĩ tới việc **đọc dict** cũng có thể ném lỗi khi có thread khác ghi.
- **Cách sửa:** Chụp nhanh bằng `list(d.items())` ở cả hai vòng. `list(dict.items())` là **một thao tác ở tầng C**, không chạy bytecode Python ở giữa nên không có điểm đổi thread — rẻ hơn `threading.Lock` (2 chỗ sửa thay vì 3 khối `with`) và **không có khoá nào bắc qua I/O mạng**.
- **Cách phát hiện / kiểm chứng:** `tests/test_on_dinh.py` — 4 thread chèn liên tục vào dict 4.000 mục trong khi luồng chính gọi `_save_opt_index()` 60 lần. Sau khi sửa: **0/60 lần ném lỗi**.
- **Bài học (để tránh lặp lại):** `try` phải bao **toàn bộ** phần có thể ném lỗi, không chỉ phần "trông nguy hiểm". Đọc một cấu trúc dữ liệu đang được thread khác ghi là thao tác **có thể ném lỗi** — điều này dễ quên vì nó không giống I/O. Và một thread nền không có `try/except` bao thân vòng lặp thì mọi lỗi bên trong đều thành **cái chết im lặng**.

### 56. Ghi `_opt_index.json` KHÔNG atomic + nhiều thread nhịp đập cùng tồn tại
- **Ngày:** 2026-08-18
- **Mức độ:** 🟠 High (mất sạch sổ cache — đúng thảm hoạ mà chính nó sinh ra để chống)
- **Vị trí:** `toi_uu_dung_luong.py` → `_save_opt_index()` và khối nhịp đập trong `optimize_package()`.
- **Triệu chứng:** Hai vấn đề chồng nhau. (a) Sổ cache được ghi **đè trực tiếp** (`open(..., "w")`) lên đích thường là **ổ mạng** — bị giết đúng lúc đang ghi là file rỗng/cụt, lần chạy sau nạp lỗi và **mã lại từ đầu** (thảm hoạ #29: 454 → 907 → 1367 file trùng). (b) `stop_hb` là biến **bị gán lại ở mỗi vòng lặp file content**, mà closure `_heartbeat` đọc theo **ô nhớ** chứ không theo giá trị ⇒ thread của vòng trước nhìn thấy `Event` của vòng sau ⇒ `stop_hb.set()` không dừng được nó ⇒ **nhiều nhịp đập sống song song, cùng ghi một file sổ**. Thêm nữa không có `hb.join()` nên luồng chính và nhịp đập có thể cùng mở file ghi.
- **Nguyên nhân gốc:** Cơ chế chống mất-tiến-độ được thêm vội (bản vá #32) mà không xét tới việc chính nó chạy đồng thời với thứ nó đang bảo vệ.
- **Cách sửa:**
  1. Ghi ra file tạm rồi `os.replace()` — đổi tên là thao tác nguyên tử, sổ **luôn** ở trạng thái hợp lệ.
  2. Tên file tạm mang `PID` + `threading.get_ident()` ⇒ dù có nhiều nhịp đập cùng ghi thì mỗi luồng vẫn ghi file riêng, `os.replace` chỉ khiến "người cuối thắng". **Không cần khoá.** Đuôi `.tmp` nên `cleanup_unused()` dọn được nếu còn sót.
  3. Ghi thất bại thì **xoá file tạm** rồi mới cảnh báo — không để rác lại.
  4. `def _heartbeat(_stop=stop_hb)` — buộc bind **giá trị** qua tham số mặc định, không đọc biến ngoài.
  5. Thêm `hb.join(timeout=10)` trước lần ghi cuối.
- **Cách phát hiện / kiểm chứng:** `tests/test_on_dinh.py` — ép `json.dump` ném lỗi giữa chừng rồi khẳng định **bản cũ còn nguyên vẹn từng byte** và **không để lại file tạm**; kèm phép kiểm sổ hỏng thì `_load_opt_index()` trả rỗng chứ không ném lỗi.
- **Bài học (để tránh lặp lại):**
  - **Mọi lần ghi đè một file trạng thái đều phải atomic.** Ghi tạm + `os.replace` là hai dòng, và nó là khác biệt giữa "mất 60 giây công" với "mất cả pha chạy hàng giờ".
  - Trong Python, closure bắt **biến** chứ không bắt **giá trị**. Biến bị gán lại trong vòng lặp mà closure đọc nó thì mọi thread sinh ra đều dùng chung số phận — dùng tham số mặc định để bind giá trị.
  - Đặt tên file tạm theo **PID + thread id** biến một bài toán đồng thời thành bài toán không cần khoá.

### 57. Ghi sổ cache định kỳ nuốt SẠCH lỗi — cơ chế chống #29 có thể chết âm thầm suốt cả lần chạy
- **Ngày:** 2026-08-18
- **Mức độ:** 🟡 Medium (mất khả năng phục hồi mà không ai biết, chỉ lộ ra khi phải chạy lại)
- **Vị trí:** `toi_uu_dung_luong.py` → nhịp đập gọi `_save_opt_index(..., log=lambda *_: None)`.
- **Triệu chứng:** Mọi thất bại ghi `_opt_index.json` **trong suốt pha chạy** đều bị nuốt sạch; chỉ lần ghi cuối cùng mới báo. Đích hết chỗ, mất mạng, hết quyền — người dùng không biết gì, và chỉ phát hiện khi bị giết giữa chừng rồi thấy lần sau mã lại từ đầu.
- **Nguyên nhân gốc:** Truyền hàm log rỗng để **tránh spam mỗi 60 giây** — mục đích đúng nhưng cách làm sai: chọn "im hoàn toàn" thay vì "nói một lần".
- **Cách sửa:** Thay bằng `_log_loi_ghi_so()`: đếm số lần lỗi, **chỉ in ở lần đầu**, và đưa tổng số vào `st["loi_ghi_so"]` để báo ở cuối pha.
- **Cách phát hiện / kiểm chứng:** KHÔNG dùng `grep` — chuỗi đó vẫn còn trong comment mô tả code cũ, nên `grep` cho kết quả dương tính giả (đã mắc đúng bẫy này khi viết mục này). Kiểm bằng **AST**, chỉ tính lời gọi thật:
  ```python
  import ast
  t = ast.parse(open("toi_uu_dung_luong.py", encoding="utf-8").read())
  xau = [n.lineno for n in ast.walk(t) if isinstance(n, ast.Call)
         for kw in (n.keywords or [])
         if kw.arg == "log" and isinstance(kw.value, ast.Lambda)
         and isinstance(kw.value.body, ast.Constant) and kw.value.body.value is None]
  assert not xau, xau
  ```
- **Bài học (để tránh lặp lại):** Khi sợ spam log, giải pháp là **giới hạn tần suất**, không phải **tắt tiếng**. "In lần đầu + đếm phần còn lại" giữ được thông tin mà vẫn không làm ngập màn hình. Đây là biến thể tinh vi của `except: pass` — nó không nuốt exception, nó nuốt **thông báo**.

### 58. `fixed_drives()` có thể TREO chứ không chỉ chậm — và nó vẫn đang liệt kê cả ổ mạng
- **Ngày:** 2026-08-18
- **Mức độ:** 🟠 High (treo ngay trước câu hỏi quan trọng nhất; và là mục "chưa cài" của #27)
- **Vị trí:** `goi_project_capcut.py` → `fixed_drives()`
- **Triệu chứng:** Hàm gọi `Path(f"{L}:/").exists()` cho **cả 26 chữ cái**. Với một ổ mạng đã ánh xạ nhưng phiên SMB đã rớt, lời gọi đó có thể chặn hàng giây tới **vô hạn** — và vì nó **không ném `OSError`** nên khối `try/except OSError` bên dưới hoàn toàn vô tác dụng. Đây là nguyên nhân gốc của #25/#28 (*"Python KHÔNG có timeout mặc định cho I/O filesystem"*) xuất hiện ở chỗ thứ ba, nằm ngay **trước** câu hỏi "Thư mục/ổ để dò".
- **Nguyên nhân gốc:** Dùng phép thử **chạm vào thiết bị** (`exists()`) để trả lời một câu hỏi thuần **siêu dữ liệu** (ổ nào đang tồn tại, thuộc loại gì).
- **Cách sửa:** Dùng `GetLogicalDrives()` (bitmask, không chạm thiết bị) để liệt kê, rồi `GetDriveTypeW()` để phân loại — cả hai chỉ tra bảng ổ cục bộ. Chỉ giữ ổ `DRIVE_FIXED`. Việc loại ổ mạng khỏi danh sách mặc định **chính là cải tiến mà #27 đề nghị**: quét cạn ổ mạng 22 TB để tìm một file là vô ích và mất hàng giờ. Cùng lúc thêm `la_o_mang()` dùng chung cơ chế đó.
- **Cách phát hiện / kiểm chứng:** `tests/test_on_dinh.py` — đo thời gian `fixed_drives()` (0,010 s) và khẳng định không ổ nào trả về là `DRIVE_REMOTE`. Trên máy này: 6 ổ tồn tại (C, D, F, G, Y, Z), trong đó **F, Y, Z là ổ mạng** và đã bị loại đúng.
- **Bài học (để tránh lặp lại):**
  - Muốn biết **thông tin về** một tài nguyên thì hỏi hệ điều hành, đừng **chạm vào** tài nguyên đó. `exists()` là I/O; `GetDriveTypeW` là tra bảng.
  - `try/except OSError` **không cứu được việc treo**. Treo không phải ngoại lệ. Mọi chỗ có thể chặn vô hạn phải được xử lý bằng cách **không gọi nó**, hoặc gọi ở nơi có thể bỏ dở.

### 59. Tham số mã hoá chốt cứng trong `main()` — không hạ được số luồng khi đích là NAS (mục "chưa cài" của #25)
- **Ngày:** 2026-08-18
- **Mức độ:** 🟡 Medium (tăng rủi ro treo SMB; và không ai chỉnh được nếu không sửa code)
- **Vị trí:** `goi_project_capcut.py` → `main()`, dict `opts`.
- **Triệu chứng:** `crf`, `preset`, `workers` được viết thẳng giữa `main()`. `workers` luôn bằng 4 bất kể đích là ổ cục bộ hay NAS. Mục #25 ghi rõ: *"chạy nhiều tác vụ nặng cùng lúc trên cùng NAS làm tăng mạnh rủi ro treo SMB, không chỉ làm chậm"* — nhưng phần đó vẫn **chưa cài**.
- **Nguyên nhân gốc:** Không có khái niệm "cấu hình". Với 15–20 người dùng trên các máy khác nhau thì không thể bắt mỗi người sửa code.
- **Cách sửa:** Thêm `cau_hinh.json` cạnh tool + `doc_cau_hinh()` và `chon_so_luong()`. Thiếu file / JSON hỏng / khoá lạ đều **báo rõ rồi dùng mặc định**, không làm chết tool. `workers: null` nghĩa là **tự chọn theo đích**: 2 luồng khi `la_o_mang(out_dir)` là đúng, 4 khi ổ cục bộ. Đặt số cụ thể thì được tôn trọng. File cấu hình có dòng `_huong_dan` giải thích từng khoá bằng tiếng Việt cho người không phải lập trình viên.
- **Cách phát hiện / kiểm chứng:** `tests/test_on_dinh.py` — đích UNC → 2 luồng, đích `C:\` → 4 luồng, `workers: 7` được tôn trọng, `workers: "ba"` (sai kiểu) quay về tự chọn thay vì chết.
- **Bài học (để tránh lặp lại):**
  - **Giá trị mặc định an toàn quan trọng hơn khả năng chỉnh.** Phần lớn trong 15–20 người sẽ không bao giờ mở tệp cấu hình — nên cái quyết định chất lượng là *mặc định*, còn tệp cấu hình chỉ phục vụ thiểu số.
  - Cấu hình đọc từ file phải chịu được **mọi kiểu sai** của người dùng (thiếu file, JSON hỏng, sai kiểu, khoá lạ) và luôn nói rõ nó đã làm gì. Một tệp cấu hình làm chết tool còn tệ hơn không có tệp nào.


### 60. E1 — tách `chung.py`: diệt vòng tròn import, bản chép `_lp()` và hack tra `sys.modules` bằng một bước
- **Ngày:** 2026-08-18
- **Mức độ:** 🟡 Medium (không phải bug đang cháy, nhưng là nguồn của #48 và của rủi ro bản chép lệch)
- **Vị trí:** file mới `chung.py`; `goi_project_capcut.py`, `toi_uu_dung_luong.py`, `xem_tien_trinh.py`.
- **Triệu chứng (trước khi tách):** ba vấn đề cùng một gốc.
  1. `toi_uu_dung_luong.py` phải đi **tìm ngược** module chính bằng `_find_main_module()` (tra `sys.modules`) ⇒ hai file phụ thuộc **vòng tròn**, và `import toi_uu_dung_luong` buộc phải nằm **trong hàm** — đưa lên đầu file là nạp file hai lần hoặc crash, mà không có comment nào cảnh báo.
  2. Cơ chế tìm-module đó nhận bừa module giả (#48).
  3. `xem_tien_trinh.py` **chép** `_lp()` và `_fmt_time()`. Mà `_lp()` đã phải sửa ít nhất ba lần (#1, #23, #34) — sửa bản gốc mà quên bản chép là hỏng âm thầm trên đường dẫn UNC/dài.
- **Nguyên nhân gốc:** code được chia theo **PHA xử lý** chứ không theo **TẦNG**. `toi_uu` chỉ mượn 17 cái tên, **tất cả đều là tiện ích tầng dưới** (hàm thuần + hằng số), không hề gọi ngược vào các pha đóng gói. Nên đây không phải vòng tròn kiến trúc thật — chỉ là *tầng tiện ích chưa được tách ra*.
- **Cách sửa:** trích **nguyên văn** 30 khối (dùng `ast` lấy đúng đoạn nguồn, **không chép tay** — chép tay là đường sinh lỗi im lặng) sang `chung.py` (346 dòng, chỉ hàm thuần + hằng số). `goi_project_capcut.py` dùng `from chung import (...)` **liệt kê tường minh** — `import *` không dùng được vì bỏ qua mọi tên bắt đầu bằng `_`, mà phần lớn tiện ích ở đây là `_lp`, `_np`, `_unlp`... `toi_uu_dung_luong.py` chỉ còn `import chung as G` (giữ tên `G` nên **không phải sửa 80+ chỗ gọi**). `xem_tien_trinh.py` bỏ hai bản chép, còn 92 dòng.
- **ĐÍNH CHÍNH (cùng ngày):** phần kiểm chứng dưới đây **CHƯA ĐỦ** và đã bỏ lọt một lỗi thật — xem mục 61. Bảng tổng kết báo "TẤT CẢ ĐẠT" trong khi `xem_tien_trinh.py` đã hỏng hoàn toàn, vì **không bộ kiểm nào từng chạy file đó**. Giữ nguyên đoạn dưới để thấy rõ một bộ kiểm xanh có thể che được cái gì.
- **Cách phát hiện / kiểm chứng:** Sao lưu ba file trước khi sửa. Sau khi sửa: 8 bộ kiểm (113 phép kiểm) đều đạt; nạp thử `import chung`, `import toi_uu_dung_luong` (G = `chung`), `import goi_project_capcut`, `python -m toi_uu_dung_luong`; `xem_tien_trinh.py` nạp được và `_lp.__module__ == "chung"`.
- **Bài học (để tránh lặp lại):**
  - **Vòng tròn phụ thuộc thường không phải vấn đề kiến trúc mà là triệu chứng của một tầng chưa được tách.** Kiểm bằng cách liệt kê các tên đi qua biên giới: nếu **tất cả** đều là tiện ích một chiều thì chỉ cần một bước tách, không cần thiết kế lại.
  - **Refactor phải trích bằng máy, không chép tay.** Dùng `ast` lấy đúng đoạn nguồn giữ nguyên cả comment và khoảng trắng, loại bỏ hoàn toàn lớp lỗi "chép thiếu một dòng".
  - Khi dời code giữa các file, **bộ kiểm sẽ gãy ở những chỗ không ngờ** — và đó là dấu hiệu tốt. Bốn kiểu gãy gặp ở đây, đều đáng nhớ:
    a. Test nạp module bằng `importlib.util.spec_from_file_location` mà **không thêm thư mục tool vào `sys.path`** ⇒ `ModuleNotFoundError` cho module mới. Nạp bằng đường dẫn không tự thêm thư mục đó vào đường tìm kiếm.
    b. Test khẳng định `G.__name__ == "goi_project_capcut"` nay phải là `"chung"` — **phải cập nhật theo thực tế mới**, không phải làm cho nó xanh trở lại bằng mọi giá.
    c. Hằng số chỉ dùng nội bộ (`_O_MANG`...) **không được re-export**, vì `from chung import (...)` chỉ liệt kê những tên file đó thực sự dùng. Bộ kiểm phải hỏi đúng nguồn.
    d. Bảng dấu văn trong `tests/kiem_nhat_ky.py` trỏ sai file sau khi code dời chỗ — chính bộ kiểm nhật ký bắt được, đúng việc nó sinh ra để làm.
  - Một bản vá có thể **biến mất một cách chính đáng**: `os.path.samefile` của #48 không còn trong code vì không còn bước tra cứu nào để đánh lừa. Khi điều đó xảy ra, phải **ghi rõ vào mục cũ**, nếu không lần rà sau sẽ tưởng bản vá bị mất.


### 61. E1 gộp hai bản chép `_fmt_time()` và lấy nhầm bản CHƯA được vá — `xem_tien_trinh.py` chết ngay nhịp đầu tiên
- **Ngày:** 2026-08-18
- **Mức độ:** 🔴 Critical (một trong ba công cụ hỏng hoàn toàn ở nhánh dùng chính, mà bảng kiểm vẫn báo "TẤT CẢ ĐẠT")
- **Vị trí:** `chung.py` → `_fmt_time()`; hậu quả ở `xem_tien_trinh.py`.
- **Triệu chứng:** Sau E1, chạy `xem_tien_trinh.py`, nhập thư mục đích rồi nhập tổng GB dự kiến → chết ngay dòng hiển thị **đầu tiên**:
  ```
  File "xem_tien_trinh.py", line 76, in main
      f"{speed/1e6:5.1f} MB/s  con ~{_fmt_time(remain)}   ")
  File "chung.py", line 338, in _fmt_time
      if sec < 0 or sec != sec:
  TypeError: '<' not supported between instances of 'NoneType' and 'int'
  ```
- **Nguyên nhân gốc:** Trước E1 có **HAI bản chép** của `_fmt_time()` và **chúng đã trôi khác nhau**:
  - `xem_tien_trinh.py`: `if sec is None or sec < 0 or sec != sec:` ← **đã được vá** thêm guard `None`
  - `goi_project_capcut.py`: `if sec < 0 or sec != sec:` ← bản gốc, chưa vá
  E1 mặc định lấy bản của file "chính" và bắt file kia dùng theo. Nhưng hai chỗ gọi dùng **sentinel khác nhau** cho "chưa biết": `goi_project_capcut.py` truyền `-1`, `xem_tien_trinh.py` truyền `None`. Vòng theo dõi luôn có `speed == 0` ở lần lặp đầu (mốc đo vừa được gán), nên `remain` **luôn** là `None` ở khung hình đầu tiên ⇒ hỏng 100% số lần, không phải nhánh hiếm.
  Sâu hơn: hai bản chép đã trôi ở **HỢP ĐỒNG**, không chỉ ở code — chúng chấp nhận tập giá trị đầu vào khác nhau. Diff dòng-với-dòng vẫn thấy được, nhưng phải **thật sự đi diff** chứ đừng giả định bản của file chính là bản chuẩn.
- **Cách sửa:** Cho `_fmt_time()` trong `chung.py` là **HỢP của cả hai** bản: `if sec is None or sec < 0 or sec != sec`. Bỏ annotation `sec: float` vì `None` cũng hợp lệ. Bản truyền `-1` vẫn ra `"?"` như cũ nên phía `goi_project_capcut.py` không đổi hành vi.
- **Cách phát hiện / kiểm chứng:** Bộ kiểm mới `tests/test_xem_tien_trinh.py` (18 phép kiểm) — file này **trước đây không hề có bộ kiểm nào**. Gồm: `_fmt_time` với **cả hai sentinel** (`None` và `-1`) cùng `NaN`, chạy **thật** vòng theo dõi bằng tiến trình con ở **cả hai nhánh** (có/không nhập tổng GB), `dir_size_and_count()` trên đường dẫn > 260 ký tự, và khẳng định không còn định nghĩa `_lp`/`_fmt_time` riêng.
  **Đã chứng minh bộ kiểm có giá trị**: tạm gỡ guard `None` ra khỏi `chung.py` → bộ kiểm FAIL đúng chỗ với đúng `TypeError`; khôi phục → 18/18 PASS.
- **Bài học (để tránh lặp lại):**
  - **Khi gộp hai bản chép thành một, PHẢI diff chúng trước.** Bản nằm trong file "phụ" hoàn toàn có thể là bản **mới hơn** — nó đã được vá tại chỗ mà không ai đồng bộ ngược lại. Mặc định lấy bản của file chính là đánh cược.
  - **Hai bản chép trôi ở hợp đồng, không chỉ ở code.** Ở đây là sentinel cho "chưa biết": `-1` và `None`. Bản dùng chung phải chấp nhận **hợp** của mọi đầu vào mà các chỗ gọi đang truyền — hãy đi đọc từng chỗ gọi, đừng chỉ đọc hàm.
  - **Một file không có bộ kiểm thì mọi bảng tổng kết xanh đều là xanh GIẢ ở phần đó.** Bảng báo "TẤT CẢ ĐẠT" với 113 phép kiểm trong khi một trong ba công cụ đã chết. Trước khi tin một bảng kiểm, hãy hỏi **nó có chạm tới file nào**, chứ không phải nó có bao nhiêu phép kiểm.
  - **Refactor "thuần tuý" vẫn phải chạy thử từng cửa vào.** E1 đã kiểm `import` được cả ba module — nhưng nạp được module không chứng minh **luồng chạy** của nó còn đúng.
  - Bẫy phụ khi viết bộ kiểm: `contextlib.redirect_stdout` **không phải thread-local**. Chạy vòng lặp vô hạn trong một luồng rồi bọc `redirect_stdout` sẽ khiến stdout bị chuyển hướng **vĩnh viễn** vì luồng không bao giờ thoát khỏi context. Muốn kiểm một chương trình chạy vòng vô hạn thì dùng **tiến trình con** kèm `timeout`, và bắt `TimeoutExpired` để lấy output dở dang — hết giờ ở đây là **bình thường**, không phải lỗi.


### 62. Giai đoạn 5 — ĐO trước khi tối ưu: phần lớn "nút thắt" trong bản rà soát hoá ra không phải nút thắt
- **Ngày:** 2026-08-18
- **Mức độ:** 🟡 Medium (không phải bug; ghi lại để lần sau không đi tối ưu nhầm chỗ)
- **Vị trí:** `chung.py` → `mo_ta_moi_truong()` (mới); `toi_uu_dung_luong.py` → `probe()` + `_PROBE_CACHE`.
- **Bối cảnh:** Bản rà soát kiến trúc liệt kê 14 "vấn đề hiệu năng", trong đó có: `is_real_abs()` *"chậm gấp ~14 lần mức cần thiết"*, thư mục đích *"bị quét đệ quy ~10 lần"*, `probe()` không có cache, copy ra NAS chạy tuần tự. Thay vì tin danh sách đó, đã **đo bằng `cProfile` trên draft giả quy mô lớn** (300 material, 301 segment, 40 file cache JSON).
- **Kết quả đo — phần lớn đề nghị KHÔNG đáng làm:**
  1. **Không có gì tăng phi tuyến.** Đo ở 150 / 300 / 600 / 1200 material: **8× số material chỉ tốn 1,14× thời gian** (0,29 s → 0,33 s), chi phí mỗi material *giảm* từ 1,95 ms xuống 0,27 ms. Chi phí **cố định** mới là phần chính, không phải chi phí theo quy mô. Mọi lo ngại về `O(n·m)` đều không đúng ở dữ liệu thật.
  2. `is_real_abs()` bị gọi **5.105 lần** nhưng chỉ tốn **0,047 s / 0,46 s = 10%**, và không tăng theo quy mô. Con số "chậm 14 lần" đúng về mặt **mỗi lời gọi** nhưng vô nghĩa về mặt **tổng thời gian** — đúng như agent phản biện đã bác bỏ.
  3. Cả tầng quét JSON chỉ tốn 0,46 s cho 300 material. Trên project thật, thời gian bị chi phối bởi **ffmpeg + I/O mạng**, không phải bởi phần này.
- **Hai thứ THẬT SỰ đáng sửa (và đã sửa):**
  1. **`platform` gọi WMI ngay trên đường khởi động.** Đo: `platform.system()` mất **33,7 ms**, `platform.platform()` mất **26,8 ms** ở lần gọi đầu. Đây là chi phí **tự gây ra** khi thêm số hiệu phiên bản (mục 40-ish), và chiếm ~20% chi phí cố định. Quan trọng hơn con số: **WMI có thể chậm hoặc treo trên máy bị siết quyền**, mà treo thì không ném lỗi (cùng họ #25). Sửa: `mo_ta_moi_truong()` tính **một lần**, bọc `try/except`, có đường lui `sys.platform` **không chạm WMI**. Khởi động + thoát nay **0,145 s**.
  2. **`probe()` không có bộ nhớ đệm.** Mỗi lời gọi là **một tiến trình con + một lượt đọc file** — trên ổ mạng là một vòng SMB. Vòng áp dụng JSON gọi `probe` cho **mọi** job, mà job `dup` (sinh ra vì `main()` luôn ghi cả `draft_content.json` lẫn `draft_info.json`) trỏ vào **đúng file đích đó**. Đo được: **15 → 10 lần gọi ffprobe thật (−33%)**, thời gian 1,56 s → 1,39 s trên **ổ cục bộ**; trên ổ mạng tỉ lệ lợi ích cao hơn vì mỗi lần là một vòng mạng.
     Khoá đệm gồm **đường dẫn + kích thước + thời điểm sửa**, nên file bị ghi đè thì không dùng kết quả cũ. Có `xoa_cache_probe()` để gọi khi bắt đầu pha có thể ghi đè.
- **Cách phát hiện / kiểm chứng:** `scratchpad/do_hieu_nang.py` (cProfile + đếm số lời gọi), `scratchpad/do_ty_le.py` (đo tỉ lệ tăng ở 4 quy mô), `scratchpad/do_probe.py` (đếm số lần gọi ffprobe thật có/không cache). Sau khi sửa: 12 bộ kiểm đều đạt.
- **Bài học (để tránh lặp lại):**
  - **Danh sách "vấn đề hiệu năng" từ việc đọc code là giả thuyết, không phải kết quả.** Ở đây phần lớn mục trong danh sách hoá ra không đáng làm, và thứ đáng làm nhất (`platform` gọi WMI) **không có trong danh sách** vì nó vừa được thêm vào sau khi rà soát.
  - **Câu hỏi đầu tiên phải là "có gì tăng phi tuyến không", không phải "chỗ nào chậm".** Một hàm chậm nhưng chi phí cố định thì vô hại trên project lớn; một hàm nhanh nhưng `O(n²)` sẽ giết ta. Đo ở **nhiều quy mô** rồi so tỉ lệ là phép thử rẻ nhất và cho biết nhiều nhất.
  - **Tối ưu đúng chỗ với công cụ này nghĩa là giảm SỐ VÒNG ĐI MẠNG và SỐ TIẾN TRÌNH CON**, không phải giảm số lời gọi hàm Python. Bộ đệm `probe` đáng giá vì mỗi lần tránh được là một tiến trình con cộng một vòng SMB — chứ không phải vì nó tiết kiệm mili-giây CPU.
  - **Mọi bộ nhớ đệm phải có khoá bao gồm dấu vết thay đổi của hiện vật** (kích thước + mtime). Đệm theo mỗi đường dẫn là tự tạo ra bug "dùng số liệu của file đã bị ghi đè".


### 63. Tài liệu bàn giao là bề mặt KHÔNG ĐƯỢC KIỂM — thiếu một mục báo cáo có thể khiến người dùng bỏ qua lỗi làm hỏng gói
- **Ngày:** 2026-08-18
- **Mức độ:** 🟠 High (không làm sai code, nhưng làm người dùng kết luận sai về gói của họ)
- **Vị trí:** `BAN_GIAO.md` mục 2 (hai bảng "CÓ ảnh hưởng" / "KHÔNG ảnh hưởng"); bộ kiểm mới `tests/test_tai_lieu.py`.
- **Triệu chứng:** Bản `BAN_GIAO.md` đầu tiên liệt kê 8 mục "CÓ ảnh hưởng", trong khi biểu thức `ok` ở `goi_project_capcut.py` có **9** điều kiện chặn kết luận "ĐỦ". Mục bị bỏ sót là **`KHONG TIM THAY NGUON khi viet lai (giu nguyen path cu)`** (biến `unresolved_hard`). Ngoài ra `DON DEP - file JSON KHONG doc duoc` cũng không được nhắc.
- **Nguyên nhân gốc:** Tài liệu được viết bằng cách **đọc code rồi tóm tắt bằng tay**, mà bản tóm tắt đó không có gì đối chiếu lại với nguồn. Đây đúng là dạng lỗi đã ghi ở mục #61 — chỉ khác là lần đó bề mặt không được kiểm là một *file .py*, còn lần này là một *file .md*. Hai bảng phân loại trong tài liệu thực chất là **một bản sao chép tay của biểu thức `ok`**, nên nó lạc hậu theo đúng cách mọi bản sao chép tay đều lạc hậu.
- **Vì sao nguy hiểm hơn vẻ ngoài:** Người dùng mở `_BAO_CAO_THIEU.txt`, thấy mục `KHONG TIM THAY NGUON`, tra tài liệu **không thấy** → suy ra "chắc không quan trọng". Nhưng mục này nghĩa là có đường dẫn công cụ không tìm ra nguồn nên **giữ nguyên path cũ**: gói KHÔNG tự chứa, sang máy khác là mất phần đó. Tài liệu im lặng ở đây tệ hơn không có tài liệu, vì sự im lặng bị đọc thành lời trấn an.
- **Cách sửa:**
  1. Bổ sung hai mục thiếu, và ghi rõ bảng "CÓ ảnh hưởng" là **danh sách đầy đủ** — chỉ cần một mục trong đó có nội dung là công cụ không kết luận "ĐỦ".
  2. Viết `tests/test_tai_lieu.py`: dùng **`ast`** lấy mọi nhãn `sect(...)` và lấy **tên biến trong biểu thức `ok`**, rồi bắt buộc (a) mọi mục báo cáo phải có trong tài liệu, (b) mục chặn kết luận phải nằm ở bảng "CÓ ảnh hưởng" và **không** được nằm ở bảng kia, (c) số hiệu phiên bản, hai câu kết luận, khoá **và giá trị mặc định** của `cau_hinh.json`, danh sách file phải chép, số mục `bug.md` — đều phải khớp chuỗi thật trong code.
  3. Bảng `DOI_CHIEU` trong bộ kiểm là chỗ duy nhất khai bằng tay mối liên hệ biến → nhãn, và bộ kiểm **bắt buộc nó phủ kín biểu thức `ok`**. Thêm một điều kiện chặn mới vào code mà quên ghi tài liệu → test đỏ ngay.
- **Cách kiểm chứng:** `scratchpad/chung_minh.py` gài **3 lỗi có chủ ý** rồi khôi phục: (1) xoá mục `KHONG TIM THAY NGUON` khỏi tài liệu — bắt được; (2) xếp `TOI UU - SEGMENT BI LECH` nhầm sang bảng "không ảnh hưởng" — bắt được; (3) sửa mặc định `workers_o_mang` trong tài liệu từ 2 thành 8 — **lúc đầu KHÔNG bắt được**.
- **Lỗ hổng phép chứng minh tìm ra (quan trọng hơn lỗi gốc):** Bản đầu của bộ kiểm chỉ xác nhận **tên khoá** có xuất hiện trong tài liệu, không bao giờ so **giá trị**. Tài liệu ghi `workers_o_mang = 8` vẫn xanh — mà đó chính là con đường dẫn thẳng vào rủi ro treo SMB ở #25, vì người dùng chép đúng con số trong tài liệu. Đã thêm `gia_tri_trong_tai_lieu()` để đọc cột "Mặc định" và so với `CAU_HINH_MAC_DINH`. Sau khi vá: bắt 3/3.
- **Bài học:**
  - **Bộ kiểm đạt ngay lần chạy đầu chưa chứng minh được gì.** Phải gài lỗi vào rồi xem nó có đỏ không. Ở đây chính phép gài lỗi đã lộ ra một lỗ hổng trong bộ kiểm mà đọc lại code không thấy được.
  - **Mọi chỗ trong tài liệu chép tay một danh sách từ code đều sẽ lạc hậu.** Cách sửa không phải "nhớ cập nhật" mà là **buộc code và tài liệu đối chiếu nhau bằng máy**, lấy từ `ast` chứ không phải regex.
  - **Với tài liệu, im lặng là một phát ngôn.** Người dùng đọc "không được nhắc tới" thành "không quan trọng". Vì vậy bảng phân loại lỗi phải nói rõ nó là **danh sách đầy đủ**, và phải có bộ kiểm bảo đảm điều đó đúng.
  - Cùng họ với #61: bề mặt nào không có bộ kiểm thì mọi bảng tổng kết xanh đều là **xanh giả ở phần đó** — kể cả khi bề mặt ấy không phải mã nguồn.


### 64. `UnboundLocalError: sect` — tool chết ĐÚNG LÚC VIẾT BÁO CÁO, sau khi đã làm xong 14,8 phút công việc
- **Ngày:** 2026-08-19
- **Mức độ:** 🔴 Critical (mất hoàn toàn báo cáo và kết luận trên một lần chạy thật đã thành công)
- **Vị trí:** `goi_project_capcut.py` → `main()`, khối `with open(_BAO_CAO_THIEU.txt)`.
- **Triệu chứng:** Chạy thật project `DS3_003` (chế độ 4, đích là NAS). Mã lại xong 256 clip, dọn dẹp xong, tự kiểm xong — rồi:
  ```
  File "goi_project_capcut.py", line 1272, in main
      if opt_clean:
  UnboundLocalError: cannot access local variable 'sect' where it is not associated with a value
  ```
  Gói **nằm đầy đủ trên đĩa** (5,40 GB, nghiệm thu độc lập xác nhận clip ghép + dự án con lồng 2 tầng đều sang đủ) nhưng **không có `_BAO_CAO_THIEU.txt`**, không có câu kết luận, không biết thiếu gì.
- **Nguyên nhân gốc:** `def sect(...)` được đặt ở **giữa** thân `with`, tại dòng 1286 — trong khi khối `if opt_clean:` gọi `sect(...)` ở dòng **1277**, tức **sớm hơn 9 dòng**. Python quét cả thân hàm khi biên dịch: thấy có `def sect` ⇒ `sect` là **biến cục bộ của `main()`**; lời gọi nằm trước điểm gán nên nổ `UnboundLocalError`. Không phải lỗi cú pháp nên không có gì cảnh báo lúc nạp file.
- **Vì sao mọi bộ kiểm đều xanh mà vẫn lọt:** nhánh đó chỉ chạy khi `opt_clean` có giá trị — tức **chế độ 4 VÀ có file thật sự bị dọn**. `tests/draft_gia.py` sinh draft sạch, không có file mồ côi/`.bak`/`.tmp`, nên `opt_clean[0] == 0` và nhánh không bao giờ được vào. **13 bộ kiểm xanh, E2E xanh, mà dòng code này chưa từng chạy một lần nào.** Đúng họ với #61 (`xem_tien_trinh.py` chết 100% số lần chạy trong khi bảng tổng kết báo "TẤT CẢ ĐẠT").
- **Cách sửa:** chuyển `def sect(...)` lên **ngay đầu** khối `with`, trước mọi chỗ dùng. Kèm chú thích giải thích vì sao vị trí này là bắt buộc, để lần sau không ai đẩy nó xuống lại.
- **Cách kiểm chứng:** viết `scratchpad/quet_unbound.py` — dùng `ast` duyệt **mọi** file `.py` của project, với mỗi hàm thu thập các hàm con định nghĩa bên trong rồi tìm lời gọi có `lineno` **nhỏ hơn** dòng `def`. Sau khi sửa: **0 chỗ** trên toàn project. Rồi chạy lại chính lần chạy thật đó → báo cáo được ghi ra bình thường.
- **Bài học:**
  - **Hàm lồng phải định nghĩa trước mọi chỗ dùng, không chỉ "trước chỗ dùng chính".** Trong Python, một `def` ở cuối hàm vẫn biến tên đó thành biến cục bộ **cho toàn bộ hàm** — mọi lời gọi phía trên đều nổ.
  - **Lỗi nguy hiểm nhất là lỗi ở BƯỚC CUỐI.** Nó phá huỷ giá trị của toàn bộ công việc phía trước: 14,8 phút mã lại thành công nhưng người dùng không có cách nào biết gói đủ hay thiếu. Khi rà soát, phải soi kỹ nhất đoạn **kết thúc** chứ không phải đoạn bắt đầu.
  - **Draft giả "sạch" là draft giả YẾU.** Nó không sinh file thừa nên cả một nhánh xử lý chưa từng được chạy. Fixture phải tạo được **rác** — `.bak`, `.tmp`, media mồ côi — thì mới chạm tới nhánh dọn dẹp.
  - Một bộ quét `ast` mười mấy dòng bắt được **cả lớp lỗi** này trên toàn project trong một giây. Rẻ hơn nhiều so với đọc mắt từng hàm.

### 65. Tool tự cảnh báo về chính chú thích trong file mẫu của nó (`cau_hinh.json`)
- **Ngày:** 2026-08-19
- **Mức độ:** 🟡 Medium (không sai chức năng, nhưng dạy người dùng mới đi sửa một thứ vốn đúng)
- **Vị trí:** `goi_project_capcut.py` → `doc_cau_hinh()`.
- **Triệu chứng:** Ngay đầu mỗi lần chạy chế độ 4, tool in:
  ```
  ! cau_hinh.json co khoa khong nhan ra (bo qua): _crf, _huong_dan, _preset, _workers, _workers_o_cuc_bo, _workers_o_mang
  ```
  Các khoá `_...` đó chính là **phần chú thích tôi cố ý đặt trong `cau_hinh.json`** để người dùng không phải lập trình viên vẫn hiểu từng tuỳ chọn. Tool đang cảnh báo về chính file mẫu mà nó phát hành kèm.
- **Nguyên nhân gốc:** `doc_cau_hinh()` coi **mọi** khoá lạ là lỗi gõ nhầm. Khi thêm phần chú thích vào file mẫu (giai đoạn cấu hình) đã không cập nhật vòng kiểm tương ứng — hai thứ được sửa ở hai thời điểm khác nhau và không ai nối chúng lại.
- **Vì sao đáng sửa dù vô hại về chức năng:** công cụ này sắp phát cho **15–20 người không phải lập trình viên**. Dấu `!` ở dòng đầu tiên đọc như "bạn cấu hình sai". Người cẩn thận sẽ đi xoá phần chú thích — tức là **xoá đúng thứ được viết ra để giúp họ**. Cảnh báo sai làm hỏng giá trị của mọi cảnh báo thật phía sau.
- **Cách sửa:** bỏ qua **im lặng** khoá bắt đầu bằng `_` (quy ước "đây là chú thích"), nhưng **vẫn báo** khoá lạ thật sự — im lặng quá mức cũng là một lỗi (gõ nhầm `workrs` thì phải biết).
- **Cách kiểm chứng:** thêm phép kiểm vào `tests/test_on_dinh.py` với **cả hai chiều**: (a) khoá `_huong_dan`/`_crf` **không** được xuất hiện trong log; (b) khoá `khoa_la_that` **phải** xuất hiện; (c) giá trị thật bên cạnh chú thích vẫn đọc đúng (`crf = 19`). Phép kiểm đổi tạm `G.__file__` sang thư mục tạm thay vì ghi đè `cau_hinh.json` thật — vì lúc đó **đang có một bản chạy production đọc file đó**. Kết quả 20/20 đạt.
- **Bài học:**
  - **Cảnh báo sai đắt hơn ta tưởng.** Nó không chỉ gây nhiễu: nó dạy người dùng bỏ qua cảnh báo, và ở đây còn xui họ xoá phần tài liệu hữu ích nhất của file cấu hình.
  - **Khi thêm dữ liệu vào một file, phải xem lại vòng kiểm tra dữ liệu đó.** File mẫu và bộ kiểm khoá là một cặp; sửa một nửa là tạo mâu thuẫn.
  - **Mỗi lần nới lỏng một phép kiểm, phải viết luôn phép kiểm cho chiều ngược lại.** Nếu chỉ kiểm "không báo khoá `_`" thì một bản vá quá tay (bỏ qua mọi khoá lạ) vẫn xanh.
  - **Đừng ghi đè file thật của project trong bộ kiểm.** Một bản chạy production có thể đang đọc nó. Đổi điểm neo (`G.__file__`) rẻ hơn và an toàn hơn nhiều.


### 66. Sổ cache mã-lại bị xoá TRƯỚC khi viết báo cáo — một lỗi ở bước cuối làm mất trắng 14,8 phút mã hoá
- **Ngày:** 2026-08-19
- **Mức độ:** 🟠 High (không mất dữ liệu, nhưng mất toàn bộ đường phục hồi đúng lúc cần nó nhất)
- **Vị trí:** `goi_project_capcut.py` → `main()`, khối bỏ `_opt_index.json` (trước ở dòng ~1199, nay chuyển xuống sau khi tính `ok`).
- **Triệu chứng:** Sau khi [[#64]] (`UnboundLocalError: sect`) làm tool chết ở bước viết báo cáo, chạy lại tưởng sẽ nhanh vì 256 clip đã mã xong. Thực tế nó **mã lại từ đầu**. Xem log lần chết thấy dòng `Da bo so cache tam (_opt_index.json).` được in **trước** khi crash.
- **Nguyên nhân gốc:** Thứ tự trong `main()` là:
  1. tự kiểm phần tối ưu → đạt
  2. **xoá `_opt_index.json`** ("đã xong rồi, bỏ file rác cho gọn")
  3. tự kiểm trên bản xuất
  4. **viết `_BAO_CAO_THIEU.txt`** ← chỗ #64 nổ

  Bước 2 tuyên bố "đã xong" trong khi còn hai bước nữa mới thật sự xong. Bản thân ý tưởng "xong thì bỏ cache" đúng; sai ở chỗ **định nghĩa "xong" quá sớm**. Đây đúng là điều `CLAUDE.md` đã ghi — *"chỉ số xong/thiếu đo trên KẾT QUẢ THỰC TẾ ở đích, không trên trạng thái trung gian"* — chỉ là trước nay chỉ áp cho việc đếm file, chưa ai nghĩ tới việc **dọn cache**.
- **Vì sao đắt hơn vẻ ngoài:** cache mã-lại (#29, #32) tồn tại **chính xác cho tình huống chạy dở rồi chết**. Xoá nó ngay trước bước dễ chết nhất là vô hiệu hoá tính năng phục hồi đúng vào lúc duy nhất nó có ích. Trên project này là 14,8 phút; trên project 355 GB đã ghi ở #32 thì là hàng giờ.
- **Cách sửa:**
  1. Không xoá tại chỗ nữa, chỉ đặt cờ `bo_cache_sau = True`.
  2. Khai báo `bo_cache_sau = False` ở **tầng ngoài cùng** của `main()` cạnh `opt_stat` — nếu khai trong `if opt_stat:` thì chế độ 1 sẽ nổ `NameError`, tức tái phạm đúng lớp lỗi #64 khi đang đi sửa nó.
  3. Thực hiện xoá **sau khi** tính xong `ok`, và **chỉ khi `ok`**. Còn lỗi thì **giữ** cache và in `GIU LAI so cache tam: con loi -> lan chay sau khoi ma lai tu dau.` — trước đây chạy lại sau thất bại vẫn phải mã lại từ đầu, giờ thì không.
- **Cách kiểm chứng:** `scratchpad/quet_unbound.py` → 0 chỗ dùng-trước-định-nghĩa; `python tests\chay_het.py` → 14/14 bộ đạt.
- **Bài học:**
  - **Dọn dẹp phải là việc CUỐI CÙNG, sau khi đã có bằng chứng thành công trên đĩa.** Bất cứ thứ gì bị xoá trước bước cuối đều là thứ ta sẽ cần nếu bước cuối hỏng.
  - **Một lỗi ở bước cuối phá huỷ giá trị của mọi bước trước.** #64 và mục này là **cùng một sự cố** nhìn từ hai phía: một cái mất báo cáo, một cái mất đường phục hồi. Khi rà soát, đoạn kết thúc đáng soi kỹ hơn đoạn mở đầu.
  - **Nguyên tắc "đo trên kết quả thực tế" áp cho cả HÀNH ĐỘNG, không chỉ CON SỐ.** "Xong nên bỏ cache" là một phép đo trạng thái trá hình — và nó sai ở đúng chỗ mà phép đếm file từng sai.
  - Khi thêm một biến cờ để hoãn hành động, **kiểm ngay tầng khai báo của nó**. Suýt tạo `NameError` cho chế độ 1 trong lúc đang sửa hậu quả của một `UnboundLocalError`.


### 67. File BIẾN MẤT khỏi gói: bỏ qua copy vì "sẽ được thay", rồi không được thay
- **Ngày:** 2026-08-19
- **Mức độ:** 🔴 Critical (máy cha mở vẫn đủ, MÁY CON MẤT HÌNH — đúng loại lỗi công cụ này sinh ra để chống)
- **Vị trí:** `goi_project_capcut.py` → `main()` (dùng `skip_media` cho `copytree`) + `toi_uu_dung_luong.py` → `plan_replacements()`, `make_copy_ignore()`, nhánh `no_gain` (~dòng 800). Bản vá: hàm mới `cuu_ban_goc_bi_bo_qua()`.
- **Triệu chứng:** Chạy thật `DS3_003` chế độ 4. Báo cáo ghi `Tu kiem: 22 tham chieu HONG`. Truy ra `A_hyperrealistic_octopus_202601211738_87kyy.mp4` (7,02 MB): **có** trong nguồn tại `subdraft/74EB31FA-.../materials/video/`, **không có** trong gói, bị **6 file JSON** trỏ tới trong đó có `draft_content.json` — timeline chính.
- **Nguyên nhân gốc — một DỰ ĐOÁN không bao giờ được đối chiếu với KẾT QUẢ:**
  1. `plan_replacements()` lập trước danh sách `skip_media` = "các file nằm trong thư mục draft chắc chắn sẽ được thay bằng bản nén".
  2. `make_copy_ignore(skip_media)` khiến `shutil.copytree` **không chép** chúng vào gói (log: `76 file NAM TRONG folder draft se duoc thay -> khoi copytree (~6.28 GB)`). Tối ưu hợp lý: khỏi tốn đường truyền cho file sắp bị ghi đè.
  3. Nhưng khi mã lại, có **ba nhánh** kết luận *"giữ bản gốc"*: `no_gain` (kết quả không nhỏ hơn 8% → xoá bản mã), mã lại thất bại, và material bị loại (`bo_qua`).
  4. Cả ba đều giả định **bản gốc đang nằm trong gói**. Với file nằm trong thư mục draft thì giả định đó **sai**, vì bước 2 đã cố tình bỏ qua nó.

  Log xác nhận: `khong loi nen giu goc 2` — đúng nhánh `no_gain`.
- **Vì sao gần như không thể tự phát hiện:** trên máy cha, mở gói bằng CapCut vẫn thấy đủ, vì đường dẫn cũ `D:\1363\...` còn nguyên trên ổ nên CapCut tự tìm thấy. Chỉ máy con mới lộ. Đây chính là lý do `BAN_GIAO.md` bắt buộc "phép thử vàng": **di chuyển gói rồi mới mở**.
- **Cách sửa — nghiệm thu DỰ ĐOÁN bằng KẾT QUẢ THẬT, không vá từng nhánh:**
  Thêm `cuu_ban_goc_bi_bo_qua(out_dir, draft_dir, skip_media, opt_stat)` chạy **ngay sau** `optimize_package()`. Với mỗi file trong `skip_media`: nếu **không** có trong `opt_stat["opt_by_src"]` (tức không thực sự được thay) **và** không có mặt ở đích → **chép bù ngay**. Cứu thất bại thì đẩy vào `st["fail"]` để ra báo cáo.
  Chọn cách này thay vì sửa riêng nhánh `no_gain` vì nó bắt **mọi** nguyên nhân làm dự đoán sai — kể cả nguyên nhân chưa nghĩ ra. Thêm mục báo cáo `DA CUU ban goc bi bo qua nham` để sự cố không diễn ra im lặng.
- **Cách kiểm chứng:**
  - `tests/test_cuu_ban_goc.py` (12 phép kiểm): cứu đúng file chưa được thay; **không** cứu file đã có bản `_opt` thật (nếu không gói phình + sinh "bản gốc thừa" của #38); giữ đúng cây thư mục khi file lồng trong `subdraft/`; chạy lại không chép lại; cứu thất bại **phải** báo ra và vào `opt_stat["fail"]`; và bốn phép kiểm chống code chết (đã nối vào `main()`, truyền đúng `skip_media`, có ra báo cáo, biến khai ở tầng ngoài).
  - **Đo trên project thật, trước/sau:** tham chiếu hỏng `22 → 18` (giảm đúng 4 = số file JSON trỏ tới nó); file media trong gói `868 → 869`; script đối chiếu nguồn↔gói: **1 nạn nhân → 0**.
- **Bài học:**
  - **Mọi tối ưu dựa trên DỰ ĐOÁN đều phải có bước đối chiếu với KẾT QUẢ THẬT.** "Khỏi chép vì sắp bị thay" là đúng khi việc thay xảy ra; sai lầm là không ai kiểm lại xem nó có xảy ra thật không. Đây là `CLAUDE.md` — *"đo trên KẾT QUẢ THỰC TẾ ở đích, không trên trạng thái trung gian"* — áp cho **quyết định bỏ qua công việc**, không chỉ cho phép đếm.
  - **Câu "giữ bản gốc" chỉ đúng nếu bản gốc CÓ THẬT ở đó.** Ba nhánh cùng viết câu đó, không nhánh nào kiểm. Khi code nói "giữ X", phải hỏi: X đang ở đâu, ai bảo đảm nó còn đó?
  - **Lỗi nguy hiểm nhất của công cụ này là lỗi mà máy cha KHÔNG thể thấy.** Mọi phép kiểm chạy trên máy gói đều mù trước lớp lỗi này. Phải nghiệm thu bằng cách **đối chiếu nguồn với gói**, hoặc di chuyển gói đi rồi mới mở.
  - **Một phép đếm đơn giản bắt được cả lớp lỗi:** "file nào có trong nguồn, không có trong gói, và không có bản `_opt`?". Rẻ, chạy vài giây, và nó tìm ra thứ mà 15 bộ kiểm đều bỏ sót.


### 68. Đọc đầu ra ffmpeg bằng BẢNG MÃ CỦA MÁY — máy phát triển (ACP 65001) mù hoàn toàn, máy con (ACP 1258) hỏng
- **Ngày:** 2026-08-19
- **Mức độ:** 🔴 Critical (máy con làm khác máy cha 100% ở chế độ 4; không có cách nào phát hiện từ máy phát triển)
- **Vị trí:** `toi_uu_dung_luong.py` → `_run()`; `tests/draft_gia.py` → `_chay()`; và 4 chỗ gọi `subprocess.run` trong `tests/`.
- **Triệu chứng (suy ra, chưa gặp thật vì máy phát triển không thể gặp):** trên máy con, chế độ 4 bỏ clip hàng loạt hoặc báo "không đọc được kết quả sau khi mã", và người dùng kết luận nhầm là footage của họ hỏng.
- **Nguyên nhân gốc:** `subprocess.run(..., text=True)` **không kèm `encoding=`** giải mã đầu ra bằng `locale.getpreferredencoding()`, tức **bảng mã ANSI của máy**. ffmpeg/ffprobe trên Windows **luôn xuất UTF-8**.
  - Máy phát triển: `GetACP() = 65001` (UTF-8) → trùng nhau → **không bao giờ lộ lỗi**.
  - Máy con Windows tiếng Việt mặc định: `ACP 1258` (hoặc 1252) → giải mã sai → `json.loads` thất bại.
  - `chcp 65001` trong `.bat` **không sửa được**: nó đổi *console* code page, không đổi *ANSI* code page của tiến trình.
- **Đường lan hậu quả:** `_probe_that()` bọc `json.loads` trong `except Exception: return None` — **nuốt trọn**. `probe()` trả `None` → tool hiểu là "không đo được video" → bỏ clip, **im lặng**. Không một dòng nào trong báo cáo cho biết đã có chuyện gì.
- **Cách sửa:**
  1. `_run()`: bỏ `text=True`, dùng **`encoding="utf-8", errors="replace"`**. `errors="replace"` để vài byte lạ không giết cả lần chạy.
  2. `_probe_that()`: phân biệt **`stdout` rỗng** với JSON hợp lệ (`json.loads("{}")` cho ra "video 0x0 dài 0 giây" — một phép đo GIẢ), và ghi vết ở **cả ba** nhánh thất bại (`returncode != 0`, rỗng, ngoại lệ) qua `_ghi_loi_probe()`. Danh sách này vào `st["fail"]` → ra báo cáo.
  3. `mo_ta_moi_truong()`: nối `| ACP <n>` vào chuỗi môi trường ở đầu `_BAO_CAO_THIEU.txt`. Khi 15-20 người gửi báo cáo về, đây là con số cho biết ngay họ có cùng thế giới với máy phát triển không.
  4. Sửa cùng lỗi ở `tests/draft_gia.py` và 4 file test — nếu bỏ sót, chính bộ kiểm sẽ hỏng trên máy con, tức mù đúng chỗ cần soi nhất.
- **Cách kiểm chứng — `tests/test_bang_ma.py` (7 phép kiểm), hai tầng:**
  - **Hành vi:** đo một clip nằm trong thư mục tên `Dự án Đèn lồng ờ ề`. Rồi **mô phỏng máy con** bằng cách thay `_run` thành bản đọc `cp1258/errors=strict` → `probe` **KHÔNG đo được**; bản thật (`encoding=utf-8`) **luôn đo được**. Đây là bằng chứng trực tiếp bản vá có tác dụng.
  - **Chốt tĩnh:** quét AST **mọi** file `.py`, bắt mọi `run/Popen/check_output` đọc dạng text mà thiếu `encoding=`. Lúc mới viết nó bắt đúng 4 chỗ còn sót trong `tests/`. Kèm phép tự kiểm: chốt tĩnh phải **bắt được** code lỗi cố ý và **không báo nhầm** code đúng.
- **Bài học:**
  - **Máy phát triển có ACP 65001 là một cái bẫy.** Nó làm cả một lớp lỗi trở nên vô hình. Với công cụ phát cho người khác, phải luôn hỏi: *"cấu hình nào của máy tôi đang che mắt tôi?"* — và viết chốt tĩnh cho những thứ đó, vì phép thử hành vi trên máy này sẽ luôn xanh.
  - **`text=True` không kèm `encoding=` là lỗi, không phải mặc định hợp lý.** Với tiến trình con xuất UTF-8 (mọi công cụ hiện đại), phải ghi rõ `encoding="utf-8"`.
  - **`json.loads("{}")` trả về phép đo GIẢ chứ không phải lỗi.** Mọi giá trị mặc định kiểu `or "{}"` / `or 0` đều có nguy cơ biến "không biết" thành "biết một con số sai".
  - **Đưa cấu hình môi trường vào báo cáo.** Một dòng `ACP 65001` tiết kiệm được nhiều ngày truy lỗi khi báo cáo từ máy lạ gửi về.

### 69. Ba chỗ còn lại nuốt lỗi đọc JSON im lặng — bản vá A2 chỉ được áp cho MỘT hàm rồi dừng
- **Ngày:** 2026-08-19
- **Mức độ:** 🟠 High (gói hỏng ở máy con mà báo cáo vẫn nói "ĐỦ")
- **Vị trí:** `toi_uu_dung_luong.py` → `repoint_registry()`, `prune_registry()`, `kiem_ban_goc_thua()`.
- **Triệu chứng:** `cleanup_unused()` đã được vá (mục A2): file JSON không đọc được thì **đếm** và **cấm xoá file mồ côi**. Nhưng ba hàm ngay cạnh gặp đúng tình huống đó lại `except Exception: continue` — **không một lời**. Một chỗ còn có chú thích `# doc loi -> khong ket luan gi`, tức người viết **biết** mình đang bỏ qua.
- **Nguyên nhân gốc:** bản vá A2 được áp cho đúng hàm gây ra sự cố lúc đó rồi dừng, không ai rà các hàm cùng loại. "Không kết luận gì" bị hiểu thành "không nói gì với ai".
- **Hậu quả từng chỗ:**
  - `repoint_registry()` — **nặng nhất**: file đó không được viết lại nên đường dẫn trong nó **vẫn trỏ vào bản gốc**. Máy cha mở vẫn đủ (file gốc còn trên ổ); **máy con mất đúng phần đó**, mà kết luận vẫn là "ĐỦ".
  - `prune_registry()`: mục chết còn trong sổ đăng ký → kho media ở máy con đầy file thiếu.
  - `kiem_ban_goc_thua()`: con số "bản gốc thừa" được tính **trên dữ liệu thiếu** nên có thể báo thừa nhầm.
- **Cách sửa:** cả ba đều `log` rõ **kèm hậu quả cụ thể** ("máy khác sẽ hỏng" / "kho media còn mục chết" / "con số bên dưới có thể SAI"). `repoint_registry()` đổi trả về `(n, loi_doc)` và `optimize_package()` nối `loi_doc` vào `st["fail"]` — dùng **đường báo cáo có sẵn** thay vì tạo cơ chế mới.
- **Cách kiểm chứng:** `scratchpad/chung_minh_nuotloi.py` — dựng gói giả có `draft_content.json` và `draft_meta_info.json` hỏng, gọi từng hàm, khẳng định có log **và** log nêu đúng hậu quả: 8/8 đạt.
- **Bài học:**
  - **Vá một bug thì phải grep cả lớp lỗi đó.** A2 sửa một hàm; ba hàm cùng file, cùng khuôn mẫu, vẫn sống thêm nhiều tháng. Sau mỗi bản vá nên hỏi: *"khuôn mẫu này còn ở đâu nữa?"*
  - **Chú thích thú nhận là dấu hiệu đỏ.** `# doc loi -> khong ket luan gi` cho thấy người viết đã thấy vấn đề và tự thuyết phục mình bỏ qua. Những chú thích như thế đáng nghi hơn code không chú thích.
  - **Thông báo lỗi phải nêu HẬU QUẢ, không chỉ sự kiện.** "Không đọc được X" không giúp ai quyết định gì; "không đọc được X → máy khác sẽ mất phần đó" thì có.


### 70. `os.walk` không có `onerror=` — NAS rớt phiên giữa chừng thì `cleanup_unused` XOÁ THẬT media rồi báo "ĐỦ"
- **Ngày:** 2026-08-19
- **Mức độ:** 🔴 Critical (mất dữ liệu trong gói bàn giao, im lặng hoàn toàn)
- **Vị trí:** `chung.py` → `iter_json_files()` (10 chỗ gọi trên toàn project); `toi_uu_dung_luong.py` → `cleanup_unused()`; các chỗ gọi trong `main()`.
- **Triệu chứng (chưa gặp thật — tìm ra khi rà soát; nhưng NAS ở đây **đã** hay trả `WinError 71` khi tải nặng):** một nhánh thư mục không liệt kê được giữa chừng ⇒ media bị xoá như "mồ côi", báo cáo vẫn kết luận "ĐỦ".
- **Nguyên nhân gốc — hai lớp cùng hỏng:**
  1. `os.walk(_lp(root))` **không có `onerror=`**. Mặc định của `os.walk` là **nuốt im lặng** mọi lỗi liệt kê thư mục: cả một nhánh cây bị bỏ qua mà không ai biết.
  2. Chốt an toàn của mục #44 — `duoc_xoa_mo_coi = not loi_doc` — **vô hiệu trước lớp lỗi này**, vì `loi_doc` chỉ ghi các file *đọc* lỗi. Những JSON trong nhánh không duyệt được **chưa hề được liệt kê**, nên chúng không "đọc lỗi"; `loi_doc` vẫn rỗng.

  Chuỗi đầy đủ: nhánh không duyệt được → JSON trong đó không được đọc → media chúng tham chiếu **không có** trong `refd` → bị coi là mồ côi → **xoá thật** → báo cáo nói "ĐỦ".
- **Cách sửa:**
  1. `iter_json_files(root, loi=None)`: thu lỗi qua `onerror=`. `loi=None` (mặc định) → **NÉM `OSError`**; truyền list vào → ghi lỗi rồi chạy tiếp. **Đảo chiều mặc định** là điểm mấu chốt: để mặc định im lặng thì 9 chỗ gọi hiện tại vẫn mù và chỗ gọi thứ 10 lại quên.
  2. `cleanup_unused()` là chỗ **duy nhất** truyền list vào (nó cần chạy tiếp để dọn `*.bak/*.tmp` — an toàn trong mọi trường hợp), và gộp lỗi duyệt vào `loi_doc` để chốt an toàn nhìn thấy.
  3. Siết chốt an toàn thành **bằng chứng dương**: `duoc_xoa_mo_coi = bool(refd) and not loi_doc`. `not loi_doc` chỉ là "vắng mặt lỗi" — quá yếu, và chính bug này lọt qua vì `loi_doc` rỗng. Xoá media dựa trên `refd` **rỗng** là vô nghĩa về mặt số học.
  4. Bọc các chỗ gọi trong `main()`: `collect_refs` / `plan_package` / `optimize_package` → dừng với thông báo tiếng Việt rõ ràng (không traceback thô cho người dùng không phải lập trình viên); `prune_registry` / `cleanup_unused` → vào `verify_loi` ⇒ kết luận thành "CHƯA KẾT LUẬN ĐƯỢC". Bốn hàm tự kiểm đã có sẵn `try/except → verify_loi` từ trước.
- **Cách kiểm chứng — `tests/test_quet_thieu.py` (14 phép kiểm):** vá **`os.scandir`** (thứ `os.walk` thật sự gọi) để ném `OSError(71, "No more connections can be made to this remote computer")` cho đúng một nhánh — **không** stub `iter_json_files`, nhờ vậy phép kiểm vẫn đúng kể cả khi ai đó viết lại hàm đó. Ba nhóm: (a) quét thiếu → ném, thông báo nêu hậu quả, và có khẳng định `scandir` giả **thật sự** được gọi (chống phép thử rỗng như #17); (b) `cleanup_unused` gặp nhánh hỏng → **media vẫn còn**; (c) `refd` rỗng → không xoá sạch `materials/`.
  `scratchpad/chung_minh_quet.py` gỡ `onerror=` ra → bộ kiểm **đỏ**; khôi phục → xanh.
- **Bài học:**
  - **`os.walk` không `onerror=` là một lỗi im lặng có sẵn trong thư viện chuẩn.** Nó không ném, không log, chỉ trả về ít hơn. Mọi vòng `os.walk` trên đường đi tới một quyết định **xoá** đều phải có `onerror=`.
  - **Mặc định phải là NÉM, không phải im lặng.** Khi một hàm tiện ích có thể trả kết quả thiếu, để mặc định "im lặng, ai cần thì tự hỏi" nghĩa là mọi chỗ gọi cũ đều sai và chỗ gọi mới sẽ sai tiếp. Đảo mặc định sửa được cả 10 chỗ trong một lần.
  - **Chốt an toàn phải dựa trên BẰNG CHỨNG DƯƠNG, không dựa trên "không thấy lỗi".** `not loi_doc` nghe như an toàn nhưng chỉ chứng minh được "không có lỗi *thuộc loại ta đang đếm*". `bool(refd)` mới là bằng chứng ta thật sự đã đọc được thứ gì đó.
  - **Một chốt an toàn đã có (#44) không có nghĩa là hạng mục đó đã an toàn.** Chốt cũ chặn đúng một đường; lớp lỗi này đi vòng qua nó. Khi rà soát, phải hỏi: *"chốt này giả định điều gì, và điều đó có thể sai theo cách nào?"*


### 71. Ba `os.walk` còn lại làm PHÉP ĐẾM nói dối — "0 đường dẫn dài", "không có bản gốc thừa", "đã bỏ N file"
- **Ngày:** 2026-08-19
- **Mức độ:** 🟡 Medium (không mất dữ liệu, nhưng làm mất giá trị của chính các phép nghiệm thu)
- **Vị trí:** `goi_project_capcut.py` → `scan_long_paths()`; `toi_uu_dung_luong.py` → `kiem_ban_goc_thua()` và vòng xoá của `cleanup_unused()`. (`xem_tien_trinh.py` → `dir_size_and_count()` **cố ý** giữ nguyên.)
- **Bối cảnh:** mục trước vá `iter_json_files()` — đường nguy hiểm nhất. Nhưng `grep "os.walk("` cho thấy còn **4 chỗ** nữa không có `onerror=`. Đây đúng là bài học của mục về bản vá A2: *vá một bug thì phải grep cả lớp lỗi đó*.
- **Phân loại theo HƯỚNG hỏng (không vá bừa cả bốn):**
  1. `scan_long_paths()` — bỏ sót nhánh ⇒ báo **"0 đường dẫn quá dài"**. Cảnh báo biến mất đúng lúc cần nó nhất (gói đặt sâu trên NAS chính là lúc dễ vượt 260 ký tự). → **NÉM**, `main()` đã bọc sẵn nên thành `verify_loi`.
  2. `kiem_ban_goc_thua()` — bỏ sót ⇒ báo **"không có bản gốc thừa"**. Đây là một **phép nghiệm thu** (sinh ra từ #38); phép nghiệm thu nói dối còn tệ hơn không có phép nào. → **NÉM**.
  3. Vòng **xoá** của `cleanup_unused()` — bỏ sót ⇒ **xoá ít hơn**, tức hỏng theo hướng **an toàn** (không thể xoá thứ không nhìn thấy). Nhưng con số `Da bo N file` sẽ SAI. → **KHÔNG ném** (đừng biến một tình huống an toàn thành lỗi chặn), mà đẩy vào `fails` để ra báo cáo, và nối thêm `(! con so nay THIEU: co thu muc khong duyet duoc)` vào dòng log.
  4. `dir_size_and_count()` của `xem_tien_trinh.py` — **cố ý giữ im lặng**: đây là cửa sổ theo dõi, chỉ đọc, không quyết định gì. Một con số hơi lệch không hại ai, còn dừng lại giữa chừng thì mất luôn công cụ theo dõi. Đã **viết chú thích giải thích** để lần rà sau không nhầm là sót.
- **Cách kiểm chứng:** mở rộng `tests/test_quet_thieu.py` lên **21 phép kiểm**, dùng lại `ScandirHong` (vá `os.scandir`, không stub hàm). Mỗi ca đều khẳng định `scandir` giả **thật sự được gọi** — chống phép thử rỗng như #17.
- **Bài học:**
  - **Không phải mọi chỗ nuốt lỗi đều đáng vá như nhau — phải phân loại theo HƯỚNG hỏng.** Bỏ sót khi *đếm để cảnh báo* thì nguy hiểm (mất cảnh báo); bỏ sót khi *đếm để xoá* thì an toàn (xoá ít hơn). Vá đồng loạt bằng "ném hết" sẽ biến một tình huống vô hại thành lỗi chặn giữa chừng.
  - **Chỗ cố ý im lặng phải được VIẾT RA LÀ CỐ Ý.** Nếu không, mỗi lần rà soát sau lại tốn công tranh luận, hoặc tệ hơn: có người "sửa" nó và làm hỏng cửa sổ theo dõi.
  - **Một phép nghiệm thu nói dối tệ hơn không có phép nghiệm thu**, vì nó tạo ra niềm tin sai. Mọi hàm có tên bắt đầu bằng `kiem_`/`verify_`/`scan_` đều phải ném khi không thu thập đủ dữ liệu.


### 72. `ff_paths()` chỉ kiểm FILE CÓ TỒN TẠI — máy con có ffmpeg hỏng sẽ chờ 15-30 phút rồi nhận hàng trăm lỗi
- **Ngày:** 2026-08-19
- **Mức độ:** 🟠 High (không mất dữ liệu, nhưng làm người dùng kết luận SAI là footage của họ hỏng)
- **Vị trí:** `toi_uu_dung_luong.py` → `kiem_ffmpeg_chay_duoc()` (mới); `goi_project_capcut.py` → `main()`, chỗ chọn chế độ 4.
- **Triệu chứng (suy ra cho máy con — máy phát triển không thể gặp):** người dùng chọn chế độ 4, tool báo `Da bat TOI UU DUNG LUONG`, chạy 15-30 phút, rồi báo hàng trăm `clip ma lai THAT BAI`. Người dùng không phải lập trình viên sẽ kết luận **footage của mình hỏng**.
- **Nguyên nhân gốc:** `ff_paths()` chỉ kiểm `isfile_safe(ffmpeg)` và `isfile_safe(ffprobe)`. **Có file ≠ chạy được.** Trên máy con, `ffmpeg.exe` có thể nằm đầy đủ đó mà vẫn vô dụng:
  - thiếu DLL (bản build khác, hoặc chép thiếu nội dung `bin/`)
  - bản **LGPL tối giản không có encoder `libx264`** → mọi clip mã lại đều hỏng
  - bị Windows Defender / chính sách máy chặn
  `kiem_tien_de()` (G1) đã kiểm phiên bản Python, file thiếu, quyền ghi — nhưng **bỏ sót đúng thứ phụ thuộc bên ngoài duy nhất** của tool.
- **Cách sửa:** `kiem_ffmpeg_chay_duoc(ffmpeg, ffprobe)` chạy **ngay lúc chọn chế độ 4**, tốn chưa tới một giây: (1) `ffmpeg -version` và `ffprobe -version` phải trả mã 0; (2) `ffmpeg -encoders` phải có **`libx264`**. Thất bại thì in lý do **kèm cách sửa** ("hãy dùng bản ffmpeg đầy đủ, vd gyan.dev essentials/full") và **hạ xuống chế độ 1** (`ffmpeg = ffprobe = None`) thay vì lao vào pha mã lại với công cụ hỏng.
- **Cách kiểm chứng:** `tests/test_ffmpeg_hong.py` (12 phép kiểm) giả `TU._run` để dựng đúng ba kiểu hỏng của máy con: ném `OSError(126)` (thiếu DLL), trả mã khác 0, và **chạy tốt nhưng danh sách encoder không có `libx264`** (bản LGPL). Kèm phép kiểm đường thuận (ffmpeg đi kèm phải qua), phép kiểm thông báo **có chỉ cách sửa**, và hai phép kiểm chống code chết (đã nối vào `main()`, và thất bại thì thật sự hạ về chế độ 1).
- **Bài học:**
  - **"File có tồn tại" là phép kiểm yếu nhất có thể viết cho một phụ thuộc bên ngoài.** Thứ đáng kiểm là **nó có làm được việc ta cần không** — ở đây là mã H.264. Một `-encoders | grep libx264` rẻ hơn 30 phút chạy hỏng.
  - **Kiểm sớm hay muộn quyết định người dùng đổ lỗi cho ai.** Cùng một lỗi: báo lúc khởi động thì họ biết "ffmpeg của tôi thiếu"; báo sau 30 phút thì họ kết luận "footage của tôi hỏng". Vị trí của phép kiểm là một quyết định về **chẩn đoán**, không chỉ về hiệu năng.
  - **Thông báo lỗi cho người không phải lập trình viên phải kèm CÁCH SỬA.** "Thiếu libx264" là vô nghĩa với họ; "hãy dùng bản ffmpeg đầy đủ (gyan.dev essentials)" thì làm được.
  - `kiem_tien_de()` đã kiểm Python, file, quyền — nhưng bỏ sót **phụ thuộc bên ngoài duy nhất**. Khi viết một hàm "kiểm tiền đề", hãy liệt kê **mọi thứ nằm ngoài tầm kiểm soát của code** rồi mới viết.


### 73. `.bat` — điểm vào của máy con chỉ có một dòng `python ...`, và bản "làm cứng" đầu tiên còn tệ hơn bản gốc
- **Ngày:** 2026-08-19
- **Mức độ:** 🟠 High (máy con không chạy được tool, người dùng không phải lập trình viên sẽ bỏ cuộc ngay bước đầu)
- **Vị trí:** `goi_project_capcut.bat`, `xem_tien_trinh.bat`; bộ kiểm mới `tests/test_bat.py`.
- **Triệu chứng ban đầu:** cả hai `.bat` chỉ có `python <ten>.py`. Trên máy con:
  - chưa cài Python → `'python' is not recognized as an internal or external command` rồi cửa sổ đóng. Không một chữ nào nói phải làm gì.
  - cài rồi nhưng **quên tích "Add python.exe to PATH"** (rất phổ biến) → y hệt như trên, dù máy **có** Python.
  - chép thiếu file `.py` → traceback Python khó hiểu.
  Ngoài ra cả hai file dùng **xuống dòng LF** (dạng Unix), không phải CRLF.
- **Bản sửa đầu tiên của tôi CÓ LỖI — và lỗi đó tệ hơn bản gốc:** tôi thêm chốt chặn lọc bản giả lập Microsoft Store:
  ```bat
  where python 2>nul | find /i "WindowsApps" >nul
  if not errorlevel 1 goto :thieu_python
  ```
  Sai **hai đường độc lập**:
  1. **Logic sai:** `where python` liệt kê **mọi** kết quả. Trên máy này nó trả về *cả* `C:\Python314\python.exe` *lẫn* bản giả lập trong `WindowsApps`. Lọc theo chuỗi sẽ kết luận "không có Python" trên máy **đang cài Python** → tool không bao giờ chạy được.
  2. **Phụ thuộc lệnh ngoài có thể bị che:** máy này có Git Bash nên `find` trỏ vào `find` của Unix, không phải `find.exe` của Windows. Lệnh lỗi (`find: '/i': No such file or directory`), errorlevel khác 0, chốt chặn **im lặng không chạy**. Nó "hoạt động" vì một lý do hoàn toàn sai — và sẽ hỏng ngay trên máy con không có Git Bash.
- **Cách sửa:** bỏ hẳn chốt chặn `where`/`find`. Thứ tự tìm Python:
  1. `py -3` — launcher của python.org, nằm ở `C:\Windows` nên **chạy được ngay cả khi quên tích Add to PATH**, và không bao giờ trúng bản giả lập Store.
  2. `python` — chỉ khi (1) thất bại.
  Cả hai dùng **phép thử phiên bản** `raise SystemExit(0 if sys.version_info>=(3,8) else 1)`. Bản giả lập Store không chạy được Python nên **tự nó trượt** — không cần lọc chuỗi. Thất bại thì in hướng dẫn cụ thể: địa chỉ python.org, nhắc **tích ô "Add python.exe to PATH"**, và giải thích nếu Windows mở Microsoft Store thì đó là bản giả lập. Thêm kiểm file `.py` có tồn tại không. Viết lại bằng **ASCII thuần + CRLF**.
- **Cách kiểm chứng:** `tests/test_bat.py` (18 phép kiểm) **chạy thật** `.bat` qua `cmd.exe`:
  - máy bình thường → tool khởi động, in số hiệu phiên bản, không traceback
  - **PATH chỉ còn `system32`** → cả `py` lẫn `python` đều không thấy → phải in hướng dẫn đầy đủ, và **không** chạy tiếp
  - chép mỗi `.bat` sang thư mục trống → báo rõ "thiếu file", "chép CẢ THƯ MỤC", không traceback
  - định dạng: ASCII thuần, CRLF, `chcp` nằm đầu
- **Hai sai lầm trong chính bộ kiểm (đáng ghi vì rất dễ lặp):**
  1. Ban đầu tôi cắt `PATH` về `system32;C:\Windows` để giả lập "không có Python". **Vô tác dụng** — `py.exe` nằm ngay trong `C:\Windows`. Phép thử báo xanh trong khi chưa hề thử điều nó nói.
  2. Sau đó tôi đặt shim `py.cmd`/`python.cmd` lên đầu PATH. Cũng sai: gọi một `.cmd` từ `.bat` **không có `call`** sẽ **chuyển hẳn quyền điều khiển và kết thúc `.bat` cha**. Kết quả: `.bat` không in gì, và phép kiểm hiểu nhầm thành "nó im lặng". Cách đúng: `PATH` chỉ còn `system32`, **không** có `C:\Windows`.
- **Bài học:**
  - **Đừng để một lệnh ngoài quyết định luồng chạy nếu nó có thể bị che.** `find`, `where`, `sort`, `more` đều có bản Unix trùng tên do Git Bash / WSL / MSYS cài. Trong `.bat`, thứ chắc chắn nhất là **chạy thử rồi xem mã thoát**, không phải phân tích chuỗi.
  - **`py -3` là cách tìm Python bền nhất trên Windows**, vì nó sống ở `C:\Windows` — miễn nhiễm với việc người dùng quên tích "Add to PATH", đúng lỗi phổ biến nhất khi phát cho người không rành máy.
  - **Bản vá "làm cứng" cũng phải bị nghi ngờ như code gốc.** Bản sửa đầu của tôi đổi một lỗi *rõ ràng* (`'python' is not recognized`) thành một lỗi *âm thầm và sai* ("máy này chưa có Python" trong khi có). Rõ ràng còn hơn im lặng-mà-sai.
  - **Phép kiểm không quan sát được điều nó tuyên bố thì là phép kiểm giả.** Cả hai lần hỏng ở trên đều cho màu xanh/đỏ vì lý do khác hẳn điều đang kiểm. Sau khi viết xong một phép kiểm môi trường, phải hỏi: *mình có thật sự dựng được đúng cảnh đó không?*


### 74. "Không có thư viện ngoài" là điều kiện nền của cả quy trình bàn giao — nhưng nó chỉ là NIỀM TIN cho tới khi có phép kiểm
- **Ngày:** 2026-08-19
- **Mức độ:** 🟡 Medium (chưa hỏng lần nào; ghi lại vì hậu quả tương lai rất nặng và rất dễ xảy ra)
- **Vị trí:** bộ kiểm mới `tests/test_khong_dependency.py`.
- **Bối cảnh:** Người dùng mô tả quy trình bàn giao có bước *"tất cả thư viện máy cha có thì máy con nếu không có sẽ tự động cài"*. Quét AST toàn bộ file `.py` của tool: **không một thư viện ngoài chuẩn nào**. Bước đó là **no-op** — và nếu làm theo nghĩa đen (chép mọi gói máy cha có) thì sẽ cài hàng trăm gói không liên quan sang máy người ta.
- **Vì sao vẫn phải ghi và phải có phép kiểm:** khẳng định "không cần cài gì" là **nền móng** của cả quy trình zip → NAS → giải nén → bấm `.bat`. Nếu sau này ai đó thêm một `import requests`:
  - **máy cha vẫn chạy tốt** (máy phát triển thường đã có sẵn gói đó)
  - **máy con vỡ ngay khi khởi động** với `ModuleNotFoundError`
  - 15-20 người không phải lập trình viên không có cách nào hiểu chuyện gì xảy ra
  Đây đúng lớp lỗi "máy cha không thể tự phát hiện" đã gặp ở #67. Khác biệt duy nhất: lần này ta chặn **trước khi** nó xảy ra.
- **Cách sửa:** biến khẳng định thành phép kiểm. `tests/test_khong_dependency.py` dùng `ast` quét mọi `import` trong các file `.py` của tool (**không** tính `tests/` — thư mục đó không bắt buộc đi kèm máy con), đối chiếu với `sys.stdlib_module_names`, trừ đi danh sách module nội bộ. Kiểm thêm:
  - không dùng API chỉ có ở Python mới hơn 3.8 (`removeprefix`, `stdlib_module_names`, `batched`...) — tool tuyên bố hỗ trợ 3.8+
  - tool có **tự kiểm phiên bản Python lúc khởi động** không
  - `BAN_GIAO.md` có ghi **đúng** ngưỡng 3.8 không
- **Cách kiểm chứng:** `scratchpad/chung_minh_dep.py` gài **3 vi phạm có chủ ý** rồi dọn: `import requests`, `from numpy import array`, và `str.removeprefix` (API 3.9). **Bắt được 3/3**, sau khi dọn thì sạch. Gài bằng cách tạo file `.py` **tạm** trong thư mục tool chứ không sửa file đang có — vì lúc đó đang có một bản chạy production trên project thật.
- **Bài học:**
  - **Mọi tiền đề của một quy trình phải là thứ ĐƯỢC KIỂM, không phải thứ được nhớ.** "Tool không cần thư viện ngoài" đúng ở thời điểm nói, nhưng không có gì giữ cho nó tiếp tục đúng. Một phép kiểm 60 dòng làm được việc đó mãi mãi.
  - **Yêu cầu của người dùng đôi khi dựa trên mô hình tinh thần sai — phải kiểm rồi nói thẳng, đừng làm theo nghĩa đen.** Ở đây "cài mọi thư viện máy cha có" nghe hợp lý nhưng thực hiện đúng chữ sẽ gây hại. Việc đúng là **đo, báo lại, rồi đề xuất thứ đạt cùng mục đích**.
  - **Bộ kiểm đạt ngay lần đầu vẫn phải bị ép thất bại.** Lần này phép gài lỗi không lộ ra lỗ hổng nào (khác với lần ở #63), nhưng chi phí chỉ vài phút và nó biến "tôi tin bộ kiểm này chạy" thành "tôi đã thấy nó bắt".
  - **Khi cần gài lỗi lúc đang có job thật chạy: TẠO file mới, đừng sửa file đang có.** Tiến trình đang chạy đã nạp module vào bộ nhớ nên sửa đĩa không ảnh hưởng nó, nhưng tạo-rồi-xoá là đường an toàn không cần lý luận.


### 75. Cảnh báo đường dẫn dài đưa ra một lời khuyên KHÔNG THỂ LÀM ĐƯỢC
- **Ngày:** 2026-08-19
- **Mức độ:** 🟡 Medium (không hỏng gói; nhưng bắt người dùng làm một việc vô ích và mất niềm tin vào báo cáo)
- **Vị trí:** `goi_project_capcut.py` → `scan_long_paths()` chỗ in ra báo cáo và màn hình. Hàm mới `phan_loai_path_dai()`; bộ kiểm `tests/test_path_dai.py`.
- **Triệu chứng:** Gói `DS3_006` xong, tool báo:
  ```
  ! 2 file co duong dan > 260 ky tu - CapCut co the khong mo duoc.
    Nen xuat ra duong dan NGAN hon (vd D:\GOI\DS3_006).
  ```
  Làm theo lời khuyên đó **không có tác dụng**.
- **Nguyên nhân gốc:** CapCut tải ảnh từ CMS và dùng **nguyên chuỗi base64 làm tên file** — 205 ký tự:
  ```
  eyJidWNrZXQiOiJmcm9udGllci1jbXMiLCJrZXkiOiIyMDI1LTEwL2p3ZTMtbGF1bmNoLXNjcmVlbnNob3RzLW1vc2FzYXVydXMt... .webp
  ```
  (giải mã ra là một khối JSON `{"bucket":"frontier-cms","key":"...","edits":{"webp":{"quality":85}...}`)

  Cộng với `subdraft/<GUID 36 ký tự>/materials/`, **riêng phần tương đối bên trong gói đã 280 ký tự** — vượt 260 **trước cả khi** cộng thư mục đích. Đặt gói ở `D:\` (3 ký tự) vẫn ra 283. Không thư mục đích nào đủ ngắn.
- **Vì sao đáng sửa dù không hỏng gói:** người dùng sẽ chuyển gói sang chỗ khác, **chạy lại 20 phút**, rồi thấy cảnh báo **y hệt**. Một báo cáo đưa ra lời khuyên không làm được sẽ dạy người dùng bỏ qua mọi cảnh báo khác — kể cả những cảnh báo thật sự quan trọng. Cùng tinh thần với #65 (cảnh báo giả về khoá `_`): sai một cảnh báo là làm hỏng giá trị của tất cả.
- **Cách sửa:** thêm `phan_loai_path_dai()` chia làm **hai nhóm**:
  1. **Rút ngắn đích cứu được** → nói rõ ngưỡng: *"đặt folder XUẤT RA ở đường dẫn tối đa N ký tự"* (N tính từ phần tương đối dài nhất, thay vì khuyên chung chung).
  2. **Rút ngắn đích KHÔNG cứu được** → mục riêng trong báo cáo, nói thẳng nguyên nhân là **tên file gốc quá dài, không phải thư mục người dùng chọn**.
  Cả báo cáo lẫn màn hình đều dùng chung phép phân loại này.
- **Cách kiểm chứng:** `tests/test_path_dai.py` (11 phép kiểm) dựng **đúng dữ liệu thật** của `DS3_006`: tên file 205 ký tự trong `subdraft/<GUID>/materials/`. Kiểm cả hai chiều — file dài vì *đích* phải vào nhóm 1, file dài vì *tên* phải vào nhóm 2 — cộng phép kiểm chống code chết và chống lời khuyên cũ quay lại.
- **Sai lầm trong chính bộ kiểm (ghi lại vì suýt kết luận nhầm là code sai):** bản đầu tôi dựng tên file giả chỉ cho phần tương đối 231 ký tự. `3 + 1 + 231 = 235 < 259` → nó **thật sự cứu được** bằng cách rút ngắn đích, nên phân loại của code là **đúng** còn kỳ vọng của bộ kiểm mới là sai. Đã sửa bằng cách dùng đúng độ dài thật (205) và **chốt lại bằng `assert`** để bộ kiểm không âm thầm đo sai thứ.
- **Bài học:**
  - **Lời khuyên trong báo cáo phải LÀM ĐƯỢC.** Trước khi viết "hãy làm X", phải tự hỏi: có trường hợp nào X không cứu được không? Nếu có, phải tách ra và nói thật.
  - **Khi con số vượt ngưỡng, phải truy xem phần nào gây ra.** Ở đây tổng 334 ký tự = 53 (người dùng chọn) + 280 (CapCut sinh ra). Chỉ phần thứ nhất là thứ người dùng đổi được — và nó **không phải** phần gây tràn.
  - **Dữ liệu trong bộ kiểm phải lấy từ ĐO THẬT, và phải `assert` lại.** Một hằng số bịa "cho giống" sẽ làm bộ kiểm đo nhầm thứ khác mà vẫn cho ra màu đỏ/xanh thuyết phục.


### 76. Thư mục tên `goi_project_capcut (1)` làm VỠ file `.bat` — đúng cái tên Windows tự đặt khi giải nén zip lần hai
- **Ngày:** 2026-08-20
- **Mức độ:** 🟠 High (máy con không chạy được tool, cửa sổ đóng ngay, không đọc được chữ nào)
- **Vị trí:** `goi_project_capcut.bat`, `xem_tien_trinh.bat` — khối `if not exist ... ( ... echo Thu muc nay: %~dp0 ... )`.
- **Triệu chứng (đo thật, không suy luận):** chép công cụ vào thư mục tên `goi_project_capcut (1)`:
  - đủ file → **tool KHÔNG khởi động**
  - thiếu `goi_project_capcut.py` → in `\ was unexpected at this time.` rồi **đóng cửa sổ ngay**, `pause` không bao giờ chạy tới
- **Nguyên nhân gốc:** `%~dp0` được `echo` **không có ngoặc kép**, bên trong khối `if ... ( ... )`. Dấu `)` trong đường dẫn **đóng khối sớm** → cú pháp vỡ. Nặng hơn: `cmd.exe` **phân tích cả khối trước khi chạy**, nên tool hỏng **ngay cả khi điều kiện `if` không đúng** — tức là hỏng cả ở đường chạy bình thường, không chỉ ở nhánh báo lỗi.
- **Vì sao đây là lỗi trên ĐƯỜNG QUAN TRỌNG NHẤT:** `<ten> (1)` chính là tên **Windows tự đặt** khi giải nén một file zip lần thứ hai vào cùng chỗ. Quy trình bàn giao của dự án này là *zip → NAS → máy con tải về → giải nén*. Người dùng giải nén lại (vì lần đầu lỗi, hoặc vì cập nhật bản mới) là chuyện gần như chắc chắn xảy ra với 15-20 người. `C:\Program Files (x86)\` cũng dính.
- **Cách sửa:** bỏ hẳn khối `( ... )`, chuyển sang `if exist ... goto :chay`, và **bọc `%~dp0` trong ngoặc kép** khi in. Không dùng `enabledelayedexpansion` + `!BIEN!` — cách đó đổi một lỗi hiếm lấy một lỗi khác (đường dẫn chứa `!` bị nuốt), trong khi ngoặc kép xử lý trọn vẹn cả `)` lẫn `&` mà không đánh đổi gì.
- **Cách kiểm chứng:** `tests/test_bat.py` thêm `test_ky_tu_dac_biet()` — dựng thư mục thật tên `goi_project_capcut (1)`, `Nguyen Van A`, `thu muc-binh_thuong`, rồi **chạy thật** `.bat` ở cả hai cảnh (đủ file / thiếu file `.py`). Trước khi sửa: 2/6 phép kiểm đỏ. Sau: 27/27 đạt.
- **Một "lỗi" hoá ra KHÔNG CÓ THẬT — và cách phân biệt:** cùng lúc đó, thư mục `thu muc & co dau va` cũng làm phép thử đỏ (`'...\thu' is not recognized`). Suýt sửa. Đo thêm ba cách gọi thì rõ:

  | Cách gọi | Kết quả |
  |---|---|
  | `cmd /c <đường dẫn>` | HỎNG |
  | `cmd /s /c "<đường dẫn>"` | HỎNG |
  | gọi **thẳng** `.bat` | **CHẠY ĐƯỢC** |

  Tức là `&` bị **chính `cmd.exe` tách lệnh trước khi `.bat` chạy** — Explorer (bấm đúp) **không đi qua đường đó**. Đây là lỗi của **cách kiểm**, không phải của `.bat`. Đã sửa `tests/test_bat.py` gọi thẳng `.bat` như Explorer.
- **Bài học:**
  - **Trong `.bat`, mọi lần dùng `%~dp0` (và mọi biến chứa đường dẫn) đều phải bọc ngoặc kép** — kể cả trong `echo`. Đường dẫn người dùng chứa `)` `&` `^` là chuyện bình thường, không phải ngoại lệ.
  - **`cmd.exe` phân tích cả khối `( ... )` trước khi chạy**, nên một lỗi cú pháp trong nhánh KHÔNG được chạy vẫn giết cả file. `goto` an toàn hơn khối ngoặc trong mọi trường hợp có nội suy biến.
  - **Phép kiểm phải mô phỏng đúng cách người dùng thật khởi động.** Kiểm bằng `cmd /c` sinh ra một lỗi không tồn tại; nếu tin nó, ta sẽ đi "sửa" một thứ không hỏng và có thể làm hỏng thứ đang chạy tốt.
  - **Khi một phép kiểm đỏ, câu hỏi đầu tiên là "cảnh này có thật không", không phải "sửa code thế nào".** Ở đây một câu hỏi đó tách được một lỗi thật khỏi một lỗi ảo, cả hai đỏ y như nhau.


### 77. File trong folder draft bị CHÉP HAI LẦN thay vì liên kết cứng — 9,45 GB lãng phí trên một gói 22 GB
- **Ngày:** 2026-08-20
- **Mức độ:** 🟠 High (không mất dữ liệu, nhưng gói phình gần gấp đôi — đúng thứ chế độ 4 sinh ra để chống)
- **Vị trí:** `goi_project_capcut.py` → `main()`, vòng copy theo `copy_plan` (biến `first_dest`).
- **Triệu chứng:** Người dùng hỏi *"Bài DS3_007 tốn nhiều dung lượng thế á"*. Đo lại: gói **22,00 GB**, trong đó
  ```
  9.45 GB  5f22a39bd4f86d4f5459e3947c16144f.mp4                    (goc goi)
  9.45 GB  subdraft/76A2858D-.../materials/5f22a39...mp4           (ban thu hai)
  ```
  Kiểm bằng `GetFileInformationByHandle`: **`nNumberOfLinks = 1` ở cả hai bản, chỉ số file khác nhau** → hai thực thể riêng biệt trên đĩa, không phải liên kết cứng.
- **Nguyên nhân gốc:** trong vòng copy, `first_dest` được khởi tạo **rỗng** và chỉ ghi nhận những bản do **chính vòng đó** tạo ra. Nhưng file nằm trong folder draft đã được **`copytree` chép sang gói từ trước** — một đường code khác. Hai đường không biết đến nhau, nên khi `copy_plan` cần bản thứ hai ở `subdraft/.../materials/`, `first_dest` không có mục nào → rơi thẳng vào `shutil.copy2` → chép lần hai toàn bộ 9,45 GB.

  Cơ chế liên kết cứng **vẫn hoạt động đúng** cho các file khác (log ghi *"63 liên kết cứng"*) — nó chỉ mù với những bản đến từ `copytree`.
- **Cách sửa:** trước khi chép, nếu nguồn nằm **trong** `draft_dir` thì suy ra vị trí bản mà `copytree` đã tạo (`out_dir / relpath(src, draft_dir)`); nếu bản đó có thật và khác đích đang cần, **liên kết cứng tới nó** thay vì chép. Ba chốt an toàn: chỉ áp dụng cho file trong draft (`_rel` không bắt đầu bằng `..`), chặn tự-liên-kết khi đích trùng nguồn, và giữ nguyên đường lui `shutil.copy2` khi `os.link` thất bại (SMB có thể không hỗ trợ).
- **Cách kiểm chứng:** `tests/test_lien_ket_cung.py` (8 phép kiểm) dựng đúng tình huống — file trong draft, mô phỏng bản `copytree`, rồi yêu cầu bản thứ hai — và kiểm bằng **`st_ino`/`st_dev`** rằng hai đường dẫn trỏ tới **cùng một thực thể**, `st_nlink == 2`, dung lượng thật bằng một bản. Cộng bốn phép kiểm chống code chết.
- **Phát hiện kèm theo (chưa sửa, cần người dùng quyết):** 19,73 GB / 22 GB của gói `DS3_007` là **bản render ngược** (`reverse_path`) của `DS021.mp4` và `1129(8)-1.mp4`. Chúng chỉ được trỏ tới qua khoá `materials.videos[].reverse_path`, **không bao giờ qua `path`**. Đó là file **dẫn xuất CapCut tự sinh** khi áp hiệu ứng tua ngược — CapCut tạo lại được. Chúng không được mã lại (không có job nào sinh ra cho chúng) và cũng không bị loại. Bỏ hẳn thì gói còn ~3 GB, nhưng máy con sẽ phải render lại chỗ tua ngược. Đây là **quyết định của người dùng**, không phải lỗi.
- **Bài học:**
  - **Hai đường code cùng ghi vào một đích thì phải chia sẻ bảng tra.** `copytree` và `copy_plan` cùng đổ file vào `out_dir` nhưng mỗi bên giữ trạng thái riêng. Mọi cơ chế khử trùng lặp chỉ đúng trong phạm vi nó nhìn thấy.
  - **Đo dung lượng bằng `os.walk` + `getsize` là SAI khi có liên kết cứng** — nó đếm mỗi liên kết một lần. Chính tôi đã báo nhầm 24,42 GB (cộng dồn) trong khi thật là 22,00 GB. Muốn đo đúng phải đếm theo **chỉ số file** (`st_ino`/`st_dev`), mỗi thực thể một lần.
  - **Câu hỏi "sao tốn nhiều thế" của người dùng là một phép thử vô lý đáng giá** (tinh thần #18/#19). Con số không khớp trực giác của người hiểu dữ liệu thường là dấu hiệu của một lỗi thật — ở đây lộ ra hai lỗi độc lập cùng lúc.
  - **Khi một file lớn bất thường, hãy tìm KHOÁ JSON trỏ tới nó, đừng chỉ tìm tên file.** `reverse_path` so với `path` là khác biệt quyết định giữa "footage gốc phải giữ" và "cache dẫn xuất có thể bỏ" — nhìn tên file thì hai thứ giống hệt nhau.


### 78. Bản render ngược (`reverse_path`) không bao giờ được nén — 147 GB trên 21 project
- **Ngày:** 2026-08-20
- **Mức độ:** 🟠 High (gói phình gấp nhiều lần; trên `DS3_007` chiếm 90% dung lượng gói)
- **Vị trí:** `toi_uu_dung_luong.py` → `collect_jobs()` (vòng duyệt `materials.videos`), phần ghi kết quả trong `optimize_package()`, và `_plan_replacements_body()`.
- **Triệu chứng:** Người dùng hỏi *"Bài DS3_007 tốn nhiều dung lượng thế á"*. Gói 22,00 GB, trong đó **19,73 GB là hai file render ngược**, không file nào được nén.
- **Nguyên nhân gốc:** CapCut sinh file này khi áp hiệu ứng **tua ngược**, và trỏ tới nó qua khoá `materials.videos[].reverse_path` — **không bao giờ qua `path`**. Vòng duyệt trong `collect_jobs()` bắt đầu bằng:
  ```python
  for m in (_d.get("materials", {}).get("videos") or []):
      if not isinstance(m, dict) or not m.get("path"):
          continue
      p = m["path"]
  ```
  Nó chỉ đọc `path`, nên **không job nào được sinh ra** cho bản ngược → không nén, không cắt, chỉ gom nguyên bản.
- **Quy mô (đo, không đoán):** quét `draft_content.json` của mọi draft trên `D:\1363\Video Capcut\CapCut Drafts`: **21 project, 34 file, tổng 147,07 GB**. Lớn nhất: project `1` (41,69 GB), `DS1_056` (20,17 GB), `DS3-005` (19,18 GB). Đây không phải chuyện riêng của một project.
- **Cách sửa (người dùng chọn "nén lại như clip thường"):** thêm một vòng riêng trong `collect_jobs()` sinh job cho `reverse_path` khi bật `recompress`. Ba quyết định thiết kế:
  1. **Không cắt gọn, không hạ phân giải** — ta không biết đoạn nào được dùng trên bản ngược, và `duration`/`width` của material mô tả bản **xuôi**. Chỉ nén bitrate.
  2. **Ghi kết quả vào `reverse_path`, KHÔNG ghi đè `path`** — ghi nhầm sẽ làm clip xuôi trỏ vào bản ngược, **hình chạy ngược**. Dùng cờ `khoa_ghi` trên job để phân nhánh.
  3. **Không đụng `duration`/`width`/`height`** của material vì chúng mô tả bản xuôi.
  Đồng thời `_plan_replacements_body()` phải đếm `reverse_path` vào `total_by_file`, nếu không điều kiện `opt_by_file >= total_by_file` không bao giờ đạt và bản gốc vẫn bị `copytree` đẩy lên đích rồi mới bị thay — tốn cả chục GB đường truyền vô ích.
- **Cách kiểm chứng:** thêm tuỳ chọn `co_reverse` vào `tests/draft_gia.py` (**trước đó draft giả không hề có `reverse_path`** — đúng lý do lỗi này sống sót qua 22 bộ kiểm). `tests/test_reverse.py` (11 phép kiểm) kiểm ở hai tầng: `collect_jobs` có sinh job đúng thuộc tính không, và **chạy thật cả pha tối ưu** rồi đọc lại `draft_content.json` ở đích. Đo được: bản ngược 1629 KB → **1028 KB**.
- **Chứng minh bộ kiểm bắt được:** gỡ từng phần bản vá ra — (a) bỏ việc sinh job, (b) ghi nhầm vào `path` — **bắt được 2/2**, khôi phục sạch.
- **Bài học:**
  - **Một vòng lặp lọc theo `if not m.get("path"): continue` là một điểm mù có hệ thống.** Mọi khoá khác trỏ tới media (`reverse_path`, và có thể còn khoá khác chưa gặp) đều biến mất khỏi mọi bước xử lý phía sau. Khi duyệt material, phải hỏi: **còn khoá nào trỏ tới file nữa không?**
  - **Fixture thiếu một hình dạng dữ liệu = một lớp lỗi không bao giờ bị bắt.** `draft_gia.py` chưa từng sinh `reverse_path`, nên 22 bộ kiểm xanh vẫn không nói gì về đường này. Cùng bài học với #64 (draft giả "sạch" không chạm nhánh dọn dẹp) và #61.
  - **Khi thêm một loại job mới, phải hỏi nó ghi kết quả vào ĐÂU.** Mặc định của code cũ là ghi vào `path`; nếu không phân nhánh, bản vá "tiết kiệm dung lượng" sẽ biến thành lỗi **hình chạy ngược** — tệ hơn nhiều so với vấn đề nó định sửa.
  - **Câu hỏi ngây thơ của người dùng đáng giá hơn nhiều lượt rà soát code.** "Sao tốn nhiều thế" lộ ra hai lỗi độc lập (mục này và #77) mà không bản rà soát nào tìm ra.


### 79. `st_nlink` nói dối trên ổ mạng — phép kiểm liên kết cứng phải dùng `st_ino`/`st_dev`
- **Ngày:** 2026-08-20
- **Mức độ:** 🟡 Medium (không phải bug trong tool; là cái bẫy làm người kiểm chứng kết luận sai)
- **Vị trí:** `tests/test_lien_ket_cung.py`; liên quan bản vá [[#77]].
- **Bối cảnh:** Bản vá #77 thay việc chép lần hai bằng `os.link`. Nhưng chú thích sẵn có trong `collect_jobs()` đã ngờ ngược lại: *"trên ổ mạng (SMB không hỗ trợ liên kết cứng) sẽ thành bản sao thật"*. Nếu điều đó đúng thì bản vá **vô tác dụng ở đúng nơi cần nhất** — mọi gói đều xuất ra NAS. Phải **đo**, không được tin cả hai phía.
- **Kết quả đo trên NAS đích thật (`\\192.168.1.214\e`):**

  | Ổ | `os.link` | `st_ino`/`st_dev` trùng | `st_nlink` |
  |---|---|---|---|
  | Cục bộ | thành công | **có** | **2** ✅ |
  | NAS (SMB) | **thành công** | **có** | **1** ❌ |

  Tức là: **SMB CÓ hỗ trợ liên kết cứng** (chú thích cũ trong code sai, hoặc đúng với NAS khác), nhưng **báo `st_nlink` sai**. Hai đường dẫn dùng chung một thực thể mà hệ thống vẫn nói "chỉ có 1 liên kết".
- **Hệ quả nếu không biết:** một phép kiểm viết theo bản năng — `assert os.stat(p).st_nlink == 2` — sẽ **đỏ trên NAS dù mọi thứ đúng**. Người bảo trì sau sẽ đi "sửa" một bản vá đang chạy tốt, hoặc tệ hơn: gỡ nó ra vì tưởng nó không hoạt động.
- **Cách sửa:** dùng **`(st_ino, st_dev)`** làm bằng chứng "cùng một thực thể" — đó là phép so đúng ngữ nghĩa và đúng trên cả hai loại ổ. Giữ `st_nlink` nhưng chỉ kiểm trên ổ cục bộ, kèm chú thích nói rõ vì sao.
- **Cách kiểm chứng:** `scratchpad/thu_link_nas.py` — tạo file thật, `os.link`, so `st_ino`/`st_dev` và `st_nlink`, rồi dọn sạch; chạy trên **cả** ổ cục bộ **và** NAS đích thật.
- **Bài học:**
  - **Chú thích trong code là giả thuyết, không phải sự thật đã kiểm.** Câu *"SMB không hỗ trợ liên kết cứng"* nằm sẵn trong `toi_uu_dung_luong.py` và nghe rất hợp lý — nhưng sai với NAS này. Một chú thích sai còn nguy hơn không có chú thích, vì nó ngăn người sau đi đo.
  - **Cùng một sự thật có thể được hệ thống tệp trả lời khác nhau tuỳ cách hỏi.** `st_nlink` và `st_ino` cùng mô tả "liên kết cứng" nhưng chỉ một cái đáng tin qua SMB. Khi kiểm một thuộc tính hệ thống tệp, phải hỏi: **cách hỏi này có đáng tin trên loại ổ mà tool thật sự chạy không?**
  - **Mọi khẳng định về môi trường phải đo TRÊN CHÍNH MÔI TRƯỜNG ĐÓ.** Đo `os.link` trên ổ C: rồi suy ra cho NAS là đúng loại sai lầm mà cả dự án này đang chống — cũng như "gói mở được trên máy cha" không nói gì về máy con.


### 80. Bản vá liên kết cứng quên cập nhật bảng tra — bản thứ ba trở đi phải dò lại qua mạng mỗi lần
- **Ngày:** 2026-08-20
- **Mức độ:** 🟡 Medium (không sai kết quả; tốn thêm một vòng SMB cho mỗi file dùng chung)
- **Vị trí:** `goi_project_capcut.py` → `main()`, nhánh `os.link` trong vòng copy. Tiếp theo [[#77]].
- **Triệu chứng:** đọc lại chính bản vá vừa viết thì thấy: khi liên kết **thành công** tới bản do `copytree` chép, `first_dest[skey]` **không được ghi**. Chỉ nhánh `shutil.copy2` mới ghi. Hệ quả: mỗi lần cần thêm một bản nữa của cùng file, code phải `isfile_safe(_ung)` lại từ đầu — **một vòng SMB thừa cho mỗi bản**.
- **Vì sao đáng sửa:** trên project thật `DS3_007`, một file được **6 đường dẫn** dùng chung. Với hàng trăm file như vậy thì đó là hàng trăm vòng mạng thừa, đúng loại chi phí mà bài học #62 đã chỉ ra là thứ **thật sự** tốn kém với công cụ này (*"tối ưu đúng chỗ nghĩa là giảm SỐ VÒNG ĐI MẠNG"*), chứ không phải mili-giây CPU.
- **Cách sửa:** `first_dest.setdefault(skey, fd)` ngay sau khi `os.link` thành công. Dùng `setdefault` chứ không phải gán thẳng, để không ghi đè bản đã biết từ trước.
- **Cách kiểm chứng:** thêm phép kiểm **bản thứ BA** vào `tests/test_lien_ket_cung.py` — mô phỏng đúng tình huống nhiều dự án con dùng chung một file, và xác nhận cả ba đường dẫn trỏ tới **cùng một `(st_ino, st_dev)`**. Trước đó bộ kiểm chỉ thử tới bản thứ hai, nên thiếu sót này hoàn toàn vô hình.
- **Bài học:**
  - **Đọc lại bản vá của chính mình như đọc code người khác.** Thiếu sót này không do agent nào tìm ra, không do bộ kiểm nào đỏ — chỉ do đọc lại đoạn vừa viết và hỏi "nhánh thành công có làm đủ việc như nhánh thất bại không?".
  - **Khi hai nhánh cùng đạt một mục tiêu, chúng phải cập nhật cùng một trạng thái.** Ở đây `os.link` và `shutil.copy2` đều tạo ra "một bản ở đích", nhưng chỉ một nhánh ghi vào bảng tra. Bất đối xứng giữa các nhánh là nơi lỗi hay nấp — cũng chính là hình dạng của #77 (hai đường code cùng ghi vào một đích mà không chia sẻ bảng tra).
  - **Bộ kiểm dừng ở "hai" thì không thấy lỗi của "ba".** Nhiều lỗi chỉ lộ từ lần lặp thứ ba trở đi. Khi kiểm một cơ chế khử trùng lặp, phải thử ít nhất ba.


### 81. Hai file nội dung song song (`draft_content.json` + `draft_info.json`) chưa từng được kiểm tính nhất quán
- **Ngày:** 2026-08-20
- **Mức độ:** 🟡 Medium (tool đang làm ĐÚNG; ghi lại vì đây là bề mặt chưa có phép kiểm nào, và hậu quả nếu hỏng là mất hình âm thầm)
- **Vị trí:** bổ sung `kiem_hai_file_noi_dung()` vào `tests/test_e2e.py`.
- **Bối cảnh:** `DS3_094` là project đầu tiên tôi để ý có **cả hai** file nội dung. Kiểm lại thì `DS3_003` cũng có. CapCut giữ hai file song song mô tả cùng một timeline.
- **Rủi ro nếu hỏng:** nếu tool chỉ viết lại `draft_content.json` mà bỏ `draft_info.json`, máy con có thể mở ra bản **chưa được viết lại** → trỏ vào `D:\1363\...` → **mất hình**. Nguy hơn nữa: bộ tự kiểm có thể vẫn kết luận **"ĐỦ"** nếu nó chỉ soi file kia. Đúng lớp lỗi "máy cha đủ, máy con hỏng" mà cả dự án này sinh ra để chống.
- **Kết quả kiểm (tool ĐANG ĐÚNG):** trên gói `DS3_003`, cả hai file còn lại **đúng cùng một tập** 3 đường dẫn tuyệt đối (3 file `Screen Recording` hỏng sẵn). Không lệch. Lý do đúng: phần viết lại đi qua `iter_json_files()` nên chạm mọi file `.json`, không phải chỉ file được chọn ở `content_name`.
- **Vì sao vẫn phải thêm phép kiểm:** `main()` có dòng `content_name = CONTENT_NAMES[0] if ... else CONTENT_NAMES[1]` — tức là **có** chỗ trong code chỉ chọn MỘT file. Nó chỉ dùng để dò GUID nên vô hại, nhưng nó cho thấy mô hình "một file nội dung" tồn tại trong code. Chỉ cần ai đó mở rộng chỗ đó, hoặc thêm một bộ lọc vào `iter_json_files()`, là lỗi thành thật mà không bộ kiểm nào đỏ.
- **Cách kiểm chứng:** `kiem_hai_file_noi_dung()` duyệt mọi thư mục trong gói có **cả hai** file, trích tập đường dẫn **tuyệt đối** còn lại trong mỗi file, và bắt buộc hai tập **bằng nhau**. Kèm một phép kiểm chống rỗng: *"có ít nhất một cặp file nội dung để kiểm"* — nếu draft giả không sinh `draft_info.json` thì phép kiểm trên là vô nghĩa và phải đỏ, chứ không được xanh giả.
- **Chứng minh bắt được:** gài lỗi cho `iter_json_files()` **bỏ qua** `draft_info.json` → phép kiểm đỏ ngay (`FAIL hai file noi dung NHAT QUAN`), khôi phục xong lại xanh.
- **Bài học:**
  - **Khi một định dạng có N bản sao của cùng một sự thật, phải kiểm chúng KHỚP NHAU** — không chỉ kiểm từng bản hợp lệ. Đây là chỗ lỗi thích nấp: mỗi file đọc riêng đều "đúng", chỉ khi so mới thấy lệch.
  - **Tool đang đúng KHÔNG phải lý do bỏ qua phép kiểm.** Nó đúng nhờ một chi tiết cài đặt (`iter_json_files` quét tất cả) chứ không nhờ một quyết định có chủ đích được bảo vệ. Phép kiểm biến sự đúng tình cờ thành sự đúng có ràng buộc.
  - **Mọi phép kiểm dạng "so hai tập" phải có chốt chống rỗng.** Nếu không tìm thấy cặp nào để so, nó sẽ xanh — và xanh vì không kiểm gì cả là kiểu xanh giả nguy hiểm nhất (cùng họ #61, #64, #78).


### 82. Draft giả chỉ có MỘT tầng subdraft — trong khi cả sáu project thật đều lồng nhiều tầng
- **Ngày:** 2026-08-20
- **Mức độ:** 🟠 High (không phải bug trong tool; là **lỗ hổng che mắt** khiến 23 bộ kiểm mù trước một tính năng cốt lõi)
- **Vị trí:** `tests/draft_gia.py` (thêm `GUID_SUB2`, `GUID_SUB3`); `tests/test_e2e.py` (thêm `kiem_subdraft_nhieu_tang()`).
- **Triệu chứng:** `DS3_094` có **17 subdraft, sâu 3 tầng** — dự án con lồng trong dự án con, rồi clip ghép trong đó:
  ```
  DS3_094 → 70B22A70 (dự án con) → F9A37AFD (dự án con) → D644F99A (clip ghép)
  ```
  Kiểm lại `draft_gia.py` thì nó chỉ sinh **một** tầng `subdraft/<GUID>/`. Nghĩa là **toàn bộ 23 bộ kiểm chưa bao giờ chạy qua tầng 2 hay tầng 3** — trong khi **cả sáu project thật** của người dùng đều có subdraft lồng nhau.
- **Vì sao nghiêm trọng dù tool đang chạy đúng:** "dự án con hoạt động trơn tru ở máy khác" là **một trong ba yêu cầu chính** người dùng nêu. Toàn bộ bằng chứng cho yêu cầu đó đến từ việc chạy tay trên project thật, không từ bộ kiểm nào. Một thay đổi làm hỏng đường lồng nhiều tầng sẽ **không bộ kiểm nào đỏ** — chỉ phát hiện được khi có người mở gói trên máy con, tức là sau khi đã bàn giao.
- **Cách sửa:** dựng đủ ba tầng trong draft giả, đúng hình dạng thật — tầng 2 là **dự án con** (có `draft_meta_info.json` riêng), tầng 3 là **clip ghép** (chỉ có `sub_draft_config.json`), mỗi tầng có media riêng tham chiếu bằng placeholder giải theo gốc của chính nó. Thêm `kiem_subdraft_nhieu_tang()` vào E2E: mọi subdraft phải sang đủ, và subdraft **sâu nhất** phải có media thật chứ không chỉ có thư mục rỗng.
- **Chốt chống rỗng:** phép kiểm đầu tiên là *"draft giả có subdraft lồng ÍT NHẤT 3 tầng"*. Nếu sau này ai đó làm fixture nông đi, phép kiểm **đỏ** thay vì xanh vô nghĩa. Không có chốt này thì `kiem_subdraft_nhieu_tang()` sẽ "đạt" trên một cây một tầng và ta lại quay về đúng chỗ cũ.
- **Cách kiểm chứng:** E2E từ 24 → **29 phép kiểm**, tất cả đạt; cây subdraft trong gói được đối chiếu với nguồn theo **đường dẫn tương đối đầy đủ**, không chỉ đếm số lượng.
- **Bài học:**
  - **Đây là lần thứ TƯ cùng một hình dạng lỗi** (#61 `xem_tien_trinh.py` không có bộ kiểm nào, #64 draft giả "sạch" không chạm nhánh dọn dẹp, #78 draft giả không có `reverse_path`). Kết luận đã đủ rõ để thành quy tắc: **mỗi khi gặp một hình dạng dữ liệu mới trên project thật, việc đầu tiên là hỏi "fixture có sinh ra nó không?"** — trước cả khi đi tìm lỗi.
  - **Số lượng bộ kiểm không đo được vùng phủ.** 23 bộ, hàng trăm phép kiểm, mà một tính năng cốt lõi vẫn không có một dòng nào chạm tới. Câu hỏi đúng không phải "có bao nhiêu phép kiểm" mà **"hình dạng dữ liệu nào của project thật chưa từng đi qua bộ kiểm?"**
  - **Fixture phải mô phỏng cái KHÓ NHẤT gặp được, không phải cái điển hình.** Một tầng subdraft là điển hình; ba tầng mới là thứ làm vỡ code. Nếu fixture chỉ dựng cái điển hình thì nó chỉ chứng minh được điều ta vốn đã tin.


### 83. Bộ kiểm subdraft nhiều tầng XANH mà không chứng minh được gì — fixture toàn placeholder
- **Ngày:** 2026-08-20
- **Mức độ:** 🟠 High (dạng "xanh giả" tinh vi nhất gặp tới nay: có bộ kiểm, chạy đúng, và **không kiểm gì cả**)
- **Vị trí:** `tests/draft_gia.py` (tầng 2, 3 nay có đường dẫn TUYỆT ĐỐI); `tests/test_e2e.py` → `kiem_subdraft_nhieu_tang()`.
- **Triệu chứng:** vừa thêm fixture subdraft 3 tầng ([[#82]]) và phép kiểm *"mọi file nội dung ở mọi tầng đều không còn đường dẫn tuyệt đối"*. Nó **xanh ngay lần đầu**. Khi gài lỗi để chứng minh, nó **vẫn xanh** — bốn lần liên tiếp.
- **Quá trình dò (đáng ghi vì mỗi bước đều là một kết luận sai suýt xảy ra):**
  1. Gài vào `scan_subprojects(max_depth=2)` → không bắt. **Kết quả này ĐÚNG**: hàm đó chỉ dùng để *in thông báo*, không quyết định việc gom. Suýt kết luận nhầm là "tool xử lý tầng sâu tốt".
  2. Gài vào `iter_json_files` bằng `os.path.relpath(fp, _lp(root))` → không bắt, vì `relpath` với gốc đã `_lp()` không cho kết quả như giả định.
  3. Gài đơn giản hơn (đếm `"subdraft"` trong đường dẫn) → vẫn không bắt.
  4. **In ra xác nhận bản gài có thật sự được chèn không** → `True`, mà bộ kiểm vẫn xanh ⇒ lỗi **không** ở phép gài, mà ở **dữ liệu fixture**.
- **Nguyên nhân gốc:** fixture dùng **placeholder ở mọi tầng** (`##_draftpath_placeholder_..._##/materials/video/tang2.mp4`). Không có đường dẫn tuyệt đối nào ⇒ không có gì để viết lại ⇒ phép kiểm *"không còn đường dẫn tuyệt đối"* đúng **một cách rỗng**. Nó xanh vì **chẳng có gì để kiểm**.
- **Cách sửa:** thêm vào tầng 2 và tầng 3 mỗi tầng **một material trỏ bằng đường dẫn TUYỆT ĐỐI** tới footage ngoài draft. Kèm **chốt chống rỗng** trong chính phép kiểm: *"NGUỒN có đường dẫn tuyệt đối ở subdraft tầng ≥2 (để có gì mà kiểm)"* — nếu ai đó lại làm fixture toàn placeholder, phép kiểm sẽ **đỏ** thay vì xanh vô nghĩa.
- **Cách kiểm chứng:** sau khi sửa, gài lại đúng lỗi cũ → **bắt được, đỏ đúng tầng 2 và tầng 3**, khôi phục sạch. E2E: 29 → **34 phép kiểm**.
- **Bài học:**
  - **Một phép kiểm dạng "KHÔNG còn X" chỉ có nghĩa nếu chứng minh được rằng ĐÃ TỪNG có X.** Đây là lỗi logic, không phải lỗi lập trình: mệnh đề phủ định trên tập rỗng luôn đúng. Mọi phép kiểm dạng `not sot`, `len(...) == 0`, `assert not thieu` đều cần một chốt "có gì để kiểm không".
  - **Khi gài lỗi mà bộ kiểm không đỏ, câu hỏi thứ hai phải là "bản gài có chạy không?"** — trước khi kết luận "code đúng nên không bắt được". Ở đây câu hỏi đó (bước 4) là thứ duy nhất tách được "code tốt" khỏi "fixture rỗng".
  - **Fixture phải chứa đúng thứ mà tính năng cần xử lý.** Muốn kiểm việc *viết lại đường dẫn* thì fixture phải có *đường dẫn cần viết lại*. Nghe hiển nhiên, nhưng tôi đã dựng đủ 3 tầng subdraft mà quên mất điều đó.

### 84. Nhịp đập chỉ đếm clip xong — im lặng 15 phút khiến người dùng tưởng treo và End Task
- **Ngày:** 2026-08-20
- **Mức độ:** 🟠 High (không sai kết quả; nhưng dẫn thẳng tới hành vi làm HỎNG draft của người dùng)
- **Vị trí:** `toi_uu_dung_luong.py` → `optimize_package()`, hàm `work()` và `_heartbeat()`.
- **Triệu chứng:** chạy `DS3_094`, nhịp đập lặp lại **15 phút liền**:
  ```
  [nhip dap] 5/6 clip  (28.1 phut)  (chua xong them clip nao)
  ```
  Không có cách nào biết tool đang chạy hay đã chết.
- **Điều tra:** đọc dòng lệnh của `ffmpeg.exe` đang chạy → đó là một video YouTube **dài 25 phút 18 giây** (`-t 1517.633`) đang hạ từ 4K xuống 2112px. Đo `wmic`: **+363 giây CPU trong 40 giây thực** (ffmpeg chạy ~9 luồng) ⇒ **đang mã thật, không treo**. Một clip duy nhất chiếm gần **nửa** thời gian cả job 32,9 phút.
- **Vì sao nguy hiểm:** người dùng máy con **không thể** đo CPU time. Họ đọc dòng "chưa xong thêm clip nào" mười lăm lần rồi kết luận tool treo → **End Task**. Mà End Task giữa chừng chính là thứ nghi ngờ đã làm hỏng draft của người dùng ngay ở đầu phiên làm việc này. Nhịp đập được thêm vào (#28) để phân biệt "chậm" với "chết" — nhưng nó chỉ làm được một nửa việc đó.
- **Cách sửa:** thêm bảng `dang_lam` ghi clip đang mã (tên, độ dài đoạn, thời điểm bắt đầu), ghi vào **trước** khi gọi `encode_job` và xoá trong `finally`. Khi số clip **đứng yên**, nhịp đập in thêm:
  ```
     dang ma: 5 Animals That Broke the Rules of Death.mp4  (doan 25.3 phut, da chay 12.4 phut)
  ```
  Và khi **không** clip nào đang mã thì nói rõ — vì đó mới là trường hợp đáng ngờ thật (đang đợi I/O hoặc đang ghi kết quả).
- **Ba chốt an toàn đa luồng:** dùng `dict` (gán/xoá một khoá là an toàn giữa các thread, khác `list` + chỉ số); duyệt qua **bản sao** `list(dang_lam.values())` để tránh `RuntimeError: dictionary changed size during iteration` (lỗi đã gặp trong dự án này); giới hạn `[:3]` dòng in để 8 luồng không biến nhịp đập thành bão lũ.
- **Cách kiểm chứng:** `tests/test_nhip_dap.py` (10 phép kiểm) — gồm cả ba chốt đa luồng ở trên và phép kiểm "nói rõ khi không clip nào đang mã".
- **Bài học:**
  - **Một chỉ báo tiến độ chỉ đo ĐẦU RA sẽ im lặng đúng lúc người dùng cần nó nhất.** Việc dài nhất là việc ít sinh đầu ra nhất. Chỉ báo phải nói được **đang làm gì**, không chỉ **đã xong bao nhiêu**.
  - **Nếu người vận hành phải chạy `wmic` để biết tool còn sống hay không, thì tool đang thiếu thông tin — không phải người dùng thiếu kỹ năng.** Với 15-20 người không phải lập trình viên, mọi câu hỏi họ không tự trả lời được sẽ thành một quyết định sai.
  - **Hành vi nguy hiểm nhất của người dùng thường do giao diện gây ra.** End Task làm hỏng draft; nhưng thứ khiến họ End Task là một dòng chữ không nói gì trong mười lăm phút.


### 85. So min với max trên tập nhỏ biến MỘT NGOẠI LỆ thành một "quy luật" — hai lần liên tiếp suýt kết luận sai về hiệu năng
- **Ngày:** 2026-08-20
- **Mức độ:** 🟡 Medium (không phải bug trong tool; là lỗi trong cách ĐO, và nó suýt dẫn tới việc đi tối ưu nhầm chỗ)
- **Bối cảnh:** `DS1_103` có **239 file JSON** — gấp 3 lần mọi project trước. Trước khi chạy, tôi muốn biết pha quét JSON có tăng **phi tuyến** không (câu hỏi mà [[#62]] dạy phải hỏi đầu tiên). Giờ đã có dữ liệu thật từ 8 project thay vì chỉ draft giả.
- **Hai phép đo, hai lần đều báo `CAN XEM LAI` — và cả hai đều SAI:**

  **Lần 1 — chọn nhầm biến.** Đo `giây/clip`, so project nhỏ nhất với lớn nhất:
  > *"Quy mô tăng 1,9 lần → chi phí mỗi clip **tăng 3,14 lần** → CẦN XEM LẠI"*

  Sai vì `giây/clip` phụ thuộc chủ yếu vào **độ dài và độ phân giải clip**, gần như không liên quan tới số file JSON. Đo một biến rồi quy kết cho một biến khác.

  **Lần 2 — đúng biến, sai cách đọc.** Đổi sang `phút/GB đầu vào`:
  > *"116 file JSON → 0,458 phút/GB, còn 61 file JSON → 0,215 → **tăng 2,13 lần** → CẦN XEM LẠI"*

  Vẫn sai. Nhìn **cả sáu** con số thay vì chỉ min–max thì thấy ngay hình dạng thật:
  ```
  006  0.191    007  0.223    010  0.226
  011  0.215    095  0.227    094  0.458   <-- mot minh mot noi
  ```
  Năm project nằm sát nhau trong khoảng **0,191–0,227**; chỉ `094` lệch gấp đôi. Đó là **một điểm ngoại lệ**, không phải một xu hướng.
- **Nguyên nhân thật của điểm ngoại lệ:** `DS3_094` chứa **một** clip YouTube dài **25 phút 18 giây** (đã xác định trước đó bằng dòng lệnh `ffmpeg`: `-t 1517.633`). Riêng clip đó chiếm ~15 phút trong tổng 30 phút của cả pha — **một nửa**. Bỏ `094` ra: 5 project chênh nhau **1,19 lần** trong khi quy mô JSON chênh **1,30 lần**, tức chi phí tăng **CHẬM HƠN** quy mô.
- **Kết luận đúng:** không có bằng chứng phi tuyến theo số file JSON. Biến quyết định thời gian là **tổng độ dài video phải mã**, không phải quy mô cấu trúc JSON.
- **Bài học:**
  - **So min với max trên tập nhỏ là cách dễ nhất để biến một ngoại lệ thành một quy luật.** Với 6 điểm dữ liệu, min và max rất có thể **đều** là ngoại lệ. Phải nhìn **phân bố của toàn bộ** — năm số chụm lại và một số lệch hẳn có hình dạng khác hẳn một dãy tăng đều.
  - **Trước khi kết luận "X gây ra Y", hỏi: mình có đang đo X không?** Lần 1 đo `giây/clip` (do độ dài clip chi phối) rồi quy cho số file JSON. Chọn sai biến thì mọi phép tính sau đó đều vô nghĩa dù đúng số học.
  - **Khi một phép đo báo bất thường, giải thích điểm bất thường trước khi sửa code.** Ở đây câu hỏi *"vì sao riêng 094 lệch?"* có câu trả lời cụ thể (một clip 25 phút) — và câu trả lời đó xoá luôn kết luận "cần xem lại".
  - Cùng họ với bốn lần script nghiệm thu báo động giả trong phiên này ([[#84]] và các mục trước): **khi phép đo báo có vấn đề, nghi ngờ phép đo trước khi nghi ngờ thứ được đo** — nhất là khi kết quả mâu thuẫn với những gì đã biết chắc.


### 86. Đóng gói bản 1.1.0 — ba lỗi chỉ lộ ra khi chạy BẢN GIẢI NÉN, không phải bản gốc
- **Ngày:** 2026-08-21
- **Mức độ:** 🟠 High (một lỗi làm cả bộ kiểm mù, một lỗi làm tài liệu nói dối, một lỗi làm trình báo lỗi tự chết)
- **Bối cảnh:** đóng gói bản bàn giao 1.1.0 kèm **Python embeddable 3.14.6** trong `python/`. Quy trình đóng gói có bước bắt buộc: **giải nén zip ra thư mục tạm rồi chạy toàn bộ bộ kiểm trên bản giải nén đó**. Bước này bắt được cả ba lỗi dưới — không lỗi nào lộ ra khi chạy ở thư mục gốc.

**Lỗi 1 — `._pth` có dòng `..` làm cảnh "thiếu `chung.py`" không dựng được nữa.**
File `python314._pth` cần dòng `..` để `import chung` hoạt động (thư mục tool là cha của `python/`). Hệ quả phụ: interpreter đó **luôn** có thư mục tool thật trên `sys.path`, bất kể chạy từ đâu. Bộ kiểm `test_dong_goi.py` chép tool sang thư mục tạm rồi xoá `chung.py` để kiểm đường báo lỗi — nhưng Python vẫn tìm thấy bản gốc, nên tool khởi động bình thường và **3 phép kiểm đỏ**.
*Với máy con thì `..` = bản sao CỦA HỌ nên hành vi vẫn đúng; đây thuần tuý là vấn đề dựng cảnh trong bộ kiểm.*
Sửa: `chay_tool_o()` chạy qua `runpy.run_path` với `sys.path` đã **loại thư mục tool thật** (giữ nguyên phần còn lại). Lần sửa đầu đặt `sys.path[:] = [thu_muc]` trần → xoá luôn thư viện chuẩn → `runpy` không nạp nổi `pkgutil`, 4 phép kiểm đỏ vì lý do khác hẳn.

**Lỗi 2 — loại `bug.md` khỏi zip làm tài liệu nói dối và bộ kiểm đỏ.**
Ban đầu tôi coi `bug.md` và `CLAUDE.md` là "tài liệu nội bộ, không phát cho người dùng cuối". Nhưng `BAN_GIAO.md` có mục **"Dành cho người bảo trì"** trỏ thẳng tới chúng, và `tests/test_tai_lieu.py` đối chiếu **số mục** trong `bug.md`. Trên bản giải nén, file không tồn tại → tài liệu chỉ tới hư không, bộ kiểm đỏ. Sửa: **đóng kèm cả hai**.

**Lỗi 3 — `_lp("D:")` : kỳ vọng của bộ kiểm sai, không phải tool sai.**
Phép kiểm khẳng định `len(_lp("D:")) > 7`. Đo thật:
```
cwd tren D:  ->  \\?\D:\tools_goi_project_capcut
cwd tren C:  ->  \\?\D:\                            (dung 7 ky tu)
```
Cả hai **đều đúng** — `D:` nghĩa là *thư mục hiện hành của ổ D*, và khi tiến trình đang ở ổ C thì thư mục đó là gốc. Kỳ vọng `len > 7` chỉ tình cờ đúng khi chạy từ ổ D. Sửa: kiểm tính chất **thật sự** cần (bug #23) — kết quả phải bắt đầu bằng `\\?\D:\`, tức không để nguyên chuỗi `D:`.

**Lỗi 4 (phát hiện thêm khi mô phỏng máy con) — trình xử lý lỗi tự chết.**
Cả `goi_project_capcut.py` lẫn `xem_tien_trinh.py` kết thúc bằng `except Exception: traceback.print_exc(); input("Enter de dong...")`. `input()` **ném EOFError khi stdin đã đóng** (bộ lập lịch, đường ống, chuyển hướng) → người dùng thấy **hai traceback chồng nhau** và lỗi THẬT ở trên bị đẩy khuất. Sửa: bọc `try/except (EOFError, KeyboardInterrupt)`. Bộ kiểm mới `tests/test_xu_ly_loi.py` chạy cả hai file với `stdin=DEVNULL` và bắt buộc **≤ 1 traceback**.

- **Kết quả:** zip 84,8 MB / 77 file, CRC sạch, giải nén ra chạy **24/24 bộ kiểm đạt**. Mô phỏng máy con (giải nén + bấm `.bat` với PATH chỉ còn `system32`): tool khởi động, dùng đúng Python đi kèm, hiện đúng bản 1.1.0.
- **Bài học:**
  - **Kiểm trên BẢN GIẢI NÉN, không phải bản gốc.** Ba lỗi trên đều vô hình ở thư mục phát triển. Bản gốc có mọi thứ ở đúng chỗ nó quen; bản giải nén mới là thứ người dùng nhận.
  - **Đóng gói làm thay đổi môi trường chạy, nên nó có thể làm ĐỎ những phép kiểm vốn xanh** — và mỗi lần đỏ phải hỏi "tool sai hay kỳ vọng sai?" trước khi sửa. Ở đây 3/4 lần là **kỳ vọng sai**.
  - **Đừng loại tài liệu ra khỏi gói nếu tài liệu khác trỏ tới nó.** Một tài liệu chỉ tới file không tồn tại còn tệ hơn không nhắc gì.
  - **Trình xử lý lỗi phải là đoạn code chắc chắn nhất trong chương trình.** Nó chạy đúng lúc mọi thứ đã hỏng; nếu nó cũng hỏng thì người dùng mất luôn thông tin duy nhất còn lại.


### 87. Thêm giao diện: `tkinter` không có trong bản embeddable, và quy tắc đa luồng bị chính tôi vi phạm hai lần
- **Ngày:** 2026-08-21
- **Mức độ:** 🟠 High (một lỗi chặn hoàn toàn, một lỗi làm giao diện chết ngay khi bấm nút)
- **Vị trí:** `giao_dien.py` (mới), `python/` (bổ sung tkinter), `goi_project_capcut.py` → `main(tuy_chon=None)`, `tests/test_giao_dien.py` (mới).

**Chặn 1 — bản Python embeddable KHÔNG có `tkinter`.**
Kiểm ngay trước khi viết dòng giao diện nào: `ModuleNotFoundError: No module named 'tkinter'`. Bản embeddable cố ý bỏ tkinter cho gọn. Phải chép tay từ bản đầy đủ **cùng phiên bản 3.14.6** (chép lệch bản sẽ hỏng theo kiểu rất khó đoán, nên script đối chiếu phiên bản trước khi chép):
```
Lib/tkinter/  ->  python/tkinter/     1,40 MB
DLLs/_tkinter.pyd                     0,07 MB
tcl/                                  5,32 MB
DLLs/tcl86t.dll                       1,75 MB
DLLs/tk86t.dll                        1,52 MB
```
Chép xong **vẫn hỏng**: `ImportError: DLL load failed while importing _tkinter`. Quét bảng import của `tcl86t.dll` không thấy gì lạ; so **toàn bộ danh sách `.dll`** giữa bản đầy đủ và bản embeddable mới ra thủ phạm: **thiếu `zlib1.dll`**. Tcl 8.6 cần nó. Thêm vào → tạo được cửa sổ thật. Tổng cộng **+10,2 MB**.

**Chặn 2 — tôi viết quy tắc rồi tự phạm ngay đoạn dưới.**
Ngay trong docstring của `giao_dien.py` tôi ghi *"tkinter KHÔNG an toàn đa luồng"*, rồi ở `_chay()` (chạy trên **thread phụ**) lại gọi `self.v_trim.get()`:
```
RuntimeError: main thread is not in main loop
```
Và `_tra_loi()` — cũng chạy trên thread phụ — cũng đọc biến tkinter. Sửa: **chụp toàn bộ giá trị form trên thread chính** vào `self.chup` trước khi khởi động thread; thread phụ chỉ dùng bản chụp.
**Rồi lỗi đó lặp lại trong chính bộ kiểm**: hàm `bam()` chạy ở thread phụ đọc `g.nut_copy["state"]` → đúng lỗi ấy. Sửa: bấm nút ngay trong vòng lặp chính, không dùng thread phụ.

**Thiết kế: giao diện KHÔNG viết lại logic.**
Nó thay `builtins.input` bằng hàm trả lời **theo NỘI DUNG câu hỏi** (không theo thứ tự — bẫy #10) và hướng `sys.stdout` vào ô Nhật ký, rồi gọi thẳng `G.main()`. Nhờ vậy giao diện và dòng lệnh **là một**, không thể lệch hành vi. Bộ kiểm chốt điều này bằng cách cấm `giao_dien.py` chứa `shutil.copytree`, `subprocess.run`, `os.remove`, `os.walk` — nếu ai đó bắt đầu cài lại logic ở đó, bộ kiểm đỏ.
Ba ô tích đi vào `main(tuy_chon=...)`; **mặc định khi không truyền vẫn là bật cả ba**, giữ nguyên hành vi mà 10 lần chạy trên project thật đã dùng.
Nút `2) TIẾN HÀNH COPY` chính là câu `Tien hanh? (y/N)` của tool — thread phụ **dừng ở `threading.Event`** cho tới khi người dùng bấm.

- **Cách kiểm chứng:** `tests/test_giao_dien.py` (30 phép kiểm) — gồm phép kiểm **chạy trọn một lượt** trên draft giả: dựng form, bấm QUÉT, chờ tool hỏi, bấm TIẾN HÀNH, rồi xác nhận có thư mục xuất + có `_BAO_CAO_THIEU.txt` + không traceback + `sys.stdout` đã được trả lại.
- **Bài học:**
  - **Kiểm ràng buộc nền TRƯỚC khi viết code dựa trên nó.** Nếu viết xong giao diện mới phát hiện embeddable không có tkinter thì phải chọn giữa vứt bỏ công sức hay đổi cả phương án đóng gói. Một lệnh `import tkinter` mất 2 giây đã trả lời được.
  - **Khi một `.pyd` báo "DLL load failed", đừng chỉ soi phụ thuộc trực tiếp — hãy SO danh sách file giữa bản chạy được và bản không chạy được.** Cách đó tìm ra `zlib1.dll` trong một bước, trong khi đọc bảng import không thấy.
  - **Viết một quy tắc vào chú thích không làm ta tuân theo nó.** Tôi ghi "tkinter không an toàn đa luồng" rồi vi phạm hai lần trong cùng một phiên. Thứ ngăn được là **bộ kiểm chạy thật**, không phải lời nhắc.
  - **Giao diện tốt nhất là giao diện không có logic riêng.** Mọi dòng logic đặt ở đó là một dòng sẽ lệch khỏi bản dòng lệnh theo thời gian — và người dùng sẽ gặp hai hành vi khác nhau cho cùng một việc.


### 88. Tự kiểm lần đầu + ẩn console — và yêu cầu "cài thư viện" hoá ra là việc KHÔNG tồn tại
- **Ngày:** 2026-08-21
- **Mức độ:** 🟡 Medium (không sửa bug; ghi lại vì cách diễn giải yêu cầu quyết định toàn bộ thiết kế)
- **Vị trí:** `tu_kiem_lan_dau.py` (mới), `giao_dien.py` → `CuaSoTuKiem`, `GIAO_DIEN.bat`, `tests/test_lan_dau.py` (mới).

**Yêu cầu như người dùng nói:** *"lần đầu click GIAO_DIEN.bat thì cài các thư viện, những lần sau vào thẳng giao diện."*

**Nhưng tool KHÔNG có thư viện nào để cài** — nó dùng thuần thư viện chuẩn (có `tests/test_khong_dependency.py` chốt điều đó), và Python đã nằm sẵn trong gói. Thứ `goi_project_capcut.bat` thật sự làm không phải "cài" mà là **kiểm tra Python chạy được**. Làm theo nghĩa đen sẽ ra một bước cài đặt rỗng.

**Việc đúng, giữ nguyên tinh thần yêu cầu:** lần đầu **tự kiểm toàn bộ gói** — thứ bảo vệ khỏi rủi ro thật của luồng zip→NAS→giải nén:
1. đủ file bắt buộc sau khi giải nén (8 file, liệt kê rõ tên thay vì đếm tổng)
2. nạp được 4 module của tool
3. tkinter tạo được cửa sổ
4. ffmpeg chạy được **và có encoder libx264**

Đo được: bước ffmpeg tốn **3,16 giây** — đó chính là thứ đáng bỏ qua ở lần sau. Lần đầu ~1–5 giây, lần sau **0,1 ms** (chỉ đọc dấu).

**Ba chốt an toàn cho cơ chế nhớ:**
- Dấu đặt **tên theo phiên bản** (`.da_tu_kiem_1.1.0.json`) → bản mới tự kiểm lại.
- Dấu **hỏng hoặc ghi "HONG"** = coi như chưa kiểm. Tin một dấu hỏng nguy hơn kiểm lại 5 giây.
- Tự kiểm **KHÔNG phải lớp bảo vệ duy nhất**: `kiem_ffmpeg_chay_duoc()` vẫn chạy mỗi lần chọn chế độ 4 (bug #72). Nhờ vậy ffmpeg bị cách ly *sau* lần kiểm đầu vẫn bị bắt đúng lúc. Có phép kiểm chốt cả hai điều này.
- Tự kiểm **chạy hết các bước dù bước đầu đã hỏng** — để người dùng thấy *hết* vấn đề trong một lần, thay vì sửa một cái rồi chạy lại để gặp cái tiếp theo.
- Dấu **bị loại khỏi zip** (`BO_QUA_TIEN_TO`). Nếu dấu đi theo gói, máy con giải nén ra sẽ bỏ qua tự kiểm **đúng lúc nó cần nhất**.

**Ẩn console — cân bằng giữa hai thứ đối nghịch.**
Ẩn ngay từ đầu thì mọi lỗi khởi động đều **im lặng**: người dùng bấm đúp, không thấy gì, không biết làm gì. Cách làm: **giữ console trong pha kiểm** (~1 giây), chỉ ẩn khi đã chắc chắn chạy được — `start "" pythonw.exe ...` rồi `exit /b 0`, không `pause` ở đường thành công.
Thêm `import tkinter` vào phép kiểm của `.bat`: nếu tkinter hỏng thì bắt được **lúc console còn hiện**, thay vì bật `pythonw` lên rồi không thấy gì.
Và chốt `sys.stdout is None`: dưới `pythonw` không có console nên `sys.stdout` có thể là `None`, mọi `print()` sẽ ném `AttributeError` ở chỗ không ngờ tới.

- **Cách kiểm chứng:** `tests/test_lan_dau.py` (28 phép kiểm). Đo console bằng **tiến trình thật**: `.bat` thoát sau **1,0 giây**, `pythonw.exe` tăng thêm 1, đầu ra rỗng.
- **Sai lầm trong phép đo (đáng ghi):** lần đầu đo bằng `subprocess.run(capture_output=True)` → **treo hết giờ**. Nguyên nhân: tiến trình `pythonw` tách ra **thừa kế đầu pipe**, nên `run()` chờ pipe đóng — tức chờ người dùng đóng giao diện. Không phải lỗi `.bat`. Sửa: ghi ra **file** thay vì pipe.
- **Bài học:**
  - **Khi yêu cầu dựa trên một tiền đề sai, phải kiểm tiền đề trước rồi nói thẳng — đừng làm theo nghĩa đen.** "Cài thư viện" nghe hợp lý nhưng ở đây là việc không tồn tại; làm theo sẽ ra một bước rỗng, còn *ý* đằng sau ("lần đầu chuẩn bị, lần sau vào thẳng") thì vẫn đúng và đáng làm.
  - **Mọi cơ chế "nhớ để lần sau bỏ qua" đều phải trả lời được: bỏ qua rồi thì ai còn canh?** Ở đây câu trả lời rõ ràng — lớp kiểm ffmpeg ở `main()` vẫn nguyên. Không có câu trả lời đó thì cơ chế nhớ chính là một bug đang chờ.
  - **Ẩn giao diện lỗi là làm hỏng khả năng gỡ rối của người dùng.** Ẩn console là đúng, nhưng chỉ sau khi đã chắc chắn không có gì cần nói.
  - **Tiến trình con thừa kế pipe của cha.** Muốn đo "chương trình cha thoát nhanh không" thì đừng dùng pipe — nó biến phép đo thành phép chờ đứa con.


### 89. `GIAO_DIEN.bat` chẩn đoán SAI: thiếu file `.py` bị báo thành "máy chưa có Python"
- **Ngày:** 2026-08-21
- **Mức độ:** 🔴 High (máy con đi sai đường 3 phút rồi vẫn hỏng, không còn manh mối nào)
- **Vị trí:** `GIAO_DIEN.bat` — thứ tự các phép kiểm.

**Triệu chứng:** máy con giải nén thiếu `chung.py`, bấm đúp `GIAO_DIEN.bat`, console hiện:

```
! Ban Python di kem trong thu muc `python\` KHONG dung duoc cho giao dien.
  ...
  May nay chua co Python 3.8 tro len (hoac Python co nhung thieu tkinter)
  Cach sua (lam MOT LAN, khoang 3 phut): ... tai Python tu python.org ...
```

Máy có Python. Máy có `python\` đi kèm hoàn toàn tốt. **Không thứ gì trong thông báo là đúng.** Người dùng tải Python, cài, tích "Add to PATH", quay lại — vẫn hỏng y như cũ, và giờ thì hết ý tưởng.

**Nguyên nhân gốc — thứ tự kiểm.** `.bat` kiểm Python **trước**, bằng `python.exe -c "import sys,chung,tkinter"`. Câu lệnh đó gộp hai câu hỏi khác hẳn nhau vào một kết quả đúng/sai:
1. Python này chạy được không?
2. File của tool còn đủ không?

Thiếu `chung.py` làm **mọi** ứng viên Python trượt — bản đi kèm, `py -3`, `python` — nên `.bat` đi tới nhánh cuối và kết luận điều duy nhất nó biết nói: chưa có Python.

**Cách sửa:** đảo thứ tự — **kiểm file của tool trước, bằng `if not exist`, không đụng đến Python**:
```bat
set "THIEU="
if not exist "%~dp0giao_dien.py" set "THIEU=%THIEU% giao_dien.py"
if not exist "%~dp0chung.py"     set "THIEU=%THIEU% chung.py"
...
if not "%THIEU%"=="" goto :thieu_file
```
Sau bước đó, một phép kiểm Python trượt **thật sự** là vấn đề của Python.

Danh sách chỉ gồm những file mà **thiếu là không thể hiện nổi cửa sổ nào** — `giao_dien.py` nạp chúng ngay lúc import, dưới `pythonw` thì lỗi đó không có chỗ nào hiện ra. Các file còn lại (`cau_hinh.json`, `ffmpeg/`, `toi_uu_dung_luong.py` — nạp trễ) để **cửa sổ tự kiểm** báo: nó giải thích rõ hơn console nhiều.

**Hai thứ sửa kèm, cùng một gốc "đừng đoán":**
- Phép thử đổi từ `import chung,tkinter` thành **`import giao_dien`** — đúng chuỗi import mà `pythonw` sẽ chạy. Kiểm mỗi `tkinter` là chưa đủ: tkinter chạy được mà `chung.py` **hỏng** (có mặt nhưng sai cú pháp) thì `pythonw` vẫn chết im lặng.
- Khi mọi ứng viên Python đều trượt, `.bat` giờ **chạy lại phép thử KHÔNG chặn đầu ra** và in nguyên traceback, kèm ba nhánh đọc hiểu (`ModuleNotFoundError` → giải nén lại; `tkinter` → cài Python; không có dòng nào → chưa có Python). Bằng chứng thay cho phỏng đoán.
- `:xong` đổi `pause` → `pause` + `exit /b 1`.

- **Cách kiểm chứng:** `tests/test_lan_dau.py::test_chan_doan_dung_khi_thieu_file` — chạy **thật** `.bat` trong thư mục cố ý thiếu `chung.py`, chốt: báo "THIEU FILE", gọi tên `chung.py`, **không** chứa chuỗi "chua co Python", có "GIAI NEN LAI", mã thoát ≠ 0. Cộng phép kiểm tĩnh: vị trí `THIEU=` phải đứng **trước** `python\python.exe` trong file. Ba cảnh máy con thật (thiếu file nạp trễ / thiếu file nạp lúc import / file có mà hỏng) đều chạy qua zip đã đóng gói.
- **Bài học:**
  - **Một phép kiểm gộp nhiều nguyên nhân thì thông báo lỗi của nó chắc chắn sai ở phần lớn các nguyên nhân.** `import chung,tkinter` trả về một bit cho hai câu hỏi; cái nhãn gắn vào bit đó chỉ đúng cho một nửa.
  - **Kiểm cái rẻ và cái chắc chắn trước.** `if not exist` không cần interpreter, không thể hiểu sai, và loại hẳn một nhóm nguyên nhân trước khi nhóm sau được đem ra đoán.
  - **Chẩn đoán sai tệ hơn không chẩn đoán.** "Không rõ vì sao" khiến người dùng đi hỏi; "máy bạn chưa có Python" khiến họ đi làm một việc vô ích rồi mới hỏi — và lúc đó họ tin là đã loại trừ được Python.
  - **Phép thử phải chạy đúng thứ mà lúc thật sẽ chạy.** Thử `import tkinter` rồi lại khởi động `import giao_dien` là kiểm một thứ và chạy một thứ khác. Cùng lỗi hình thái với #72 (file có mặt ≠ chạy được).
  - Lỗi này lọt qua **27 bộ kiểm** vì `tests/test_bat.py` chỉ soi hai file `.bat` cũ, còn `test_lan_dau.py` chỉ đọc **nội dung** `GIAO_DIEN.bat` chứ chưa **chạy** nó ở cảnh thiếu file. Nó chỉ lộ ra khi mô phỏng máy con thật.


### 90. Cùng lỗi chẩn đoán sai của [#89] còn nằm ở `goi_project_capcut.bat` và `xem_tien_trinh.bat`
- **Ngày:** 2026-08-21
- **Mức độ:** 🟠 Medium-High (nhẹ hơn #89 vì console ở lại, nhưng vẫn dẫn sai đường)
- **Vị trí:** `goi_project_capcut.bat`, `xem_tien_trinh.bat` — cùng chỗ, cùng nguyên nhân với **#89**.

**Cách phát hiện:** sau khi sửa #89 ở `GIAO_DIEN.bat`, đi soi hai file `.bat` còn lại xem có cùng hình thái không. Có — cả hai đều mở đầu bằng `python.exe -c "import sys,chung;..."`, tức gộp "Python chạy được?" với "file tool còn đủ?" vào một kết quả đúng/sai.

**Vì sao nó ẩn lâu hơn #89:** trên máy **có** Python hệ thống, nhánh dự phòng `py -3 -c "import sys"` không import `chung`, nên nó qua được, tool chạy, và `goi_project_capcut.py` in ra thông báo tử tế của chính nó (khối `try/except` quanh `from chung import ...`, dòng 38 và 84–91). Người dùng vẫn được chỉ dẫn đúng — chỉ kèm thêm một câu vu oan "bản Python đi kèm KHÔNG chạy được".

Nhưng trên máy **không** có Python hệ thống — đúng cảnh mà bản đóng gói nhắm tới — cả ba ứng viên đều trượt và thông báo cuối cùng là "may nay chua co Python 3.8 tro len". Sai y hệt #89.

**Cách sửa:** chèn cùng khối kiểm file lên đầu, trước mọi thao tác Python:
```bat
set "THIEU="
if not exist "%~dp0goi_project_capcut.py" set "THIEU=%THIEU% goi_project_capcut.py"
if not exist "%~dp0chung.py" set "THIEU=%THIEU% chung.py"
if not "%THIEU%"=="" goto :thieu_file
```
Lớp bảo vệ trong `goi_project_capcut.py` **giữ nguyên** — nó vẫn cần cho người chạy thẳng file `.py`.

- **Cách kiểm chứng:** `tests/test_bat.py::test_chan_doan_thieu_file` — chạy **thật** cả **ba** file `.bat` trong thư mục cố ý thiếu `chung.py`, với `PATH` chỉ còn `system32`. Cùng bốn điều kiện cho cả ba: báo "THIEU FILE", gọi tên `chung.py`, **không** chứa "chua co Python", có chỉ dẫn sửa. Thêm `GIAO_DIEN.bat` vào danh sách kiểm định dạng ASCII/CRLF/`chcp` — trước nay bộ kiểm chỉ soi hai file `.bat` cũ.
- **Bài học:**
  - **Sửa xong một lỗi, đi tìm anh em của nó ngay** — cùng hình thái, khác vị trí. Ở đây chỉ mất một lần `grep "import sys,chung"` để tìm ra hai chỗ nữa.
  - **Một lớp bảo vệ tốt ở dưới có thể che lỗi ở trên rất lâu.** Thông báo tử tế trong `goi_project_capcut.py` làm cảnh "có Python hệ thống" trông ổn, nên lỗi chỉ lộ ra ở đúng cảnh máy con không có Python — cảnh khó gặp nhất khi ngồi trên máy cha.
  - **Bộ kiểm liệt kê tường minh thì phải rà lại mỗi khi thêm file.** `BAT = (...)` chỉ có hai tên; file `.bat` thứ ba ra đời mà không ai thêm vào, nên nó nằm ngoài mọi phép kiểm định dạng. Cùng loại với hai danh sách nội bộ lạc hậu ở **#88**.


### 91. Gọi `ttk.Style()` trước khi có `tk.Tk()` → tkinter ÂM THẦM đẻ ra một cửa sổ lạc; 3 ô đường dẫn chết, lần chạy đầu treo hẳn
- **Ngày:** 2026-08-21
- **Mức độ:** 🔴 Critical (mọi máy con, cú bấm đúp ĐẦU TIÊN sau khi giải nén)
- **Vị trí:** `giao_dien.py` → `main()`, dòng đầu tiên.

**Triệu chứng người dùng báo:** bấm "Chọn...", chọn thư mục xong, **ô nhập vẫn trống**. Gõ tay hoặc dán vào ô cũng vô ích.

**Nguyên nhân gốc.** `main()` mở đầu bằng:
```python
try:
    ttk.Style()          # <- khong master, va luc nay CHUA co tk.Tk() nao
except Exception:
    pass
```
`ttk.Style.__init__` → `setup_master(None)` → `tkinter._get_default_root()` gọi **không có** tham số `what` → nhánh `if _default_root is None: root = Tk()`. Nó **không ném lỗi mà TẠO** một `Tk()` — một cửa sổ thật, hiện trên màn hình, tên `tk`, 200×200. Đo:
```
truoc : tkinter._default_root = None
sau   : tkinter._default_root = <tkinter.Tk object .>
root lac: title='tk' | hien=1 | 200x200
```
Rồi `main()` tạo cửa sổ giao diện **thứ hai**. Mỗi `Tk()` là **một interpreter Tcl riêng**. `tk.StringVar()` gọi không `master=` bám vào `_default_root` = cửa sổ **lạc**, còn `ttk.Entry(..., textvariable=...)` thuộc interpreter của cửa sổ **thật**. Entry tra tên biến Tcl (`PY_VAR0`) trong interpreter CỦA NÓ, không thấy, nên tự tạo một biến rỗng khác. Dây `textvariable` **đứt cả hai chiều**:
```
bien.set('D:\thu muc\duong dan mau')
  bien.get()  = 'D:\thu muc\duong dan mau'   <- bien CO gia tri
  o.get()     = ''                             <- o VAN TRONG
```
Thêm `master=root`, cùng đoạn code đó: `o2.get() == 'D:\duong dan dung'`.

**Ba hậu quả nặng hơn cái người dùng nhìn thấy:**
1. **3 ô tích mục 4 chết.** `checkbutton state = ['alternate','alternate','alternate']` — tam trạng, không phải tích. Người dùng **bỏ tích mà tool vẫn đọc `True`** → vẫn nén lại toàn bộ footage.
2. **LẦN CHẠY ĐẦU TREO HẲN.** `r0.mainloop()` của cửa sổ tự kiểm chỉ thoát khi `Tk_GetNumMainWindows()==0`, mà root lạc vẫn sống → không bao giờ trả về. Đo: hết 20 giây, `GiaoDien` chưa từng được tạo. Bỏ dòng đó → `main()` trả về sau **1,40 s**. Zip bàn giao **không** chứa dấu tự kiểm, nên đây là cú bấm đúp đầu tiên của **mọi** máy con. Dấu vẫn được ghi trước lúc treo nên lần thứ hai mới vào được — đó là lý do trên máy dev không ai thấy.
3. Chọn project từ Listbox (thao tác chính) cũng không hiện gì; và một cửa sổ trắng `tk` nằm đè lên giao diện.

**Cách sửa:**
- Bỏ hẳn `ttk.Style()` trần. Theme đặt qua `_dat_theme(root)` → `ttk.Style(root).theme_use("vista")`, **luôn có master**.
- **Mọi** `StringVar/BooleanVar` truyền `master=` tường minh — bảo hiểm để lỗi không sống lại dù ai đó lỡ tạo root sớm.
- Không dùng `tkinter.NoDefaultRoot()`: với biến chưa có master nó ném `RuntimeError` và giao diện chết hẳn. Chỉ an toàn SAU khi đã truyền master cho tất cả.

**Vì sao 27 bộ kiểm (30 PASS / 0 FAIL) hoàn toàn mù.** `tests/test_giao_dien.py` tự gọi `tk.Tk()` rồi `GiaoDien(root)` và **không bao giờ gọi `giao_dien.main()`** — mà dòng lỗi chỉ nằm trong `main()`. Tk do chính bộ kiểm tạo trở thành `_default_root`, nên mọi biến bám đúng → PASS oan. **Bộ kiểm dựng đối tượng thay vì chạy điểm vào thì không thể thấy loại lỗi này.** Cùng hình thái với #89 hôm nay: chỗ duy nhất người dùng thật đi qua lại là chỗ không ai kiểm.

**BỐN GIẢ THUYẾT ĐÃ BỊ BÁC BỎ** (ghi lại để session sau đừng đi sửa nhầm — cả bốn đều *nghe* rất hợp lý):
- `str(Path(d))` làm hỏng đường dẫn → **sai**. Đúng với mọi dạng: `'D:/'→'D:\'` (không thành `'D:'`), UNC giữ đủ 2 backslash, tiếng Việt/khoảng trắng/path 402 ký tự nguyên vẹn. `askdirectory` trả **gạch xuôi** nên `str(Path(d))` là chịu lực — đừng "đơn giản hoá" thành `bien.set(d)`.
- `if d:` xử lý Cancel sai → **sai**. Cancel trả `''` (str, len 0), đúng cả hai chiều.
- Thiếu `parent=` làm hộp thoại mở sau lưng → **sai trên root sạch**. Đo bằng ctypes: no-parent và `parent=root` cho owner giống hệt, cùng thứ tự Z, cùng khoá modal. Hộp thoại chỉ gắn nhầm chủ **vì có root lạc**. (Vẫn nên ghim `parent=` tường minh, nhưng nó không phải thuốc.)
- Ctrl+V / Ctrl+A / Shift+Insert / tiếng Việt có dấu hỏng → **sai**, đo được đều chạy đúng.

- **Cách kiểm chứng:** `tests/test_giao_dien.py` — `test_o_duong_dan_hien_that` và `test_lan_dau_khong_treo` chạy `giao_dien.main()` **THẬT trong TIẾN TRÌNH RIÊNG** (bắt buộc: một `tk.Tk()` do bộ kiểm khác tạo trước sẽ che mất bug), cộng `test_chot_tinh_chong_tai_phat` đọc bằng **AST**. **Đã chứng minh bộ kiểm không xanh rỗng:** dựng lại đúng con bug trên một bản sao (thêm lại `ttk.Style()` trần, gỡ 8 chỗ `master=`) → **12 phép kiểm hoá đỏ**, `55 PASS / 12 FAIL`; trên bản đã sửa `67 PASS / 0 FAIL`.
- **Bài học:**
  - **Một thư viện có thể "giúp" bạn bằng cách tạo ra thứ bạn không xin.** `_get_default_root()` tạo cửa sổ thay vì báo lỗi. Quy tắc rút ra: **không gọi bất cứ thứ gì của tkinter/ttk trước khi tự tay tạo `Tk()`**, và luôn truyền `master=`.
  - **Hỏng mà không có exception là loại hỏng đắt nhất.** Không traceback, không log, giao diện vẫn vẽ ra, nút vẫn bấm được — chỉ là mọi giá trị đi lạc sang một interpreter khác. Không có gì để grep, không có gì để đọc.
  - **Bộ kiểm phải chạy ĐÚNG ĐIỂM VÀO mà người dùng chạy.** Dựng `GiaoDien(root)` trong tiến trình sạch là kiểm một chương trình KHÁC với chương trình được bàn giao. 30 PASS / 0 FAIL trong khi ứng dụng hỏng hoàn toàn ngoài đời.
  - **Trạng thái toàn cục ẩn (`_default_root`) do thứ tự dòng lệnh quyết định.** Một dòng vô hại ở đầu hàm đổi hành vi của mọi dòng phía sau.
  - **Ghi lại cả những giả thuyết BỊ BÁC BỎ.** Bốn giả thuyết trên đều hợp lý và đều sai; không ghi thì session sau sẽ tốn đúng ngần ấy công để loại trừ lại, hoặc tệ hơn là "sửa" một thứ đang đúng.

### 92. Ô "dò theo tên" nuốt im lặng đường dẫn sai, và `_bat_dau()` không kiểm đầu vào — chọn nhầm thư mục mẹ làm treo cứng máy
- **Ngày:** 2026-08-21
- **Mức độ:** 🔴 High
- **Vị trí:** `giao_dien.py` → `_bat_dau()`; `goi_project_capcut.py` → chỗ đọc "Thu muc/o de do" và `index_by_names`.

**Bốn lỗi ở cùng một đường dữ liệu — thứ người dùng gõ vào ô số 3 và ô số 2:**

**(a) `.strip('"')` áp lên CẢ chuỗi thay vì từng phần tử.** Windows 11 "Copy as path" (Shift+chuột phải) cho ra đường dẫn **có nháy kép**. Dán hai thư mục ra `"A";"B"` → strip cả chuỗi chỉ gỡ được hai dấu ngoài cùng → tách theo `;` ra `['A"', '"B']` → **cả hai root đều hỏng**.

**(b) Root sai bị bỏ hoàn toàn, không một chữ nào.** `index_by_names` bỏ qua root không tồn tại (`if not isdir_safe(root): continue`) và trả về rỗng trong 0,00 giây. Rồi tool in `--- THIEU (khong tim thay o bat ky o nao) ---`. **Đó là nói dối:** nó chưa quét ở đâu cả. Người dùng đi tìm một file vẫn còn nằm nguyên đó. Vi phạm thẳng checklist "không `except: pass` che lỗi; đếm mọi thất bại".

**(c) Nhãn dạy người dùng gõ SAI.** Giao diện in `O phat hien: C:\, D:\, G:\` — nối bằng **dấu phẩy**, trong khi bộ đọc tách bằng **`;`**. Ví dụ duy nhất họ nhìn thấy lại là ví dụ sai; gõ theo thì cả chuỗi thành MỘT đường dẫn rác → về lại (b). Và lời nhắc `[Enter = tat ca o]` cũng sai: `fixed_drives()` **chỉ** lấy ổ DRIVE_FIXED, ổ mạng và USB **không** được quét (cố ý, xem #27/#58) — nhưng `HUONG_DAN_GOI_PROJECT.md` lại viết "Enter = quét mọi ổ (C:/D:/E:/W:...)", trong đó `W:` chính là ổ mạng.

**(d) `_bat_dau()` chỉ kiểm `is_dir()` và "khác rỗng".** Hai hậu quả đo được:
- Chọn nhầm **thư mục mẹ** (`...\com.lveditor.draft`) — thao tác tự nhiên nhất — thì `choose_draft()` in "Thu lai." rồi hỏi lại, `_tra_loi` trả lời **y hệt** → **vòng lặp vô hạn ~33.000 vòng/giây, RAM +18 MB/giây, cửa sổ Not Responding, chỉ End Task mới thoát.**
- Ô 2 gõ `"D:"` → `tuyet_doi_that` chưa có, `abspath` âm thầm nối vào thư mục làm việc → **gói đổ thẳng vào chính thư mục công cụ**, và tool vẫn in "XONG. Ban tu chua DU." Đây là **#23 sống lại ở cửa vào giao diện**.

**Cách sửa:**
- `chung.py` thêm `tuyet_doi_that()` — chặn `"D:"`, `"D:Videos"`, tên trần, và `"\192.168.1.214\e"` (một backslash, dạng do shell nuốt mất một dấu, #9). **Không** tự sửa bằng `abspath()`: sửa âm thầm chính là cơ chế của #23, phát hiện thì phải **BÁO TO**.
- `giao_dien.py`: `_lam_sach_ds_duong_dan()` strip nháy kép **từng phần tử**, coi xuống hàng là dấu ngăn, khử trùng. Dùng `splitlines()` **chứ không** `.replace("\n", ";")` — viết literal sẽ phá `D:\news` thành rác. Chỉ strip nháy **kép**: thư mục tên `Kho 'B'` là hợp lệ trên Windows.
- `_bat_dau()`: chặn thư mục không có `draft_content.json` (dùng `isfile_safe`, **không** `Path.is_file()` — draft ở path 663 ký tự sẽ bị chặn oan); chặn ô 2 không tuyệt đối / là file / là chính thư mục tool; cảnh báo (`askyesno`, không chặn cứng) các thư mục ô 3 không tồn tại.
- `_tra_loi()`: chốt chống lặp phổ quát — cùng một câu hỏi quá 3 lần thì ném lỗi thay vì quay vòng.
- `goi_project_capcut.py`: strip nháy từng phần tử; nếu **cả chuỗi** là một thư mục có thật thì **không tách** (tên thư mục được phép chứa `;`); liệt kê root bị bỏ; khử trùng root (đo: 3 lần lặp → 3723 thư mục/0,130 s xuống 1241/0,038 s); và dòng THIEU nói rõ **đã dò bao nhiêu thư mục**, hoặc "CHUA DO O DAU CA".
- Nhãn nối bằng `"; "` cho khớp bộ đọc, thêm dòng cam nói rõ ổ mạng/USB không được quét; sửa `HUONG_DAN_GOI_PROJECT.md`.

- **Cách kiểm chứng:** `tests/test_giao_dien.py::test_bat_dau_phai_chan_dau_vao_xau` — ma trận 6 đầu vào xấu, mỗi cái phải hiện hộp thoại VÀ **không khởi động thread nào**; cộng một hàng hợp lệ phải cho chạy. `test_lam_sach_ds_duong_dan` chốt 6 cặp, trong đó có `D:\reports;E:\news` (bắt lỗi `.replace("\n",";")`) và UNC giữ đủ 2 backslash.
- **Bài học:**
  - **"Không tìm thấy" và "chưa tìm" là hai kết luận khác nhau**, và gộp chúng lại là nói dối với người dùng theo hướng tệ nhất: họ đi tìm thứ vẫn còn đó. Bất kỳ báo cáo "thiếu" nào cũng phải kèm **đã kiểm bao nhiêu**.
  - **Ví dụ mà giao diện in ra CHÍNH LÀ tài liệu.** In dấu phẩy trong khi bộ đọc tách bằng chấm phẩy là tự dạy người dùng gõ sai, rồi phạt họ bằng sự im lặng.
  - **Chuẩn hoá phải áp lên TỪNG PHẦN TỬ, không lên cả chuỗi.** `normpath` cả chuỗi nhiều đường dẫn chỉ giữ backslash kép ở vị trí 0 → phần tử UNC thứ hai mất một backslash → `_lp` ra **sai ổ hoàn toàn**.
  - **Trả lời tự động cho `input()` biến "hỏi lại" thành vòng lặp vô hạn.** Người thật sẽ sửa câu trả lời; máy thì lặp y nguyên. Mọi cầu nối input tự động phải có bộ đếm chống lặp.


### 93. Nút "Dừng dò" đổi nhãn thành "Đã huỷ." ngay, rồi quét tiếp 25,8 giây nữa
- **Ngày:** 2026-08-21
- **Mức độ:** 🔴 High
- **Vị trí:** `giao_dien.py` → `_dung_do()`; `goi_project_capcut.py` → `index_by_names()`, `collect_refs()`, `main()`.

**Triệu chứng:** bấm "Dừng dò" giữa pha dò theo tên. Nhãn đổi thành "Đã huỷ." **ngay lập tức**. Nhưng đo bằng bộ đếm thư mục: bấm ở giây thứ 8, tool quét thêm **~261.000 thư mục trong 25,8 giây nữa**. Trên ổ mạng còn lâu hơn nhiều.

**Nguyên nhân gốc:** `_dung_do()` chỉ đặt `tra_loi_tien_hanh = "n"` rồi `cho_tien_hanh.set()`. Cờ đó chỉ được đọc **khi tool chạy tới câu hỏi "Tiến hành?"** — tức là sau khi đã quét xong. Không một vòng lặp nào trong `main()` có mốc huỷ. Nút không nối với thứ gì đang chạy.

**Cách sửa:** truyền một `nen_dung: () -> bool` (là `threading.Event.is_set`) xuống, và cắm mốc ở **sáu** pha nặng: `collect_refs` (đo 17,73 s trên project NAS thật), vòng `bo_bytes` chế độ 4, Pass 1, vòng quét của `index_by_names`, vòng `size_of`, và cửa vào `plan_replacements` (từng treo 75 s — #28).

Bốn chi tiết quyết định, mỗi cái đều suýt sai:
1. **Đọc `nen_dung` ở ĐẦU `main()`.** Chỗ đọc `tuy_chon` sẵn có (`_tc`) nằm **bên trong** `if input("Chon 1 hoac 4") == "4"` **và** trong nhánh `else` của phép kiểm ffmpeg. Cắm ở đó thì nút **câm hoàn toàn** ở chế độ nguyên bản, hoặc khi ffmpeg máy con hỏng (đo: thừa 36,77 s và 46,62 s).
2. **`collect_refs` phải NÉM, `index_by_names` thì `break`.** Kết quả một phần của `collect_refs` là **tai hoạ**: refs thiếu → media đang dùng không nằm trong `refd` → `cleanup_unused` **xoá thật** rồi báo cáo vẫn ghi "ĐỦ". Chính `iter_json_files` cũng ném chứ không trả một phần, đúng vì lý do đó. Còn `idx` một phần chỉ làm `resolved` nhỏ đi, không hỏng gì.
3. **Phải `break` cả vòng ngoài `for root in roots`.** Trên ổ cục bộ giá chỉ ~3 thư mục, nhưng nếu root sau là host SMB chết thì riêng `isdir_safe(root)` chặn **21,03 s**. Đo: có break ngoài 0,010 s / quên 21,057 s. Vì thế mốc kiểm đặt **TRƯỚC** `isdir_safe`, không phải sau.
4. **Đặt `co_huy` TRƯỚC `cho_tien_hanh`** trong `_dung_do`, nếu không thread phụ tỉnh dậy trước khi thấy cờ và nhãn cuối lại thành "Xong.".

**Vẫn KHÔNG huỷ được (nói thật, đừng hứa):** một lời gọi `scandir`/`stat` **đang treo** trên SMB — Python không có timeout cho I/O filesystem (#25/#28/#37), đo được 21,03 s mỗi host ở lần chạm đầu. Mốc huỷ nằm *giữa* các thư mục, không cắt được lời gọi đang chạy. Câu được phép nói: *"thường dưới 1 giây; ổ mạng lạnh có thể vài giây."*

- **Cách kiểm chứng:** `tests/test_dung_do.py` (50 phép kiểm, đã đăng ký vào `BO_KIEM`). Đo bằng **SỐ ĐẾM thư mục** chứ không bằng đồng hồ — đồng hồ sẽ chớp tắt trên máy khác. Đo được: không huỷ 801 thư mục, huỷ sau 5 → **6 thư mục**.
- **Giả thuyết ĐÃ BỊ BÁC BỎ:** *"chỉ `break` vòng trong sẽ bắt phải quét hết các root sau"* — **sai**. Giá thật chỉ là một lần liệt kê tầng đầu mỗi root. Ghi lại để phiên sau đừng tốn công "sửa" một thứ không hỏng.
- **Bài học:**
  - **Nút bấm phải nối với thứ đang chạy, không phải với một cờ sẽ được đọc lúc nào đó.** Đổi nhãn ngay rồi làm tiếp 25 giây là một dạng nói dối giao diện.
  - **Huỷ giữa chừng thì kết quả một phần có được phép tồn tại hay không phụ thuộc vào NGƯỜI ĐỌC nó sau đó.** Cùng một cơ chế huỷ, chỗ này `break` là đúng, chỗ kia `break` là mất dữ liệu.
  - **Một hằng số đọc từ `tuy_chon` nằm trong nhánh `if` thì nó chỉ tồn tại trong nhánh đó.** Đọc cấu hình ở đầu hàm, dùng ở khắp nơi.

### 94. `_da_quet` lấy số từ bộ đếm tiến độ (mỗi 3000) — bản vá của [#92] đang nói dối ngay khi vừa viết xong
- **Ngày:** 2026-08-21
- **Mức độ:** 🔴 High (bug ĐANG SỐNG, không phải hệ quả của việc thêm nút huỷ)
- **Vị trí:** `goi_project_capcut.py` — dòng in `--- THIEU ... ---`.

**Triệu chứng:** mục #92 sửa dòng THIẾU để nó nói *"đã dò N thư mục"* thay vì khẳng định suông. Nhưng `N` lấy từ `_da_quet[0]`, mà biến đó chỉ được `on_progress` cập nhật khi `scanned % 3000 == 0`. Hậu quả đo được:

| Thực tế quét | Báo cáo in ra |
|---|---|
| 1.501 thư mục | **"CHUA DO O DAU CA"** |
| 4.971 thư mục | "đã dò **3000** thư mục" |
| 776 thư mục | **"CHUA DO O DAU CA"** |

**55/61 thư mục gốc thật trên máy này có dưới 3000 thư mục con** — nghĩa là với người dùng gõ một thư mục cụ thể vào ô 3 (đúng thứ ta vừa khuyên họ làm ở #92), báo cáo gần như **luôn** nói "chưa dò ở đâu cả" trong khi vừa dò xong.

**Nguyên nhân gốc:** biến dùng để **in tiến độ cho vui mắt** bị dùng làm **nguồn số liệu cho báo cáo**. Hai mục đích khác nhau, hai yêu cầu về độ chính xác khác nhau: tiến độ được phép thưa, báo cáo thì không.

**Cách sửa:** bỏ hẳn `_da_quet`. `index_by_names` nhận thêm `thong_ke` (dict ghi ngược ra) và ghi `quet` = `scanned` THẬT, cùng `da_dung`, `goc`, `loi`. Dòng THIẾU đọc từ đó. `on_progress` quay về đúng vai trò: chỉ in.

- **Cách kiểm chứng:** `tests/test_dung_do.py::t2` — dựng cây 501 thư mục (dưới ngưỡng 3000), chốt `on_progress` **không được gọi lần nào** mà `thong_ke["quet"]` vẫn > 250. Nếu `on_progress` được gọi thì chính phép kiểm mất ý nghĩa, nên nó chốt cả điều đó.
- **Bài học:**
  - **Sửa một lời nói dối bằng một con số thì con số đó phải đúng.** #92 sửa đúng ý nhưng lấy nhầm nguồn, nên chỉ đổi lời nói dối này lấy lời nói dối khác — và lần này còn khó thấy hơn vì đã có một con số trông rất thuyết phục.
  - **Bộ đếm để hiển thị và bộ đếm để kết luận phải là hai thứ.** Cái đầu được phép thưa, làm tròn, bỏ nhịp. Cái sau thì không.
  - Bug này **không** do người dùng báo và **không** do bộ kiểm nào bắt — nó lộ ra vì đi soi lại đường đi của chính bản vá vừa viết. Đáng làm mỗi khi vá xong một mục về "báo cáo nói dối".

### 95. Huỷ xong, nhãn cuối cùng vẫn là "Xong." — không phân biệt được với một lần chạy thành công
- **Ngày:** 2026-08-21
- **Mức độ:** 🟠 Medium-High
- **Vị trí:** `giao_dien.py` → `_chay()`, `_dung_do()`, `_rut_hang_doi()`.

**Triệu chứng:** đo 5/5 lần — bấm "Dừng dò", nhãn hiện "Đã huỷ." được **12–66 giây** (đúng khoảng thời gian tool vẫn đang quét), rồi khi `main()` trả về thì `_chay` đặt `("xong", "Xong.")` **đè lên**. Trạng thái CUỐI CÙNG người dùng nhìn thấy là **"Xong."**.

Nghịch lý: sau khi cắm mốc huỷ, lỗi này **nặng hơn** chứ không nhẹ đi — "Đã huỷ." chỉ còn hiện **0,033–0,140 giây** rồi bị "Xong." đè. Cài mốc huỷ mà không sửa nhãn là biến một lỗi khó thấy thành một lỗi chắc chắn thấy.

Thêm ba chỗ cùng gốc:
- Bấm "Dừng dò" **lần thứ hai** hiện hộp thoại *"Đã bắt đầu copy rồi"* — chưa copy một byte nào. Do chốt cũ gộp "đã bấm COPY" với "vừa bấm HUỶ" làm một; chính cú bấm thứ nhất làm cả hai vế thành đúng.
- Sau khi huỷ, nút **"2) TIẾN HÀNH COPY" vẫn được bật** và mời người vừa huỷ đi bấm.
- Hộp thoại hứa *"lần sau chạy tiếp không phải làm lại"* — đo được là **copy lại từ đầu** và còn tạo bản trùng (`canh1_1.mp4`), gói phình gấp đôi.

**Cách sửa:** nhãn kết thúc phụ thuộc cờ huỷ (`"Da huy - chua copy gi ca."`); chốt lần bấm thứ hai đổi thành `if self.tra_loi_tien_hanh == "y"`; nút tự xám và đổi chữ "Đang dừng..." ngay khi bấm; `_rut_hang_doi` bỏ qua tin `cho_tien_hanh` nếu cờ huỷ đã bật; viết lại hộp thoại cho đúng sự thật. **Hai nhánh `except` giữ nguyên** — lỗi thật phải thắng nhánh huỷ, không được bọc `finally` bằng cờ huỷ rồi che mất lỗi.

- **Cách kiểm chứng:** `tests/test_dung_do.py::t6, t7`.
- **Bài học:** **"Đã huỷ" mà kết thúc bằng nhãn của lần chạy thành công là một biến thể của lỗi báo cáo sai "đã xong".** Và phải đo trên **thứ người dùng NHÌN THẤY sau cùng**, không đo trên lệnh `set()` mà code gọi — code gọi đúng cả hai lần, chỉ là lần sau đè lên lần trước.

### 96. Giao diện gọi I/O có thể treo trên THREAD CHÍNH — NAS chết làm đông cứng cửa sổ 11–21 giây
- **Ngày:** 2026-08-21
- **Mức độ:** 🟠 Medium-High — cùng hình thái với [#58], khác vị trí
- **Vị trí:** `giao_dien.py` → `_bat_dau()` (**đã sửa**) và `_quet_thu_muc_me()` (**chưa sửa**).

**Triệu chứng:** phần kiểm ô 2 / ô 3 thêm vào `_bat_dau()` trong cùng đợt này gọi `isdir_safe` / `isfile_safe` ngay trên thread chính. Trỏ vào host SMB không nối được, một lời gọi chặn **11,10–21,06 giây**: Windows dán nhãn "Not Responding", và đúng lúc đó nút "Dừng dò" đang **xám** — không có đường thoát nào ngoài End Task. Đo cả **ba** ô đều dính.

**Nguyên nhân gốc:** một phép kiểm được thêm vào *để bảo vệ người dùng* lại chạy ở đúng chỗ không được phép chặn. Python không có timeout cho I/O filesystem nên không cách nào cắt.

- **Cách sửa (đã cài cho `_bat_dau`):** thêm `_kiem_nhanh_duoc(p)` — trả `False` cho mọi đường dẫn UNC (`\\...` hoặc `//...`). Với UNC thì **bỏ qua phép kiểm trước** và để lỗi nổ ở `_chay()` trên thread phụ, nơi đã có sẵn nhánh dịch `OSError` sang tiếng Việt. Ổ cục bộ vẫn kiểm bình thường (chỉ tốn vài chục micro giây).
- **Cách sửa `_quet_thu_muc_me()` — ĐÃ CÀI ngày 2026-08-22 (xem mục #97):** nút "Quét thư mục mẹ..." vẫn chạy `scan_drafts_recursive` **trên thread chính** — đo thật `F:\AutoEdit\library` = 8,9–11,6 giây, Windows dán nhãn "Not Responding" 4,0 giây, không nút nào dừng được. Phải đẩy sang thread phụ + có mốc huỷ, giống pha dò.
- **Cách kiểm chứng:** `tests/test_giao_dien.py::test_khong_io_treo_tren_thread_chinh` — thay `isdir_safe`/`isfile_safe` bằng bản đếm, đặt cả ba ô là UNC, chốt **không lần chạm filesystem nào**.
- **Bài học:**
  - **Thêm một phép kiểm để bảo vệ người dùng vẫn có thể làm hại họ, nếu nó chạy sai chỗ.** Việc đầu tiên cần hỏi khi thêm bất kỳ lời gọi filesystem nào vào giao diện: *nó đang chạy trên thread nào, và nếu nó chặn 20 giây thì người dùng bấm được gì?*
  - **Sửa xong một lỗi thì đi tìm anh em của nó ngay** (quy tắc 3 của CLAUDE.md): một lần `grep` `_quet_thu_muc_me` là ra chỗ thứ hai cùng bệnh.


### 97. Hoàn tất [#96] — "Quét thư mục mẹ" đóng băng cửa sổ 19,6 giây, và một lỗi ĐANG SỐNG cùng chỗ
- **Ngày:** 2026-08-22
- **Mức độ:** 🟠 Medium-High
- **Vị trí:** `giao_dien.py` → `_quet_thu_muc_me()`; `goi_project_capcut.py` → `scan_drafts_recursive()`; `chung.py` → `mtime_an_toan()` (mới).

**Triệu chứng:** bấm "Quét thư mục mẹ..." trỏ vào ổ mạng thì cửa sổ **đông cứng 19,6 giây**, Windows dán nhãn "Not Responding" **14,6 giây**, và **mọi** cú bấm nút bị hoãn **19,3 giây** — kể cả nút X. Toàn bộ thời gian nằm trong **MỘT** khoảng chặn duy nhất của mainloop, nên không có kẽ nào để thoát.

**Và một lỗi ĐANG SỐNG ngay cạnh, nặng hơn:** `ds.sort(key=lambda x: x.stat().st_mtime)` dùng `Path.stat()` **trần**. `scan_drafts_recursive` **TÌM ĐƯỢC** draft nằm sau 260 ký tự (vì `is_draft_dir` đi qua `isfile_safe` → `_lp`), nhưng khoá sort thì không — nó ném `FileNotFoundError WinError 3`. Cả lệnh `sort` ném → rơi vào `except Exception` → giao diện hiện **"Không quét được"** và danh sách **RỖNG**, trong khi tool vừa tìm thấy đủ project. Thư mục mẹ dài là chuyện thường ngày trên NAS bàn giao.

**Cách sửa:**
- `chung.py` thêm `mtime_an_toan(p)` — đi qua `_lp`, trả `0.0` thay vì ném. Trả 0.0 chứ không ném vì đây chỉ là **khoá sắp xếp**: một project không đọc được thời điểm sửa thì cho xuống cuối danh sách, **không được làm hỏng cả danh sách**. Thay ở **cả bốn** chỗ, kể cả ba chỗ của đường dòng lệnh.
- `scan_drafts_recursive` nhận `nen_dung` + `on_error`, và **giữ nguyên kiểu trả về cũ** (list trần) khi gọi kiểu cũ — đường dòng lệnh không đổi một chút nào.
- Mốc huỷ đặt **TRƯỚC** `isdir_safe(parent)`: chính lời gọi đó chặn ~21 giây khi `parent` trỏ vào host SMB chết.
- `onerror=lambda e: None` → đếm và báo ra. Trước đây cả một nhánh cây biến mất mà giao diện vẫn nói "tìm thấy N project" — báo thiếu mà không ai biết ([#37]).
- Giao diện: quét ở thread phụ, kết quả về qua hàng đợi, **chỉ** `_rut_hang_doi` (thread chính) mới chạm tkinter.

**Hai chi tiết suýt sai, đều đo được:**
1. **KHÔNG được dùng lại `self.co_huy`.** Kịch bản thường ngày: bấm "Quét thư mục mẹ", thấy lâu nên bấm "Dừng dò", rồi bấm "1) QUÉT" để gói project khác. `_bat_dau()` có `co_huy.clear()` — nó xoá đúng cái cờ mà thread quét đang đọc, nên thread **HỒI SINH** và quét tiếp đến hết cây. Phải có `co_huy_quet` **riêng**.
2. **Cần SỐ PHIÊN quét.** Huỷ không cắt được lời gọi I/O đang chạy, nên kết quả phiên cũ vẫn sẽ về — chỉ là về muộn — và đè lên danh sách của phiên mới.

- **Cách kiểm chứng:** `tests/test_giao_dien.py` (99 phép kiểm). Đo bằng **SỐ NHỊP `after` chạy được trong lúc quét**, không bằng giây — con số đó không đổi theo tốc độ máy. **Chứng minh bắt được lỗi:** 6 đột biến cho #96, tất cả đều hoá đỏ.
- **Bài học:**
  - **Một hàm đi qua `_lp` và một hàm không, dùng chung trên một tập dữ liệu, là một quả bom hẹn giờ.** `is_draft_dir` tìm thấy thứ mà `stat()` không đọc nổi — và thứ vỡ ra không phải một dòng lỗi mà là **cả danh sách bị vứt**.
  - **Cờ huỷ dùng chung giữa hai pha thì pha này sẽ xoá cờ của pha kia.** Mỗi pha một Event.
  - **Huỷ không phải là dừng.** Lời gọi I/O đang chạy vẫn chạy tới cùng, nên mọi kết quả về sau khi huỷ đều phải kèm số phiên để biết còn dùng được không.

### 98. Hoàn tất [#25] mục (c) — canh gác phát hiện treo NAS, sau khi BỐN tín hiệu "hiển nhiên" đều bị đo là SAI
- **Ngày:** 2026-08-22
- **Mức độ:** 🔴 High (chống lại lần mất 2 tiếng đã xảy ra)
- **Vị trí:** `canh_gac.py` (mới), `goi_project_capcut.py` → `main()`.

**Bối cảnh:** #25 ghi lại một lần tool treo vĩnh viễn giữa hai file content khi ghi qua NAS — mất 2 tiếng, không một thông báo. Mục (c) để lại watchdog "chưa cài, vẫn cần người vận hành quyết định". Lý do để lại: **#25 đã báo động giả hai lần**.

**Đo lại, và cả bốn tín hiệu trực giác đều SAI:**

| Tín hiệu | Số đo bác bỏ |
|---|---|
| "Log không đổi > 15 phút" | Log chỉ in mỗi 25 clip; gặp cụm file lớn thì im lặng 20+ phút là **bình thường** |
| "Thấy 0 tiến trình ffmpeg" | Phiên **khoẻ mạnh** có **19 cửa sổ "0 ffmpeg"** trong 7,35 giây; một pha hợp lệ không có ffmpeg nào suốt **51,6 giây** |
| "Tiến trình CHA không đọc/ghi" | Bộ đếm I/O là của **riêng từng tiến trình**, không cộng từ con lên cha. Đo: cha tiêu 0,344 s CPU trong khi **cả cây** tiêu 406,4 s — chênh **1180 lần** |
| "Có thay đổi = còn sống" | **Bẫy nặng nhất:** nhịp đập của chính tool ghi `_opt_index.json` ra đích mỗi 60 giây. Lúc **đã treo**, bộ đếm GHI vẫn tăng **49 byte/giây** → luật này **không bao giờ** kích hoạt trên tool thật |

**Thiết kế cuối:**
- Đo **cả cây tiến trình** bằng **Job Object** (`CreateJobObjectW` + `AssignProcessToJobObject`): bộ đếm của nó cộng dồn cả tiến trình **đã chết** nên **đơn điệu tuyệt đối**. Lấy mẫu cây thì bỏ sót **74–96%** I/O của ffmpeg — ffmpeg là tiến trình ngắn, sinh-và-chết giữa hai lần lấy mẫu, mà phần lớn lượng ghi lại dồn vào lúc đóng file ngay trước khi thoát. Có bản dò cây làm dự phòng, kèm `dict pid → bộ đếm cuối` để tổng không **tụt** khi một ffmpeg thoát (đo: 16% khoảng đo có delta âm ở phiên khoẻ mạnh).
- Tín hiệu là **hợp của ba nhóm**, không được bỏ nhóm nào: byte (read+write+**other**), số thao tác, và CPU. Mỗi nhóm đều có một pha khoẻ mạnh làm nó đứng yên: quét metadata NAS làm byte đọc/ghi đứng yên **93% thời lượng** (SMB metadata chỉ tăng `Other*`); copy lên NAS làm CPU đứng yên **6,7 giây**; metadata cục bộ thì chỉ CPU nhúc nhích.
- Quyết định bằng **NGƯỠNG KHỐI LƯỢNG** trong cửa sổ 60 giây, không phải "có thay đổi": `(read+other) ≥ 64 KB` hoặc `write ≥ 1 MB` hoặc `≥ 200 thao tác` hoặc `CPU ≥ 1,0 s`.
- Cảnh báo ở **5 phút**, kết luận nghi treo ở **15 phút**. **KHÔNG bao giờ tự giết tiến trình** — #25 đã từ chối phương án đó, và đo được cái giá: dừng ở pha **mã lại** thì không mất công (cache dùng lại được), nhưng dừng ở pha **copy** thì phải copy **lại từ đầu**. Văn bản cảnh báo nói rõ đang ở pha nào và dừng ở đó mất gì.
- **Thread RIÊNG**, không ghép vào nhịp đập: thread nhịp đập tự nó ghi ra NAS, nên đúng lúc NAS kẹt thì nó kẹt theo. Thân canh gác **tuyệt đối không gọi hàm filesystem nào** — chỉ ctypes/kernel32 (tra cứu bảng trong nhân, không chạm thiết bị).
- Bao **hết** `main()` chứ không riêng `optimize_package()`: đo được 601 lời gọi filesystem trong một lần chạy, **421 nằm ngoài** mọi vùng có nhịp đập.

- **Cách kiểm chứng:** `tests/test_canh_gac.py` (30 phép kiểm) — bơm **đồng hồ giả + cảm biến giả** rồi gọi `_mot_nhip()` trực tiếp, nên chạy trong mili giây thay vì chờ 15 phút. Số phép kiểm cho **"KHÔNG được báo"** nhiều hơn số cho "phải báo". **Chứng minh bắt được lỗi:** 5 đột biến cho canh gác, tất cả đều hoá đỏ.
- **Bài học:**
  - **Một canh gác kêu oan còn tệ hơn không có canh gác** — người dùng sẽ học cách phớt lờ, và lần treo thật sẽ không ai tin. Vì vậy phần lớn công sức phải đổ vào việc chứng minh nó **không** báo bậy.
  - **Bộ đếm phải ĐƠN ĐIỆU thì mới so sánh được theo thời gian.** Cộng các tiến trình "đang sống" cho ra tổng tụt xuống khi một tiến trình thoát.
  - **Thứ ta dùng để canh có thể chính là thứ làm ta mù.** Nhịp đập sinh ra để chống im lặng, nhưng lại tạo ra đúng lượng tín hiệu vừa đủ để một watchdog ngây thơ luôn thấy "còn sống".

### 99. `AssignProcessToJobObject` "thất bại" — thật ra là quên khai báo `argtypes`, và `except Exception` nuốt mất chẩn đoán
- **Ngày:** 2026-08-22
- **Mức độ:** 🟡 Medium
- **Vị trí:** `canh_gac.py` → `_k32()`, `_DoBangJob.bat_dau()`.

**Triệu chứng:** phép đo báo `Job Object tao+gan duoc: False`, chương trình âm thầm rơi về cách dò cây (kém hơn nhiều), và tôi suýt kết luận "máy này không dùng được Job Object".

**Nguyên nhân gốc:** `GetCurrentProcess()` trả **pseudo-handle -1**. Không khai báo `restype/argtypes` thì ctypes coi giá trị trả về là `c_int`, rồi khi truyền sang `AssignProcessToJobObject` nó ném `OverflowError: int too long to convert`. Lỗi đó bị `except Exception: return False` **nuốt gọn**, nên nó hiện ra dưới dạng "Windows không cho" thay vì "code sai".

Khai báo `argtypes` xong: `IsProcessInJob -> trong_job=False`, `AssignProcessToJobObject -> ok=True`. Hoàn toàn dùng được.

**Cách sửa:** khai báo `restype`/`argtypes` cho **mọi** hàm kernel32 được dùng, và ghi lý do thất bại vào `self.vi_sao` rồi **in ra** thay vì âm thầm xuống cách kém hơn.

- **Cách kiểm chứng:** `tests/test_canh_gac.py::t7` chốt `g.cach == "job"` — nếu tụt về dò cây thì bộ kiểm đỏ, không im lặng.
- **Bài học:**
  - **`except Exception` quanh một lời gọi ctypes biến lỗi lập trình thành "hệ điều hành không hỗ trợ".** Đúng loại nuốt lỗi mà checklist cấm, ở một hình thái mới: nó không giấu một sự cố, nó giấu **nguyên nhân** và khiến ta đi sửa nhầm chỗ.
  - **Với ctypes, khai báo `argtypes` không phải để cho đẹp** — thiếu nó thì pseudo-handle và con trỏ 64-bit hỏng âm thầm.
  - Khi một cơ chế "dự phòng" tự động kích hoạt, nó **phải nói ra vì sao**. Dự phòng im lặng = mất luôn cơ hội phát hiện rằng đường chính đáng lẽ chạy được.

### 100. Bộ kiểm giao diện tự sát: thêm ĐÚNG MỘT root Tk nữa làm `Tcl_AsyncDelete` giết cả tiến trình
- **Ngày:** 2026-08-22
- **Mức độ:** 🟡 Medium (lỗi của bộ kiểm, không phải của app — nhưng nó xoá kết quả nên rất dễ hiểu nhầm)
- **Vị trí:** `tests/test_giao_dien.py`.

**Triệu chứng:** thêm 3 phép kiểm cho #96 thì cả bộ kiểm chết bằng `Tcl_AsyncDelete: async handler deleted by the wrong thread`, kèm hàng chục dòng `Exception ignored ... Variable.__del__`. Vì crash xảy ra **trước** khi in dòng "KET QUA", `chay_het.py` báo **THẤT BẠI** — dù mọi phép kiểm đều đạt.

**Nguyên nhân gốc:** bộ kiểm tạo hơn mười root Tk trong **một** tiến trình (app thật chỉ tạo MỘT). Mỗi root để lại vài biến tkinter; đến lúc thu gom rác thì interpreter Tcl tương ứng đã bị huỷ, và Tcl bỏ ra lỗi giết tiến trình. Chạy **riêng lẻ thì không phép kiểm nào crash** — chính **SỐ LƯỢNG** root mới là nguyên nhân.

**Ba cách đã thử và KHÔNG đủ** (ghi lại để khỏi thử lại): huỷ `after` còn treo; giữ tham chiếu để việc dọn xảy ra trên thread chính; tách riêng phép kiểm có thread nền. Cách hiệu quả: **mọi phép kiểm tạo root Tk mới đều chạy trong TIẾN TRÌNH RIÊNG** qua `_chay_con()` — đúng khuôn mà `test_o_duong_dan_hien_that` đã dùng.

**Một sai lầm phụ, tốn công thật:** khi cô lập, tôi dùng regex `def test_X\(\):.*?(?=
def main\(\):)` để cắt hàm cũ. Nó **nuốt luôn 11 hàm** nằm giữa. Phát hiện được nhờ `NameError` lúc chạy, và khôi phục từ file zip bàn giao. **Đừng cắt code bằng regex `.*?` tới một mốc xa** — dùng mốc là hàm **kế tiếp**, hoặc tốt hơn là AST.

- **Cách kiểm chứng:** `tests/test_giao_dien.py` — 99 PASS / 0 FAIL, mã thoát 0, không một dòng `Tcl_AsyncDelete`. Cách chẩn đoán dùng được lần sau: chạy dồn dần 1, 2, 3... phép kiểm để tìm cái làm tràn (`scratchpad/chia_doi.py`).
- **Bài học:**
  - **Một bộ kiểm chết vì lý do của chính nó trông y hệt một bộ kiểm phát hiện lỗi thật.** Phân biệt được là nhờ mã thoát + dòng "KET QUA" biến mất, không phải nhờ đọc code.
  - **Chạy riêng thì qua, chạy chung thì chết** là dấu hiệu của trạng thái tích luỹ, không phải lỗi logic. Chia đôi theo **số lượng** chứ đừng soi từng phép kiểm.
  - **Nghịch lý đáng nhớ:** bật canh gác thì KHÔNG crash, tắt canh gác thì crash. Nghĩa là thứ trông như thủ phạm lại chỉ là thứ làm đổi thời điểm thu gom rác. Khi nghi một thành phần, hãy **tắt nó đi và đo lại** trước khi kết luận.


### 101. `doc_cau_hinh()` ưu tiên sai thứ tự làm bộ kiểm không giả lập được nữa
- **Ngày:** 2026-09-10
- **Mức độ:** 🟡 Medium (bắt được ngay bởi bộ kiểm; nhưng nếu lọt thì bộ kiểm mất khả năng dò một lớp lỗi thật)
- **Vị trí:** `goi_project_capcut.doc_cau_hinh()`.

**Triệu chứng:** sau khi thêm `loi/phien_ban.py` và cho `doc_cau_hinh()` tìm `cau_hinh.json` qua `tim_tai_nguyen()`, bộ `test_on_dinh.py` báo 2 FAIL: `van doc duoc gia tri that ben canh chu thich` (crf = 21 thay vì 19) và `VAN bao khoa la that su go nham` (log rỗng).

**Nguyên nhân gốc:** bộ kiểm giả lập bằng cách **đổi tạm `G.__file__`** sang một thư mục tạm rồi ghi `cau_hinh.json` giả vào đó. Bản vá cho `doc_cau_hinh()` **tìm qua `tim_tai_nguyen()` TRƯỚC**, mà hàm đó dựa trên `sys.executable`/`__file__` của **module `loi.phien_ban`** chứ không phải của `goi_project_capcut`. Nên nó luôn trả về file thật ở gốc repo, và phép giả lập bị vô hiệu — im lặng.

**Cách sửa:** đảo thứ tự. Thử **cạnh module trước** (giữ nguyên hành vi cũ, và đây là đường bộ kiểm giả lập), chỉ khi không thấy mới tìm qua `tim_tai_nguyen()` — đường này chỉ cần cho bản đóng gói .exe.

- **Cách kiểm chứng:** `python tests\test_on_dinh.py` → 20 PASS / 0 FAIL. Trước khi sửa là 18 PASS / 2 FAIL.
- **Bài học:**
  - **Thêm một đường tìm kiếm "tốt hơn" lên TRƯỚC đường cũ có thể giết chết điểm móc của bộ kiểm.** Khi một hàm đang được giả lập ở một điểm cụ thể (`__file__`), đường mới phải nằm **sau** làm dự phòng, không nằm trước.
  - Bộ kiểm FAIL sau một thay đổi tưởng là thuần tuý mở rộng → **nghi bản vá trước, đừng nghi bộ kiểm**. Ở đây bộ kiểm đúng, code sai.

### 102. Bộ kiểm "chỉ dùng thư viện chuẩn" không nhìn thấy package con → báo động giả và bỏ sót
- **Ngày:** 2026-09-10
- **Mức độ:** 🟡 Medium (hai lỗi ngược chiều trong cùng một bộ kiểm)
- **Vị trí:** `tests/test_khong_dependency.py`.

**Triệu chứng:** tạo package `loi/` xong, bộ kiểm báo FAIL: ``` `loi` trong ['giao_dien.py', 'goi_project_capcut.py', 'tu_kiem_lan_dau.py'] -> may con se vo bang ModuleNotFoundError```. Nhưng `loi` là module **của chính tool**, không phải thư viện ngoài.

**Nguyên nhân gốc:** `NOI_BO` được suy ra bằng `glob("*.py")` — chỉ thấy file `.py` **ở gốc**, không thấy thư mục package. Đây là **hai lỗi ngược chiều** trong một:
1. **Báo động giả:** import nội bộ bị coi là thư viện ngoài.
2. **Bỏ sót (nguy hiểm hơn):** `cac_file_tool()` cũng chỉ `glob("*.py")` ở gốc, nên **code trong `loi/` hoàn toàn không được kiểm** — một `import requests` đặt trong đó sẽ lọt qua.

**Cách sửa:** cả hai hàm nhận diện package con bằng dấu hiệu `__init__.py`, **tự suy ra** chứ không gõ tay — đúng tinh thần ghi chú sẵn có trong file ("danh sách gõ tay đã lạc hậu BA lần").

- **Cách kiểm chứng:** `cac_file_tool()` trả **9 file** thay vì 7, có `loi\__init__.py` và `loi\phien_ban.py`; `'loi' in NOI_BO` → True. `python tests\test_khong_dependency.py` → 4 PASS / 0 FAIL.
- **Bài học:**
  - **Một bộ kiểm báo động giả và một bộ kiểm bỏ sót thường là CÙNG một lỗi nhìn từ hai phía.** Sửa xong phải kiểm cả hai chiều: nó hết kêu oan chưa, VÀ nó có thật sự quét thứ mới không. Chỉ kiểm chiều thứ nhất thì rất dễ "sửa" bằng cách nới điều kiện cho qua.
  - Chuyển từ **module phẳng** sang **package** làm hỏng mọi chỗ dò file bằng `glob("*.py")` ở gốc. Trước khi tách package, tìm hết các chỗ đó.

### 103. `_EXIST_CACHE` dính giữa các lần chạy `main()` — chặn hàng đợi nhiều project
- **Ngày:** 2026-09-10
- **Mức độ:** 🔴 High (hỏng im lặng, cả hai chiều; chỉ lộ ra khi chạy nhiều project trong một tiến trình)
- **Vị trí:** `toi_uu_dung_luong.py` — `_EXIST_CACHE` / `_exists()`.

**Triệu chứng:** chưa xảy ra trên bản đang dùng. Phát hiện khi đánh giá khả năng làm hàng đợi nhiều project. **Đo thực nghiệm:**

```
_exists(f) -> False        (file chưa tạo)
[tạo file thật]
_exists(f) -> False        SAI - vẫn trả kết quả cũ
_exists(g) -> True         (file có thật)
[xoá file]
_exists(g) -> True         SAI - dính cả chiều ngược
```

**Nguyên nhân gốc:** `_EXIST_CACHE` là dict toàn cục **không có ai xoá**. Hai cache anh em đều có: `_PROBE_CACHE` có `xoa_cache_probe()` (gọi trong `optimize_package()`), `_LOI_PROBE` tự dọn trong `lay_loi_probe()`. Riêng cái này bị sót.

Ở chế độ dòng lệnh và giao diện một project, **mỗi lần gói là một tiến trình mới** nên cache chết theo tiến trình — không ai thấy vấn đề. Hàng đợi nhiều project gọi `main()` nhiều lần trong **cùng một tiến trình**: project sau thừa hưởng cache project trước → **báo thiếu file oan** (file đã có mà bảo không), hoặc **copy thất bại** (file đã xoá mà bảo còn).

**Cách sửa:** thêm `xoa_cache_ton_tai()` và gọi ở đầu `main()` — nơi **mọi** lần chạy đều đi qua — cùng với `xoa_cache_probe()`. Bọc `try/except` để thiếu module tối ưu không chặn chế độ 1.

- **Cách kiểm chứng:**
  - `tests\test_hang_doi.py` → 14 PASS / 0 FAIL. Chốt cả hai chiều dính, chốt `xoa_cache_ton_tai()` **không được là code chết**, chốt cảnh gác vẫn tắt trong `finally`.
  - E2E thật: gọi `main()` **hai lần liên tiếp trong một tiến trình** trên hai draft giả → cả hai ra **6 file, 5670 KB** giống hệt nhau.
- **Bài học:**
  - **"Mỗi lần chạy là một tiến trình mới" là một giả định ngầm, không phải sự thật vĩnh viễn.** Nó đúng với dòng lệnh, và che giấu mọi trạng thái toàn cục cho tới ngày có ai đó gọi hàm hai lần. Trước khi thêm tính năng chạy-nhiều-lần, phải **liệt kê hết biến toàn cục** và hỏi từng cái: "ai xoá mày?".
  - **Cache có anh em thì kiểm cả họ.** Ở đây ba cache cùng loại, hai cái có đường dọn, một cái không — chính sự không đồng đều đó là dấu hiệu bỏ sót, dễ thấy hơn là soi từng cái riêng lẻ.
  - Người viết code **đã lường trước** kịch bản này ở chỗ khác: `main()` bọc `_main_than()` trong `try/finally` để tắt cảnh gác, với ghi chú nói rõ *"ở chế độ GIAO DIEN thì `main()` trả về mà tiến trình VẪN SỐNG"*. Cùng một suy nghĩ, chỉ sót một biến.

### 104. Báo "CÒN THIẾU" oan vì không phân biệt lệch DO GÓI với lệch VỐN CÓ
- **Ngày:** 2026-09-10
- **Mức độ:** 🔴 High (báo cáo sai kết quả — người dùng đi tìm một lỗi không tồn tại, và có thể vứt một gói tốt)
- **Vị trí:** `toi_uu_dung_luong.verify_optimize()`.

**Triệu chứng:** gói DS1_124 xong, mọi chỉ số đều tốt — `THIEU: 0`, `COPY THAT BAI: 0`, giảm 94,42 GB, 1092 clip xử lý 0 thất bại — nhưng kết luận cuối lại là **`=> CON THIEU. XEM _BAO_CAO_THIEU.txt, bo sung roi chay lai.`** Nguyên nhân: 3 segment bị báo `BI LECH sau khi cat gon`.

**Nguyên nhân gốc:** cả 3 dòng là **cùng một material** (`8B4163E9`) lặp ở 3 file JSON. Đo thực tế:

| | duration | đoạn dùng | vượt |
|---|---|---|---|
| Draft **gốc** | 30,700s | 5,600 → 30,800s | **+0,100s** |
| Bản **gói** | 25,592s | 0,500 → 25,700s | **+0,108s** |

Đoạn dùng giữ **nguyên 25,200s** ở cả hai bên, offset dịch 5,600 → 0,500 (đệm 0,5s đầu) — **cắt hoàn toàn đúng**. Lệch tăng đúng **8 mili giây**, do `duration` của material đổi từ 30,700s xuống 25,592s (độ dài bản `_opt` thật) trong khi lệch gốc đã có sẵn.

Nói cách khác: **CapCut tự nó đã ghi lệch từ trước**, tool chỉ làm con số lệch nhích thêm 8ms rồi vượt ngưỡng. `verify_package()` đã có tham số `draft_dir` để loại trừ đúng loại "hỏng sẵn" này, nhưng `verify_optimize()` thì không.

**Cách sửa:** thêm `draft_dir` cho `verify_optimize()`; material nào **đã lệch sẵn** ở draft gốc thì xếp riêng vào `lech_san` (chỉ ghi nhận) thay vì `bad` (chặn kết luận).

**Một bẫy trong chính bản vá — ngưỡng phải THẤP hơn:** lần vá đầu tôi dùng cùng ngưỡng `> d + 100_000` cho cả hai hàm, và bản vá **không có tác dụng gì**: draft gốc lệch **đúng bằng** 100_000µs, tức `30800000 > 30800000` là `False` — nó vừa **lọt** qua phép kiểm. Phải hạ xuống `>= d + 90_000` thì mới nhận ra được. Dùng đúng một ngưỡng cho "phát hiện lỗi" và "nhận ra lỗi vốn có" là bản vá vô dụng.

- **Cách kiểm chứng:** trên dữ liệu THẬT (gói DS1_124 vừa chạy):
  - không truyền `draft_dir` → `bad = 3`, `lech_san = 0` (hành vi cũ, kết luận sai)
  - có truyền `draft_dir` → `bad = 0`, `lech_san = 3` (kết luận đúng)
  - `tests\test_lech_von_co.py` — chốt cả hai chiều và chốt cái bẫy ngưỡng.
- **Bài học:**
  - **"Hỏng sẵn từ trước" và "ta làm hỏng" là hai chuyện khác nhau, và chỉ phân biệt được khi ĐỐI CHIẾU VỚI BẢN GỐC.** `verify_package` đã học bài này (2325/2366 tham chiếu hỏng là cache CapCut tự sinh); `verify_optimize` thì chưa — cùng một bài học phải áp cho MỌI phép nghiệm thu, không chỉ cái đầu tiên.
  - **Một chỉ số xấu duy nhất kéo tụt cả kết luận thì phải soi nó trước khi tin.** Ở đây 3 dòng lệch làm hạ kết luận của một gói có 0 thiếu, 0 copy lỗi, 0 clip mã hỏng.
  - Khi một bản vá "không có tác dụng gì", **nghi ngưỡng/điều kiện biên trước khi nghi logic** — `>` và `>=` khác nhau đúng một trường hợp, và trường hợp đó lại chính là dữ liệu thật.

### 105. Tiếng Việt CÓ DẤU làm chết cả tiến trình trên máy ACP 1258
- **Ngày:** 2026-09-10
- **Mức độ:** 🔴 High (chết hẳn tiến trình, và **chỉ chết trên máy người dùng**)
- **Vị trí:** mọi `print()` — điểm vào `goi_project_capcut.py`, `giao_dien.py`, `xem_tien_trinh.py`.

**Bối cảnh:** chủ dự án yêu cầu đổi toàn bộ giao diện sang tiếng Việt **có dấu**. `SPEC_UI_UX.md` §7 đang ghi ràng buộc "phải không dấu", nên phải đo trước khi hứa.

**Đo được — bốn đường chữ đi ra, kết quả KHÁC NHAU:**

| Đường ra | Kết quả |
|---|---|
| Nhãn tkinter (Tcl) | **An toàn** — không qua stdout |
| Ô Nhật ký của giao diện | **An toàn** — chuỗi Python thuần |
| File báo cáo (`encoding="utf-8"`) | **An toàn** |
| Console chế độ dòng lệnh | **CHẾT** với cp1258 / cp1252 |

```
UnicodeEncodeError: 'charmap' codec can't encode character '\u1eaf'
```

`\u1eaf` là chữ `ắ`.

**Nguyên nhân gốc:** máy phát triển có `ACP 65001` (UTF-8) nên `print` chữ có dấu **không bao giờ lỗi**. Máy con Windows tiếng Việt mặc định là **ACP 1258** (hoặc 1252), ở đó `cp1258` không có bảng mã cho `ắ` → `charmap` codec ném → **chết cả tiến trình**. Đây đúng loại lỗi mà #68 đã cảnh báo, chỉ khác chiều: #68 là *đọc* đầu ra ffmpeg, #105 là *ghi* ra console.

**Ba cách đã thử** (ghi lại để khỏi thử lại):

| Cách | cp1258 | cp1252 | mặc định |
|---|---|---|---|
| không sửa gì | **chết** | **chết** | OK |
| `reconfigure(errors='replace')` | `C?t g?n` | `C?t g?n` | OK |
| **`reconfigure(encoding='utf-8', errors='replace')`** | **OK** | **OK** | **OK** |

**Cách sửa:** module mới `loi/bang_ma.py` với `ep_utf8()`, gọi **ngay đầu cả ba điểm vào, trước dòng `print` đầu tiên**. Giữ `errors="replace"` để một ký tự lạ chỉ thành `?` chứ không giết một lần gom đang chạy dở hàng chục phút. Hàm **không bao giờ ném** — dưới `pythonw` thì `sys.stdout` có thể là `None`, và một lỗi ở đó sẽ giết chương trình trước khi giao diện kịp hiện.

- **Cách kiểm chứng:** `tests\test_tieng_viet.py` — 14 PASS / 0 FAIL. Bộ kiểm chạy trong **tiến trình con** với `PYTHONIOENCODING=cp1258`; chạy trong chính tiến trình hiện tại là **vô nghĩa** (luôn PASS trên máy phát triển). Nó **chứng minh lỗi có thật trước**, rồi mới chứng minh cách sửa.
- **Bài học:**
  - **Một bộ kiểm bảng mã chạy trên máy phát triển là bộ kiểm rỗng.** Phải ép môi trường của máy đích (`PYTHONIOENCODING`) trong tiến trình con. Cùng bài học với #68 nhưng ở chiều ngược lại — **đọc** đã học rồi, **ghi** thì chưa.
  - **"Ngôn ngữ hiển thị" không phải một quyết định duy nhất.** Bốn đường ra có bốn kết quả khác nhau; ba an toàn sẵn, chỉ một cần vá. Kết luận "không dùng được tiếng Việt có dấu" là sai — chỉ đúng cho một đường.
  - `errors='replace'` **một mình là bẫy**: không chết nhưng ra `C?t g?n`, tức là hỏng âm thầm — loại tệ hơn chết hẳn.

### 106. Vẽ lại bảng trong chính handler chọn dòng → đệ quy vô hạn, cửa sổ treo cứng
- **Ngày:** 2026-09-10
- **Mức độ:** 🔴 High (treo cứng ngay khi thêm mục đầu tiên — không dùng được gì)
- **Vị trí:** `ui/cua_so_hang_doi.py` — `_chon_muc()` / `_ve_bang()`.

**Triệu chứng:** thêm một mục vào hàng đợi rồi gọi `root.update()` → **không bao giờ trả về**. Script E2E bị `timeout` với mã thoát **124**, không một dòng lỗi nào.

**Nguyên nhân gốc — vòng lặp bốn chặng:**

```
_ve_bang()  ->  selection_set()  ->  Tk sinh <<TreeviewSelect>>
     ^                                          |
     |                                          v
_ve_tat_ca()  <-------------------------  _chon_muc()
```

`_ve_bang()` xoá sạch bảng rồi dựng lại, nên phải `selection_set()` để giữ lại dòng đang chọn. Nhưng `selection_set` **sinh sự kiện** `<<TreeviewSelect>>`, và handler của nó gọi `_ve_tat_ca()` → lại `_ve_bang()`.

**Đếm được:** 39 lần `_chon_muc`, 21 lần `_ve_bang` trước khi bộ đếm chặn lại.

**Hai lần vá SAI trước khi tìm ra cách đúng** (ghi lại để khỏi đi lại):

1. **Cờ `_dang_ve` bọc quanh `_ve_bang()`** — không ăn thua. Tk gửi `<<TreeviewSelect>>` **trễ**, tới lúc `root.update()` xử lý hàng đợi sự kiện thì cờ đã trả về `False` từ lâu.
2. **Mở rộng cờ ra cả `selection_set()` ở `_luu_form()`** — vẫn treo, cùng lý do.

**Cách sửa đúng — bỏ hẳn nguyên nhân thay vì chặn triệu chứng:** `_chon_muc()` **không được gọi `_ve_bang()`**. Chọn một dòng KHÔNG làm đổi nội dung bảng, nên vẽ lại bảng ở đó vừa thừa vừa sinh vòng lặp. Nó chỉ cập nhật những thứ thật sự đổi: đầu form, nhật ký, trạng thái nút.

- **Cách kiểm chứng:** bọc `_chon_muc`/`_ve_bang` bằng bộ đếm ném khi vượt 20 lần. Trước khi sửa: 39/21. Sau khi sửa: **1/1**. E2E `root.update()` trả về bình thường, mã thoát 0.
- **Bài học:**
  - **Handler của một sự kiện KHÔNG được gọi thứ sinh ra chính sự kiện đó.** Với `Treeview`: `delete`, `insert`, `selection_set` đều sinh `<<TreeviewSelect>>`.
  - **Cờ chống tái nhập không cứu được sự kiện GỬI TRỄ.** Nó chỉ chặn được đệ quy đồng bộ. Tk xếp sự kiện vào hàng đợi và xử lý ở `update()`/`mainloop()`, lúc đó cờ đã tắt. Cách duy nhất chắc chắn là **không tạo ra vòng**.
  - **Treo có mã thoát 124 và KHÔNG một dòng lỗi** — khác hẳn crash. Khi một script GUI "chạy mãi không xong", nghi vòng lặp sự kiện trước khi nghi I/O chậm. Cách chẩn đoán nhanh nhất: bọc các hàm nghi ngờ bằng bộ đếm ném khi vượt ngưỡng.

### 107. CI đỏ 4 bộ trong khi máy phát triển 47/47 ĐẠT — bốn lỗi, bốn nguyên nhân khác nhau
- **Ngày:** 2026-09-11
- **Mức độ:** 🔴 High (CI đỏ ngay lần chạy đầu của bản phát hành v2.0.0)
- **Vị trí:** `tests/chay_het.py`, `tests/test_duong_dan.py`, `tests/test_dong_goi.py`, `tests/test_a7.py`, `.github/workflows/kiem_nhanh.yml`.

**Triệu chứng:** đẩy v2.0.0 lên GitHub, CI báo `CO 4 BO KIEM KHONG DAT`. Trên máy phát triển **47/47 ĐẠT**. Đúng rủi ro **R-05** đã ghi sẵn trong `tai_lieu/RISK.md`.

**Bốn nguyên nhân KHÁC NHAU — không có nguyên nhân chung:**

| Bộ | Nguyên nhân |
|---|---|
| `DUONG DAN` | Runner **bật sẵn LongPathsEnabled** → `os.path.isfile` cũng thấy file dài → phép **đối chiếu** (chứng minh `_lp()` có tác dụng) mất ý nghĩa. `_lp()` không hỏng. |
| `A7` | `assert ffmpeg` → `AssertionError` → mã thoát 1 → đọc là **THẤT BẠI**, trong khi sự thật là **không chạy được** vì máy thiếu ffmpeg |
| `DONG GOI` | So `str(tmp)` với đường dẫn đã `.resolve()`. Runner có `TEMP` là tên **ngắn 8.3** (`RUNNER~1`), `.resolve()` bung thành `runneradmin` → hai bên lệch |
| `QUET THU` | **bug #105 tái diễn ở chính bộ chạy test.** `subprocess.run(errors="replace")` biến ký tự lạ thành `\ufffd`; in ra console CI (cp1252) thì `charmap` ném → **cả bộ chạy chết**, dù bộ kiểm con đã ĐẠT |

**Một lỗi thứ năm, âm thầm hơn:** `MAX_BO_QUA=0` trong CI dựa trên ghi chú *"đã đo 2026-09-11: 43/43 ĐẠT khi không có ffmpeg"*. Con số đó **sai ngay từ đầu**: phép đo cũ chỉ giấu thư mục `ffmpeg/`, mà máy đo **có ffmpeg trong PATH** — nên `ff_paths()` vẫn tìm thấy và không bộ nào bỏ qua.

**Cách sửa:**

1. `chay_het.py` gọi `ep_utf8()` ngay đầu file.
2. `test_duong_dan.py`: phép đối chiếu chỉ **ghi nhận**, không chặn khi máy bật long path.
3. `test_dong_goi.py`: so với `Path(tmp).resolve()`.
4. `test_a7.py`: **bỏ qua có khai lý do** (mã thoát 2) thay vì `assert` chết.
5. Bốn bộ bỏ qua im lặng (`DEM`, `#38`, `NUOT LOI`, `REVERSE`) đổi sang khuôn `BO QUA: <lý do>`.
6. `MAX_BO_QUA` 0 → **7**, kèm cách đo đúng.

- **Cách kiểm chứng:** giả lập runner bằng cách giấu **CẢ** thư mục `ffmpeg/` **LẪN** ffmpeg trong PATH:
  ```
  mv ffmpeg ffmpeg_tam && PATH="$(echo "$PATH" | tr ':' 
' | grep -vi ffmpeg | paste -sd:)" python tests\chay_het.py
  ```
  Trước khi sửa: 4 THẤT BẠI + 1 LỖI CHẠY. Sau khi sửa: **`TAT CA DAT` (7 bộ bỏ qua, trong ngưỡng)**, và máy đầy đủ vẫn 47/47.
- **Bài học:**
  - **Giấu một nguồn tài nguyên là chưa đủ để mô phỏng máy sạch.** Giấu thư mục `ffmpeg/` mà quên ffmpeg trong PATH thì phép đo ra kết quả **ngược hẳn** — và con số sai đó đi thẳng vào cấu hình CI. Muốn mô phỏng máy thiếu thứ gì, phải chặn **mọi đường** nó có thể đến.
  - **"Phép đối chiếu" khác "phép kiểm".** Một dòng chứng minh *"không có X thì hỏng"* phụ thuộc vào môi trường; biến nó thành điều kiện bắt buộc là làm CI đỏ oan ở nơi môi trường khác.
  - **`assert` trong bộ kiểm là bẫy:** nó không phân biệt được *"chạy và sai"* với *"không chạy được"*. Bộ kiểm cần bỏ qua thì phải bỏ qua có khai lý do, không dùng `assert`.
  - **Bug đã sửa ở lõi vẫn sống trong công cụ.** #105 đã vá ở ba điểm vào của tool, nhưng `chay_het.py` — thứ chạy *quanh* tool — thì chưa. Khi sửa một lớp lỗi, phải hỏi *"còn chỗ nào cùng loại mà tôi chưa nghĩ tới?"*

**Lần sửa thứ hai (cùng ngày) — hai lỗi còn sót, cả hai là "sửa chưa tới nơi":**

| Bộ | Tôi đã sửa gì | Vì sao vẫn đỏ |
|---|---|---|
| `QUET THU` | `chay_het.py` gọi `ep_utf8()` | Chỉ sửa tiến trình **CHA**. Tiến trình **CON** tự in tiếng Việt và chết *trước* khi cha kịp làm gì |
| `DONG GOI` | Phép kiểm thứ nhất: `str(tmp)` → `Path(tmp).resolve()` | Phép kiểm thứ **HAI** vẫn so `(tmp / "giai_nen_tam")` với bản đã resolve. `.resolve()` trên thư mục **chưa tồn tại** không bung được tên ngắn 8.3 |

**Cách sửa lần hai:**
- `chay_het.py` truyền `PYTHONIOENCODING=utf-8:replace` xuống **mọi tiến trình con**. Đo được **15 file test** có chữ có dấu mà không gọi `ep_utf8()` — sửa ở một chỗ bảo vệ cả 15 file lẫn mọi file viết sau, thay vì thêm một dòng boilerplate vào từng file.
- `test_dong_goi.py`: resolve **thư mục CHA** rồi mới nối tên con, và đặt `sys._MEIPASS`/`sys.executable` bằng đường dẫn đã resolve.

**Kiểm chứng lần hai** — tái hiện lỗi trước, rồi chứng minh cách sửa:
```
PYTHONIOENCODING=cp1252 python tests\test_quet_thu.py   -> UnicodeEncodeError (tai hien dung loi CI)
PYTHONIOENCODING=cp1252 python tests\chay_het.py        -> ca hai bo DAT
+ giau ffmpeg + MAX_BO_QUA=7                        -> TAT CA DAT (7 bo qua)
may thuong                                          -> 47/47 DAT
```

**Bài học bổ sung — hai cái, đều về "sửa chưa tới nơi":**
  - **Sửa biến môi trường ở tiến trình cha KHÔNG chạm được tiến trình con.** `sys.stdout.reconfigure()` chỉ sống trong tiến trình gọi nó. Muốn con thừa hưởng thì phải truyền qua `env`.
  - **Sửa một nửa rồi tưởng xong là chính cái bẫy mục này cảnh báo.** Tôi sửa phép kiểm thứ nhất của `DONG GOI` mà bỏ qua phép kiểm thứ hai ngay dưới nó — trong cùng một hàm, cùng một loại lỗi. Khi sửa một chỗ, **grep cả file** xem còn chỗ nào cùng dạng.

---

## Checklist nhanh khi viết/sửa code (rút ra từ các bug trên)

**Đường dẫn trên Windows:**
- [ ] Long-path prefix: UNC → `\\?\UNC\server\...`; drive → `\\?\D:\...`. KHÔNG nối thẳng `\\?\` vào path bắt đầu `\\`.
- [ ] Hàm chuẩn hoá path phải idempotent (đã có `\\?\`/`\\.\` thì giữ nguyên).
- [ ] Dùng CÙNG một hàm `_lp` cho MỌI thao tác fs (copy, getsize, isfile, walk, copytree).
- [ ] Test UNC bằng loopback `\\localhost\C$\...` khi không có NAS.
- [ ] WinError 123 = cú pháp path sai → kiểm tra CẢ nguồn lẫn đích.
- [ ] `"D:"` KHÔNG phải gốc ổ — phải `"D:\"`. Thiếu backslash → drive-relative, nối âm thầm vào cwd (xem #23).

**Xử lý lỗi & báo cáo:**
- [ ] Không `except: pass` / `return False` che lỗi mà không đếm/không báo.
- [ ] Đếm mọi thất bại (copy_fail, skipped_items) và đưa vào báo cáo + console.
- [ ] Chỉ số "thành công/thiếu" đo trên KẾT QUẢ THỰC TẾ ở đích, không trên trạng thái trước khi hành động.
- [ ] Mặc định "CHƯA XONG" cho tới khi chứng minh xong; thông báo lỗi in đủ ngữ cảnh (nguồn + đích).
- [ ] Side-effect fail thì bước phụ thuộc không được tiếp tục như thể thành công.

**File .bat / encoding:**
- [ ] `chcp 65001 >nul` ngay sau `@echo off`, trước mọi comment.
- [ ] Comment trong `.bat` để không dấu (ASCII).

**Định dạng CapCut (draft lồng nhau):**
- [ ] Draft KHÔNG phẳng: `subdraft/<GUID>/` là draft đầy đủ, **lồng nhiều tầng**; còn được nhúng inline ở `materials.drafts[].draft`. Mọi xử lý (gom / đổi path / verify) phải ĐỆ QUY trên MỌI file `.json`.
- [ ] Gốc giải `##_draftpath_placeholder_..._##` và `./` = **tổ tiên gần nhất có `draft_meta_info.json` hoặc `sub_draft_config.json`**. `Timelines/<GUID>/` có `draft_content.json` nhưng KHÔNG phải root.
- [ ] GUID trong placeholder là hằng số `0E685133-18CE-45ED-8CB8-2904A212EC80` (giống nhau mọi project).
- [ ] Có **HAI** dạng placeholder: `##_draftpath_placeholder_..._##` và `##_subdraft_placeholder_..._##`. Xử lý/kiểm phải biết cả hai (xem #24).
- [ ] Chuỗi kết thúc bằng `.mp4/.wav/...` CHƯA CHẮC là đường dẫn: `material_name`, `materialName`, `extra_info` chỉ là nhãn. Lọc theo TÊN KHOÁ (`path`, `file_Path`, `source_path`) (xem #24).
- [ ] Khóa `file_Path` (sổ đăng ký) ghi dạng `./materials/...`; các khóa khác ghi dạng placeholder.
- [ ] Gom media vào `materials/` của TỪNG draft root → path sâu hơn → phải cảnh báo file vượt 260 ký tự.

**Đọc yêu cầu & kiểm tính hợp lý của kết quả:**
- [ ] Tách yêu cầu thành từng gạch đầu dòng, đánh dấu từng cái. "Hạ 4K / nén bitrate" = **hai** việc (xem #19).
- [ ] Có **phép thử vô lý**: dung lượng gói ≈ thời lượng timeline × bitrate mục tiêu. Lệch một bậc độ lớn → dừng lại truy nguyên nhân, KHÔNG đi giải thích tại sao nó hợp lý (xem #18, #19).
- [ ] Thao tác nặng (mã lại hàng nghìn clip, copy hàng trăm GB): **mã thử vài mẫu thật để dự báo dung lượng + thời gian TRƯỚC khi chạy**.
- [ ] Không phải tham chiếu nào cũng đáng gom: phân biệt timeline / kho / cache (xem #18).
- [ ] **Báo tiến độ/ETA phải lấy từ bộ đếm của chính tool** (`...N/M clip`), KHÔNG suy ra từ hiện vật trên đĩa: job `dup` chỉ copy chứ không mã lại nên đếm file `_opt` sẽ thổi phồng tốc độ (xem #24).
- [ ] Hai phép đo lệch nhau vài lần → **con số bi quan thường đúng**; đã lỡ báo số sai cho người dùng thì đính chính NGAY.
- [ ] **"Tiến trình còn sống" ≠ "đang chạy"**: đo `ReadTransferCount`/`WriteTransferCount`/CPU-time theo thời gian + đếm tiến trình con. Thấy `ffmpeg.exe` thì PHẢI kiểm `ParentProcessId` xem có đúng của mình không (xem #25).
- [ ] Pha dài chạy trên **ổ mạng** phải có **heartbeat** định kỳ — nếu không sẽ không phân biệt được "chậm" với "treo chết" (SMB treo vô hạn, Python không timeout I/O filesystem) (xem #25).

**Tối ưu dung lượng (mục 4 — mã lại media):**
- [ ] Một file media được giữ "sống" bởi NHIỀU nơi: content materials + sổ đăng ký `draft_materials` + sub-draft. Muốn bỏ được file gốc thì phải trỏ lại HẾT (xem #14).
- [ ] Một nguồn có thể sinh **NHIỀU** bản `_opt` (mỗi đoạn cắt một file) → bảng tra `setdefault(src, dest)` chỉ giữ 1 đích là SAI, làm sót bản gốc (xem #38).
- [ ] Nghiệm thu phải hỏi: **"còn bản gốc nào bị sổ đăng ký giữ sống không?"** — phân loại file trong gói thành `_opt`/gốc/khác rồi giải KHOÁ ĐƯỜNG DẪN (không so theo tên file) (xem #38).
- [ ] Chỉ đổi `source_timerange` khi ffmpeg thành công VÀ file đích có thật; thất bại thì giữ nguyên bản gốc và đếm vào báo cáo.
- [ ] **`returncode==0` + file tồn tại KHÔNG đủ**: phải `ffprobe` file kết quả và so ĐỘ DÀI với `span` yêu cầu (lệch > 0,6 s ⇒ coi là THẤT BẠI, giữ bản gốc). File cụt vẫn cho returncode 0 (xem #35).
- [ ] Sửa file media xong phải sửa luôn `duration` trong MỌI file JSON trỏ tới nó — CapCut tin JSON chứ không tin file (xem #35).
- [ ] Sau khi cắt phải tự kiểm: mọi segment nằm trong `[0, duration]` của material.
- [ ] Kiểm phần cắt bằng cách **so khung hình thật** (ffmpeg SSIM giữa bản gốc ở thời điểm cũ và bản cắt ở thời điểm mới) — chỉ so độ dài là không đủ để phát hiện lệch.
- [ ] SSIM PHẢI kèm **phép kiểm soát** (gốc-vs-gốc lệch cùng Δt) để biết ngưỡng nhiễu; cảnh động đúng hoàn toàn vẫn có thể chỉ ~0,55. Ưu tiên bằng chứng số học `source_timerange` (xem #25).
- [ ] SSIM đòi HAI ảnh **cùng kích thước**; clip đã hạ 4K phải scale về cùng size trước khi so, nếu không ffmpeg `Conversion failed` và phép đo trả rỗng (xem #33).
- [ ] Phân biệt **"phép đo thất bại"** (`None`/`?`) với **"kết quả xấu"** — đừng gộp cả hai vào nhóm "nghi ngờ", sẽ đi sửa sản phẩm đang đúng. Gọi công cụ ngoài thì luôn in `stderr` khi parse thất bại (xem #33).
- [ ] Đích là ổ mạng: ĐO tốc độ ghi thật trước; quyết định "cái gì cần copy" TRƯỚC khi copy; mọi decode/encode phải đọc từ bản nội bộ (xem #15).
- [ ] Coi "làm được 0 việc" (`0/0 clip`, `0 file se duoc thay`) là tín hiệu SAI, không phải chạy êm (xem #16, #26).
- [ ] **Thứ tự pha là một phần của tính đúng đắn**: `plan_package()` (lập kế hoạch copy) chạy TRƯỚC `repoint_registry()` nên KHÔNG tự thấy bản tối ưu → phải truyền `opt_by_src` cho nó, nếu không sẽ copy lại bản gốc đã bị thay (xem #26).
- [ ] Footage thường nằm NGOÀI folder draft (ổ khác/NAS) → `plan_replacements()` (chỉ lọc file trong draft) trả 0 là bình thường; phần đó phải chặn ở `plan_package()` (xem #26).
- [ ] Trước khi trả lời "dò trên tất cả ổ": kiểm `Get-PSDrive` xem có ổ MẠNG nào không — quét TB qua SMB có thể mất hàng giờ; file người dùng cố ý xoá sẽ khiến nó quét cạn vô ích (xem #27).

**Kiểm chứng:**
- [ ] Fix xong phải chạy test/E2E thật (không chỉ đọc code) — unit test hàm lõi + E2E luồng chính, gồm cả case lỗi (buộc fail để xem báo cáo đúng chưa).
- [ ] Cẩn thận khi test path Windows qua bash/`python -c`: backslash dễ bị nuốt. Dùng file test Python hoặc `chr(92)` thay vì gõ `\` trong shell.
- [ ] **Chứng minh "tự chứa" phải bằng cách ĐỔI CHỖ gói** (đổi tên/copy sang chỗ khác) rồi verify lại. Mở bằng CapCut trên chính máy gốc là bằng chứng GIẢ — path tuyệt đối vẫn resolve được ở đó.
- [ ] Verifier nghiệm thu nên viết **ĐỘC LẬP**, không import hàm của tool — dùng lại chính hàm bị lỗi thì lỗi không bao giờ lộ.
- [ ] **Bộ kiểm phải FAIL khi không có dữ liệu**: kết luận "đạt" bắt buộc kèm "đã kiểm N thứ" với N > 0. Quét 0 file mà báo PASS là lỗi nặng hơn báo FAIL sai (xem #36).
- [ ] `os.walk` **nuốt lỗi mặc định** → trên ổ mạng, mất kết nối biến thành "thư mục rỗng". Truyền `onerror=` và đối chiếu số file quét được với kỳ vọng (xem #37).
- [ ] Ping được + port 445 mở **KHÔNG** nghĩa là đọc được: NAS có thể trả `WinError 71` (hết phiên SMB) (xem #37).
- [ ] Đừng chốt quy tắc từ vài mẫu: đo trên hàng nghìn mẫu thật và so ít nhất 2 giả thuyết cạnh tranh (xem #12).

**Chạy tool tự động (nạp input thay người dùng):**
- [ ] KHÔNG truyền path UNC qua **bất kỳ kênh nào đi qua shell** — stdin redirect, file answers, **và cả `argv`** (đều nuốt backslash → output nằm sai ổ, xem #9 và #34). Dùng Python wrapper, path bằng biến (`chr(92)`), monkeypatch `input`.
- [ ] Script báo "không thấy file" mà bạn tin là có → in `repr()` đường dẫn ở cả 3 mức (argv → join → sau `lp()`) TRƯỚC khi nghĩ tiến trình chạy chưa tới (xem #34).
- [ ] Trả lời `input()` theo NỘI DUNG câu hỏi, KHÔNG theo list cứng — số bước đổi tùy có file thiếu (bước "dò theo tên" chỉ hiện khi thiếu).
- [ ] Sau khi chạy: LUÔN verify output nằm đúng đích thật (đếm `materials/` qua `_lp`, so `draft_fold_path`), không tin dòng "XONG". Kiểm dòng "Se copy ... vao <đích>" có đúng 2 backslash UNC.
