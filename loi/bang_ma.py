# -*- coding: utf-8 -*-
"""BẢNG MÃ - làm cho tiếng Việt CÓ DẤU in được trên mọi máy.

Vì sao module này tồn tại
--------------------------
Máy phát triển có ACP 65001 (UTF-8) nên in tiếng Việt có dấu không bao giờ
lỗi. Máy con Windows tiếng Việt mặc định là **ACP 1258** hoặc 1252, và ở đó
`print("Cắt gọn")` **làm chết cả tiến trình**:

    UnicodeEncodeError: 'charmap' codec can't encode character '\\u1eaf'

Đây đúng loại lỗi mà `bug.md` #68 cảnh báo: *"máy phát triển ACP 65001 trùng
nhau nên KHÔNG BAO GIỜ lộ lỗi"*. Nó chỉ nổ trên máy người dùng.

Đo thực nghiệm (2026-09-10)
---------------------------
Bốn đường chữ đi ra, kết quả KHÁC NHAU:

    Nhãn tkinter (Tcl)          -> AN TOÀN, không qua stdout
    Ô Nhật ký của giao diện     -> AN TOÀN, chuỗi Python thuần
    File báo cáo (utf-8)        -> AN TOÀN
    Console chế độ dòng lệnh    -> CHẾT với cp1258/cp1252

Ba cách đã thử:

    không sửa gì                       -> chết cp1258, chết cp1252
    reconfigure(errors='replace')      -> không chết nhưng ra "C?t g?n"
    reconfigure(encoding='utf-8',
                errors='replace')      -> ĐÚNG trên cả ba môi trường

Cách thứ ba là cách duy nhất vừa không chết vừa giữ đúng chữ.

Vì sao vẫn cần `errors="replace"`
----------------------------------
Ép `encoding="utf-8"` là đủ cho tiếng Việt. Nhưng đường ra có thể là một pipe
hoặc file do người khác mở với bảng mã khác; `errors="replace"` bảo đảm một ký
tự lạ chỉ thành dấu `?` chứ **không giết cả lần gom** đang chạy dở hàng chục
phút.

Chỉ dùng thư viện chuẩn.
"""
from __future__ import annotations

import sys

# Đã ép rồi thì thôi - gọi hai lần không sai nhưng tốn công vô ích.
_DA_EP = False


def ep_utf8(bat_buoc=False):
    """Ép `sys.stdout`/`sys.stderr` sang UTF-8. Gọi càng SỚM càng tốt.

    Trả về True nếu đã ép được ít nhất một luồng.

    `bat_buoc=True`: ép lại kể cả khi đã ép rồi (dùng cho bộ kiểm).

    KHÔNG nem exception trong mọi trường hợp: dưới `pythonw` thì `sys.stdout`
    có thể là None, và một lỗi ở đây sẽ giết chương trình trước khi giao diện
    kịp hiện ra - tức là "bấm đúp không thấy gì", đúng triệu chứng tệ nhất.
    """
    global _DA_EP
    if _DA_EP and not bat_buoc:
        return True

    da = False
    for ten in ("stdout", "stderr"):
        luong = getattr(sys, ten, None)
        if luong is None:
            continue                  # pythonw: không có console
        rc = getattr(luong, "reconfigure", None)
        if rc is None:
            continue                  # đã bị thay bằng lớp giả (Ong, _KhongDau)
        try:
            rc(encoding="utf-8", errors="replace")
            da = True
        except Exception:
            # Luồng đã đóng, hoặc là lớp giả không cho đổi. Không sao - các
            # lớp giả trong tool đều nhận chuỗi Python thuần nên vốn đã an toàn.
            pass

    if da:
        _DA_EP = True
    return da


def mo_ta_bang_ma():
    """Một dòng mô tả bảng mã, để in vào đầu báo cáo khi hỗ trợ từ xa.

    Con số ACP cho biết ngay máy người dùng có cùng thế giới với máy phát
    triển không (bài học `bug.md` #68).
    """
    phan = []
    try:
        import ctypes
        phan.append(f"ACP {ctypes.windll.kernel32.GetACP()}")
    except Exception:
        pass
    try:
        enc = getattr(sys.stdout, "encoding", None)
        if enc:
            phan.append(f"stdout {enc}")
    except Exception:
        pass
    return " | ".join(phan) or "(không đọc được bảng mã)"
