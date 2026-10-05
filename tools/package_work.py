#!/usr/bin/env python3
"""013：Docker 內的乾淨來源、編譯核對及交付清冊步驟。"""
import argparse
import json
from pathlib import Path
import re
import shutil
import tarfile

import package_files as pf
import package_rights as pr
import package_stage as stage
import package_text as pt


def export_sources(work, version, project_commit, engine_commit):
    work = pf.directory(work)
    pt.version(version)
    for commit in (project_commit, engine_commit):
        if not re.fullmatch(r"[0-9a-f]{40}", commit): raise ValueError("commit 須為完整 SHA")
    output = work / "source"
    index = work / "source-inputs.json"
    if output.exists() or index.exists(): raise ValueError("乾淨來源目錄或清冊已存在")
    archives = {}
    for name in ("project", "engine"):
        path = work / (name + ".tar")
        data = pf.file_bytes(path)
        archives[name] = pf.record(path.name, data)
        # 只處理 git archive 的一般檔案與目錄，不寫回原工作樹。
        with tarfile.open(path) as archive:
            seen = set()
            for member in archive.getmembers():
                stage.ps.path_parts(member.name)
                if member.name in seen or not (member.isfile() or member.isdir()):
                    raise ValueError("Git 匯出含重複或非一般項目")
                seen.add(member.name)
                if member.size > stage.ps.MAX_FILE: raise ValueError("匯出成員超限")
    output.mkdir()
    index_created = False
    try:
        for name in ("project", "engine"):
            with tarfile.open(work / (name + ".tar")) as archive:
                archive.extractall(output / name, filter="data")
        payload = {"version": version, "project_commit": project_commit, "engine_commit": engine_commit,
                   "archives": archives, "scope": "clean git exports only; no package acceptance"}
        with index.open("x") as stream:
            index_created = True
            json.dump(payload, stream, indent=2); stream.write("\n")
    except BaseException:
        shutil.rmtree(output)
        if index_created: index.unlink()
        raise
    return payload


