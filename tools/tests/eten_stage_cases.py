"""014：三平台倚天布局與來源隔離的合成反例。"""
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest
from unittest.mock import patch

import eten_font_cases as font_cases
import package_stage_cases as stage_cases

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_eten_font as eten
import package_files as pf
import package_stage as stage


class EtenStageCases(unittest.TestCase):
    def setUp(self):
        self.layout = stage_cases.PackageStageCases(); self.layout.setUp()
        self.addCleanup(self.layout.doCleanups)
        self.font = font_cases.EtenFontCases(); self.font.setUp()
        self.addCleanup(self.font.doCleanups)
        self.sources = patch.object(eten, "SOURCES", self.font.fingerprints)
        self.sources.start(); self.addCleanup(self.sources.stop)

    def prepare(self, platform="windows", output=None):
        self.layout.binaries(platform)
        return self.layout.prepare(platform, local=True, output=output, eten_dir=self.font.source)

    def test_three_local_platforms_with_literal_source_records(self):
        for platform in ("linux", "windows", "macos"):
            with self.subTest(platform=platform):
                dest = self.layout.root / (platform + "-eten")
                result = self.prepare(platform, dest)
                base, _, _, _, font_dir, _ = pf.profile(dest, platform)
                data = (base / font_dir / "zh-TW.golemfnt").read_bytes()
                self.assertEqual(data[-37:], struct.pack("<IB", 0x4E2D, 0x82) + bytes(range(1, 31)) + bytes(2))
                for language in ("zh-CN", "ja", "ko"):
                    other = (base / font_dir / (language + ".golemfnt")).read_bytes()
                    self.assertEqual(other[-37:], struct.pack("<IB", 0x4E2D, 0x81) + bytes(32))
                info = result["fonts"]["zh-TW"]
                self.assertEqual(info["rights"], "local-only")
                self.assertEqual(info["eten"]["sources"], {name: {"bytes": size, "sha256": sha}
                                                          for name, (size, sha) in self.font.fingerprints.items()})
                self.assertEqual(json.loads((dest / "LICENSES.json").read_bytes())["fonts"], result["fonts"])
                self.assertIn("繁體中文全形採本機倚天", (dest / "README.txt").read_text(encoding="utf-8-sig"))
                self.assertFalse(any(p.name in eten.SOURCES for p in dest.rglob("*")))
                pf.bundle(dest, platform, "v.1.0.0-20261005", "b" * 40, self.layout.text, verify=True)

    def test_public_stage_and_other_language_reject_eten(self):
        self.layout.binaries("windows")
        with self.assertRaisesRegex(ValueError, "僅接受本機"):
            self.layout.prepare(eten_dir=self.font.source)
        self.assertFalse(self.layout.output.exists())
        self.prepare()
        font = self.layout.output / "font/ko.golemfnt"
        data = font.read_bytes(); font.write_bytes(data[:-33] + b"\x82" + data[-32:])
        with self.assertRaisesRegex(ValueError, "來源旗標"):
            pf.bundle(self.layout.output, "windows", "v.1.0.0-20261005", "b" * 40, self.layout.text, verify=True)

    def test_metadata_cannot_label_gnu_as_eten_or_move_eten_to_patch(self):
        result = self.prepare()
        stage.validate_fonts(self.layout.output, "font", result["fonts"], True, "OFL-1.1")
        with self.assertRaises(ValueError): stage.validate_fonts(self.layout.output, "font", result["fonts"], False, "OFL-1.1")
        entry = result["fonts"]["zh-TW"]; entry["eten"]["source_height"] = 16
        with self.assertRaisesRegex(ValueError, "尺寸"):
            stage.validate_fonts(self.layout.output, "font", result["fonts"], True, "OFL-1.1")

    def test_wrapper_eten_requires_formal_local_before_git_or_docker(self):
        wrapper = str(Path(stage.__file__).with_name("package.sh"))
        for args, expected in ((["--eten-dir", str(self.font.source)], "正式本機完整版"),
                               (["--build-only", "--local", "--eten-dir", str(self.font.source)], "正式本機完整版"),
                               (["--local"], "須明示 --eten-dir")):
            p = subprocess.run(["bash", wrapper, "windows", "--version", "v.1.0.0-20261005", *args],
                               capture_output=True, timeout=10)
            self.assertEqual(p.returncode, 1)
            self.assertIn(expected, p.stderr.decode())


if __name__ == "__main__": unittest.main()
