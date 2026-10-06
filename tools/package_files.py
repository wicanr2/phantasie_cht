#!/usr/bin/env python3
"""013 §4／§5／§12：必要資產清冊及 ZIP。只在 Docker 內執行。

輸入是已整理的研究／封裝布局；本工具不建置、選授權或宣稱正式包完成。
原版外洩、二進位架構、第三方條款及 GUI 另依 013 驗證。
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import stat
import struct
import zipfile
import zlib

import catalog_lib as cl
import package_scan
import package_text


def no_links(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("路徑含符號連結")
    return path


def directory(path):
    path = no_links(path)
    if not path.is_dir():
        raise ValueError("布局來源須為實際目錄")
    return path


def file_bytes(path):
    path = package_scan.regular(path)
    if path.stat().st_size > package_scan.MAX_FILE:
        raise ValueError("布局檔案超過大小上限")
    return path.read_bytes()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def record(name, data):
    return {"name": name, "bytes": len(data), "sha256": digest(data)}


def art_files(path, original):
    """015：只回傳完整驗證的本機城鎮組，不收研究附件。"""
    path, original = directory(path), directory(original)
    data = file_bytes(path / "profile.json")
    if len(data) > 65536:
        raise ValueError("HD profile 過大")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ValueError("HD profile 重複欄位")
            result[key] = value
        return result
    p = json.loads(data, object_pairs_hook=unique)
    if isinstance(p, dict) and type(p.get("schema")) is int and p["schema"] in (2, 3):
        approved = "package_art_assets.json" if p["schema"] == 2 else "package_party_art_assets.json"
        canonical = json.loads(file_bytes(Path(__file__).with_name(approved)), object_pairs_hook=unique)
        if json.dumps(p, sort_keys=True, separators=(",", ":")) != json.dumps(canonical, sort_keys=True, separators=(",", ":")):
            raise ValueError("HD 組不是018／020已批准完整資產")
        files = {"profile.json": data}
        for source in p["sources"]:
            raw = file_bytes(original / source["file"])
            if len(raw) != source["bytes"] or digest(raw) != source["sha256"]:
                raise ValueError("HD 原版來源指紋不符")
        for image in p["images"]:
            raw = file_bytes(path / image["file"])
            if len(raw) != image["bytes"] or digest(raw) != image["sha256"]:
                raise ValueError("HD 圖像指紋不符")
            files[image["file"]] = raw
        return files, {"rights": "local-only original-derived art", "profile_sha256": digest(data),
                       "sources": p["sources"], "images": p["images"], "pages": len(p["pages"]), "sprites": len(p["sprites"])}
    expected = {"schema", "source_file", "source_bytes", "source_sha256", "source_rect", "image", "image_bytes", "image_sha256"}
    if not isinstance(p, dict) or set(p) != expected or type(p["schema"]) is not int or p["schema"] != 1:
        raise ValueError("HD profile 欄位不符")
    if p["source_file"] != "PELNOR.IBM" or p["source_bytes"] != 16384 or p["source_sha256"] != "68833b5ae2ef2c77317b7a30998aacca1a7edf942c20dd0316df833e4394036c" or p["source_rect"] != [0, 8, 320, 184] or any(type(v) is not int for v in p["source_rect"]) or p["image"] != "town-painted.png":
        raise ValueError("HD 來源或矩形不是已驗證城鎮")
    # 封包只接受015列明、已由實際前端解碼的這份資產。
    # 未來替換圖像須更新證據與固定身份，不能以自填profile放行。
    if p["image_bytes"] != 2524255 or p["image_sha256"] != "f520bd1e2fdb112e630ac05c5ac6006f0ae23607d95f1c7c4deaf5a0e03cec06":
        raise ValueError("HD 圖像不是015已驗證資產")
    raw = file_bytes(original / p["source_file"])
    image = file_bytes(path / p["image"])
    if len(raw) != p["source_bytes"] or digest(raw) != p["source_sha256"] or type(p["image_bytes"]) is not int or len(image) != p["image_bytes"] or digest(image) != p["image_sha256"]:
        raise ValueError("HD 資產指紋不符")
    if len(image) > 16 * 1024 * 1024 or image[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("HD 圖像須為有界 PNG")
    offset, chunks = 8, []
    while offset < len(image):
        if offset + 12 > len(image): raise ValueError("HD PNG chunk 截斷")
        n = struct.unpack_from(">I", image, offset)[0]
        end = offset + 12 + n
        if end > len(image): raise ValueError("HD PNG chunk 越界")
        kind = image[offset + 4:offset + 8]
        payload = image[offset + 8:end - 4]
        if zlib.crc32(kind + payload) != struct.unpack_from(">I", image, end - 4)[0]: raise ValueError("HD PNG CRC 不符")
        chunks.append((kind, payload))
        offset = end
        if kind == b"IEND": break
    if offset != len(image) or not chunks or chunks[0][0] != b"IHDR" or len(chunks[0][1]) != 13 or chunks[-1] != (b"IEND", b"") or not any(k == b"IDAT" for k, _ in chunks):
        raise ValueError("HD PNG 結構不符")
    w, h = struct.unpack_from(">II", chunks[0][1])
    if not (0 < w <= 4096 and 0 < h <= 4096 and w * h <= 4_000_000) or abs(w * 184 / (h * 320) - 1) > .005:
        raise ValueError("HD PNG 尺寸不符")
    return {"profile.json": data, p["image"]: image}, {"rights": "local-only original-derived art", "profile_sha256": digest(data), "source_sha256": p["source_sha256"], "image_sha256": p["image_sha256"], "dimensions": [w, h]}


def profile(stage, platform):
    stage = directory(stage)
    if platform == "linux":
        return directory(stage / "usr/bin"), "bundle.json", "phantasie-play", "text", "font", "original"
    if platform == "windows":
        return stage, "bundle.json", "phantasie-play.exe", "text", "font", "original"
    if platform == "macos":
        base = directory(stage / "Phantasie.app/Contents")
        return base, "Resources/bundle.json", "MacOS/phantasie-play", "Resources/text", "Resources/font", "Resources/original"
    raise ValueError("平台須為 linux、windows 或 macos")


def font_coverage(data, needed, local_eten=False):
    if len(data) < 16 or data[:8] != b"GOLEMFNT":
        raise ValueError("字型標頭無效")
    width, height, count = struct.unpack_from("<HHI", data, 8)
    if (width, height) != (16, 16) or count == 0 or len(data) != 16 + count * 37:
        raise ValueError("字型尺寸或記錄長度不符")
    codes = set()
    previous = -1
    for offset in range(16, len(data), 37):
        cp, source = struct.unpack_from("<IB", data, offset)
        allowed_source = source in (1, 0x81) or (local_eten and source == 0x82 and cp >= 128)
        if cp <= previous or cp > 0x10FFFF or 0xD800 <= cp <= 0xDFFF or not allowed_source:
            raise ValueError("字型碼點、順序或來源旗標不符")
        codes.add(cp)
        previous = cp
    if not needed <= codes:
        raise ValueError("字型缺必要譯文字元")
    return count


def bundle_data(stage, platform, version, engine, local_manual=None):
    version = package_text.version(version)
    if not re.fullmatch(r"[0-9a-f]{40}", engine):
        raise ValueError("引擎須為完整 commit")
    base, manifest, backend, text, font, original = profile(stage, platform)
    if local_manual:
        reference = directory(local_manual)
        if reference == Path(stage).absolute() or Path(stage).absolute() in reference.parents or reference in Path(stage).absolute().parents:
            raise ValueError("本機提示來源與布局不得重疊")
        inputs = package_scan.originals(base / original, Path(__file__).resolve().parents[1] / "docs/re/001-input-inventory.tsv")
        if len(inputs) != 70 or {p.name.casefold() for p in (base / original).iterdir()} != inputs.keys():
            raise ValueError("本機原版目錄須恰含固定 70 檔")
    elif (base / original).exists():
        raise ValueError("無答案布局不得帶入原版目錄")
    files = {backend: file_bytes(base / backend)}
    if not files[backend]:
        raise ValueError("後端不得為空檔")
    if platform != "windows" and not (base / backend).stat().st_mode & 0o111:
        raise ValueError("後端缺執行權限")
    expected_keys = {}
    help_files, _ = package_text.collect_help(base / text)
    files.update({f"{text}/{name}": data for name, data in help_files.items()})
    for language in package_text.LANGUAGES:
        needed = set(range(0x20, 0x7F))
        for family in ("ui", "prose", "manual"):
            name = f"{text}/{family}.{language}.tsv"
            path = base / name
            data = file_bytes(path)
            _, rows = package_text.catalog(path)
            keys = frozenset(key for _, key, _, _ in rows)
            if family != "manual":
                if family in expected_keys and keys != expected_keys[family]:
                    raise ValueError("四語 catalog 鍵集合不同")
                expected_keys[family] = keys
            elif local_manual:
                if package_text.local_manual(path)[0] != package_text.local_manual(reference / path.name)[0]:
                    raise ValueError("本機提示表與指定來源不符")
            elif keys != package_text.TITLES or len(rows) != 2:
                raise ValueError("無答案 manual 必須僅有兩個標題")
            for _, _, translation, _ in rows:
                needed.update(ord(c) for c in translation if c not in cl.CENTER + "\n\r\t")
            files[name] = data
        name = f"{font}/{language}.golemfnt"
        data = file_bytes(base / name)
        help_name = f"help.{language}.tsv"
        if help_name in help_files:
            _, help_rows = package_text.help_catalog(base / text / help_name, language)
            flags = {struct.unpack_from("<I", data, offset)[0]: data[offset + 4]
                     for offset in range(16, len(data), 37)} if len(data) >= 16 and (len(data) - 16) % 37 == 0 else {}
            for _, _, translation, _ in help_rows:
                needed.update(map(ord, translation))
                if sum(16 if flags.get(ord(c), 0) & 0x80 else 8 for c in translation) > 576:
                    raise ValueError("Help 實際字型行寬超過576像素")
        font_coverage(data, needed, bool(local_manual) and language == "zh-TW")
        files[name] = data
    name = f"{text}/protected.tsv"
    file_bytes(base / name)
    files[name] = package_text.protected(base / name)[0]
    art = "Resources/art" if platform == "macos" else "art"
    has_art = (base / art).exists()
    if has_art:
        if not local_manual: raise ValueError("patch 不接受 HD 素材")
        group, _ = art_files(base / art, base / original)
        if {p.name for p in (base / art).iterdir()} != set(group): raise ValueError("HD 素材目錄含研究附件")
        files.update({f"{art}/{name}": data for name, data in group.items()})
    result = {"schema": 1, "version": version, "engine_commit": engine, "backend": backend,
              "text": text, "font": font, "assets": [record(name, data) for name, data in sorted(files.items())]}
    if local_manual:
        result["local_original"] = original
    if has_art:
        result["art"] = art
    return base / manifest, result


def bundle(stage, platform, version, engine, local_manual=None, verify=False):
    path, expected = bundle_data(stage, platform, version, engine, local_manual)
    if verify:
        canonical = (json.dumps(expected, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if file_bytes(path) != canonical:
            raise ValueError("bundle.json 與實際必要資產不符")
    else:
        no_links(path)
        # 排他建立，失敗只移除本次建立的清冊。
        stream = path.open("x", encoding="utf-8", newline="\n")
        try:
            with stream:
                json.dump(expected, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
        except BaseException:
            path.unlink()
            raise
    return expected


def snapshot(stage):
    stage = directory(stage)
    result = {}
    seen = set()
    total = 0
    for path in [stage, *sorted(stage.rglob("*"))]:
        name = stage.name if path == stage else stage.name + "/" + path.relative_to(stage).as_posix()
        package_scan.path_parts(name)
        key = name.casefold()
        if key in seen:
            raise ValueError("布局含不分大小寫的重複名稱")
        seen.add(key)
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            result[name + "/"] = {"directory": True, "bytes": 0, "sha256": digest(b""), "mode": stat.S_IFDIR | 0o755}
        elif stat.S_ISREG(mode):
            data = file_bytes(path)
            total += len(data)
            if total > package_scan.MAX_BYTES:
                raise ValueError("布局總大小超過上限")
            result[name] = {"directory": False, "bytes": len(data), "sha256": digest(data),
                            "mode": stat.S_IFREG | (0o755 if mode & 0o111 else 0o644)}
        else:
            raise ValueError("布局含符號連結或特殊檔案")
        if len(result) > package_scan.MAX_ENTRIES:
            raise ValueError("布局項目數超過上限")
    if not any(not row["directory"] for row in result.values()):
        raise ValueError("布局沒有檔案")
    return result


def windows_text(stage):
    data = file_bytes(Path(stage) / "README.txt")
    if not data.startswith(b"\xef\xbb\xbf") or not data.endswith(b"\r\n"):
        raise ValueError("Windows README.txt 須為 UTF-8 BOM 及 CRLF")
    data.decode("utf-8-sig")
    if b"\n" in data.replace(b"\r\n", b"") or b"\r" in data.replace(b"\r\n", b""):
        raise ValueError("Windows README.txt 換行不符")
    for path in Path(stage).rglob("*"):
        if path.suffix.casefold() == ".bat":
            data = file_bytes(path)
            data.decode("ascii")
            if not data.endswith(b"\r\n") or b"\n" in data.replace(b"\r\n", b"") or b"\r" in data.replace(b"\r\n", b""):
                raise ValueError("批次檔須為 ASCII 及 CRLF，不含 BOM")


def zip_date(version):
    date = datetime.strptime(package_text.version(version)[-8:], "%Y%m%d")
    if not 1980 <= date.year <= 2107:
        raise ValueError("版號日期超過 ZIP 時間範圍")
    return date.year, date.month, date.day, 0, 0, 0


def verify_zip(stage, archive, version, platform):
    if platform not in ("windows", "macos"):
        raise ValueError("ZIP 平台須為 windows 或 macos")
    expected = snapshot(stage)
    stamp = zip_date(version)
    if platform == "windows":
        windows_text(stage)
    archive = package_scan.regular(archive)
    seen = set()
    with zipfile.ZipFile(archive) as source:
        if source.comment:
            raise ValueError("ZIP 不得帶額外註解")
        for member in source.infolist():
            name = member.filename
            package_scan.path_parts(name)
            if name not in expected or name in seen:
                raise ValueError("ZIP 含額外或重複項目")
            seen.add(name)
            row = expected[name]
            if member.is_dir() != row["directory"] or member.file_size != row["bytes"] or member.external_attr >> 16 != row["mode"]:
                raise ValueError("ZIP 項目型態、大小或執行權限不符")
            if member.flag_bits & 1 or any(ord(c) > 127 for c in name) and not member.flag_bits & 0x800:
                raise ValueError("ZIP 加密或非 ASCII 名稱缺 UTF-8 旗標")
            if member.date_time != stamp or member.extra or member.comment:
                raise ValueError("ZIP 時間或附加資料不符")
            if digest(source.read(member)) != row["sha256"]:
                raise ValueError("ZIP 內容與布局雜湊不同")
    if seen != expected.keys():
        raise ValueError("ZIP 缺布局項目")
    return {"files": sum(not row["directory"] for row in expected.values()), "entries": len(expected),
            "bytes": archive.stat().st_size, "sha256": digest(archive.read_bytes())}


def make_zip(stage, archive, version, platform):
    stage = directory(stage)
    archive = no_links(archive)
    if stage == archive or stage in archive.parents or archive in stage.parents:
        raise ValueError("ZIP 輸出與布局不得重疊")
    if not archive.parent.is_dir():
        raise ValueError("ZIP 輸出父目錄缺席")
    if platform not in ("windows", "macos"):
        raise ValueError("ZIP 平台須為 windows 或 macos")
    if platform == "windows":
        windows_text(stage)
    expected = snapshot(stage)
    stamp = zip_date(version)
    # 用檔案物件及排他模式，不能覆寫任何既有封包。
    destination = archive.open("xb")
    try:
        with destination:
            with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as output:
                for name, row in sorted(expected.items()):
                    info = zipfile.ZipInfo(name, stamp)
                    info.create_system = 3
                    info.external_attr = row["mode"] << 16 | (0x10 if row["directory"] else 0)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    path = stage.parent / name
                    data = b"" if row["directory"] else file_bytes(path)
                    if digest(data) != row["sha256"]:
                        raise ValueError("封裝期間輸入改變")
                    output.writestr(info, data, compresslevel=9)
            destination.flush()
            if snapshot(stage) != expected:
                raise ValueError("封裝期間布局改變")
            result = verify_zip(stage, archive, version, platform)
    except BaseException:
        archive.unlink()
        raise
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("bundle", "verify-bundle", "zip", "verify-zip"))
    parser.add_argument("--stage", required=True, type=Path)
    parser.add_argument("--platform", required=True, choices=("linux", "windows", "macos"))
    parser.add_argument("--version", required=True)
    parser.add_argument("--engine", help="bundle 操作必要的完整引擎 commit")
    parser.add_argument("--local-manual", type=Path, help="明示本機答案來源；不自動尋找")
    parser.add_argument("--archive", type=Path, help="ZIP 操作必要的輸出／核對檔案")
    args = parser.parse_args()
    try:
        if args.action in ("bundle", "verify-bundle"):
            if not args.engine or args.archive:
                raise ValueError("bundle 操作須明示 engine，不接受 archive")
            result = bundle(args.stage, args.platform, args.version, args.engine, args.local_manual, args.action == "verify-bundle")
            summary = {"assets": len(result["assets"])}
        else:
            if not args.archive or args.engine or args.local_manual or args.platform == "linux":
                raise ValueError("ZIP 操作須明示 archive 與 windows／macos，不接受 engine／local-manual")
            function = make_zip if args.action == "zip" else verify_zip
            summary = function(args.stage, args.archive, args.version, args.platform)
    except (OSError, UnicodeError, ValueError, struct.error, zipfile.BadZipFile) as error:
        parser.exit(1, f"封包檔案處理失敗：{error}\n")
    print(json.dumps({"result": "PASS package files only", "action": args.action, **summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
