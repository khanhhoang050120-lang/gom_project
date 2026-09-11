# -*- coding: utf-8 -*-
"""E2E tren draft gia: chay ca luong that, roi CHUNG MINH ban xuat tu chua.

Gom ba loai kiem ma bug.md coi la bat buoc:

  D2 - TINH CHAT quan trong nhat: tool KHONG BAO GIO ghi/xoa gi trong draft GOC.
       Do bang cach bam van tay (hash) toan bo draft goc truoc va sau khi chay.

  D3 - CHUNG MINH TU CHUA bang cach DOI CHO GOI. Mo tai cho cu la bang chung GIA
       vi duong dan tuyet doi van resolve duoc o may goc (checklist bug.md).

  D4 - EP LOI: bat cac buoc that bai roi khang dinh bao cao PHAI noi that bai,
       khong duoc in "Ban tu chua DU".
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from draft_gia import tao_draft_gia          # noqa: E402
import chay_tool                             # noqa: E402
import nghiem_thu_goi as NT                  # noqa: E402
#  ^ VERIFIER DOC LAP. Cac phep kiem ben duoi dung `G.iter_json_files`,
#    `G.deep_walk_strings`, `G.is_real_abs` - tuc la HAM CUA CHINH TOOL.
#    Neu tool hieu sai dinh dang CapCut, no ghi sai theo dung cai hieu sai
#    do roi tu kiem lai bang chinh ham da hieu sai -> bo kiem XANH trong
#    khi goi HONG. `nghiem_thu_goi` viet tu dau, khong import gi cua tool,
#    nen no hoi mot cau KHAC HAN: 'mot chuong trinh khac, khong biet gi ve
#    tool, co mo duoc goi nay khong?'

pas = fail = 0


def check(ten, dk, chi_tiet=""):
    global pas, fail
    if dk:
        pas += 1
        print(f"  PASS  {ten}")
    else:
        fail += 1
        print(f"  FAIL  {ten}")
        if chi_tiet:
            for d in str(chi_tiet).splitlines():
                print(f"           {d}")


def van_tay(thu_muc):
    """Bam van tay toan bo cay thu muc: duong dan tuong doi + kich thuoc + noi dung."""
    G = chay_tool.nap_tool()
    ra = {}
    for dp, _dirs, fs in os.walk(G._lp(thu_muc)):
        for f in fs:
            p = Path(G._unlp(dp)) / f
            rel = os.path.relpath(str(p), str(thu_muc))
            try:
                b = Path(G._lp(p)).read_bytes()
            except OSError as ex:
                ra[rel] = f"<khong doc duoc: {ex}>"
                continue
            ra[rel] = hashlib.sha256(b).hexdigest()
    return ra


def doc_bao_cao(out_dir):
    p = Path(out_dir) / "_BAO_CAO_THIEU.txt"
    G = chay_tool.nap_tool()
    if not G.isfile_safe(p):
        return None
    return Path(G._lp(p)).read_text(encoding="utf-8", errors="replace")


def dem_media(thu_muc):
    G = chay_tool.nap_tool()
    n = 0
    for dp, _d, fs in os.walk(G._lp(thu_muc)):
        for f in fs:
            if Path(f).suffix.lower() in G.VIDEO_AUDIO_EXT:
                n += 1
    return n


# ==========================================================================
def kich_ban_binh_thuong(ffmpeg, ffprobe):
    print("=" * 72)
    print("E2E 1 - luong binh thuong (che do NGUYEN BAN)")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="e2e_ok_"))
    try:
        mo_ta = tao_draft_gia(tmp, ffmpeg, ffprobe)
        draft = mo_ta["draft_dir"]
        out = tmp / "GOI_RA"

        truoc = van_tay(draft)                       # D2: van tay TRUOC
        G = chay_tool.nap_tool()
        ma, ra, _ = chay_tool.chay(G, draft, out, che_do="1")
        sau = van_tay(draft)                         # D2: van tay SAU

        check("main() chay xong khong thoat bat thuong", ma is None, f"ma thoat = {ma}")

        # --- D2: draft GOC phai NGUYEN VEN ---
        doi = [k for k in set(truoc) | set(sau) if truoc.get(k) != sau.get(k)]
        check("D2: draft GOC khong bi doi mot byte nao",
              not doi, "File bi doi/them/mat:\n" + "\n".join(f"- {d}" for d in doi[:10]))

        bc = doc_bao_cao(out)
        check("co file _BAO_CAO_THIEU.txt", bc is not None)
        if bc:
            check("bao cao ghi so hieu phien ban",
                  "goi_project_capcut " in bc and "Python" in bc,
                  bc.splitlines()[0] if bc else "")
            check("bao cao ket luan DU", "Khong thieu" in bc,
                  "\n".join(bc.splitlines()[:24]))

        kiem_hai_file_noi_dung(out)
        kiem_subdraft_nhieu_tang(out, draft)

        # --- NGHIEM THU DOC LAP (V-1..V-4) ---
        kq = NT.nghiem_thu(out)
        check("V-0 verifier doc lap kiem duoc tham chieu THAT (N > 0)",
              kq.tong_tham_chieu > 0,
              "quet 0 tham chieu -> khong ket luan duoc gi (bug #36)")
        check("V-1 khong con duong dan TUYET DOI trong goi",
              not kq.tuyet_doi,
              "\n".join(f"{f.name} :: {k} = {v}"
                        for f, k, v in kq.tuyet_doi[:8]))
        check("V-2 moi tham chieu phan giai duoc toi file co that",
              not kq.khong_phan_giai,
              "\n".join(f"{f.name} :: {k} = {v}"
                        for f, k, v in kq.khong_phan_giai[:8]))
        check("V-2 khong co file media RONG (0 byte)", not kq.rong,
              "\n".join(f"{f.name} :: {v}" for f, k, v in kq.rong[:8]))
        check("V-3 de quy duoc vao subdraft (tim thay > 1 draft root)",
              len(kq.draft_root) > 1, f"chi thay {len(kq.draft_root)} root")
        check("V-4 moi .json parse duoc sau khi tool ghi lai",
              not kq.json_hong,
              "\n".join(f"{f.name}: {e}" for f, e in kq.json_hong[:8]))

        # --- PHEP THU DI CHUYEN: bang chung TU CHUA that su ---
        #  Mo goi tai CHO CU khong chung minh duoc gi - duong dan tuyet doi
        #  cu van resolve duoc tren chinh may nay (checklist bug.md: "chung
        #  minh tu chua phai bang cach DOI CHO goi roi verify lai").
        cho_moi = tmp / "DA_DOI_CHO" / "sau_khi_chuyen"
        cho_moi.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(out, cho_moi)
        kq2 = NT.nghiem_thu(cho_moi)
        check("DI CHUYEN: goi van TU CHUA sau khi doi cho", kq2.dat(),
              f"tuyet_doi={len(kq2.tuyet_doi)}"
              f" khong_pg={len(kq2.khong_phan_giai)} rong={len(kq2.rong)}")
        check("DI CHUYEN: van kiem dung so tham chieu nhu truoc",
              kq2.tong_tham_chieu == kq.tong_tham_chieu,
              f"{kq2.tong_tham_chieu} vs {kq.tong_tham_chieu}")

        # --- Media phai duoc gom sang dich ---
        n_goc = dem_media(mo_ta["footage_dir"]) + dem_media(draft)
        n_dich = dem_media(out)
        check("da gom media sang ban xuat", n_dich >= 4,
              f"nguon {n_goc} file, dich {n_dich} file")

        # --- Khong con duong dan tuyet doi tro RA NGOAI goi ---
        con_ngoai = []
        for jf in G.iter_json_files(out):
            try:
                obj, _ = G.read_json_loose(jf)
            except Exception as ex:
                con_ngoai.append(f"{jf.name}: khong doc duoc ({ex})")
                continue

            def cb(k, v, _jf=jf):
                if not isinstance(v, str) or not G.is_real_abs(v):
                    return
                if Path(v.replace("/", os.sep)).suffix.lower() not in G.VIDEO_AUDIO_EXT:
                    return
                if not G._is_under(v, out):
                    con_ngoai.append(f"{_jf.name}: {v}")
            G.deep_walk_strings(obj, cb)
        check("khong con tham chieu media tro RA NGOAI goi",
              not con_ngoai, "\n".join(con_ngoai[:10]))

        # --- D3: DOI CHO GOI roi tu kiem lai ---
        cho_moi = tmp / "DA_CHUYEN_CHO"
        shutil.move(str(out), str(cho_moi))
        bad = G.verify_package(cho_moi, None)
        bad_that = [b for b in bad if not b[3]]      # bo qua anh bia
        check("D3: sau khi DOI CHO, khong tham chieu nao hong",
              not bad_that,
              "\n".join(f"- {b[0]} | {b[1]} | {b[2]}" for b in bad_that[:10]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
def kich_ban_thieu_file(ffmpeg, ffprobe):
    print()
    print("=" * 72)
    print("D4 - draft co tham chieu toi file KHONG ton tai -> phai bao THIEU")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="e2e_thieu_"))
    try:
        mo_ta = tao_draft_gia(tmp, ffmpeg, ffprobe, co_file_thieu=True)
        out = tmp / "GOI_RA"
        G = chay_tool.nap_tool()
        # thu_muc_do = thu muc rong -> chac chan KHONG do ra file thieu
        rong = tmp / "RONG"
        rong.mkdir(exist_ok=True)
        ma, ra, _ = chay_tool.chay(G, mo_ta["draft_dir"], out, che_do="1",
                                   thu_muc_do=str(rong))
        check("main() khong chet khi co file thieu", ma is None, f"ma thoat = {ma}")
        bc = doc_bao_cao(out)
        check("co bao cao", bc is not None)
        if bc:
            check("bao cao KHONG duoc ket luan 'Khong thieu'",
                  "Khong thieu" not in bc,
                  "\n".join(bc.splitlines()[:24]))
            check("bao cao co nhac file thieu",
                  "khong_he_ton_tai" in bc,
                  "\n".join(bc.splitlines()[:24]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
def kich_ban_ep_verify_chet(ffmpeg, ffprobe):
    print()
    print("=" * 72)
    print("D4 - EP verify_package() nem loi -> TUYET DOI khong duoc bao 'DU'")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="e2e_verr_"))
    try:
        mo_ta = tao_draft_gia(tmp, ffmpeg, ffprobe)
        out = tmp / "GOI_RA"
        G = chay_tool.nap_tool()

        that = G.verify_package

        def no_loi(*a, **k):
            raise OSError("[ep loi] mat ket noi toi o mang giua chung")

        G.verify_package = no_loi
        try:
            ma, ra, _ = chay_tool.chay(G, mo_ta["draft_dir"], out, che_do="1")
        finally:
            G.verify_package = that

        check("main() khong chet khi bo kiem nem loi", ma is None, f"ma thoat = {ma}")
        bc = doc_bao_cao(out)
        check("co bao cao", bc is not None)
        if bc:
            check("KHONG duoc in 'Khong thieu. Ban tu chua DU'",
                  "Khong thieu" not in bc,
                  "DAY LA BUG #41 - truoc khi sua, cho nay in 'DU' du chua he kiem")
            check("bao cao co muc 'BO TU KIEM THAT BAI'",
                  "BO TU KIEM THAT BAI" in bc,
                  "\n".join(bc.splitlines()[:30]))
            check("bao cao noi ro chua ket luan duoc",
                  "CHUA KET LUAN DUOC" in bc,
                  "\n".join(bc.splitlines()[:30]))
        check("console canh bao muc NANG", "NANG" in ra or "THAT BAI" in ra,
              ra[-600:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
def kich_ban_chan_ghi_de_goc(ffmpeg, ffprobe):
    print()
    print("=" * 72)
    print("A0 - dan nham chinh project goc vao o XUAT RA -> phai DUNG LAI")
    print("=" * 72)
    tmp = Path(tempfile.mkdtemp(prefix="e2e_a0_"))
    try:
        mo_ta = tao_draft_gia(tmp, ffmpeg, ffprobe)
        draft = mo_ta["draft_dir"]
        G = chay_tool.nap_tool()

        for ten, dich in (("dich TRUNG draft goc", draft),
                          ("dich NAM TRONG draft goc", draft / "GOI_RA"),
                          ("draft goc NAM TRONG dich", tmp)):
            truoc = van_tay(draft)
            ma, ra, _ = chay_tool.chay(G, draft, dich, che_do="1")
            sau = van_tay(draft)
            doi = [k for k in set(truoc) | set(sau) if truoc.get(k) != sau.get(k)]
            check(f"{ten}: draft goc khong doi mot byte",
                  not doi, "\n".join(f"- {d}" for d in doi[:8]))
            check(f"{ten}: co in canh bao DUNG LAI", "DUNG LAI" in ra, ra[-400:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def kiem_subdraft_nhieu_tang(out, draft):
    """Du an con LONG NHIEU TANG phai sang du, va media trong do phai giai duoc.

    Do that: CA SAU project that deu co subdraft long nhau; `DS3_094` co 17
    subdraft du 3 tang (du an con LONG TRONG du an con, roi clip ghep trong do).
    Truoc khi them fixture nay, draft gia chi co MOT tang - tuc 23 bo kiem chua
    bao gio cham toi tang 2/3.
    """
    from chung import CONTENT_NAMES, isfile_safe

    def cay(goc):
        ra = {}

        def di(base, tien_to=""):
            sd = Path(base) / "subdraft"
            if not sd.is_dir():
                return
            try:
                ds = sorted(os.listdir(str(sd)))
            except OSError:
                return
            for nm in ds:
                con = sd / nm
                if not con.is_dir():
                    continue
                if not any(isfile_safe(con / x) for x in CONTENT_NAMES):
                    continue
                rel = f"{tien_to}subdraft/{nm}".lower()
                ra[rel] = con
                di(con, rel + "/")

        di(goc)
        return ra

    c_nguon, c_goi = cay(draft), cay(out)
    sau_nhat = max([r.count("subdraft/") for r in c_nguon] or [0])
    check("draft gia co subdraft long IT NHAT 3 tang", sau_nhat >= 3,
          f"tang sau nhat = {sau_nhat} -> fixture khong cham toi truong hop that"
          " (DS3_094 co 3 tang)")
    mat = sorted(set(c_nguon) - set(c_goi))
    check(f"moi subdraft sang du ({len(c_nguon)} cai, {sau_nhat} tang)", not mat,
          "MAT:\n" + "\n".join(f"- {m}" for m in mat[:5]))

    # Media o tang sau nhat phai giai duoc trong goi
    for rel, con in sorted(c_goi.items(), key=lambda x: -x[0].count("subdraft/"))[:1]:
        n = sum(1 for _dp, _dn, fn in os.walk(str(con)) for f in fn
                if Path(f).suffix.lower() in (".mp4", ".mov", ".m4a", ".aac"))
        check(f"subdraft sau nhat co media ({rel[-40:]})", n > 0,
              "sang du thu muc nhung RONG media -> may con mo ra se thieu hinh")

    # ĐIỂM QUAN TRỌNG NHẤT: JSON trong subdraft SÂU phai duoc XU LY, khong chi
    # duoc chep sang. `copytree` luon chep ca cay nen phep kiem "thu muc co sang
    # du khong" LUON XANH - ke ca khi `iter_json_files()` bo qua chung hoan toan.
    # Da chung minh: gai loi cho iter_json_files bo qua subdraft long -> phep
    # kiem cu VAN XANH. Phai kiem thu that su quyet dinh: moi file noi dung o
    # MOI TANG deu KHONG con duong dan tuyet doi.
    import json as _json
    from chung import MEDIA_EXT, CONTENT_NAMES as _CN
    B = chr(92)

    def con_tuyet_doi(o):
        if isinstance(o, str):
            q = o.replace("\\", "/")
            la_abs = (len(o) > 1 and o[1] == ":") or o.startswith(B * 2) or q.startswith("//")
            if la_abs and Path(q).suffix.lower() in MEDIA_EXT:
                yield o
        elif isinstance(o, dict):
            for v in o.values():
                yield from con_tuyet_doi(v)
        elif isinstance(o, list):
            for v in o:
                yield from con_tuyet_doi(v)

    n_kiem = 0
    for rel, con in sorted(c_goi.items()):
        tang = rel.count("subdraft/")
        for ten in _CN:
            jf = con / ten
            if not jf.is_file():
                continue
            n_kiem += 1
            try:
                sot = sorted(set(con_tuyet_doi(_json.loads(
                    jf.read_text(encoding="utf-8")))))
            except Exception as ex:
                check(f"doc duoc {ten} o tang {tang}", False, str(ex))
                continue
            check(f"tang {tang}: {ten} da duoc viet lai het duong dan tuyet doi",
                  not sot,
                  f"con {len(sot)} duong dan tuyet doi: {sot[:2]}"
                  "\n-> file JSON nay KHONG duoc xu ly (chi duoc copytree chep"
                  " sang) -> may con mo ra se tro vao duong dan cu")
    check("co kiem it nhat mot file noi dung trong subdraft", n_kiem > 0,
          "khong tim thay file noi dung nao trong subdraft -> phep kiem vo nghia")

    # CHOT CHONG RONG - quan trong nhat.
    # Phep kiem tren chi co y nghia neu NGUON that su co duong dan tuyet doi o
    # tang sau de ma viet lai. Neu fixture chi dung placeholder o moi tang thi
    # "khong con duong dan tuyet doi" LUON dung, va bo kiem xanh vi KHONG CO GI
    # DE KIEM. Da mac dung bay do: gai loi cho iter_json_files bo qua subdraft
    # long -> bo kiem VAN XANH.
    n_abs_nguon = 0
    for rel, con in c_nguon.items():
        if rel.count("subdraft/") < 2:
            continue
        for ten in _CN:
            jf = con / ten
            if not jf.is_file():
                continue
            try:
                n_abs_nguon += len(set(con_tuyet_doi(_json.loads(
                    jf.read_text(encoding="utf-8")))))
            except Exception:
                pass
    check("NGUON co duong dan tuyet doi o subdraft tang >=2 (de co gi ma kiem)",
          n_abs_nguon > 0,
          "fixture chi dung placeholder o tang sau -> phep kiem tren la XANH GIA:"
          " no dung ma khong chung minh duoc gi")


def kiem_hai_file_noi_dung(out):
    """`draft_content.json` va `draft_info.json` phai duoc viet lai NHAT QUAN.

    CapCut giu HAI file noi dung song song (do that: DS3_003 va DS3_094 deu co).
    Neu tool chi viet lai mot cai, may con co the mo ra ban CHUA duoc viet lai
    -> tro vao duong dan cu -> mat hinh. Va bo tu kiem van co the bao "DU" neu
    no chi soi file kia.

    Kiem: hai file phai con LAI CUNG MOT TAP duong dan tuyet doi.
    """
    import json as _json
    from chung import MEDIA_EXT
    B = chr(92)

    def tuyet_doi(o):
        if isinstance(o, str):
            q = o.replace("\\", "/")
            la_abs = (len(o) > 1 and o[1] == ":") or o.startswith(B * 2) or q.startswith("//")
            if la_abs and Path(q).suffix.lower() in MEDIA_EXT:
                yield o
        elif isinstance(o, dict):
            for v in o.values():
                yield from tuyet_doi(v)
        elif isinstance(o, list):
            for v in o:
                yield from tuyet_doi(v)

    n_cap = 0
    for dp, _dn, fn in os.walk(str(out)):
        if not {"draft_content.json", "draft_info.json"} <= set(fn):
            continue
        n_cap += 1
        tap = {}
        for f in ("draft_content.json", "draft_info.json"):
            try:
                with open(os.path.join(dp, f), "r", encoding="utf-8") as fh:
                    tap[f] = set(tuyet_doi(_json.load(fh)))
            except Exception as ex:
                check(f"doc duoc {f}", False, str(ex))
                return
        a, b = tap["draft_content.json"], tap["draft_info.json"]
        rel = os.path.relpath(dp, str(out))
        check(f"hai file noi dung NHAT QUAN ({rel})", a == b,
              f"chi trong content: {sorted(a - b)[:2]}"
              f"\nchi trong info   : {sorted(b - a)[:2]}"
              "\n-> mot file da duoc viet lai, file kia CHUA -> may con co the"
              " mo ra ban cu va mat hinh")
    check("co it nhat mot cap file noi dung de kiem", n_cap > 0,
          "draft gia khong sinh draft_info.json -> phep kiem nay vo nghia")


def main():
    sys.path.insert(0, str(HERE.parent))
    import toi_uu_dung_luong as TU
    ffmpeg, ffprobe = TU.ff_paths(HERE.parent)
    if not ffmpeg:
        print("KET QUA: 0 PASS / 0 FAIL")
        print("BO QUA: khong tim thay ffmpeg/ffprobe - E2E can ma hoa media that")
        return 2
    kich_ban_binh_thuong(ffmpeg, ffprobe)
    kich_ban_thieu_file(ffmpeg, ffprobe)
    kich_ban_ep_verify_chet(ffmpeg, ffprobe)
    kich_ban_chan_ghi_de_goc(ffmpeg, ffprobe)
    print()
    print("=" * 72)
    print(f"KET QUA: {pas} PASS / {fail} FAIL")
    print("=" * 72)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
