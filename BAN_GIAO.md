# GÓI PROJECT CAPCUT — Tài liệu bàn giao

**Phiên bản 2.0.0** · Python 3.14.6 đi kèm · ffmpeg đi kèm

Tài liệu này dành cho **người nhận công cụ**. Cách chạy từng bước xem
`HUONG_DAN_GOI_PROJECT.md`. Ở đây chỉ nói ba việc:

1. Cài đặt và những gì phải chép theo
2. **Đọc báo cáo thế nào** — phần quan trọng nhất
3. Gặp lỗi thì làm gì, báo lại ra sao

---

## 1. Cài đặt

### Yêu cầu

- Windows
- **KHÔNG cần cài gì cả.** Bộ công cụ đã mang sẵn Python 3.14.6 trong thư mục
  `python/` — giải nén ra là chạy được ngay.
  - Không cần quyền quản trị (admin)
  - Không đụng tới Python sẵn có trên máy bạn
  - Không cần mạng
- Nếu vì lý do nào đó thư mục `python/` bị thiếu, công cụ sẽ tự dùng Python của
  máy (cần **3.8 trở lên**) và báo rõ nếu không có.

### Chép công cụ sang máy khác

> **Chép NGUYÊN CẢ THƯ MỤC. Đừng chép từng file.**

Thư mục gồm:

| Thành phần | Vai trò |
|---|---|
| `GIAO_DIEN.bat` | **bấm đúp cái này — giao diện có cửa sổ, dễ dùng nhất** |
| `giao_dien.py` | mã của giao diện |
| `tu_kiem_lan_dau.py` | bộ tự kiểm chạy ở lần mở đầu tiên |
| `goi_project_capcut.py` | công cụ chính (chạy được cả không cần giao diện) |
| `chung.py` | thư viện dùng chung — **thiếu file này là không chạy được** |
| `toi_uu_dung_luong.py` | chế độ 4 (tối ưu dung lượng) |
| `canh_gac.py` | canh gác phát hiện treo trên ổ mạng — chỉ cảnh báo, không tự dừng |
| `loi/` | lõi dùng chung (xác định thư mục gốc khi đóng gói) — **thiếu là không chạy được** |
| `ui/` | cầu nối giao diện ↔ lõi và các phép kiểm đầu vào — **thiếu là không mở được giao diện** |
| `xem_tien_trinh.py` | cửa sổ theo dõi tiến độ, chạy song song |
| `cau_hinh.json` | tuỳ chọn — xoá đi thì dùng giá trị mặc định |
| `python/` | **bản Python đi kèm — thiếu thư mục này thì phải có Python trên máy** |
| `ffmpeg/` | bản ffmpeg đi kèm |
| `tests/` | bộ kiểm — không cần để chạy, nhưng nên giữ |
| `*.bat` | bấm đúp để chạy |

Nếu chép thiếu, công cụ **báo ngay khi khởi động** kèm tên file thiếu — nó không
để bạn trả lời hết câu hỏi rồi mới chết giữa chừng.

### Kiểm tra sau khi chép

```
python\python.exe tests\chay_het.py
```

(Dùng `python\python.exe` chứ không phải `python` — để chạy đúng bản đi kèm,
không phụ thuộc máy bạn có Python hay không.)

Chạy khoảng 45 giây, không cần NAS, không đụng vào project nào. Kết thúc phải
thấy `=> TAT CA DAT.` Nếu không, đừng dùng công cụ cho tới khi hiểu vì sao.

---

### Chạy bằng giao diện (khuyên dùng)

**Lần mở đầu tiên** sẽ có một cửa sổ nhỏ tự kiểm bộ công cụ (khoảng 1–5 giây):
đủ file sau khi giải nén chưa, Python đi kèm chạy được không, ffmpeg có bị phần
mềm bảo vệ chặn không. Kiểm xong nó ghi một dấu, **các lần sau vào thẳng giao diện**.

Nếu bước tự kiểm báo lỗi, nó nói rõ thiếu gì và phải làm gì. Bạn vẫn có thể bấm
"Vẫn mở giao diện" để dùng tiếp — nhưng nên sửa trước.

> Cửa sổ đen (console) chỉ chớp khoảng 1 giây rồi biến mất. Giao diện chạy không
> kèm console. Nếu console **ở lại** và hiện chữ, tức là có lỗi — hãy đọc nó.

