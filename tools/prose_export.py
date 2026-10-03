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
"""
import json
import os
import sys


def rstrip_nul(s: str) -> str:
    return s.replace("~", " ").rstrip()


def main():
    src, out = sys.argv[1], sys.argv[2]
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 25
    units = []
    for n in range(1, 11):
        for line in open(f"{src}/MESS{n}.msgs.tsv", encoding="utf-8"):
            f = line.rstrip("\n").split("\t")
            kind, idx, length, text, opt = f[0], f[1], f[2], f[3], (f[4] if len(f) > 4 else "")
            lines = [rstrip_nul(x) for x in text.split("|")]
            if not any(lines) or any("\\x" in l for l in lines):
                continue  # 空白行與流程標記（含控制字元，例如結束序列）不是文字
            units.append({"id": f"mess{n}:{idx}", "kind": kind, "len": int(length), "lines": lines,
                          "opt": rstrip_nul(opt) if opt else None})
    for line in open(f"{src}/SCROLLS.tsv", encoding="utf-8"):
        n, text = line.rstrip("\n").split("\t", 1)
        lines = [rstrip_nul(x) for x in text.split("|")]
        while lines and not lines[-1]:
            lines.pop()
        if lines:
            units.append({"id": f"scroll{n}", "kind": "scroll", "len": 0, "lines": lines, "opt": None})
    os.makedirs(f"{out}/batches", exist_ok=True)
    with open(f"{out}/prose-units.jsonl", "w", encoding="utf-8") as f:
        for u in units:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")
    # 卷軸每卷最多 20 行，單獨成批，其餘按單位數分批
    batches, cur = [], []
    for u in units:
        if u["kind"] == "scroll":
            batches.append([u])
            continue
        cur.append(u)
        if len(cur) >= per:
            batches.append(cur)
            cur = []
    if cur:
        batches.append(cur)
    for i, b in enumerate(batches, 1):
        with open(f"{out}/batches/batch-{i:03d}.jsonl", "w", encoding="utf-8") as f:
            for u in b:
                f.write(json.dumps(u, ensure_ascii=False) + "\n")
    lines_total = sum(len(u["lines"]) for u in units)
    print(f"{len(units)} 單位、{lines_total} 行、{len(batches)} 批")


if __name__ == "__main__":
    main()
