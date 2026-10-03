"""譯文 catalog 的共用函式：TSV 讀寫與跳脫、格式規格解析、格式引擎、寬度計算（docs/spec/003）。只在 Docker 內使用。"""
import re
import tarfile

# 003 §7：支援的轉換規格。旗標只有 -，寬度、精度、長度 l；轉換 s d u c；%% 另計。
# 不接受旗標 0 + # *、長度 h、轉換 x X o e f g、位置語法 %n$（lint 與執行期一致）。
CONV = re.compile(r"%(-?)([1-9]\d*)?(?:\.(\d+))?(l?)([sdcu%])")

# 置中標記：檔案內是開頭的 \c，記憶體內以私用區字元表示，避免與字面的 \\c 混淆。
CENTER = ""
BOM = "﻿"


def unescape(s: str) -> str:
    """跳脫只有 \\t、\\\\（003 §3）；開頭的 \\c 由 read_tsv 先處理。"""
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
        else:
            raise ValueError("不認得的跳脫 \\" + n)
    return "".join(out)


def escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("\t", "\\t")


def read_tsv(path: str, errors=None):
    """回傳 [(行號, key, translation, source)]；第一列是欄名。跳脫已還原；譯文開頭的 \\c 以 CENTER 字元表示。

    errors 為 None（預設，工具載入用）：鍵有尾端空白、跳脫錯誤、欄數錯誤等一律 raise ValueError；譯文尾端空白容錯去除
    （003 §3：執行期載入器容錯）。
    errors 為 list（lint 用）：每列的問題以 (行號, 訊息) 附加進去並盡量繼續（壞列略過，不使整檔放棄）；鍵或譯文有
    尾端空白也列為錯誤（讀原始行，不得靜默 rstrip），該列仍以去除後的內容回傳，使其他檢查繼續。
    """
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        data = f.read()

    def bad(n, msg):
        if errors is None:
            raise ValueError(f"第 {n} 列：{msg}")
        errors.append((n, msg))

    if data.startswith(BOM):
        bad(1, "檔案含 BOM")
        data = data[1:]
    if "\r" in data:
        bad(1, "檔案含 CR（要 LF）")
        data = data.replace("\r", "")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    for n, line in enumerate(lines, 1):
        if n == 1:
            if line.split("\t") != ["key", "translation", "source"]:
                bad(n, "第一列欄名要是 key、translation、source")
            continue
        cols = line.split("\t")
        if len(cols) != 3:
            bad(n, f"欄數是 {len(cols)}，要 3")
            continue
        if cols[0] != cols[0].rstrip(" "):
            bad(n, "鍵有尾端空白（003 §3 不允許）")
        if errors is not None and cols[1] != cols[1].rstrip(" "):
            bad(n, "譯文有尾端空白（003 §3 不允許）")
        tr = cols[1]
        marker = ""
        if tr.startswith("\\c"):
            marker, tr = CENTER, tr[2:]
        try:
            key = unescape(cols[0]).rstrip(" ")
            val = unescape(tr).rstrip(" ")
        except ValueError as e:
            bad(n, str(e))
            continue
        rows.append((n, key, marker + val, cols[2]))
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


def wide_table_loaded() -> bool:
    return _wide_set is not None


def wide(r: str) -> bool:
    c = ord(r)
    if _wide_set is not None:
        return c in _wide_set
    return c >= 0x2E80 or 0xFF00 <= c <= 0xFFEF


def width_h(s: str) -> int:
    """半格寬度（h）：全形 2、其他 1。置中標記不計。"""
    return sum(2 if wide(c) else 1 for c in s if c != CENTER)


# ---- 格式引擎（003 §7；與 Go 的 FormatEnglish、formatTarget 共用 tests/vectors） ----

def _to_s16(v: int) -> int:
    return ((v + 0x8000) & 0xFFFF) - 0x8000


def _to_s32(v: int) -> int:
    return ((v + 0x80000000) & 0xFFFFFFFF) - 0x80000000


def parse_fmt(fmt: str):
    """解析格式字串，回傳片段清單：("lit", 文字) 或 ("conv", 旗標-, 寬度, 精度, l, 類型)。
    含不支援的規格時 raise ValueError。"""
    if has_bad_percent(fmt):
        raise ValueError("含不支援的轉換規格")
    out, pos = [], 0
    for m in CONV.finditer(fmt):
        if m.start() > pos:
            out.append(("lit", fmt[pos:m.start()]))
        pos = m.end()
        if m.group(5) == "%":
            out.append(("lit", "%"))
            continue
        out.append(("conv", m.group(1) == "-", int(m.group(2)) if m.group(2) else 0,
                    int(m.group(3)) if m.group(3) is not None else None, m.group(4) == "l", m.group(5)))
    if pos < len(fmt):
        out.append(("lit", fmt[pos:]))
    return out


