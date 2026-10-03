#!/usr/bin/env python3
"""共用測試向量（tests/vectors/*.tsv）的 Python 端（docs/spec/003 §7.3、§13）。只在 Docker 內執行。

  docker run --rm --network none -u "$(id -u):$(id -g)" -v "$PWD:/p:ro" python:3.13-bookworm \
    python -B /p/tools/tests/run_vectors.py /p/tests/vectors

向量檔內 `_` 代表一個半形空白（引數與期望值都適用）；期望值以 [ ] 包住以保留首尾空白。
Go 端（apps/phantasie 的 format 測試）讀同一批檔案，期望值是字面值，不以另一個語言的輸出當期望。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import catalog_lib as cl  # noqa: E402


def rows(path):
    out = []
    for i, line in enumerate(open(path, encoding="utf-8")):
        if i == 0:
            continue
        out.append(line.rstrip("\n").split("\t"))
    return out


def sp(s):
    return s.replace("_", " ")


def parse_args(token, target):
    args = []
    for t in token.split("|") if token else []:
        kind, _, val = t.partition(":")
        if kind == "w":
            args.append(int(val, 16))
        elif kind == "s":
            args.append(("s", sp(val)) if target else sp(val))
        elif kind == "t":
            args.append(("t", sp(val)))
        else:
            raise SystemExit(f"不認得的引數 {t!r}")
    return args


def conv_text(c):
    _, left, width, prec, ll, conv = c
    return ("-" if left else "") + (str(width) if width else "") + ("." + str(prec) if prec is not None else "") + \
        ("l" if ll else "") + conv


def main():
    d = sys.argv[1]
    fails = n = 0

    def check(name, got, want):
        nonlocal fails, n
        n += 1
        if got != want:
            fails += 1
            print(f"失敗 {name}: 得 {got!r}，要 {want!r}")

    for fmt, expect in rows(f"{d}/parse.tsv"):
        try:
            got = ",".join(conv_text(s) for s in cl.parse_fmt(fmt) if s[0] == "conv") or "(none)"
        except ValueError:
            got = "ERR"
        check(f"parse {fmt!r}", got, expect)
    for fmt, args, expect in rows(f"{d}/english.tsv"):
        got = "[" + cl.format_english(fmt, parse_args(args, False)).replace(" ", "_") + "]"
        check(f"english {fmt!r} {args!r}", got, expect)
    for tpl, args, expect, h in rows(f"{d}/target.tsv"):
        s = cl.format_target(tpl, parse_args(args, True))
        check(f"target {tpl!r} {args!r}", "[" + s.replace(" ", "_") + "]", expect)
        check(f"target 寬度 {tpl!r} {args!r}", cl.width_h(s), int(h))
    print(f"{n} 項，失敗 {fails}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
