#!/usr/bin/env python3
"""譯文 catalog 的 lint（docs/spec/003 §10）。只在 Docker 內執行。

  python -B lint_catalog.py [--release] [--glossary text/glossary.tsv] [--protected text/protected.tsv] \
      [--font-tar unifont.tar.gz --font-member unifont-17.0.05/font/precompiled/unifont_t-17.0.05.hex] \
      [--sources workplace/text-enum/ui-candidates.tsv] [--harvest workplace/harvest/texts.tsv] \
      text/ui.zh-TW.tsv [text/prose.zh-TW.tsv ...]

同一次呼叫內的檔案視為同一語言的各家族（ui、prose）；鍵唯一在家族內檢查，ui 與 prose 之間檢查衝突。
讀原始行：鍵或譯文有尾端空白、壞跳脫、欄數錯誤都以「該列」為單位報錯並繼續。
違規印出並以非零離開。空譯文在草稿模式只計數，--release 才是錯誤。
"""
import argparse
import hashlib
import os
import re
import sys
import tarfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalog_lib as cl  # noqa: E402

EDGE_TOLERANCE_H = 2
# 一般詞：在句子裡常作動詞或普通名詞，詞表只在鍵恰為該詞時強制（日文、韓文的活用與詞序使「含譯詞」的檢查不適用）
GENERIC = {"exit", "option", "bank", "inn", "guild", "armory"}


def font_codepoints(tar_path, member):
    cps = set(range(0x20, 0x7F))
    t = tarfile.open(tar_path)
    for line in t.extractfile(member).read().decode().splitlines():
        if ":" in line:
            cps.add(int(line.split(":", 1)[0], 16))
    return cps


def conv_sig(s):
    """轉換序的簽章（依序）：旗標 -、精度、l、類型；寬度不比（可為對齊右緣而調整，003 §7.2）。"""
    return [(left, prec, ll, conv) for (left, _w, prec, ll, conv) in cl.convs(s)]


def has_english_literal(fmt: str) -> bool:
    """去掉轉換規格後仍含英文字母。"""
    return bool(re.search(r"[A-Za-z]", cl.CONV.sub("", fmt)))


