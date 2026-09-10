# -*- coding: utf-8 -*-
"""Noi `ui/hang_doi.py` voi `goi_project_capcut.main()` THAT.

Day la cho DUY NHAT trong hang doi cham vao loi, va no phai giu dung nguyen
tac o tai_lieu/SPEC_UI_UX.md muc 1:

    Goi `main()` DUNG MOT LAN cho moi project, lai no bang `builtins.input`.
    TUYET DOI khong tu goi cac ham con (`collect_refs`, `plan_package`,
    `optimize_package`...).

Neu vi pham, giao dien va dong lenh se lech hanh vi - dung cai bay ma nguyen
tac do sinh ra de tranh.

Module nay co import `goi_project_capcut`, nhung KHONG import tkinter.
"""
from __future__ import annotations

import builtins
import sys
import traceback

from ui.cau_noi import Ong, TraLoi

# So dong nhat ky giu lai cho MOI muc. Mot lan gom sinh hang chuc nghin dong;
# giu het thi 5 project trong hang doi la phinh RAM lien tuc.
GIOI_HAN_NHAT_KY = 2000


class _KhongCoNguoiBam:
    """`threading.Event` gia, luon o trang thai DA DAY.

    Trong hang doi khong co nguoi ngoi bam "TIEN HANH COPY" cho tung project -
    ca hang doi da duoc duyet MOT LAN truoc khi chay. Nen cau hoi "Tien hanh?"
    phai tra loi ngay, khong duoc cho.
    """

    def wait(self, timeout=None):
        return True

    def is_set(self):
        return True


def chay_mot_project(muc, nen_dung, G, hd_tin=None, ghi_ra=None):
    """Chay MOT project. Nem exception neu that bai - `HangDoi` se bat.

    muc      : `ui.hang_doi.Muc`
    nen_dung : ham khong tham so, tra True khi nguoi dung muon dung
    G        : module `goi_project_capcut` (truyen vao de kiem chung thay duoc)
    hd_tin   : hang doi tin cua giao dien (co the None khi chay khong giao dien)
    ghi_ra   : ham nhan tung dong - de ghi THANG ra file/console.

    Vi sao can `ghi_ra`: khong co no thi khi chay KHONG GIAO DIEN (kich ban tu
    dong, CI), moi dong log nam trong RAM cho toi luc ket thuc - nguoi dung
    khong thay tien do, va neu tien trinh bi giet thi mat sach nhat ky. Do that:
    mot lan gom 30 phut ma file log chi co 358 byte tu luc khoi dong.
    """
    chup = {
        "draft": muc.draft,
        "out": muc.out,
        "do": muc.tuy_chon.get("do", ""),
        "trim": bool(muc.tuy_chon.get("trim", True)),
        "scale": bool(muc.tuy_chon.get("scale", True)),
        "cleanup": bool(muc.tuy_chon.get("cleanup", True)),
    }

    class _Gom:
        """Nhan moi dong log: ghi vao nhat ky RIENG cua muc, day len giao dien
        neu co, va ghi thang ra ngoai neu co `ghi_ra`.

        Ghi rieng tung muc de sau nay bam vao mot muc trong hang doi la doc
        duoc dung nhat ky cua no.
        """

        def put(self, tin):
            loai, gt = tin
            if loai == "log":
                muc.nhat_ky.append(gt)
                # GIOI HAN: mot lan gom sinh hang chuc nghin dong. Voi 5 project
                # trong hang doi, list khong gioi han se phinh RAM lien tuc.
                # Giu 2000 dong CUOI - dong moi nhat la dong quan trong nhat.
                if len(muc.nhat_ky) > GIOI_HAN_NHAT_KY:
                    bo = len(muc.nhat_ky) - GIOI_HAN_NHAT_KY
                    del muc.nhat_ky[:bo]
                    muc.nhat_ky[0] = f"... (đã bỏ {bo} dòng đầu cho đỡ tốn bộ nhớ)"
                if ghi_ra is not None:
                    # Ghi THANG ra ngoai: khong co dong nay thi chay khong giao
                    # dien se im lang hoan toan cho toi luc ket thuc.
                    try:
                        ghi_ra(gt)
                    except Exception:
                        pass          # ghi log hong KHONG duoc lam hong lan gom
                if hd_tin is not None:
                    hd_tin.put(("log_muc", (muc, gt)))
            elif hd_tin is not None:
                hd_tin.put(tin)

    gom = _Gom()
    tra_loi = TraLoi(
        chup=chup,
        hd=gom,
        cho_tien_hanh=_KhongCoNguoiBam(),
        # Ca hang doi da duoc duyet mot lan roi - moi muc tu dong "y".
        doc_tra_loi_tien_hanh=lambda: "y",
    )

    cu_in, cu_out = builtins.input, sys.stdout
    builtins.input = tra_loi
    sys.stdout = Ong(gom)
    try:
        # MOT loi goi `main()` duy nhat. Khong tach pha, khong goi ham con.
        G.main(tuy_chon={
            "trim": chup["trim"],
            "scale": chup["scale"],
            "cleanup": chup["cleanup"],
            "nen_dung": nen_dung,
        })
    except OSError as ex:
        # Loi filesystem la loai hay gap nhat (het cho, mat mang, mat quyen).
        # Ghi them goi y truoc khi nem len cho `HangDoi` bat.
        muc.nhat_ky.append(f"! KHÔNG GHI/ĐỌC ĐƯỢC: {ex.strerror or ex}")
        muc.nhat_ky.append("  -> Kiểm ổ đích: có đủ chỗ không, có quyền ghi"
                           " không. Nếu là ổ mạng: kiểm kết nối.")
        raise
    except BaseException:
        for d in traceback.format_exc().splitlines():
            muc.nhat_ky.append(d)
        raise
    finally:
        # PHAI tra lai trong `finally`: 13 duong `return` trong than `main()`,
        # va neu khong tra lai thi muc SAU se chay voi `input` cua muc TRUOC.
        try:
            sys.stdout.flush()
        except Exception:
            pass
        builtins.input, sys.stdout = cu_in, cu_out
