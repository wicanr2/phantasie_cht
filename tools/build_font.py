#!/usr/bin/env python3
"""由 GNU Unifont 的 hex 檔建立 GOLEMFNT 字型子集（只在 Docker 內執行）。

GOLEMFNT：magic「GOLEMFNT」、u16 W、u16 H、u32 字數（小端），之後每字 u32 碼點、
u8 來源、H×((W+7)/8) bytes 字模（MSB 在左）。這裡 W=H=16；Unifont 的 8×16 半形字
放在每列第一個 byte，第二個 byte 為 0。

用法：
  build_font.py --tar unifont.tar.gz --member unifont-17.0.05/font/precompiled/unifont_t-17.0.05.hex \
      --chars text/ui.zh-TW.tsv --out font.golemfnt

--chars 可重複給；TSV 取 translation 欄，其餘檔案整個當字元清單。ASCII 0x20 至 0x7E 一律收。
缺任何一個要求的字就以非零離開，不為遷就缺字而改譯文。
"""
import argparse
import csv
import hashlib
import struct
import sys
import tarfile

SOURCE_UNIFONT = 1


def read_hex(data):
    glyphs = {}
    for line in data.decode("ascii").splitlines():
        if not line or ":" not in line:
            continue
        code, bits = line.split(":", 1)
        cp = int(code, 16)
        raw = bytes.fromhex(bits)
        if len(raw) == 16:  # 8×16 半形
            glyphs[cp] = b"".join(bytes([b, 0]) for b in raw)
        elif len(raw) == 32:  # 16×16 全形
            glyphs[cp] = raw
        else:
            raise SystemExit("U+%04X 的字模長度 %d 不是 16 或 32" % (cp, len(raw)))
    return glyphs


def wanted_chars(paths):
    chars = {chr(c) for c in range(0x20, 0x7F)}
    for p in paths:
        with open(p, encoding="utf-8", newline="") as f:
            if p.endswith(".tsv"):
                rows = csv.reader(f, delimiter="\t")
                header = next(rows)
                col = header.index("translation")
                for r in rows:
                    if len(r) > col:
                        chars.update(r[col])
            else:
                chars.update(f.read())
    chars.discard("\n")
    chars.discard("\r")
    chars.discard("\t")
    return chars


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tar", required=True)
    ap.add_argument("--member", required=True)
    ap.add_argument("--chars", action="append", default=[])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with tarfile.open(a.tar) as t:
        src = t.extractfile(a.member).read()
    glyphs = read_hex(src)
    want = wanted_chars(a.chars)
    missing = sorted(c for c in want if ord(c) not in glyphs)
    if missing:
        print("缺字：" + "".join(missing), file=sys.stderr)
        sys.exit(1)
    cps = sorted(ord(c) for c in want)
    out = bytearray(b"GOLEMFNT" + struct.pack("<HHI", 16, 16, len(cps)))
    for cp in cps:
        out += struct.pack("<IB", cp, SOURCE_UNIFONT) + glyphs[cp]
    with open(a.out, "wb") as f:
        f.write(out)
    print("字數 %d，sha256 %s，來源 sha256 %s" % (
        len(cps), hashlib.sha256(out).hexdigest(), hashlib.sha256(src).hexdigest()))


main()
