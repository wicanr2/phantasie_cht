#!/usr/bin/env python3
"""MESSn 與 SCROLLS.DTX 的解碼與列舉（只讀原版檔，輸出到指定目錄）。

格式與證據見 docs/re/007-message-and-scroll-formats.md。需在 Docker 內執行：

  docker run --rm --network none -u "$(id -u):$(id -g)" \
    -v <原版目錄>:/o:ro -v <輸出目錄>:/out -v "$PWD/tools:/t:ro" \
    python:3.13-bookworm python -B /t/gamedata.py /o /out

輸出（都是原版文字，只寫進 workplace/，不進版控）：
  MESSn.msgs.tsv  每則訊息一列：索引、總長 L、行（以 | 連接）、選項
  SCROLLS.tsv     每卷一列：卷號、行（以 | 連接）
"""
import struct
import sys

HEADER = 230          # 偏移表 112 個字組 + 6 bytes 標記；訊息記錄從 0x65EC - 0x6506 起
TABLE_WORDS = 112
CHUNK = 41            # 1 byte 長度或選項數 + 40 bytes 文字


def decode_mess(raw: bytes, n: int) -> bytes:
    """OV2 sub_8382：buf[i] = buf[i] + key；key = 3n+1，之後 key = key*33 + 31 (mod 256)。只作用於實際讀到的位元組。"""
    key = 3 * n + 1
    out = bytearray()
    for c in raw[:4000]:
        out.append((c + key) & 0xFF)
        key = (key * 33 + 0x1F) & 0xFF
    return bytes(out)


def decode_scroll(raw: bytes, n: int) -> bytes:
    """常駐 sub_2B9C 與 sub_2BF8：每卷 800 bytes，buf[i] -= ((i & 0x7F) * (4n+9) + 0x0D) & 0x7F。"""
    key = n * 4 + 9
    return bytes((raw[i] - (((i & 0x7F) * key + 0x0D) & 0x7F)) & 0xFF for i in range(len(raw)))


def chunk_at(dec: bytes, table, idx):
    """sub_88F4：索引 idx（1 起算）。表項相同代表沒有這則；否則回傳 (第一個 byte, 40 bytes 文字)。"""
    if idx < 1 or idx >= TABLE_WORDS:
        return None
    if table[idx - 1] == table[idx]:
        return None
    off = HEADER + table[idx - 1]
    rec = dec[off:off + CHUNK]
    if len(rec) < CHUNK:
        rec = rec + b"\x00" * (CHUNK - len(rec))
    return rec[0], rec[1:CHUNK]


def parse_mess(dec: bytes):
    table = struct.unpack_from("<%dH" % TABLE_WORDS, dec, 0)
    msgs = []
    idx = 1
    while idx < TABLE_WORDS:
        c = chunk_at(dec, table, idx)
        if c is None:
            idx += 1
            continue
        length, text = c
        lines = [text]
        nxt = idx + 1
        # sub_8F71：每 40 個字元讀下一個索引
        for _ in range(max(0, (length + 39) // 40 - 1)):
            c2 = chunk_at(dec, table, nxt)
            if c2 is None:
                break
            lines.append(c2[1])
            nxt += 1
        options = None
        if length == 40:
            c3 = chunk_at(dec, table, nxt)
            if c3 is not None and 2 <= c3[0] <= 20:
                options = (c3[0], c3[1])
                nxt += 1
        msgs.append((idx, length, lines, options))
        idx = nxt
    return msgs


def show(b: bytes) -> str:
    return b.decode("latin-1").replace("\x00", "~").replace("\t", " ").replace("\n", " ")


def main():
    src, out = sys.argv[1], sys.argv[2]
    total_msgs = total_chars = 0
    for n in range(1, 11):
        raw = open(f"{src}/phantasi/MESS{n}", "rb").read()
        dec = decode_mess(raw, n)
        msgs = parse_mess(dec)
        with open(f"{out}/MESS{n}.msgs.tsv", "w", encoding="utf-8") as f:
            for idx, length, lines, options in msgs:
                opt = "" if options is None else f"{options[0]}:{show(options[1])}"
                f.write(f"{idx}\t{length}\t{'|'.join(show(l) for l in lines)}\t{opt}\n")
        total_msgs += len(msgs)
        total_chars += sum(len(l.rstrip(b' \x00')) for m in msgs for l in m[2])
        print(f"MESS{n}: {len(raw)} bytes, {len(msgs)} messages")
    raw = open(f"{src}/phantasi/SCROLLS.DTX", "rb").read()
    with open(f"{out}/SCROLLS.tsv", "w", encoding="utf-8") as f:
        for n in range(len(raw) // 800):
            dec = decode_scroll(raw[n * 800:(n + 1) * 800], n)
            lines = [dec[i:i + 40] for i in range(0, 800, 40)]
            f.write(f"{n}\t{'|'.join(show(l.split(b'\\x00')[0]) for l in lines)}\n")
    print(f"MESS 合計 {total_msgs} 則、約 {total_chars} 個字元；SCROLLS {len(raw) // 800} 卷")


if __name__ == "__main__":
    main()
