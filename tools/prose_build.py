#!/usr/bin/env python3
"""把訊息層級的譯文（JSONL）合併成行層級的 text/prose.<lang>.tsv。只在 Docker 內執行。

  python -B prose_build.py <prose-units.jsonl> <譯文目錄> <輸出 prose.zh-TW.tsv> \
      [--glossary text/glossary.tsv] [--font-tar T --font-member M] [--report 報告檔]

譯文檔：<譯文目錄>/*.zh.jsonl，每列 {"id": ..., "zh": [每行一個字串], "opt_zh": [選項標籤]}。
檢查（任一項違規就列出，違規的單位不寫入）：
  id 都在單位清單內、行數與原文相同、每行顯示寬度（全形 2、其他 1，半格）不超過 80、無控制字元、
  字型有該字、英文原文含術語表的詞（不分大小寫、詞界）時，該則譯文必須含對應譯詞。
輸出：key = h:<sha256(UTF-8 的原文行 rstrip)[:12]>、translation = 該行譯文（空白行寫 <blank>）、
  source = <id>#<行號>。同一原文行有不同譯文時列為衝突，輸出取第一筆。
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys
import tarfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalog_lib as cl  # noqa: E402

BLANK = "<blank>"
GENERIC = {"Exit", "Option", "Bank", "Inn", "Guild", "Armory"}


def is_centered(u, i):
    """置中判斷（docs/spec/003 §8）：卷軸前兩行（標題）；訊息行兩端空白都至少 1 且（差不超過 2 或含 --）。"""
    if u["kind"] == "scroll":
        return i < 2
    lead, trail = u.get("lead", [0] * 99)[i], u.get("trail", [0] * 99)[i]
    return lead >= 1 and trail >= 1 and (abs(lead - trail) <= 2 or "--" in u["lines"][i])


def key_of(line: str) -> str:
    return "h:" + hashlib.sha256(line.rstrip().encode("utf-8")).hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("units")
    ap.add_argument("zhdir")
    ap.add_argument("out")
    ap.add_argument("--glossary")
    ap.add_argument("--font-tar")
    ap.add_argument("--font-member")
    ap.add_argument("--report")
    a = ap.parse_args()
    units = {}
    for l in open(a.units, encoding="utf-8"):
        u = json.loads(l)
        units[u["id"]] = u
    cps = None
    if a.font_tar:
        cl.load_wide_from_hex(a.font_tar, a.font_member)
        cps = set(range(0x20, 0x7F))
        for line in tarfile.open(a.font_tar).extractfile(a.font_member).read().decode().splitlines():
            if ":" in line:
                cps.add(int(line.split(":", 1)[0], 16))
    glossary = []
    if a.glossary:
        for i, line in enumerate(open(a.glossary, encoding="utf-8")):
            if i and line.strip():
                c = line.rstrip("\n").split("\t")
                glossary.append((c[0], c[1]))
    problems, got = [], {}
    for path in sorted(glob.glob(os.path.join(a.zhdir, "*.zh.jsonl"))):
        for n, l in enumerate(open(path, encoding="utf-8"), 1):
            if not l.strip():
                continue
            try:
                t = json.loads(l)
            except json.JSONDecodeError as e:
                problems.append(f"{path}:{n}: JSON 錯誤 {e}")
                continue
            uid = t.get("id")
            if uid not in units:
                problems.append(f"{path}:{n}: 未知的 id {uid}")
                continue
            u = units[uid]
            zh = t.get("zh")
            where = f"{os.path.basename(path)}:{uid}"
            bad = False
            if not isinstance(zh, list) or len(zh) != len(u["lines"]):
                problems.append(f"{where}: 行數 {len(zh) if isinstance(zh, list) else '?'} 與原文 {len(u['lines'])} 不同")
                continue
            for i, line in enumerate(zh):
                if not isinstance(line, str):
                    problems.append(f"{where}#{i}: 不是字串")
                    bad = True
                    continue
                if line.strip() and not u["lines"][i].strip():
                    problems.append(f"{where}#{i}: 原文是空白行，譯文不得放文字（不會被顯示）")
                    bad = True
                if any(ord(c) < 0x20 for c in line):
                    problems.append(f"{where}#{i}: 含控制字元")
                    bad = True
                # 寬度上限依該行實際繪出的長度（avail = 2 × 繪出字元數，docs/spec/001 §6）：開頭空白數、去尾端空白的原文、尾端空白數
                if u["lines"][i].strip():
                    avail = 2 * (u["lead"][i] + len(u["lines"][i].lstrip(" ")) + u["trail"][i])
                    w = cl.width_h(line.strip(" ") if is_centered(u, i) else line.rstrip(" "))
                    if w > avail:
                        problems.append(f"{where}#{i}: 寬度 {w}h 超過這行的 {avail}h")
                        bad = True
                if cps is not None:
                    for ch in set(line):
                        if ord(ch) not in cps:
                            problems.append(f"{where}#{i}: 字型缺字 U+{ord(ch):04X} {ch}")
                            bad = True
            oz = t.get("opt_zh", [])
            if len(oz) != len(u.get("opt_cells", [])) or any(not isinstance(x, str) or not x.strip() for x in oz):
                problems.append(f"{where}: opt_zh 數量 {len(oz)} 與選項 {len(u.get('opt_cells', []))} 不同或有空白")
                continue
            raw_cells = [c.replace("~", " ") for c in (u.get("opt") or "").split("|") if c.strip()]
            for j, x in enumerate(oz):
                # 選項欄位每格 11 或 3 字元（開頭空白保留，只去尾端）：上限 = 2 × 欄位實際長度
                avail = 2 * len(raw_cells[j]) if j < len(raw_cells) else 22
                if cl.width_h(x.strip()) > avail:
                    problems.append(f"{where}: 選項 {j} 寬度 {cl.width_h(x.strip())}h 超過 {avail}h")
                    bad = True
            en_all = " ".join(u["lines"] + u.get("opt_cells", []))
            zh_all = "".join(zh + oz)
            for en_term, zh_term in glossary:
                if en_term in GENERIC:
                    continue  # 一般詞（Exit 等）在敘事裡常作動詞，不檢查
                if re.search(r"(?<![A-Za-z])" + re.escape(en_term) + r"S?(?![A-Za-z])", en_all, re.I) and zh_term not in zh_all:
                    problems.append(f"{where}: 原文含 {en_term}，譯文應含「{zh_term}」")
                    bad = True
            if not bad:
                got[uid] = t
    rows, conflicts, seen = [], [], {}  # seen[k] = rows 內的位置

    def add(k, tr, src):
        """同一鍵有不同譯文時取顯示寬度較小者（較不易超寬），列為衝突待人工確認。"""
        if k not in seen:
            seen[k] = len(rows)
            rows.append((k, tr, src))
            return
        old = rows[seen[k]]
        if old[1] != tr:
            conflicts.append(f"{k} {old[2]} 與 {src}: 譯文不同，取顯示寬度較小者")
            if cl.width_h(tr.removeprefix(cl.CENTER)) < cl.width_h(old[1].removeprefix(cl.CENTER)):
                rows[seen[k]] = (k, tr, old[2])

    for uid, t in got.items():
        u = units[uid]
        for i, (en, zh) in enumerate(zip(u["lines"], t["zh"])):
            if not en.strip():
                continue
            # 置中行去掉頭尾空白（版面層置中）；其他行只去尾端，保留譯文自己的開頭空白（docs/spec/001 §6）
            if not zh.strip():
                tr = BLANK
            elif is_centered(u, i):
                tr = cl.CENTER + zh.strip(" ")
            else:
                tr = zh.rstrip(" ")
            add(key_of(en), tr, f"{uid}#{i}")
        for j, (en, zh) in enumerate(zip(u.get("opt_cells", []), t.get("opt_zh", []))):
            add(key_of(en), zh.strip(), f"{uid}/opt{j}")
    rows.sort()
    cl.write_tsv(a.out, rows)
    lines_total = sum(1 for u in units.values() for l in u["lines"] if l.strip())
    msg = [f"單位 {len(units)}，已譯 {len(got)}；行鍵 {len(rows)}（原文非空行 {lines_total}，去重前）",
           f"問題 {len(problems)}，衝突 {len(conflicts)}"] + problems + conflicts
    open(a.report, "w", encoding="utf-8").write("\n".join(msg) + "\n") if a.report else None
    print("\n".join(msg[:2]))
    for p in (problems + conflicts)[:30]:
        print(p)


if __name__ == "__main__":
    main()
