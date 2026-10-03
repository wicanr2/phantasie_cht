#!/usr/bin/env python3
"""MESSn 與 SCROLLS.DTX 的解碼與列舉（只讀原版檔，輸出到指定目錄）。

格式與證據見 docs/re/007-message-and-scroll-formats.md。需在 Docker 內執行：

  docker run --rm --network none -u "$(id -u):$(id -g)" \
    -v <原版目錄>:/o:ro -v <輸出目錄>:/out -v "$PWD/tools:/t:ro" \
    python:3.13-bookworm python -B /t/gamedata.py /o /out

輸出（都是原版文字，只寫進 workplace/，不進版控）：
  MESSn.msgs.tsv  每則訊息一列：種類（msg、orphan）、索引、總長 L、行（以 | 連接）、選項
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
    """依 OV2 sub_8F71 的規則切成訊息。

    訊息從第一個 chunk 開始，其第 1 byte 是整則長度 L，ceil(L / 40) 個連續索引各給一行。
    選項數是索引 idx+1 那個 chunk 的第 1 byte（2 至 20 才算），選項文字在最後一行之後的 chunk。
    L 小於 40 的 chunk 是短訊息（文字在前 L 個字元，其後是選項欄位，見 sub_8F71 的 var_45 強制為 3）。
    第 1 byte 為 0、1、32 的 chunk 是續頁與標記。沒有被任何訊息取用的 chunk 列為 orphan，不補規則。
    回傳 [(kind, idx, L, 行 list, 選項數, 選項文字)]。
    """
    table = struct.unpack_from("<%dH" % TABLE_WORDS, dec, 0)
    chunks = {i: chunk_at(dec, table, i) for i in range(1, TABLE_WORDS)}
    used = set()
    msgs = []
    for idx in range(1, TABLE_WORDS):
        c = chunks[idx]
        if c is None or idx in used:
            continue
        length = c[0]
        if length in (0, 1, 32):
            continue  # 續頁、標記；沒被取用的之後列為 orphan
        kind = "short" if length < 40 else "msg"
        n = (length + 39) // 40
        lines = []
        for k in range(n):
            ck = chunks.get(idx + k)
            if ck is None:
                break
            lines.append(ck[1])
            used.add(idx + k)
        opt_n, opt_text = None, None
        nxt = chunks.get(idx + 1)
        if nxt is not None and 2 <= nxt[0] <= 20:
            oc = chunks.get(idx + n)
            if oc is not None:
                opt_n, opt_text = nxt[0], oc[1]
                used.add(idx + n)
        msgs.append((kind, idx, length, lines, opt_n, opt_text))
    for idx in range(1, TABLE_WORDS):
        c = chunks[idx]
        if c is not None and idx not in used:
            msgs.append(("orphan", idx, c[0], [c[1]], None, None))
    msgs.sort(key=lambda m: m[1])
    return msgs


def show(b: bytes) -> str:
    return b.decode("latin-1").replace("\x00", "~").replace("\t", " ").replace("\n", " ")


def main():
    src, out = sys.argv[1], sys.argv[2]
    kinds = {"msg": 0, "short": 0, "orphan": 0}
    total_chars = 0
    for n in range(1, 11):
        raw = open(f"{src}/phantasi/MESS{n}", "rb").read()
        dec = decode_mess(raw, n)
        msgs = parse_mess(dec)
        with open(f"{out}/MESS{n}.msgs.tsv", "w", encoding="utf-8") as f:
            for kind, idx, length, lines, opt_n, opt_text in msgs:
                opt = "" if opt_n is None else f"{opt_n}:{show(opt_text)}"
                f.write(f"{kind}\t{idx}\t{length}\t{'|'.join(show(l) for l in lines)}\t{opt}\n")
        for m in msgs:
            kinds[m[0]] += 1
            total_chars += sum(len(l.rstrip(b' \x00')) for l in m[3])
        print(f"MESS{n}: {len(raw)} bytes, msg {sum(1 for m in msgs if m[0] == 'msg')}, orphan {sum(1 for m in msgs if m[0] == 'orphan')}")
    raw = open(f"{src}/phantasi/SCROLLS.DTX", "rb").read()
    with open(f"{out}/SCROLLS.tsv", "w", encoding="utf-8") as f:
        for n in range(len(raw) // 800):
            dec = decode_scroll(raw[n * 800:(n + 1) * 800], n)
            lines = [dec[i:i + 40] for i in range(0, 800, 40)]
            f.write(f"{n}\t{'|'.join(show(l.split(b'\\x00')[0]) for l in lines)}\n")
    print(f"MESS 合計 msg {kinds["msg"]}、short {kinds["short"]}、orphan {kinds['orphan']}，可讀字元約 {total_chars}；SCROLLS {len(raw) // 800} 卷")


if __name__ == "__main__":
    main()
