#!/usr/bin/env python3
"""調整 ui 模板譯文中各欄位的寬度，使右緣對齊原文（docs/spec/003 §7.2、§10 的「欄位右緣」警告）。只在 Docker 內執行。

  python -B ui_align.py <ui.<lang>.tsv> [--font-tar T --font-member M] [--apply]

只動「原文有明寫寬度、且其後還有內容」的欄位；類型、旗標、精度與順序不變，只改寬度（原版的格，1 格 = 2 h）。
預設只印出建議，--apply 才改寫檔案。寬度取使右緣最接近原文者（四捨五入到整格，誤差至多 1 h）；
欄位寬度不得小於該欄內容的最小需要（精度所限的內容寬度）。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalog_lib as cl  # noqa: E402


def content_h(left, width, prec, ll, conv):
    """目標語言該欄內容的樣本寬度（h）：%s 取精度所限的 'X' 串（無精度取寬度或 8），數字取最大位數（有精度取精度）。"""
    if conv == "s":
        n = prec if prec is not None else (width or 8)
        return n
    if conv == "c":
        return 1
    n = len(cl.NUM_MAX.get((conv, ll), "65535"))
    return min(n, prec) if prec is not None else n


def align(key: str, tr: str):
    flag = ""
    if tr.startswith(cl.CENTER):
        flag, tr = cl.CENTER, tr[1:]
    en = cl.field_right_edges(key, [], True)
    key_convs = cl.convs(key)
    segs = cl.parse_fmt(tr)
    out, cur, ci = [], 0, 0
    for seg in segs:
        if seg[0] == "lit":
            cur += cl.width_h(seg[1])
            out.append(seg[1].replace("%", "%%"))
            continue
        _, left, width, prec, ll, conv = seg
        edge_en, adjust = en[ci] if ci < len(en) else (0, False)
        ci += 1
        need = content_h(left, width, prec, ll, conv)
        if width:
            need = min(need, 2 * width)  # 與 field_right_edges 相同：有明寫寬度時內容放得進欄位
        new_w = width
        if adjust:
            desired = edge_en - cur
            new_w = max(1, round(desired / 2))
            if 2 * new_w < need:
                new_w = -(-need // 2)
        cur += max(need, 2 * new_w)
        out.append("%" + ("-" if left else "") + (str(new_w) if new_w else "") +
                   ("." + str(prec) if prec is not None else "") + ("l" if ll else "") + conv)
    return flag + "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ui")
    ap.add_argument("--font-tar")
    ap.add_argument("--font-member")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if a.font_tar:
        cl.load_wide_from_hex(a.font_tar, a.font_member)
    rows, changed = [], 0
    for ln, key, tr, src in cl.read_tsv(a.ui):
        if tr and tr != "<blank>" and cl.convs(key) and not cl.has_bad_percent(key) and not cl.has_bad_percent(tr):
            new = align(key, tr)
            if new != tr:
                changed += 1
                print(f"{ln}: {key!r}\n    {tr!r}\n -> {new!r}")
                tr = new
        rows.append((key, tr, src))
    print(f"調整 {changed} 筆")
    if a.apply:
        cl.write_tsv(a.ui, rows)


if __name__ == "__main__":
    main()
