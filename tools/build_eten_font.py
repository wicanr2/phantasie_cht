#!/usr/bin/env python3
"""014：由固定本機倚天來源替換繁中全形字；僅在 Docker 執行。"""
import argparse
import json
from pathlib import Path
import struct

import package_files as pf

SOURCES = {
    "STDFONT.15": (392820, "39ba9c8519d75fe11d5988a8a27e6daa5794ad2ea215108390b0d7e9e53ff701"),
    "SPCFONT.15": (12240, "f32049ba2a7a21db908878a488a2c1d93c389d17398cf46db1390ba89e247605"),
}


def raw_index(code):
    hi, lo = code >> 8, code & 255
    if not (0x40 <= lo <= 0x7E or 0xA1 <= lo <= 0xFE):
        raise ValueError("倚天 Big5 尾碼無效")
    return (hi - 0xA1) * 157 + (lo - 0x40 if lo < 0x7F else lo - 0x62)


def location(code):
    index = raw_index(code)
    if 0xA140 <= code <= 0xA3BF:
        return "SPCFONT.15", index
    if 0xA440 <= code <= 0xC67E:
        return "STDFONT.15", index - raw_index(0xA440)
    if 0xC940 <= code <= 0xF9D5:
        return "STDFONT.15", 5401 + index - raw_index(0xC940)
    raise ValueError("倚天 Big5 空隙、擴充或超界")


def glyph(cp, sources):
    try:
        encoded = b"\xa1\xe3" if cp == 0xFF5E else chr(cp).encode("big5")
    except UnicodeEncodeError:
        raise ValueError("必要字元無倚天 Big5 對應") from None
    if len(encoded) != 2:
        raise ValueError("必要全形字元無兩碼 Big5 對應")
    name, index = location(int.from_bytes(encoded, "big"))
    bitmap = sources[name][index * 30:(index + 1) * 30]
    if len(bitmap) != 30:
        raise ValueError("倚天字模越界")
    return bitmap + b"\0\0"


def base_records(data):
    pf.font_coverage(data, set(range(32, 127)))
    result = []
    for offset in range(16, len(data), 37):
        cp, source = struct.unpack_from("<IB", data, offset)
        if (32 <= cp <= 126 and source != 1) or (not 32 <= cp <= 126 and (cp < 128 or source != 0x81)):
            raise ValueError("繁中基準須為 95 個 GNU ASCII 半形及其餘全形")
        result.append((cp, data[offset:offset + 37]))
    return result


def build(eten_dir, base_font, output):
    root = pf.directory(eten_dir)
    base_font, output = pf.no_links(base_font), pf.no_links(output)
    data = pf.file_bytes(base_font)
    records = base_records(data)
    if output.exists() or not output.parent.is_dir():
        raise ValueError("倚天輸出須為新檔且父目錄已存在")
    sources = {}
    source_records = {}
    for name, expected in SOURCES.items():
        raw = pf.file_bytes(root / name)
        if (len(raw), pf.digest(raw)) != expected:
            raise ValueError("倚天固定來源大小或 SHA-256 不符")
        sources[name] = raw
        source_records[name] = {"bytes": len(raw), "sha256": pf.digest(raw)}
    converted = bytearray(data[:16])
    for cp, row in records:
        converted += row if 32 <= cp <= 126 else struct.pack("<IB", cp, 0x82) + glyph(cp, sources)
    stream = output.open("xb")
    try:
        with stream:
            stream.write(converted)
    except BaseException:
        output.unlink()
        raise
    return {"schema": 1, "scope": "local-only ETEN fullwidth; GNU ASCII retains selected terms",
            "glyphs": len(records), "eten_fullwidth": len(records) - 95, "gnu_ascii": 95,
            "source_height": 15, "canvas": [16, 16], "sources": source_records,
            "base_font_sha256": pf.digest(data), "sha256": pf.digest(converted)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("eten-dir", "base-font", "out"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    try:
        result = build(args.eten_dir, args.base_font, args.out)
    except (OSError, ValueError, UnicodeError, struct.error) as error:
        parser.exit(1, f"倚天字型建置失敗：{error}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
