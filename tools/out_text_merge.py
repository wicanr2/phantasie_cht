#!/usr/bin/env python3
"""把 OUT*.DAT 的位置描述文字譯文併進 prose.<lang>.tsv（docs/spec/003 §12 第 6 項）。只在 Docker 內執行。

  python -B tools/out_text_merge.py <out-text.tsv> <譯文對照檔> <text/prose.<lang>.tsv>

out-text.tsv：tools/out_text.py 的輸出（檔名、位移、原文行）。
譯文對照檔：UTF-8，每行 `去頭尾空白的英文<TAB>譯文`（工作區檔案，含原版英文，不進版控）。
鍵：與 prose 一致，`h:` 加 sha256(原文行 rstrip)[:12]；原文行含開頭空白時整行不同鍵，所以同一句不同置中位置各自一列。
譯文：原文行開頭有空白（資料已置中）者加 \\c 前綴由版面置中，開頭沒有空白者靠左。
已存在的鍵不覆寫（譯文不同時報錯）。輸出依鍵排序。
"""
import hashlib
import sys

import catalog_lib as cl


def key_of(line):
    return "h:" + hashlib.sha256(line.rstrip().encode("utf-8")).hexdigest()[:12]


def main(out_text, mapfile, prose):
    tr = {}
    for n, line in enumerate(open(mapfile, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        cols = line.split("\t")
        if len(cols) != 2 or not cols[1].strip():
            sys.exit(f"{mapfile}:{n}: 要兩欄且譯文非空")
        if cols[0] in tr:
            sys.exit(f"{mapfile}:{n}: 英文重複 {cols[0]!r}")
        tr[cols[0]] = cols[1].strip()
    rows = {k: (t, s) for _, k, t, s in cl.read_tsv(prose)}
    added, missing = 0, set()
    for i, line in enumerate(open(out_text, encoding="utf-8")):
        if i == 0:
            continue
        f, off, text = line.rstrip("\n").split("\t")
        stripped = text.strip()
        if stripped not in tr:
            missing.add(stripped)
            continue
        key = key_of(text)
        t = tr[stripped]
        if text.startswith(" "):
            t = cl.CENTER + t
        if key in rows:
            if rows[key][0] != t:
                sys.exit(f"鍵 {key} 已有不同譯文：{rows[key][0]!r} 與 {t!r}")
            continue
        rows[key] = (t, f"out:{f}#{off}")
        added += 1
    if missing:
        sys.exit("譯文對照檔缺：\n  " + "\n  ".join(sorted(missing)))
    cl.write_tsv(prose, sorted((k, t, s) for k, (t, s) in rows.items()))
    print(f"新增 {added} 列；{prose} 共 {len(rows)} 列")


if __name__ == "__main__":
    main(*sys.argv[1:4])
