"""輸入清冊產生器。只在 Docker 內執行，不掛入主機 Python。

用法（見 docs/re/001-input-inventory.md 的「重跑方法」）：
  /in   專案根目錄，唯讀（內含原版壓縮檔）
  /out  workplace/，解壓結果寫到 /out/orig
  /re   docs/re/，寫出 001-input-inventory.tsv

只讀 bytes 與標頭，判定不超過 bytes 本身能支持的等級。
"""
import hashlib
import os
import struct
import sys
import zipfile

ZIP = "/in/Phantasie (1987).zip"
OUT = "/out/orig"
TSV = "/re/001-input-inventory.tsv"

DOC_NAMES = {"GENERAL.DOC", "LISTING.DOC", "ORDER.DOC"}


def lzexe_fields(d):
    """MZ 標頭欄位與 0x1C 的簽章字串。"""
    if d[:2] != b"MZ":
        return None
    cblp, cp, crlc, cparhdr, minalloc, maxalloc, ss, sp, csum, ip, cs = struct.unpack("<11H", d[2:24])
    return {
        "image_bytes": (cp - 1) * 512 + (cblp or 512),
        "hdr_paras": cparhdr,
        "reloc": crlc,
        "minalloc": minalloc,
        "maxalloc": maxalloc,
        "ss:sp": "%04X:%04X" % (ss, sp),
        "cs:ip": "%04X:%04X" % (cs, ip),
        "sig_at_1C": d[0x1C:0x20].decode("latin-1"),
    }


def classify(name, d, ratio):
    """回傳 (類別, 格式判定, 等級, 權利分類)。"""
    base = os.path.basename(name)
    up = base.upper()
    rights_game = "原版遊戲檔（權利人待查；使用者本機輸入，不入 Git）"
    rights_pub = "發行商附檔（WizardWorks；非遊戲文字，不翻譯；不入 Git）"

    if len(d) == 0:
        return ("空檔", "0 bytes", "已證實（bytes）", "無內容；不入 Git")
    if up in DOC_NAMES:
        return ("發行商附檔", "純 ASCII 文字，CRLF", "已證實（bytes）", rights_pub)
    if up == "VERSION":
        return ("版本字串", "純 ASCII 文字", "已證實（bytes）", rights_game)
    if up == "WIZ.BAT":
        return ("啟動腳本", "純 ASCII 文字，CRLF", "已證實（bytes）", rights_game)
    if up == "PHANTASI.EXE":
        f = lzexe_fields(d)
        note = "MZ；%s" % "；".join("%s=%s" % kv for kv in f.items())
        lvl = "已證實（標頭 bytes）；LZEXE 0.90 壓縮為強推論" if f["sig_at_1C"] == "LZ09" else "已證實（標頭 bytes）"
        return ("主程式", note, lvl, rights_game)
    if up.endswith(".COM"):
        mz = d[:2] == b"MZ"
        return ("啟動用 COM", "無 MZ 簽章" if not mz else "MZ（非預期）",
                "已證實（簽章 bytes）；指令內容為強推論（手工解讀，未經反組譯器）", rights_game)
    if up.endswith(".OVR"):
        return ("overlay", "開頭 %s；不是 Borland 的 FBOV 簽章" % d[:4].hex(" ").upper(),
                "已證實（bytes）；載入機制未知", rights_game)
    if up.startswith("MESS") or up == "SCROLLS.DTX":
        return ("資料檔", "非明文（可列印比例 %.2f）；編碼或壓縮未知" % ratio, "未知", rights_game)
    if up.startswith("OUT") and up.endswith(".DAT"):
        return ("資料檔", "固定 %d bytes；內容未知" % len(d), "未知", rights_game)
    if up.startswith("DNG") and not up.endswith(".SAV"):
        return ("資料檔", "內容未知", "未知", rights_game)
    if up == "FONT":
        ok = len(d) == 127 * 16
        return ("字模", "%d bytes %s 127×16；CGA 模式 4 的 8×8 字模為假說" % (len(d), "=" if ok else "≠"),
                "大小已證實；用途為假說", rights_game)
    if up == "WIZ-MAIN.BSV":
        if d[0] == 0xFD and len(d) >= 7:
            _, seg, off, ln = struct.unpack("<BHHH", d[:7])
            note = "BSAVE 標頭：魔數 FD、段 %04X、偏移 %04X、長度 %04X（%d）；檔案大小 %d %s 7+長度" % (
                seg, off, ln, ln, len(d), "=" if len(d) == 7 + ln else "≠")
            return ("圖形資料", note, "標頭已證實；內容為畫面影像屬強推論", rights_game)
        return ("圖形資料", "非 BSAVE 標頭", "未知", rights_game)
    if up.endswith(".IBM") or up == "IBMCOVER" or up.endswith(".PAT"):
        return ("圖形資料", "檔名與大小暗示圖形；格式與顯示模式未知", "假說", rights_game)
    return ("資料檔", "內容與用途未知", "未知", rights_game)


def main():
    print("python", sys.version.split()[0])
    zbytes = open(ZIP, "rb").read()
    zsha = hashlib.sha256(zbytes).hexdigest()
    rows = []
    with zipfile.ZipFile(ZIP) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            norm = os.path.normpath(info.filename)
            if norm.startswith("..") or os.path.isabs(norm):
                raise SystemExit("unsafe path: " + info.filename)
            d = z.read(info)
            dst = os.path.join(OUT, norm)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                f.write(d)
            printable = sum(1 for b in d if 32 <= b < 127 or b in (9, 10, 13))
            ratio = printable / len(d) if d else 0.0
            cat, fmt, lvl, rights = classify(info.filename, d, ratio)
            rows.append([os.path.basename(norm), len(d), hashlib.sha256(d).hexdigest(), cat, fmt, lvl, rights])
    rows.sort(key=lambda r: r[0].upper())
    with open(TSV, "w", encoding="utf-8") as f:
        f.write("name\tbytes\tsha256\tcategory\tformat\tevidence_level\trights\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    print("zip_sha256", zsha, "size", len(zbytes))
    print("files", len(rows), "total_bytes", sum(r[1] for r in rows))


main()
