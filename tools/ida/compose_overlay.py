"""把 overlay 依載入器的語意疊到常駐映像上，產出可載入 IDA 的映像。只在 Docker 內執行。

依據 docs/re/003-ida-static-survey.md 發現 11 與 docs/re/004-overlay-format.md：
  標頭 14 bytes = 7 個小端字組：簽章 00F2h、程式碼目的偏移、程式碼長度、
  資料目的偏移、資料長度、額外長度、入口偏移。
  程式碼段落讀到 CS:程式碼目的偏移（CS=0110，映像偏移同值）；
  資料段落讀到 DS:資料目的偏移（DS=0DAF，映像偏移為 0xC9F0 + 偏移）。
  檔案大小必須等於 14 + 程式碼長度 + 資料長度。

用法：python compose_overlay.py <常駐映像> <overlay> <輸出>
"""
import struct
import sys

DGROUP_IMAGE_OFFSET = 0xC9F0

base = bytearray(open(sys.argv[1], "rb").read())
ovl = open(sys.argv[2], "rb").read()
sig, code_dst, code_len, data_dst, data_len, extra, entry = struct.unpack("<7H", ovl[:14])
assert sig == 0x00F2, "簽章不符"
assert 14 + code_len + data_len == len(ovl), "檔案大小與標頭不符"
code = ovl[14:14 + code_len]
data = ovl[14 + code_len:]
assert code_dst + code_len <= DGROUP_IMAGE_OFFSET, "程式碼段落超出程式碼段"
d0 = DGROUP_IMAGE_OFFSET + data_dst
assert d0 + data_len <= len(base), "資料段落超出映像"
base[code_dst:code_dst + code_len] = code
base[d0:d0 + data_len] = data
open(sys.argv[3], "wb").write(base)
print("composed", sys.argv[3], len(base), "bytes; code %04X..%04X data image+%05X..%05X entry %04X" % (
    code_dst, code_dst + code_len, d0, d0 + data_len, entry))