Bấm đúp **`GIAO_DIEN.bat`**. Cửa sổ có 4 mục, làm từ trên xuống:

| Mục | Làm gì |
|---|---|
| **1) Chọn project** | Bấm một dòng trong danh sách, hoặc `Quét thư mục mẹ...` nếu project nằm chỗ khác, hoặc dán thẳng đường dẫn |
| **2) Folder XUẤT RA** | Chọn nơi đặt gói. **Phải nằm NGOÀI project gốc** — công cụ tự chặn nếu sai |
| **3) Dò theo tên** | Chỉ dùng khi có file thiếu. Để trống = chỉ quét các ổ **trong máy**; **ổ mạng và USB KHÔNG được quét tự động**. Footage ở NAS thì bấm `Thêm thư mục...`. Nhiều thư mục **cách nhau bằng dấu `;`** (không phải dấu phẩy) |
| **4) Tối ưu dung lượng** | Ba ô tích. Bỏ hết cả ba = copy nguyên bản (an toàn nhất nhưng nặng hơn nhiều) |

Rồi bấm **`1) QUÉT`**. Công cụ quét xong sẽ **dừng lại** và hiện kế hoạch trong ô
Nhật ký — đọc xong thấy ổn thì bấm **`2) TIẾN HÀNH COPY`**. Chưa bấm thì chưa có
gì được ghi ra đĩa.

> **Nút `Dừng dò`** dừng bước quét đang chạy — thường **dưới 1 giây**, ổ mạng lạnh
> có thể vài giây. Dừng rồi thì **chưa có gì được ghi ra đĩa** và bấm `1) QUÉT`
> lại là chạy lại được, không phải đóng cửa sổ. Nếu bạn đã bấm `2) TIẾN HÀNH COPY`
> thì **không dừng giữa chừng được nữa** — muốn dừng hẳn phải đóng cửa sổ, và lần
> sau hãy chọn một thư mục xuất ra MỚI (chạy lại vào chính thư mục cũ sẽ tạo bản
> trùng và làm gói phình gấp đôi).
>
> Khi bạn dừng giữa bước dò, báo cáo ghi rõ **"ĐÃ DỪNG… N thư mục"** và đánh dấu
> các file bằng `?` chứ không phải `X` — nghĩa là *chưa dò xong*, **không** phải
> *không tìm thấy*. Đừng vội kết luận là file đã mất.

> **Nút `Quét thư mục mẹ...`** giờ chạy nền — cửa sổ **không đông cứng** nữa, và
> bấm `Dừng dò` là dừng được. Nếu có thư mục nào không đọc được (thiếu quyền, ổ
> mạng rớt phiên), Nhật ký ghi rõ **số lượng** và cảnh báo danh sách có thể
> **thiếu project** — đừng coi danh sách là đầy đủ khi thấy dòng đó.

### Nếu công cụ bị treo trên ổ mạng

Công cụ có một **canh gác** tự theo dõi. Nó **không bao giờ tự dừng** — chỉ báo:

| Sau | Nó nói gì |
|---|---|
| **5 phút** không thấy tiến triển | `CANH BAO: khong thay tien trien` — kèm câu *"nếu đang copy một file rất lớn qua mạng thì đây có thể là bình thường"*. **Cứ đợi thêm.** |
| **15 phút** | `NGHI TOOL DA TREO` — kèm số đo và **bạn quyết định** |

Nếu nó báo nghi treo, đọc dòng **"Đang ở bước:"** rồi cân nhắc:

- Đang ở bước **mã lại / tối ưu** → dừng **mất ít**: các clip đã mã xong được ghi nhớ, lần sau chạy lại dùng lại được.
- Đang ở bước **copy** → dừng **mất nhiều**: lần sau phải copy lại từ đầu. Hãy đợi thêm trước khi dừng.

Muốn dừng hẳn thì đóng cửa sổ. Nguyên nhân hay gặp nhất là ổ mạng rớt phiên —
Python không có giới hạn thời gian cho ổ đĩa nên công cụ sẽ chờ mãi mãi.

> Giao diện và bản dòng lệnh dùng **chung một mã** — không có chuyện chạy ra kết
> quả khác nhau.

