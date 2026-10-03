#!/usr/bin/env python3
"""譯文 catalog 的 lint（docs/spec/003 §9）。只在 Docker 內執行。

  python -B lint_catalog.py [--release] [--glossary text/glossary.tsv] \
      [--font-tar unifont.tar.gz --font-member unifont-17.0.05/font/precompiled/unifont_t-17.0.05.hex] \
      text/ui.zh-TW.tsv [text/prose.zh-TW.tsv ...]

違規印出並以非零離開。空譯文在草稿模式只計數，--release 才是錯誤。
"""
import argparse
import os
import re
import sys
import tarfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalog_lib as cl  # noqa: E402


def font_codepoints(tar_path, member):
    cps = set(range(0x20, 0x7F))
    t = tarfile.open(tar_path)
    for line in t.extractfile(member).read().decode().splitlines():
        if ":" in line:
            cps.add(int(line.split(":", 1)[0], 16))
    return cps


def conv_sig(s):
    """轉換序的簽章：類型（含 l）依序；位置語法 %n$ 重排後依原順序。"""
    items = []
    for i, (pos, left, zero, width, prec, ll, conv) in enumerate(cl.convs(s)):
        items.append((int(pos) if pos else i + 1, ("l" if ll else "") + conv))
    items.sort()
    return [t for _, t in items]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--release", action="store_true")
    ap.add_argument("--glossary")
    ap.add_argument("--font-tar")
    ap.add_argument("--font-member")
    a = ap.parse_args()
    errors, warns = [], []
    cps = font_codepoints(a.font_tar, a.font_member) if a.font_tar else None
    glossary = []
    if a.glossary:
        for i, line in enumerate(open(a.glossary, encoding="utf-8")):
            if i == 0 or not line.strip():
                continue
            c = line.rstrip("\n").split("\t")
            glossary.append((c[0], c[1]))
    seen = {}
    empty = 0
    total = 0
    for path in a.files:
        try:
            rows = cl.read_tsv(path)
        except ValueError as e:
            errors.append(f"{path}: {e}")
            continue
        for ln, key, tr, src in rows:
            total += 1
            where = f"{path}:{ln}"
            if not key:
                errors.append(f"{where}: 鍵是空的")
                continue
            if key in seen:
                errors.append(f"{where}: 鍵重複（另一筆在 {seen[key]}）")
            seen[key] = where
            if not tr:
                empty += 1
                continue
            if any(ord(c) < 0x20 for c in tr):
                errors.append(f"{where}: 譯文含控制字元")
            if cl.has_bad_percent(key) or cl.has_bad_percent(tr):
                errors.append(f"{where}: 含不支援的轉換規格")
                continue
            if conv_sig(key) != conv_sig(tr):
                errors.append(f"{where}: 轉換序不一致 原 {conv_sig(key)} 譯 {conv_sig(tr)}")
            if cps is not None:
                for ch in sorted(set(tr)):
                    if ch not in " " and ord(ch) not in cps:
                        errors.append(f"{where}: 字型缺字 U+{ord(ch):04X} {ch}")
            # 寬度：譯文的半格寬度不超過原文格數的兩倍
            if not key.startswith("h:"):
                en = cl.english_cells(key)
                zh_h = cl.sample_format(tr, []) if cl.convs(tr) else cl.width_h(tr)
                if zh_h > 2 * en:
                    errors.append(f"{where}: 寬度超出 譯文 {zh_h}h > 原文 {en} 格（{2 * en}h）")
            # 術語
            if glossary and not key.startswith("h:"):
                for en_term, zh_term in glossary:
                    if re.search(r"(?<![A-Za-z])" + re.escape(en_term) + r"(?![A-Za-z])", key, re.I) and zh_term not in tr:
                        errors.append(f"{where}: 術語 {en_term} 應含「{zh_term}」")
    if empty:
        (errors if a.release else warns).append(f"空譯文 {empty} 筆")
    for w in warns:
        print("警告:", w)
    for e in errors:
        print("錯誤:", e)
    print(f"共 {total} 筆，錯誤 {len(errors)}，警告 {len(warns)}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
