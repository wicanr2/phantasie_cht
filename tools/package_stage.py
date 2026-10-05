#!/usr/bin/env python3
"""013：從固定材料組裝三平台中間布局。只在 Docker 內執行。

必須明示已選定的字型條款；無預設。正式 tag、乾淨建置及平台冒煙由編排層核對。
"""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import shutil
import struct
import subprocess
import sys
import tarfile

import package_files as pf
import package_rights as pr
import package_scan as ps
import package_text as pt
import build_eten_font as eten_font

FONT_MEMBERS = {
    "zh-TW": ("unifont_t-17.0.05.hex", "169634258e4037b507beaafad5d72edc2e44b3faeaa856d9669e4657d1eee454"),
    "zh-CN": ("unifont-17.0.05.hex", "fd79af3613ec1b984a98d33428fdd43fcf06018d18059960d78edeb63d958622"),
    "ja": ("unifont_jp-17.0.05.hex", "3e88e5e98470e7547555202cebb13bcd4c393d417e2296a0f0f8adade7d37f43"),
    "ko": ("unifont-17.0.05.hex", "fd79af3613ec1b984a98d33428fdd43fcf06018d18059960d78edeb63d958622"),
}
FONT_TERMS = ("OFL-1.1", "GPL-2.0-or-later-with-font-exception")
ICON = b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><rect width="64" height="64" fill="#000"/><path fill="#0ff" d="M16 12h32v24H24v16h-8zm8 8v8h16v-8z"/></svg>\n'
APPRUN = b'#!/bin/sh\nset -eu\napp_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexec "$app_dir/usr/bin/phantasie" "$@"\n'


def binary(data, platform, architecture="amd64", console=False):
    """只核對標頭與 universal 邊界，不等於可啟動性／ABI 驗證。"""
    if platform == "linux":
        if len(data) < 64 or data[:6] != b"\x7fELF\x02\x01" or struct.unpack_from("<H", data, 18)[0] != 62:
            raise ValueError("Linux 二進位須為 ELF x86-64")
    elif platform == "windows":
        if len(data) < 64 or data[:2] != b"MZ": raise ValueError("Windows 二進位標頭不符")
        offset = struct.unpack_from("<I", data, 60)[0]
        if offset < 64 or offset + 96 > len(data) or data[offset:offset + 4] != b"PE\0\0":
            raise ValueError("Windows PE 邊界不符")
        if (struct.unpack_from("<H", data, offset + 4)[0] != 0x8664 or
            struct.unpack_from("<H", data, offset + 24)[0] != 0x20B or
            struct.unpack_from("<H", data, offset + 24 + 68)[0] != (3 if console else 2)):
            raise ValueError("Windows 架構或子系統不符")
    elif platform == "macos":
        if architecture in ("amd64", "arm64"):
            cpu = 0x01000007 if architecture == "amd64" else 0x0100000C
            if len(data) < 32 or data[:4] != bytes.fromhex("cffaedfe") or struct.unpack_from("<I", data, 4)[0] != cpu:
                raise ValueError("macOS thin 架構不符")
        else:
            if len(data) < 48 or data[:4] != bytes.fromhex("cafebabe") or struct.unpack_from(">I", data, 4)[0] != 2:
                raise ValueError("macOS 須為雙架構 universal")
            cpus, ranges = set(), []
            for i in range(2):
                cpu, _, offset, size, alignment = struct.unpack_from(">IIIII", data, 8 + 20 * i)
                if cpu not in (0x01000007, 0x0100000C) or cpu in cpus or size < 32 or offset < 48 or offset + size > len(data) or alignment > 31 or offset % (1 << alignment):
                    raise ValueError("macOS universal slice 邊界不符")
                cpus.add(cpu); ranges.append((offset, offset + size))
                binary(data[offset:offset + size], "macos", "amd64" if cpu == 0x01000007 else "arm64")
            if max(ranges[0][0], ranges[1][0]) < min(ranges[0][1], ranges[1][1]):
                raise ValueError("macOS universal slices 重疊")
    else:
        raise ValueError("平台不符")


