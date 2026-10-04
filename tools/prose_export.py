#!/usr/bin/env python3
"""把 MESS 與 SCROLLS 的列舉結果（tools/gamedata.py 的輸出）切成翻譯批次。只在 Docker 內執行。

  docker run --rm --network none -u "$(id -u):$(id -g)" \
    -v <workplace/mess>:/mess:ro -v <輸出目錄>:/out -v "$PWD/tools:/t:ro" \
    python:3.13-bookworm python -B /t/prose_export.py /mess /out [每批單位數]

輸出（原版英文，只寫 workplace/，不進版控）：
  /out/prose-units.jsonl      每單位一列：{"id", "kind", "lines":[英文行...], "opt": 選項原文或 null}
  /out/batches/batch-NNN.jsonl  同上分批，供子代理翻譯
單位 id：mess<N>:<索引>（訊息）、scroll<N>（卷軸）。行是 rstrip 後的 40 字元行，開頭空白保留。
全空白的單位不輸出。
短訊息預設略過；已實測的正文可加 --include-short mess5:61 納入（規格 009）。
"""
import json
import os
import sys
import argparse


def rstrip_nul(s: str) -> str:
    return s.replace("~", " ").rstrip()


def spaces(s: str):
    """原始行（NUL 視為空白）的開頭與尾端空白數，供置中判斷（docs/spec/003 §8）。"""
    raw = s.replace("~", " ")
    return len(raw) - len(raw.lstrip(" ")), len(raw) - len(raw.rstrip(" "))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("per", nargs="?", type=int, default=25)
    ap.add_argument("--include-short", action="append", default=[], metavar="ID",
                    help="明示納入已實測的短訊息 id，可重複；預設略過短訊息（009）")
    args = ap.parse_args()
    src, out, per = args.src, args.out, args.per
    if per < 1:
        ap.error("批次大小必須大於零")
    requested = set(args.include_short)
    encountered, invalid = set(), set()
    units = []
    for n in range(1, 11):
        for line in open(f"{src}/MESS{n}.msgs.tsv", encoding="utf-8"):
            f = line.rstrip("\n").split("\t")
            kind, idx, length, text, opt = f[0], f[1], f[2], f[3], (f[4] if len(f) > 4 else "")
            uid = f"mess{n}:{idx}"
            lines = [rstrip_nul(x) for x in text.split("|")]
            nontext = not any(lines) or any("\\x" in l or any(ord(c) < 0x20 or ord(c) > 0x7E for c in l) for l in lines)
            if uid in requested:
                encountered.add(uid)
                if kind != "short" or nontext or not 0 < int(length) < 40:
                    invalid.add(uid)
            if nontext:
                continue  # 空白行與流程標記（含控制字元，例如結束序列）不是文字
            if kind == "short" and uid not in requested:
                continue  # 只有明示的已實測短訊息才納入，其他分支仍待量測（009）
            unit = {"id": uid, "kind": kind, "len": int(length), "lines": lines, "opt": None, "opt_cells": [], "lead": [spaces(x)[0] for x in text.split("|")], "trail": [spaces(x)[1] for x in text.split("|")]}
            if opt:
                cnt, _, body = opt.partition(":")
                unit["opt"] = body
                unit["opt_cells"] = [c.rstrip() for c in body.split("|") if c.strip()]  # 開頭空白保留（003 §4）
            units.append(unit)
    if invalid or requested - encountered:
        ap.error("無效或不存在的短訊息 id：" + ", ".join(sorted(invalid | (requested - encountered))))
    for line in open(f"{src}/SCROLLS.tsv", encoding="utf-8"):
        n, text = line.rstrip("\n").split("\t", 1)
        lines = [rstrip_nul(x) for x in text.split("|")]
        while lines and not lines[-1]:
            lines.pop()
        if lines:
            raws = text.split("|")[:len(lines)]
            units.append({"id": f"scroll{n}", "kind": "scroll", "len": 0, "lines": lines, "opt": None, "opt_cells": [], "lead": [spaces(x)[0] for x in raws], "trail": [spaces(x)[1] for x in raws]})
    os.makedirs(f"{out}/batches", exist_ok=True)
    with open(f"{out}/prose-units.jsonl", "w", encoding="utf-8") as f:
        for u in units:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")
    # 卷軸每 4 卷成一批（每卷最多 20 行），訊息按單位數分批
    batches, cur, scrolls = [], [], []
    for u in units:
        if u["kind"] == "scroll":
            scrolls.append(u)
            if len(scrolls) == 4:
                batches.append(scrolls)
                scrolls = []
            continue
        cur.append(u)
        if len(cur) >= per:
            batches.append(cur)
            cur = []
    if cur:
        batches.append(cur)
    if scrolls:
        batches.append(scrolls)
    for i, b in enumerate(batches, 1):
        with open(f"{out}/batches/batch-{i:03d}.jsonl", "w", encoding="utf-8") as f:
            for u in b:
                f.write(json.dumps(u, ensure_ascii=False) + "\n")
    lines_total = sum(len(u["lines"]) for u in units)
    print(f"{len(units)} 單位、{lines_total} 行、{len(batches)} 批")


if __name__ == "__main__":
    main()
