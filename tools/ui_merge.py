#!/usr/bin/env python3
"""把新增的 ui 鍵與譯文併入既有 ui.<lang>.tsv（依鍵排序，鍵不得重複）。只在 Docker 內執行。

  python -B ui_merge.py <ui.<lang>.tsv> <新增.tsv（鍵 TAB 譯文，無欄名）> <strings.tsv> [--dyn 鍵...]

source 欄由 strings.tsv（enumerate_text.py 的輸出）以文字查詢（<region>:<DS 偏移>，多筆以 ; 分隔）；
查不到者寫 dyn（動態出現的變體，例如選項開關符號的另一個極性，docs/spec/001 §4）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalog_lib as cl  # noqa: E402


def main():
    ui_path, add_path, strings_path = sys.argv[1:4]
    rows = [(k, tr, src) for _, k, tr, src in cl.read_tsv(ui_path)]
    have = {k for k, _, _ in rows}
    src = {}
    for i, line in enumerate(open(strings_path, encoding="utf-8")):
        if i == 0:
            continue
        region, ds, ln, imm, dptr, kind, text = line.rstrip("\n").split("\t")
        text = text.encode().decode("unicode_escape", errors="replace").rstrip()
        src.setdefault(text, []).append(f"{region}:{ds}")
    added = 0
    for line in open(add_path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            sys.exit(f"新增檔的列要是 鍵 TAB 譯文：{line!r}")
        k, tr = parts
        if k in have:
            sys.exit(f"鍵已存在：{k!r}")
        rows.append((k, tr, ";".join(dict.fromkeys(src.get(k, ["dyn"])))))
        have.add(k)
        added += 1
    rows.sort(key=lambda r: r[0])
    cl.write_tsv(ui_path, rows)
    print(f"新增 {added} 筆，共 {len(rows)} 筆 → {ui_path}")


if __name__ == "__main__":
    main()
