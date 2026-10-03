#!/usr/bin/env python3
"""彙整 textlog 的繪字事件記錄，與靜態字串列舉對照。只在 Docker 內執行。

  docker run --rm --network none -u "$(id -u):$(id -g)" \
    -v <probe-out>:/in:ro -v <text-enum>:/enum:ro -v <輸出目錄>:/out -v "$PWD/tools:/t:ro" \
    python:3.13-bookworm python -B /t/harvest_events.py /out /in/mk1.log /in/mk2.log ...

輸入：textlog -args 的輸出（每行 `T step=.. r=.. c=.. caller=.. ov=.. fmtptr=.. fmt="..." text="..." args=[..]`）。
輸出（原版文字，只寫 workplace/，不進版控）：
  events.tsv   每個 (ov, caller, fmt) 一列：次數、類別、文字樣本、位置樣本
  texts.tsv    每個規範化文字（rstrip）一列：次數、類別、是否在靜態字串列舉
"""
import ast
import re
import sys
from collections import defaultdict

LINE = re.compile(
    r'^T step=(\d+) r=(\d+) c=(\d+) caller=([0-9A-F]+) ov=(\S+) fmtptr=([0-9A-F]+) '
    r'fmt=("(?:[^"\\]|\\.)*") text=("(?:[^"\\]|\\.)*")')


def unq(s):
    # textlog 以 Go 的 %q 輸出；\x.. 與 \u.... 都用 Python 的字串字面解析即可（單色字元範圍）
    return ast.literal_eval(s)


def classify(fmt: str, text: str) -> str:
    if text and all(ord(c) < 0x20 or ord(c) > 0x7E for c in text):
        return "ctrl"
    if any(ord(c) < 0x20 or ord(c) > 0x7E for c in text):
        return "mixed"
    if "%" not in fmt:
        return "lit"
    if re.fullmatch(r"(%[-0-9.]*l?[sdcu])+", fmt):
        return "fmtonly"
    return "tpl"


def main():
    out = sys.argv[1]
    logs = sys.argv[2:]
    events = defaultdict(lambda: {"n": 0, "text": "", "pos": ""})
    texts = defaultdict(lambda: {"n": 0, "cls": set()})
    for path in logs:
        for line in open(path, encoding="utf-8", errors="replace"):
            m = LINE.match(line)
            if not m:
                continue
            step, r, c, caller, ov, fmtptr, fmt, text = m.groups()
            fmt, text = unq(fmt), unq(text)
            cls = classify(fmt, text)
            e = events[(ov, caller, fmt)]
            e["n"] += 1
            e["cls"] = cls
            if not e["text"]:
                e["text"], e["pos"] = text, f"r{r}c{c}"
            if cls != "ctrl":
                t = texts[text.rstrip()]
                t["n"] += 1
                t["cls"].add(cls)
    static = set()
    try:
        for i, line in enumerate(open("/enum/strings.tsv", encoding="utf-8")):
            if i == 0:
                continue
            static.add(line.rstrip("\n").split("\t")[6].encode().decode("unicode_escape", errors="replace").rstrip())
    except FileNotFoundError:
        pass
    with open(f"{out}/events.tsv", "w", encoding="utf-8") as f:
        f.write("ov\tcaller\tcls\tcount\tpos\tfmt\ttext\n")
        for (ov, caller, fmt), e in sorted(events.items(), key=lambda kv: (kv[1]["cls"], kv[0])):
            f.write(f"{ov}\t{caller}\t{e['cls']}\t{e['n']}\t{e['pos']}\t{fmt!r}\t{e['text']!r}\n")
    with open(f"{out}/texts.tsv", "w", encoding="utf-8") as f:
        f.write("count\tcls\tin_static\ttext\n")
        for t, e in sorted(texts.items(), key=lambda kv: -kv[1]["n"]):
            f.write(f"{e['n']}\t{','.join(sorted(e['cls']))}\t{'Y' if t in static else 'N'}\t{t!r}\n")
    by = defaultdict(int)
    for e in events.values():
        by[e["cls"]] += 1
    print("events", len(events), dict(by))
    print("distinct texts", len(texts), "in static", sum(1 for t in texts if t in static))


if __name__ == "__main__":
    main()
