#!/usr/bin/env python3
"""由本機核對表產生手冊提示，答案不內嵌。Docker 內執行，見規格 006。"""
import argparse
import pathlib
import re

import catalog_lib as cl

LANGUAGES = ("zh-TW", "zh-CN", "ja", "ko")


def table(path):
    result = {}
    for _, key, value, source in cl.read_tsv(str(path)):
        if key in result or not value or not source:
            raise ValueError(f"{path.name}：重複鍵、空值或缺少來源")
        if any(ord(c) < 32 or ord(c) == 127 or c == cl.CENTER for c in value):
            raise ValueError(f"{path.name}：不接受控制字元或置中標記")
        result[key] = (value, source)
    return result


def reference(path):
    rows = table(path)
    items, spells = set(), set()
    for key, (value, _) in rows.items():
        if key.startswith("item:") and re.fullmatch(r"[ -~]+", key[5:]):
            if not re.fullmatch(r"[1-9][0-9]*", value) or not 1 <= int(value) <= 100:
                raise ValueError("物品編號不在 1 至 100")
            if int(value) in items:
                raise ValueError("物品編號重複")
            items.add(int(value))
        elif key.startswith("spell:") and re.fullmatch(r"[1-9][0-9]*", key[6:]):
            if not 1 <= int(key[6:]) <= 54 or not re.fullmatch(r"[ -~]+", value):
                raise ValueError("法術編號或名稱不合法")
            spells.add(int(key[6:]))
        else:
            raise ValueError("核對表含不支援的鍵")
    if items != set(range(1, 101)) or spells != set(range(1, 55)):
        raise ValueError("核對表須包含 100 個物品及 54 個法術")
    return rows


def bounded(value, cells):
    # 保守檢查：非 ASCII 全按全形算；執行期再以 GOLEMFNT 實際寬度與字模檢查。
    if any(ord(c) < 32 or ord(c) == 127 or c == cl.CENTER for c in value):
        raise ValueError("提示含控制字元")
    if sum(1 if ord(c) < 128 else 2 for c in value) > cells:
        raise ValueError("提示超出原事件安全寬度")


def build(rows, text_dir, lang):
    labels = table(text_dir / f"manual-labels.{lang}.tsv")
    if set(labels) != {"prompt:item", "prompt:spell", "answer"}:
        raise ValueError("手冊標籤須有兩種題型與答案句型")
    if any("%" in labels[key][0] for key in ("prompt:item", "prompt:spell")):
        raise ValueError("題型標題不得含 placeholder")
    pattern = labels["answer"][0]
    if pattern.count("%s") != 1 or "%" in pattern.replace("%s", ""):
        raise ValueError("答案句型須有且只有一個 %s")
    ui = {key: (value, source) for _, key, value, source in cl.read_tsv(str(text_dir / f"ui.{lang}.tsv"))}
    out = ["key\ttranslation\tsource"]

    def add(key, value, source, cells):
        bounded(value, cells)
        out.append("\t".join(cl.escape(s) for s in (key, value, source)))

    add("prompt:item", *labels["prompt:item"], 56)
    add("prompt:spell", *labels["prompt:spell"], 30)
    for key, (value, source) in rows.items():
        if key.startswith("spell:"):
            if value not in ui:
                raise ValueError(f"{lang}：法術名稱在既有 catalog 中缺譯")
            value = ui[value][0]
            if not value.strip() or value == "<blank>":
                raise ValueError(f"{lang}：法術名稱在既有 catalog 中為空")
            cells = len(f"of spell {key[6:]}? (back cover)") * 2
        else:
            cells = len(f"{key[5:]}? (page 15,16)") * 2
        add(key, pattern.replace("%s", value), source, cells)
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True, type=pathlib.Path)
    parser.add_argument("--text", default="text", type=pathlib.Path)
    args = parser.parse_args()
    rows = reference(args.reference)
    outputs = {lang: build(rows, args.text, lang) for lang in LANGUAGES}
    for lang, output in outputs.items():
        (args.text / f"manual.{lang}.tsv").write_text(output, encoding="utf-8")
    print("PASS：四語手冊提示各 156 筆，答案表限本機")


if __name__ == "__main__":
    main()
