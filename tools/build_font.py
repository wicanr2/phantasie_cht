#!/usr/bin/env python3
"""由 GNU Unifont 的 hex 檔建立 GOLEMFNT 字型子集（只在 Docker 內執行）。

GOLEMFNT：magic「GOLEMFNT」、u16 W、u16 H、u32 字數（小端），之後每字 u32 碼點、
u8 來源、H×((W+7)/8) bytes 字模（MSB 在左）。這裡 W=H=16；Unifont 的 8×16 半形字
放在每列第一個 byte，第二個 byte 為 0。

來源位元組：bit 7 為 1 表示該字是全形（16 px 寬），低 7 位元是來源編號（Unifont = 1）。
`xlate.ParseFont` 不解讀該位元組，adapter 以自己的檔頭解析讀出 wide 表（docs/spec/004 §3）。

用法：
  build_font.py --tar unifont.tar.gz --member unifont-17.0.05/font/precompiled/unifont_t-17.0.05.hex \
      --chars text/ui.zh-TW.tsv --chars text/prose.zh-TW.tsv --chars font/zh-TW.extra.txt --out font.golemfnt

--chars 可重複給；.tsv 以 catalog_lib 讀取，取 translation 欄（去掉 \\c 標記），其餘檔案整個當字元清單。
ASCII 0x20 至 0x7E 一律收。缺任何一個要求的字就以非零離開，不為遷就缺字而改譯文。
"""
import argparse
import hashlib
import os
import struct
import sys
import tarfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalog_lib as cl  # noqa: E402

SOURCE_UNIFONT = 1
WIDE_BIT = 0x80


def read_hex(data):
    """回傳 ({碼點: 16×16 位元圖}, {全形碼點集合})。"""
    glyphs, wide = {}, set()
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
            wide.add(cp)
        else:
            raise SystemExit("U+%04X 的字模長度 %d 不是 16 或 32" % (cp, len(raw)))
    return glyphs, wide


def wanted_chars(paths):
    chars = {chr(c) for c in range(0x20, 0x7F)}
    for p in paths:
        if p.endswith(".tsv"):
            for _, _, tr, _ in cl.read_tsv(p):
                chars.update(tr.replace(cl.CENTER, ""))
        else:
            with open(p, encoding="utf-8", newline="") as f:
                chars.update(f.read())
    for c in "\n\r\t":
        chars.discard(c)
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
    glyphs, wide = read_hex(src)
    want = wanted_chars(a.chars)
    missing = sorted(c for c in want if ord(c) not in glyphs)
    if missing:
        print("缺字：" + "".join(missing), file=sys.stderr)
        sys.exit(1)
    cps = sorted(ord(c) for c in want)
    out = bytearray(b"GOLEMFNT" + struct.pack("<HHI", 16, 16, len(cps)))
    for cp in cps:
        out += struct.pack("<IB", cp, SOURCE_UNIFONT | (WIDE_BIT if cp in wide else 0)) + glyphs[cp]
    with open(a.out, "wb") as f:
        f.write(out)
    print("字數 %d（全形 %d），sha256 %s，來源 sha256 %s" % (
        len(cps), sum(1 for c in cps if c in wide), hashlib.sha256(out).hexdigest(), hashlib.sha256(src).hexdigest()))


main()
