#!/usr/bin/env python3
"""擷取 OUT*.DAT 內的位置描述文字（docs/spec/003 §12 第 6 項、docs/re/010）。只在 Docker 內執行。

  python -B tools/out_text.py <原版目錄> [--tsv 輸出檔]

每個 OUT*.DAT 是 1024 bytes：前段是地圖資料，偏移 595 起是 7 個 40 bytes 的槽，遊戲以「槽起點的指標」把 NUL 結尾字串
交給 25A5（`%s`，最多畫 40 字元）。字串左右常以空白置中，部分檔案以 0Dh 等控制字元當空白（FONT 的 09h 至 0Eh 等字模全空，
畫出來就是空白）。本工具依 FONT 的空白字模把這類控制字元視為空格後取字串。

輸出：檔名、槽偏移、正規化後的字串（控制空白換成空格）。不含大寫字母三個以上、或含非空白字模的控制字元的槽略過並列在 stderr。
"""
import argparse
import glob
import os
import re
import sys

SLOT0, SLOT = 595, 40


def blank_ctl(font):
    """FONT 內字模全 0 的控制字元（1 至 31）。"""
    return {g for g in range(1, 32) if not any(font[g * 16:g * 16 + 16])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--tsv")
    a = ap.parse_args()
    font = open(os.path.join(a.root, "FONT"), "rb").read()
    blanks = blank_ctl(font)
    rows, skipped = [], []
    for path in sorted(glob.glob(os.path.join(a.root, "OUT*.DAT")), key=lambda p: int(re.search(r"OUT(\d+)", p).group(1))):
        data = open(path, "rb").read()
        name = os.path.basename(path)
        for off in range(SLOT0, min(len(data), SLOT0 + 7 * SLOT), SLOT):
            raw = data[off:off + SLOT]
            end = raw.find(b"\x00")
            raw = raw if end < 0 else raw[:end]
            text = bytes(0x20 if b in blanks else b for b in raw)
            if any(b < 0x20 or b > 0x7E for b in text):
                if len(re.findall(rb"[A-Z]", text)) >= 3:
                    skipped.append((name, off, raw))
                continue
            s = text.decode("ascii")
            if len(re.findall(r"[A-Z]", s)) < 3:
                continue
            if "ENDING SEQUENCE" in s:  # 原版資料瑕疵：描述行被其他字串覆寫一半（docs/re/010），保持原文不譯
                skipped.append((name, off, raw))
                continue
            rows.append((name, off, s))
    out = open(a.tsv, "w", encoding="utf-8") if a.tsv else sys.stdout
    print("file\toffset\ttext", file=out)
    for name, off, text in rows:
        print(f"{name}\t{off}\t{text}", file=out)
    uniq = {t.rstrip() for _, _, t in rows}
    print(f"# {len(rows)} 行，相異 {len(uniq)}；略過 {len(skipped)}", file=sys.stderr)
    for name, off, raw in skipped:
        print(f"# 略過 {name}#{off}: {raw!r}", file=sys.stderr)


if __name__ == "__main__":
    main()