def rights_files(root, with_runtime):
    root = pf.directory(root)
    profile = pr.load_profile()
    index = json.loads(pf.file_bytes(root / "rights-inputs.json"))
    if index["schema"] != 1 or index["profile_sha256"] != pf.digest(pf.file_bytes(pr.PROFILE)):
        raise ValueError("授權材料清冊與固定版本不符")
    expected = {"common/" + row["name"] for row in profile["common"]} | {"common/module-source-notices.json"}
    if index["with_runtime"]:
        expected |= {"runtime/" + row["name"] for row in profile["runtime"]} | {"runtime/" + profile["runtime_source"]["name"]}
    elif with_runtime:
        raise ValueError("Linux 缺 runtime 條款及配套來源")
    rows = index["files"]
    if len(rows) != len(expected) or {row["name"] for row in rows} != expected:
        raise ValueError("授權材料項目集合不符")
    all_files = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    if all_files != expected | {"rights-inputs.json"}:
        raise ValueError("授權材料含額外或缺失檔案")
    payloads = {row["name"]: pr.fingerprint(pf.file_bytes(root / row["name"]), row) for row in rows}
    for row in profile["common"]:
        pr.fingerprint(payloads["common/" + row["name"]], row)
    if index["with_runtime"]:
        for row in profile["runtime"]:
            pr.fingerprint(payloads["runtime/" + row["name"]], row)
        row = profile["runtime_source"]
        pr.fingerprint(payloads["runtime/" + row["name"]], row)
    notices = json.loads(payloads["common/module-source-notices.json"])
    modules = sorted({re.match(r"(.+?@[^/]+)/", row["source"]).group(1) for row in profile["common"] if row["kind"] == "modules"})
    if notices["modules"] != modules or len(notices["notices"]) != index["module_header_notices"]:
        raise ValueError("模組作者聲明清冊不符")
    return {name: data for name, data in payloads.items() if name.startswith("common/") or with_runtime}, index


def font_sources(path):
    profile = pr.load_profile()
    if pf.digest(pf.file_bytes(path)) != profile["unifont_sha256"]:
        raise ValueError("字型來源壓縮檔不符")
    with tarfile.open(path) as archive:
        for name, expected in set(FONT_MEMBERS.values()):
            member = archive.getmember("unifont-17.0.05/font/precompiled/" + name)
            if not member.isfile() or member.size > ps.MAX_FILE:
                raise ValueError("字型來源成員型態或大小不符")
            with archive.extractfile(member) as stream: data = stream.read()
            if pf.digest(data) != expected:
                raise ValueError("字型 hex 成員與固定來源不符")


def validate_fonts(base, font_dir, fonts, local, font_license):
    """字型來源紀錄須與實際字模一致；來源2只許本機繁中。"""
    if set(fonts) != set(pt.LANGUAGES):
        raise ValueError("字型來源紀錄語言集合不符")
    for language, row in fonts.items():
        data = pf.file_bytes(base / font_dir / (language + ".golemfnt"))
        actual_hash = pf.digest(data)
        count = pf.font_coverage(data, set(range(32, 127)), local and language == "zh-TW")
        if row.get("sha256") != actual_hash:
            raise ValueError("字型來源紀錄與產物 SHA-256 不符")
        if row.get("source") == "GNU Unifont 17.0.05":
            if row != {"source": "GNU Unifont 17.0.05", "terms": font_license, "sha256": actual_hash}:
                raise ValueError("GNU 字型來源紀錄不符")
            pf.font_coverage(data, set())  # 本機 GNU 也不能誤帶來源2。
        elif row.get("source") == "ETEN local fullwidth with GNU ASCII":
            if not local or language != "zh-TW" or row.get("rights") != "local-only" or row.get("terms_gnu_ascii") != font_license:
                raise ValueError("倚天來源紀錄只許本機繁中")
            provenance = row.get("eten", {})
            expected_sources = {name: {"bytes": size, "sha256": sha} for name, (size, sha) in eten_font.SOURCES.items()}
            expected = {"schema": 1, "scope": "local-only ETEN fullwidth; GNU ASCII retains selected terms",
                        "glyphs": count, "eten_fullwidth": count - 95, "gnu_ascii": 95,
                        "source_height": 15, "canvas": [16, 16], "sources": expected_sources, "sha256": actual_hash}
            if {key: value for key, value in provenance.items() if key != "base_font_sha256"} != expected or not re.fullmatch(r"[0-9a-f]{64}", provenance.get("base_font_sha256", "")):
                raise ValueError("倚天字模來源、尺寸或字數紀錄不符")
            if set(row) != {"source", "rights", "terms_gnu_ascii", "sha256", "eten"}:
                raise ValueError("倚天來源紀錄含未知欄位")
            for offset in range(16, len(data), 37):
                cp, flag = struct.unpack_from("<IB", data, offset)
                if not ((32 <= cp <= 126 and flag == 1) or (cp >= 128 and flag == 0x82)):
                    raise ValueError("本機繁中倚天來源旗標不符")
        else:
            raise ValueError("未知字型來源紀錄")


