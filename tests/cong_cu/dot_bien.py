# -*- coding: utf-8 -*-
r"""Phep thu DOT BIEN - "bo kiem co THAT SU bat duoc loi khong?"

KHONG phai bo kiem thuong quy (nen khong nam trong `BO_KIEM`). Chay bang tay:

    python tests\cong_cu\dot_bien.py

Vi sao ton tai:
  Mot bo kiem XANH chua chung minh duoc gi cho toi khi biet no DO trong
  truong hop nao. Du an nay da hoc bang mau: phep thu dot bien tung pha
  `index_by_names` cho luon tra {} ma 27/27 bo kiem VAN DAT (ghi o
  `tests/test_dung_do.py`). Do la luc phat hien 526 PASS kia co lo hong.

Cach lam:
  Voi moi dot bien: thay mot chuoi trong ma nguon -> chay bo kiem -> khoi
  phuc. Bo kiem DO = dot bien "bi giet" (tot). Bo kiem VAN XANH = dot bien
  "song sot" -> hoac bo kiem co lo hong, hoac day la dot bien TUONG DUONG
  (doi ma nhung khong doi hanh vi quan sat duoc).

  Song sot KHONG tu dong nghia la hong. PHAI dieu tra tung con va ghi lai
  ket luan - dung im lang bo qua, cung dung voi vang "sua" mot phep kiem
  khong he hong.

Ket qua lan chay 2026-09-11 tren `ui/cua_so_hang_doi.py`: 12 dot bien,
10 bi giet (83%), 2 song sot - ca hai da dieu tra va ket luan la TUONG DUONG.
Chi tiet ghi trong docstring cua `tests/test_cua_so_hang_doi.py`.

KHOI PHUC: file goc luon duoc ghi lai trong `finally`. Neu tien trinh bi giet
giua chung thi kiem `git diff ui/cua_so_hang_doi.py` TRUOC khi lam tiep - mot
dot bien sot lai trong ma nguon la chuyen da xay ra that trong luc phat trien.
"""
import shutil, subprocess, sys, tempfile
from pathlib import Path

# Tu suy ra - KHONG hardcode, KHONG nhan qua argv (bug #9/#34: backslash bi
# nuot khi di qua shell).
ROOT = Path(__file__).resolve().parent.parent.parent
GOC = (ROOT / "ui" / "cua_so_hang_doi.py").read_bytes()

# (ten dot bien, chuoi cu, chuoi moi, phep kiem MONG DOI bi giet)
DOT_BIEN = [
    ("bo gioi han 200 tin/nhip",
     "for _ in range(200):", "while True:", "HDUI-09"),
    ("bo khoi tao bien truoc try (bay dong 489)",
     "        ve_bang = ve_log = ve_nut = False\n        try:", "        try:", "HDUI-10c"),
    ("bo khoa chong de quy khi them muc",
     "            cu = self._dang_ve\n            self._dang_ve = True",
     "            cu = self._dang_ve", "HDUI-02/03"),
    ("cho sua muc DANG CHAY",
     "            if m.trang_thai == DANG_CHAY:", "            if False:", "HDUI-05"),
    ("khong xoa so lieu quet cu khi doi cau hinh",
     "            m.byte_goc = m.so_file = None", "            pass", "HDUI-07"),
    ("noi 'Xong.' ngay ca khi con muc cho",
     'self.v_trangthai.set("Sẵn sàng." if con else',
     'self.v_trangthai.set("Xong." if False else', "HDUI-23"),
    ("noi ';' thanh ','",
     'self.v_do.set(f"{cu};{d}" if cu else d)',
     'self.v_do.set(f"{cu},{d}" if cu else d)', "HDUI-20"),
    ("khong doi / thanh backslash khi chon thu muc",
     'bien.set(d.replace("/", "\\\\"))', 'bien.set(d)', "HDUI-21b"),
    ("bo kiem widget con trong _huy_nhip",
     "        if ev is not None and ev.widget is not self.root:\n            return",
     "        pass", "HDUI-12"),
    ("dong cua so khong hoi khi dang chay",
     "        if self.hd.dang_chay and not messagebox.askyesno(",
     "        if False and not messagebox.askyesno(", "HDUI-13"),
    ("cho bam Quet thu chong nhau",
     "        if self._luong_quet is not None and self._luong_quet.is_alive():\n            return",
     "        pass", "HDUI-17"),
    ("muc TAM bi them vao hang doi",
     "            m = Muc(draft, out or draft, tuy_chon=tc)   # mục tạm, không thêm",
     "            m = self.hd.them(Muc(draft, out or draft, tuy_chon=tc))", "HDUI-19"),
]

print("=" * 70)
print(" PHEP THU DOT BIEN - bo kiem co THAT SU bat duoc loi khong?")
print("=" * 70)
bi_giet = song_sot = 0
for ten, cu, moi, mong_doi in DOT_BIEN:
    if cu.encode("utf-8") not in GOC:
        print(f"  ?? BO QUA  {ten}\n      khong tim thay moc trong ma nguon")
        continue
    tmp = Path(tempfile.mkdtemp(prefix="dbien_"))
    try:
        (ROOT / "ui" / "cua_so_hang_doi.py").write_bytes(
            GOC.replace(cu.encode("utf-8"), moi.encode("utf-8"), 1))
        r = subprocess.run([sys.executable, str(ROOT / "tests" / "test_cua_so_hang_doi.py")],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=300, cwd=str(ROOT))
        ra = r.stdout or ""
        do = [d.strip() for d in ra.splitlines() if d.strip().startswith("FAIL")]
        if r.returncode != 0 and do:
            bi_giet += 1
            print(f"  GIET   {ten}")
            print(f"           -> {do[0][:95]}")
        elif r.returncode == 7:
            bi_giet += 1
            print(f"  GIET   {ten}  (bi dong ho canh bat: TREO)")
        else:
            song_sot += 1
            print(f"  !! SONG {ten}  (mong doi {mong_doi} phai do)")
    finally:
        (ROOT / "ui" / "cua_so_hang_doi.py").write_bytes(GOC)
        shutil.rmtree(tmp, ignore_errors=True)

print()
tong = bi_giet + song_sot
print(f"  Bi giet: {bi_giet}/{tong}" + (f"  ({100*bi_giet//tong}%)" if tong else ""))
if song_sot:
    print(f"  => {song_sot} dot bien SONG SOT.")
    print("     Song sot KHONG tu dong nghia la bo kiem hong. Phai DIEU TRA")
    print("     tung con: hoac bo kiem co lo hong that, hoac day la dot bien")
    print("     TUONG DUONG (doi ma nhung khong doi hanh vi quan sat duoc).")
    print("     Ghi ket luan lai - dung im lang bo qua, cung dung voi sua.")
else:
    print("  => MOI dot bien deu bi bat. Bo kiem khong rong.")
