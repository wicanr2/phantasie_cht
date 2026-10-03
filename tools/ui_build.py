#!/usr/bin/env python3
"""由待譯鍵清單與對照譯文產生 text/ui.<lang>.tsv。只在 Docker 內執行。

  python -B ui_build.py <ui-keys.txt> <ui-zh-all.tsv> <strings.tsv> <輸出 ui.zh-TW.tsv>

ui-zh-all.tsv：每列「鍵 TAB 譯文」，行序必須與 ui-keys.txt 完全對應（鍵逐列核對，錯位就中止）。
strings.tsv（enumerate_text.py 的輸出）用來補 source 欄（<region>:<DS 偏移>，多筆以 ; 分隔）。
輸出依鍵排序。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalog_lib as cl  # noqa: E402


def main():
    keys_path, zh_path, strings_path, out = sys.argv[1:5]
    keys = [l.rstrip("\n") for l in open(keys_path, encoding="utf-8")]
    zh = [l.rstrip("\n") for l in open(zh_path, encoding="utf-8")]
    if len(keys) != len(zh):
        sys.exit(f"行數不同：鍵 {len(keys)}，譯文 {len(zh)}")
    src = {}
    for i, line in enumerate(open(strings_path, encoding="utf-8")):
        if i == 0:
            continue
        region, ds, ln, imm, dptr, kind, text = line.rstrip("\n").split("\t")
        text = text.encode().decode("unicode_escape", errors="replace").rstrip()
        src.setdefault(text, []).append(f"{region}:{ds}")
    rows = []
    for i, (k, line) in enumerate(zip(keys, zh), 1):
        parts = line.split("\t")
        if len(parts) != 2 or parts[0] != k:
            sys.exit(f"第 {i} 列的鍵不符：清單「{k}」，譯文檔「{parts[0] if parts else ''}」")
        rows.append((k, parts[1], ";".join(dict.fromkeys(src.get(k, ["dyn"])))))
    rows.sort(key=lambda r: r[0])
    cl.write_tsv(out, rows)
    print(len(rows), "筆 →", out)


if __name__ == "__main__":
    main()
