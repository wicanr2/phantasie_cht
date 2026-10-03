#!/usr/bin/env python3
"""譯文 catalog 的 lint（docs/spec/003 §10）。只在 Docker 內執行。

  python -B lint_catalog.py [--release] [--glossary text/glossary.tsv] [--protected text/protected.tsv] \
      [--font-tar unifont.tar.gz --font-member unifont-17.0.05/font/precompiled/unifont_t-17.0.05.hex] \
      [--sources workplace/text-enum/ui-candidates.tsv] \
      text/ui.zh-TW.tsv [text/prose.zh-TW.tsv ...]

同一次呼叫內的檔案視為同一語言的各家族（ui、prose）；鍵唯一在家族內檢查，ui 與 prose 之間檢查衝突。
違規印出並以非零離開。空譯文在草稿模式只計數，--release 才是錯誤。
"""
import argparse
import os
import re
import sys
import tarfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalog_lib as cl  # noqa: E402


def font_codepoints(tar_path, member):
    cps = set(range(0x20, 0x7F))
    t = tarfile.open(tar_path)
    for line in t.extractfile(member).read().decode().splitlines():
        if ":" in line:
            cps.add(int(line.split(":", 1)[0], 16))
    return cps


def conv_sig(s):
    """轉換序的簽章：類型（含 l）依序。"""
    return [("l" if ll else "") + conv for (_, _, _, ll, conv) in cl.convs(s)]


def has_english_literal(fmt: str) -> bool:
    """去掉轉換規格後仍含英文字母。"""
    return bool(re.search(r"[A-Za-z]", cl.CONV.sub("", fmt)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--release", action="store_true")
    ap.add_argument("--glossary")
    ap.add_argument("--protected")
    ap.add_argument("--font-tar")
    ap.add_argument("--font-member")
    ap.add_argument("--sources")
    a = ap.parse_args()
    errors, warns = [], []
    cps = None
    if a.font_tar:
        cps = font_codepoints(a.font_tar, a.font_member)
        cl.load_wide_from_hex(a.font_tar, a.font_member)
    glossary = []
    if a.glossary:
        for i, line in enumerate(open(a.glossary, encoding="utf-8")):
            if i == 0 or not line.strip():
                continue
            c = line.rstrip("\n").split("\t")
            glossary.append((c[0], c[1]))
    protected = set()
    if a.protected:
        for i, line in enumerate(open(a.protected, encoding="utf-8")):
            if i and line.strip():
                protected.add(line.split("\t")[0].rstrip())
    fam_keys = {}
    nonempty = {}
    empty = total = 0
    for path in a.files:
        fam = "prose" if os.path.basename(path).startswith("prose.") else "ui"
        try:
            rows = cl.read_tsv(path)
        except ValueError as e:
            errors.append(f"{path}: {e}")
            continue
        seen = fam_keys.setdefault(fam, {})
        for ln, key, tr, src in rows:
            total += 1
            where = f"{path}:{ln}"
            if not key:
                errors.append(f"{where}: 鍵是空的")
                continue
            if key in seen:
                errors.append(f"{where}: 鍵重複（另一筆在 {seen[key]}）")
            seen[key] = where
            if key in protected:
                errors.append(f"{where}: 保護清單的鍵不得出現在 catalog")
            if fam == "prose" and not re.fullmatch(r"h:[0-9a-f]{12}", key):
                errors.append(f"{where}: prose 的鍵要是 h: 加 12 位小寫十六進位")
            if fam == "ui" and key.startswith("h:"):
                errors.append(f"{where}: ui 的鍵不得以 h: 開頭")
            if not tr:
                empty += 1
                continue
            nonempty.setdefault(key, set()).add(fam)
            if tr == "<blank>":
                continue
            body = tr.replace(cl.CENTER, "")
            if cl.CENTER in tr[1:]:
                errors.append(f"{where}: 置中標記只能在開頭")
            if any(ord(c) < 0x20 for c in body):
                errors.append(f"{where}: 譯文含控制字元")
            if "" in body or "\\c" in tr.replace("\\\\", ""):
                pass
            if fam == "ui":
                if cl.has_bad_percent(key) or cl.has_bad_percent(body):
                    errors.append(f"{where}: 含不支援的轉換規格")
                    continue
                if conv_sig(key) != conv_sig(body):
                    errors.append(f"{where}: 轉換序不一致 原 {conv_sig(key)} 譯 {conv_sig(body)}")
                if cl.convs(key) and not has_english_literal(key) and body == key:
                    warns.append(f"{where}: 恆等模板（譯文等於鍵，沒有英文字面）冗餘")
            if cps is not None:
                for ch in sorted(set(body)):
                    if ord(ch) not in cps:
                        errors.append(f"{where}: 字型缺字 U+{ord(ch):04X} {ch}")
            # 寬度：譯文的半格寬度不超過原文格式化寬度的兩倍（ui；prose 由 prose_build 依單元實際長度檢查）
            if fam == "ui":
                en = cl.english_cells(key)
                zh_h = cl.sample_format(body, []) if cl.convs(body) else cl.width_h(body)
                if zh_h > 2 * en:
                    errors.append(f"{where}: 寬度超出 譯文 {zh_h}h > 原文 {en} 格（{2 * en}h）")
            # 術語（只涵蓋 ui）
            if glossary and fam == "ui":
                for en_term, zh_term in glossary:
                    if re.search(r"(?<![A-Za-z])" + re.escape(en_term) + r"(?![A-Za-z])", key, re.I) and zh_term not in body:
                        errors.append(f"{where}: 術語 {en_term} 應含「{zh_term}」")
    # ui 與 prose 同鍵（prose 鍵是 h: 開頭，不會與 ui 英文鍵相同）；同一規範化文字的衝突由 prose_build 檢查
    if a.sources:
        cand = set()
        for i, line in enumerate(open(a.sources, encoding="utf-8")):
            if i:
                cand.add(line.split("\t")[0])
        ui = set(fam_keys.get("ui", {}))
        for k in sorted(ui - cand):
            warns.append(f"孤兒鍵（不在靜態列舉）: {k!r}")
        for k in sorted(cand - ui - protected):
            warns.append(f"缺譯（靜態列舉有、ui 沒有）: {k!r}")
    if empty:
        (errors if a.release else warns).append(f"空譯文 {empty} 筆")
    for w in warns:
        print("警告:", w)
    for e in errors:
        print("錯誤:", e)
    print(f"共 {total} 筆，錯誤 {len(errors)}，警告 {len(warns)}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
