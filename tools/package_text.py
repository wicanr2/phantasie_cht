#!/usr/bin/env python3
"""依規格 013 §4 整理執行期譯文。只在 Docker 內執行。

輸出是封裝的中間輸入，不是正式交付包；不複製原版或字型。
預設完全不讀本機 manual catalog，僅保留兩個提示標題。
"""
import argparse
import hashlib
import json
import re
import shutil
import stat
from datetime import datetime
from pathlib import Path

import catalog_lib as cl

LANGUAGES = ("zh-TW", "zh-CN", "ja", "ko")
TITLES = frozenset(("prompt:item", "prompt:spell"))
HEADER = "key\ttranslation\tsource\n"


def version(value):
    if not re.fullmatch(r"v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}", value):
        raise ValueError("版號須為 v.<主版>.<次版>.<修訂版>-YYYYMMDD")
    try:
        datetime.strptime(value[-8:], "%Y%m%d")
    except ValueError as error:
        raise ValueError("版號日期無效") from error
    return value


def regular_bytes(path):
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError(f"輸入須為一般檔案：{path.name}")
    return path.read_bytes()


def catalog(path):
    data = regular_bytes(path)
    text = data.decode("utf-8")
    if any(ord(c) < 32 and c not in "\t\n" for c in text):
        raise ValueError(f"catalog 含控制字元：{path.name}")
    if not text.endswith("\n"):
        raise ValueError(f"catalog 缺尾端換行：{path.name}")
    # 保持正式檔的原始 bytes。共用讀取器只用於驗證跳脫及格式。
    rows = cl.read_tsv(str(path))
    keys = set()
    for row, key, translation, source in rows:
        if not key or not translation or not source or key in keys:
            raise ValueError(f"catalog 第 {row} 列缺必要欄位或重複鍵：{path.name}")
        keys.add(key)
    if not rows:
        raise ValueError(f"catalog 沒有資料：{path.name}")
    return data, rows


def manual_labels(path):
    data, rows = catalog(path)
    keys = {key for _, key, _, _ in rows}
    if keys != TITLES | {"answer"}:
        raise ValueError(f"手冊標籤鍵不符合規格：{path.name}")
    for _, key, translation, _ in rows:
        if key in TITLES and "%" in translation:
            raise ValueError(f"手冊標題不得含 placeholder：{path.name}")
    # 原始三欄按鍵選出，保留跳脫；不帶 answer 模板。
    lines = data.decode("utf-8").splitlines()
    selected = [line for line in lines[1:] if line.split("\t")[0] in TITLES]
    return (HEADER + "\n".join(selected) + "\n").encode("utf-8"), 2


def local_manual(path):
    data, rows = catalog(path)
    keys = {key for _, key, _, _ in rows}
    items = {key for key in keys if key.startswith("item:") and len(key) > 5}
    spells = {f"spell:{number}" for number in range(1, 55)}
    if len(items) != 100 or keys != TITLES | items | spells:
        raise ValueError(f"本機手冊表不完整或含非預期鍵：{path.name}")
    return data, len(rows)


def protected(path):
    data = regular_bytes(path)
    text = data.decode("utf-8")
    if not text.endswith("\n") or text.startswith("\ufeff") or "\r" in text:
        raise ValueError("protected.tsv 須為無 BOM 的 UTF-8、LF")
    lines = text.splitlines()
    if not lines or lines[0] != "key\tnote":
        raise ValueError("protected.tsv 欄名不符")
    keys = set()
    for line in lines[1:]:
        fields = line.split("\t")
        if len(fields) != 2 or not all(fields) or fields[0] in keys:
            raise ValueError("protected.tsv 缺欄位或重複鍵")
        if any(ord(c) < 32 for field in fields for c in field):
            raise ValueError("protected.tsv 含控制字元")
        keys.add(fields[0])
    if not keys:
        raise ValueError("protected.tsv 沒有資料")
    return data, len(keys)


def collect(source, local=False):
    """先驗證全部輸入，不寫輸出；未選取的檔案從未開啟。"""
    files, counts, source_keys = {}, {}, {}
    for language in LANGUAGES:
        for family in ("ui", "prose"):
            name = f"{family}.{language}.tsv"
            data, rows = catalog(source / name)
            keys = frozenset(key for _, key, _, _ in rows)
            if family in source_keys and source_keys[family] != keys:
                raise ValueError(f"四語鍵集合不同：{family}")
            source_keys[family] = keys
            files[name], counts[name] = data, len(rows)
        if local:
            data, count = local_manual(source / f"manual.{language}.tsv")
        else:
            data, count = manual_labels(source / f"manual-labels.{language}.tsv")
        name = f"manual.{language}.tsv"
        files[name], counts[name] = data, count
    files["protected.tsv"], counts["protected.tsv"] = protected(source / "protected.tsv")
    return files, counts


def prepare(source, output, release_version, local=False):
    release_version = version(release_version)
    source = Path(source)
    output = Path(output)
    if source.is_symlink() or not source.is_dir():
        raise ValueError("譯文來源須為實際目錄")
    source = source.resolve()
    if output.is_symlink() or output.exists():
        raise ValueError("輸出目錄必須尚不存在")
    if not output.parent.is_dir():
        raise ValueError("輸出父目錄必須存在")
    output = output.resolve()
    if source == output or source in output.parents or output in source.parents:
        raise ValueError("來源與輸出不得重疊")
    files, counts = collect(source, local)
    manifest = {
        "version": release_version,
        "scope": "runtime text staging only; not a delivery package",
        "rights": "local-only" if local else "no-original-or-manual-answers",
        "languages": list(LANGUAGES),
        "files": {name: {"bytes": len(data), "rows": counts[name],
                         "sha256": hashlib.sha256(data).hexdigest()}
                  for name, data in sorted(files.items())},
    }
    # mkdir 排他保留本次輸出；任何失敗只清理本次建立的目錄。
    output.mkdir(mode=0o755)
    try:
        text = output / "text"
        text.mkdir()
        for name, data in files.items():
            with (text / name).open("xb") as stream:
                stream.write(data)
        with (output / "runtime-text.json").open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(manifest, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        # 檢查實際寫入檔案及 bytes，不能只驗證預計複製的清單。
        if {path.name for path in text.iterdir()} != files.keys():
            raise ValueError("輸出含非預期檔案")
        if any((text / name).read_bytes() != data for name, data in files.items()):
            raise ValueError("輸出 bytes 與核對輸入不同")
    except BaseException:
        shutil.rmtree(output)
        raise
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="正式 text 目錄")
    parser.add_argument("--out", required=True, type=Path, help="尚不存在的中間輸出目錄")
    parser.add_argument("--version", required=True, help="已定案完整版號")
    parser.add_argument("--local-manual", action="store_true", help="明示本機專用答案變體")
    args = parser.parse_args()
    try:
        result = prepare(args.source, args.out, args.version, args.local_manual)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(1, f"譯文封裝失敗：{error}\n")
    print(json.dumps({"version": result["version"], "rights": result["rights"],
                      "files": len(result["files"]), "result": "PASS runtime text staging only"},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
