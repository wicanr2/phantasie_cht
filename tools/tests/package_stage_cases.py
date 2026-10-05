"""平台組裝的合成測試；自製字模及資料，不含原版或第三方字型。"""
import hashlib
import io
import json
from pathlib import Path
import plistlib
import struct
import subprocess
import sys
import tarfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package_files as pf
import package_rights as rights
import package_scan as scan
import package_stage as stage
import package_rights_cases as rights_cases


class PackageStageCases(unittest.TestCase):
    def setUp(self):
        self.fixture = rights_cases.PackageRightsCases()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        self.root = f.root
        # 保留合成條款，另放自製全零字模。沒有讀取 GNU 字型。
        with tarfile.open(f.tar) as archive:
            members = {m.name: archive.extractfile(m).read() for m in archive.getmembers()}
        self.hex = ("".join(f"{c:04X}:" + "00" * 16 + "\n" for c in range(32, 127)) +
                    "4E2D:" + "00" * 32 + "\n").encode()
        self.font_members = {lang: (name, pf.digest(self.hex)) for lang, (name, _) in stage.FONT_MEMBERS.items()}
        for name, _ in set(self.font_members.values()):
            members["unifont-17.0.05/font/precompiled/" + name] = self.hex
        with tarfile.open(f.tar, "w:gz") as archive:
            for name, data in members.items():
                info = tarfile.TarInfo(name); info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
        f.profile["unifont_sha256"] = pf.digest(f.tar.read_bytes())
        with tarfile.open(f.packet, "w:gz") as archive:
            data = b"Synthetic public source\n"
            info = tarfile.TarInfo("source.c"); info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
        f.profile["runtime_source"].update(bytes=f.packet.stat().st_size, sha256=pf.digest(f.packet.read_bytes()))
        self.profile_patch = patch.object(rights, "load_profile", return_value=f.profile)
        self.profile_patch.start(); self.addCleanup(self.profile_patch.stop)
        self.font_patch = patch.object(stage, "FONT_MEMBERS", self.font_members)
        self.font_patch.start(); self.addCleanup(self.font_patch.stop)
        f.prepare(True)
        self.text = self.root / "text"; self.text.mkdir()
        for lang in stage.pt.LANGUAGES:
            for family in ("ui", "prose"):
                (self.text / f"{family}.{lang}.tsv").write_text("key\ttranslation\tsource\nfixture\t中\tFixture\n")
            titles = "prompt:item\t中\tItem\nprompt:spell\t中\tSpell\n"
            (self.text / f"manual-labels.{lang}.tsv").write_text("key\ttranslation\tsource\n" + titles + "answer\t%v\tAnswer\n")
            items = "".join(f"item:synthetic{n}\t{n}\tSynthetic\n" for n in range(100))
            spells = "".join(f"spell:{n}\t{n}\tSynthetic\n" for n in range(1, 55))
            (self.text / f"manual.{lang}.tsv").write_text("key\ttranslation\tsource\n" + titles + items + spells)
        (self.text / "protected.tsv").write_text("key\tnote\nFixture\tSynthetic\n")
        self.original = self.root / "original"; self.original.mkdir()
        self.fingerprints = {}
        for n in range(70):
            name = f"FILE{n:02}.DAT"; data = f"SYNTHETIC original input {n}\n".encode()
            (self.original / name).write_bytes(data)
            self.fingerprints[name.casefold()] = len(data), pf.digest(data)
        original_patch = patch.object(scan, "originals", return_value=self.fingerprints)
        original_patch.start(); self.addCleanup(original_patch.stop)
        self.launcher, self.backend, self.receipt, self.arm = [self.root / n for n in ("launcher", "backend", "receipt", "arm")]
        self.output = self.root / "stage"

    @staticmethod
    def header(platform, cpu=0x01000007, console=False):
        if platform == "linux":
            data = bytearray(64); data[:6] = b"\x7fELF\x02\x01"; struct.pack_into("<H", data, 18, 62)
        elif platform == "windows":
            data = bytearray(192); data[:2] = b"MZ"; struct.pack_into("<I", data, 60, 64)
            data[64:68] = b"PE\0\0"; struct.pack_into("<H", data, 68, 0x8664)
            struct.pack_into("<H", data, 88, 0x20B); struct.pack_into("<H", data, 156, 3 if console else 2)
        else:
            data = bytearray(32); data[:4] = bytes.fromhex("cffaedfe"); struct.pack_into("<I", data, 4, cpu)
        return bytes(data)

    def binaries(self, platform):
        if platform == "macos":
            amd, arm = self.header(platform), self.header(platform, 0x0100000C)
            fat = bytes.fromhex("cafebabe") + struct.pack(">I", 2)
            fat += struct.pack(">IIIII", 0x01000007, 0, 48, 32, 4)
            fat += struct.pack(">IIIII", 0x0100000C, 0, 80, 32, 4) + amd + arm
            self.launcher.write_bytes(fat); self.backend.write_bytes(fat)
            self.receipt.write_bytes(amd); self.arm.write_bytes(arm)
        else:
            self.launcher.write_bytes(self.header(platform)); self.backend.write_bytes(self.header(platform))
            self.receipt.write_bytes(self.header(platform, console=True))

    def prepare(self, platform="windows", local=False, font_license="OFL-1.1", output=None):
        return stage.prepare(output or self.output, platform, "v.1.0.0-20261005", "a" * 40, "b" * 40,
                             font_license, self.text, self.fixture.tar, self.fixture.output, self.original,
                             self.launcher, self.backend, self.receipt, self.arm if platform == "macos" else None, local)

    def test_three_platform_layouts_and_actual_fonts(self):
        for platform in ("linux", "windows", "macos"):
            with self.subTest(platform=platform):
                self.binaries(platform)
                result = self.prepare(platform, output=self.root / platform)
                output = self.root / platform
                self.assertEqual(result["rights"], "no-original-or-manual-answers")
                base, manifest, backend, text, font, _ = pf.profile(output, platform)
                bundle = json.loads((base / manifest).read_bytes())
                self.assertEqual(len(bundle["assets"]), 18)
                self.assertEqual(bundle["version"], "v.1.0.0-20261005")
                for lang in stage.pt.LANGUAGES:
                    data = (base / font / f"{lang}.golemfnt").read_bytes()
                    self.assertEqual(data[:8], b"GOLEMFNT")
                    self.assertEqual(struct.unpack_from("<HHI", data, 8), (16, 16, 96))
                    # 字模獨立字面 oracle：95 個半形 ASCII 與一個全形「中」。
                    expected = b"".join(struct.pack("<IB", cp, 1 if cp < 127 else 129) + bytes(32)
                                        for cp in [*range(32, 127), 0x4E2D])
                    self.assertEqual(data[16:], expected)
                    self.assertEqual(len(stage.pt.catalog(base / text / f"manual.{lang}.tsv")[1]), 2)
                self.assertFalse(any(p.name == "original" for p in output.rglob("*")))
                self.assertFalse((output / "licenses/unifont/unifont-17.0.05.tar.gz").exists())
                self.assertEqual((output / "LICENSE").read_bytes(), self.fixture.expected["common/LICENSE-project"])
                expected_files = {name: row for name, row in pf.snapshot(output).items()
                                  if not row["directory"] and not name.endswith("/package-stage.json")}
                self.assertEqual(result["files"], expected_files)
                self.assertEqual((output / "licenses/runtime").exists(), platform == "linux")
                if platform == "macos":
                    info = plistlib.loads((base / "Info.plist").read_bytes())
                    self.assertEqual(info["CFBundleShortVersionString"], "1.0.0")
                    self.assertEqual(info["PhantasieReleaseVersion"], "v.1.0.0-20261005")
                if platform == "windows": pf.windows_text(output)

    def test_local_variant_and_gpl_source_pair(self):
        self.binaries("windows")
        before = {p: pf.digest(p.read_bytes()) for root in (self.original, self.text) for p in root.iterdir()}
        result = self.prepare(local=True, font_license="GPL-2.0-or-later-with-font-exception")
        self.assertEqual(result["rights"], "local-only")
        self.assertEqual({p.name for p in (self.output / "original").iterdir()}, {p.name for p in self.original.iterdir()})
        for lang in stage.pt.LANGUAGES:
            self.assertEqual((self.output / "text" / f"manual.{lang}.tsv").read_bytes(), (self.text / f"manual.{lang}.tsv").read_bytes())
        self.assertEqual((self.output / "licenses/unifont/unifont-17.0.05.tar.gz").read_bytes(), self.fixture.tar.read_bytes())
        self.assertEqual({p: pf.digest(p.read_bytes()) for p in before}, before)

    def test_wrong_binary_and_subsystem_rejected(self):
        self.binaries("windows")
        self.launcher.write_bytes(self.header("linux"))
        with self.assertRaisesRegex(ValueError, "Windows 二進位"): self.prepare()
        self.binaries("windows"); self.receipt.write_bytes(self.header("windows"))
        with self.assertRaisesRegex(ValueError, "子系統"): self.prepare()
        self.assertFalse(self.output.exists())
        fat = bytearray(bytes.fromhex("cafebabe") + struct.pack(">I", 2) + bytes(104))
        struct.pack_into(">IIIII", fat, 8, 0x01000007, 0, 48, 32, 4)
        struct.pack_into(">IIIII", fat, 28, 0x0100000C, 0, 48, 32, 4)
        fat[48:80] = self.header("macos")
        with self.assertRaises(ValueError): stage.binary(bytes(fat), "macos", "universal")

    def test_explicit_terms_source_fingerprints_and_missing_license(self):
        self.binaries("windows")
        for election in ("", "automatic"):
            with self.assertRaisesRegex(ValueError, "不採預設"): self.prepare(font_license=election)
        data = self.fixture.tar.read_bytes(); self.fixture.tar.write_bytes(b"WRONG")
        with self.assertRaisesRegex(ValueError, "字型來源壓縮檔不符"): self.prepare()
        self.fixture.tar.write_bytes(data)
        license = self.fixture.output / "common/LICENSE-project"; license.write_bytes(b"WRONG")
        with self.assertRaisesRegex(ValueError, "固定清單不符"): self.prepare()
        self.assertFalse(self.output.exists())

    def test_missing_glyph_cleanup_existing_output_and_overlap(self):
        self.binaries("windows")
        path = self.text / "ui.zh-TW.tsv"; path.write_text("key\ttranslation\tsource\nfixture\t缺\tFixture\n")
        with self.assertRaisesRegex(ValueError, "字型重建失敗"): self.prepare()
        self.assertFalse(self.output.exists()); self.assertTrue(self.fixture.output.exists())
        path.write_text("key\ttranslation\tsource\nfixture\t中\tFixture\n")
        with self.assertRaisesRegex(ValueError, "不得重疊"): self.prepare(output=self.text / "stage")
        self.output.mkdir(); marker = self.output / "keep"; marker.write_bytes(b"preserve")
        with self.assertRaisesRegex(ValueError, "新目錄"): self.prepare()
        self.assertEqual(marker.read_bytes(), b"preserve")

    def test_linux_runtime_required_and_local_input_verified(self):
        self.binaries("linux")
        common = self.root / "common"
        self.fixture.prepare(output=common)
        with self.assertRaisesRegex(ValueError, "Linux 缺 runtime"):
            stage.rights_files(common, True)
        self.binaries("windows")
        (self.original / "FILE00.DAT").write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "本機原版來源改變"): self.prepare(local=True)
        self.assertFalse(self.output.exists())

    def test_apprun_preserves_working_directory_and_arguments(self):
        app = self.root / "中文 App"; (app / "usr/bin").mkdir(parents=True)
        (app / "AppRun").write_bytes(stage.APPRUN); (app / "AppRun").chmod(0o755)
        stub = app / "usr/bin/phantasie"
        stub.write_bytes(b'#!/bin/sh\nprintf "%s\\n" "$@"\n'); stub.chmod(0o755)
        result = subprocess.run([str(app / "AppRun"), "中文 參數", "--fixture"], cwd=self.root, capture_output=True, check=True)
        self.assertEqual(result.stdout.decode(), "中文 參數\n--fixture\n")

    def test_cli_has_no_default_font_election(self):
        result = subprocess.run([sys.executable, "-B", str(Path(stage.__file__)), "--platform", "windows"], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"--font-license", result.stderr)
        self.assertFalse(self.output.exists())


if __name__ == "__main__": unittest.main()
