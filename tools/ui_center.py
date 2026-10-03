#!/usr/bin/env python3
"""由動態記錄找出「原版以英文長度置中」的 ui 鍵，產生 \\c（置中）候選（docs/spec/003 §8）。只在 Docker 內執行。

  python -B ui_center.py <ui.<lang>.tsv> <textlog 記錄...> [--apply]

只看呼叫端白名單內的事件（訊息列與兩行訊息，確認原版以字串長度算置中欄：Col == (40 - len(Text)) / 2）；
選單項目等其他呼叫端會因欄位寬度巧合而符合同一公式，不在白名單內不判斷。
同一個鍵在白名單呼叫端的所有事件都置中，且至少 2 次，才列為候選。鍵的取法：組句（格式字串指標等於某筆 sprintf 的目的）
取 sprintf 的格式字串；沒有轉換的格式字串取規範化 Text；其餘取格式字串。--apply 才改寫 ui 檔：
候選鍵的譯文開頭加置中標記（已有者不動）。
"""
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalog_lib as cl  # noqa: E402

# 白名單：確認以長度置中的訊息呼叫端（映像偏移，docs/re 與第二輪審查 S-06 的量測）
CALLERS = {"A1E2", "5663", "2EA0", "2EEE", "2F10", "9C4C", "99B1", "991D"}

T_LINE = re.compile(
    r'^T step=(\d+) r=(\d+) c=(\d+) caller=([0-9A-F]+) ov=(\S+) fmtptr=([0-9A-F]+) '
    r'fmt="((?:[^"\\]|\\.)*)" text="((?:[^"\\]|\\.)*)" args=\[([0-9A-F ]*)\]')
S_LINE = re.compile(r'^S step=(\d+) caller=([0-9A-F]+) dest=([0-9A-F]+) fmt="((?:[^"\\]|\\.)*)"')


def unq(s):
    return bytes(s, "latin-1").decode("unicode_escape")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply = "--apply" in sys.argv
    ui_path, logs = args[0], args[1:]
    rows = cl.read_tsv(ui_path)
    ui = {k for _, k, _, _ in rows}
    stat = defaultdict(lambda: [0, 0])  # key -> [事件數, 置中數]
    for log in logs:
        dests = {}
        for line in open(log, encoding="utf-8", errors="replace"):
            m = S_LINE.match(line)
            if m:
                dests[m.group(3)] = unq(m.group(4))
                continue
            m = T_LINE.match(line)
            if not m:
                continue
            _, r, c, caller, _ov, fmtptr, fmt, text, argw = m.groups()
            if caller not in CALLERS:
                continue
            fmt, text = unq(fmt), unq(text)
            arg0 = argw.split()[0] if argw.split() else ""
            if fmtptr in dests:
                key = dests[fmtptr].rstrip()
            elif fmt == "%s" and arg0 in dests:  # 引數是組句緩衝區（例：兩行訊息）
                key = dests[arg0].rstrip()
            elif "%" not in fmt:
                key = text.rstrip()
            else:
                key = fmt.rstrip()
            if len(text) < 2:
                continue
            centered = int(c) == (40 - len(text)) // 2
            stat[key][0] += 1
            stat[key][1] += centered
    cand = sorted(k for k, (n, ok) in stat.items() if n >= 2 and ok == n and k in ui)
    notin = sorted(k for k, (n, ok) in stat.items() if n >= 2 and ok == n and k not in ui)
    mixed = sorted(k for k, (n, ok) in stat.items() if 0 < ok < n)
    print(f"置中候選（在 ui 內）{len(cand)} 筆；全置中但不在 ui（組句片段或資料型）{len(notin)} 筆；部分置中 {len(mixed)} 筆")
    for k in cand:
        print("  候選:", repr(k), stat[k])
    for k in notin:
        print("  全置中但不在 ui:", repr(k), stat[k])
    for k in mixed:
        print("  部分置中（不標）:", repr(k), stat[k])
    if apply:
        sel = set(cand)
        out, n = [], 0
        for _, k, tr, src in rows:
            if k in sel and tr and not tr.startswith(cl.CENTER) and tr != "<blank>":
                tr = cl.CENTER + tr
                n += 1
            out.append((k, tr, src))
        cl.write_tsv(ui_path, out)
        print(f"已標 {n} 筆 → {ui_path}")


if __name__ == "__main__":
    main()