def verify_build(work, platform, version, engine):
    work = pf.directory(work)
    pt.version(version)
    source = json.loads(pf.file_bytes(work / "source-inputs.json"))
    if source["version"] != version or source["engine_commit"] != engine:
        raise ValueError("編譯版本與乾淨來源不符")
    folder = pf.directory(work / "build" / platform)
    suffix = ".exe" if platform == "windows" else ""
    arches = ("amd64", "arm64") if platform == "macos" else ("amd64",)
    profiles = pr.load_profile()
    available = {re.match(r"(.+?)@([^/]+)/", row["source"]).groups()
                 for row in profiles["common"] if row["kind"] == "modules"}
    binaries, modules = {}, set()
    for arch in arches:
        for kind in ("launcher", "backend", "receipt"):
            path = folder / f"{kind}-{arch}{suffix}"
            data = pf.file_bytes(path)
            stage.binary(data, platform, arch, kind == "receipt")
            metadata = pf.file_bytes(folder / f"modules-{kind}-{arch}.txt").decode()
            if not metadata.splitlines()[0].endswith(": go1.24.13"):
                raise ValueError("二進位 Go 版本不符")
            package = ("github.com/wicanr2/phantasie_cht/launcher" if kind == "launcher" else
                       "github.com/wicanr2/dosgolem/apps/phantasie/cmd/phantasie-" + ("play" if kind == "backend" else "receipt"))
            fields = [line.strip().split("\t") for line in metadata.splitlines()[1:]]
            paths = [row[1] for row in fields if len(row) == 2 and row[0] == "path"]
            settings = [row[1].split("=", 1) for row in fields if len(row) == 2 and row[0] == "build" and "=" in row[1]]
            setting_map = dict(settings)
            if paths != [package]:
                raise ValueError("編譯工具或後端路徑不符")
            dependencies = {tuple(line.strip().split()[1:3]) for line in metadata.splitlines() if line.lstrip().startswith("dep\t")}
            if not dependencies <= available: raise ValueError("編入未收錄條款的模組版本")
            if len(setting_map) != len(settings) or setting_map.get("GOARCH") != arch or setting_map.get("GOOS") != ("darwin" if platform == "macos" else platform):
                raise ValueError("Go build info 架構不符")
            # Go 1.24.13 的 trimpath 明確省略 -ldflags build setting。
            # 啟動器才有正式版本變數；其餘程式以匯出及實際 bytes 定位。
            if kind == "launcher" and (version.encode() not in data or engine.encode() not in data):
                raise ValueError("啟動器未帶完整版本及引擎字串")
            modules |= dependencies
            binaries[path.name] = pf.record(path.name, data)
    if platform == "macos":
        for kind in ("launcher", "backend"):
            path = folder / f"{kind}-universal"; data = pf.file_bytes(path)
            stage.binary(data, platform, "universal")
            # universal 每片必須是本次實際 thin bytes，不能只接受 CPU 標頭。
            import struct
            slices = {}
            for i in range(2):
                cpu, _, offset, size, _ = struct.unpack_from(">IIIII", data, 8 + 20 * i)
                slices["amd64" if cpu == 0x01000007 else "arm64"] = data[offset:offset + size]
            for arch in arches:
                if slices[arch] != pf.file_bytes(folder / f"{kind}-{arch}"):
                    raise ValueError("universal 與本次 thin bytes 不符")
            binaries[path.name] = pf.record(path.name, data)
    result = {"scope": "offline compilation/header/module checks only; not delivery or GUI", "platform": platform,
              "version": version, "engine_commit": engine, "binaries": binaries, "modules": sorted(modules)}
    if platform == "linux":
        expected = f"{version}\n引擎 {engine}\n"
        if pf.file_bytes(folder / "launcher-version.txt").decode() != expected:
            raise ValueError("實際啟動器版本輸出不符")
        dynamic = pf.file_bytes(folder / "backend-dynamic.txt").decode()
        needed = re.findall(r"\(NEEDED\).*?\[([^]]+)\]", dynamic)
        if set(needed) != {"libX11.so.6", "libm.so.6", "libc.so.6"}:
            raise ValueError("Linux 直接附庫改變，須回到工具鏈證據核對")
        text = pf.file_bytes(folder / "backend-symbol-versions.txt").decode()
        versions = {tuple(map(int, v.split("."))) for v in re.findall(r"GLIBC_([0-9]+(?:\.[0-9]+)+)", text)}
        if not versions: raise ValueError("沒有取得 glibc 符號需求")
        result["linux_direct_dependencies"] = sorted(needed)
        result["maximum_glibc_symbol"] = ".".join(map(str, max(versions)))
    with (folder / "build-verification.json").open("x") as stream: json.dump(result, stream, indent=2); stream.write("\n")
    return result


def local_text(project, reference, output):
    output = pf.no_links(output)
    if output.exists() or not output.parent.is_dir(): raise ValueError("本機譯文中間輸出須為新目錄")
    project, reference = pf.directory(project), pf.directory(reference)
    if any(output == path or output in path.parents or path in output.parents for path in (project, reference)):
        raise ValueError("本機譯文來源與輸出重疊")
    payload, _ = pt.collect(project / "text")
    for language in pt.LANGUAGES:
        name = f"manual.{language}.tsv"
        payload[name] = pt.local_manual(reference / name)[0]
    output.mkdir()
    try:
        for name, data in payload.items():
            with (output / name).open("xb") as stream: stream.write(data)
    except BaseException:
        shutil.rmtree(output)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("export", "verify-build", "local-text"))
    parser.add_argument("--work", type=Path)
    parser.add_argument("--version")
    parser.add_argument("--project-commit")
    parser.add_argument("--engine-commit")
    parser.add_argument("--platform", choices=("linux", "windows", "macos"))
    parser.add_argument("--project", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    required = {"export": ("work", "version", "project_commit", "engine_commit"),
                "verify-build": ("work", "version", "engine_commit", "platform"),
                "local-text": ("project", "reference", "out")}[args.action]
    if any(getattr(args, name) is None for name in required): parser.error("此動作缺必要參數")
    try:
        if args.action == "export": result = export_sources(args.work, args.version, args.project_commit, args.engine_commit)
        elif args.action == "verify-build": result = verify_build(args.work, args.platform, args.version, args.engine_commit)
        else: local_text(args.project, args.reference, args.out); result = {"scope": "local text staging only"}
    except (OSError, ValueError, UnicodeError, KeyError, tarfile.TarError) as error:
        parser.exit(1, f"封包工作步驟失敗：{error}\n")
    print(json.dumps({"result": "PASS " + result["scope"]}, ensure_ascii=False))


if __name__ == "__main__": main()
