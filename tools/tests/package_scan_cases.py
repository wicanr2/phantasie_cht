"""封包外洩掃描的合成反例；不使用原版或手冊內容。"""
import csv
import hashlib
import gzip
import io
from pathlib import Path
import stat
import sys
import tarfile
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package_scan as scan


class PackageScanCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="phantasie-package-scan-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.original = self.base / "原版 唯讀"
        self.original.mkdir()
        self.inventory = self.base / "inventory.tsv"
        self.inputs = {"ORIGINAL.EXE": b"SYNTHETIC_ORIGINAL_BYTES", "EMPTY.EXO": b""}
        with self.inventory.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")
            writer.writerow(["name", "bytes", "sha256"])
            for name, data in self.inputs.items():
                (self.original / name).write_bytes(data)
                writer.writerow([name, len(data), hashlib.sha256(data).hexdigest()])
        self.fingerprint = scan.originals(self.original, self.inventory)
        self.bundle = self.base / "中文 封包"
        self.bundle.mkdir()
        (self.bundle / "README.txt").write_text("合成封包\n", encoding="utf-8")
        self.before = {p.name: p.read_bytes() for p in self.original.iterdir()}

    def tearDown(self):
        self.assertEqual(self.before, {p.name: p.read_bytes() for p in self.original.iterdir()})

    def scanner(self, **kwargs):
        return scan.Scanner(self.fingerprint, **kwargs)

    def archive(self, name, entries, tar=False):
        path = self.base / name
        if tar:
            with tarfile.open(path, "w:gz") as archive:
                for member, data in entries:
                    info = tarfile.TarInfo(member)
                    info.size = len(data)
                    archive.addfile(info, io.BytesIO(data))
        else:
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
                for member, data in entries:
                    archive.writestr(member, data)
        return path

    def test_clean_directory_and_unicode_zip(self):
        result = self.scanner().scan(self.bundle)
        self.assertEqual(result["rights"], "no-original-or-manual-answers")
        self.assertEqual(result["files"], 1)
        zipped = self.archive("clean.zip", [("中文 資料/README.txt", b"fixture")])
        self.assertEqual(self.scanner().scan(zipped)["archives"], 1)

    def test_filename_hash_and_empty_file_rejected(self):
        for name, data in [("original.exe", b"changed"), ("renamed.bin", self.inputs["ORIGINAL.EXE"]),
                           ("renamed-empty", b"")]:
            with self.subTest(name=name):
                path = self.bundle / name
                path.write_bytes(data)
                with self.assertRaisesRegex(ValueError, "原版檔名或 SHA"):
                    self.scanner().scan(self.bundle)
                path.unlink()

    def test_missing_wrong_original_and_symbolic_links(self):
        with self.assertRaises(ValueError):
            scan.originals(self.base / "missing", self.inventory)
        other = self.base / "other"
        other.mkdir()
        (other / "ORIGINAL.EXE").write_bytes(b"wrong")
        (other / "EMPTY.EXO").write_bytes(b"")
        with self.assertRaises(ValueError):
            scan.originals(other, self.inventory)
        path = self.bundle / "link"
        path.symlink_to(self.original / "ORIGINAL.EXE")
        with self.assertRaises(ValueError):
            self.scanner().scan(self.bundle)

    def test_private_inputs_and_empty_original_directory(self):
        for name in ["answers.tsv", "manual.pdf", "normal.route", "evidence.i64", "manual-labels.zh-TW.tsv"]:
            path = self.bundle / name
            path.write_bytes(b"fixture")
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.scanner().scan(self.bundle)
            path.unlink()
        for name in ["workplace", "original", "manual-derived"]:
            path = self.bundle / name
            path.mkdir()
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.scanner().scan(self.bundle)
            path.rmdir()

    def test_manual_titles_and_hidden_answers(self):
        path = self.bundle / "manual.zh-TW.tsv"
        clean = b"key\ttranslation\tsource\nprompt:item\tITEM\tfixture\nprompt:spell\tSPELL\tfixture\n"
        path.write_bytes(clean)
        self.scanner().scan(self.bundle)
        for data in [clean + b"spell:1\tSYNTHETIC\tfixture\n", clean + b"answer\tTEMPLATE\tfixture\n",
                     clean.replace(b"prompt:spell", b"prompt:other"), clean.replace(b"\n", b"\r\n")]:
            path.write_bytes(data)
            with self.assertRaises(ValueError):
                self.scanner().scan(self.bundle)
        path.unlink()
        (self.bundle / "disguised.bin").write_bytes(b"prefix\nitem:FIXTURE\tSYNTHETIC\tfixture\n")
        with self.assertRaises(ValueError):
            self.scanner().scan(self.bundle)

    def test_nested_archives_and_renamed_archive(self):
        inner = self.archive("inner.zip", [("renamed.bin", self.inputs["ORIGINAL.EXE"])])
        outer = self.archive("outer.tar.gz", [("inner.bin", inner.read_bytes())], tar=True)
        with self.assertRaisesRegex(ValueError, "原版檔名或 SHA"):
            self.scanner().scan(outer)
        hidden = self.archive("gzip.zip", [("opaque.bin", gzip.compress(self.inputs["ORIGINAL.EXE"]))])
        with self.assertRaisesRegex(ValueError, "原版檔名或 SHA"):
            self.scanner().scan(hidden)
        clean = self.archive("opaque.bin", [("note.txt", b"fixture")])
        self.assertEqual(self.scanner().scan(clean)["archives"], 1)
        corrupt = self.base / "broken.zip"
        corrupt.write_bytes(b"not an archive")
        with self.assertRaises(ValueError):
            self.scanner().scan(corrupt)
        plain = self.base / "opaque.AppImage"
        plain.write_bytes(b"not an unpacked image")
        with self.assertRaises(ValueError):
            self.scanner().scan(plain)
        for magic in [b"7z\xbc\xaf\x27\x1c", b"Rar!\x1a\x07", b"\xfd7zXZ\x00", b"BZh"]:
            (self.bundle / "unsupported.bin").write_bytes(magic + b"fixture")
            with self.subTest(magic=magic), self.assertRaises(ValueError):
                self.scanner().scan(self.bundle)

    def test_zstandard_frames_and_extensions_rejected(self):
        # libzstd 1.5.4 ZSTD_compress(level=1) 的合法合成 frame；非原版輸入。
        frame = bytes.fromhex("28b52ffd2018c1000053594e5448455449435f4f524947494e414c5f4259544553")
        # 1.5.6 doc/zstd_compression_format.md：magic + uint32 length + user data。
        frames = [frame] + [magic.to_bytes(4, "little") + bytes(4) + frame
                            for magic in range(0x184D2A50, 0x184D2A60)]
        path = self.bundle / "opaque.bin"
        for data in frames:
            path.write_bytes(data)
            with self.subTest(magic=data[:4].hex()), self.assertRaisesRegex(ValueError, "壓縮檔無法讀取"):
                self.scanner().scan(self.bundle)
        path.unlink()
        for name in ["opaque.zst", "opaque.zstd"]:
            path = self.bundle / name
            path.write_bytes(b"unsupported archive")
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.scanner().scan(self.bundle)
            path.unlink()

    def test_zip_and_tar_paths_duplicates_links_and_limits(self):
        for member in ["../escape", "/absolute", "C:/drive", "folder\\file", "a//b", "a/\nfile"]:
            path = self.archive("invalid.zip", [(member, b"fixture")])
            with self.subTest(member=member), self.assertRaises(ValueError):
                self.scanner().scan(path)
        duplicate = self.archive("duplicate.zip", [("A.txt", b"one"), ("a.txt", b"two")])
        with self.assertRaisesRegex(ValueError, "重複"):
            self.scanner().scan(duplicate)
        linked = self.base / "linked.tar"
        with tarfile.open(linked, "w") as archive:
            info = tarfile.TarInfo("link")
            info.type = tarfile.SYMTYPE
            info.linkname = "../target"
            archive.addfile(info)
        with self.assertRaises(ValueError):
            self.scanner().scan(linked)
        for mode in [stat.S_IFIFO, stat.S_IFSOCK, stat.S_IFCHR, stat.S_IFLNK]:
            path = self.base / "special.zip"
            with zipfile.ZipFile(path, "w") as archive:
                info = zipfile.ZipInfo("special")
                info.create_system = 3
                info.external_attr = (mode | 0o600) << 16
                archive.writestr(info, b"fixture")
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "特殊檔案"):
                self.scanner().scan(path)
        path = self.archive("directory-payload.zip", [("folder/", self.inputs["ORIGINAL.EXE"])])
        with self.assertRaisesRegex(ValueError, "目錄項目不得含資料"):
            self.scanner().scan(path)
        previous = scan.MAX_FILE
        try:
            scan.MAX_FILE = 3
            with self.assertRaises(ValueError):
                self.scanner().scan(self.bundle)
        finally:
            scan.MAX_FILE = previous

    def test_zip_unicode_missing_flag_rejected(self):
        path = self.archive("unicode.zip", [("中文.txt", b"fixture")])
        data = bytearray(path.read_bytes())
        # 保留名稱原始 UTF-8 bytes，只在實際 local/central header 清 bit 11。
        for marker, delta in [(b"PK\x03\x04", 6), (b"PK\x01\x02", 8)]:
            offset = data.index(marker) + delta
            flag = int.from_bytes(data[offset:offset + 2], "little")
            self.assertEqual(flag & 0x800, 0x800)
            data[offset:offset + 2] = (flag & ~0x800).to_bytes(2, "little")
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            self.scanner().scan(path)

    def test_fixed_source_archive_does_not_accept_arbitrary_exemption(self):
        path = self.bundle / "runtime-source-r1.tar.gz"
        path.write_bytes(b"not the approved source bytes")
        with self.assertRaises(ValueError):
            self.scanner().scan(self.bundle)

    def test_local_complete_directory_and_zip(self):
        local = self.base / "local-tables"
        local.mkdir()
        text = self.bundle / "text"
        text.mkdir()
        rows = ["prompt:item\tITEM\tfixture", "prompt:spell\tSPELL\tfixture"]
        rows += [f"item:FIXTURE {i}\tSYNTHETIC\tfixture" for i in range(100)]
        rows += [f"spell:{i}\tSYNTHETIC\tfixture" for i in range(1,55)]
        data = ("key\ttranslation\tsource\n" + "\n".join(rows) + "\n").encode()
        for language in ("zh-TW", "zh-CN", "ja", "ko"):
            (local / f"manual.{language}.tsv").write_bytes(data)
            (text / f"manual.{language}.tsv").write_bytes(data)
        original = self.bundle / "original"
        original.mkdir()
        for name, contents in self.inputs.items():
            (original / name).write_bytes(contents)
        args = {"local_original": "original", "local_manual": local}
        result = self.scanner(**args).scan(self.bundle)
        self.assertEqual(result["rights"], "local-only")
        with self.assertRaisesRegex(ValueError, "不得重疊"):
            self.scanner(local_original="original", local_manual=text).scan(self.bundle)
        zipped = self.archive("local.zip", [(p.relative_to(self.bundle).as_posix(),p.read_bytes())
                                              for p in self.bundle.rglob("*") if p.is_file()])
        self.assertEqual(self.scanner(**args).scan(zipped)["rights"], "local-only")
        with self.assertRaises(ValueError):
            self.scanner().scan(zipped)
        (text / "manual.ko.tsv").unlink()
        with self.assertRaisesRegex(ValueError, "缺原版或本機提示"):
            self.scanner(**args).scan(self.bundle)
        with self.assertRaises(ValueError):
            self.scanner(local_original="original")


if __name__ == "__main__":
    unittest.main()
