#!/usr/bin/env python3
"""把子代理翻譯的 ui 批次（ja、ko）合併成 text/ui.<lang>.tsv，逐鍵核對。只在 Docker 內執行。

  python -B ui_merge_lang.py <text/ui.zh-TW.tsv> <批次輸出目錄> <lang> <輸出 text/ui.<lang>.tsv>

批次輸出檔 `ui-NN.<lang>.tsv`：每列「鍵 TAB 譯文」（鍵以 catalog 跳脫寫出），順序與批次檔 `ui-batch-NN.tsv` 相同。
依 zh-TW 的鍵集合核對：鍵不一致、缺鍵、多鍵一律報錯（子代理手抄鍵可能出錯，這是最後一道防線）。
沒有對應批次檔的鍵，譯文留空（草稿）。置中標記（\\c）沿用 zh-TW 的設定。
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalog_lib as cl  # noqa: E402


def main():
    zh_path, bdir, lang, out = sys.argv[1:5]
    zh = cl.read_tsv(zh_path)
    batch = {}
    problems = []
    for path in sorted(glob.glob(f"{bdir}/ui-[0-9][0-9].{lang}.tsv")):
        nn = os.path.basename(path).split(".")[0].split("-")[1]
        bpath = f"{bdir}/ui-batch-{nn}.tsv"
        keys = [l.rstrip("\n").split("\t")[0] for l in open(bpath, encoding="utf-8")]
        lines = [l.rstrip("\n") for l in open(path, encoding="utf-8")]
        if len(lines) != len(keys):
            problems.append(f"{path}: 行數 {len(lines)}，批次檔 {len(keys)}")
            continue
        for i, (k, line) in enumerate(zip(keys, lines), 1):
            parts = line.split("\t")
            if len(parts) != 2 or parts[0] != k:
                problems.append(f"{path}:{i}: 鍵不符：批次 {k!r}，輸出 {parts[0] if parts else ''!r}")
                continue
            batch[cl.unescape(k)] = cl.unescape(parts[1]).rstrip(" ")
    rows, missing = [], 0
    for _, key, tr, src in zh:
        t = batch.get(key.rstrip(" "), "") if key.rstrip(" ") in batch else batch.get(key, "")
        if not t:
            missing += 1
        elif tr.startswith(cl.CENTER):
            t = cl.CENTER + t
        rows.append((key, t, src))
    cl.write_tsv(out, rows)
    for p in problems:
        print("問題:", p)
    print(f"{len(rows)} 筆，已譯 {len(rows) - missing}，未譯 {missing}，問題 {len(problems)} → {out}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
