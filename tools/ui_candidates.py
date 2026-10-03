#!/usr/bin/env python3
"""由 enumerate_text.py 的 strings.tsv（及 harvest 的 texts.tsv）產生 ui 家族的候選鍵清單。只在 Docker 內執行。

  docker run --rm --network none -u "$(id -u):$(id -g)" \
    -v <text-enum>:/enum:ro -v <harvest>:/harvest:ro -v <輸出目錄>:/out -v "$PWD/tools:/t:ro" \
    python:3.13-bookworm python -B /t/ui_candidates.py /enum /harvest /out

輸出 /out/ui-candidates.tsv（原版文字，只寫 workplace/，不進版控）：
  欄：key、kind（text、fmt）、regions、dyn_seen（動態收集看過 Y／N）、note
過濾：丟掉檔名、非英文的垃圾字串（資料區的二進位誤判）。結果仍需人工複核，這只是候選上界。
"""
import re
import sys

OK_CHARS = re.compile(r"^[A-Za-z0-9 .,:;!?'%+\-/*()#$@=<>&_\[\]]+$")
SHORT_OK = {"GP", "HP", "MP", "OK", "XP", "NO", "ON", "ID"}


def plausible(s: str) -> bool:
    t = s.strip()
    if len(t) < 2 or not OK_CHARS.match(s):
        return False
    letters = sum(c.isalpha() for c in t)
    if letters < 2:
        return False
    if t in SHORT_OK:
        return True
    # 二進位誤判的特徵：大小寫夾雜且無母音、符號比例高
    sym = sum(not (c.isalnum() or c == " ") for c in t)
    if sym * 2 > len(t) and "%" not in t:
        return False
    words = re.findall(r"[A-Za-z]+", t)
    has_vowel_word = any(re.search(r"[AEIOUaeiou]", w) and len(w) >= 2 for w in words)
    if not has_vowel_word and "%" not in t:
        return False
    mixed = any(w != w.upper() and w != w.lower() and w != w.capitalize() for w in words)
    return not mixed


def main():
    enum, harvest, out = sys.argv[1], sys.argv[2], sys.argv[3]
    seen = {}
    for i, line in enumerate(open(f"{enum}/strings.tsv", encoding="utf-8")):
        if i == 0:
            continue
        region, ds, ln, imm, dptr, kind, text = line.rstrip("\n").split("\t")
        if kind == "file":
            continue
        text = text.encode().decode("unicode_escape", errors="replace")
        key = text.rstrip()
        if not plausible(key):
            continue
        e = seen.setdefault(key, {"kind": kind, "regions": set()})
        e["regions"].add(region)
    dyn = set()
    try:
        for i, line in enumerate(open(f"{harvest}/texts.tsv", encoding="utf-8")):
            if i == 0:
                continue
            cnt, cls, in_static, text = line.rstrip("\n").split("\t", 3)
            dyn.add(eval(text))
    except FileNotFoundError:
        pass
    with open(f"{out}/ui-candidates.tsv", "w", encoding="utf-8") as f:
        f.write("key\tkind\tregions\tdyn_seen\tnote\n")
        for key in sorted(seen):
            e = seen[key]
            f.write(f"{key}\t{e['kind']}\t{','.join(sorted(e['regions']))}\t{'Y' if key in dyn else 'N'}\t\n")
    print(len(seen), "candidates")


if __name__ == "__main__":
    main()