def readme(version, platform, local, eten=False, hd=False):
    source = ("已附本機原版及手冊提示資料，只供本機使用，不得上傳。" if local else
              "未附原版、手冊或答案。請自行準備支援版本的原版資料。")
    launch = {"linux": "將 original 目錄放在 AppImage 旁，賦予 AppImage 執行權限後開啟。",
              "windows": "完整解壓縮，將 original 目錄放在 phantasie.exe 旁，再開啟 phantasie.exe。",
              "macos": "完整解壓縮，將 original 目錄放在 Phantasie.app 旁，再開啟 App。"}[platform]
    locations = {"linux": "$XDG_DATA_HOME/phantasie-cht；未設定則 ~/.local/share/phantasie-cht",
                 "windows": "%LOCALAPPDATA%/phantasie-cht",
                 "macos": "~/Library/Application Support/phantasie-cht"}
    if local: launch = launch.replace("將 original 目錄放在 AppImage 旁，", "").replace("，將 original 目錄放在 phantasie.exe 旁", "").replace("，將 original 目錄放在 Phantasie.app 旁", "")
    text = f"""幽靈戰士（Phantasie）中文化 {version}

{source}
{launch}
首次啟動會核對並匯入支援版本；原版來源保持不變。
使用者資料：{locations[platform]}；原版副本在 original，存檔在 saves。
命令列可明示 -root、-data、-state；已有合法匯入時不需保留外部來源。
已有舊平面存檔時，使用另一個 -data，並以 -state 指向原位置。

F11 全螢幕；F12 切換繁體中文、簡體中文、英文原版、日文、韓文。
Shift+F12 切換顯示主題；命令列 -theme 可選 auto、original、amber、hd。
手冊題由玩家選答；本機提示不自動送鍵或改判定。
音訊無輸出。日文與韓文為機器輔助，未經母語者校對。
已按正常 UI 類別抽樣；15 個新增鍵未逐鍵驗收，地城備份還原及部分畫面參數未驗證。
中文停用項目不重現原版變暗外觀，少數日韓數字欄位右緣有排版警告。

專案條款見 LICENSE；第三方全文、作者聲明及所選字型條款見 licenses 與 LICENSES.json。
tools 內的收據工具需另備原版及重播路線；缺驗證資料時的 SKIP 不代表驗收通過。
"""
    if eten:
        text += "\n繁體中文全形採本機倚天；ASCII 與其他語言採 GNU Unifont。倚天只供本機使用，所選 GNU 字型條款及專案 LICENSE 不涵蓋倚天或原版。\n"
    if hd:
        text += "\n手繪主題涵蓋城鎮、標題、已辨識場景及怪物。有遮擋或無法確認的畫面保留原版；手繪圖像只供本機使用。\n"
    if platform == "linux":
        text += "\nLinux 需 X11、OpenGL 及 glibc；正式封包的最低 ABI 與實際冒煙結果見交付清冊。未驗證的發行版未宣稱支援。\n"
    elif platform == "macos":
        text += "\nmacOS 未簽章，未做 macOS 真機驗證。若系統阻擋已確認來源的 App，先嘗試開啟，再到系統設定的隱私權與安全性，按強制打開。Apple 官方步驟：https://support.apple.com/zh-tw/102445\n"
    else:
        text += "\nWindows 目前僅有 Wine 路徑研究證據；正式包結果見交付清冊，未宣稱 Windows 真機驗證。\n"
    return b"\xef\xbb\xbf" + text.replace("\n", "\r\n").encode() if platform == "windows" else text.encode()


