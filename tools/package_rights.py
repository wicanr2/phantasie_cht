#!/usr/bin/env python3
"""013 §4 的全文條款與來源中間輸入。只在 Docker 執行。

只收錄固定公開輸入及模組的來源聲明，不複製字型，不選散布條款。
這不是正式封包、法律審查或完整權利通過的證明。
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tarfile

import package_files as pf

PROFILE = Path(__file__).with_name("package_licenses.json")


def fingerprint(data, row):
    if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
        raise ValueError("授權或來源輸入與固定清單不符：" + row["name"])
    return data


def load_profile():
    profile = json.loads(pf.file_bytes(PROFILE))
    if profile["schema"] != 1 or len(profile["common"]) != 20 or len(profile["runtime"]) != 13:
        raise ValueError("固定授權清單不符")
    return profile


def leading_notice(data):
    """完整保留檔首連續註解；不是對整個來源作授權分類。"""
    text = data.decode("utf-8-sig")
    lines, selected, block = text.splitlines(), [], False
    for line in lines:
        stripped = line.lstrip()
        if not stripped:
            selected.append(line)
        elif block:
            if "*/" in line:
                comment, remainder = line.split("*/", 1)
                selected.append(comment + "*/")
                block = False
                if remainder.strip():
                    break
            else:
                selected.append(line)
        elif stripped.startswith("//"):
            selected.append(line)
        elif stripped.startswith("/*"):
            if "*/" in line:
                comment, remainder = line.split("*/", 1)
                selected.append(comment + "*/")
                if remainder.strip():
                    break
            else:
                selected.append(line)
                block = True
        else:
            break
    notice = "\n".join(selected).strip()
    if block:
        raise ValueError("來源檔首註解未結束")
    return notice if re.search(r"copyright|SPDX-|permission|license", notice, re.I) else ""


def module_notices(modules, names):
    result = []
    for name in sorted(names):
        root = pf.directory(modules / name)
        for path in sorted(root.rglob("*")):
            if path.is_symlink():
                raise ValueError("模組來源含符號連結")
            if not path.is_file() or path.suffix not in (".go", ".c", ".h", ".m", ".s", ".S"):
                continue
            data = pf.file_bytes(path)
            notice = leading_notice(data)
            if notice:
                result.append({"module": name, "file": path.relative_to(root).as_posix(),
                               "source_sha256": hashlib.sha256(data).hexdigest(), "notice": notice})
    return result


def unifont_notices(path, profile):
    data = pf.file_bytes(path)
    if hashlib.sha256(data).hexdigest() != profile["unifont_sha256"]:
        raise ValueError("Unifont 來源壓縮檔不符")
    result = {}
    with tarfile.open(path) as archive:
        for name in ("COPYING", "OFL-1.1.txt", "font/Makefile"):
            member = archive.getmember("unifont-17.0.05/" + name)
            if not member.isfile() or member.size > 1024 * 1024:
                raise ValueError("Unifont 授權成員型態不符")
            with archive.extractfile(member) as source:
                result[name] = source.read()
    if hashlib.sha256(result["font/Makefile"]).hexdigest() != profile["unifont_makefile_sha256"]:
        raise ValueError("Unifont 作者來源不符")
    lines = result["font/Makefile"].decode().splitlines()
    position = next(i for i, line in enumerate(lines) if line.startswith("COPYRIGHT ="))
    selected = []
    while position < len(lines):
        line = lines[position]; selected.append(line); position += 1
        if not line.rstrip().endswith("\\"):
            break
    result["author-source"] = ("\n".join(selected) + "\n").encode()
    return result


def prepare(output, project, engine, modules, go_license, unifont, runtime=None, runtime_source=None):
    output = pf.no_links(output)
    if output.exists() or not output.parent.is_dir():
        raise ValueError("授權輸出須為尚不存在的目錄，父目錄須存在")
    project, engine, modules = map(pf.directory, (project, engine, modules))
    sources = [project, engine, modules, pf.no_links(go_license), pf.no_links(unifont)]
    if bool(runtime) != bool(runtime_source):
        raise ValueError("runtime 目錄及來源包須同時明示")
    if runtime:
        runtime = pf.directory(runtime)
        sources += [runtime, pf.no_links(runtime_source)]
    if any(output == path or path in output.parents or output in path.parents for path in sources):
        raise ValueError("授權來源與輸出不得重疊")
    profile = load_profile()
    font = unifont_notices(unifont, profile)
    payloads = {}
    for row in profile["common"]:
        kind = row["kind"]
        if kind == "unifont":
            data = font[row["source"]]
        else:
            path = {"project": project / row["source"], "engine": engine / row["source"],
                    "modules": modules / row["source"], "go": Path(go_license)}[kind]
            data = pf.file_bytes(path)
        payloads["common/" + row["name"]] = fingerprint(data, row)
    # root 由 module@version 前綴識別，避免巢狀 LICENSE.md 被當成新模組。
    module_roots = {re.match(r"(.+?@[^/]+)/", row["source"]).group(1)
                    for row in profile["common"] if row["kind"] == "modules"}
    notices = module_notices(modules, module_roots)
    payloads["common/module-source-notices.json"] = (json.dumps({"scope": "leading source comments only; full terms retained separately",
        "modules": sorted(module_roots), "notices": notices}, ensure_ascii=False, indent=2) + "\n").encode()
    if runtime:
        for row in profile["runtime"]:
            payloads["runtime/" + row["name"]] = fingerprint(pf.file_bytes(runtime / row["source"]), row)
        row = profile["runtime_source"]
        payloads["runtime/" + row["name"]] = fingerprint(pf.file_bytes(runtime_source), row)
    index = {"schema": 1, "scope": "license/source staging only; no font distribution or election",
             "font_terms": "pending user election", "profile_sha256": hashlib.sha256(pf.file_bytes(PROFILE)).hexdigest(),
             "module_header_notices": len(notices), "with_runtime": bool(runtime),
             "files": [pf.record(name, data) for name, data in sorted(payloads.items())]}
    output.mkdir()
    try:
        for name, data in payloads.items():
            path = output / name; path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream: stream.write(data)
        with (output / "rights-inputs.json").open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(index, stream, ensure_ascii=False, indent=2); stream.write("\n")
        for row in index["files"]:
            fingerprint(pf.file_bytes(output / row["name"]), row)
    except BaseException:
        shutil.rmtree(output)
        raise
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("out", "project", "engine", "modules", "go-license", "unifont"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--runtime-source", type=Path)
    args = parser.parse_args()
    try:
        result = prepare(args.out, args.project, args.engine, args.modules, args.go_license, args.unifont, args.runtime, args.runtime_source)
    except (OSError, ValueError, UnicodeError, KeyError, StopIteration, tarfile.TarError) as error:
        parser.exit(1, f"授權材料整理失敗：{error}\n")
    print(json.dumps({"result": "PASS license/source staging only", "files": len(result["files"]),
                      "module_header_notices": result["module_header_notices"], "font_terms": result["font_terms"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
