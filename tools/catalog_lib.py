"""譯文 catalog 的共用函式：TSV 讀寫與跳脫、格式規格解析、寬度計算（docs/spec/003）。只在 Docker 內使用。"""
import re

# 003 §7：支援的轉換規格。旗標只有 -，寬度、精度、長度 l。
CONV = re.compile(r"%(?:(\d+)\$)?(-?)(0?)(\d*)(?:\.(\d+))?(l?)([sdcuxX%])")


def unescape(s: str) -> str:
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c != "\\":
            out.append(c)
            i += 1
            continue
        if i + 1 >= len(s):
            raise ValueError("尾端的反斜線")
        n = s[i + 1]
        if n == "t":
            out.append("\t")
            i += 2
        elif n == "\\":
            out.append("\\")
            i += 2
        elif n == "x" and i + 3 < len(s) + 1:
            out.append(chr(int(s[i + 2:i + 4], 16)))
            i += 4
        else:
            raise ValueError("不認得的跳脫 \\" + n)
    return "".join(out)


def escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("\t", "\\t")


def read_tsv(path: str):
    """回傳 [(key, translation, source)]；第一列是欄名。跳脫已還原，translation 的尾端空白已去除（003 §3）。"""
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        data = f.read()
    if data.startswith("﻿"):
        raise ValueError("檔案含 BOM")
    if "\r" in data:
        raise ValueError("檔案含 CR（要 LF）")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    for n, line in enumerate(lines):
        if n == 0:
            if line.split("\t") != ["key", "translation", "source"]:
                raise ValueError("第一列欄名要是 key、translation、source")
            continue
        cols = line.split("\t")
        if len(cols) != 3:
            raise ValueError(f"第 {n + 1} 列欄數是 {len(cols)}，要 3")
        rows.append((n + 1, unescape(cols[0]), unescape(cols[1]).rstrip(" "), cols[2]))
    return rows


def write_tsv(path: str, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("key\ttranslation\tsource\n")
        for key, tr, src in rows:
            f.write(f"{escape(key)}\t{escape(tr.rstrip(' '))}\t{src}\n")


def convs(fmt: str):
    """格式字串內的轉換序（不含 %%）：[(位置, 旗標-, 零, 寬度, 精度, l, 類型)]；位置為 None 代表依序。"""
    out = []
    for m in CONV.finditer(fmt):
        if m.group(7) == "%":
            continue
        out.append((m.group(1), m.group(2) == "-", m.group(3) == "0", int(m.group(4)) if m.group(4) else 0,
                    int(m.group(5)) if m.group(5) is not None else None, m.group(6) == "l", m.group(7)))
    return out


def has_bad_percent(fmt: str) -> bool:
    """有 % 但不是支援的規格（尾端 %、%x 以外的規格等）。"""
    rest = CONV.sub("", fmt)
    return "%" in rest


def wide(r: str) -> bool:
    c = ord(r)
    return c >= 0x2E80 or 0xFF00 <= c <= 0xFFEF


def width_h(s: str) -> int:
    """半格寬度（h）：全形 2、其他 1。"""
    return sum(2 if wide(c) else 1 for c in s)


NUM_MAX = {("d", False): "-32768", ("u", False): "65535", ("d", True): "-2147483648", ("u", True): "4294967295",
           ("x", False): "FFFF", ("X", False): "FFFF"}


def sample_format(tpl: str, samples):
    """以樣本引數格式化模板，回傳 h 寬度。samples：依序給 %s 用的字串（不足以 'X' 重複寬度補），數字用最大位數。
    寬度與精度以「格」為單位（1 格 = 2 h）。"""
    out_h = 0
    pos = 0
    si = 0
    for m in CONV.finditer(tpl):
        out_h += width_h(tpl[pos:m.start()].replace("%%", "%"))
        pos = m.end()
        if m.group(7) == "%":
            out_h += 1
            continue
        left, zero, width, prec, ll, conv = m.group(2) == "-", m.group(3) == "0", int(m.group(4) or 0), m.group(5), m.group(6) == "l", m.group(7)
        if conv == "s":
            s = samples[si] if si < len(samples) else "X" * (int(prec) if prec is not None else (width or 8))
            si += 1
            if prec is not None:
                keep, acc = [], 0
                for ch in s:
                    w = 2 if wide(ch) else 1
                    if acc + w > 2 * int(prec):
                        break
                    keep.append(ch)
                    acc += w
                s = "".join(keep)
            h = width_h(s)
        elif conv == "c":
            h = 1
            si += 1
        else:
            digits = NUM_MAX.get((conv, ll), "65535")
            h = len(digits)
            if prec is not None:
                h = max(h, int(prec))
        out_h += max(h, 2 * width)
    out_h += width_h(tpl[pos:].replace("%%", "%"))
    return out_h


def english_cells(key: str) -> int:
    """原文格式化寬度（格）：原版每個字元一格。字面字元數加各轉換的欄位寬度（無寬度時用樣本長度：%s 8、數字最大位數）。"""
    total, pos = 0, 0
    for m in CONV.finditer(key):
        total += len(key[pos:m.start()])
        pos = m.end()
        if m.group(7) == "%":
            total += 1
            continue
        width = int(m.group(4) or 0)
        prec = m.group(5)
        conv, ll = m.group(7), m.group(6) == "l"
        if conv == "s":
            n = int(prec) if prec is not None else 8
        elif conv == "c":
            n = 1
        else:
            n = len(NUM_MAX.get((conv, ll), "65535"))
            if prec is not None:
                n = max(n, int(prec))
        total += max(n, width)
    return total + len(key[pos:])