def prepare(output, platform, version, project_commit, engine_commit, font_license, text_source, unifont,
            rights, original, launcher, backend, receipt_amd64, receipt_arm64=None, local=False, eten_dir=None, hd_dir=None):
    version = pt.version(version)
    if platform not in ("linux", "windows", "macos") or font_license not in FONT_TERMS:
        raise ValueError("平台或字型條款須明示，不採預設")
    if eten_dir and not local:
        raise ValueError("倚天來源僅接受本機變體")
    if hd_dir and not local:
        raise ValueError("HD 來源僅接受本機變體")
    if not all(re.fullmatch(r"[0-9a-f]{40}", value) for value in (project_commit, engine_commit)):
        raise ValueError("兩個 repo 須為完整 commit")
    if (platform == "macos") != bool(receipt_arm64):
        raise ValueError("macOS 收據須同時有兩種架構，其餘平台只附 amd64")
    output = pf.no_links(output)
    if output.exists() or not output.parent.is_dir():
        raise ValueError("stage 須為新目錄且父目錄已存在")
    source_dirs = [pf.directory(path) for path in (text_source, rights, original)]
    sources = source_dirs + [pf.no_links(path) for path in (unifont, launcher, backend, receipt_amd64)]
    if receipt_arm64: sources.append(pf.no_links(receipt_arm64))
    if eten_dir: sources.append(pf.directory(eten_dir))
    if hd_dir: sources.append(pf.directory(hd_dir))
    if any(output == path or output in path.parents or path in output.parents for path in sources):
        raise ValueError("來源與 stage 不得重疊")
    fingerprint = ps.originals(original, Path(__file__).resolve().parents[1] / "docs/re/001-input-inventory.tsv")
    if len(fingerprint) != 70: raise ValueError("原版掃描來源須為固定 70 檔")
    art_payloads, art_notice = pf.art_files(hd_dir, original) if hd_dir else ({}, None)
    text, _ = pt.collect(pf.directory(text_source), local)
    licenses, rights_index = rights_files(rights, platform == "linux")
    font_sources(unifont)
    executable = {"launcher": pf.file_bytes(launcher), "backend": pf.file_bytes(backend), "receipt-amd64": pf.file_bytes(receipt_amd64)}
    if receipt_arm64: executable["receipt-arm64"] = pf.file_bytes(receipt_arm64)
    for name, data in executable.items():
        binary(data, platform, "universal" if platform == "macos" and name in ("launcher", "backend") else "arm64" if name == "receipt-arm64" else "amd64", name.startswith("receipt"))
    original_payloads = {}
    if local:
        for path in pf.directory(original).iterdir():
            if path.name.casefold() in fingerprint:
                data = pf.file_bytes(path)
                if (len(data), pf.digest(data)) != fingerprint[path.name.casefold()]: raise ValueError("本機原版來源改變")
                original_payloads[path.name] = data
        if len(original_payloads) != 70: raise ValueError("本機原版缺檔")
    output.mkdir()
    try:
        if platform == "linux": base = output / "usr/bin"; text_dir, font_dir, original_dir = "text", "font", "original"
        elif platform == "windows": base = output; text_dir, font_dir, original_dir = "text", "font", "original"
        else: base = output / "Phantasie.app/Contents"; text_dir, font_dir, original_dir = "Resources/text", "Resources/font", "Resources/original"
        def write(path, data, mode=0o644):
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream: stream.write(data)
            path.chmod(mode)
        suffix = ".exe" if platform == "windows" else ""
        bin_dir = base / "MacOS" if platform == "macos" else base
        write(bin_dir / ("phantasie" + suffix), executable["launcher"], 0o755)
        write(bin_dir / ("phantasie-play" + suffix), executable["backend"], 0o755)
        for arch in ("amd64", "arm64") if platform == "macos" else ("amd64",):
            name = f"phantasie-receipt-{arch}" if platform == "macos" else "phantasie-receipt" + suffix
            write(output / "tools" / name, executable["receipt-" + arch], 0o755)
        for name, data in text.items(): write(base / text_dir / name, data)
        for name, data in original_payloads.items(): write(base / original_dir / name, data, 0o444)
        art_dir = "Resources/art" if platform == "macos" else "art"
        for name, data in art_payloads.items(): write(base / art_dir / name, data)
        for name, data in licenses.items():
            target = output / "LICENSE" if name == "common/LICENSE-project" else output / "licenses" / (name[7:] if name.startswith("common/") else name)
            write(target, data)
        if font_license == "GPL-2.0-or-later-with-font-exception":
            write(output / "licenses/unifont/unifont-17.0.05.tar.gz", pf.file_bytes(unifont))
        for language in pt.LANGUAGES:
            member = "unifont-17.0.05/font/precompiled/" + FONT_MEMBERS[language][0]
            destination = base / font_dir / (language + ".golemfnt")
            destination.parent.mkdir(parents=True, exist_ok=True)
            args = [sys.executable, "-B", str(Path(__file__).with_name("build_font.py")), "--tar", str(unifont), "--member", member, "--out", str(destination)]
            for family in ("ui", "prose", "manual"): args += ["--chars", str(base / text_dir / f"{family}.{language}.tsv")]
            if subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False).returncode:
                raise ValueError("字型重建失敗：" + language)
        fonts = {language: {"source": "GNU Unifont 17.0.05", "terms": font_license,
                           "sha256": pf.digest(pf.file_bytes(base / font_dir / (language + ".golemfnt")))}
                 for language in pt.LANGUAGES}
        if eten_dir:
            destination = base / font_dir / "zh-TW.golemfnt"
            converted = destination.with_suffix(".eten")
            provenance = eten_font.build(eten_dir, destination, converted)
            converted.replace(destination)
            fonts["zh-TW"] = {"source": "ETEN local fullwidth with GNU ASCII", "rights": "local-only",
                              "terms_gnu_ascii": font_license, "sha256": provenance["sha256"], "eten": provenance}
        validate_fonts(base, font_dir, fonts, local, font_license)
        pf.bundle(output, platform, version, engine_commit, text_source if local else None)
        write(output / "README.txt", readme(version, platform, local, bool(eten_dir), bool(hd_dir)))
        notice = {"font_license": font_license, "scope": "selected font terms; other components retain their own terms",
                  "source_profile_sha256": rights_index["profile_sha256"], "module_header_notices": rights_index["module_header_notices"],
                  "fonts": fonts}
        if art_notice: notice["art"] = art_notice
        write(output / "LICENSES.json", (json.dumps(notice, ensure_ascii=False, indent=2) + "\n").encode())
        if platform == "linux":
            write(output / "AppRun", APPRUN, 0o755); write(output / "phantasie.svg", ICON); write(output / ".DirIcon", ICON)
            write(output / "phantasie.desktop", f"[Desktop Entry]\nType=Application\nName=幽靈戰士\nExec=phantasie\nIcon=phantasie\nTerminal=false\nCategories=Game;\nX-Phantasie-Version={version}\n".encode())
        elif platform == "macos":
            semantic = version[2:].split("-", 1)[0]
            info = {"CFBundleIdentifier": "org.wicanr2.phantasie-cht", "CFBundleName": "Phantasie", "CFBundleDisplayName": "幽靈戰士",
                    "CFBundleExecutable": "phantasie", "CFBundlePackageType": "APPL", "CFBundleVersion": semantic,
                    "CFBundleShortVersionString": semantic, "PhantasieReleaseVersion": version, "PhantasieEngineCommit": engine_commit,
                    "LSMinimumSystemVersion": "11.0"}
            write(base / "Info.plist", plistlib.dumps(info, sort_keys=True))
        scope = {"schema": 1, "scope": "platform staging only; not formal package acceptance", "version": version,
                 "project_commit": project_commit, "engine_commit": engine_commit, "platform": platform,
                 "rights": "local-only" if local else "no-original-or-manual-answers", "font_license": font_license,
                 "fonts": fonts,
                 "files": {name: row for name, row in pf.snapshot(output).items() if not row["directory"]}}
        if art_notice: scope["art"] = art_notice
        write(output / "package-stage.json", (json.dumps(scope, ensure_ascii=False, indent=2) + "\n").encode())
        if platform == "windows": pf.windows_text(output)
        scan = ps.Scanner(fingerprint, str((base / original_dir).relative_to(output)) if local else None, text_source if local else None).scan(output)
        if scan["rights"] != scope["rights"]: raise ValueError("stage 權利分類不符")
    except BaseException:
        shutil.rmtree(output)
        raise
    return scope


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=("linux", "windows", "macos"), required=True)
    parser.add_argument("--font-license", choices=FONT_TERMS, required=True)
    for name in ("out", "text-source", "unifont", "rights", "original", "launcher", "backend", "receipt-amd64"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--receipt-arm64", type=Path)
    for name in ("version", "project-commit", "engine-commit"): parser.add_argument("--" + name, required=True)
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--eten-dir", type=Path, help="僅本機繁中變體的固定倚天來源")
    parser.add_argument("--hd-dir", type=Path, help="僅本機完整版的已驗證完整手繪圖像組")
    args = parser.parse_args()
    try:
        result = prepare(args.out, args.platform, args.version, args.project_commit, args.engine_commit, args.font_license,
                         args.text_source, args.unifont, args.rights, args.original, args.launcher, args.backend,
                         args.receipt_amd64, args.receipt_arm64, args.local, args.eten_dir, args.hd_dir)
    except (OSError, UnicodeError, ValueError, KeyError, struct.error, tarfile.TarError) as error:
        parser.exit(1, f"平台組裝失敗：{error}\n")
    print(json.dumps({"result": "PASS platform staging only", "platform": result["platform"], "rights": result["rights"],
                      "files": len(result["files"]), "version": result["version"]}, ensure_ascii=False))


if __name__ == "__main__": main()
