# -*- coding: utf-8 -*-
"""G5 - doi chieu BAN_GIAO.md voi CODE THAT.

Tai lieu ban giao noi doi con nguy hiem hon khong co tai lieu: nguoi dung tin no.
Bo kiem nay bien "tai lieu lac hau" thanh MOT LOI TEST, khong phai thu phat hien
duoc bang mat khi doc lai.

No chot bon dieu:
  1. MOI muc `sect(...)` trong bao cao deu duoc ghi trong tai lieu.
  2. Muc nao CHAN ket luan "DU" (nam trong bieu thuc `ok`) phai nam dung o bang
     "CO anh huong", muc nao khong chan phai nam o bang kia. Xep sai bang la
     loi NANG: nguoi dung se bo qua mot muc that su lam hong goi.
  3. So hieu phien ban, khoa + gia tri mac dinh cua cau_hinh.json, hai cau ket
     luan - deu phai khop chuoi that trong code.
  4. Danh sach file phai chep khong bo sot file nao cua tool.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import chung as C                      # noqa: E402

MAIN = ROOT / "goi_project_capcut.py"
DOC = ROOT / "BAN_GIAO.md"

pas = fail = 0


def check(ten, dk, chi_tiet=""):
    global pas, fail
    if dk:
        pas += 1
        print(f"  PASS  {ten}")
    else:
        fail += 1
        print(f"  FAIL  {ten}")
        for d in str(chi_tiet).splitlines():
            print(f"           {d.encode('ascii', 'replace').decode('ascii')}")


# --------------------------------------------------------------------------
# Doc code: cac muc bao cao va muc nao chan ket luan "DU"
# --------------------------------------------------------------------------
def cac_muc_bao_cao(src: str):
    """Tra ve danh sach nhan truyen cho sect(...) - lay tu AST, khong regex.

    Regex se hong voi chuoi noi nhieu dong (`"a" " b"`), va trong file that co
    dung dang do.
    """
    cay = ast.parse(src)
    nhan = []
    for nut in ast.walk(cay):
        if (isinstance(nut, ast.Call) and isinstance(nut.func, ast.Name)
                and nut.func.id == "sect" and nut.args):
            a = nut.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                nhan.append(a.value)
    return nhan


def bien_chan_ket_luan(src: str):
    """Ten cac bien trong `ok = not (...)`.

    Lay tu AST nen them mot dieu kien chan moi vao code se lam bo kiem nay
    that bai cho toi khi nguoi sua khai bao no o bang DOI_CHIEU.
    """
    cay = ast.parse(src)
    for nut in ast.walk(cay):
        if (isinstance(nut, ast.Assign) and len(nut.targets) == 1
                and isinstance(nut.targets[0], ast.Name)
                and nut.targets[0].id == "ok"):
            return {n.id for n in ast.walk(nut.value) if isinstance(n, ast.Name)}
    return set()


# Bien trong bieu thuc `ok` -> nhan muc bao cao tuong ung.
# Bang nay la CHO DUY NHAT noi con nguoi phai khai bao moi lien he do; bo kiem
# ben duoi bat buoc no phu kin bieu thuc `ok` that.
DOI_CHIEU = {
    "misses_hard":    "THIEU - khong gom duoc",
    "copy_fail":      "COPY THAT BAI",
    "skipped_items":  "FOLDER DRAFT COPY THIEU",
    "bad_hard":       "TU KIEM - tham chieu HONG",
    "unresolved_hard": "KHONG TIM THAY NGUON khi viet lai",
    "rewrite_fail":   "KHONG VIET LAI DUOC",
    "_jf_hard":       "FILE .json DOC LOI (timeline/so dang ky",
    "opt_bad":        "TOI UU - SEGMENT BI LECH",
    "verify_loi":     "BO TU KIEM THAT BAI",
}


# --------------------------------------------------------------------------
# Doc tai lieu
# --------------------------------------------------------------------------
def bang_trong_tai_lieu(doc: str, tieu_de: str):
    """Cac chuoi trong dau ` ` o cot dau cua bang nam duoi tieu de nay."""
    i = doc.find(tieu_de)
    if i < 0:
        return None
    phan = doc[i + len(tieu_de):]
    ket = phan.find("\n### ")
    if ket < 0:
        ket = phan.find("\n---")
    phan = phan[:ket if ket > 0 else len(phan)]
    ra = []
    for dong in phan.splitlines():
        m = re.match(r"\s*\|\s*`([^`]+)`\s*\|", dong)
        if m:
            ra.append(m.group(1))
    return ra


def nhu_trong_tai_lieu(v):
    """Gia tri Python -> dang nguoi doc thay trong bang cua tai lieu."""
    if v is None:
        return "null"          # tai lieu viet theo JSON, khong viet "None"
    return str(v)


def gia_tri_trong_tai_lieu(doc: str, khoa: str):
    """Cot 'Mac dinh' cua dong ta `khoa` trong bang cau hinh (bo dau ` )."""
    m = re.search(r"^\s*\|\s*`" + re.escape(khoa) + r"`\s*\|([^|]*)\|",
                  doc, re.M)
    return m.group(1).strip().strip("`").strip() if m else None


def main():
    src = MAIN.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")

    print("=" * 72)
    print("Muc bao cao: code va tai lieu phai khop")
    print("=" * 72)

    muc = cac_muc_bao_cao(src)
    check("doc duoc danh sach sect(...) tu code", len(muc) >= 10,
          f"chi thay {len(muc)} muc - co the sect() da doi ten")
    print(f"  code co {len(muc)} muc bao cao")

    co_ah = bang_trong_tai_lieu(doc, "### Các mục CÓ ảnh hưởng") or []
    khong_ah = bang_trong_tai_lieu(doc, "### Các mục KHÔNG ảnh hưởng") or []
    check("tai lieu co bang 'CO anh huong'", co_ah, "khong tim thay bang")
    check("tai lieu co bang 'KHONG anh huong'", khong_ah, "khong tim thay bang")
    print(f"  tai lieu: {len(co_ah)} muc CO anh huong, {len(khong_ah)} muc khong")

    trong_doc = co_ah + khong_ah
    # Tai lieu ghi PHAN DAU cua nhan (de nguoi dung Ctrl+F duoc), nen doi chieu
    # theo tien to chu khong doi bang nhau.
    thieu = [m for m in muc
             if not any(m.startswith(d) for d in trong_doc)
             # muc ghi rieng o phan "chu y rieng", khong nam trong hai bang
             and not m.startswith("DUONG DAN QUA DAI")]
    check("moi muc bao cao deu co trong tai lieu", not thieu,
          "\n".join(f"chua ghi: {t}" for t in thieu)
          + "\n-> nguoi dung gap muc nay se khong biet no nghia la gi")

    thua = [d for d in trong_doc
            if not any(m.startswith(d) for m in muc)
            and d not in ("BAN GOC CON TRONG GOI",)]
    check("tai lieu khong ta muc khong ton tai", not thua,
          "\n".join(f"tai lieu ghi nhung code khong co: {t}" for t in thua))

    print()
    print("=" * 72)
    print("Xep bang dung: muc CHAN ket luan 'DU' phai o bang 'CO anh huong'")
    print("=" * 72)

    bien = bien_chan_ket_luan(src)
    check("doc duoc bieu thuc `ok` tu code", bien, "khong tim thay `ok = not (...)`")
    chua_khai = bien - set(DOI_CHIEU) - {"not"}
    check("bang DOI_CHIEU phu kin bieu thuc `ok`", not chua_khai,
          f"bien moi chua khai bao: {sorted(chua_khai)}\n"
          "-> co dieu kien CHAN ket luan moi; phai them vao DOI_CHIEU va vao"
          " bang 'CO anh huong' cua BAN_GIAO.md")

    for ten_bien, nhan in DOI_CHIEU.items():
        if ten_bien not in bien:
            check(f"`{ten_bien}` van con chan ket luan", False,
                  "bien nay khong con trong bieu thuc `ok` -> DOI_CHIEU lac hau")
            continue
        check(f"{nhan[:44]:<44} o bang CO anh huong",
              any(d.startswith(nhan) or nhan.startswith(d) for d in co_ah),
              f"muc nay CHAN ket luan 'DU' (bien `{ten_bien}`) nhung tai lieu"
              " khong xep no vao bang 'CO anh huong'")
        check(f"{nhan[:44]:<44} khong bi xep nham",
              not any(d.startswith(nhan) for d in khong_ah),
              "muc CHAN ket luan bi ghi la 'khong anh huong' -> nguoi dung se"
              " bo qua mot loi that su lam hong goi")

    # Chieu nguoc: muc KHONG chan ket luan khong duoc ghi la co anh huong
    nhan_chan = tuple(DOI_CHIEU.values())
    xep_qua = [d for d in co_ah if not any(d.startswith(n) or n.startswith(d)
                                           for n in nhan_chan)]
    check("bang 'CO anh huong' khong chua muc vo hai", not xep_qua,
          "\n".join(f"khong chan ket luan nhung bi xep vao: {t}" for t in xep_qua))

    print()
    print("=" * 72)
    print("So hieu phien ban / cau ket luan / cau hinh")
    print("=" * 72)

    m = re.search(r'TOOL_VERSION\s*=\s*"([^"]+)"', src)
    check("code co TOOL_VERSION", m)
    if m:
        check(f"tai lieu ghi dung phien ban {m.group(1)}", m.group(1) in doc,
              f"code = {m.group(1)}, tai lieu khong nhac den")

    for cau in ("Khong thieu. Ban tu chua DU", "CHUA KET LUAN DUOC"):
        check(f"cau ket luan '{cau[:28]}...' co that trong code", cau in src)
        check(f"cau ket luan '{cau[:28]}...' co trong tai lieu", cau in doc)

    ch = json.loads((ROOT / "cau_hinh.json").read_text(encoding="utf-8"))
    for khoa, gia_tri in C.CAU_HINH_MAC_DINH.items():
        check(f"cau_hinh.json co khoa `{khoa}`", khoa in ch,
              "mac dinh trong chung.py nhung file mau khong co")
        check(f"tai lieu ta khoa `{khoa}`", f"`{khoa}`" in doc,
              "nguoi dung khong biet khoa nay ton tai")
        if khoa in ch:
            check(f"gia tri mau `{khoa}` = {gia_tri!r} khop mac dinh",
                  ch[khoa] == gia_tri,
                  f"file mau = {ch[khoa]!r}, mac dinh trong code = {gia_tri!r}")
        # Ten khoa dung ma GIA TRI ghi sai thi con nguy hon khong ghi: nguoi dung
        # se chep dung con so trong tai lieu. Vi du `workers_o_mang` ghi thanh 8
        # se dan thang vao rui ro treo SMB o bug #25.
        ghi = gia_tri_trong_tai_lieu(doc, khoa)
        check(f"tai lieu ghi dung mac dinh cua `{khoa}`",
              ghi is not None and ghi == nhu_trong_tai_lieu(gia_tri),
              f"tai lieu ghi {ghi!r}, mac dinh that la"
              f" {nhu_trong_tai_lieu(gia_tri)!r}")

    print()
    print("=" * 72)
    print("Danh sach file phai chep")
    print("=" * 72)

    # Bo qua file SINH RA luc chay (dau tu kiem): no khong duoc chep di dau,
    # va co y KHONG nam trong zip - tai lieu nhac toi no la sai.
    def _phai_chep(p):
        if p.name.startswith(".da_tu_kiem_"):
            return False
        return p.suffix in (".py", ".json")

    for tep in sorted(p.name for p in ROOT.iterdir() if _phai_chep(p)):
        check(f"tai lieu nhac `{tep}`", tep in doc,
              "file nay o thu muc goc nhung tai lieu khong bao phai chep")

    n_bug = len(re.findall(r"^### (\d+)\.", (ROOT / "bug.md").read_text(
        encoding="utf-8"), re.M))
    m2 = re.search(r"(\d+)\s*mục, mỗi mục có Triệu chứng", doc)
    check("tai lieu ghi dung so muc bug.md", m2 and int(m2.group(1)) == n_bug,
          f"bug.md co {n_bug} muc, tai lieu ghi"
          f" {m2.group(1) if m2 else 'khong ro'}")

    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
