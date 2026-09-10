#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hook PostToolUse: sau khi Claude sua 1 file code (.py/.bat) trong project,
nhac Claude doc/cap nhat bug.md. Doc JSON tren stdin, in JSON ra stdout voi
hookSpecificOutput.additionalContext (chi nhac, KHONG chan).

Khong dung jq (may khong co) - dung Python thuan.
"""
import sys, json, os


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return  # khong parse duoc -> im lang, khong lam phien

    ti = data.get("tool_input", {}) or {}
    fp = ti.get("file_path") or ""
    resp = data.get("tool_response", {}) or {}
    fp = fp or resp.get("filePath") or ""
    if not fp:
        return

    low = fp.replace("\\", "/").lower()
    base = os.path.basename(low)

    # Chi nhac cho file code trong project; bo qua chinh bug.md / CLAUDE.md / file test tam
    if base in ("bug.md", "claude.md"):
        return
    if not (low.endswith(".py") or low.endswith(".bat")):
        return
    if "/scratchpad/" in low or "/temp/" in low or base.startswith("test_"):
        return

    msg = (
        "NHAC (bug.md): Ban vua sua file code trong project GOI PROJECT CAPCUT. "
        "Theo quy tac trong CLAUDE.md: (1) neu chua doc bug.md trong session nay, hay doc "
        "phan 'Checklist nhanh' de tranh tai pham loi cu (path UNC/long-path, nuot loi am tham, "
        "bao cao sai 'da xong', encoding .bat). (2) Neu thay doi nay LA de sua mot bug/loi, "
        "hay TU DONG them 1 muc moi vao bug.md (Trieu chung -> Nguyen nhan goc -> Cach sua -> "
        "Kiem chung -> Bai hoc). Neu chi la thay doi thuong (khong phai sua bug), bo qua nhac nay."
    )
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": msg,
        },
        "suppressOutput": True,
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