**Vẫn muốn dùng dòng lệnh?** Bấm đúp `goi_project_capcut.bat`.

---

## 2. Đọc báo cáo `_BAO_CAO_THIEU.txt`

Sau mỗi lần chạy, công cụ ghi file này vào thư mục xuất ra. **Đây là thứ quyết
định gói của bạn có dùng được hay không** — đừng chỉ nhìn dòng "XONG" trên màn hình.

### Đầu file: bạn đang chạy bản nào

```
Tool: goi_project_capcut 1.0.0 | Python 3.14.6 | Windows 11
ffmpeg: ffmpeg version 8.1.2-essentials_build...
Chay luc: 2026-08-18 16:42:10
```

Khi báo lỗi, **gửi nguyên file này** — mấy dòng trên cho biết bạn chạy bản nào,
trên máy gì. Không có nó thì gần như không gỡ được.

### Câu kết luận — tìm một trong ba câu này

| Câu trong báo cáo | Nghĩa là |
|---|---|
| `Khong thieu. Ban tu chua DU` | ✅ Gói đủ. Dùng được. |
| `CHUA KET LUAN DUOC` | ⚠️ **Bộ tự kiểm bị lỗi nên không có bằng chứng gì.** Không phải "đủ", cũng không phải "thiếu" — là *chưa biết*. Xem mục `BO TU KIEM THAT BAI` rồi chạy lại. |
| Không có câu nào ở trên | ❌ Có vấn đề. Đọc tiếp các mục bên dưới. |

> Công cụ **không bao giờ** kết luận "ĐỦ" khi phép kiểm của nó bị lỗi. Nếu bạn
> thấy "ĐỦ" thì nó thật sự đã kiểm và đã đạt.

### Các mục CÓ ảnh hưởng — phải xử lý

Đây là **danh sách đầy đủ** — chỉ cần một mục trong bảng này có nội dung là
công cụ **không** kết luận "ĐỦ".

| Mục | Ý nghĩa |
|---|---|
| `THIEU - khong gom duoc` | Media không tìm thấy ở đâu cả. Gói **sẽ mất hình/tiếng**. Bổ sung file rồi chạy lại. |
| `COPY THAT BAI` | Tìm thấy nhưng không ghi được sang đích (hết chỗ, mất mạng, hết quyền). |
| `FOLDER DRAFT COPY THIEU` | Một phần thư mục draft không chép được. |
| `TU KIEM - tham chieu HONG` | Sau khi gom xong, vẫn có đường dẫn trỏ vào chỗ trống. |
| `KHONG TIM THAY NGUON khi viet lai` | Có đường dẫn công cụ **không tìm ra file nguồn** nên giữ nguyên path cũ. Gói **không tự chứa**: sang máy khác sẽ mất phần đó. Thường là media đã bị xoá/đổi tên sau khi dựng. |
| `KHONG VIET LAI DUOC` | Đường dẫn trong JSON không sửa được → gói **không tự chứa**. |
| `FILE .json DOC LOI (timeline/so dang ky` | File cấu trúc bị hỏng. |
| `TOI UU - SEGMENT BI LECH` | Đoạn cắt bị lệch → **hình sẽ sai**. Nghiêm trọng nhất trong nhóm tối ưu. |
| `BO TU KIEM THAT BAI` | Phép kiểm chết. Mọi kết luận khác đều mất giá trị. |

### Các mục KHÔNG ảnh hưởng video — đọc cho biết thôi

| Mục | Vì sao không sao |
|---|---|
| `TU KIEM - anh bia/thumbnail hong` | Chỉ xấu giao diện CapCut, không mất hình. |
| `TOI UU - segment DA LECH SAN trong draft goc` | Đoạn dùng đã vượt độ dài clip **ngay trong project gốc**, trước khi gói. CapCut tự ghi như vậy. Công cụ không gây ra, và mang sang máy khác cũng không tệ hơn bản gốc. |
| `FILE .json cache doc loi` | File cache CapCut tự sinh. Không liên quan timeline. |
| `TOI UU - clip ma lai that bai` | Đã **giữ nguyên bản gốc** — không mất hình, chỉ là gói to hơn. |
| `TOI UU - clip KHONG dua vao ma lai` | Clip dài quá ngưỡng hoặc không tìm thấy nguồn để nén. Giữ nguyên bản gốc. |
| `DON DEP - file KHONG xoa duoc` | Còn sót file thừa. Gói vẫn đủ, chỉ hơi nặng. |
| `DA CUU ban goc bi bo qua nham` | Công cụ đã **tự phát hiện và sửa** một sự cố: nó dự đoán vài file sẽ được thay bằng bản nén nên không chép, nhưng việc thay không xảy ra. Các file đó đã được chép bù. Gói **vẫn đủ** — mục này chỉ để bạn biết. |
| `DON DEP - file JSON KHONG doc duoc` | Có file JSON không đọc được nên công cụ **cố ý không xoá** file mồ côi nào — chọn an toàn thay vì xoá nhầm. |
| `BAN GOC CON TRONG GOI` | Bản gốc còn sót lại mà không ai dùng — có thể xoá tay để nhẹ gói. |

