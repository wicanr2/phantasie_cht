"""譯文 catalog 的共用函式：TSV 讀寫與跳脫、格式規格解析、寬度計算（docs/spec/003）。只在 Docker 內使用。"""
import re
import tarfile

# 003 §7：支援的轉換規格。旗標只有 -，寬度、精度、長度 l；轉換 s d u c；%% 另計。
CONV = re.compile(r"%(-?)(\d*)(?:\.(\d+))?(l?)([sdcu%])")

# 置中標記：檔案內是開頭的 \c，記憶體內以私用區字元表示，避免與字面的 \\c 混淆。
CENTER = ""


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
        elif n == "x":
            h = s[i + 2:i + 4]
            if len(h) != 2 or any(ch not in "0123456789abcdefABCDEF" for ch in h):
                raise ValueError("\\x 後要剛好兩位十六進位")
            out.append(chr(int(h, 16)))
            i += 4
        else:
            raise ValueError("不認得的跳脫 \\" + n)
    return "".join(out)


def escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("\t", "\\t")


def read_tsv(path: str):
    """回傳 [(行號, key, translation, source)]；第一列是欄名。跳脫已還原；鍵有尾端空白是錯誤，譯文尾端空白已去除。
    譯文開頭的 \\c 以 CENTER 字元表示。"""
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
        if cols[0] != cols[0].rstrip(" "):
            raise ValueError(f"第 {n + 1} 列的鍵有尾端空白（003 §3 不允許）")
        tr = cols[1]
        marker = ""
        if tr.startswith("\\c"):
            marker, tr = CENTER, tr[2:]
        rows.append((n + 1, unescape(cols[0]), marker + unescape(tr).rstrip(" "), cols[2]))
    return rows


def write_tsv(path: str, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("key\ttranslation\tsource\n")
        for key, tr, src in rows:
            marker = ""
            if tr.startswith(CENTER):
                marker, tr = "\\c", tr[1:]
            f.write(f"{escape(key)}\t{marker}{escape(tr.rstrip(' '))}\t{src}\n")


def convs(fmt: str):
    """格式字串內的轉換序（不含 %%）：[(旗標-, 寬度, 精度, l, 類型)]。"""
    out = []
    for m in CONV.finditer(fmt):
        if m.group(5) == "%":
            continue
        out.append((m.group(1) == "-", int(m.group(2)) if m.group(2) else 0,
                    int(m.group(3)) if m.group(3) is not None else None, m.group(4) == "l", m.group(5)))
    return out


def has_bad_percent(fmt: str) -> bool:
    """有 % 但不是支援的規格（尾端 %、旗標 0 + # * h、%x %o %e %f %g、%n$ 等）。"""
    rest = CONV.sub("", fmt)
    return "%" in rest


# 全形判定：由字型寬度表決定（docs/spec/001 §6、004 §3）。沒載入字型時退回碼點範圍（僅供沒有字型的情形）。
_wide_set = None


def load_wide_from_hex(tar_path: str, member: str):
    """由 Unifont hex 的行長建立全形碼點集合（64 個十六進位字元 = 16 px 寬）。"""
    global _wide_set
    wide_cps = set()
    t = tarfile.open(tar_path)
    for line in t.extractfile(member).read().decode().splitlines():
        if ":" in line:
            code, bits = line.split(":", 1)
            if len(bits) == 64:
                wide_cps.add(int(code, 16))
    _wide_set = wide_cps
    return wide_cps


def wide(r: str) -> bool:
    c = ord(r)
    if _wide_set is not None:
        return c in _wide_set
    return c >= 0x2E80 or 0xFF00 <= c <= 0xFFEF


def width_h(s: str) -> int:
    """半格寬度（h）：全形 2、其他 1。置中標記不計。"""
    return sum(2 if wide(c) else 1 for c in s if c != CENTER)


# 各規格最大位數（用於樣本寬度）
NUM_MAX = {("d", False): "-32768", ("u", False): "65535", ("d", True): "-2147483648", ("u", True): "4294967295"}


def sample_format(tpl: str, samples):
    """以樣本引數格式化目標語言模板，回傳 h 寬度。%s 樣本不足時以 'X' 重複（精度或寬度，預設 8）。
    寬度與精度以「格」為單位（1 格 = 2 h）；數字精度是最多輸出字元數（原版語意）。"""
    out_h = 0
    pos = 0
    si = 0
    for m in CONV.finditer(tpl):
        out_h += width_h(tpl[pos:m.start()].replace("%%", "%"))
        pos = m.end()
        if m.group(5) == "%":
            out_h += 1
            continue
        width = int(m.group(2) or 0)
        prec = m.group(3)
        ll, conv = m.group(4) == "l", m.group(5)
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
            h = len(NUM_MAX.get((conv, ll), "65535"))
            if prec is not None:
                h = min(h, int(prec))
        out_h += max(h, 2 * width)
    out_h += width_h(tpl[pos:].replace("%%", "%"))
    return out_h


def english_cells(key: str) -> int:
    """原文格式化寬度（格）：原版每個字元一格。字面字元數加各轉換的欄位寬度（無寬度時用樣本長度：%s 8、數字最大位數，
    數字有精度時最多精度個字元）。"""
    total, pos = 0, 0
    for m in CONV.finditer(key):
        total += len(key[pos:m.start()])
        pos = m.end()
        if m.group(5) == "%":
            total += 1
            continue
        width = int(m.group(2) or 0)
        prec = m.group(3)
        conv, ll = m.group(5), m.group(4) == "l"
        if conv == "s":
            n = int(prec) if prec is not None else 8
        elif conv == "c":
            n = 1
        else:
            n = len(NUM_MAX.get((conv, ll), "65535"))
            if prec is not None:
                n = min(n, int(prec))
        total += max(n, width)
    return total + len(key[pos:])
