"""封包清冊與 ZIP 的獨立合成反例；不附原版或手冊。"""
import hashlib
import json
from pathlib import Path
import stat
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package_files as files

VERSION = "v.1.0.0-20261005"
ENGINE = "8d9807df4f191c02eef46a22b6f7bbecb426ef5b"


class PackageFilesCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="phantasie-package-files-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def fixture(self, platform):
        root = self.root / ("幽靈戰士 " + platform)
        root.mkdir()
        if platform == "linux":
            base = root / "usr/bin"
            text, font, backend, manifest = "text", "font", "phantasie-play", "bundle.json"
        elif platform == "windows":
            base = root
            text, font, backend, manifest = "text", "font", "phantasie-play.exe", "bundle.json"
            (root / "README.txt").write_bytes(b"\xef\xbb\xbf" + "合成說明\r\n".encode())
        else:
            base = root / "Phantasie.app/Contents"
            text, font, backend, manifest = "Resources/text", "Resources/font", "MacOS/phantasie-play", "Resources/bundle.json"
        (base / text).mkdir(parents=True)
        (base / font).mkdir(parents=True)
        (base / backend).parent.mkdir(parents=True, exist_ok=True)
        (base / backend).write_bytes(b"SYNTHETIC_BACKEND")
        (base / backend).chmod(0o755)
        for language in ("zh-TW", "zh-CN", "ja", "ko"):
            for family in ("ui", "prose"):
                (base / text / f"{family}.{language}.tsv").write_text("key\ttranslation\tsource\nfixture\t\\c測試\\t%%\tsynthetic\n", encoding="utf-8")
            (base / text / f"manual.{language}.tsv").write_text("key\ttranslation\tsource\nprompt:item\t物品\tsynthetic\nprompt:spell\t法術\tsynthetic\n", encoding="utf-8")
            # 獨立字面集合，不用被測 wanted 字元或其輸出作期望。
            codes = sorted(set(range(32, 127)) | {ord(c) for c in "測試物品法術"})
            font_data = b"GOLEMFNT" + struct.pack("<HHI", 16, 16, len(codes))
            font_data += b"".join(struct.pack("<IB", cp, 1 if cp < 127 else 129) + bytes(32) for cp in codes)
            (base / font / f"{language}.golemfnt").write_bytes(font_data)
        (base / text / "protected.tsv").write_text("key\tnote\nfixture\tsynthetic\n", encoding="utf-8")
        return root, base, text, font, backend, manifest

    def test_three_platform_manifest_paths_and_literal_assets(self):
        for platform in ("linux", "windows", "macos"):
            with self.subTest(platform=platform):
                stage, base, text, font, backend, manifest = self.fixture(platform)
                result = files.bundle(stage, platform, VERSION, ENGINE)
                expected_names = {backend, text + "/protected.tsv"}
                expected_names |= {f"{text}/{family}.{lang}.tsv" for lang in ("zh-TW", "zh-CN", "ja", "ko") for family in ("ui", "prose", "manual")}
                expected_names |= {f"{font}/{lang}.golemfnt" for lang in ("zh-TW", "zh-CN", "ja", "ko")}
                self.assertEqual(result["schema"], 1)
                self.assertEqual(result["version"], VERSION)
                self.assertEqual(result["engine_commit"], ENGINE)
                self.assertEqual({row["name"] for row in result["assets"]}, expected_names)
                self.assertEqual(len(result["assets"]), 18)
                for row in result["assets"]:
                    data = (base / row["name"]).read_bytes()
                    self.assertEqual(row["bytes"], len(data))
                    self.assertEqual(row["sha256"], hashlib.sha256(data).hexdigest())
                self.assertNotIn("local_original", json.loads((base / manifest).read_text()))
                files.bundle(stage, platform, VERSION, ENGINE, verify=True)
                original = (base / manifest).read_bytes()
                with self.assertRaises(FileExistsError):
                    files.bundle(stage, platform, VERSION, ENGINE)
                self.assertEqual((base / manifest).read_bytes(), original)

    def test_each_required_asset_missing_is_rejected(self):
        stage, base, text, font, backend, manifest = self.fixture("windows")
        names = [backend, text + "/protected.tsv"]
        names += [f"{text}/{family}.{lang}.tsv" for lang in ("zh-TW", "zh-CN", "ja", "ko") for family in ("ui", "prose", "manual")]
        names += [f"{font}/{lang}.golemfnt" for lang in ("zh-TW", "zh-CN", "ja", "ko")]
        for name in names:
            path = base / name
            data = path.read_bytes(); path.unlink()
            with self.subTest(name=name), self.assertRaises(OSError):
                files.bundle(stage, "windows", VERSION, ENGINE)
            self.assertFalse((base / manifest).exists())
            path.write_bytes(data)

    def test_changed_manifest_and_same_size_payload_rejected(self):
        stage, base, text, font, backend, manifest = self.fixture("windows")
        files.bundle(stage, "windows", VERSION, ENGINE)
        path = base / backend
        data = path.read_bytes(); path.write_bytes(bytes(len(data)))
        with self.assertRaisesRegex(ValueError, "實際必要資產"):
            files.bundle(stage, "windows", VERSION, ENGINE, verify=True)
        path.write_bytes(data)
        path = base / manifest
        data = path.read_bytes(); path.write_bytes(data.replace(b'"schema": 1', b'"schema": true'))
        with self.assertRaises(ValueError):
            files.bundle(stage, "windows", VERSION, ENGINE, verify=True)

    def test_font_missing_glyph_and_bad_records_rejected(self):
        stage, base, text, font, backend, manifest = self.fixture("windows")
        path = base / font / "zh-TW.golemfnt"
        original = path.read_bytes()
        needed = ord("測")
        # 精確移除一筆已知字模，獨立修正 count；合法長度仍須拒絕缺字。
        count = struct.unpack_from("<I", original, 12)[0]
        records = [original[i:i + 37] for i in range(16, len(original), 37)]
        self.assertEqual(sum(struct.unpack_from("<I", row)[0] == needed for row in records), 1)
        missing = b"GOLEMFNT" + struct.pack("<HHI", 16, 16, count - 1)
        missing += b"".join(row for row in records if struct.unpack_from("<I", row)[0] != needed)
        for data in (missing, original[:-1], original + b"x", original.replace(b"GOLEMFNT", b"BADFONT!", 1),
                     original[:16] + records[0] + original[16:]):
            path.write_bytes(data)
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                files.bundle(stage, "windows", VERSION, ENGINE)
        self.assertFalse((base / manifest).exists())

    def test_keys_answers_source_links_versions_and_execute_mode(self):
        stage, base, text, font, backend, manifest = self.fixture("linux")
        path = base / text / "manual.zh-TW.tsv"
        original = path.read_bytes()
        path.write_bytes(original + b"spell:1\tSYNTHETIC\tfixture\n")
        with self.assertRaisesRegex(ValueError, "兩個標題"):
            files.bundle(stage, "linux", VERSION, ENGINE)
        path.write_bytes(original)
        path = base / text / "ui.ko.tsv"
        original = path.read_bytes(); path.write_bytes(original.replace(b"fixture\t", b"different\t"))
        with self.assertRaisesRegex(ValueError, "鍵集合不同"):
            files.bundle(stage, "linux", VERSION, ENGINE)
        path.write_bytes(original)
        path = base / backend; path.chmod(0o644)
        with self.assertRaisesRegex(ValueError, "執行權限"):
            files.bundle(stage, "linux", VERSION, ENGINE)
        path.chmod(0o755)
        for version, engine in (("1.0", ENGINE), ("v.1.0.0-20260230", ENGINE), (VERSION, "short")):
            with self.subTest(version=version), self.assertRaises(ValueError):
                files.bundle(stage, "linux", version, engine)
        path = base / font / "ko.golemfnt"; original = path.read_bytes(); path.unlink()
        target = self.root / "outside-font"; target.write_bytes(original); path.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "符號連結"):
            files.bundle(stage, "linux", VERSION, ENGINE)
        self.assertFalse((base / manifest).exists())

    def test_deterministic_unicode_zip_permissions_and_source_unchanged(self):
        stage, base, text, font, backend, manifest = self.fixture("windows")
        files.bundle(stage, "windows", VERSION, ENGINE)
        before = {str(p.relative_to(stage)): (p.read_bytes(), p.stat().st_mode) for p in stage.rglob("*") if p.is_file()}
        first, second = self.root / "first.zip", self.root / "second.zip"
        result = files.make_zip(stage, first, VERSION, "windows")
        for path in stage.rglob("*"):
            if path.is_file():
                import os
                os.utime(path, (0, 0))
        files.make_zip(stage, second, VERSION, "windows")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with zipfile.ZipFile(first) as archive:
            for member in archive.infolist():
                self.assertTrue(member.flag_bits & 0x800)
                self.assertEqual(member.date_time, (2026, 10, 5, 0, 0, 0))
            info = archive.getinfo(stage.name + "/" + backend)
            self.assertEqual(info.external_attr >> 16, stat.S_IFREG | 0o755)
        self.assertEqual(before, {str(p.relative_to(stage)): (p.read_bytes(), p.stat().st_mode) for p in stage.rglob("*") if p.is_file()})
        self.assertEqual(result["sha256"], hashlib.sha256(first.read_bytes()).hexdigest())
        with self.assertRaises(FileExistsError):
            files.make_zip(stage, first, VERSION, "windows")
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_windows_readme_and_batch_encoding_controls(self):
        stage, base, text, font, backend, manifest = self.fixture("windows")
        path = stage / "README.txt"
        original = path.read_bytes()
        for data in (original[3:], original.replace(b"\r\n", b"\n"), b"\xef\xbb\xbfinvalid\r"):
            path.write_bytes(data)
            with self.assertRaises(ValueError):
                files.make_zip(stage, self.root / "bad.zip", VERSION, "windows")
            self.assertFalse((self.root / "bad.zip").exists())
        path.write_bytes(original)
        path = stage / "launch.bat"
        for data in (b"\xef\xbb\xbf@echo off\r\n", b"@echo off\n"):
            path.write_bytes(data)
            with self.assertRaises(ValueError):
                files.make_zip(stage, self.root / "bad.zip", VERSION, "windows")
        path.write_bytes(b"@echo off\r\n")
        files.make_zip(stage, self.root / "good.zip", VERSION, "windows")

    def test_zip_extra_missing_changed_and_utf8_flag_rejected(self):
        stage, base, text, font, backend, manifest = self.fixture("macos")
        archive = self.root / "good.zip"
        files.make_zip(stage, archive, VERSION, "macos")
        original = archive.read_bytes()
        with zipfile.ZipFile(archive, "a") as target:
            target.writestr("extra.txt", b"fixture")
        with self.assertRaisesRegex(ValueError, "額外"):
            files.verify_zip(stage, archive, VERSION, "macos")
        archive.write_bytes(original)
        changed = bytearray(original)
        for marker, offset in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
            i = changed.index(marker) + offset
            flag = int.from_bytes(changed[i:i + 2], "little")
            changed[i:i + 2] = (flag & ~0x800).to_bytes(2, "little")
        archive.write_bytes(changed)
        with self.assertRaises(ValueError):
            files.verify_zip(stage, archive, VERSION, "macos")
        archive.write_bytes(original)
        path = base / backend; data = path.read_bytes(); path.write_bytes(bytes(len(data)))
        with self.assertRaisesRegex(ValueError, "雜湊不同"):
            files.verify_zip(stage, archive, VERSION, "macos")
        path.write_bytes(data)
        (base / "new.txt").write_bytes(b"fixture")
        with self.assertRaisesRegex(ValueError, "缺布局項目"):
            files.verify_zip(stage, archive, VERSION, "macos")

    def test_zip_cleanup_and_existing_output_preserved(self):
        stage, base, text, font, backend, manifest = self.fixture("macos")
        archive = self.root / "new.zip"
        with patch.object(files, "verify_zip", side_effect=ValueError("injected verification failure")):
            with self.assertRaises(ValueError):
                files.make_zip(stage, archive, VERSION, "macos")
        self.assertFalse(archive.exists())
        archive.write_bytes(b"EXISTING_OUTPUT")
        with self.assertRaises(FileExistsError):
            files.make_zip(stage, archive, VERSION, "macos")
        self.assertEqual(archive.read_bytes(), b"EXISTING_OUTPUT")

    def test_overlap_links_collisions_and_empty_tree_rejected(self):
        stage = self.root / "plain"; stage.mkdir()
        with self.assertRaisesRegex(ValueError, "沒有檔案"):
            files.make_zip(stage, self.root / "empty.zip", VERSION, "macos")
        (stage / "normal").write_bytes(b"fixture")
        with self.assertRaisesRegex(ValueError, "不得重疊"):
            files.make_zip(stage, stage / "inside.zip", VERSION, "macos")
        (stage / "NORMAL").write_bytes(b"another")
        with self.assertRaisesRegex(ValueError, "重複名稱"):
            files.make_zip(stage, self.root / "bad.zip", VERSION, "macos")
        (stage / "NORMAL").unlink()
        (stage / "link").symlink_to(stage / "normal")
        with self.assertRaisesRegex(ValueError, "符號連結"):
            files.make_zip(stage, self.root / "bad.zip", VERSION, "macos")
        self.assertFalse((self.root / "bad.zip").exists())


if __name__ == "__main__":
    unittest.main()
