# Hướng dẫn — Công cụ GÓI PROJECT CAPCUT (registry-aware + subdraft-aware)

Gom toàn bộ media của một draft CapCut vào 1 folder tự chứa để bàn giao/nhân bản.

> ✅ **Hỗ trợ "Dự án con".** Nếu project của bạn có nhập project khác vào để gộp
> (folder `subdraft/`), tool sẽ gom cả media của các dự án con đó — kể cả khi
> chúng lồng nhau nhiều tầng. Xem mục "Dự án con" ở dưới.

> ⚠ **CHẠY TRÊN MÁY CÓ FOOTAGE.** CapCut quản lý media qua **sổ đăng ký
> `draft_materials`** — footage thường nằm rải nhiều ổ (E:/U: local máy editor, V: NAS).
> Tool đọc đúng sổ này và gom hết. Nhưng nó **chỉ gom được file đang truy cập được
> trên máy đang chạy** → phải chạy trên **máy editor gốc** (nơi có đủ các ổ đó), KHÔNG
> chạy trên máy khác đã mất đường dẫn. File nào không thấy → ghi vào `_BAO_CAO_THIEU.txt`.

## Cài 1 lần
Cần **Python 3.8+**. Nếu chưa có: tải ở python.org → khi cài **tích "Add Python to
PATH"**. Kiểm tra: mở PowerShell gõ `python --version`.

## Chạy
- Cách 1: bấm đúp **`goi_project_capcut.bat`**.
- Cách 2: mở PowerShell tại folder này, gõ `python goi_project_capcut.py`.

## Các bước công cụ hỏi
1. **Chọn project**: nó liệt kê các project ở thư mục CapCut mặc định (nếu có) — gõ số
   để chọn. Vì công ty lưu project ở **folder riêng trên ổ D:/W:**, dùng:
   - **T** = quét cả một **thư mục mẹ** rồi liệt kê mọi project bên trong. Ví dụ dán
     `D:\EDIT NHAN BAN AUTO\PROJECT` → nó hiện tất cả project trong đó để gõ số chọn.
     (Đây là cách tiện nhất cho quy trình của bạn.)
   - **P** = dán THẲNG đường dẫn 1 folder draft (folder chứa `draft_content.json`,
     vd `D:\EDIT NHAN BAN AUTO\PROJECT\REAL73\REAL73 PROJECT`).
2. **Folder xuất ra**: Enter để dùng mặc định (`<tên>_PORTABLE` cạnh project), hoặc
   nhập nơi khác.
3. **Dò media (tự động 2 lớp):**
   - **Pass 1** — kiểm đúng đường dẫn gốc trong draft.
   - **Pass 2** — file nào không thấy (vì đã relink / chuyển sang ổ D:/E:), tool **tự
     dò theo TÊN FILE**. Khi được hỏi "Thư mục/ổ để dò": **Enter** = chỉ quét các ổ
     **trong máy** (C:/D:/G:... — ổ mạng và USB **KHÔNG** được quét tự động, vì quét
     hàng TB qua mạng có thể mất hàng giờ). Footage nằm trên ổ mạng thì phải **nhập
     thư mục cụ thể**, nhiều thư mục **cách nhau bằng dấu `;`** (không phải dấu phẩy),
     vd `D:\FOOTAGE;E:\NHAC;\\192.168.1.214\e\VOICE`.
   - Thư mục nào không tồn tại sẽ được **liệt kê ra**, không bị bỏ qua im lặng.
   - Tool dừng quét sớm ngay khi đã tìm đủ.
4. Nó báo **bao nhiêu file tìm thấy / thiếu + dung lượng**, hỏi xác nhận → gõ `y`.
   "Thiếu thật sự" = **đã dò N thư mục mà không thấy** (tool in rõ N). Nếu nó ghi
   "CHƯA DÒ Ở ĐÂU CẢ" thì nghĩa là không thư mục nào bạn nhập quét được — hãy kiểm
   lại đường dẫn, đừng vội kết luận là file đã mất.

## Mục 4 — Tối ưu dung lượng
Sau khi nhập folder xuất ra, tool hỏi chế độ:

```
CHE DO GOI:
  1. NGUYEN BAN - copy y nguyen (an toan nhat, nhung nang)
  4. TOI UU DUNG LUONG - cat gon footage dai (chi giu doan dung)
       + ha 4K/nen bitrate H.264 theo khung hinh + bo file thua/mo coi/lich su
```

