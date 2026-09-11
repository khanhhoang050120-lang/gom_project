#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOI PROJECT CAPCUT -> folder tu chua (REGISTRY-AWARE + SUBDRAFT-AWARE).

CapCut quan ly media qua NHIEU noi, khong chi material.path trong draft_content.json:
  1. So dang ky draft_materials[].file_Path trong draft_meta_info.json
  2. materials.videos / materials.audios trong draft_content.json
  3. DU AN CON (subdraft): folder subdraft/<GUID>/ - co the LONG NHIEU TANG.
     Moi sub-draft co draft_content.json rieng, path media TUYET DOI, va con
     duoc NHUNG INLINE vao materials.drafts[].draft cua draft cha.

Tool nay quet DE QUY MOI file .json trong draft (ke ca subdraft long nhau), gom
media va viet lai path trong CHINH file khai bao no.

QUY TAC PLACEHOLDER (da do tren 8650 duong dan that cua 5 draft):
  '##_draftpath_placeholder_<GUID>_##/x/y.mp4' duoc CapCut giai theo DRAFT ROOT
  GAN NHAT tinh nguoc len tu file JSON do (thu muc co draft_meta_info.json hoac
  sub_draft_config.json) - KHONG phai theo thu muc chua file, cung KHONG phai
  luon luon la draft cha. Ty le khop: draft-root gan nhat 99.9% | thu muc chua
  file 85.1% | luon la draft cha 53.3%.
  => file JSON trong subdraft/X/     -> goc la subdraft/X/
  => file JSON trong Timelines/Y/    -> goc la draft bao ngoai (Timelines KHONG
     phai draft root) - day la cho de sai nhat.

CHAY TREN MAY CO FOOTAGE (vd may editor goc co du o E:/U:/V:). Chi dung thu vien chuan.
"""

from __future__ import annotations
import json, os, platform, re, shutil, string, sys, time
from pathlib import Path

# EP UTF-8 NGAY DAY - truoc moi `print`. May con Windows tieng Viet co ACP 1258
# va o do `print` chu co dau lam CHET ca tien trinh (bug.md #68, #105).
# Dat trong try vi `loi/` co the thieu; luc do `kiem_tien_de()` se bao ro.
try:
    from loi.bang_ma import ep_utf8 as _ep_utf8
    _ep_utf8()
except Exception:
    pass

# G1: `chung.py` duoc import o CAP MODULE nen neu no thieu, file nay chet NGAY
# tai day - truoc ca main() va truoc kiem_tien_de(). Vi vay phep kiem cho no
# PHAI nam dung o cho import, khong the doi den phan tien de. Nguoi dung chep
# thieu file se thay huong dan ro rang thay vi mot traceback ModuleNotFoundError.
try:
    from chung import (  # E1: tang tien ich dung chung
        MEDIA_EXT,
        VIDEO_AUDIO_EXT,
        CONTENT_NAMES,
        PLACEHOLDER_RE,
        DEFAULT_GUID,
        ROOT_MARKERS,
        _lp,
        _unlp,
        _np,
        _is_under,
        _rel_posix,
        isfile_safe,
        isdir_safe,
        mtime_an_toan,
        CAU_HINH_NAME,
        CAU_HINH_MAC_DINH,
        _O_KHONG_BIET,
    mo_ta_moi_truong,
        _loai_o,
        _cac_o_dang_co,
        fixed_drives,
        la_o_mang,
        read_json_loose,
        write_json_loose,
        iter_json_files,
        draft_root_of,
        json_role,
        is_real_abs,
        is_cosmetic,
        deep_walk_strings,
        deep_rewrite_strings,
        _fmt_time,
    )
except ImportError as _ex:
    import sys as _sys
    from pathlib import Path as _Path
    _goc = _Path(__file__).resolve().parent
    print("=" * 64)
    print(" KHONG THE CHAY - thieu file cua tool")
    print("=" * 64)
    print(f"  {_ex}")
    print(f"  Thu muc tool: {_goc}")
    # PHAI phan biet hai nguyen nhan khac han nhau, neu khong se chan doan SAI:
    #   (a) file that su khong co   -> chep thieu
    #   (b) file CO NGAY DO nhung Python khong tim thay -> sys.path, xay ra khi
    #       nap module bang duong dan (spec_from_file_location, runpy, wrapper)
    if (_goc / "chung.py").is_file():
        print("  Nhung `chung.py` CO NGAY trong thu muc do -> khong phai chep thieu.")
        print("  Nguyen nhan la Python khong co thu muc nay trong duong tim kiem.")
        print("  Xay ra khi nap tool bang duong dan (runpy / spec_from_file_location /")
        print("  wrapper). Cach sua: them thu muc tool vao sys.path TRUOC khi nap:")
        print(f"      sys.path.insert(0, r\"{_goc}\")")
    else:
        print("  Tool gom cac file: chung.py, goi_project_capcut.py,"
              " toi_uu_dung_luong.py, xem_tien_trinh.py, cau_hinh.json,"
              " thu muc ffmpeg/ va tests/")
        print("  -> Hay chep LAI CA THU MUC tool, dung chep tung file rieng le.")
    _sys.exit(2)

# So hieu phien ban. TANG khi phat hanh ban moi cho nguoi dung khac.
# Muc dich: khi nguoi dung gui _BAO_CAO_THIEU.txt ve, biet duoc ho chay ban NAO.
# Khong co so nay thi moi bao loi tu may khac deu khong the truy nguyen.
TOOL_VERSION = "2.0.2"






















def doc_cau_hinh(log=print):
    """Doc `cau_hinh.json` nam canh tool. Thieu file thi dung mac dinh - KHONG loi.

    Muc dich: may manh may yeu khac nhau, va nguoi dung khong phai lap trinh vien
    nen khong the bat ho sua code. File hong/thieu khoa thi bao RO roi dung mac
    dinh cho khoa do, khong duoc im lang (checklist bug.md).
    """
    ch = dict(CAU_HINH_MAC_DINH)
    # Thu CANH MODULE truoc (hanh vi cu, va la cho bo kiem gia lap bang cach
    # doi tam `__file__`). Chi khi khong thay moi tim qua cac thu muc tai
    # nguyen - can cho ban dong goi .exe, noi `__file__` khong tro vao thu muc
    # chua .exe.
    duong = Path(__file__).resolve().parent / CAU_HINH_NAME
    if not isfile_safe(duong):
        try:
            from loi import phien_ban as _PB
            tim = _PB.tim_tai_nguyen(CAU_HINH_NAME)
            if tim is not None:
                duong = tim
        except ImportError:
            pass
    if not isfile_safe(duong):
        return ch
    try:
        doc = json.loads(Path(_lp(duong)).read_text(encoding="utf-8"))
    except Exception as ex:
        log(f"  ! {CAU_HINH_NAME} doc khong duoc ({ex}) -> dung gia tri mac dinh")
        return ch
    if not isinstance(doc, dict):
        log(f"  ! {CAU_HINH_NAME} khong phai doi tuong JSON -> dung mac dinh")
        return ch
    la = []
    for k, v in doc.items():
        # Khoa bat dau bang '_' la CHU THICH cua chinh file mau (`_crf`, `_workers`...).
        # Chung khong phai loi cau hinh, nen KHONG duoc bao nhu loi: nguoi dung moi
        # se tuong minh go sai va di sua mot thu von dung. Bo qua im lang.
        if k.startswith("_"):
            continue
        if k not in ch:
            la.append(k)
            continue
        ch[k] = v
    if la:
        log(f"  ! {CAU_HINH_NAME} co khoa khong nhan ra (bo qua): {', '.join(sorted(la))}")
    return ch


def chon_so_luong(ch, out_dir, log=print):
    """So tien trinh ma hoa chay song song, quyet dinh theo DICH.

    bug.md #25 ghi ro: chay nhieu tac vu nang cung luc tren cung mot NAS lam TANG
    MANH rui ro TREO SMB, khong chi lam cham. Vi vay dich la o mang thi ha xuong.
    Nguoi dung van chinh de duoc qua `workers` trong cau_hinh.json.
    """
    if ch.get("workers"):
        try:
            n = max(1, int(ch["workers"]))
            log(f"  So luong ma hoa: {n} (dat cung trong {CAU_HINH_NAME})")
            return n
        except (TypeError, ValueError):
            log(f"  ! `workers` trong {CAU_HINH_NAME} khong phai so -> tu chon")
    mang = la_o_mang(out_dir)
    khoa = "workers_o_mang" if mang else "workers_o_cuc_bo"
    try:
        n = max(1, int(ch.get(khoa) or CAU_HINH_MAC_DINH[khoa]))
    except (TypeError, ValueError):
        n = CAU_HINH_MAC_DINH[khoa]
    log(f"  So luong ma hoa: {n}"
        + ("  (dich la O MANG -> ha xuong de giam rui ro treo SMB, xem bug #25)"
           if mang else "  (dich la o cuc bo)"))
    return n
















def _progress_line(done_files, tot_files, done_bytes, tot_bytes, t0):
    """Tra 1 dong tien trinh: % dung luong, GB, toc do MB/s, ETA con lai."""
    import time as _t
    el = max(_t.monotonic() - t0, 1e-6)
    pct = (done_bytes / tot_bytes * 100) if tot_bytes else 100.0
    speed = done_bytes / el                      # bytes/s
    remain = (tot_bytes - done_bytes) / speed if speed > 0 else -1
    # thanh [#####-----]
    filled = int(pct / 5)
    bar = "#" * filled + "-" * (20 - filled)
    return (f"  [{bar}] {pct:5.1f}%  {done_files}/{tot_files} file  "
            f"{done_bytes/1e9:6.2f}/{tot_bytes/1e9:.2f} GB  "
            f"{speed/1e6:5.1f} MB/s  con ~{_fmt_time(remain)}")


def capcut_roots():
    bases = []
    for env in ("LOCALAPPDATA", "APPDATA"):
        b = os.environ.get(env, "")
        if b:
            bases.append(Path(b))
    home = Path.home()
    bases += [home / "AppData" / "Local", home / "Documents"]
    roots = []
    for b in bases:
        for app in ("CapCut", "JianyingPro"):
            roots.append(b / app / "User Data" / "Projects" / "com.lveditor.draft")
        roots.append(b / "CapCut")
    seen, out = set(), []
    for r in roots:
        s = str(r).lower()
        if s not in seen:
            seen.add(s); out.append(r)
    return out


def is_draft_dir(d: Path) -> bool:
    # A5: qua isfile_safe (co _lp) - draft nam sau duong dan dai van phai nhan ra
    return (any(isfile_safe(d / n) for n in CONTENT_NAMES)
            and isfile_safe(d / "draft_meta_info.json"))


def scan_drafts_recursive(parent, max_depth: int = 3, nen_dung=None,
                          on_error=None):
    """Tim moi folder draft nam trong `parent` (toi da `max_depth` tang).

    `nen_dung`: ham () -> bool, PHAI KHONG BAO GIO NEM. Kiem moi thu muc.
    `on_error`: nhan danh sach OSError khong doc duoc thu muc. Truoc day cho
        `onerror=lambda e: None` -> ca mot nhanh cay bien mat ma giao dien van
        bao "tim thay N project", tuc la bao thieu ma khong ai biet (#37).
    Tra: (danh_sach, so_loi, da_dung) khi `nen_dung` hoac `on_error` duoc
        truyen; nguoc lai tra danh_sach TRAN de duong dong lenh cu khong doi.
    """
    found = []
    loi = []
    ngat = False
    parent = Path(parent)
    # Kiem TRUOC `isdir_safe`: chinh loi goi do chan ~21 giay khi `parent` tro
    # vao mot host SMB chet, va khong co cach nao cat (Python khong co timeout
    # cho I/O filesystem - #25/#28/#37).
    if nen_dung and nen_dung():
        return ([], 0, True) if (nen_dung or on_error) else []
    if not isdir_safe(parent):
        return ([], 0, False) if (nen_dung or on_error) else found
    base_depth = len(parent.parts)
    # A5: quet qua _lp. Khi do `dp` mang prefix extended-length nen PHAI _unlp
    # truoc khi dem so thanh phan, neu khong phep tinh do sau bi lech va cat
    # nham nhanh cay thu muc.
    for dp, dirs, _ in os.walk(_lp(parent), onerror=loi.append):
        if nen_dung and nen_dung():
            ngat = True
            break
        d = Path(_unlp(dp))
        if len(d.parts) - base_depth > max_depth:
            dirs[:] = []
            continue
        if is_draft_dir(d):
            found.append(d)
            # KHONG liet ke sub-draft nhu 1 project rieng (no la thanh phan cua draft cha)
            dirs[:] = [x for x in dirs if x.lower() != "subdraft"]
    if loi and on_error:
        on_error(loi)
    if nen_dung or on_error:
        return found, len(loi), ngat
    return found


def scan_subprojects(draft_dir, max_depth: int = 8):
    """Phat hien tinh nang 'Du an con' cua CapCut. CHI doc THU MUC, khong parse JSON
    -> du nhanh de chay cho ca danh sach 200 project.

    Trong subdraft/ co LAN LON 2 loai khac han nhau, phan biet bang file danh dau:
      - DU AN CON : nhap 1 PROJECT KHAC vao de gop -> co 'draft_meta_info.json' rieng
                    (trong do 'draft_fold_path' tro ve project nguon).
      - CLIP GHEP : gop vai clip trong CHINH project nay -> chi co 'sub_draft_config.json'.
    Folder 'subdraft' RONG (rat pho bien) = KHONG dung ca hai.

    Tra (imported, compound); moi phan tu = (Path, do_sau), do_sau 1 = tang ngoai cung."""
    imported, compound = [], []

    def walk(base, depth):
        if depth > max_depth:
            return
        sd = Path(base) / "subdraft"
        try:
            names = sorted(os.listdir(_lp(sd)))
        except OSError:
            return
        for nm in names:
            child = sd / nm
            try:
                if not os.path.isdir(_lp(child)):
                    continue
            except OSError:
                continue
            if not any(isfile_safe(child / n) for n in CONTENT_NAMES):
                continue                      # khong phai draft -> bo qua
            if isfile_safe(child / "draft_meta_info.json"):
                imported.append((child, depth))
            elif isfile_safe(child / "sub_draft_config.json"):
                compound.append((child, depth))
            walk(child, depth + 1)            # du an con co the chua du an con

    walk(Path(draft_dir), 1)
    return imported, compound


def subproject_origin(sub_dir):
    """(ten hien thi, project nguon) cua 1 du an con - doc draft_meta_info.json cua no."""
    try:
        m, _ = read_json_loose(Path(sub_dir) / "draft_meta_info.json")
        return (m.get("draft_name") or Path(sub_dir).name,
                m.get("draft_fold_path") or "(khong ro)")
    except Exception:
        return Path(sub_dir).name, "(khong doc duoc)"


def subproject_tag(draft_dir) -> str:
    """Nhan ngan gan sau ten project trong danh sach chon.
    CHI hien so DU AN CON - clip ghep khong lien quan cau hoi 'co nhap project khac
    vao khong' va so luong rat lon (co project 42 cai) nen se lam roi danh sach."""
    try:
        imp, _ = scan_subprojects(draft_dir)
    except Exception:
        return ""
    if not imp:
        return ""
    top = sum(1 for _, dep in imp if dep == 1)
    extra = len(imp) - top
    return f"  << {top} DU AN CON" + (f" (+{extra} long ben trong)" if extra else "")


def draft_label(draft_dir: Path) -> str:
    name = draft_dir.name
    dur = ""
    try:
        m, _ = read_json_loose(draft_dir / "draft_meta_info.json")
        name = m.get("draft_name") or name
        us = m.get("tm_duration") or 0
        if us:
            dur = f"{us/1e6/60:.1f} phut"
    except Exception:
        pass
    return f"{name}  [{dur or '?'}]"


def list_drafts(roots):
    items = []
    for root in roots:
        if Path(root).is_dir():
            for d in Path(root).iterdir():
                if d.is_dir() and is_draft_dir(d):
                    items.append(d)
    seen, out = set(), []
    for d in sorted(items, key=mtime_an_toan, reverse=True):
        s = str(d).lower()
        if s not in seen:
            seen.add(s); out.append(d)
    return out


def _print_list(drafts):
    n_sub = 0
    for i, d in enumerate(drafts[:40], 1):
        t = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime_an_toan(d)))
        tag = subproject_tag(d)
        if "DU AN CON" in tag:
            n_sub += 1
        print(f"  {i:2d}. {draft_label(d):45s}  sua {t}{tag}")
    if n_sub:
        print(f"\n  (<< DU AN CON = project co nhap project khac vao de gop."
              f" Co {n_sub} project nhu vay o tren.)")