### Mục cần chú ý riêng

Công cụ xử lý được đường dẫn dài, nhưng **CapCut và Windows Explorer có thể
không mở nổi**. Báo cáo chia làm **hai mục khác nhau — cách xử lý khác hẳn**:

| Mục | Nghĩa là | Bạn phải làm gì |
|---|---|---|
| `DUONG DAN QUA DAI (>260 ky tu)` | Dài vì **thư mục bạn chọn** dài | Đặt gói ở đường dẫn ngắn hơn. Báo cáo ghi rõ **tối đa bao nhiêu ký tự**. |
| `DUONG DAN QUA DAI ma RUT NGAN THU MUC DICH KHONG CUU DUOC` | Dài vì **tên file gốc** quá dài | **Đổi thư mục đích không giải quyết được** — đừng mất công chạy lại. Xem bên dưới. |

**Vì sao có trường hợp thứ hai:** CapCut khi tải ảnh từ trên mạng đôi khi dùng
nguyên chuỗi mã hoá làm tên file — có file dài **205 ký tự**. Cộng với
`subdraft/<GUID>/materials/`, riêng phần bên trong gói đã vượt 260 ký tự, nên
kể cả đặt gói ở `D:\` cũng không cứu được.

Trường hợp này thường là **ảnh bìa hoặc ảnh nền**, không ảnh hưởng video xuất
ra. Nếu CapCut ở máy con báo thiếu đúng ảnh đó, cách xử lý là mở project rồi
**thay lại ảnh đó bằng tay**.

---

### Giải nén ở đâu

Đường dẫn bên trong gói có thể dài tới **188 ký tự**, mà Windows giới hạn 260.
Vì vậy thư mục bạn giải nén ra nên **không quá 70 ký tự**.

| Chỗ giải nén | Tổng | |
|---|---|---|
| `C:\GOI\` | 195 | ✅ an toàn nhất |
| `C:\Users\<tên>\Desktop\` | ~226 | ✅ |
| `C:\Users\<tên>\Downloads\` | ~228 | ✅ |
| Lồng thêm 2-3 tầng thư mục nữa | > 260 | ⚠️ CapCut có thể không mở được |

---

## 3. Phép thử vàng — trước khi bàn giao cho người khác

Mở gói bằng CapCut **trên chính máy vừa gói là bằng chứng giả**: đường dẫn cũ
vẫn còn trên máy đó nên CapCut vẫn tìm thấy file, kể cả khi gói thiếu.

Muốn chắc chắn:

1. **Đổi tên hoặc di chuyển** thư mục gói sang chỗ khác
2. Mở lại bằng CapCut
3. Xem timeline có đủ hình, đủ tiếng không

Chỉ khi qua được bước này thì gói mới thật sự tự chứa.

---

## 4. Gặp lỗi thì làm gì

### Công cụ báo `KHONG THE CHAY` ngay khi khởi động

Đọc dòng lỗi. Thường là chép thiếu file — chép lại cả thư mục.

Nếu nó nói *"`chung.py` CÓ NGAY trong thư mục đó"* thì vấn đề khác: bạn đang
chạy công cụ theo cách không chuẩn (qua script bọc ngoài). Hãy chạy trực tiếp
bằng file `.bat` hoặc `python goi_project_capcut.py`.

### Công cụ bảo `DUNG LAI: folder XUAT RA nam TRONG folder project goc`

Đây là **chốt an toàn**, không phải lỗi. Bạn đã chọn thư mục xuất nằm trong (hoặc
trùng với) project gốc. Nếu chạy tiếp, công cụ sẽ ghi đè lên project gốc và có
thể xoá media trong đó. Hãy chọn một thư mục **ngoài** project gốc.

### Máy lag khi đang chạy

Chế độ 4 mã lại video nên ăn nhiều CPU. Công cụ **tự hạ xuống 2 luồng khi thư
mục xuất nằm trên ổ mạng** (chạy nhiều luồng trên cùng NAS làm tăng mạnh rủi ro
treo, không chỉ chậm). Muốn nhẹ hơn nữa, sửa `cau_hinh.json`:

```json
{ "workers": 1 }
```

> **Đừng mở CapCut và chạy công cụ cùng lúc trên cùng một project.** Công cụ đọc
> draft, CapCut ghi draft. Và **đừng bao giờ End Task CapCut** — nó có thể đang
> lưu dở, làm hỏng draft.

### Công cụ chạy rất lâu, không biết còn bao nhiêu

Mở thêm cửa sổ, bấm đúp `xem_tien_trinh.bat`, dán đường dẫn thư mục xuất ra.
Nó chỉ đọc, không đụng gì vào tiến trình đang chạy.

Lưu ý: nó đo bằng cách quét thư mục đích liên tục, nên nếu đích là NAS thì bản
thân việc theo dõi cũng tạo tải. Đang gói project lớn qua mạng thì đừng mở nó
suốt.

### Báo lỗi về cho người phát hành

Gửi kèm:

1. **File `_BAO_CAO_THIEU.txt`** (có số hiệu phiên bản ở đầu — bắt buộc)
2. Ảnh chụp màn hình dòng lỗi
3. Bạn chọn chế độ nào (1 hay 4), thư mục xuất ra nằm ở ổ nào (ổ máy hay NAS)

---

## 5. Tuỳ chỉnh — `cau_hinh.json`

Xoá file đi thì công cụ dùng mặc định. Sai cú pháp JSON thì nó **báo rõ rồi dùng
mặc định**, không chết.

| Khoá | Mặc định | Ý nghĩa |
|---|---|---|
| `crf` | 21 | Chất lượng nén. Số **nhỏ** = nét hơn, nặng hơn. |
| `preset` | `veryfast` | Tốc độ mã hoá. Chậm hơn = file nhỏ hơn chút. |
| `workers` | `null` | Số clip mã cùng lúc. `null` = tự chọn theo đích. |
| `workers_o_mang` | 2 | Dùng khi đích là ổ mạng/NAS. **Giữ thấp.** |
| `workers_o_cuc_bo` | 4 | Dùng khi đích là ổ cứng của máy. |

---

## 6. Dành cho người bảo trì

- **`bug.md` là nhật ký lỗi** — 107 mục, mỗi mục có Triệu chứng → Nguyên nhân gốc
  → Cách sửa → Cách kiểm chứng → Bài học. Đọc phần **"Checklist nhanh"** ở cuối
  trước khi sửa bất kỳ dòng code nào.
- **`CLAUDE.md`** ghi quy tắc bắt buộc, gồm cả cách làm việc khi nhiều người cùng
  sửa repo.
- **Chạy `python tests\kiem_nhat_ky.py`** trước khi thêm mục vào `bug.md` — nó
  kiểm số hiệu trùng/thiếu và đối chiếu nhãn "chưa cài" với code thật.
- **Chạy `python tests\chay_het.py`** trước *và* sau mỗi khối việc.
- **`tests/test_tai_lieu.py` khoá chính tài liệu này vào code.** Nó đọc bằng
  `ast` mọi mục báo cáo và mọi điều kiện trong biểu thức `ok`, rồi bắt buộc tài
  liệu phải mô tả đủ và **xếp đúng bảng**. Thêm một điều kiện chặn kết luận mới
  mà quên ghi vào đây → bộ kiểm đỏ. Đừng sửa bộ kiểm cho hết đỏ; hãy sửa tài liệu.
- Sửa xong một lỗi thì **viết luôn bộ kiểm cho nó**. Một file không có bộ kiểm
  thì mọi bảng tổng kết xanh đều là xanh giả ở phần đó — đã mắc đúng lỗi này một
  lần với `xem_tien_trinh.py` (xem mục #61).
