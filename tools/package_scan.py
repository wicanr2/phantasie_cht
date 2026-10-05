#!/usr/bin/env python3
"""規格 013 §7 的封包外洩掃描。只在 Docker 內執行。

掃描已解出的目錄或 ZIP／tar，唯讀核對指定原版清單。
此工具不證明授權、字型覆蓋、可啟動性或正式封包完成。
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import tarfile
import zipfile

import package_text

# 固定來源已由 013 §9.1／font/README.md 的獨立收據逐項核對。
# 只接受精確 bytes；未命中的壓縮檔逐層掃描，不由呼叫者追加豁免。
SOURCE_ARCHIVES = {
    "runtime-source-r1.tar.gz": "3fdd3a4bbaacc949f56b0a167a2b99ad27855bcac7aa01574fbaf5d63c00fe08",
    "unifont-17.0.05.tar.gz": "f287cffb26e22723aa36e6684869b0f3ff3bfb822c4b01008bd847911ec1b631",
}
ANSWER_ROWS = re.compile(rb"(?:^|\n)(?:item:[^\t\r\n]+|spell:[0-9]+|answer)\t")
PRIVATE_PARTS = {"workplace", "research", "manual-derived", "play-state", "session-data"}
MAX_BYTES = 512 * 1024 * 1024
MAX_FILE = 128 * 1024 * 1024
MAX_ENTRIES = 50000
MAX_DEPTH = 5


def path_parts(name):
    """封包項目採相對 POSIX 路徑；不解析到主機檔案系統。"""
    name = name.rstrip("/")
    parts = name.split("/")
    if not name or "\\" in name or ":" in name or any(ord(c) < 32 or ord(c) == 127 for c in name) or any(p in ("", ".", "..") for p in parts):
        raise ValueError("封包項目路徑無效")
    return parts


def regular(path):
    path = Path(path).absolute()
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise ValueError("輸入路徑含符號連結")
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("輸入須為一般檔案")
    return path


def originals(root, inventory):
    root = Path(root).absolute()
    if not root.is_dir() or any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError("原版掃描來源缺席或型態不符，不能當作無外洩")
    with regular(inventory).open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    result = {}
    for row in rows:
        name = row["name"]
        if len(path_parts(name)) != 1 or name.casefold() in result:
            raise ValueError("原版清冊名稱無效或重複")
        size, digest = int(row["bytes"]), row["sha256"]
        if size < 0 or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("原版清冊大小或雜湊無效")
        path = regular(root / name)
        if path.stat().st_size != size or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("原版掃描來源與固定清冊不符")
        result[name.casefold()] = (size, digest)
    if not result:
        raise ValueError("原版清冊不得為空")
    return result


class Scanner:
    def __init__(self, fingerprint, local_original=None, local_manual=None):
        if bool(local_original) != bool(local_manual):
            raise ValueError("本機模式須同時明示包內原版路徑及本機提示來源")
        self.originals = fingerprint
        self.hashes = {digest for _, digest in fingerprint.values()}
        self.local_prefix = tuple(path_parts(local_original)) if local_original else None
        self.local_tables = {}
        self.local_source = Path(local_manual).absolute() if local_manual else None
        if local_manual:
            root = Path(local_manual).absolute()
            for language in package_text.LANGUAGES:
                name = f"manual.{language}.tsv"
                path = regular(root / name)
                self.local_tables[name] = package_text.local_manual(path)[0]
        self.local_seen = set()
        self.manual_seen = set()
        self.bytes = 0
        self.entries = 0
        self.files = 0
        self.archives = 0
        self.sources = []

    def entry(self, name, size=0):
        parts = path_parts(name)
        self.entries += 1
        self.bytes += size
        if self.entries > MAX_ENTRIES or size > MAX_FILE or self.bytes > MAX_BYTES:
            raise ValueError("掃描超過項目或解壓大小上限")
        if any(part.casefold() in PRIVATE_PARTS for part in parts):
            raise ValueError("封包含研究或狀態目錄")
        if not self.local_prefix and any(part.casefold() == "original" for part in parts):
            raise ValueError("可散布包不得含 original 目錄")
        return parts

    def payload(self, name, data, depth=0, allow_local=True, root_container=False):
        parts = self.entry(name, len(data))
        self.files += 1
        leaf = parts[-1]
        folded = leaf.casefold()
        digest = hashlib.sha256(data).hexdigest()
        # 本機原版只能在明示的目錄內逐檔對應清冊，不能散落其他位置。
        if self.local_prefix and tuple(parts[:-1]) == self.local_prefix and allow_local:
            if folded not in self.originals or self.originals[folded] != (len(data), digest):
                raise ValueError("本機包原版與清冊不符")
            if folded in self.local_seen:
                raise ValueError("本機包原版重複")
            self.local_seen.add(folded)
            return
        if folded in self.originals or digest in self.hashes:
            raise ValueError("封包命中原版檔名或 SHA-256")
        if any(p.casefold() == "original" for p in parts) and not self.local_prefix:
            raise ValueError("可散布包不得含 original 目錄")
        if folded.endswith((".pdf", ".route", ".i64", ".idb")) or folded in {"answers.tsv", "answers.json"}:
            raise ValueError("封包含手冊、作答路線或研究資料")
        if folded.startswith("manual-labels."):
            raise ValueError("封包不得含手冊答案模板來源")
        if leaf in self.local_tables and allow_local:
            if len(parts) < 2 or parts[-2] != "text" or data != self.local_tables[leaf] or leaf in self.manual_seen:
                raise ValueError("本機提示表的位置、內容或數量不符")
            self.manual_seen.add(leaf)
        else:
            if ANSWER_ROWS.search(data):
                raise ValueError("封包含手冊答案或答案模板資料列")
            if re.fullmatch(r"manual\.(?:zh-TW|zh-CN|ja|ko)\.tsv", leaf):
                try:
                    text = data.decode("utf-8")
                    lines = text.splitlines()
                    rows = [line.split("\t") for line in lines[1:]]
                    keys = [row[0] for row in rows]
                    valid = (lines[0] == "key\ttranslation\tsource" and text.endswith("\n")
                             and len(rows) == 2 and set(keys) == package_text.TITLES
                             and all(len(row) == 3 and all(row) for row in rows)
                             and not any(ord(c) < 32 and c not in "\n\t" for c in text))
                except (UnicodeError, IndexError):
                    valid = False
                if not valid:
                    raise ValueError("無答案包的手冊表必須只有兩個合法標題")
        if leaf in SOURCE_ARCHIVES and digest == SOURCE_ARCHIVES[leaf]:
            self.sources.append({"name": leaf, "sha256": digest})
            return
        self.archive(name, data, depth, root_container)

    def archive(self, name, data, depth, root_container=False):
        stream = io.BytesIO(data)
        is_zip = zipfile.is_zipfile(stream)
        stream.seek(0)
        is_tar = False
        if not is_zip:
            try:
                with tarfile.open(fileobj=stream, mode="r:*"):
                    is_tar = True
            except tarfile.ReadError:
                pass
        if not is_zip and not is_tar:
            if data.startswith(b"\x1f\x8b"):
                if depth >= MAX_DEPTH:
                    raise ValueError("壓縮檔巢狀層數超過上限")
                self.archives += 1
                with gzip.GzipFile(fileobj=io.BytesIO(data)) as source:
                    payload = source.read(MAX_FILE + 1)
                self.payload(name + "!/<gzip-payload>", payload, depth + 1, allow_local=False)
                return
            unsupported = (b"7z\xbc\xaf\x27\x1c", b"Rar!\x1a\x07", b"\xfd7zXZ\x00", b"BZh", b"LZIP", b"\x28\xb5\x2f\xfd")
            # Zstandard 1.5.6 格式契約：16 種 skippable frame 的 little-endian magic。
            zstd_skippable = len(data) >= 4 and 0x184D2A50 <= int.from_bytes(data[:4], "little") <= 0x184D2A5F
            if data.startswith(unsupported) or zstd_skippable or name.casefold().endswith((".zip", ".tar", ".gz", ".tgz", ".xz", ".bz2", ".7z", ".rar", ".lz", ".zst", ".zstd", ".appimage", ".iso")):
                raise ValueError("封包壓縮檔無法讀取")
            return
        if depth >= MAX_DEPTH:
            raise ValueError("壓縮檔巢狀層數超過上限")
        self.archives += 1
        seen = set()
        stream.seek(0)
        archive = zipfile.ZipFile(stream) if is_zip else tarfile.open(fileobj=stream, mode="r:*")
        with archive:
            for member in archive.infolist() if is_zip else archive:
                member_name = member.filename if is_zip else member.name
                parts = path_parts(member_name)
                canonical = "/".join(parts).casefold()
                if canonical in seen:
                    raise ValueError("壓縮檔含重複名稱")
                seen.add(canonical)
                nested = "/".join(parts) if root_container else name + "!/" + "/".join(parts)
                # 分開 archive 展示路徑，不能讓 !/ 使 ../ 路徑變合法。
                if is_zip:
                    mode = member.external_attr >> 16
                    kind = stat.S_IFMT(mode)
                    # Windows ZIP 常不提供 Unix type bits；零值保留。
                    if kind not in (0, stat.S_IFREG, stat.S_IFDIR) or member.flag_bits & 1:
                        raise ValueError("ZIP 含連結、特殊檔案或加密項目")
                    if any(ord(c) > 127 for c in member_name) and not member.flag_bits & 0x800:
                        raise ValueError("ZIP 非 ASCII 名稱缺 UTF-8 旗標")
                    directory, size = member.is_dir(), member.file_size
                    opener = lambda: archive.open(member)
                else:
                    if not member.isdir() and not member.isfile():
                        raise ValueError("tar 含連結或特殊項目")
                    directory, size = member.isdir(), member.size
                    opener = lambda: archive.extractfile(member)
                if directory:
                    if size != 0:
                        raise ValueError("壓縮檔的目錄項目不得含資料")
                    self.entry(nested)
                    continue
                if size > MAX_FILE or self.bytes + size > MAX_BYTES:
                    raise ValueError("壓縮檔解出大小超過上限")
                with opener() as source:
                    payload = source.read(MAX_FILE + 1)
                if len(payload) != size:
                    raise ValueError("壓縮檔項目大小不符")
                self.payload(nested, payload, depth + 1, allow_local=root_container)

    def scan(self, target):
        target = Path(target).absolute()
        if any(p.is_symlink() for p in (target, *target.parents)):
            raise ValueError("掃描路徑含符號連結")
        if self.local_source and (self.local_source == target or target in self.local_source.parents or self.local_source in target.parents):
            raise ValueError("本機提示來源與掃描範圍不得重疊")
        if target.is_dir():
            for path in sorted(target.rglob("*")):
                mode = path.lstat().st_mode
                name = path.relative_to(target).as_posix()
                if stat.S_ISDIR(mode):
                    self.entry(name)
                elif stat.S_ISREG(mode):
                    if path.stat().st_size > MAX_FILE:
                        raise ValueError("檔案大小超過上限")
                    self.payload(name, path.read_bytes())
                else:
                    raise ValueError("掃描目錄含連結或特殊檔案")
        else:
            path = regular(target)
            if path.stat().st_size > MAX_FILE:
                raise ValueError("檔案大小超過上限")
            self.payload(path.name, path.read_bytes(), allow_local=False, root_container=True)
            if not self.archives and not self.sources:
                raise ValueError("單一檔案須為可讀壓縮檔；AppImage 請先解出目錄")
        if not self.files:
            raise ValueError("掃描範圍沒有檔案")
        if self.local_prefix and (self.local_seen != self.originals.keys() or self.manual_seen != self.local_tables.keys()):
            raise ValueError("本機包缺原版或本機提示表")
        return {"result": "PASS leakage scan only", "rights": "local-only" if self.local_prefix else "no-original-or-manual-answers",
                "files": self.files, "archives": self.archives, "scanned_bytes": self.bytes,
                "original_inputs": len(self.originals), "fixed_source_archives": self.sources}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan", required=True, type=Path)
    parser.add_argument("--original", required=True, type=Path, help="支援版本的唯讀原版掃描來源")
    parser.add_argument("--local-original", help="本機包內的相對原版目錄")
    parser.add_argument("--local-manual", type=Path, help="本機正式提示表來源")
    args = parser.parse_args()
    try:
        fingerprint = originals(args.original, Path(__file__).resolve().parents[1] / "docs/re/001-input-inventory.tsv")
        if len(fingerprint) != 70:
            raise ValueError("固定原版清冊須為 70 檔")
        result = Scanner(fingerprint, args.local_original, args.local_manual).scan(args.scan)
    except (OSError, ValueError, UnicodeError, KeyError, zipfile.BadZipFile, tarfile.TarError) as error:
        parser.exit(1, f"封包外洩掃描失敗：{error}\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