def choose_draft() -> Path:
    drafts = list_drafts(capcut_roots())
    print("\n=== CHON PROJECT CAN GOI ===")
    if drafts:
        print(f"(Tim thay {len(drafts)} project o thu muc CapCut mac dinh)\n")
        _print_list(drafts)
    else:
        print("(Khong thay project o thu muc CapCut mac dinh - dung T hoac P.)")
    print("\n  T. QUET mot thu muc me de liet ke project ben trong")
    print("  P. Nhap THANG duong dan 1 folder draft")
    print("  Q. Thoat")
    while True:
        c = input("\nNhap so / T / P / Q: ").strip().lower()
        if c == "q":
            sys.exit(0)
        if c == "t":
            p = input("Dan duong dan THU MUC ME: ").strip().strip('"')
            print("  Dang quet...")
            drafts = scan_drafts_recursive(Path(p))
            drafts.sort(key=mtime_an_toan, reverse=True)
            if not drafts:
                print("  X Khong thay project nao. Thu lai / dung P.")
                continue
            print(f"\n  Tim thay {len(drafts)} project:\n")
            _print_list(drafts)
            continue
        if c == "p":
            p = input("Dan duong dan folder draft: ").strip().strip('"')
            d = Path(p)
            if any((d / n).is_file() for n in CONTENT_NAMES):
                return d
            print("  X Folder do khong co draft_content.json. Thu lai.")
            continue
        if c.isdigit() and 1 <= int(c) <= min(len(drafts), 40):
            return drafts[int(c) - 1]
        print("  X Lua chon khong hop le.")






# --------------------------------------------------------------------------
# Duyet / sua DE QUY moi chuoi trong cay JSON
# --------------------------------------------------------------------------











def _new_path_forms(rel_posix: str, guid: str):
    """Tra (dang_placeholder, dang_'./') cho 1 duong dan tuong doi so voi thu muc chua file JSON."""
    return (f"##_draftpath_placeholder_{guid}_##/{rel_posix}", f"./{rel_posix}")


def _pick_form(key, forms):
    """So dang ky (file_Path) dung './...', con lai dung placeholder - dung kieu CapCut ghi."""
    return forms[1] if key == "file_Path" else forms[0]


# --------------------------------------------------------------------------
# Pha 1: THU THAP tham chieu tren TOAN BO draft (ke ca subdraft long nhieu tang)
# --------------------------------------------------------------------------

class _DaHuy(Exception):
    """Nguoi dung bam 'Dung do'. KHONG BAO GIO duoc de no bay ra ngoai main():
    moi cho nem deu phai co `except _DaHuy` ngay tai cho goi.

    Vi sao pha QUET JSON dung `raise` con pha DO THEO TEN dung `break`:
      - `collect_refs` quet THIEU la tham hoa: refs thieu -> media dang dung
        khong nam trong `refd` -> chot `duoc_xoa_mo_coi` vo hieu -> `cleanup_unused`
        XOA THAT roi bao cao van ghi "DU". Chinh `iter_json_files` cung NEM chu
        khong tra ve mot phan, dung vi ly do do. Ket qua mot phan cua no khong
        duoc phep ton tai du mot dong.
      - `index_by_names` la phep do best-effort: idx mot phan chi lam `resolved`
        nho di, khong lam hong gi. Giu lai de con dem duoc "da do bao nhieu".
    """


def collect_refs(draft_dir: Path, nen_dung=None):
    """Quet moi file .json trong draft. Tra:
       refs      : {path_tuyet_doi: {"files": {json_rel,...}, "keys": {key,...}}}
       need_copy : path phai GOM them (chua nam san dung cho trong goi)
       json_fail : file .json doc loi (dua vao bao cao, KHONG nuot)
       n_json    : tong so file .json da quet
    """
    refs, need_copy, json_fail = {}, set(), []
    files = iter_json_files(draft_dir)
    root_cache = {}
    for jf in files:
        # Pha nay do duoc 17,73 s tren project that o NAS (457 json / 4401 ref).
        # Khong co moc o day thi nut "Dung do" cam suot 18 giay dau.
        if nen_dung and nen_dung():
            raise _DaHuy("dang doc file .json cua draft")
        try:
            obj, _ = read_json_loose(jf)
        except Exception as ex:
            json_fail.append((_rel_posix(jf, draft_dir) or str(jf), str(ex)))
            continue
        jrel = _rel_posix(jf, draft_dir) or str(jf)
        base = draft_root_of(jf, draft_dir, root_cache)

        role = json_role(jf.name)

        def cb(k, v, _jrel=jrel, _base=base, _role=role):
            if not is_real_abs(v):
                return
            rec = refs.setdefault(v, {"files": set(), "keys": set(), "roles": set()})
            rec["files"].add(_jrel)
            rec["keys"].add(k or "")
            rec["roles"].add(_role)
            # Nam san TRONG thu muc cua chinh file JSON do va co that -> khong can gom,
            # chi can viet lai thanh duong dan tuong doi.
            np = _np(v)
            if _is_under(np, _base) and isfile_safe(np):
                return
            need_copy.add(v)

        deep_walk_strings(obj, cb)
    return refs, need_copy, json_fail, len(files)


# --------------------------------------------------------------------------
# Pha 2: LEN KE HOACH viet lai + copy (chua dong vao dia)
# --------------------------------------------------------------------------

def plan_package(out_dir: Path, draft_dir: Path, resolved: dict, guid: str,
                 gather_only=None, opt_by_src=None):
    """Duyet moi .json trong BAN XUAT, quyet dinh moi path tuyet doi se thanh gi.

    opt_by_src: {(draft_root_normcase, src_normcase): dest} - bang do pha TOI UU tra ve.
      Path goc nao DA CO ban toi uu thi tro thang sang ban do, KHONG copy ban goc nua.
      Thieu buoc nay thi so dang ky (draft_meta_info.json) + file cache van giu path goc
      -> lap ke hoach copy ca tram GB ban goc dang le da duoc thay (bug #23).

    Tra:
      plans      : {json_rel: {old_path: (dang_ph, dang_./)}}
      copy_plan  : {dest_str: src_Path}   - media can copy them
      unresolved : {old_path: {json_rel,...}} - khong tim thay nguon -> giu nguyen
      json_fail  : file .json doc loi
    """
    plans, copy_plan, unresolved, json_fail = {}, {}, {}, []
    used_by_base, placed, root_cache = {}, {}, {}
    # Tra nhanh theo RIENG file nguon (khong phan biet draft root): so dang ky/cache
    # cua root nay co the tro toi file da duoc toi uu o root khac.
    opt_any = {}
    for (_b, _s), _d in (opt_by_src or {}).items():
        opt_any.setdefault(_s, _d)

    def place(base: Path, src: Path) -> str:
        """Chon ten duy nhat trong <base>/materials/ cho file nguon src (dedupe theo base)."""
        bkey = os.path.normcase(str(base))
        skey = os.path.normcase(str(src))
        if (bkey, skey) in placed:
            return placed[(bkey, skey)]
        matdir = base / "materials"
        used = used_by_base.get(bkey)
        if used is None:
            used = set()
            try:
                for x in os.listdir(_lp(matdir)):
                    used.add(x.lower())
            except OSError:
                pass
            used_by_base[bkey] = used
        b = Path(src).name
        stem, suf = Path(b).stem, Path(b).suffix
        name, n = b, 1
        while name.lower() in used:
            name = f"{stem}_{n}{suf}"
            n += 1
        used.add(name.lower())
        placed[(bkey, skey)] = name
        copy_plan[str(matdir / name)] = Path(src)
        return name

    for jf in iter_json_files(out_dir):
        try:
            obj, _ = read_json_loose(jf)
        except Exception as ex:
            json_fail.append((_rel_posix(jf, out_dir) or str(jf), str(ex)))
            continue
        jrel = _rel_posix(jf, out_dir) or str(jf)
        base = draft_root_of(jf, out_dir, root_cache)
        # Che do 4: KHONG dat ban copy chi vi mot file CACHE nhac toi media do.
        # Neu khong, 1 file dung o timeline goc se bi nhan ban vao materials/ cua moi
        # draft root co mini_draft.json/draft_agency_*.json nhac den no (do duoc:
        # 776 ban dat -> 1586 ban dat, 51.6 GB -> 150.9 GB).
        skip_place = gather_only is not None and json_role(jf.name) == "cache"
        mapping = {}

        def cb(k, v, _base=base, _jrel=jrel, _m=mapping):
            if not is_real_abs(v) or v in _m:
                return
            # Che do 4: path khong nam trong tap "dung that" -> KHONG gom, giu nguyen.
            # (No chi xuat hien o kho/cache; se duoc don o buoc prune_registry.)
            if gather_only is not None and v not in gather_only:
                return
            if skip_place:
                return
            np = _np(v)
            # (0) File nay DA CO ban toi uu (da ma lai xong o pha truoc) -> tro thang
            #     sang ban do. KHONG copy ban goc: no chinh la thu ta co y thay the.
            #     Neu bo qua nhanh nay, so dang ky + cache van giu path goc nen ke hoach
            #     copy phinh len ca tram GB (bug #23).
            if opt_any:
                srck = os.path.normcase(str(resolved.get(v) or np))
                dest = (opt_by_src or {}).get((os.path.normcase(str(_base)), srck)) \
                    or opt_any.get(srck)
                if dest is not None and isfile_safe(dest):
                    rp = _rel_posix(dest, _base)
                    if rp:
                        _m[v] = _new_path_forms(rp, guid)
                        return
            # (1) File da nam san trong goi, DUOI thu muc cua chinh file JSON nay
            #     -> chi viet lai thanh tuong doi, KHONG ton them byte nao.
            if _is_under(np, draft_dir):
                sub = _rel_posix(np, draft_dir)
                if sub:
                    cand = out_dir / sub.replace("/", os.sep)
                    rp = _rel_posix(cand, _base)
                    if rp and isfile_safe(cand):
                        _m[v] = _new_path_forms(rp, guid)
                        return
            # (2) Phai dat 1 ban duoi <base>/materials/
            src = resolved.get(v)
            if src is None and isfile_safe(np):
                src = Path(np)
            if src is None:
                unresolved.setdefault(v, set()).add(_jrel)
                return
            _m[v] = _new_path_forms("materials/" + place(_base, src), guid)

        deep_walk_strings(obj, cb)
        if mapping:
            plans[jrel] = mapping
    return plans, copy_plan, unresolved, json_fail


