#!/usr/bin/env python3
"""ui 候選鍵的剔除清單（非顯示用字串、二進位誤判、手冊對照提示）。只在 Docker 內執行。

  python -B ui_prune.py <ui-candidates.tsv> <輸出 keys.txt> <輸出 pruned.tsv> <text/protected.tsv>

手冊對照提示（防拷題）維持原文，不進 catalog，也不翻譯（AGENTS.md §1）：鍵一律讀 protected.tsv，
不在此另維護一份（docs/spec/003 §9）；這裡只依特徵字串剔除，不分析其資料或答案。
"""
import sys

DROP = {
    ">Awd": "binary", "Xi": "binary", "ji": "binary", "mi": "binary", "n!wi": "binary",
    "0123456789abcdef": "table", ".ovr": "file", "DNG%-d": "file", "DNG%d": "file", "MESS%-d": "file",
    "OUT%-d.DAT": "file", "OUT%d.DAT": "file", "Too many args.": "runtime", "Error %d loading overlay: %s$": "runtime",
    "D SHEALTH REPORT:": "binary-prefix", "ibmcover": "file",
}

for i, line in enumerate(open(sys.argv[4], encoding="utf-8")):
    if i and line.strip():
        DROP[line.split("\t")[0].rstrip()] = "manual-lookup"

keys, pruned = [], []
for i, line in enumerate(open(sys.argv[1], encoding="utf-8")):
    if i == 0:
        continue
    k = line.split("\t")[0]
    if k in DROP:
        pruned.append((k, DROP[k]))
    else:
        keys.append(k)
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(keys) + "\n")
open(sys.argv[3], "w", encoding="utf-8").write("".join(f"{k}\t{why}\n" for k, why in pruned))
print(len(keys), "keys,", len(pruned), "pruned")