def prose_key(text: str) -> str:
    return "h:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--release", action="store_true")
    ap.add_argument("--glossary")
    ap.add_argument("--protected")
    ap.add_argument("--font-tar")
    ap.add_argument("--font-member")
    ap.add_argument("--sources")
    ap.add_argument("--harvest")
    a = ap.parse_args()
    errors, warns = [], []
    cps = None
    if a.font_tar:
        cps = font_codepoints(a.font_tar, a.font_member)
        cl.load_wide_from_hex(a.font_tar, a.font_member)
    else:
        warns.append("沒有指定字型表（--font-tar），字元寬度以碼點範圍估計，不可靠（003 §10）")
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
    fam_rows = {"ui": {}, "prose": {}}  # 規範化鍵 -> (where, 譯文)
    ui_src = {}  # ui 鍵 -> source 欄
    empty = total = 0
    for path in a.files:
        fam = "prose" if os.path.basename(path).startswith("prose.") else "ui"
        row_errs = []
        try:
            rows = cl.read_tsv(path, row_errs)
        except OSError as e:
            errors.append(f"{path}: {e}")
            continue
        for ln, msg in row_errs:
            errors.append(f"{path}:{ln}: {msg}")
        seen = fam_rows[fam]
        for ln, key, tr, src in rows:
            total += 1
            where = f"{path}:{ln}"
            if not key:
                errors.append(f"{where}: 鍵是空的")
                continue
            if key in seen:
                errors.append(f"{where}: 鍵重複（規範化後，另一筆在 {seen[key][0]}）")
            seen[key] = (where, tr)
            if fam == "ui":
                ui_src[key] = src
            if key in protected:
                errors.append(f"{where}: 保護清單的鍵不得出現在 catalog")
            if fam == "prose" and not re.fullmatch(r"h:[0-9a-f]{12}", key):
                errors.append(f"{where}: prose 的鍵要是 h: 加 12 位小寫十六進位")
            if fam == "ui":
                if key.startswith("h:"):
                    errors.append(f"{where}: ui 的鍵不得以 h: 開頭")
                if any(ord(c) < 0x20 or ord(c) > 0x7E for c in key):
                    errors.append(f"{where}: ui 的鍵含 20h 至 7Eh 以外的字元")
            if not tr:
                empty += 1
                continue
            centered = tr.startswith(cl.CENTER)
            body = tr[1:] if centered else tr
            if cl.CENTER in body:
                errors.append(f"{where}: 置中標記只能在開頭，且只能出現一次")
                body = body.replace(cl.CENTER, "")
            if "<blank>" in body and body != "<blank>":
                errors.append(f"{where}: <blank> 只能是整句譯文，不得在模板內或與其他文字並用")
            if body == "<blank>":
                if centered:
                    errors.append(f"{where}: <blank> 不得與置中標記並用")
                continue
            if any(ord(c) < 0x20 or ord(c) == 0x7F for c in body):
                errors.append(f"{where}: 譯文含控制字元")
            if fam == "ui":
                bad_key, bad_tr = cl.has_bad_percent(key), cl.has_bad_percent(body)
                if bad_key or bad_tr:
                    errors.append(f"{where}: 含不支援的轉換規格（{'鍵' if bad_key else '譯文'}）")
                    continue
                if conv_sig(key) != conv_sig(body):
                    errors.append(f"{where}: 轉換序或精度、旗標不一致 原 {conv_sig(key)} 譯 {conv_sig(body)}")
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
                # 欄位右緣：有明寫寬度的轉換，原文與譯文的右緣差超過容差時警告
                if cl.convs(key):
                    en_edges = cl.field_right_edges(key, [], True)
                    zh_edges = cl.field_right_edges(body, [], False)
                    for i, ((e_en, w_en), (e_zh, _)) in enumerate(zip(en_edges, zh_edges)):
                        if w_en and abs(e_en - e_zh) > EDGE_TOLERANCE_H:
                            warns.append(f"{where}: 第 {i + 1} 個欄位右緣 原 {e_en}h 譯 {e_zh}h，差超過 {EDGE_TOLERANCE_H}h")
            # 術語（只涵蓋 ui）
            if glossary and fam == "ui":
                for en_term, zh_term in glossary:
                    if en_term.lower() in GENERIC and key.strip().lower() != en_term.lower():
                        continue
                    if re.search(r"(?<![A-Za-z])" + re.escape(en_term) + r"(?![A-Za-z])", key, re.I) and zh_term not in body:
                        errors.append(f"{where}: 術語 {en_term} 應含「{zh_term}」")
    # ui 與 prose 同一規範化文字同時有非空譯文：譯文不同為錯誤（ui 優先，但兩處不一致表示維護錯誤），相同為警告
    prose_by_key = fam_rows["prose"]
    for key, (where, tr) in sorted(fam_rows["ui"].items()):
        if not tr:
            continue
        pk = prose_key(key)
        if pk in prose_by_key and prose_by_key[pk][1]:
            other_where, other_tr = prose_by_key[pk]
            if other_tr.replace(cl.CENTER, "") != tr.replace(cl.CENTER, ""):
                errors.append(f"{where}: 與 {other_where} 同一規範化文字在 ui 與 prose 譯文不同")
            else:
                warns.append(f"{where}: 與 {other_where} 同文同譯（ui 與 prose 重複）")
    if a.sources:
        cand = set()
        for i, line in enumerate(open(a.sources, encoding="utf-8")):
            if i:
                cand.add(line.split("\t")[0])
        ui = set(fam_rows["ui"])
        for k in sorted(ui - cand):
            if not any(t.startswith(("res:", "ov1:", "ov2:")) for t in ui_src.get(k, "").split(";")):
                continue  # 動態變體（dyn）與資料檔字串（TWNS.DAT）本來就不在靜態列舉內
            warns.append(f"孤兒鍵（不在靜態列舉）: {k!r}")
        for k in sorted(cand - ui - protected):
            warns.append(f"缺譯（靜態列舉有、ui 沒有）: {k!r}")
    if a.harvest:
        ui = set(fam_rows["ui"])
        for i, line in enumerate(open(a.harvest, encoding="utf-8")):
            if i == 0:
                continue
            cnt, cls, in_static, text = line.rstrip("\n").split("\t", 3)
            t = eval(text).rstrip()  # 動態蒐集的 repr，來源是自己的工具輸出
            if in_static != "Y" or not re.search(r"[A-Za-z]", t) or t in protected:
                continue
            if t not in ui:
                errors.append(f"動態缺譯：in_static=Y 的字串不在 ui: {t!r}（出現 {cnt} 次）")
    # 原地改寫的兩極性（003 §10、001 §4 的 P 類）：+X 與 -X 要成對
    ui_keys = set(fam_rows["ui"])
    for k in sorted(ui_keys):
        if re.match(r"[+-][A-Za-z]", k):
            other = ("-" if k[0] == "+" else "+") + k[1:]
            if other not in ui_keys:
                errors.append(f"開關標籤 {k!r} 缺相反極性的鍵 {other!r}（001 §4 P 類）")
    if a.release:
        for opt, name in ((a.font_tar, "--font-tar"), (a.glossary, "--glossary"), (a.protected, "--protected")):
            if not opt:
                errors.append(f"--release 要求指定 {name}")
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