# --------------------------------------------------------------------------
# Pha 4: TU KIEM tren BAN XUAT (quet de quy - chong bao "DU" sai)
# --------------------------------------------------------------------------

def verify_package(out_dir: Path, draft_dir=None):
    """draft_dir: neu truyen vao, tham chieu nao VON DA HONG SAN trong draft goc se
    duoc xep loai 'khong chan' - vi ta khong lam no hong, va mang sang may khac no
    cung khong te hon may goc. Do tren project that: 2325/2366 tham chieu hong la
    cache CapCut tu sinh (Resources/videoAlg/...) da thieu san tu truoc."""
    """Quet MOI file .json trong ban xuat, kiem tra tung tham chieu media.
    Tra list (json_rel, path, ly_do, cosmetic)."""
    bad = []
    root_cache = {}
    for jf in iter_json_files(out_dir):
        try:
            obj, _ = read_json_loose(jf)
        except Exception as ex:
            bad.append((_rel_posix(jf, out_dir) or str(jf), "", f"doc JSON loi: {ex}", False))
            continue
        jrel = _rel_posix(jf, out_dir) or str(jf)
        base = draft_root_of(jf, out_dir, root_cache)
        # Tham chieu trong file CACHE (mini_draft, draft_agency_*) khong dung de dung
        # hinh -> hong cung KHONG anh huong video xuat ra. Coi la canh bao, khong chan.
        is_cache = json_role(jf.name) == "cache"
        seen = set()

        def cb(k, v, _base=base, _jrel=jrel, _seen=seen, _cache=is_cache):
            if not isinstance(v, str) or not v:
                return
            ext = Path(v.replace("\\", "/")).suffix.lower()
            if ext not in MEDIA_EXT:
                return
            if v in _seen:
                return
            _seen.add(v)
            cos = is_cosmetic(k, v) or _cache
            if is_real_abs(v):
                # Con duong dan tuyet doi = KHONG tu chua (may nhan se doi relink)
                bad.append((_jrel, v, "con duong dan TUYET DOI (chua viet lai)", cos))
                return
            if v.startswith("##"):
                i = v.find("_##")
                if i == -1:
                    return
                tail = v[i + 3:].lstrip("/\\")
            elif v.startswith("./") or v.startswith(".\\"):
                tail = v[2:].lstrip("/\\")
            else:
                return          # path la (khong xac dinh) -> bo qua
            fp = _base / tail.replace("/", os.sep)
            if not isfile_safe(fp):
                # Von da hong san trong draft goc? -> khong phai loi cua ta, khong chan.
                pre_broken = False
                if draft_dir is not None:
                    rel = _rel_posix(fp, out_dir)
                    if rel and not isfile_safe(Path(draft_dir) / rel.replace("/", os.sep)):
                        pre_broken = True
                bad.append((_jrel, v,
                            "hong SAN tu draft goc (CapCut tu tao lai)" if pre_broken
                            else "tro toi file KHONG co tren dia",
                            cos or pre_broken))

        deep_walk_strings(obj, cb)
    return bad


# --------------------------------------------------------------------------

def json_fail_hard(danh_sach):
    """Loc cac file .json doc loi THUC SU anh huong: chi content + registry.

    File CACHE cua CapCut (mini_draft.json, draft_agency_*.json...) hong SAN trong
    draft goc thi khong anh huong video xuat ra. `verify_package()` da biet ha cap
    chung qua `json_role`, nhung `json_fail` thi khong -> mot file cache hong san
    khien tool VINH VIEN ket luan "CON THIEU" o moi lan chay, va nguoi dung khong
    co cach nao lam cho no sach. Day la bao dong gia, dung ho bai hoc #31/#39:
    bao dong gia lam mat niem tin vao ca lop tu kiem.
    """
    ra = []
    for a, b in danh_sach:
        ten = Path(str(a).replace("\\", "/")).name
        if json_role(ten) != "cache":
            ra.append((a, b))
    return ra