Gõ `4` để bật. Cần **ffmpeg** (đã có sẵn trong `ffmpeg\bin\`). Ba việc nó làm:

| Việc | Cách làm | Ghi chú |
|---|---|---|
| **Cắt gọn footage dài** | Lấy đúng khoảng bạn dùng trên timeline, đệm 0,5 s hai đầu, rồi dời `source_timerange` của mọi segment cho khớp | Chỉ cắt khi dùng < 85% file và tiết kiệm > 8 MB |
| **Hạ 4K / nén bitrate** | Bề rộng đích = khung hình × mức phóng to lớn nhất clip đó dùng × 1,1. H.264 CRF 20 + AAC 192k | Chỉ hạ khi nguồn rộng hơn nhu cầu > 15% |
| **Bỏ file thừa** | Xoá media không còn JSON nào tham chiếu + `*.bak`, `*.tmp` | Chỉ đụng trong các thư mục `materials/` |

**Kết quả đo thật** trên `DS3 - BÀI 6`: 0,60 GB so với 0,95 GB — **giảm 37%**, 48 clip xử lý, 0 thất bại.

**Những điều cần biết:**
- Project **gốc KHÔNG bị đụng tới**. Mọi thao tác chỉ diễn ra trên bản xuất.
- Media bị **mã lại** nên tốn thời gian CPU. Bù lại tool không đẩy bản gốc lên đích
  nữa (tiết kiệm rất nhiều nếu đích là ổ mạng).
- Clip nào mã lại thất bại thì **tự động giữ nguyên bản gốc** — không mất hình, và
  được ghi vào báo cáo.
- Vì đã cắt gọn, bản giao **không còn phần footage thừa** để cắt lại. Nếu bên nhận
  cần dựng lại từ đầu thì hãy dùng chế độ 1.
- Tool tự kiểm riêng phần này: mọi đoạn dùng phải nằm trong độ dài clip. Lệch là báo
  `CANH BAO: N segment BI LECH` và kết luận **CÒN THIẾU**.

## Kết quả
- Folder tự chứa: media nằm trong `materials/`, đường dẫn đã viết lại thành
  **tương đối** → di chuyển folder đi đâu cũng chạy.
- File **`_BAO_CAO_THIEU.txt`**: liệt kê file còn thiếu (nếu có) → bổ sung rồi chạy lại.

## Làm sao biết project nào có dùng Dự án con?
Tool **tự nhận biết và nói cho bạn**, không cần bạn nhớ:

- **Ở danh sách chọn project** (kể cả khi dùng **T** để quét cả thư mục mẹ), project
  nào có dự án con sẽ có nhãn ở cuối dòng:
  ```
   1. DS1_103  [35.5 phut]        sua 2026-08-10 17:08  << 3 DU AN CON (+1 long ben trong)
   2. DS3 - BÀI 6  [5.3 phut]     sua 2026-07-07 20:01
  ```
- **Sau khi chọn**, tool liệt kê rõ từng cái và **nhập từ project nào**:
  ```
    >> CO DU AN CON: 4 cai (+ 42 clip ghep)
       - Intro Text
         (nhap tu: D:/1363/Video Capcut/CapCut Drafts/Intro Text)
           - DS3-005
             (nhap tu: D:/1363/Video Capcut/CapCut Drafts/DS3-005)
  ```
  Project không dùng thì ghi thẳng `>> Project nay KHONG dung du an con.`
- Thông tin này cũng được ghi đầu file `_BAO_CAO_THIEU.txt` để lưu hồ sơ bàn giao.

**Cách tool phân biệt** — trong `subdraft/` có lẫn 2 thứ khác hẳn nhau:

| Loại | Dấu hiệu | Ý nghĩa |
|---|---|---|
| **Dự án con** | có `draft_meta_info.json` riêng | Bạn đã **nhập một project khác** vào để gộp. `draft_fold_path` trong đó chỉ ra project nguồn. |
| **Clip ghép** | chỉ có `sub_draft_config.json` | Bạn gộp vài clip **trong chính project này** — không phải dự án con. |

Rất nhiều project có folder `subdraft` nhưng **rỗng** → không dùng cả hai. Tool chỉ
đọc thư mục để phân loại nên chạy rất nhanh, không phải mở file JSON lớn.

## Dự án con (subdraft)
CapCut lưu mỗi dự án con thành một **draft đầy đủ riêng** trong `subdraft/<GUID>/`,
có `draft_content.json` riêng trỏ media bằng đường dẫn tuyệt đối — và chúng có thể
**lồng nhau nhiều tầng**. Tool quét đệ quy toàn bộ, gom media cho từng tầng và viết
lại đường dẫn trong chính file khai báo nó.

- Media dùng chung bởi nhiều dự án con được **liên kết cứng (hard link)** → không
  nhân đôi dung lượng. Ổ đích không hỗ trợ thì tự động quay về copy thường.
- Vì mỗi dự án con có `materials/` riêng nên đường dẫn sâu hơn. Nếu có file vượt
  **260 ký tự**, tool sẽ cảnh báo → hãy chọn folder xuất ra có đường dẫn NGẮN
  (ví dụ `D:\GOI\<tên project>`), đừng để sâu trong nhiều lớp thư mục.

## PHÉP THỬ VÀNG (kiểm nhanh)
⚠ **Mở bản xuất bằng CapCut ngay trên máy gốc KHÔNG chứng minh được gì** — nếu còn
sót đường dẫn cũ thì trên máy đó nó vẫn mở được bình thường, lỗi chỉ lộ ra sau khi
đã bàn giao. Cách kiểm đúng:

1. **Đổi tên** folder kết quả (hoặc copy sang ổ/máy khác) rồi mới mở bằng CapCut.
2. KHÔNG đòi relink/locate media = **ĐẠT**, bàn giao được.
3. Còn đòi relink = còn thiếu file → xem `_BAO_CAO_THIEU.txt`, bổ sung rồi chạy lại.

Trước đó hãy đọc dòng cuối trong `_BAO_CAO_THIEU.txt`: chỉ khi ghi
`Khong thieu. Ban tu chua DU` thì mới coi là xong.

## Lưu ý
- Công cụ KHÔNG sửa project gốc, chỉ tạo bản copy mới.
- Media có thể vài GB → cần đủ dung lượng ổ đích; copy hơi lâu là bình thường.
- Ảnh bìa/thumbnail hỏng được báo riêng và KHÔNG chặn bàn giao (không ảnh hưởng
  video xuất ra); chỉ media video/audio thiếu mới bị tính là "còn thiếu".