def _word_text(conv: str, ll: bool, words):
    """依型別取出引數字組，回傳（數字文字或字元, 用掉的字組數）。"""
    if conv == "c":
        return chr(words[0] & 0xFF), 1
    if ll:
        v = (words[1] << 16) | words[0]
        return str(_to_s32(v) if conv == "d" else v), 2
    v = words[0] & 0xFFFF
    return str(_to_s16(v) if conv == "d" else v), 1


def format_english(fmt: str, args):
    """原版 sub_5032 的英文語意。args 是依序的引數：%s 取 str，其餘取 16 位元字組（int），%ld %lu 取兩個字組（低在前）。"""
    out, ai = [], 0
    for seg in parse_fmt(fmt):
        if seg[0] == "lit":
            out.append(seg[1])
            continue
        _, left, width, prec, ll, conv = seg
        if conv == "s":
            text = args[ai]
            ai += 1
            if prec is not None:
                text = text[:prec]
        else:
            n = 2 if ll and conv in "du" else 1
            text, used = _word_text(conv, ll, args[ai:ai + n])
            ai += used
            if prec is not None and conv != "c":
                text = text[:prec]
        pad = max(0, width - len(text))
        out.append(text + " " * pad if left else " " * pad + text)
    return "".join(out)


def format_target(tpl: str, args):
    """目標語言語意（003 §7.2）。args：%s 取 ("s", 文字)（原樣保留的 ASCII）或 ("t", 文字)（譯文），其餘同 format_english。
    回傳字串；寬度以 h 計請用 width_h。欄位寬度 W 一律是 2W h；%s 精度對譯文是 2P h 的整字前綴，對原樣 ASCII 是 P 字元。"""
    out, ai = [], 0
    for seg in parse_fmt(tpl):
        if seg[0] == "lit":
            out.append(seg[1])
            continue
        _, left, width, prec, ll, conv = seg
        if conv == "s":
            kind, text = args[ai]
            ai += 1
            if prec is not None:
                if kind == "t":
                    keep, acc = [], 0
                    for ch in text:
                        w = 2 if wide(ch) else 1
                        if acc + w > 2 * prec:
                            break
                        keep.append(ch)
                        acc += w
                    text = "".join(keep)
                else:
                    text = text[:prec]
        else:
            n = 2 if ll and conv in "du" else 1
            text, used = _word_text(conv, ll, args[ai:ai + n])
            ai += used
            if prec is not None and conv != "c":
                text = text[:prec]
        pad = max(0, 2 * width - width_h(text))
        out.append(text + " " * pad if left else " " * pad + text)
    return "".join(out)


# 各規格最大位數（用於樣本寬度）
NUM_MAX = {("d", False): "-32768", ("u", False): "65535", ("d", True): "-2147483648", ("u", True): "4294967295"}


def sample_format(tpl: str, samples):
    """以樣本引數格式化目標語言模板，回傳 h 寬度。%s 樣本不足時以 'X' 重複（精度或寬度，預設 8）。
    欄位寬度與精度以「格」為單位（1 格 = 2 h）；數字精度是最多輸出字元數（原版語意）。"""
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


def field_right_edges(tpl: str, samples, english: bool):
    """每個轉換的 (右緣位置 h, 有明寫寬度且其後還有內容)。english 為真時以原文語意（1 字元 = 2 h，原版每格寬）計，否則以目標語言語意。"""
    edges = []
    cur = 0
    pos = 0
    si = 0
    for m in CONV.finditer(tpl):
        lit = tpl[pos:m.start()].replace("%%", "%")
        cur += 2 * len(lit) if english else width_h(lit)
        pos = m.end()
        if m.group(5) == "%":
            cur += 2 if english else 1
            continue
        width = int(m.group(2) or 0)
        prec = m.group(3)
        ll, conv = m.group(4) == "l", m.group(5)
        if conv == "s":
            s = samples[si] if si < len(samples) else "X" * (int(prec) if prec is not None else (width or 8))
            si += 1
            if prec is not None:
                if english:
                    s = s[:int(prec)]
                else:
                    keep, acc = [], 0
                    for ch in s:
                        w = 2 if wide(ch) else 1
                        if acc + w > 2 * int(prec):
                            break
                        keep.append(ch)
                        acc += w
                    s = "".join(keep)
            h = 2 * len(s) if english else width_h(s)
        elif conv == "c":
            h = 2 if english else 1
            si += 1
        else:
            n = len(NUM_MAX.get((conv, ll), "65535"))
            if prec is not None:
                n = min(n, int(prec))
            h = 2 * n if english else n
        if width:
            h = min(h, 2 * width)  # 有明寫寬度時假設內容放得進欄位：欄寬就是 2W h（兩側同一規則）
        cur += max(h, 2 * width)
        rest = tpl[m.end():]
        edges.append((cur, width > 0 and bool(rest.strip() or CONV.search(rest))))
    return edges


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