def import_toi_uu():
    """Nap module toi_uu_dung_luong.py (nam canh file nay).

    PHAI them thu muc cua chinh file nay vao sys.path truoc khi import: khi tool duoc
    goi tu mot thu muc khac (shortcut co 'Start in' khac, runpy, wrapper tu dong...)
    thi sys.path[0] KHONG phai thu muc chua tool -> import se ModuleNotFoundError."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import toi_uu_dung_luong as TU
    return TU


def phan_loai_path_dai(long_paths, out_dir, limit: int = 259):
    """Chia duong dan qua dai lam HAI loai - vi cach xu ly khac han nhau.

    Loi khuyen "hay dat folder XUAT RA o duong dan ngan hon" chi dung khi do dai
    den TU thu muc dich. Do tren project that DS3_006: mot anh CapCut tai ve tu
    CMS co ten dai 205 ky tu (chuoi base64 dung lam ten file), khien rieng PHAN
    TUONG DOI trong goi da 280 ky tu - vuot 260 truoc ca khi cong thu muc dich.
    Voi file do, rut ngan dich xuong `D:\\` (3 ky tu) van la 283. Loi khuyen kia
    la loi khuyen KHONG THE LAM DUOC, va bao cao noi doi con te hon khong noi.

    Tra (rut_ngan_duoc, khong_cuu_duoc, do_dai_toi_da_cua_dich).
    """
    goc = len(str(_unlp(str(out_dir))).rstrip("\\/"))
    rut_ngan_duoc, khong_cuu_duoc, phan_tuong_doi_max = [], [], 0
    for p in long_paths:
        # Phan tuong doi = phan CapCut sinh ra, nguoi dung khong doi duoc
        n_rel = max(0, len(p) - goc - 1)
        phan_tuong_doi_max = max(phan_tuong_doi_max, n_rel)
        # Dat o goc ngan nhat co the (`D:\` = 3) thi con vuot khong?
        if 3 + 1 + n_rel > limit:
            khong_cuu_duoc.append((p, n_rel))
        else:
            rut_ngan_duoc.append((p, n_rel))
    # Do dai toi da cua thu muc dich de KHONG file nao vuot gioi han
    toi_da = limit - 1 - phan_tuong_doi_max
    return rut_ngan_duoc, khong_cuu_duoc, toi_da


def scan_long_paths(out_dir, limit: int = 259):
    """Liet ke file trong ban xuat co duong dan vuot gioi han 260 ky tu cua Windows.
    Tool doc/ghi duoc nho _lp, NHUNG CapCut (hoac Explorer) co the KHONG mo duoc.
    Gom media vao subdraft/<GUID>/materials/ lam path sau hon truoc -> phai canh bao."""
    out = []
    # Quet thieu -> bao "0 duong dan qua dai" SAI, tuc canh bao bien mat dung luc
    # can no. Nem de chay len `verify_loi` (main da boc san) thay vi noi doi.
    _loi_walk = []
    for dp, dirs, fs in os.walk(_lp(out_dir), onerror=_loi_walk.append):
        for f in fs:
            p = _unlp(os.path.join(dp, f))
            if len(p) > limit:
                out.append(p)
    if _loi_walk:
        raise OSError(f"khong duyet duoc {len(_loi_walk)} thu muc khi quet duong"
                      f" dan dai: {_loi_walk[0]}"
                      f"  -> khong duoc bao '0 duong dan qua dai' khi quet thieu")
    return out


def index_by_names(roots, wanted, on_progress=None, on_error=None,
                   nen_dung=None, thong_ke=None):
    """Do file theo TEN tren cac goc `roots`.

    A5: PHAI quet qua _lp(), neu khong moi thu muc nam sau gioi han 260 ky tu deu
    bi bo qua va ta bao "THIEU" oan cho file van con nam do (do thuc te: path 506
    ky tu -> khong _lp tim thay 0 file, co _lp tim thay 1).
    Ngoai ra `os.walk` mac dinh NUOT loi (onerror=None): mot thu muc khong doc duoc
    se bien mat khoi ket qua ma khong ai biet. Phai dem lai va bao ra.

    `nen_dung`: ham () -> bool, PHAI KHONG BAO GIO NEM (dung `threading.Event.is_set`).
        Duoc goi MOI THU MUC. Chi phi do duoc 41-48 ns/lan -> 853.271 thu muc chi
        het 0,029 s = 0,046% tong thoi gian, nam duoi san nhieu cua phep do.
        Kiem thua ra moi 3000 thu muc thi tiet kiem duoc 0,029 s do NHUNG lam do
        tre huy tang len 5,3 s (o cuc bo) va 8,0 s (o mang) - DUNG LAM.
    `thong_ke`: dict duoc ghi nguoc ra: quet / da_dung / goc / loi.
        `on_progress` chi de IN TIEN DO, TUYET DOI khong duoc dung lam nguon so
        lieu cho bao cao: no chi ban moi 3000 thu muc nen lech toi 2999 (do that:
        quet 1501 thu muc bao 0, quet 4971 bao 3000).
    """
    idx = {}
    remaining = set(wanted)
    scanned = 0
    loi = []
    # Khu trung root: nguoi dung bam "Them thu muc..." nhieu lan hoac dan lap se
    # lam ta quet cung mot cay N lan (do that: 3 lan -> 3723 thu muc/0,130s thay
    # vi 1241/0,038s). Khong sai ket qua nhung phi thoi gian cua ho.
    _da, _loc = set(), []
    for _r in roots:
        try:
            _k = os.path.normcase(os.path.normpath(str(_r)))
        except Exception:
            _k = str(_r).lower()
        if _k not in _da:
            _da.add(_k)
            _loc.append(_r)
    roots = _loc
    if thong_ke is not None:
        # Ghi NGAY, TRUOC vong lap: neu moi root deu isdir_safe=False thi ta van
        # phai bao duoc "quet 0 thu muc" va "goc nao da duoc dua vao".
        thong_ke.update({"quet": 0, "da_dung": False,
                         "goc": [str(r) for r in roots], "loi": 0})
    ngat = False
    for root in roots:
        # Kiem TRUOC `isdir_safe`: neu mot root la host SMB chet thi chinh loi
        # goi do chan 21,03 s va khong cach nao cat duoc (Python khong co timeout
        # cho I/O filesystem - #25/#28/#37). Do that: co moc 0,010 s, khong co
        # moc 21,057 s.
        if nen_dung and nen_dung():
            ngat = True
            break
        root = Path(root)
        if not isdir_safe(root):
            continue
        for dp, dirs, fs in os.walk(_lp(root), onerror=loi.append):
            # DAT TRUOC `scanned += 1`: nhu vay `quet` la so thu muc da xu ly
            # XONG, dung nghia voi cau "da do N thu muc" in ra cho nguoi dung.
            if nen_dung and nen_dung():
                ngat = True
                break
            scanned += 1
            if on_progress and scanned % 3000 == 0:
                on_progress(scanned, len(idx), len(wanted))
            plain = _unlp(dp)
            for f in fs:
                fl = f.lower()
                if fl in remaining and fl not in idx:
                    idx[fl] = Path(plain) / f
                    remaining.discard(fl)
            if not remaining:
                break
        if ngat or not remaining:
            break
    if loi and on_error:
        on_error(loi)
    if thong_ke is not None:
        thong_ke["quet"] = scanned
        thong_ke["da_dung"] = ngat
        thong_ke["loi"] = len(loi)
    return idx


def kiem_tien_de():
    """G1: kiem MOI THU tool can, NGAY khi khoi dong. Tra list loi (rong = on).

    Truoc day thieu `toi_uu_dung_luong.py` thi che do 4 chi chet bang traceback
    SAU KHI nguoi dung da tra loi xong het cau hoi va bam 'y' - mat toan bo phan
    hoi dap, va thong bao loi ('ModuleNotFoundError') khong noi len van de that
    la "ban chep thieu file". Voi 15-20 nguoi dung tu chep thu muc sang may minh,
    day la loi se xay ra.
    """
    loi = []
    # DOC tai nguyen: khi dong goi .exe day co the la thu muc giai nen tam,
    # khong phai thu muc chua .exe.
    try:
        from loi import phien_ban as _PB
        goc = _PB.thu_muc_tai_nguyen()
    except ImportError:
        _PB = None
        goc = Path(__file__).resolve().parent

    # 1. Phien ban Python: f-string co '=' va os.replace deu can >= 3.8
    if sys.version_info < (3, 8):
        loi.append(f"Python qua cu: dang chay {mo_ta_moi_truong()[0]},"
                   f" tool can 3.8 tro len.")

    # 2. Cac file bat buoc phai co (chep thieu mot file la hong).
    #    KHONG kiem `chung.py` o day: neu no thieu thi khoi try/except quanh
    #    `from chung import ...` o dau file DA thoat truoc khi den duoc ham nay.
    #    Kiem lai o day la NHANH CHET - te hon vo dung, vi no lam nguoi doc tuong
    #    da co lop bao ve trong khi lop that nam cho khac.
    for ten, vi_sao in (("toi_uu_dung_luong.py", "che do 4 - toi uu dung luong"),):
        if not isfile_safe(goc / ten):
            loi.append(f"THIEU file `{ten}` ({vi_sao}) trong {goc}."
                       f" Hay chep LAI CA THU MUC tool, dung chep tung file.")

    # 3. Nap thu module toi uu - bat loi cu phap / import hong ngay bay gio
    if isfile_safe(goc / "toi_uu_dung_luong.py"):
        try:
            import_toi_uu()
        except Exception as ex:
            loi.append(f"Khong nap duoc `toi_uu_dung_luong.py`:"
                       f" {type(ex).__name__}: {ex}")

    # 4. Quyen ghi. PHAI kiem NOI GHI THAT chu khong phai thu muc tai nguyen:
    #    khi dong goi onefile, thu muc tai nguyen la thu muc giai nen TAM (se
    #    bien mat), con khi cai vao `Program Files` thi thu muc chuong trinh
    #    khong ghi duoc va tool da tu lui ve `%LOCALAPPDATA%`. Kiem nham cho se
    #    bao loi OAN tren mot ban cai hoan toan binh thuong.
    #    Cung KHONG dung `os.access(W_OK)`: tren Windows no doc quyen he thong
    #    chu khong tinh UAC virtualization -> tra ket qua sai. Thu GHI THAT.
    if _PB is not None:
        noi_ghi = _PB.thu_muc_ghi()
        if not _PB._ghi_duoc(noi_ghi):
            loi.append(f"Khong ghi duoc vao {noi_ghi} - mot so buoc se that bai.")
    elif not os.access(str(goc), os.W_OK):
        loi.append(f"Khong co quyen ghi trong {goc} - mot so buoc se that bai.")
    return loi


def cuu_ban_goc_bi_bo_qua(out_dir, draft_dir, skip_media, opt_stat, log=print):
    """NGHIEM THU DU DOAN: file nao bi bo qua copytree ma KHONG duoc thay -> cuu ve.

    `skip_media` la mot DU DOAN lap truoc khi ma lai: "file nay chac chan se duoc
    thay bang ban toi uu, nen khoi copy vao goi cho do ton duong truyen". Du doan
    do co the SAI, it nhat ba duong:
      - `no_gain`: ma xong thay khong nho hon 8% -> xoa ban ma, "giu ban goc"
      - ma lai THAT BAI -> "giu ban goc"
      - material bi loai khoi viec ma lai (`bo_qua`)
    Ca ba nhanh deu ket luan "giu ban goc" - nhung ban goc DA BI BO QUA o copytree
    nen no khong he nam trong goi. Ket qua: file bien mat khoi CA HAI dang.

    Do tren project that DS3_003: `A_hyperrealistic_octopus_...87kyy.mp4` (7,02 MB)
    co trong nguon, KHONG co trong goi, bi 6 file JSON tro toi ke ca `draft_content.json`.
    May cha van mo duoc (path cu con tren o dia); MAY CON MAT HINH.

    Vi vay: do tren KET QUA THAT o dich, khong tin du doan (checklist bug.md).
    Tra list duong dan da cuu.
    """
    da_thay = {s for (_b, s) in ((opt_stat or {}).get("opt_by_src") or {})}
    cuu, that_bai = [], []
    for src in sorted(skip_media or ()):
        if os.path.normcase(str(src)) in da_thay:
            continue                       # dung la da duoc thay -> khong sao
        try:
            rel = os.path.relpath(str(src), str(draft_dir))
        except ValueError:                 # khac o dia - khong the o trong draft_dir
            continue
        if rel.startswith(".."):
            continue
        dest = Path(out_dir) / rel
        if isfile_safe(dest):
            continue                       # da co san trong goi
        try:
            Path(_lp(dest.parent)).mkdir(parents=True, exist_ok=True)
            shutil.copy2(_lp(str(src)), _lp(dest))
            cuu.append(str(dest))
        except OSError as ex:
            that_bai.append((str(dest), f"{type(ex).__name__}: {ex}"))
    if cuu:
        log(f"  CUU {len(cuu)} ban goc bi bo qua nham (du doan se duoc thay nhung"
            f" khong duoc thay) -> neu thieu buoc nay, may khac se MAT HINH")
    if that_bai:
        # Khong duoc im lang: cuu that bai = file van mat o may con.
        log(f"  ! {len(that_bai)} ban goc CUU KHONG DUOC -> xem bao cao")
        (opt_stat or {}).setdefault("fail", []).extend(
            [(d, f"cuu ban goc bi bo qua nham that bai: {e}") for d, e in that_bai])
    return cuu


def main(tuy_chon=None):
    """tuy_chon: dict {trim, scale, cleanup} do GIAO DIEN truyen vao.

    None = chay tu dong lenh -> giu nguyen hanh vi cu (bat ca ba khi chon che do 4).
    """
    # Vo bao mong CHI de bao dam canh gac luon duoc tat. Than that nam o
    # `_main_than`. Vi sao can vo nay: than co 13 duong `return` (huy giua
    # chung, thieu dieu kien, loi o mang...). O che do DONG LENH thi khong sao
    # - tien trinh thoat la thread daemon chet theo. Nhung o che do GIAO DIEN
    # thi `main()` tra ve ma tien trinh VAN SONG, nen mot canh gac quen tat se
    # tiep tuc lay mau va sau 5 phut giao dien nam im se in "CANH BAO khong
    # thay tien trien" - mot bao dong khong, dung loai lam nguoi dung het tin.
    _giu_gac = []
    # XOA BO NHO DEM cua lan chay TRUOC. Bat buoc khi `main()` duoc goi NHIEU
    # LAN trong CUNG mot tien trinh (hang doi nhieu project): project sau se
    # thua huong cache cua project truoc -> bao THIEU FILE oan, hoac tuong file
    # da xoa van con. Ca hai deu im lang. Xem `xoa_cache_ton_tai()`.
    # O che do dong lenh moi lan chay la mot tien trinh moi nen khong anh huong.
    try:
        _TU = import_toi_uu()
        _TU.xoa_cache_ton_tai()
        _TU.xoa_cache_probe()
    except Exception:
        # Thieu module toi uu KHONG duoc chan lan chay - che do 1 (copy nguyen)
        # van dung duoc. `kiem_tien_de()` da bao ro chuyen thieu file roi.
        pass
    try:
        return _main_than(tuy_chon, _giu_gac)
    finally:
        for _g in _giu_gac:
            try:
                _g.dung()
            except Exception:
                pass


def _main_than(tuy_chon, _giu_gac):
    print("=" * 64)
    print(" GOI PROJECT CAPCUT -> TU CHUA (doc SO DANG KY + DU AN CON/subdraft)")
    _py, _he = mo_ta_moi_truong()
    print(f" Phien ban {TOOL_VERSION}  |  Python {_py}  |  {_he}")
    print("=" * 64)

    # ---- MOC HUY ----------------------------------------------------------
    # PHAI doc O DAY, khong duoc doc canh `_tc` phia duoi: dong do nam TRONG
    # `if ... == "4":` VA trong nhanh `else:` cua phep kiem ffmpeg. Che do 1,
    # hoac che do 4 tren may co ffmpeg hong, se khong bao gio thay no -> nut
    # "Dung do" cam hoan toan (do that: thua 36,77 s va 46,62 s).
    _nen_dung = (tuy_chon or {}).get("nen_dung")

    def _da_huy():
        return bool(_nen_dung and _nen_dung())

    def _thoat_huy(o_dau):
        """Loi ra DUY NHAT cho moi cho bi huy TRUOC cau hoi 'Tien hanh?'.

        CANH BAO cho nguoi sua sau: moi duong huy deu `return` TRUOC khoi ghi
        `_BAO_CAO_THIEU.txt`, nen file do khong ton tai sau khi huy va khong co
        gi noi doi. Neu sau nay ai cho phep "huy do nhung van goi tiep" thi dong
        `THIEU (khong tim thay o bat ky o nao)` trong file bao cao se mang nguyen
        loi noi doi cua #92 vao ban ban giao - phai sua no cung luc.
        """
        print("\n  === DA DUNG THEO YEU CAU ===")
        print(f"    (dang o buoc: {o_dau})")
        print("    CHUA COPY GI CA - thu muc XUAT RA khong duoc tao,"
              " project GOC khong bi dong toi.")
        print("    Bam '1) QUET' lai la chay lai duoc - khong phai dong cua so.")
        print("Da huy.")
    # -----------------------------------------------------------------------

    # ---- CANH GAC ---------------------------------------------------------
    # Phat hien tool bi TREO VINH VIEN tren o mang (#25 muc c). Phai bao HET
    # main() chu khong chi `optimize_package()`: do duoc 601 loi goi filesystem
    # trong mot lan chay, 421 nam ngoai moi vung co nhip dap.
    # Canh gac KHONG BAO GIO tu giet tien trinh - no chi noi, nguoi dung quyet.
    try:
        import canh_gac
        _gac = canh_gac.CanhGac()
        if _gac.bat_dau():
            _giu_gac.append(_gac)      # de vo `main()` tat duoc o `finally`
        else:
            _gac = None
    except Exception as _ex:
        # Canh gac hong KHONG duoc lam hong lan chay - nhung cung khong duoc im.
        print(f"  ! Khong bat duoc canh gac ({_ex}) - lan chay nay se khong co"
              f" canh bao neu bi treo tren o mang.")
        _gac = None

    def _pha(ten):
        """Danh dau dang o buoc nao. CHI de canh gac NOI dang ket o dau -
        khong tham gia vao viec ket luan song/chet."""
        if _gac:
            _gac.dat_pha(ten)
    # -----------------------------------------------------------------------

    # G1: chan NGAY o day, truoc khi hoi bat ky cau nao. Phat hien som mot loi
    # cai dat dang gia hon nhieu so voi chet giua chung sau 20 phut hoi dap.
    _loi_td = kiem_tien_de()
    if _loi_td:
        print("\n  ! KHONG THE CHAY - thieu dieu kien:")
        for d in _loi_td:
            print(f"      - {d}")
        print("\n  Sua xong roi chay lai.")
        return

    draft_dir = choose_draft()
    print(f"\n-> Da chon: {draft_dir}")

    # --- Bao cho nguoi dung biet project nay CO dung 'Du an con' hay khong ---
    sub_imported, sub_compound = scan_subprojects(draft_dir)
    if sub_imported:
        print(f"\n  >> CO DU AN CON: {len(sub_imported)} cai"
              + (f" (+ {len(sub_compound)} clip ghep)" if sub_compound else ""))
        for p, depth in sub_imported:
            nm, src = subproject_origin(p)
            pad = "    " * (depth - 1)
            print(f"     {pad}- {nm}")
            print(f"     {pad}  (nhap tu: {src})")
        print("     -> tool se gom ca media cua cac du an con nay (moi tang).")
    elif sub_compound:
        print(f"\n  >> Khong co du an con nhap tu ngoai."
              f" Chi co {len(sub_compound)} clip ghep trong chinh project.")
    else:
        print("\n  >> Project nay KHONG dung du an con.")
    content_name = CONTENT_NAMES[0] if (draft_dir / CONTENT_NAMES[0]).is_file() else CONTENT_NAMES[1]
    content, content_trail = read_json_loose(draft_dir / content_name)
    meta, meta_trail = read_json_loose(draft_dir / "draft_meta_info.json")

    gmatch = PLACEHOLDER_RE.search(json.dumps(content))
    guid = gmatch.group(1) if gmatch else DEFAULT_GUID

    default_out = draft_dir.parent / (draft_dir.name + "_PORTABLE")
    out_in = input(f"\nFolder XUAT RA [Enter = {default_out}]: ").strip().strip('"')
    out_dir = Path(out_in) if out_in else default_out

    # --- CHAN 1: dua ve TUYET DOI ngay (bug #23) ---
    # "D:" KHONG phai goc o dia - Windows hieu la drive-relative va noi am tham vao
    # thu muc hien hanh. Path tuong doi ("goi_moi") cung vay. Neu de nguyen, moi thao
    # tac phia sau se lam viec tren mot dich KHAC voi cai nguoi dung nghi.
    out_dir = Path(os.path.abspath(_unlp(out_dir)))

    # --- CHAN 2: dich KHONG duoc trung hoac nam trong project goc ---
    # Neu lot: dong ghi 3 file JSON goc se DE LEN chinh draft goc, va che do 4 se
    # ma lai + os.remove media "mo coi" NGAY TRONG project goc - trong khi tool van
    # in "project GOC KHONG bi thay doi". Day la duong duy nhat lam hong du lieu goc.
    if _is_under(out_dir, draft_dir):
        print("\n  ! DUNG LAI: folder XUAT RA nam TRONG (hoac chinh la) folder project goc.")
        print(f"      project goc: {draft_dir}")
        print(f"      xuat ra    : {out_dir}")
        print("      Neu tiep tuc, tool se GHI DE draft goc va co the XOA media trong do.")
        print("      Hay chon mot folder NGOAI project goc.")
        return
    # Chieu nguoc lai cung hong: project goc nam trong folder xuat -> pha don dep
    # (cleanup_unused) se quet ca project goc va xoa file trong do.
    if _is_under(draft_dir, out_dir):
        print("\n  ! DUNG LAI: folder project goc nam TRONG folder XUAT RA.")
        print(f"      project goc: {draft_dir}")
        print(f"      xuat ra    : {out_dir}")
        print("      Pha don dep se quet ca project goc va co the xoa media trong do.")
        print("      Hay chon mot folder KHAC.")
        return

    # --- Che do goi ---
    print("\nCHE DO GOI:")
    print("  1. NGUYEN BAN - copy y nguyen (an toan nhat, nhung nang)")
    print("  4. TOI UU DUNG LUONG - cat gon footage dai (chi giu doan dung)")
    print("       + ha 4K/nen bitrate H.264 theo khung hinh + bo file thua/mo coi/lich su")
    opts, ffmpeg, ffprobe = None, None, None
    if input("Chon 1 hoac 4 [Enter = 1]: ").strip() == "4":
        TU = import_toi_uu()
        ffmpeg, ffprobe = TU.ff_paths()
        # `ff_paths()` chi kiem file CO TON TAI. Phai thu CHAY that: tren may con,
        # ffmpeg.exe co the nam day du do ma thieu DLL / thieu libx264 / bi chan.
        # Khong kiem o day thi nguoi dung cho 15-30 phut roi nhan ve hang tram loi.
        _ff_ok, _ff_vi = (False, "khong tim thay ffmpeg/ffprobe")
        if ffmpeg:
            _ff_ok, _ff_vi = TU.kiem_ffmpeg_chay_duoc(ffmpeg, ffprobe)
        if not _ff_ok:
            print(f"  ! KHONG dung duoc ffmpeg -> khong toi uu duoc: {_ff_vi}")
            print("    -> Se goi NGUYEN BAN (an toan, nhung nang hon).")
            ffmpeg = ffprobe = None
        else:
            _ch = doc_cau_hinh()
            # `tuy_chon` do GUI truyen vao (3 o tich). None = che do dong lenh,
            # giu nguyen hanh vi cu: bat CA BA. Khong duoc doi mac dinh nay -
            # 10 lan chay tren project that deu dung no.
            _tc = tuy_chon or {}
            opts = {"trim": _tc.get("trim", True),
                    "scale": _tc.get("scale", True),
                    "cleanup": _tc.get("cleanup", True),
                    # NEN BITRATE: ma lai H.264 ca nhung clip khong can cat/ha phan giai.
                    # Footage mua thuong 11-50 Mbps; CRF 21 con ~3-5 Mbps.
                    # Di theo o "ha 4K/nen bitrate" tren giao dien.
                    "recompress": _tc.get("scale", True),
                    "crf": _ch["crf"], "preset": _ch["preset"],
                    "workers": chon_so_luong(_ch, out_dir)}
            print(f"  -> Da bat TOI UU DUNG LUONG (ffmpeg: {ffmpeg})")
            print("     Luu y: media se duoc MA LAI (H.264) nen ton them thoi gian CPU;"
                  " project GOC khong bi dong toi.")

    # --- Liet ke media can gom: quet DE QUY moi .json (cha + moi tang subdraft) ---
    _pha("quet file JSON cua draft")
    print("\nDang quet toan bo file JSON cua draft (ke ca du an con long nhieu tang)...")
    try:
        refs, need_copy, json_fail, n_json = collect_refs(draft_dir,
                                                          nen_dung=_nen_dung)
    except _DaHuy as ex:
        _thoat_huy(str(ex))
        return
    except OSError as ex:
        # `iter_json_files` gio NEM khi khong duyet het duoc cay thu muc. O day
        # ta chua gom gi ca, nen dung han la dung: quet thieu -> ke hoach thieu ->
        # goi thieu ma khong ai biet. Bao ro thay vi traceback tho.
        print("\n  ! KHONG QUET DUOC HET project goc:")
        print(f"    {ex}")
        print("    Thuong gap khi: o mang rot phien (WinError 71), thu muc bi khoa")
        print("    quyen, hoac o cam bi rut. Hay kiem tra ket noi roi chay lai.")
        return
    n_sub = sum(1 for r in refs.values() for f in r["files"] if f.startswith("subdraft/"))
    print(f"  Da quet {n_json} file .json | {len(refs)} duong dan media tuyet doi duoc khai bao")
    print(f"  Trong do {len(need_copy)} file phai GOM (chua nam dung cho trong goi)")
    if json_fail:
        print(f"  ! {len(json_fail)} file .json doc khong duoc (se ghi vao bao cao)")

    # --- CHE DO 4: chi gom media THUC SU DUNG tren timeline ---
    # Do tren project that: 3133 file (355 GB) chi xuat hien o file cache/kho, tuc la
    # footage KHONG dung. Gom chung se lam ban xuat phinh gap ~8 lan va chay hang chuc gio.
    gather_only = None
    if opts:
        gather_only = {p for p, r in refs.items() if "content" in r.get("roles", set())}
        bo = need_copy - gather_only
        bo_bytes = 0
        for p in bo:
            if _da_huy():
                break
            np = _np(p)
            if isfile_safe(np):
                try:
                    bo_bytes += os.path.getsize(_lp(np))
                except OSError:
                    pass
        need_copy = need_copy & gather_only
        print(f"  CHE DO 4: bo {len(bo)} file chi nam o kho/cache (~{bo_bytes/1e9:.2f} GB)"
              f" -> chi gom {len(need_copy)} file dung that")
        if _da_huy():
            _thoat_huy("do dung luong nhom file khong dung (che do 4)")
            return

    # --- Resolve: exact path -> else theo ten ---
    resolved, misses = {}, []
    _pha("Pass 1 - kiem tung duong dan goc")
    for p in sorted(need_copy):
        # `isfile_safe` do duoc 0,478-0,557 ms/lan tren NAS -> 4401 ref ~ 2,4 s.
        if _da_huy():
            break
        np = _np(p)
        if isfile_safe(np):
            resolved[p] = Path(np)
        else:
            misses.append(p)
    if _da_huy():
        _thoat_huy("Pass 1 - kiem tung duong dan goc")
        return
    print(f"  Pass 1 (path goc): co {len(resolved)}, chua thay {len(misses)}")
    # So thu muc THAT + co "bi ngat", do chinh `index_by_names` ghi nguoc ra.
    # BO HAN `_da_quet`: no lay so tu `on_progress` (chi ban moi 3000 thu muc)
    # nen SAI SAN - do that: quet 1501 thu muc bao "CHUA DO O DAU CA", quet
    # 4971 thu muc bao "3000". Mot bo dem de in tien do khong duoc phep tro
    # thanh nguon so lieu cho bao cao.
    _tk_do = {}
    if misses:
        drives = fixed_drives()
        print(f"  {len(misses)} file khong o path goc -> DO THEO TEN.")
        # Noi bang "; " cho KHOP voi dau tach ma ta doc lai o duoi. In dau
        # phay o day la day nguoi dung go sai roi ca chuoi thanh MOT path rac.
        print("  O phat hien:", "; ".join(str(d) for d in drives) or "(khong)")
        print("  (o MANG va USB KHONG duoc quet tu dong - muon do o do thi go"
              " duong dan vao)")
        extra = input("  Thu muc/o de do (nhieu thu muc cach nhau bang dau ';')"
                      " [Enter = chi quet o trong may]: ").strip()
        if not extra:
            roots = drives
        elif isdir_safe(Path(extra.strip().strip('"'))):
            # CA CHUOI la mot thu muc co that -> KHONG tach, du ten co chua ';'
            roots = [Path(extra.strip().strip('"'))]
        else:
            # strip nhay kep TUNG PHAN TU: Windows "Copy as path" cho ra co nhay,
            # dan hai thu muc se thanh '"A";"B"' -> strip ca chuoi chi go duoc
            # hai dau ngoai cung, hai phan tu ben trong van hong.
            roots = [Path(x.strip().strip('"')) for x in extra.split(";")
                     if x.strip().strip('"')]
            bo = [r for r in roots if not isdir_safe(r)]
            roots = [r for r in roots if isdir_safe(r)]
            if bo:
                print(f"  ! {len(bo)} thu muc KHONG TON TAI -> se KHONG duoc do:")
                for r in bo:
                    print("      X", r)
                print("      (nhieu thu muc phai cach nhau bang dau ';',"
                      " khong phai dau phay hay xuong dong)")
            if not roots:
                print("  ! KHONG con thu muc hop le -> BO QUA hoan toan buoc"
                      " do theo ten.")
                print("  ! Muc THIEU duoi day KHONG co nghia la file khong ton"
                      " tai - tool CHUA HE QUET O DAU CA.")
        wanted = {Path(p.replace("\\", "/")).name.lower() for p in misses}
        def prog(n, got, tot):
            # CHI de in tien do. KHONG con la nguon so lieu cho bao cao.
            print(f"    ...{n} thu muc, thay {got}/{tot}")
        _pha("do theo ten tren cac o")
        print("  Dang do theo ten (dung som khi du)...")
        idx = index_by_names(
            roots, wanted, on_progress=prog,
            nen_dung=_nen_dung, thong_ke=_tk_do,
            on_error=lambda ls: print(f"    ! {len(ls)} thu muc khong doc duoc"
                                      f" (vd: {ls[0]})"))
        still = []
        for p in misses:
            sp = idx.get(Path(p.replace("\\", "/")).name.lower())
            if sp:
                resolved[p] = sp
            else:
                still.append(p)
        misses = still

        if _tk_do.get("da_dung"):
            # BUG #92 SONG LAI NEU BO KHOI NAY. "Khong tim thay" va "chua tim"
            # la HAI ket luan khac nhau. Do that: mot file CO THAT nam o thu muc
            # thu 5.000/6.481 bi tuyen bo "khong thay" khi huy o thu muc 3.500.
            print("\n  === DA DUNG BUOC DO THEO TEN THEO YEU CAU ===")
            print("    Moi do %d thu muc tren %d goc thi ban bam Dung."
                  % (_tk_do.get("quet", 0), len(_tk_do.get("goc", []))))
            print("    %d file duoi day CHUA duoc do xong. Day KHONG phai ket"
                  " luan 'khong tim thay':" % len(misses))
            for p in misses[:30]:
                # Dau "?" chu KHONG phai "X": trong ca tool nay "X" luon nghia la
                # thieu/that bai. Day la "chua biet".
                print("     ?", Path(p.replace(chr(92), "/")).name, "<-", p)
            if len(misses) > 30:
                print(f"     ... +{len(misses)-30} nua")
            print("    Chung CO THE van con nam nguyen tren o - tool chua do het.")
            print("    Lan sau nhanh hon: go DUNG thu muc chua footage vao muc 3"
                  " thay vi de no quet ca o.")
            _thoat_huy("do theo ten")
            return
    # thieu ma chi la anh bia thi khong chan viec bàn giao
    misses_hard = [p for p in misses
                   if not all(is_cosmetic(k, p) for k in refs.get(p, {}).get("keys", {""}))]
    _hard_set = set(misses_hard)
    misses_soft = [p for p in misses if p not in _hard_set]
    print(f"  TONG resolve: {len(resolved)} | THIEU THAT SU: {len(misses_hard)}"
          f" (+{len(misses_soft)} anh bia, khong anh huong video)")

    if misses_hard:
        # Noi ro DA QUET BAO NHIEU thu muc. Bao "THIEU" trong khi chua quet
        # o dau ca la noi doi: nguoi dung se di tim mot file van con nam
        # nguyen do, trong khi that ra tool khong co thu muc nao de do.
        # Ba trang thai chu khong phai hai. Trang thai "dung giua chung" da
        # `return` o tren, nen o day chi con hai nhanh - va ca hai gio lay so
        # THAT tu `_tk_do`, khong lay tu bo dem tien do (%3000).
        if _tk_do.get("quet"):
            print("\n  --- THIEU (da do HET %d thu muc tren %d goc,"
                  " khong thay) ---"
                  % (_tk_do["quet"], len(_tk_do.get("goc", []))))
        else:
            print("\n  --- THIEU (CHUA DO O DAU CA - khong thu muc nao quet duoc) ---")
        for p in misses_hard[:30]:
            print("     X", Path(p.replace("\\", "/")).name, "<-", p)
        if len(misses_hard) > 30:
            print(f"     ... +{len(misses_hard)-30} nua")

    total = 0
    size_of = {}
    for op, sp in resolved.items():
        # `getsize` do duoc 1,52 ms/lan tren NAS that -> 3000 file = 4,6 s,
        # 20.000 file = 30 s. Vong nay chay o CA che do 1 lan che do 4.
        if _da_huy():
            _thoat_huy("do dung luong cac file se gom")
            return
        try:
            sz = os.path.getsize(_lp(sp))
        except OSError:
            sz = 0
        size_of[op] = sz
        total += sz
    # --- Neu bat toi uu: tinh TRUOC nhung file se bi thay -> khoi copy ban goc ---
    skip_media, skip_bytes = set(), 0
    if opts:
        TU = import_toi_uu()
        # Pha nay CHI co ich khi co media nam TRONG folder draft (de bao copytree bo qua).
        # Neu toan bo footage nam ngoai draft thi no chac chan tra ve rong, trong khi van
        # phai hoi hang nghin file qua o MANG (hang chuc phut + rui ro treo - bug #28).
        # => Dem truoc bang du lieu da co san (resolved), chi chay khi that su can.
        n_in_draft = sum(1 for sp in resolved.values() if _is_under(sp, draft_dir))
        if n_in_draft:
            # `plan_replacements` KHONG co moc huy ben trong va da tung treo
            # 75 s (bug #28). Chan o CUA, khong di vao.
            if _da_huy():
                _thoat_huy("truoc pha 'tinh truoc phan se duoc toi uu'")
                return
            _pha("tinh truoc phan se duoc toi uu")
            print("\nDang tinh truoc phan se duoc toi uu (de khoi copy ban goc)...")
            skip_media, skip_bytes = TU.plan_replacements(draft_dir, opts)
            print(f"  {len(skip_media)} file NAM TRONG folder draft se duoc thay"
                  f" -> khoi copytree (~{skip_bytes/1e9:.2f} GB)")
        else:
            print(f"\n  (Bo qua pha 'tinh truoc': ca {len(resolved)} file media deu nam"
                  f" NGOAI folder draft)")
        # Footage thuong nam NGOAI folder draft (o khac / NAS). Nhung file do khong di
        # qua copytree ma qua copy_plan, va se duoc bo o buoc plan_package nho bang
        # opt_by_src (bug #26). Phai noi ro, neu khong '0 file' se bi hieu nham la
        # 'khong toi uu duoc gi' - do chinh la luc phai nghi ngo (xem bug #16, #26).
        print("  -> ban goc cua chung se duoc bo o buoc lap ke hoach copy"
              " (khong ton duong truyen)")

    print(f"\n  Se gom toi da {len(resolved)} file (~{total/1e9:.2f} GB) vao {out_dir}")
    if opts:
        print(f"  Nhung dang bat TOI UU nen thuc te se it hon NHIEU"
              f" (bo qua {skip_bytes/1e9:.2f} GB ban goc + cat gon/nen phan con lai)")
    print("  (file dung chung boi nhieu du an con se duoc lien ket cung, khong nhan doi dung luong)")
    if input("Tien hanh? (y/N): ").strip().lower() != "y":
        print("Da huy.")
        return

    # --- Copy folder draft (mang theo materials/ + subdraft/ da co san) ---
    _pha("copy folder draft")
    print("\nDang copy folder draft (thumbnail, materials san co, subdraft...)...")
    # A5: dich la path NGUOI DUNG GO -> de vuot 260 ky tu nhat. Truoc day dung
    # out_dir.mkdir() tran, nen tool chet bang traceback SAU KHI da hoi xong het
    # (do that: path 305 ky tu -> FileNotFoundError WinError 3).
    Path(_lp(out_dir)).mkdir(parents=True, exist_ok=True)
    Path(_lp(out_dir / "materials")).mkdir(exist_ok=True)
    skipped_items = []   # (ten, loi) - item cua folder draft copy khong duoc (dua vao bao cao)
    ignore_fn = None
    if skip_media:
        ignore_fn = import_toi_uu().make_copy_ignore(skip_media)
    for item in draft_dir.iterdir():
        if item.name in CONTENT_NAMES or item.name == "draft_meta_info.json":
            continue
        dest = out_dir / item.name
        try:
            if item.is_dir():
                if item.name.lower() == "materials":
                    # 'materials' da duoc tao san o tren. PHAI merge (dirs_exist_ok) de KHONG
                    # danh mat materials/audio + materials/video cua draft goc: media tro path
                    # TUONG DOI (./materials/...) hoac PLACEHOLDER chi ton tai trong folder nay.
                    shutil.copytree(_lp(item), _lp(dest), dirs_exist_ok=True,
                                    ignore=ignore_fn)
                else:
                    # subdraft/ va cac folder khac: merge de chay lai khong bi bo qua
                    shutil.copytree(_lp(item), _lp(dest), dirs_exist_ok=True,
                                    ignore=ignore_fn)
            else:
                if os.path.normcase(os.path.abspath(str(item))) in skip_media:
                    continue          # se duoc thay bang ban toi uu -> khoi copy ban goc
                shutil.copy2(_lp(item), _lp(dest))
        except Exception as ex:
            skipped_items.append((item.name, str(ex)))
            print(f"  ! Bo qua {item.name}: {ex}")

    # --- Ghi 3 file JSON goc cua draft cha (chua viet lai path - pha sau lo) ---
    write_json_loose(out_dir / "draft_content.json", content, content_trail)
    write_json_loose(out_dir / "draft_info.json", content, content_trail)
    meta["draft_fold_path"] = str(out_dir)
    meta["draft_root_path"] = str(out_dir.parent)
    write_json_loose(out_dir / "draft_meta_info.json", meta, meta_trail)

    # --- MUC 4: TOI UU DUNG LUONG (truoc khi len ke hoach copy, de khong copy ban to) ---
    opt_stat, opt_clean, opt_prune = None, None, None
    # Phai khai bao o TAM NGOAI CUNG cua main(): cho dung no nam sau khi viet bao
    # cao, ma khoi gan lai nam trong `if opt_stat` (chi che do 4). Khai bao ben
    # trong khoi do se lam che do 1 nem NameError - dung lop loi #64 vua sua.
    bo_cache_sau = False
    cuu_ban_goc = []        # PHAI o tang ngoai: bao cao doc no ca o che do 1
    if opts:
        TU = import_toi_uu()
        print("\n=== TOI UU DUNG LUONG: cat gon + ha phan giai (dang ma lai H.264) ===")
        print("    (buoc nay lau nhat; project GOC KHONG bi thay doi)")
        t_opt = time.monotonic()
        try:
            opt_stat = TU.optimize_package(out_dir, draft_dir, resolved, guid,
                                           opts, ffmpeg, ffprobe)
        except OSError as ex:
            print("\n  ! KHONG QUET DUOC HET ban xuat khi toi uu:")
            print(f"    {ex}")
            print("    So cache ma-lai duoc GIU: chay lai se khong phai ma lai tu dau.")
            print("    Hay kiem tra ket noi (o mang rot phien?) roi chay lai.")
            return
        print(f"  Xong toi uu sau {_fmt_time(time.monotonic() - t_opt)}:"
              f" {opt_stat['ok']}/{opt_stat['jobs']} clip"
              f" (cat gon {opt_stat['trim']}, ha phan giai {opt_stat['scale']},"
              f" nen bitrate {opt_stat['recompress']},"
              f" dung lai {opt_stat['reused']}, khong loi nen giu goc {opt_stat['no_gain']})")
        print(f"  Giam duoc ~{opt_stat['saved']/1e9:.2f} GB"
              f" (phan ma lai chiem {opt_stat['added']/1e9:.2f} GB)")
        if opt_stat["fail"]:
            print(f"  ! {len(opt_stat['fail'])} clip ma lai THAT BAI"
                  f" -> giu nguyen ban goc cho cac clip do (xem bao cao)")
        cuu_ban_goc = cuu_ban_goc_bi_bo_qua(
            out_dir, draft_dir, skip_media, opt_stat)

    # --- Len ke hoach viet lai cho MOI file .json trong ban xuat ---
    print("\nDang len ke hoach viet lai duong dan (moi file JSON, moi tang subdraft)...")
    try:
        plans, copy_plan, unresolved, json_fail2 = plan_package(
            out_dir, draft_dir, resolved, guid, gather_only,
            opt_by_src=(opt_stat or {}).get("opt_by_src"))
    except OSError as ex:
        # Quet thieu ban xuat -> ke hoach viet lai thieu -> goi con duong dan tro
        # ra ngoai ma khong ai biet. Dung lai la dung: du lieu tren dia van con,
        # chay lai sau khi khoi phuc ket noi se dung lai duoc phan da ma.
        print("\n  ! KHONG QUET DUOC HET ban xuat khi lap ke hoach viet lai:")
        print(f"    {ex}")
        print("    Ban xuat dang do dang tren dia - KHONG dung duoc. Hay kiem tra")
        print("    ket noi (o mang rot phien?) roi CHAY LAI: phan da ma se duoc dung lai.")
        return
    n_rewrite = sum(len(m) for m in plans.values())
    print(f"  {len(plans)} file JSON co duong dan can sua | {n_rewrite} tham chieu")
    print(f"  {len(copy_plan)} file media can copy them vao cac thu muc materials/")

    # --- Copy media theo ke hoach (dedupe: file trung dung hard link cho do ton dia) ---
    copy_fail = []       # (dest, loi)
    n_link = 0
    plan_items = sorted(copy_plan.items())
    plan_bytes = 0
    for dest, src in plan_items:
        try:
            plan_bytes += os.path.getsize(_lp(src))
        except OSError:
            pass
    _pha("copy media")
    print("\nDang copy media...  (% tinh theo dung luong; ETA = uoc tinh thoi gian con lai)")
    first_dest = {}
    t0 = time.monotonic()
    done_bytes = 0.0
    last_draw = 0.0
    n_items = len(plan_items)
    for i, (dest, src) in enumerate(plan_items, 1):
        try:
            Path(_lp(Path(dest).parent)).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        skey = os.path.normcase(str(src))
        fd = first_dest.get(skey)
        if not fd:
            # File nam TRONG folder draft da duoc `copytree` chep sang goi tu truoc.
            # `first_dest` chi biet nhung ban do CHINH VONG NAY tao ra, nen ban cua
            # copytree khong bao gio duoc dung lai -> chep lan hai, ton gap doi.
            # Do tren DS3_007: mot file 9,45 GB nam o CA goc goi lan trong subdraft,
            # hai thuc the rieng biet (so_lien_ket=1 moi ban) -> lang phi 9,45 GB
            # tren mot goi 22 GB. Tim ban co san roi LIEN KET toi no.
            try:
                _rel = os.path.relpath(str(src), str(draft_dir))
            except ValueError:
                _rel = ".."
            if not _rel.startswith(".."):
                _ung = out_dir / _rel
                if (isfile_safe(_ung)
                        and os.path.normcase(str(_ung)) != os.path.normcase(str(dest))):
                    fd = str(_ung)
        ok = False
        if fd:
            try:
                os.link(_lp(fd), _lp(dest))     # cung o dia -> khong ton them dung luong
                ok = True
                n_link += 1
                # Ghi nho de lan sau khoi phai suy ra lai duong dan cua ban
                # copytree. Thieu dong nay thi moi file tu ban thu BA tro di deu
                # phai `isfile_safe` mot lan nua tren o MANG - mot vong SMB thua
                # cho moi file, va tren project co hang tram file dung chung thi
                # do la hang tram vong.
                first_dest.setdefault(skey, fd)
            except Exception:
                ok = False
        if not ok:
            try:
                shutil.copy2(_lp(src), _lp(dest))
                first_dest[skey] = dest
                ok = True
            except Exception as ex:
                copy_fail.append((dest, str(ex)))
                print("\n  ! Copy loi", src, "->", dest, "->", ex)
        try:
            done_bytes += os.path.getsize(_lp(src))
        except OSError:
            pass
        now = time.monotonic()
        if now - last_draw >= 0.5 or i == n_items:
            last_draw = now
            print("\r" + _progress_line(i, n_items, done_bytes, plan_bytes, t0) + "  ",
                  end="", flush=True)
    if n_items:
        print()
    if n_link:
        print(f"  ({n_link} file dung chung -> lien ket cung, khong ton them dung luong)")
    if copy_fail:
        print(f"  ! CANH BAO: {len(copy_fail)}/{n_items} media KHONG copy duoc"
              f" -> ban xuat CHUA du (xem _BAO_CAO_THIEU.txt).")

    # --- Ap dung viet lai: CHI viet lai khi file dich CO THAT (chong bug 'rewrite du copy fail') ---
    _pha("viet lai duong dan trong JSON")
    print("\nDang viet lai duong dan trong cac file JSON...")
    rewrite_fail, n_applied, n_files_written = [], 0, 0
    apply_cache = {}
    for jrel, mapping in sorted(plans.items()):
        jf = out_dir / jrel.replace("/", os.sep)
        base = draft_root_of(jf, out_dir, apply_cache)
        good = {}
        for oldp, forms in mapping.items():
            tail = forms[1][2:]                      # bo './'
            if isfile_safe(base / tail.replace("/", os.sep)):
                good[oldp] = forms
            else:
                rewrite_fail.append((jrel, oldp))
        if not good:
            continue
        try:
            obj, trail = read_json_loose(jf)
        except Exception as ex:
            rewrite_fail.append((jrel, f"(doc lai loi) {ex}"))
            continue
        def fn(k, v, _g=good):
            f = _g.get(v)
            return _pick_form(k, f) if f else None
        n = deep_rewrite_strings(obj, fn)
        if n:
            try:
                write_json_loose(jf, obj, trail)
                n_applied += n
                n_files_written += 1
            except Exception as ex:
                rewrite_fail.append((jrel, f"(ghi loi) {ex}"))
    print(f"  Da sua {n_applied} tham chieu trong {n_files_written} file JSON")

    # --- MUC 4c: bo file thua (chay SAU khi viet lai xong moi biet cai gi con dung) ---
    opt_bad = []
    opt_lech_san = []       # lech VON CO trong draft goc - chi ghi nhan, khong chan
    goc_thua = []
    # Moi bo kiem CHET deu phai ghi vao day. Danh sach nay khong rong = KHONG duoc
    # ket luan "DU", vi ta khong con bang chung nao ca (checklist bug.md: mac dinh CHUA XONG).
    verify_loi = []
    if opts and opts.get("cleanup"):
        TU = import_toi_uu()
        print("\nDang don so dang ky (bo muc tro toi footage khong dung)...")
        try:
            opt_prune = TU.prune_registry(out_dir)
        except Exception as ex:
            # `iter_json_files` gio nem khi quet thieu. Khong don duoc so dang ky
            # thi kho media o may con con muc chet -> phai vao verify_loi, khong
            # duoc de tool ket luan "DU".
            verify_loi.append(f"prune_registry: {type(ex).__name__}: {ex}")
            print(f"  ! Don so dang ky THAT BAI: {ex}")
        print("Dang bo file khong dung / mo coi / lich su...")
        try:
            opt_clean = TU.cleanup_unused(out_dir)
        except Exception as ex:
            verify_loi.append(f"cleanup_unused: {type(ex).__name__}: {ex}")
            print(f"  ! Don file thua THAT BAI: {ex}")
        # NGHIEM THU (bai hoc #38): con ban GOC nao bi giu song vo ich khong?
        # Bug #38 giu lai 10,46 GB va chi lo ra khi co nguoi thay goi phinh vo ly.
        try:
            goc_thua = TU.kiem_ban_goc_thua(out_dir)
        except Exception as ex:
            goc_thua = []
            verify_loi.append(f"kiem_ban_goc_thua: {type(ex).__name__}: {ex}")
            print(f"  ! Kiem ban goc thua THAT BAI: {ex}")
        print("\nDang tu kiem rieng phan toi uu (doan dung co lech khong)...")
        opt_verify_ok = False
        try:
            # Truyen `draft_dir` de phan biet lech DO TA GAY RA voi lech VON CO
            # trong draft goc (bug #104). Cung cach lam nhu `verify_package`.
            opt_bad, opt_lech_san = TU.verify_optimize(out_dir, draft_dir)
            opt_verify_ok = True
        except Exception as ex:
            verify_loi.append(f"verify_optimize: {type(ex).__name__}: {ex}")
            print(f"  ! TU KIEM TOI UU THAT BAI (khong the ket luan OK): {ex}")
        if opt_lech_san:
            # Ghi nhan, KHONG canh bao to: khong phai loi cua lan gom nay.
            print(f"  (i) {len(opt_lech_san)} segment da lech san trong draft GOC"
                  f" - khong phai do goi, mang sang may khac khong te hon ban goc")
        if opt_bad:
            print(f"  ! {len(opt_bad)} segment BI LECH sau khi cat gon -> XEM BAO CAO")
        elif not opt_verify_ok:
            # Phep do THAT BAI khac han voi phep do cho ket qua tot (bai hoc #33).
            # Khong in "OK", va GIU LAI so cache de lan chay sau con duong phuc hoi.
            print(f"  ! GIU LAI so cache tam ({TU.OPT_INDEX_NAME}) vi chua tu kiem duoc.")
        else:
            print("  OK: moi doan dung deu nam trong pham vi clip.")
            # KHONG bo so cache o day. Truoc day bo ngay tai cho nay, nhung giua
            # day va luc viet xong bao cao con ca buoc tu kiem + ghi bao cao. Bug
            # #64 nem UnboundLocalError dung o khoang do: cache DA bi xoa trong
            # khi bao cao CHUA duoc ghi -> lan chay lai phai ma lai tu dau, mat
            # trang 14,8 phut da ma xong. Bo cache la viec cua "da thuc su xong",
            # ma "xong" chi duoc tuyen bo sau khi bao cao nam tren dia.
            bo_cache_sau = True

    # --- TU KIEM tren ban xuat (quet de quy) ---
    _pha("tu kiem ban xuat")
    # verify_loi: bo kiem CHET thi KHONG duoc coi la "khong co loi". Mac dinh phai la
    # CHUA XONG cho toi khi chung minh duoc la xong (checklist bug.md). Truoc day chi
    # gan bad = [] roi di tiep -> tool in "Ban tu chua DU" du chua he tu kiem lan nao.
    try:
        bad = verify_package(out_dir, draft_dir)
    except Exception as ex:
        bad = []
        verify_loi.append(f"verify_package: {type(ex).__name__}: {ex}")
        print(f"  ! TU KIEM THAT BAI (khong the ket luan DU): {ex}")
    bad_hard = [b for b in bad if not b[3]]
    bad_soft = [b for b in bad if b[3]]

    unresolved_hard = {p: f for p, f in unresolved.items()
                       if not all(is_cosmetic(k, p) for k in refs.get(p, {}).get("keys", {""}))}

    try:
        long_paths = scan_long_paths(out_dir)
    except Exception as ex:
        long_paths = []
        verify_loi.append(f"scan_long_paths: {type(ex).__name__}: {ex}")
        print(f"  ! Quet duong dan dai THAT BAI: {ex}")

    # Phien ban ffmpeg cho dau bao cao. CHI import toi_uu khi che do 4 that su co ffmpeg
    # -> che do NGUYEN BAN khong phu thuoc toi_uu_dung_luong.py (chep thieu file van chay).
    if ffmpeg:
        try:
            ff_ver = import_toi_uu().ff_version(ffmpeg)
        except Exception as ex:
            ff_ver = f"khong lay duoc phien ban ({type(ex).__name__}: {ex})"
    else:
        ff_ver = "khong dung (che do NGUYEN BAN)"

    with open(_lp(out_dir / "_BAO_CAO_THIEU.txt"), "w", encoding="utf-8") as f:

        # PHAI dinh nghia TRUOC moi cho dung. Truoc day `sect` nam o giua than
        # `with`, sau mot cho da goi no (khoi `if opt_clean:`) -> Python coi `sect`
        # la bien CUC BO cua main() nen lan goi som hon nem UnboundLocalError.
        # Loi do chi no o che do 4 VA khi co file bi don, tuc dung luc da lam xong
        # het viec: goi nam day du tren dia nhung KHONG co bao cao va KHONG co ket
        # luan. Xem bug.md.
        def sect(title, rows, limit=80):
            if not rows:
                return
            f.write(title + "\n")
            for r in rows[:limit]:
                f.write("  " + r + "\n")
            if len(rows) > limit:
                f.write(f"  ... +{len(rows)-limit} nua\n")
            f.write("\n")

        # Dau bao cao PHAI co so hieu phien ban + moi truong: khi nguoi dung o may khac
        # gui file nay ve, day la thu duy nhat cho biet ho chay ban nao, tren gi.
        _py, _he = mo_ta_moi_truong()
        f.write(f"Tool: goi_project_capcut {TOOL_VERSION}"
                f" | Python {_py} | {_he}\n")
        f.write(f"ffmpeg: {ff_ver}\n")
        f.write(f"Chay luc: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-" * 60 + "\n")
        f.write(f"Project: {draft_dir}\n")
        f.write(f"DU AN CON (nhap tu project khac): {len(sub_imported)}"
                f" | clip ghep: {len(sub_compound)}\n")
        for p, depth in sub_imported:
            nm, src = subproject_origin(p)
            f.write(f"  {'  ' * (depth - 1)}- {nm}   (nhap tu: {src})\n")
        f.write(f"Da quet {n_json} file .json (gom ca du an con/subdraft long nhieu tang)\n")
        f.write(f"Tham chieu media tuyet doi: {len(refs)} | phai gom: {len(need_copy)}\n")
        f.write(f"Copy them: {len(copy_plan)} file (trong do {n_link} lien ket cung)\n")
        f.write(f"Da viet lai: {n_applied} tham chieu trong {n_files_written} file JSON\n")
        f.write(f"THIEU (khong tim thay o bat ky o nao): {len(misses_hard)}"
                f" (+{len(misses_soft)} anh bia)\n")
        f.write(f"COPY THAT BAI: {len(copy_fail)}\n")
        f.write(f"Folder draft copy thieu: {len(skipped_items)}\n")
        f.write(f"Tu kiem: {len(bad_hard)} tham chieu HONG (+{len(bad_soft)} anh bia)\n")
        f.write(f"File co duong dan > 260 ky tu: {len(long_paths)}\n")
        if opt_stat:
            f.write("\n--- TOI UU DUNG LUONG (muc 4) ---\n")
            f.write(f"Clip xu ly: {opt_stat['ok']}/{opt_stat['jobs']}"
                    f" | cat gon: {opt_stat['trim']} | ha phan giai: {opt_stat['scale']}"
                    f" | dung lai ban da ma: {opt_stat['reused']}\n")
            f.write(f"Giam duoc: ~{opt_stat['saved']/1e9:.2f} GB"
                    f" | phan ma lai chiem: {opt_stat['added']/1e9:.2f} GB\n")
            f.write(f"Ma lai THAT BAI (giu nguyen ban goc): {len(opt_stat['fail'])}\n")
            if opt_prune:
                f.write(f"So dang ky: bo {opt_prune[0]} muc tro toi footage KHONG dung"
                        f", giu {opt_prune[1]} muc\n")
            if opt_clean:
                f.write(f"Da bo file thua: {opt_clean[0]} file"
                        f" (~{opt_clean[1]/1e9:.2f} GB)\n")
                # A4: truoc day hai danh sach nay bi vut di hoan toan - file xoa
                # khong duoc va file JSON hong khong bao gio den mat nguoi dung.
                sect("DON DEP - file KHONG xoa duoc:",
                     [f"{a}  <-- {b}" for a, b in (opt_clean[2] or [])])
                if len(opt_clean) > 3 and opt_clean[3]:
                    sect("DON DEP - file JSON KHONG doc duoc"
                         " (da BO QUA viec xoa file mo coi cho an toan):",
                         [f"{a}  <-- {b}" for a, b in opt_clean[3]])
            f.write(f"Segment BI LECH sau khi cat: {len(opt_bad)}\n")
            if opt_lech_san:
                f.write(f"Segment da lech SAN trong draft goc"
                        f" (khong phai do goi): {len(opt_lech_san)}\n")
        f.write("\n")

        sect("THIEU - khong gom duoc (bo sung roi chay lai):",
             [f"{p}   <- khai bao boi: {', '.join(sorted(refs.get(p, {}).get('files', []))[:3])}"
              for p in misses_hard])
        sect("COPY THAT BAI - khong ghi duoc vao ban xuat:",
             [f"{d}  <-- {ex}" for d, ex in copy_fail])
        sect("FOLDER DRAFT COPY THIEU:",
             [f"{nm}  <-- {ex}" for nm, ex in skipped_items])
        sect("KHONG TIM THAY NGUON khi viet lai (giu nguyen path cu):",
             [f"{p}   <- {', '.join(sorted(fs)[:3])}" for p, fs in unresolved_hard.items()])
        sect("KHONG VIET LAI DUOC (file dich khong co that):",
             [f"{a}  <-- {b}" for a, b in rewrite_fail])
        _jf_all = json_fail + json_fail2
        _jf_hard = json_fail_hard(_jf_all)
        _jf_cache = [x for x in _jf_all if x not in _jf_hard]
        sect("FILE .json DOC LOI (timeline/so dang ky - CO anh huong):",
             sorted({f"{a}  <-- {b}" for a, b in _jf_hard}))
        sect("FILE .json cache doc loi (KHONG anh huong video xuat ra):",
             sorted({f"{a}  <-- {b}" for a, b in _jf_cache}))
        sect("TU KIEM - tham chieu HONG (anh huong video xuat ra):",
             [f"[{r}] {p}   trong {j}" for j, p, r, _ in bad_hard])
        sect("TU KIEM - anh bia/thumbnail hong (KHONG anh huong video):",
             [f"[{r}] {p}   trong {j}" for j, p, r, _ in bad_soft])
        if long_paths:
            _rut, _khong, _toi_da = phan_loai_path_dai(long_paths, out_dir)
            sect(f"DUONG DAN QUA DAI (>260 ky tu) - CapCut/Explorer co the khong mo"
                 f" duoc. Cach xu ly: dat folder XUAT RA o duong dan toi da"
                 f" {_toi_da} ky tu:",
                 [f"({len(p)} ky tu) {p}" for p, _n in _rut], limit=20)
            # Loai nay rut ngan dich KHONG cuu duoc - phai noi that, dung khuyen
            # nguoi dung lam mot viec vo ich (do tren DS3_006: ten file 205 ky tu
            # do CapCut tai tu CMS, rieng phan tuong doi da 280 ky tu).
            sect("DUONG DAN QUA DAI ma RUT NGAN THU MUC DICH KHONG CUU DUOC"
                 " (rieng phan ben trong goi da vuot 260 ky tu - do TEN FILE goc"
                 " qua dai, khong phai do thu muc ban chon):",
                 [f"(tong {len(p)} ky tu | rieng phan trong goi {n}) {p}"
                  for p, n in _khong], limit=20)

        sect("TOI UU - SEGMENT BI LECH (hinh se sai, PHAI xu ly):",
             [f"{j} | material {m} | {r}" for j, m, r in opt_bad])
        sect("TOI UU - segment DA LECH SAN trong draft goc"
             " (KHONG phai do goi, chi de biet):",
             [f"{j} | material {m} | {r}" for j, m, r in opt_lech_san])
        sect("TOI UU - clip ma lai that bai (da giu nguyen ban goc, khong mat hinh):",
             [f"{a}  <-- {b}" for a, b in (opt_stat["fail"] if opt_stat else [])])

        # Clip bi LOAI khoi viec ma lai (dai qua muc, khong tim thay nguon...).
        # Truoc day moi cho nay deu `continue` tran nen nguoi dung khong bao gio
        # hieu vi sao clip dai nhat cua ho khong duoc nen.
        if goc_thua:
            _tong = sum(x[1] for x in goc_thua) / 1e9
            f.write(f"\nBAN GOC CON TRONG GOI ma KHONG file noi dung nao dung"
                    f" (~{_tong:.2f} GB) - co the bo di:\n")
            for _p, _sz in goc_thua[:30]:
                f.write(f"  ({_sz / 1e6:.0f} MB) {_p}\n")
            if len(goc_thua) > 30:
                f.write(f"  ... va {len(goc_thua) - 30} file nua\n")

        sect("TOI UU - clip KHONG dua vao ma lai (giu nguyen ban goc):",
             [f"{a}  <-- {b}"
              for a, b in ((opt_stat or {}).get("bo_qua") or [])])

        sect("DA CUU ban goc bi bo qua nham (du doan se duoc thay nhung khong duoc thay):",
             cuu_ban_goc)

        sect("BO TU KIEM THAT BAI (KHONG the ket luan gi ve ban xuat):", verify_loi)

        if not (misses_hard or copy_fail or skipped_items or bad_hard
                or unresolved_hard or rewrite_fail or _jf_hard
                or opt_bad or verify_loi):
            f.write("Khong thieu. Ban tu chua DU"
                    " (da tu kiem DE QUY moi file JSON, ke ca du an con).\n")
        elif verify_loi:
            f.write("CHUA KET LUAN DUOC: bo tu kiem bi loi nen KHONG co bang chung"
                    " rang ban xuat da du. Hay xem muc 'BO TU KIEM THAT BAI' o tren"
                    " va chay lai.\n")

    # verify_loi PHAI nam trong dieu kien nay: bo kiem chet thi khong con bang chung
    # nao de tuyen bo "DU". Mac dinh la CHUA XONG (checklist bug.md).
    if _gac:
        _gac.dung()
    ok = not (misses_hard or copy_fail or skipped_items or bad_hard
              or unresolved_hard or rewrite_fail or _jf_hard
              or opt_bad or verify_loi)

    # BAY GIO moi duoc bo so cache ma-lai: bao cao da nam tren dia va da co ket
    # luan. Bo som hon (nhu truoc bug #64) nghia la neu buoc viet bao cao chet
    # thi vua mat bao cao vua mat ca duong phuc hoi -> lan chay lai ma lai tu dau.
    # Con loi thi GIU cache: lan chay sau con dung lai duoc phan da ma.
    if bo_cache_sau and ok:
        try:
            _idx = out_dir / import_toi_uu().OPT_INDEX_NAME
            if isfile_safe(_idx):
                os.remove(_lp(_idx))
                print(f"  Da bo so cache tam ({import_toi_uu().OPT_INDEX_NAME}).")
        except OSError as ex:
            print(f"  ! Khong bo duoc so cache tam: {ex}")
    elif bo_cache_sau:
        print("  GIU LAI so cache tam: con loi -> lan chay sau khoi ma lai tu dau.")

    print("\n" + "=" * 64)
    print(f"XONG. Ban tu chua: {out_dir}")
    print(f"  Copy them: {len(copy_plan)} file | viet lai: {n_applied} tham chieu"
          f" | THIEU: {len(misses_hard)} | COPY THAT BAI: {len(copy_fail)}")
    if verify_loi:
        print(f"  ! NANG: {len(verify_loi)} bo tu kiem THAT BAI -> KHONG the ket luan"
              " ban xuat da du. Xem _BAO_CAO_THIEU.txt roi chay lai.")
    if copy_fail:
        print(f"  ! CANH BAO: {len(copy_fail)} media KHONG copy duoc -> CHUA du")
    if skipped_items:
        print(f"  ! CANH BAO: {len(skipped_items)} item folder draft bi bo qua")
    if unresolved_hard:
        print(f"  ! CANH BAO: {len(unresolved_hard)} tham chieu khong tim thay nguon")
    if rewrite_fail:
        print(f"  ! CANH BAO: {len(rewrite_fail)} tham chieu khong viet lai duoc")
    if bad_hard:
        print(f"  ! CANH BAO: {len(bad_hard)} tham chieu HONG sau khi gom")
    if opt_stat:
        print(f"  Toi uu: giam ~{opt_stat['saved']/1e9:.2f} GB"
              f" ({opt_stat['ok']} clip xu ly, {len(opt_stat['fail'])} that bai)"
              + (f", bo {opt_clean[0]} file thua" if opt_clean else ""))
    if opt_bad:
        print(f"  ! CANH BAO: {len(opt_bad)} segment BI LECH sau khi cat gon")
    if goc_thua:
        print(f"  (i) {len(goc_thua)} ban goc (~{sum(x[1] for x in goc_thua)/1e9:.2f} GB)"
              f" con trong goi ma khong file noi dung nao dung - xem bao cao")
    if bad_soft:
        print(f"  (i) {len(bad_soft)} anh bia/thumbnail hong - khong anh huong video xuat ra")
    if long_paths:
        _rut, _khong, _toi_da = phan_loai_path_dai(long_paths, out_dir)
        print(f"  ! {len(long_paths)} file co duong dan > 260 ky tu"
              f" - CapCut co the khong mo duoc.")
        if _rut:
            print(f"      {len(_rut)} file: dat folder XUAT RA o duong dan toi da"
                  f" {_toi_da} ky tu la het (vd D:\\GOI\\{draft_dir.name}).")
        if _khong:
            # KHONG duoc khuyen "rut ngan dich" cho nhom nay: rieng phan ben trong
            # goi da vuot 260 nen dat o `D:\` cung khong cuu duoc. Noi that de
            # nguoi dung khong mat cong lam mot viec vo ich.
            print(f"      {len(_khong)} file: rut ngan thu muc dich KHONG cuu duoc"
                  f" - TEN FILE do CapCut sinh qua dai. Xem bao cao.")
    if ok:
        print("  => KHONG THIEU. Ban tu chua DU.")
    else:
        print("  => CON THIEU. XEM _BAO_CAO_THIEU.txt, bo sung roi chay lai.")
    print("  PHEP THU VANG: COPY folder nay SANG MAY KHAC roi mo bang CapCut.")
    print("  (mo tren chinh may nay KHONG chung minh duoc gi: path cu van con tren o dia)")
    print("=" * 64)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDa dung.")
    except Exception:
        import traceback; traceback.print_exc()
        # KHONG duoc de chinh trinh xu ly loi chet: `input()` nem EOFError khi
        # stdin da dong (bo lap lich / duong ong / chuyen huong), luc do nguoi
        # dung thay HAI traceback chong nhau va loi THAT bi che mat.
        try:
            input("Enter de dong...")
        except (EOFError, KeyboardInterrupt):
            pass
