#!/usr/bin/env python3
"""013：核對實際封裝後寫入唯一交付根。平台冒煙另行驗證。"""
import argparse
import json
from pathlib import Path
import re
import shutil
import tarfile
import zipfile

import package_files as pf
import package_scan as ps
import package_stage as stage
import package_text as pt

RUNTIME_BYTES = 944632
RUNTIME_SHA = "0341f742081a99f00f6c8654d742e470e85c66dafabd17d851ab5b662dc7f511"


def relative_snapshot(path):
    return {name.split("/", 1)[1]: row for name, row in pf.snapshot(path).items() if name != path.name + "/"}


def verify(work, original, version, project_commit, engine_commit, font_license):
    work = pf.directory(work); pt.version(version)
    if font_license not in stage.FONT_TERMS: raise ValueError("字型條款須明示")
    source = json.loads(pf.file_bytes(work / "source-inputs.json"))
    for key, expected in (("version", version), ("project_commit", project_commit), ("engine_commit", engine_commit)):
        if source[key] != expected: raise ValueError("乾淨來源及交付版本不符")
    fingerprint = ps.originals(original, Path(__file__).resolve().parents[1] / "docs/re/001-input-inventory.tsv")
    if len(fingerprint) != 70: raise ValueError("固定原版掃描來源須為 70 檔")
    stages = sorted(pf.directory(work / "stage").iterdir())
    if not stages: raise ValueError("沒有平台布局")
    records, expected_artifacts = [], set()
    for folder in stages:
        folder = pf.directory(folder)
        meta = json.loads(pf.file_bytes(folder / "package-stage.json"))
        for key, expected in (("version", version), ("project_commit", project_commit), ("engine_commit", engine_commit), ("font_license", font_license)):
            if meta[key] != expected: raise ValueError("布局交付參數不符")
        platform = meta["platform"]
        local = meta["rights"] == "local-only"
        if meta["rights"] not in ("local-only", "no-original-or-manual-answers"): raise ValueError("布局權利分類不符")
        architecture = {"linux": "x86_64", "windows": "amd64", "macos": "universal"}[platform]
        variant = "full-local" if local else "patch"
        if folder.name != f"phantasie-cht-{version}-{platform}-{architecture}-{variant}":
            raise ValueError("封包名稱與平台、版本或權利不符")
        expected_files = {name: row for name, row in pf.snapshot(folder).items()
                          if not row["directory"] and name != folder.name + "/package-stage.json"}
        if meta["files"] != expected_files: raise ValueError("封裝前布局已變更")
        reference = work / "local-text" if local else None
        pf.bundle(folder, platform, version, engine_commit, reference, verify=True)
        base, _, _, _, _, original_dir = pf.profile(folder, platform)
        prefix = (base / original_dir).relative_to(folder).as_posix() if local else None
        artifact = work / "artifacts" / (folder.name + (".AppImage" if platform == "linux" else ".zip"))
        expected_artifacts.add(artifact.name)
        if platform == "linux":
            data = pf.file_bytes(artifact)
            squash = pf.file_bytes(work / (folder.name + ".squashfs"))
            if len(data) <= RUNTIME_BYTES or pf.digest(data[:RUNTIME_BYTES]) != RUNTIME_SHA or data[RUNTIME_BYTES:] != squash:
                raise ValueError("AppImage runtime 或實際 SquashFS 不符")
            extracted = pf.directory(work / "extracted" / folder.name / "squashfs-root")
            if relative_snapshot(folder) != relative_snapshot(extracted):
                raise ValueError("實際 AppImage 解出內容與布局不符")
            scan = ps.Scanner(fingerprint, prefix, reference).scan(extracted)
        else:
            pf.verify_zip(folder, artifact, version, platform)
            scan = ps.Scanner(fingerprint, folder.name + "/" + prefix if local else None, reference).scan(artifact)
        if scan["rights"] != meta["rights"]: raise ValueError("實際封裝權利分類不符")
        build = json.loads(pf.file_bytes(work / "build" / platform / "build-verification.json"))
        if build["version"] != version or build["engine_commit"] != engine_commit or build["platform"] != platform:
            raise ValueError("建置核對清冊不符")
        for row in build["binaries"].values():
            pr_data = pf.file_bytes(work / "build" / platform / row["name"])
            if len(pr_data) != row["bytes"] or pf.digest(pr_data) != row["sha256"]:
                raise ValueError("已核對的編譯輸出改變")
        suffix = ".exe" if platform == "windows" else ""
        launcher = base / ("MacOS/phantasie" if platform == "macos" else "phantasie" + suffix)
        backend = base / ("MacOS/phantasie-play" if platform == "macos" else "phantasie-play" + suffix)
        arch = "universal" if platform == "macos" else "amd64"
        for kind, path in (("launcher", launcher), ("backend", backend)):
            if pf.file_bytes(path) != pf.file_bytes(work / "build" / platform / f"{kind}-{arch}{suffix}"):
                raise ValueError("包內程式與本次編譯不符")
        for receipt_arch in (("amd64", "arm64") if platform == "macos" else ("amd64",)):
            name = f"phantasie-receipt-{receipt_arch}" if platform == "macos" else "phantasie-receipt" + suffix
            if pf.file_bytes(folder / "tools" / name) != pf.file_bytes(work / "build" / platform / f"receipt-{receipt_arch}{suffix}"):
                raise ValueError("包內收據工具與本次編譯不符")
        record = {**pf.record(artifact.name, pf.file_bytes(artifact)), "platform": platform, "architecture": architecture,
                  "rights": meta["rights"], "directory": variant, "scan": scan, "build": build,
                  "stage_manifest_sha256": pf.digest(pf.file_bytes(folder / "package-stage.json")),
                  "smoke": "pending; not CONFORMED"}
        records.append(record)
    if {path.name for path in pf.directory(work / "artifacts").iterdir()} != expected_artifacts:
        raise ValueError("封包集合含額外或缺失項目")
    return {"schema": 1, "version": version, "project_commit": project_commit, "engine_commit": engine_commit,
            "font_license": font_license, "status": "built and inspected; platform smoke pending",
            "input_archives": source["archives"], "packages": records,
            "toolchain": {"Go": "1.24.13", "macOS_deployment": "11.0", "SquashFS": "4.5.1", "Linux_compression": "gzip"},
            "limits": ["no public Release", "Windows requires package Wine smoke", "macOS native verification unavailable",
                       "Linux package five-language/save smoke pending", "no original same-state claim from package tools"]}


