#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MUC 4 - TOI UU DUNG LUONG cho ban goi CapCut.

Gom 3 viec:
  a) CAT GON footage dai  : chi giu doan THUC SU dung tren timeline (+ dem an toan),
                            roi doi source_timerange cua moi segment cho khop.
  b) HA 4K / NEN BITRATE  : ha phan giai xuong dung nhu KHUNG HINH can (canvas x scale
                            lon nhat ma clip do duoc phong to), ma lai H.264 CRF.
  c) BO FILE THUA         : file media khong con JSON nao tham chieu + file lich su
                            (*.bak, *.tmp).

NGUYEN TAC AN TOAN (rut ra tu bug.md):
  - Chi doi source_timerange khi ffmpeg BAO THANH CONG va file dich CO THAT.
  - ffmpeg loi -> quay ve copy nguyen ban, KHONG doi gi trong JSON, va DEM vao bao cao.
  - Sau khi lam xong phai TU KIEM: moi segment phai nam trong [0, duration cua material].
  - Chi xoa file trong cac thu muc 'materials/' (va *.bak/*.tmp) - khong dung toi
    file la cua CapCut.
"""

from __future__ import annotations
import json, os, shutil, subprocess, sys, tempfile, threading, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


# E1: truoc day phai di TIM NGUOC module chinh (vong tron phu thuoc + hack tra
# sys.modules, xem #48). Gio moi thu dung chung nam o tang tien ich rieng, nen
# chi can mot dong import binh thuong. Giu ten `G` de khong phai sua 80+ cho goi.
import chung as G

US = 1_000_000                 # 1 giay = 1e6 microgiay (don vi cua CapCut)
PAD_US = 500_000               # dem 0.5s moi dau khi cat
TRIM_MIN_FRAC = 0.85           # chi cat khi doan dung < 85% do dai file
TRIM_MIN_SAVE = 8 * 1024 ** 2  # va tiet kiem it nhat 8 MB
SCALE_MARGIN = 1.10            # chua he so an toan cho do net
SCALE_MIN_GAIN = 1.15          # chi ha phan giai khi rong hon nhu cau >15%
MAX_SPAN_US = 30 * 60 * US     # doan dai hon 30 phut -> khong ma lai (qua ton thoi gian)
MAX_DUR_DIFF_S = 0.6           # (bug #35) ket qua lech qua nguong nay = BI CUT -> that bai
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}


def _cac_goc_ffmpeg(base_dir=None):
    """Cac thu muc co the chua ffmpeg di kem, theo THU TU UU TIEN.

    E2: khi dong goi bang PyInstaller, `__file__` tro vao thu muc GIAI NEN TAM
    (`sys._MEIPASS`) chu khong phai thu muc chua file .exe. Neu chi dua vao
    `__file__` thi ban ffmpeg di kem KHONG duoc tim thay, tool lang le quay sang
    `shutil.which()` va dung mot ffmpeg KHAC trong PATH - phien ban khac, tham so
    khac, khong mot canh bao nao. Do la kieu sai am tham te nhat.
    """
    goc = []
    if base_dir:
        goc.append(Path(base_dir))
    # Thu muc chua file .exe khi da dong goi (sys.frozen do PyInstaller dat)
    if getattr(sys, "frozen", False):
        goc.append(Path(sys.executable).resolve().parent)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            goc.append(Path(meipass))
    goc.append(Path(__file__).resolve().parent)
    # Bo trung, giu thu tu
    ra, da = [], set()
    for g in goc:
        k = os.path.normcase(str(g))
        if k not in da:
            da.add(k)
            ra.append(g)
    return ra


def ff_paths(base_dir=None):
    """Tim ffmpeg/ffprobe di kem tool; None neu khong co.

    Tra (ffmpeg, ffprobe). Uu tien ban DI KEM tool, sau do moi den PATH he thong.
    """
    for root in _cac_goc_ffmpeg(base_dir):
        ff = root / "ffmpeg" / "bin" / "ffmpeg.exe"
        fp = root / "ffmpeg" / "bin" / "ffprobe.exe"
        # Qua isfile_safe (co _lp): tool co the duoc dat sau duong dan dai
        if G.isfile_safe(ff) and G.isfile_safe(fp):
            return str(ff), str(fp)
    ff2, fp2 = shutil.which("ffmpeg"), shutil.which("ffprobe")
    return (ff2, fp2) if (ff2 and fp2) else (None, None)


def _run(cmd, timeout):
    """Chay ffmpeg/ffprobe va doc dau ra bang UTF-8.

    PHAI co `encoding="utf-8"`. `text=True` khong kem `encoding=` se giai ma dau
    ra bang BANG MA ANSI CUA MAY (`locale.getpreferredencoding()`), ma ffmpeg tren
    Windows luon xuat UTF-8.
      - May phat trien co ACP 65001 (UTF-8) -> trung nhau -> KHONG BAO GIO thay loi.
      - May con Windows tieng Viet mac dinh ACP 1258 (hoac 1252) -> giai ma SAI:
        hoac nem UnicodeDecodeError, hoac tra ve chuoi rac lam json.loads that bai.
    Hau qua o `_probe_that`: tra None -> tool tuong "khong do duoc video" -> bo clip.
    `chcp 65001` trong file .bat KHONG sua duoc, vi no doi console code page chu
    khong doi ANSI code page cua tien trinh.
    `errors="replace"` de mot vai byte la khong lam chet ca lan chay.
    """
    return subprocess.run(cmd, capture_output=True, timeout=timeout,
                          encoding="utf-8", errors="replace",
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def kiem_ffmpeg_chay_duoc(ffmpeg, ffprobe, timeout=30):
    """Thu ffmpeg/ffprobe NGAY LUC KHOI DONG. Tra (ok, ly_do).

    `ff_paths()` chi kiem FILE CO TON TAI. Tren may con, `ffmpeg.exe` co the nam
    day du do ma van khong chay duoc:
      - thieu DLL (ban build khac, hoac chep thieu thu muc bin/)
      - ban LGPL toi gian KHONG co encoder `libx264` -> ma lai clip nao cung hong
      - bi Windows Defender / chinh sach may chan
    Neu khong kiem o day, nguoi dung cho 15-30 phut roi nhan ve hang tram loi va
    tuong footage cua minh hong. Ba loi goi nay ton chua toi mot giay.
    """
    if not ffmpeg or not ffprobe:
        return False, "khong tim thay ffmpeg/ffprobe"
    for ten, duong in (("ffmpeg", ffmpeg), ("ffprobe", ffprobe)):
        try:
            r = _run([duong, "-hide_banner", "-version"], timeout)
        except Exception as ex:
            return False, (f"{ten} KHONG chay duoc ({type(ex).__name__}: {ex})."
                           f" Thuong la thieu DLL hoac bi chan boi phan mem bao ve.")
        if r.returncode != 0:
            return False, (f"{ten} tra ma loi {r.returncode}."
                           f" {(r.stderr or '').strip()[:160]}")
    # Co encoder H.264 khong? Ban LGPL toi gian khong co libx264.
    try:
        r = _run([ffmpeg, "-hide_banner", "-encoders"], timeout)
        ds = (r.stdout or "") + (r.stderr or "")
    except Exception as ex:
        return False, f"khong liet ke duoc encoder cua ffmpeg ({ex})"
    if "libx264" not in ds:
        return False, ("ban ffmpeg nay KHONG co encoder `libx264` (H.264)."
                       " Che do 4 can no de ma lai. Hay dung ban ffmpeg day du"
                       " (vd gyan.dev 'essentials' hoac 'full').")
    return True, ""


def ff_version(ffmpeg, timeout=15):
    """Dong dau cua 'ffmpeg -version', vd 'ffmpeg version 8.1.2 ...'.

    Dung cho DAU BAO CAO: khi nguoi dung o may khac gui bao cao ve, phai biet ho
    chay ffmpeg nao (ban di kem tool hay ban trong PATH - hai ban co the khac nhau).
    Tra chuoi mo ta loi thay vi None de bao cao LUON noi ro tai sao khong lay duoc,
    khong de trong (checklist bug.md: khong nuot loi am tham).
    """
    if not ffmpeg:
        return "khong dung (che do NGUYEN BAN hoac khong tim thay ffmpeg)"
    try:
        r = _run([ffmpeg, "-hide_banner", "-version"], timeout)
    except Exception as ex:
        return f"khong lay duoc phien ban ({type(ex).__name__}: {ex})"
    if r.returncode != 0:
        return f"khong lay duoc phien ban (ffmpeg tra ma {r.returncode})"
    dong = (r.stdout or "").splitlines()
    return dong[0].strip() if dong and dong[0].strip() else "khong doc duoc dong phien ban"


# Bo nho dem cho probe(). Moi lan goi la MOT TIEN TRINH CON cong mot luot doc
# file - tren o mang la mot vong SMB. Vong ap dung JSON goi probe cho MOI job,
# ma job `dup` (sinh ra vi main() luon ghi ca draft_content.json lan
# draft_info.json) tro vao DUNG file dich do -> probe lai y het. Khoa gom ca
# kich thuoc + thoi diem sua de neu file bi ghi de thi khong dung ket qua cu.
_PROBE_CACHE = {}


def _khoa_probe(path):
    try:
        st = os.stat(G._lp(path))
        return (os.path.normcase(str(path)), st.st_size, int(st.st_mtime))
    except OSError:
        return None


def xoa_cache_probe():
    """Xoa bo nho dem probe. Goi khi bat dau mot pha co the ghi de file."""
    _PROBE_CACHE.clear()


def probe(ffprobe, path, timeout=120):
    """Tra (width, height, duration_us, co_audio) - None neu khong doc duoc."""
    khoa = _khoa_probe(path)
    if khoa is not None and khoa in _PROBE_CACHE:
        return _PROBE_CACHE[khoa]
    kq = _probe_that(ffprobe, path, timeout)
    if khoa is not None and kq is not None:
        _PROBE_CACHE[khoa] = kq
    return kq


def _probe_that(ffprobe, path, timeout=120):
    """Goi ffprobe THAT (khong qua bo nho dem)."""
    try:
        r = _run([ffprobe, "-v", "error", "-print_format", "json",
                  "-show_streams", "-show_format", G._lp(path)], timeout)
        if r.returncode != 0:
            # Cung phai de lai vet. `stderr` phan biet hai chuyen rat khac nhau:
            # "No such file" (file that su khong co) va loi codec/moi truong.
            _ghi_loi_probe(path, f"ffprobe tra ma {r.returncode}: "
                                 f"{(r.stderr or '').strip()[:200]}")
            return None
        # "" khong phai la JSON rong: `json.loads("{}")` cho ra video 0x0 dai 0
        # giay, tra ve mot phep do GIA thay vi noi "khong do duoc". Phan biet ro.
        if not (r.stdout or "").strip():
            _ghi_loi_probe(path, f"ffprobe khong tra ve gi (stderr: "
                                 f"{(r.stderr or '').strip()[:200]})")
            return None
        d = json.loads(r.stdout)
    except Exception as ex:
        # Truoc day nuot tron. Tren may con giai ma sai bang ma thi ffprobe van
        # chay dung nhung json.loads that bai -> im lang bo clip. Phai de lai vet.
        _ghi_loi_probe(path, f"{type(ex).__name__}: {ex}")
        return None
    w = h = 0
    has_a = False
    for s in d.get("streams", []):
        if s.get("codec_type") == "video" and not w:
            w, h = int(s.get("width") or 0), int(s.get("height") or 0)
        elif s.get("codec_type") == "audio":
            has_a = True
    try:
        dur = int(float((d.get("format") or {}).get("duration") or 0) * US)
    except Exception:
        dur = 0
    return (w, h, dur, has_a)


# Moi lan probe that bai deu duoc ghi lai. Danh sach nay di vao bao cao qua
# `st["fail"]`: mot clip khong do duoc la mot clip KHONG duoc toi uu, va neu xay
# ra HANG LOAT thi do la dau hieu moi truong hong (bang ma, ffmpeg la) chu khong
# phai footage cua nguoi dung hong. Truoc day khong co gi phan biet hai kha nang do.
_LOI_PROBE = []


def _ghi_loi_probe(path, mo_ta):
    _LOI_PROBE.append((str(path), mo_ta))


def lay_loi_probe():
    """Tra ban sao danh sach loi probe, roi don sach cho pha sau."""
    ra = list(_LOI_PROBE)
    _LOI_PROBE.clear()
    return ra


def _even(n):
    n = int(round(n))
    return n - (n % 2) if n > 2 else 2


# Bo nho dem cho isfile_safe: mot file duoc hoi di hoi lai hang chuc lan (moi material,
# moi lan goi resolve_material_file). Tren o MANG moi lan hoi la mot round-trip SMB
# -> pha 'tinh truoc' co the mat hang chuc phut va lam tang rui ro treo (bug #25, #28).
_EXIST_CACHE = {}


def _exists(p) -> bool:
    k = os.path.normcase(str(p))
    v = _EXIST_CACHE.get(k)
    if v is None:
        v = G.isfile_safe(p)
        _EXIST_CACHE[k] = v
    return v


def xoa_cache_ton_tai():
    """Xoa bo nho dem `_exists`. PHAI goi o dau MOI lan chay `main()`.

    Vi sao can (do that, 2026-09-10):
        _exists(f) -> False        (file chua tao)
        [tao file that]
        _exists(f) -> False        SAI - van tra ket qua cu
        _exists(g) -> True         (file co that)
        [xoa file]
        _exists(g) -> True         SAI - dinh ca chieu nguoc

    O che do dong lenh va giao dien MOT project, moi lan goi la mot TIEN TRINH
    moi nen cache chet theo tien trinh - khong ai thay van de. Nhung hang doi
    NHIEU project goi `main()` nhieu lan trong CUNG mot tien trinh: project sau
    thua huong cache cua project truoc -> bao THIEU FILE oan (file da co ma bao
    khong), hoac COPY THAT BAI (file da xoa ma bao con). Ca hai deu im lang.

    `_PROBE_CACHE` da co `xoa_cache_probe()`, `_LOI_PROBE` tu don trong
    `lay_loi_probe()`. Rieng cai nay bi sot.
    """
    _EXIST_CACHE.clear()


def resolve_material_file(path_str, base, draft_dir, out_dir, resolved):
    """Doi path trong JSON -> FILE NGUON that de doc (uu tien ban trong goi)."""
    if not path_str:
        return None
    if G.is_real_abs(path_str):
        np = G._np(path_str)
        # UU TIEN BAN GOC O MAY NAY. Neu lay ban trong goi thi khi dich la o MANG,
        # ffmpeg se phai doc file goc QUA MANG de ma lai - cuc cham (file 8K vai GB).
        if _exists(np):
            return Path(np)
        src = resolved.get(path_str)
        if src is not None and _exists(src):
            return Path(src)
        if G._is_under(np, draft_dir):
            sub = G._rel_posix(np, draft_dir)
            if sub:
                cand = out_dir / sub.replace("/", os.sep)
                if _exists(cand):
                    return cand
        return None
    if path_str.startswith("##"):
        i = path_str.find("_##")
        if i == -1:
            return None
        tail = path_str[i + 3:].lstrip("/\\")
    elif path_str.startswith("./") or path_str.startswith(".\\"):
        tail = path_str[2:].lstrip("/\\")
    else:
        return None
    tail = tail.replace("/", os.sep)
    # UU TIEN ban NAM TRONG DRAFT GOC tren may nay (goi co the o o mang -> doc rat cham),
    # va nhat la khi ta CO Y khong copy ban goc len dich nua thi trong goi se KHONG co file
    # nay -> bat buoc phai lui ve draft goc, neu khong se khong tim thay gi de ma lai.
    rel_base = G._rel_posix(base, out_dir)
    if rel_base is not None:
        cand_src = (Path(draft_dir) if rel_base == "."
                    else Path(draft_dir) / rel_base.replace("/", os.sep)) / tail
        if _exists(cand_src):
            return cand_src
    cand_pkg = Path(base) / tail
    return cand_pkg if _exists(cand_pkg) else None


def _uniq_name(matdir, stem, suffix, used):
    name, n = f"{stem}{suffix}", 1
    while name.lower() in used:
        name = f"{stem}_{n}{suffix}"
        n += 1
    used.add(name.lower())
    return name


def iter_draft_objs(content):
    """Yield draft goc VA moi blob du an con NHUNG INLINE trong materials.drafts[].draft.

    CapCut nhung NGUYEN NOI DUNG cua du an con vao day (co materials + tracks rieng).
    Neu chi doc materials/tracks o tang ngoai cung thi toan bo media cua du an con
    KHONG BAO GIO duoc cat gon -> phai copy nguyen ban (do duoc 50.86 GB tren 1 project)."""
    yield content
    for dm in (content.get("materials", {}).get("drafts") or []):
        if isinstance(dm, dict) and isinstance(dm.get("draft"), dict):
            yield from iter_draft_objs(dm["draft"])


def collect_jobs(content, jf, base, draft_dir, out_dir, resolved, opts, used_names,
                 key_names=None):
    """Duyet 1 file content -> (danh_sach_viec, danh_sach_bi_bo_qua).

    KHONG dong vao dia. `danh_sach_bi_bo_qua` la cac (nguon, ly_do) bi loai
    khoi viec ma lai - PHAI di vao bao cao, khong duoc bo qua im lang.

    key_names: bang dung chung {(draft_root, khoa): duong_dan_dich} de HAI material
    giong het nhau (cung nguon + cung diem cat + cung be rong) dung CHUNG 1 file dich.
    Neu khong co bang nay, moi material se sinh 1 file rieng -> tren o mang (SMB khong
    ho tro lien ket cung) se thanh ban sao that, phinh dung luong vo ich."""
    jobs = []
    # Cac material bi LOAI khoi danh sach viec, kem LY DO. Truoc day moi cho
    # nay deu `continue` tran -> nguoi dung khong bao gio biet vi sao mot clip
    # khong duoc nen (checklist bug.md: dem moi that bai va dua vao bao cao).
    bo_qua = []
    # Nguong co the chinh qua opts (mac dinh la hang so o dau file).
    # Cho phep chinh de: (a) test khong can fixture hang chuc MB,
    # (b) nguoi dung muon gom manh tay hon / nhe tay hon.
    min_frac = float(opts.get("trim_min_frac", TRIM_MIN_FRAC))
    min_save = float(opts.get("trim_min_save", TRIM_MIN_SAVE))
    scale_gain = float(opts.get("scale_min_gain", SCALE_MIN_GAIN))

    matdir = base / "materials"
    root_canvas = content.get("canvas_config") or {}
    for _d in iter_draft_objs(content):
        canvas_w = int((_d.get("canvas_config") or root_canvas).get("width") or 0)
        segs_of = defaultdict(list)
        scale_of = defaultdict(float)
        for tr in (_d.get("tracks") or []):
            for sg in (tr.get("segments") or []):
                mid = sg.get("material_id")
                if not mid:
                    continue
                segs_of[mid].append(sg)
                sc = ((sg.get("clip") or {}).get("scale") or {}).get("x") or 1.0
                try:
                    scale_of[mid] = max(scale_of[mid], abs(float(sc)))
                except (TypeError, ValueError):
                    scale_of[mid] = max(scale_of[mid], 1.0)
        for m in (_d.get("materials", {}).get("videos") or []):
            if not isinstance(m, dict) or not m.get("path"):
                continue
            p = m["path"]
            if Path(p.replace("\\", "/")).suffix.lower() not in VIDEO_EXT:
                continue
            src = resolve_material_file(p, base, draft_dir, out_dir, resolved)
            if src is None:
                # Khong tim thay nguon -> khong the ma lai. Truoc day bo qua HOAN
                # TOAN im lang; nguoi dung khong hieu vi sao clip do khong duoc nen.
                bo_qua.append((str(p), "khong tim thay file nguon"))
                continue
            try:
                size = os.path.getsize(G._lp(src))
            except OSError as ex:
                bo_qua.append((str(src), f"khong doc duoc kich thuoc: {ex}"))
                continue
            dur = int(m.get("duration") or 0)
            segs = segs_of.get(m.get("id")) or []
            spans = [(int(s["source_timerange"]["start"]),
                      int(s["source_timerange"]["start"]) + int(s["source_timerange"]["duration"]))
                     for s in segs
                     if isinstance(s.get("source_timerange"), dict)
                     and "start" in s["source_timerange"]
                     and "duration" in s["source_timerange"]]

            lo, hi = 0, dur
            if opts.get("trim") and spans and dur > 0:
                lo = max(0, min(s for s, _ in spans) - PAD_US)
                hi = min(dur, max(e for _, e in spans) + PAD_US)
                if hi <= lo:
                    lo, hi = 0, dur
            span = hi - lo
            do_trim = bool(opts.get("trim") and dur > 0 and span < dur * min_frac
                           and size * (1 - span / dur) > min_save)
            if not do_trim:
                lo, span = 0, dur

            src_w = int(m.get("width") or 0)
            need_w = 0
            do_scale = False
            if opts.get("scale") and canvas_w and src_w:
                need_w = _even(canvas_w * max(scale_of.get(m.get("id"), 1.0), 1.0) * SCALE_MARGIN)
                do_scale = src_w > need_w * scale_gain

            # NEN BITRATE: ma lai H.264 KE CA khi khong can cat, khong can ha phan giai.
            # Footage mua (Artlist/Storyblocks...) thuong 11-50 Mbps; ma lai CRF ~21
            # con ~3-5 Mbps ma o khung 1080p mat thuong khong phan biet duoc.
            # Neu ma xong ma KHONG nho hon -> bo ket qua, giu ban goc (kiem o
            # optimize_package) => khong bao gio lam file to ra.
            do_recompress = bool(opts.get("recompress") and segs and dur > 0)

            if not (do_trim or do_scale or do_recompress):
                continue
            if span <= 0 or span > MAX_SPAN_US:
                # `st["skipped_big"]` von duoc khai bao nhung KHONG BAO GIO tang.
                # Clip dai hon 30 phut bi loai khoi danh sach viec ma khong dem,
                # khong in, khong vao bao cao -> nguoi dung khong bao gio hieu tai
                # sao clip dai nhat cua ho khong duoc nen.
                bo_qua.append((str(src),
                               f"doan dai {span / US / 60:.1f} phut, vuot muc"
                               f" {MAX_SPAN_US / US / 60:.0f} phut -> khong ma lai"))
                continue

            key = (os.path.normcase(str(src)), lo, span, need_w if do_scale else 0)
            kk = (os.path.normcase(str(base)), key)
            dup = False
            if key_names is not None and kk in key_names:
                dest = key_names[kk]          # dung chung file dich - khong ma lai lan 2
                dup = True
            else:
                stem = Path(str(src)).stem
                dest = matdir / _uniq_name(matdir, stem + "_opt", ".mp4", used_names)
                if key_names is not None:
                    key_names[kk] = dest
            jobs.append({
                "jf": jf, "m": m, "segs": segs, "src": Path(src), "dest": dest,
                "lo": lo, "span": span, "target_w": need_w if do_scale else 0,
                "old_dur": dur, "size": size, "trim": do_trim, "scale": do_scale,
                "key": key, "dup": dup, "recompress": do_recompress,
            })

        # --- BAN RENDER NGUOC (`reverse_path`) ---
        # CapCut sinh file nay khi ap hieu ung TUA NGUOC. No duoc tro toi qua khoa
        # `reverse_path`, KHONG BAO GIO qua `path`, nen vong lap tren khong nhin
        # thay -> khong job nao duoc sinh ra -> gom nguyen ban, khong nen.
        # Do that: DS3_007 co mot ban render nguoc 9,45 GB; quet 21 project tren
        # may thay 34 file / 147 GB deu roi vao dien nay.
        # Khong cat gon va khong ha phan giai (ta khong biet doan nao duoc dung
        # tren ban nguoc), chi NEN BITRATE - dung co che an toan san co: ma xong
        # ma khong nho hon dang ke thi bo ket qua, giu ban goc.
        if opts.get("recompress"):
            for m in (_d.get("materials", {}).get("videos") or []):
                if not isinstance(m, dict):
                    continue
                rp = m.get("reverse_path")
                if not rp or not isinstance(rp, str):
                    continue
                if Path(rp.replace("\\", "/")).suffix.lower() not in VIDEO_EXT:
                    continue
                src_r = resolve_material_file(rp, base, draft_dir, out_dir, resolved)
                if src_r is None:
                    bo_qua.append((str(rp), "ban render nguoc: khong tim thay file nguon"))
                    continue
                try:
                    size_r = os.path.getsize(G._lp(src_r))
                except OSError as ex:
                    bo_qua.append((str(src_r), f"ban render nguoc: khong doc duoc kich thuoc: {ex}"))
                    continue
                key_r = (os.path.normcase(str(src_r)), 0, 0, 0)
                kk_r = (os.path.normcase(str(base)), key_r)
                dup_r = False
                if key_names is not None and kk_r in key_names:
                    dest_r = key_names[kk_r]
                    dup_r = True
                else:
                    stem_r = Path(str(src_r)).stem
                    dest_r = matdir / _uniq_name(matdir, stem_r + "_opt", ".mp4", used_names)
                    if key_names is not None:
                        key_names[kk_r] = dest_r
                jobs.append({
                    "jf": jf, "m": m, "segs": [], "src": Path(src_r), "dest": dest_r,
                    "lo": 0, "span": 0, "target_w": 0,
                    "old_dur": 0, "size": size_r, "trim": False, "scale": False,
                    "key": key_r, "dup": dup_r, "recompress": True,
                    # Danh dau de buoc ap dung ghi vao `reverse_path`, KHONG phai `path`
                    "khoa_ghi": "reverse_path",
                })
    return jobs, bo_qua


def plan_replacements(draft_dir, opts, log=print):
    """Tra (tap_file_se_bi_thay, tong_byte) - cac FILE NGUON nam TRONG draft chac chan
    se duoc thay bang ban toi uu.

    Muc dich: KHONG copy ban goc len dich nua. Neu khong lam buoc nay, tool se day
    ca chuc GB len o mang roi mã lai roi... xoa di - vua lau vua ton bang thong."""
    total_by_file = defaultdict(int)      # file -> so material video tro toi
    opt_by_file = defaultdict(int)        # file -> so material se duoc toi uu
    audio_files = set()                   # file bi material AUDIO dung -> khong dam bo
    sizes = {}

    # HEARTBEAT (bug #28): pha nay hoi hang nghin file qua o MANG. Da tung treo chet
    # o day 75s+ khong doc/ghi/CPU nao. Khong co nhip dap thi khong biet la cham hay chet.
    _hb_stop = threading.Event()
    _hb_state = {"file": "(bat dau)", "n": 0, "tot": "?"}

    def _hb():
        t_hb = time.monotonic()
        last = -1
        n_same = 0
        while not _hb_stop.wait(30):
            n = _hb_state["n"]
            # Mot file content co the chua HANG TRAM material -> dung yen vai nhip la
            # BINH THUONG. Chi canh bao khi dung yen qua lau (>5 nhip = 2.5 phut) va
            # noi ro phai lam gi, thay vi doa nguoi dung ngay nhip thu 2.
            n_same = n_same + 1 if n == last else 0
            tag = ""
            if n_same >= 5:
                tag = (f"  (! dung yen {n_same*30}s - neu keo dai, kiem I/O tien trinh:"
                       f" ReadTransferCount/CPU co tang khong)")
            log(f"    [nhip dap] dang xet file content thu {n}/{_hb_state.get('tot','?')}"
                f"  ({(time.monotonic()-t_hb)/60:.1f} phut){tag}")
            last = n

    _t = threading.Thread(target=_hb, daemon=True)
    _t.start()
    try:
        _plan_replacements_body(draft_dir, opts, total_by_file, opt_by_file,
                                audio_files, sizes, _hb_state)
    finally:
        _hb_stop.set()

    skip, nbytes = set(), 0
    for k, n_tot in total_by_file.items():
        if k in audio_files:
            continue                       # con bi audio dung -> phai giu ban goc
        if opt_by_file.get(k, 0) >= n_tot > 0 and G._is_under(k, draft_dir):
            skip.add(k)
            nbytes += sizes.get(k, 0)
    return skip, nbytes


def _plan_replacements_body(draft_dir, opts, total_by_file, opt_by_file,
                            audio_files, sizes, hb_state):
    """Than cua plan_replacements - tach ra de bao heartbeat bao boc duoc."""
    for jf in G.iter_json_files(draft_dir):
        if jf.name not in G.CONTENT_NAMES:
            continue
        hb_state["file"] = jf.name
        hb_state["n"] += 1
        try:
            c, _ = G.read_json_loose(jf)
        except Exception:
            continue
        base = G.draft_root_of(jf, draft_dir)
        for m in (c.get("materials", {}).get("audios") or []):
            if isinstance(m, dict) and m.get("path"):
                f = resolve_material_file(m["path"], base, draft_dir, draft_dir, {})
                if f is not None:
                    audio_files.add(os.path.normcase(str(f)))
        for m in (c.get("materials", {}).get("videos") or []):
            if not isinstance(m, dict) or not m.get("path"):
                continue
            f = resolve_material_file(m["path"], base, draft_dir, draft_dir, {})
            if f is None:
                continue
            k = os.path.normcase(str(f))
            total_by_file[k] += 1
            if k not in sizes:
                try:
                    sizes[k] = os.path.getsize(G._lp(f))
                except OSError:
                    sizes[k] = 0
            # Ban render nguoc cung la MOT tham chieu toi file do -> phai dem vao
            # `total_by_file`, neu khong dieu kien `opt_by_file >= total_by_file`
            # o `plan_replacements()` khong bao gio dat va ban goc van bi copytree
            # chep len dich roi moi bi thay (ton ca chuc GB duong truyen vo ich).
            rp = m.get("reverse_path")
            if rp and isinstance(rp, str):
                fr = resolve_material_file(rp, base, draft_dir, draft_dir, {})
                if fr is not None:
                    kr = os.path.normcase(str(fr))
                    total_by_file[kr] += 1
                    if kr not in sizes:
                        try:
                            sizes[kr] = os.path.getsize(G._lp(fr))
                        except OSError:
                            sizes[kr] = 0
        for j in collect_jobs(c, jf, base, draft_dir, draft_dir, {}, opts, set())[0]:
            opt_by_file[os.path.normcase(str(j["src"]))] += 1


def make_copy_ignore(skip_set):
    """Ham 'ignore' cho shutil.copytree: bo qua dung cac file se bi thay the."""
    def _ignore(dirpath, names):
        d = G._unlp(dirpath)
        out = set()
        for n in names:
            full = os.path.normcase(os.path.abspath(os.path.join(d, n)))
            if full in skip_set:
                out.add(n)
        return out
    return _ignore


def encode_job(ffmpeg, job, tmpdir, crf, preset, timeout=1800, ffprobe=None):
    """Chay ffmpeg cho 1 job. Tra (ok, loi).

    BUG #35: returncode==0 + file ton tai KHONG chung minh thanh cong. Da gap
    file ket qua bi CUT (yeu cau 12,47 s nhung chi ra 1,70 s) ma ffmpeg van tra
    ma 0 -> tool nhan la xong, cap nhat JSON, roi nhan ban cai hong ra moi
    materials/ qua cache/dup. Vi vay phai DO DO DAI ket qua truoc khi nhan.
    """
    tmp = Path(tmpdir) / (f"{abs(hash(job['key'])):x}_" + job["dest"].name)
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-nostdin"]
    if job["lo"] > 0:
        cmd += ["-ss", f"{job['lo'] / US:.3f}"]
    cmd += ["-i", G._lp(job["src"])]
    if job["span"] > 0 and job["trim"]:
        cmd += ["-t", f"{job['span'] / US:.3f}"]
    cmd += ["-map", "0:v:0", "-map", "0:a?"]
    if job["target_w"]:
        cmd += ["-vf", f"scale={job['target_w']}:-2:flags=lanczos"]
    cmd += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf),
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", G._lp(tmp)]
    try:
        r = _run(cmd, timeout)
    except subprocess.TimeoutExpired:
        return False, "ffmpeg qua thoi gian"
    except Exception as ex:
        return False, str(ex)
    if r.returncode != 0 or not G.isfile_safe(tmp):
        return False, (r.stderr or "").strip()[-300:] or f"ffmpeg tra ma {r.returncode}"
    # BUG #35: KIEM DO DAI THAT cua ket qua. File cut van cho returncode 0.
    if ffprobe and job["span"] > 0:
        info = probe(ffprobe, tmp)
        if not info or info[2] <= 0:
            return False, "khong doc duoc do dai ket qua (file hong?)"
        got, want = info[2] / US, job["span"] / US
        # CHI bat chieu NGAN (mat hinh). Ket qua DAI hon yeu cau thi vo hai - truoc
        # day dung abs() nen ban dai hon cung bi tu choi oan.
        if got < want - MAX_DUR_DIFF_S:
            # NGHI NGO - nhung TRUOC KHI KET TOI phai loai tru kha nang NGUON VON DA
            # NGAN hon so `duration` ghi trong JSON cua draft goc. Chinh bug #35 ghi
            # nhan Boom.aac: JSON noi 7,47 s nhung file that chi 3,01 s, va rieng goi
            # DS1_090 co 16 file dang nay. Bao "BI CUT" cho chung la BAO DONG GIA
            # (bai hoc #21/#31: khong nhan toi cai hong CO SAN trong draft goc), va
            # con lam chung khong bao gio duoc nen -> goi to ra vo co.
            # Chi probe NGUON o nhanh nghi ngo => duong chay binh thuong KHONG ton
            # them mot vong I/O nao qua mang.
            info_src = probe(ffprobe, job["src"]) if job.get("src") else None
            co_san = None
            if info_src and info_src[2] > 0:
                co_san = max(0.0, (info_src[2] - job["lo"]) / US)
            # Khong doc duoc nguon = khong phan biet duoc => mac dinh CHUA XONG.
            if co_san is None or got < min(want, co_san) - MAX_DUR_DIFF_S:
                return False, (f"ket qua BI CUT: dai {got:.2f}s nhung yeu cau"
                               f" {want:.2f}s -> giu ban goc")
    try:
        Path(G._lp(job["dest"].parent)).mkdir(parents=True, exist_ok=True)
        shutil.copy2(G._lp(tmp), G._lp(job["dest"]))
    except Exception as ex:
        return False, f"copy ket qua that bai: {ex}"
    finally:
        try:
            os.remove(G._lp(tmp))
        except OSError:
            pass
    return True, ""


OPT_INDEX_NAME = "_opt_index.json"


def _opt_index_path(out_dir):
    return Path(str(out_dir)) / OPT_INDEX_NAME


def _load_opt_index(out_dir, log=print):
    """BUG #29: nap lai cache ma-lai tu DIA de lan chay sau khong ma lai tu dau.

    Tra (cache, key_names). Chi nhan muc nao ma FILE DICH CON TON TAI THAT - neu
    file da bi xoa/dang do thi bo qua (mac dinh 'chua lam', khong tin so sach).
    """
    cache, key_names = {}, {}
    p = _opt_index_path(out_dir)
    try:
        if not G.isfile_safe(p):
            return cache, key_names
        with open(G._lp(p), "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as ex:
        log(f"  (khong doc duoc {OPT_INDEX_NAME}: {ex} -> bo qua, coi nhu chua co cache)")
        return cache, key_names

    n_bo = 0
    for rec in (data.get("items") or []):
        try:
            src, lo, span, tw = rec["key"]
            dest = Path(rec["dest"])
            base = rec.get("base")
        except (KeyError, TypeError, ValueError):
            n_bo += 1
            continue
        if not G.isfile_safe(dest):
            n_bo += 1                 # file dich khong con -> phai ma lai
            continue
        key = (src, int(lo), int(span), int(tw))
        cache[key] = dest
        if base:
            key_names[(base, key)] = dest
    if cache or n_bo:
        log(f"  Cache ma-lai: dung lai {len(cache)} clip da co tren dich"
            f"{f' (bo {n_bo} muc khong con file)' if n_bo else ''}")
    return cache, key_names


def _save_opt_index(out_dir, cache, key_names, log=print):
    """Ghi so cache ra dia. Loi ghi KHONG duoc lam hong lan chay (chi canh bao)."""
    # CHUP NHANH bang list(): hai vong duoi chay trong khi cac thread ma hoa dang
    # chen khoa moi vao CHINH hai dict nay. Duyet `dict.items()` truc tiep se nem
    # RuntimeError "dictionary changed size during iteration" -> loi thoat khoi
    # _save_opt_index -> thoat khoi thread nhip dap (khong co try/except o do) ->
    # MAT CA nhip dap chong treo (#25) LAN co che ghi cache dinh ky (#29).
    # `list(d.items())` la MOT thao tac o tang C, khong co diem doi thread o giua.
    # Do duoc duoi cung dieu kien ep: duyet truc tiep 37/150 lan nem loi, chup
    # nhanh 0/150.
    base_of = {}
    for (b, k), d in list((key_names or {}).items()):
        base_of[k] = b
    items = []
    for k, d in list((cache or {}).items()):
        items.append({"key": [k[0], k[1], k[2], k[3]],
                      "dest": str(d), "base": base_of.get(k)})
    # GHI ATOMIC. Dich thuong la o MANG; ghi de truc tiep ma bi giet dung luc dang
    # ghi = mat sach so cache, tuc dung cai tham hoa ma no sinh ra de chong
    # (#29: 454 -> 907 -> 1367 file trung). Ten file tam mang PID + ID luong nen
    # du co nhieu nhip dap cung ghi mot luc thi moi luong van ghi file rieng, va
    # os.replace chi khien "nguoi cuoi thang" - so LUON nguyen ven, khong can khoa.
    # Duoi .tmp nen cleanup_unused() don duoc neu con sot.
    dich = _opt_index_path(out_dir)
    tam = Path(f"{dich}.{os.getpid()}.{threading.get_ident():x}.tmp")
    try:
        with open(G._lp(tam), "w", encoding="utf-8") as fh:
            json.dump({"version": 1, "items": items}, fh)
        os.replace(G._lp(tam), G._lp(dich))
    except Exception as ex:
        try:
            os.remove(G._lp(tam))
        except OSError:
            pass
        log(f"  ! Khong ghi duoc {OPT_INDEX_NAME}: {ex}"
            f" (chay lai se phai ma lai tu dau)")


def optimize_package(out_dir, draft_dir, resolved, guid, opts, ffmpeg, ffprobe, log=print):
    """Chay toan bo pha toi uu tren BAN XUAT. Tra dict thong ke."""
    # Bat dau mot pha MOI: bo het ket qua probe cua lan chay truoc. Khoa dem da
    # gom kich thuoc + mtime nen ve ly thuyet khong the cu, NHUNG mtime tren mot
    # so he thong tep chi chinh xac toi GIAY - mot file bi ghi de trong cung mot
    # giay ma kich thuoc khong doi se cho khoa Y HET. Xoa o dau pha la cach re
    # nhat de loai han rui ro do.
    xoa_cache_probe()
    st = {"jobs": 0, "ok": 0, "fail": [], "saved": 0, "added": 0,
          "trim": 0, "scale": 0, "reused": 0, "skipped_big": 0, "repointed": 0,
          "recompress": 0, "no_gain": 0,
          # (nguon, ly_do) cho moi material bi LOAI khoi viec ma lai
          "bo_qua": [],
          # (file_goc, so_byte) con bi SO DANG KY giu song sau khi da tro lai
          "con_giu_goc": [],
          "loi_ghi_so": 0}
    opt_by_src = {}          # (draft_root, file_goc) -> file da toi uu (de sua so dang ky)
    # BUG #38: mot file nguon sinh ra NHIEU ban `_opt` (moi doan cat mot file;
    # co clip sinh toi 24 ban). `opt_by_src` chi giu ban DAU TIEN nen nhieu muc
    # so dang ky khong khop -> giu nguyen duong dan goc -> ban goc khong bao gio
    # thanh mo coi -> cleanup khong dam xoa (do that: 9 file, 10,46 GB).
    # Bang nay giu TAT CA cac ban de con chon duoc ban day du nhat.
    opt_all_by_src = defaultdict(list)
    # Dem so lan GHI SO CACHE dinh ky that bai. Truoc day moi lan ghi dinh ky deu
    # nuot loi hoan toan, nen neu dich het cho / mat mang thi co che chong #29 chet
    # am tham suot ca lan chay. Chi in o lan dau de khong spam moi 60 giay.
    _loi_ghi_so = [0]

    def _log_loi_ghi_so(msg):
        _loi_ghi_so[0] += 1
        if _loi_ghi_so[0] == 1:
            log(msg + "  (chi bao lan dau; se dem tiep va ghi vao bao cao)")
    crf = int(opts.get("crf", 20))
    preset = opts.get("preset", "veryfast")
    workers = max(1, min(int(opts.get("workers", 4)), (os.cpu_count() or 4)))
    _saved_srcs = set()              # BUG #30: file nguon da tinh "tiet kiem" (khong cong trung)
    # BUG #29: cache PHAI song qua cac lan chay. Pha nay chay hang gio tren o mang,
    # bi treo/giet tien trinh la chuyen thuong (#25, #28). Neu cache chi nam trong RAM
    # thi lan chay lai se ma lai TU DAU va sinh bo file trung (454 -> 907 -> 1367 file).
    cache, key_names = _load_opt_index(out_dir, log)
    tmpdir = tempfile.mkdtemp(prefix="capcut_opt_")
    t0 = time.monotonic()
    try:
        content_files = [jf for jf in G.iter_json_files(out_dir)
                         if jf.name in G.CONTENT_NAMES]
        for idx, jf in enumerate(content_files, 1):
            # LOG TRUOC khi dung toi file (bug #25): neu treo o doc/ghi qua NAS thi
            # con biet treo o DAU. Khong co dong nay thi "im lang" khong phan biet
            # duoc voi "dang chay cham".
            rel = G._rel_posix(jf, out_dir) or jf.name
            log(f"  [{idx}/{len(content_files)}] dang mo {rel} ...")
            try:
                content, trail = G.read_json_loose(jf)
            except Exception as ex:
                st["fail"].append((str(jf), f"doc JSON loi: {ex}"))
                continue
            base = G.draft_root_of(jf, out_dir)
            used = set()
            try:
                used = {x.lower() for x in os.listdir(G._lp(base / "materials"))}
            except OSError:
                pass
            jobs, bo_qua_file = collect_jobs(content, jf, base, draft_dir, out_dir,
                                             resolved, opts, used, key_names)
            st["bo_qua"].extend(bo_qua_file)
            if not jobs:
                continue
            log(f"  [{idx}/{len(content_files)}] {rel}: {len(jobs)} clip can xu ly")
            st["jobs"] += len(jobs)

            todo = []
            for j in jobs:
                if j.get("dup"):
                    # dung chung file dich voi 1 job khac -> khong ma lai, chi cho ket qua
                    st["reused"] += 1
                    continue
                hit = cache.get(j["key"])
                if hit and G.isfile_safe(hit):
                    try:
                        Path(G._lp(j["dest"].parent)).mkdir(parents=True, exist_ok=True)
                        try:
                            os.link(G._lp(hit), G._lp(j["dest"]))
                        except OSError:
                            shutil.copy2(G._lp(hit), G._lp(j["dest"]))
                        j["done"] = True
                        st["reused"] += 1
                        continue
                    except Exception:
                        pass
                todo.append(j)

            done_n = [0]
            # Clip DANG ma, de nhip dap noi duoc "dang lam gi" chu khong chi
            # "chua xong them clip nao". Do that tren DS3_094: mot clip YouTube
            # dai 25 phut chiem gan NUA thoi gian ca job - nhip dap im lang 15
            # phut lien, va nguoi dung may con se tuong tool treo roi End Task
            # (dung thu tung lam hong draft, xem dau bug.md).
            # dict cua Python an toan cho gan/xoa mot khoa giua cac thread.
            dang_lam = {}

            def work(j):
                dang_lam[id(j)] = (Path(j["src"]).name, j["span"], time.monotonic())
                try:
                    ok, err = encode_job(ffmpeg, j, tmpdir, crf, preset,
                                         ffprobe=ffprobe)
                finally:
                    dang_lam.pop(id(j), None)
                j["done"] = ok
                if not ok:
                    st["fail"].append((str(j["src"]), err))
                else:
                    cache[j["key"]] = j["dest"]
                    key_names[(os.path.normcase(str(base)), j["key"])] = j["dest"]
                done_n[0] += 1
                if done_n[0] % 25 == 0 or done_n[0] == len(todo):
                    el = time.monotonic() - t0
                    log(f"      ...{done_n[0]}/{len(todo)} clip  ({el/60:.1f} phut)")
                return ok

            if todo:
                # HEARTBEAT (bug #25): pha nay co the im lang hang chuc phut khi gap
                # clip dai / doc nguon qua mang. Khong co nhip dap thi khong phan biet
                # duoc "dang chay cham" voi "treo chet o I/O SMB".
                stop_hb = threading.Event()

                # `_stop=stop_hb` BUOC PHAI la tham so mac dinh, khong duoc doc bien
                # ngoai: `stop_hb` bi GAN LAI o moi vong lap file content, ma closure
                # doc theo O NHO chu khong theo gia tri -> thread cua vong truoc se
                # thay Event cua vong SAU, nen `stop_hb.set()` khong dung duoc no.
                # Hau qua: nhieu nhip dap song song, cung ghi mot so cache.
                def _heartbeat(_stop=stop_hb):
                    last = -1
                    while not _stop.wait(60):
                        n = done_n[0]
                        el = time.monotonic() - t0
                        tag = "" if n != last else "  (chua xong them clip nao)"
                        log(f"      [nhip dap] {n}/{len(todo)} clip"
                            f"  ({el/60:.1f} phut){tag}")
                        # Khi so clip DUNG YEN, phai noi ro DANG LAM GI - neu
                        # khong nguoi dung tuong treo. Clip dai 25 phut co the
                        # ma mat hon 30 phut, va do la binh thuong.
                        if n == last:
                            for _ten, _span, _bd in list(dang_lam.values())[:3]:
                                _phut = (time.monotonic() - _bd) / 60
                                _dai = f"{_span / US / 60:.1f} phut" if _span else "ca clip"
                                log(f"         dang ma: {_ten[:52]}"
                                    f"  (doan {_dai}, da chay {_phut:.1f} phut)")
                            if not dang_lam:
                                log("         (khong clip nao dang ma - dang doi"
                                    " I/O hoac dang ghi ket qua)")
                        # BUG #29: ghi so cache dinh ky -> bi giet giua chung thi lan
                        # chay sau chi mat toi da ~60s cong, khong phai ca pha.
                        if n != last:
                            # Truoc day nuot SACH loi bang `log=lambda *_: None`: neu
                            # dich het cho / mat mang thi ca co che chong #29 chet am
                            # tham suot lan chay ma khong ai biet. Gio dem lai va chi
                            # in o lan dau de khong spam moi 60 giay.
                            _save_opt_index(out_dir, cache, key_names,
                                            log=_log_loi_ghi_so)
                        last = n

                hb = threading.Thread(target=_heartbeat, daemon=True)
                hb.start()
                try:
                    with ThreadPoolExecutor(max_workers=workers) as ex:
                        list(ex.map(work, todo))
                finally:
                    stop_hb.set()
                    # Doi nhip dap ket thuc HAN roi moi ghi lan cuoi: neu khong, hai
                    # luong co the cung ghi so mot luc (dich la o mang nen cua so nay
                    # khong he ngan). Ghi atomic da chong hong file, nhung join() con
                    # tranh luon viec ban ghi cu de len ban moi.
                    hb.join(timeout=10)
                    _save_opt_index(out_dir, cache, key_names, log=log)

            # --- Ap dung vao JSON: CHI cho job thanh cong va file dich CO THAT ---
            changed = 0
            for j in jobs:
                if j.get("dup"):
                    j["done"] = G.isfile_safe(j["dest"])
                if not j.get("done") or not G.isfile_safe(j["dest"]):
                    continue
                info = probe(ffprobe, j["dest"])
                if not info or info[2] <= 0:
                    st["fail"].append((str(j["dest"]), "khong doc duoc ket qua sau khi ma"))
                    continue
                w, h, new_dur, _ = info
                try:
                    new_size = os.path.getsize(G._lp(j["dest"]))
                except OSError:
                    new_size = 0
                # VAN AN TOAN: chi nhan ban da ma lai khi no THUC SU nho hon dang ke.
                # Neu khong (vd footage von da nen rat toi), bo ket qua va giu ban goc
                # -> "toi uu" khong bao gio lam ban xuat to ra.
                # Job co CAT GON thi luon giu (da bot thoi luong nen chac chan nho hon).
                if not j["trim"] and not j.get("dup") and new_size >= j["size"] * 0.92:
                    st["no_gain"] += 1
                    try:
                        os.remove(G._lp(j["dest"]))
                    except OSError:
                        pass
                    continue
                rel_m = G._rel_posix(j["dest"], base)
                if not rel_m:
                    st["fail"].append((str(j["dest"]), "khong tinh duoc duong dan tuong doi"))
                    continue
                m = j["m"]
                # Job cua ban render nguoc phai ghi vao `reverse_path`, KHONG duoc
                # ghi de `path` - ghi nham se lam clip xuoi tro vao ban NGUOC.
                # Cung khong duoc dong toi `duration`/`width`/`height`: chung mo ta
                # material XUOI, ban nguoc chi la file dan xuat di kem.
                if j.get("khoa_ghi") == "reverse_path":
                    m["reverse_path"] = f"##_draftpath_placeholder_{guid}_##/{rel_m}"
                else:
                    m["path"] = f"##_draftpath_placeholder_{guid}_##/{rel_m}"
                    m["duration"] = new_dur
                    if w:
                        m["width"], m["height"] = w, h
                if j["trim"] and j["lo"]:
                    for sg in j["segs"]:
                        srt = sg.get("source_timerange")
                        if isinstance(srt, dict) and "start" in srt:
                            srt["start"] = max(0, int(srt["start"]) - j["lo"])
                _kb = (os.path.normcase(str(base)), os.path.normcase(str(j["src"])))
                opt_by_src.setdefault(_kb, j["dest"])
                if j["dest"] not in opt_all_by_src[_kb]:
                    opt_all_by_src[_kb].append(j["dest"])
                # BUG #30: cong theo FILE NGUON DUY NHAT. Mot file 7,5 GB duoc 20
                # material tham chieu se bi cong 20 lan -> tong "tiet kiem" vuot ca
                # dung luong nguon that (da tung bao 1817 GB tren nguon 146 GB).
                _sk = os.path.normcase(str(j["src"]))
                if _sk not in _saved_srcs:
                    _saved_srcs.add(_sk)
                    st["saved"] += max(0, j["size"] - new_size)
                # BUG #30 (mo rong): MOI phep cong don theo JOB deu co nguy co dem
                # trung, khong rieng `saved`. Job `dup` la job dung CHUNG file dich
                # voi mot job khac - no khong goi ffmpeg lan nao va khong them mot
                # byte nao vao dia. Truoc day chi `saved` duoc rao, nen `added`/`ok`/
                # `trim`/`scale`/`recompress` bi NHAN DOI mot cach he thong (do E2E:
                # 1 lan ma that -> st["added"] = dung 2,0 lan kich thuoc file that).
                # Nguon goc: main() luon ghi CA draft_content.json LAN draft_info.json
                # voi cung noi dung, ma ca hai deu nam trong CONTENT_NAMES.
                if not j.get("dup"):
                    st["added"] += new_size
                    st["ok"] += 1
                    st["trim"] += 1 if j["trim"] else 0
                    st["scale"] += 1 if j["scale"] else 0
                    st["recompress"] += 1 if (j.get("recompress") and not j["trim"]
                                              and not j["scale"]) else 0
                changed += 1
            if changed:
                G.write_json_loose(jf, content, trail)

        # PHAI lam sau cung: cho so dang ky tro sang ban da toi uu, neu khong
        # file goc van bi giu lai va goi con to hon ban khong toi uu.
        if opt_by_src:
            st["repointed"], _loi_rp = repoint_registry(
                out_dir, draft_dir, opt_by_src, log,
                opt_all_by_src=opt_all_by_src, resolved=resolved)
            # Noi vao duong bao cao CO SAN thay vi tao co che moi.
            st["fail"].extend(_loi_rp)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    # Bang tra FILE GOC -> BAN DA TOI UU, de plan_package() KHONG lap ke hoach copy
    # ban goc nua (xem bug #23). Khoa la path nguon da normcase; gia tri la dich.
    st["opt_by_src"] = opt_by_src
    # Probe that bai = clip KHONG duoc toi uu. Hang loat loi o day thuong nghia la
    # moi truong hong (bang ma / ffmpeg la), khong phai footage hong -> phai ra
    # bao cao de nguoi dung o may khac gui ve con truy duoc.
    _lp_loi = lay_loi_probe()
    if _lp_loi:
        log(f"  ! {len(_lp_loi)} lan DO clip that bai (ffprobe) -> cac clip do khong"
            f" duoc toi uu. Neu so nay lon, nghi ngo moi truong chu khong phai footage.")
        st["fail"].extend([(p, f"do clip that bai: {m}") for p, m in _lp_loi])
    st["loi_ghi_so"] = _loi_ghi_so[0]
    if _loi_ghi_so[0]:
        log(f"  ! Ghi so cache dinh ky that bai {_loi_ghi_so[0]} lan"
            f" -> neu bi giet giua chung, lan chay sau se ma lai nhieu hon du kien")
    return st


def cleanup_unused(out_dir, log=print):
    """Bo file media MO COI (khong JSON nao tham chieu) + file lich su (*.bak/*.tmp).
    CHI dung toi file trong cac thu muc 'materials/' de khong lam hong cau truc CapCut."""
    refd = set()
    # A2: file JSON nao KHONG doc duoc thi ta KHONG BIET no tham chieu gi. Truoc
    # day chi `continue` -> media ma no dang dung bi coi la MO COI va bi XOA am
    # tham. Gio phai ghi lai, va con mot loi doc thi CAM xoa file mo coi.
    loi_doc = []
    # Truyen list vao de KHONG nem: ham nay van can chay tiep de don *.bak/*.tmp
    # (an toan trong moi truong hop). Nhung mot loi duyet thu muc o day nghia la ta
    # KHONG liet ke het JSON -> `refd` thieu -> khong duoc phep xoa file "mo coi".
    # List rieng vi `onerror` day vao OSError tran, con `loi_doc` giu tuple (file, loi).
    loi_walk = []
    for jf in G.iter_json_files(out_dir, loi=loi_walk):
        try:
            o, _ = G.read_json_loose(jf)
        except Exception as ex:
            loi_doc.append((str(jf), f"{type(ex).__name__}: {ex}"))
            continue
        base = G.draft_root_of(jf, out_dir)

        def cb(k, v, _b=base):
            if not isinstance(v, str) or not v:
                return
            if Path(v.replace("\\", "/")).suffix.lower() not in G.MEDIA_EXT:
                return
            if v.startswith("##"):
                i = v.find("_##")
                if i == -1:
                    return
                tail = v[i + 3:].lstrip("/\\")
            elif v.startswith("./") or v.startswith(".\\"):
                tail = v[2:].lstrip("/\\")
            elif G.is_real_abs(v):
                refd.add(os.path.normcase(os.path.abspath(G._np(v))))
                return
            else:
                return
            refd.add(os.path.normcase(os.path.abspath(str(_b / tail.replace("/", os.sep)))))

        G.deep_walk_strings(o, cb)

    removed_n = removed_b = 0
    fails = []
    # A2: mot file JSON khong doc duoc = khong biet no dung media nao => KHONG duoc
    # xoa file "mo coi" nua. Van don duoc *.bak/*.tmp vi chung an toan trong moi
    # truong hop. Tha de lai vai file thua con hon xoa nham hinh cua nguoi ta.
    # Loi DUYET thu muc cung nguy hiem y het loi DOC file, va con am tham hon:
    # JSON trong nhanh khong duyet duoc chua he duoc liet ke, nen `loi_doc` van
    # RONG trong khi `refd` da thieu. Phai gop vao cung mot chot an toan.
    for _e in loi_walk:
        loi_doc.append((getattr(_e, "filename", "?") or "?",
                        f"khong duyet duoc thu muc: {_e}"))

    # Chot an toan dua tren BANG CHUNG DUONG, khong chi tren "vang mat loi":
    # `refd` rong nghia la khong doc duoc gi ca -> xoa theo no la vo nghia.
    duoc_xoa_mo_coi = bool(refd) and not loi_doc
    if loi_doc:
        log(f"  ! {len(loi_doc)} file JSON KHONG doc/duyet duoc -> BO QUA viec xoa"
            f" file mo coi (khong the biet chac file nao con duoc dung).")
        for tep, vi in loi_doc[:5]:
            log(f"      {tep}  <-- {vi}")
    elif not refd:
        log("  ! KHONG tim thay tham chieu media nao trong goi -> BO QUA viec xoa"
            " file mo coi (xoa theo mot danh sach rong se xoa sach materials/).")

    # Vong XOA. Quet thieu o day hong theo huong AN TOAN (xoa it hon, khong xoa
    # nham), nhung con so "da bo N file" se SAI - va bao cao sai thi lan sau khong
    # ai truy duoc. Ghi vao `fails` de no ra bao cao qua muc "file KHONG xoa duoc".
    _loi_walk2 = []
    for dp, dirs, fs in os.walk(G._lp(out_dir), onerror=_loi_walk2.append):
        plain = G._unlp(dp)
        # A3: phai so theo THANH PHAN THU MUC va tinh TUONG DOI so voi out_dir.
        # Ban cu kiem chuoi con tren duong dan TUYET DOI: neu goi nam duoi mot thu
        # muc ten "materials*" bat ky (vd D:\materials_2026\GOI\...) thi MOI thu muc
        # trong goi deu khop -> pham vi xoa nuot ca ban xuat, ke ca Resources/.
        try:
            rel = os.path.relpath(plain, str(out_dir))
        except ValueError:              # khac o dia - khong the o trong out_dir
            continue
        in_materials = "materials" in [x.lower() for x in rel.split(os.sep) if x]
        for f in fs:
            p = Path(plain) / f
            low = f.lower()
            is_hist = low.endswith(".bak") or low.endswith(".tmp")
            is_orphan = (duoc_xoa_mo_coi
                         and in_materials
                         and Path(f).suffix.lower() in G.MEDIA_EXT
                         and os.path.normcase(os.path.abspath(str(p))) not in refd)
            if not (is_hist or is_orphan):
                continue
            try:
                sz = os.path.getsize(G._lp(p))
                os.remove(G._lp(p))
                removed_n += 1
                removed_b += sz
            except OSError as ex:
                fails.append((str(p), str(ex)))
    for _e in _loi_walk2:
        fails.append((getattr(_e, "filename", "?") or "?",
                      f"khong duyet duoc thu muc khi don: {_e}"
                      f" -> con so 'da bo' ben duoi bi THIEU"))
    log(f"  Da bo {removed_n} file thua (~{removed_b/1e9:.2f} GB)"
        + ("  (! con so nay THIEU: co thu muc khong duyet duoc)" if _loi_walk2 else ""))
    if fails:
        log(f"  ! {len(fails)} file KHONG xoa duoc -> xem bao cao")
    # A4: tra ca `loi_doc` de main() dua vao bao cao. Truoc day `fails` bi main()
    # vut di, nen file xoa khong duoc khong bao gio den mat nguoi dung.
    return removed_n, removed_b, fails, loi_doc


def kiem_ban_goc_thua(out_dir, log=print):
    """NGHIEM THU THUONG TRUC (bai hoc #38): con ban GOC nao nam trong goi ma
    KHONG file noi dung nao dung khong?

    Bug #38 duoc phat hien bang tay, sau khi thay goi phinh vo ly (29,82 GB cho
    32,8 phut timeline). Truy ra: 9 file (10,46 GB) chi con SO DANG KY tro toi,
    nen `cleanup_unused()` khong dam xoa. Phep dem nay bien viec truy tay do thanh
    mot buoc tu dong, luon chay - dung tinh than "phep thu vo ly" cua #18/#19.

    QUAN TRONG (bay #24): phai so bang DUONG DAN da giai, KHONG so bang ten file.
    Lan dau truy bang ten file cho ket qua sai hoan toan.

    Tra list (duong_dan, so_byte) sap xep giam dan theo dung luong.
    """
    dung_boi_content = set()
    for jf in G.iter_json_files(out_dir):
        if G.json_role(jf.name) != "content":
            continue
        try:
            o, _ = G.read_json_loose(jf)
        except Exception as ex:
            # "Khong ket luan gi" KHONG duoc bien thanh "khong noi gi voi ai"
            # (bai hoc A2). File noi dung nay khong doc duoc nghia la ta khong
            # biet no dung media nao -> con so "ban goc thua" ben duoi duoc tinh
            # TREN DU LIEU THIEU va co the bao thua NHAM.
            log(f"  ! Khong doc duoc {jf.name} khi dem ban goc thua: {ex}"
                f" -> con so ben duoi co the SAI (tinh thieu file noi dung nay)")
            continue
        base = G.draft_root_of(jf, out_dir)

        def cb(k, v, _b=base):
            if not isinstance(v, str) or not v:
                return
            if Path(v.replace("\\", "/")).suffix.lower() not in G.MEDIA_EXT:
                return
            real = resolve_material_file(v, _b, _b, out_dir, {})
            if real is not None:
                dung_boi_content.add(os.path.normcase(os.path.abspath(str(real))))

        G.deep_walk_strings(o, cb)

    thua = []
    # Quet thieu -> bao "khong co ban goc thua" SAI. Ham nay la mot PHEP NGHIEM THU
    # (bai hoc #38), ma phep nghiem thu noi doi con te hon khong co phep nao.
    _loi_walk = []
    for dp, _d, fs in os.walk(G._lp(out_dir), onerror=_loi_walk.append):
        plain = G._unlp(dp)
        for f in fs:
            if Path(f).suffix.lower() not in G.MEDIA_EXT:
                continue
            if "_opt" in f.lower():
                continue                     # ban da toi uu - dung nghia
            pth = Path(plain) / f
            if os.path.normcase(os.path.abspath(str(pth))) in dung_boi_content:
                continue
            try:
                thua.append((str(pth), os.path.getsize(G._lp(pth))))
            except OSError:
                pass
    if _loi_walk:
        raise OSError(f"khong duyet duoc {len(_loi_walk)} thu muc khi dem ban goc"
                      f" thua: {_loi_walk[0]}"
                      f"  -> con so ben duoi se THIEU, khong duoc coi la 'khong thua'")
    thua.sort(key=lambda x: -x[1])
    if thua:
        tong = sum(x[1] for x in thua)
        log(f"  ! {len(thua)} ban GOC con trong goi ma KHONG file noi dung nao dung"
            f" (~{tong / 1e9:.2f} GB) - xem bao cao")
    return thua


def repoint_registry(out_dir, draft_dir, opt_by_src, log=print,
                     opt_all_by_src=None, resolved=None):
    """Cho MOI file JSON con tro toi ban goc chuyen sang tro vao ban DA TOI UU.

    Neu bo qua buoc nay: so dang ky van tro vao file GOC -> file goc van bi coi la
    'dang duoc dung' -> cleanup khong dam xoa -> goi chua CA HAI ban (goc + da toi uu)
    va con TO HON ban khong toi uu. Day la cai bay chinh cua tinh nang nay."""
    n = 0
    loi_doc = []
    resolved = resolved or {}
    opt_all_by_src = opt_all_by_src or {}
    # Gom bang tra theo TEN FILE NGUON (khong phan biet draft root): file cache/so dang ky
    # co the nam o root khac voi noi clip duoc toi uu, nhung van tro toi cung file goc.
    by_src = {}
    for (b, srckey), dest in opt_by_src.items():
        by_src.setdefault(srckey, dest)

    # BUG #38: mot nguon co NHIEU ban `_opt`. Muc so dang ky chi phuc vu THU VIEN
    # MEDIA cua CapCut (khong phai timeline), nen tro no vao ban DAY DU NHAT - tuc
    # ban co kich thuoc lon nhat trong so cac ban da ma. Nho vay ban GOC khong con
    # ai tro toi va `cleanup_unused()` moi don duoc no.
    day_du_nhat = {}
    for (b, srckey), ds in opt_all_by_src.items():
        tot, to_nhat = None, -1
        for d in ds:
            try:
                sz = os.path.getsize(G._lp(d))
            except OSError:
                continue
            if sz > to_nhat:
                tot, to_nhat = d, sz
        if tot is not None:
            day_du_nhat.setdefault(srckey, tot)

    for jf in G.iter_json_files(out_dir):
        try:
            obj, trail = G.read_json_loose(jf)
        except Exception as ex:
            # KHONG duoc im lang (cung ho bug A2 da va o cleanup_unused). File nay
            # khong duoc viet lai nen duong dan trong no VAN TRO VAO BAN GOC: may
            # nay mo van du vi file goc con nam do, nhung MAY KHAC se mat dung
            # phan do - ma bao cao lai noi "DU".
            loi_doc.append((str(jf), f"doc JSON loi khi viet lai so dang ky: {ex}"))
            continue
        base = G.draft_root_of(jf, out_dir)
        changed = [0]

        def fix(k, v):
            # PHAI xu ly ca path TUYET DOI lan TUONG DOI/placeholder: so dang ky cua
            # draft goc thuong ghi './materials/video/x.mp4' (tuong doi). Neu chi loc
            # path tuyet doi thi cac muc nay khong duoc tro lai -> file goc van bi coi
            # la 'dang dung' -> cleanup khong xoa duoc (lap lai dung bug #14).
            if not isinstance(v, str) or not v:
                return None
            if Path(v.replace("\\", "/")).suffix.lower() not in G.MEDIA_EXT:
                return None
            # PHAI truyen `resolved` y het luc collect_jobs() giai duong dan. Neu
            # truyen {} thi file nao duoc "do theo ten" se giai ra ket qua KHAC voi
            # khoa da luu -> khong khop -> muc so dang ky giu nguyen path goc (bug #38).
            real = resolve_material_file(v, base, draft_dir, out_dir, resolved)
            if real is None:
                return None
            key = os.path.normcase(str(real))
            dest = (opt_by_src.get((os.path.normcase(str(base)), key))
                    or by_src.get(key)
                    or day_du_nhat.get(key))
            if dest is None or not G.isfile_safe(dest):
                return None
            rel = G._rel_posix(dest, base)
            if not rel:
                return None
            changed[0] += 1
            return f"./{rel}" if k == "file_Path" else f"##_draftpath_placeholder_{G.DEFAULT_GUID}_##/{rel}"

        G.deep_rewrite_strings(obj, fix)
        if changed[0]:
            G.write_json_loose(jf, obj, trail)
            n += changed[0]
    log(f"  Da tro {n} tham chieu (so dang ky + cache) sang ban da toi uu")
    if loi_doc:
        log(f"  ! {len(loi_doc)} file JSON KHONG doc duoc khi viet lai so dang ky"
            f" -> duong dan trong chung VAN TRO VAO BAN GOC (may khac se hong)")

    return n, loi_doc


def prune_registry(out_dir, log=print):
    """Bo cac muc trong SO DANG KY (draft_materials) tro toi file KHONG co trong goi.

    O che do 4 ta co y KHONG gom footage chi nam trong kho (khong dung tren timeline).
    Neu de nguyen, so dang ky se treo hang nghin muc chet -> CapCut hien 'kho media'
    day file thieu, va lop tu kiem bao hong. Bo han muc do chinh la y nghia cua
    'bo file khong dung'. Timeline KHONG bi anh huong vi no doc materials trong
    draft_content.json, khong doc so dang ky."""
    removed = kept = 0
    for jf in G.iter_json_files(out_dir):
        if jf.name != "draft_meta_info.json":
            continue
        base = jf.parent
        try:
            meta, trail = G.read_json_loose(jf)
        except Exception as ex:
            # Khong doc duoc so dang ky -> khong don duoc muc chet trong no. Phai
            # noi ra: o may con, CapCut se hien 'kho media' day file thieu.
            log(f"  ! Khong doc duoc {jf.name} de don so dang ky: {ex}"
                f" -> kho media o may khac se con muc chet")
            continue
        changed = False
        for blk in (meta.get("draft_materials") or []):
            vals = blk.get("value")
            if not isinstance(vals, list):
                continue
            keep = []
            for e in vals:
                fp = (e or {}).get("file_Path") if isinstance(e, dict) else None
                if not fp:
                    keep.append(e)
                    continue
                real = resolve_material_file(fp, base, base, out_dir, {})
                inside = real is not None and G._is_under(real, out_dir)
                if inside:
                    keep.append(e)
                    kept += 1
                else:
                    removed += 1
                    changed = True
            blk["value"] = keep
        if changed:
            G.write_json_loose(jf, meta, trail)
    log(f"  So dang ky: bo {removed} muc tro toi footage khong dung, giu {kept} muc")
    return removed, kept


def _lech_san_o_goc(draft_dir):
    """Tap material_id DA lech san trong draft GOC (truoc khi goi).

    Vi sao can: CapCut tu no ghi `source_timerange` vuot qua `duration` mot
    chut (do that: +0.100s tren DS1_124). Do la lech VON CO, khong phai do
    viec goi gay ra - mang sang may khac no cung khong te hon may goc.
    Bao chung thanh "BI LECH sau khi cat gon" la BAO CAO SAI: nguoi dung se
    di tim mot loi khong ton tai, va cau ket luan bi ha xuong "CON THIEU"
    trong khi goi that su du.
    """
    ra = set()
    if not draft_dir:
        return ra
    try:
        cac_file = list(G.iter_json_files(draft_dir))
    except Exception:
        return ra
    for jf in cac_file:
        if jf.name not in G.CONTENT_NAMES:
            continue
        try:
            c, _ = G.read_json_loose(jf)
        except Exception:
            continue          # doc khong duoc thi thoi, khong the ket luan gi
        dur_of = {}
        for cat in ("videos", "audios"):
            for m in (c.get("materials", {}).get(cat) or []):
                if isinstance(m, dict) and m.get("id"):
                    dur_of[m["id"]] = int(m.get("duration") or 0)
        for tr in (c.get("tracks") or []):
            for sg in (tr.get("segments") or []):
                mid, srt = sg.get("material_id"), sg.get("source_timerange")
                if not mid or mid not in dur_of or not isinstance(srt, dict):
                    continue
                d = dur_of[mid]
                if d <= 0:
                    continue
                s1 = int(srt.get("start") or 0) + int(srt.get("duration") or 0)
                # NGUONG THAP HON `verify_optimize` (`>` thanh `>=`, va tru them
                # mot chut). Ly do do duoc tren DS1_124: draft goc lech DUNG
                # BANG 100_000us, tuc la vua LOT qua phep kiem `s1 > d+100_000`.
                # Sau khi cat gon, `duration` cua material doi tu 30.700s xuong
                # 25.592s (do dai ban _opt that) trong khi doan dung giu nguyen
                # 25.200s -> lech thanh 108_000us va vuot nguong.
                # Neu o day dung DUNG mot nguong voi `verify_optimize` thi lech
                # von co KHONG BAO GIO nhan ra duoc, va ban va thanh vo dung.
                if s1 >= d + 90_000:
                    ra.add(mid)
    return ra


def verify_optimize(out_dir, draft_dir=None):
    """TU KIEM rieng cho pha toi uu: khong segment nao duoc tro ra ngoai do dai
    material (dau hieu chac chan cua viec doi offset SAI -> hinh se bi lech).

    `draft_dir`: neu truyen vao, material NAO DA LECH SAN trong draft goc se
    duoc xep rieng - ta khong lam no lech, va no khong lam goi te hon ban goc.
    Cung cach lam nhu `G.verify_package(out_dir, draft_dir)`.

    Tra ve (bad, lech_san) - `bad` la loi THAT do goi gay ra (CHAN),
    `lech_san` la lech von co (chi GHI NHAN).
    """
    lech_goc = _lech_san_o_goc(draft_dir)
    bad = []
    lech_san = []
    for jf in G.iter_json_files(out_dir):
        if jf.name not in G.CONTENT_NAMES:
            continue
        try:
            c, _ = G.read_json_loose(jf)
        except Exception as ex:
            bad.append((str(jf), "", f"doc JSON loi: {ex}"))
            continue
        rel = G._rel_posix(jf, out_dir) or jf.name
        dur_of = {}
        for cat in ("videos", "audios"):
            for m in (c.get("materials", {}).get(cat) or []):
                if isinstance(m, dict) and m.get("id"):
                    dur_of[m["id"]] = int(m.get("duration") or 0)
        for tr in (c.get("tracks") or []):
            for sg in (tr.get("segments") or []):
                mid, srt = sg.get("material_id"), sg.get("source_timerange")
                if not mid or mid not in dur_of or not isinstance(srt, dict):
                    continue
                d = dur_of[mid]
                if d <= 0:
                    continue
                s0 = int(srt.get("start") or 0)
                s1 = s0 + int(srt.get("duration") or 0)
                if s0 < 0:
                    bad.append((rel, mid, f"start am ({s0})"))
                elif s1 > d + 100_000:          # cho sai so 0.1s
                    mo_ta = (f"doan dung vuot do dai clip: het o {s1/US:.2f}s"
                             f" nhung clip chi dai {d/US:.2f}s")
                    if mid in lech_goc:
                        # DA lech san o draft goc -> khong phai loi cua ta.
                        lech_san.append((rel, mid, mo_ta + " (DA LECH SAN o draft goc)"))
                    else:
                        bad.append((rel, mid, mo_ta))
    return bad, lech_san
