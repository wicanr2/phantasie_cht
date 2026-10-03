#!/usr/bin/env python3
"""靜態列舉常駐映像與兩個 overlay 的 DGROUP 字串，附程式碼與資料指標參照。

只在 Docker 內執行；輸入唯讀，輸出寫進指定目錄（原版文字，不進版控）。

  docker run --rm --network none -u "$(id -u):$(id -g)" \
    -v <workplace/ida>:/ida:ro -v <原版目錄>:/o:ro -v <輸出目錄>:/out -v "$PWD/tools:/t:ro" \
    python:3.13-bookworm python -B /t/enumerate_text.py /ida /o /out

輸入：
  /ida/phantasi_unpacked.bin、ov1_composed.bin、ov2_composed.bin（tools/ida/compose_overlay.py 的產物）
  /o/phantasi/OV1.OVR、OV2.OVR（只讀標頭）
輸出：
  /out/strings.tsv   欄：region、ds、len、imm_refs、dptr_refs、kind、text（跳脫）
  /out/summary.txt   各 region 與 kind 的計數

映像座標：DGROUP 在映像位移 0C9F0h；DS 偏移 = 映像位移 - 0C9F0h。程式碼：常駐 0000h 至 53E9h，
overlay 程式碼 53EAh 起（長度見標頭）。overlay 資料載入到 DS:B8F0。
"""
import re
import struct
import sys

DG = 0xC9F0
OV_CODE = 0x53EA
OV_DATA = 0xB8F0
MIN_LEN = 2
FILE_RE = re.compile(r"^[A-Za-z0-9_%-]+(\.[A-Za-z0-9]{1,3})?$")
FILE_WORDS = {"font", "phm", "pat", "ov1", "ov2", "phbackup", "sack", "twns", "guild"}


def strings_in(data: bytes, lo: int, hi: int):
    """lo..hi 是 DS 偏移範圍；回傳 [(ds, bytes)]，字串以 NUL 結尾，全部是 20h 至 7Eh。"""
    out = []
    i = lo
    while i < hi:
        j = i
        while j < hi and 0x20 <= data[DG + j] <= 0x7E:
            j += 1
        if j - i >= MIN_LEN and j < hi and data[DG + j] == 0:
            out.append((i, bytes(data[DG + i:DG + j])))
            i = j + 1
        else:
            i = max(j, i) + 1
    return out


def imm_refs(code: bytes, base: int, ds: int):
    """程式碼內以 imm16 取得 DS 偏移的位置：mov r16,imm（B8 至 BF）、push imm（68）。"""
    pat = struct.pack("<H", ds)
    hits = []
    pos = code.find(pat)
    while pos >= 0:
        if pos >= 1 and (0xB8 <= code[pos - 1] <= 0xBF or code[pos - 1] == 0x68):
            hits.append(base + pos - 1)
        pos = code.find(pat, pos + 1)
    return hits


def dptr_refs(data: bytes, lo: int, hi: int, ds: int):
    """DGROUP 資料內，偶數對齊、值等於 ds 的字組位置（DS 偏移）。"""
    pat = struct.pack("<H", ds)
    hits = []
    pos = data.find(pat, DG + lo, DG + hi)
    while pos >= 0:
        if (pos - DG) % 2 == 0:
            hits.append(pos - DG)
        pos = data.find(pat, pos + 1, DG + hi)
    return hits


def kind_of(text: str) -> str:
    if "%" in text:
        return "fmt"
    if FILE_RE.match(text) and (("." in text) or text.lower() in FILE_WORDS):
        return "file"
    return "text"


def esc(b: bytes) -> str:
    return b.decode("latin-1").replace("\\", "\\\\").replace("\t", "\\t")


def main():
    ida, orig, out = sys.argv[1], sys.argv[2], sys.argv[3]
    res = open(f"{ida}/phantasi_unpacked.bin", "rb").read()
    regions = [("res", res, 0, OV_DATA, [(0, OV_CODE)])]
    for name in ("ov1", "ov2"):
        comp = open(f"{ida}/{name}_composed.bin", "rb").read()
        hdr = open(f"{orig}/phantasi/{name.upper()}.OVR", "rb").read(14)
        sig, code_dst, code_len, data_dst, data_len, extra, entry = struct.unpack("<7H", hdr)
        assert sig == 0xF2 and data_dst == OV_DATA and code_dst == OV_CODE
        regions.append((name, comp, OV_DATA, OV_DATA + data_len, [(0, OV_CODE), (OV_CODE, OV_CODE + code_len)]))
    rows = []
    for label, img, lo, hi, code_ranges in regions:
        code = b"".join(img[a:b] for a, b in code_ranges)
        # 映像位移對照：串接後的位置換回映像位移
        offs = []
        acc = 0
        for a, b in code_ranges:
            offs.append((acc, a))
            acc += b - a
        for ds, raw in strings_in(img, lo, hi):
            imm = imm_refs(code, 0, ds)
            imm_img = []
            for p in imm:
                for start, a in reversed(offs):
                    if p >= start:
                        imm_img.append(a + (p - start))
                        break
            dp = dptr_refs(img, 0, 0xFFFF, ds)
            text = raw.decode("latin-1")
            rows.append((label, ds, len(raw), imm_img, dp, kind_of(text), esc(raw)))
    with open(f"{out}/strings.tsv", "w", encoding="utf-8") as f:
        f.write("region\tds\tlen\timm_refs\tdptr_refs\tkind\ttext\n")
        for r in rows:
            f.write(f"{r[0]}\t{r[1]:04X}\t{r[2]}\t{','.join('%04X' % x for x in r[3][:6])}\t"
                    f"{','.join('%04X' % x for x in r[4][:6])}\t{r[5]}\t{r[6]}\n")
    from collections import Counter
    c = Counter((r[0], r[5]) for r in rows)
    ref = Counter((r[0], "ref" if (r[3] or r[4]) else "noref") for r in rows)
    with open(f"{out}/summary.txt", "w", encoding="utf-8") as f:
        for k, v in sorted(c.items()):
            f.write(f"{k[0]}\t{k[1]}\t{v}\n")
        for k, v in sorted(ref.items()):
            f.write(f"{k[0]}\t{k[1]}\t{v}\n")
    print(open(f"{out}/summary.txt").read())


if __name__ == "__main__":
    main()
