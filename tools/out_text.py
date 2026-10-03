#!/usr/bin/env python3
"""擷取 OUT*.DAT 內的位置描述文字（docs/spec/003 §12 第 6 項：第三種文字來源）。只在 Docker 內執行。

  python -B tools/out_text.py <原版目錄> [--tsv 輸出檔]

每個 OUT*.DAT 是 1024 bytes：前段是地圖資料，後段是 40 bytes 一筆的描述行（39 個可印字元加 NUL，兩側以空白置中）。
輸出每筆的檔名、檔內位移與文字。位移用來推算執行期位址：讀進 DS 緩衝區的起點由動態收據決定（見 docs/re/010）。
"""
import argparse
import glob
import os
import re
import sys

LINE = re.compile(rb"[\x20-\x7E]{39}\x00")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--tsv")
    a = ap.parse_args()
    rows = []
    for path in sorted(glob.glob(os.path.join(a.root, "OUT*.DAT")), key=lambda p: int(re.search(r"OUT(\d+)", p).group(1))):
        data = open(path, "rb").read()
        name = os.path.basename(path)
        for m in LINE.finditer(data):
            text = m.group(0)[:39].decode("ascii")
            if len(re.findall(r"[A-Z]", text)) < 3 or " " not in text.strip():
                if len(re.findall(r"[A-Z]", text)) < 3:
                    continue
            rows.append((name, m.start(), text))
    out = open(a.tsv, "w", encoding="utf-8") if a.tsv else sys.stdout
    print("file\toffset\ttext", file=out)
    for name, off, text in rows:
        print(f"{name}\t{off}\t{text}", file=out)
    uniq = {t.rstrip() for _, _, t in rows}
    print(f"# {len(rows)} 行，相異 {len(uniq)}", file=sys.stderr)


if __name__ == "__main__":
    main()