def finish(work, delivery, original, version, project_commit, engine_commit, font_license):
    delivery = pf.directory(delivery)
    work = pf.directory(work)
    output = delivery / pt.version(version)
    if output.exists(): raise ValueError("既有交付版本不得覆寫")
    for path in (work, pf.directory(original)):
        if output == path or output in path.parents or path in output.parents:
            raise ValueError("交付與來源不得重疊")
    result = verify(work, original, version, project_commit, engine_commit, font_license)
    output.mkdir()
    try:
        for package in result["packages"]:
            source = work / "artifacts" / package["name"]
            parent = output / package["directory"]; parent.mkdir(exist_ok=True)
            target = parent / source.name
            with target.open("xb") as stream: stream.write(pf.file_bytes(source))
            target.chmod(0o755 if target.suffix == ".AppImage" else 0o644)
            data = pf.file_bytes(target)
            if len(data) != package["bytes"] or pf.digest(data) != package["sha256"]:
                raise ValueError("交付副本與已核對封包不符")
        (output / "smoke").mkdir()
        with (output / "SHA256SUMS.json").open("x") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write("\n")
    except BaseException:
        shutil.rmtree(output)
        raise
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("work", "delivery", "original"): parser.add_argument("--" + name, type=Path, required=True)
    for name in ("version", "project-commit", "engine-commit", "font-license"): parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    try: result = finish(args.work, args.delivery, args.original, args.version, args.project_commit, args.engine_commit, args.font_license)
    except (OSError, ValueError, UnicodeError, KeyError, tarfile.TarError, zipfile.BadZipFile) as error: parser.exit(1, f"封包交付失敗：{error}\n")
    print(json.dumps({"result": "PASS built/inspected only; smoke pending", "version": result["version"], "packages": len(result["packages"])}, ensure_ascii=False))


if __name__ == "__main__": main()
