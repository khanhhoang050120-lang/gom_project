# -*- coding: utf-8 -*-
"""QUÉT THỬ - xem trước số liệu một project mà KHÔNG copy gì cả.

Vì sao có chức năng này
-----------------------
Cửa sổ chính có hai bước `1) QUÉT` rồi `2) TIẾN HÀNH COPY`, dừng lại giữa
chừng cho người dùng đọc kế hoạch. Hàng đợi thì chạy thẳng cả loạt — nếu
dừng hỏi từng project thì mất hẳn ý nghĩa của hàng đợi.

Nút "Quét thử" bù lại chỗ đó: chạy riêng một mục, in ra bao nhiêu file, bao
nhiêu GB, thiếu gì — rồi **dừng, không ghi một byte nào ra đĩa**.

Nguyên tắc SPEC §1 vẫn giữ
--------------------------
Module này KHÔNG gọi `main()`. Nó chỉ gọi các hàm ĐỌC của lõi
(`collect_refs`, `index_by_names`) — những hàm không ghi gì cả. Đây không
phải "viết lại logic gói": nó không copy, không mã lại, không viết lại
đường dẫn. Nó chỉ đếm.

Ranh giới rạch ròi: **hàm nào có thể GHI thì module này không được gọi.**

Module này TUYỆT ĐỐI không import tkinter.
"""
from __future__ import annotations

import os


class KetQuaQuet:
    """Số liệu một lần quét thử."""

    def __init__(self):
        self.tong_tham_chieu = 0
        self.so_file_gom = 0
        self.byte_gom = 0
        self.so_bo_qua = 0         # file chỉ nằm ở kho/cache (chế độ 4 bỏ)
        self.byte_bo_qua = 0
        self.thieu = []            # đường dẫn không tìm thấy ở đâu cả
        self.loi = None            # chuỗi mô tả nếu quét thất bại

    @property
    def dat(self):
        return self.loi is None

    def cac_dong(self):
        """Trả danh sách dòng để đổ vào ô Nhật ký."""
        if self.loi:
            return [f"! Quét thử THẤT BẠI: {self.loi}"]
        from ui.hang_doi import co
        d = [
            "=== QUÉT THỬ (chưa copy gì cả) ===",
            f"  Tổng tham chiếu media : {self.tong_tham_chieu}",
            f"  Sẽ gom                : {self.so_file_gom} file, {co(self.byte_gom)}",
        ]
        if self.so_bo_qua:
            d.append(f"  Chế độ 4 bỏ qua       : {self.so_bo_qua} file,"
                     f" {co(self.byte_bo_qua)} (chỉ nằm ở kho/cache)")
        if self.thieu:
            d.append(f"  ! KHÔNG tìm thấy      : {len(self.thieu)} file")
            for p in self.thieu[:8]:
                d.append(f"      {p}")
            if len(self.thieu) > 8:
                d.append(f"      ... và {len(self.thieu) - 8} file nữa")
        else:
            d.append("  Không thiếu file nào.")
        d.append("  (Chưa ghi gì ra đĩa. Bấm CHẠY CẢ HÀNG ĐỢI để gom thật.)")
        return d


def quet_thu(muc, G, nen_dung=None):
    """Quét một mục, trả `KetQuaQuet`. KHÔNG ghi gì ra đĩa.

    `nen_dung`: hàm không tham số, trả True khi người dùng muốn dừng.

    KHÔNG ném: mọi lỗi vào `kq.loi` để người gọi hiển thị. Một lần quét thử
    hỏng không được làm chết cửa sổ hàng đợi.
    """
    kq = KetQuaQuet()
    try:
        from chung import _lp, _np, isfile_safe

        refs, need_copy, *_ = G.collect_refs(muc.draft, nen_dung=nen_dung)
        kq.tong_tham_chieu = len(refs)

        # Chế độ 4 chỉ gom media THỰC SỰ DÙNG trên timeline (vai trò 'content').
        # Công thức phải KHỚP TỪNG CHỮ với `_main_than()` — nó lọc trên
        # `need_copy` chứ KHÔNG phải trên toàn bộ `refs`, vì file đã nằm sẵn
        # đúng chỗ trong gói thì không phải gom lại. Lệch một chút là số liệu
        # xem trước nói dối, mà người dùng lại quyết định dựa trên số đó.
        bat_toi_uu = any(muc.tuy_chon.get(k) for k in ("trim", "scale", "cleanup"))
        if bat_toi_uu:
            chi_content = {p for p, r in refs.items()
                           if "content" in r.get("roles", set())}
            gom = need_copy & chi_content
            bo = need_copy - chi_content
        else:
            gom, bo = set(need_copy), set()

        for tap, dem_thieu in ((gom, True), (bo, False)):
            for p in tap:
                if nen_dung and nen_dung():
                    kq.loi = "đã dừng theo yêu cầu"
                    return kq
                np = _np(p)
                if not isfile_safe(np):
                    if dem_thieu:
                        kq.thieu.append(str(p))
                    continue
                try:
                    sz = os.path.getsize(_lp(np))
                except OSError:
                    # Đọc được `isfile` mà không lấy được kích thước: ổ mạng
                    # rớt phiên giữa chừng. Đếm là CÓ nhưng không cộng byte —
                    # thà báo dung lượng thiếu còn hơn báo thiếu file.
                    sz = 0
                if dem_thieu:
                    kq.so_file_gom += 1
                    kq.byte_gom += sz
                else:
                    kq.so_bo_qua += 1
                    kq.byte_bo_qua += sz

        # Ghi vào mục để bảng hiện cột "Dung lượng" ngay
        muc.byte_goc = kq.byte_gom
        muc.so_file = kq.so_file_gom
    except BaseException as ex:
        kq.loi = f"{type(ex).__name__}: {ex}"
    return kq
