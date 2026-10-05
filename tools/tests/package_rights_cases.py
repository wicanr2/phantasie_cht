"""授權材料整理的合成測試；不包含第三方字型或原版。"""
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package_rights as rights


class PackageRightsCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="phantasie-package-rights-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project, self.engine, self.modules, self.runtime = [self.root / n for n in ("project", "engine", "modules", "runtime")]
        for path in (self.project, self.engine, self.modules, self.runtime): path.mkdir()
        self.go = self.root / "go-license"; self.tar = self.root / "font-input.tar.gz"
        self.packet = self.root / "runtime-source.tar.gz"; self.packet.write_bytes(b"SYNTHETIC_SOURCE_PACKET")
        self.output = self.root / "output"
        self.profile = copy.deepcopy(rights.load_profile())
        font = {"COPYING": b"SYNTHETIC COPYING\n", "OFL-1.1.txt": b"SYNTHETIC OFL\n",
                "font/Makefile": b"COPYRIGHT = Synthetic Author \\\n    Synthetic Terms\nall:\n"}
        authors = b"COPYRIGHT = Synthetic Author \\\n    Synthetic Terms\n"
        with tarfile.open(self.tar, "w:gz") as archive:
            for name, data in font.items():
                member = tarfile.TarInfo("unifont-17.0.05/" + name); member.size = len(data)
                archive.addfile(member, io.BytesIO(data))
        self.profile["unifont_sha256"] = hashlib.sha256(self.tar.read_bytes()).hexdigest()
        self.profile["unifont_makefile_sha256"] = hashlib.sha256(font["font/Makefile"]).hexdigest()
        self.expected = {}
        for row in self.profile["common"]:
            kind = row["kind"]
            if kind == "unifont": data = authors if row["source"] == "author-source" else font[row["source"]]
            else:
                data = ("SYNTHETIC " + row["name"] + "\n").encode()
                path = {"project": self.project / row["source"], "engine": self.engine / row["source"],
                        "modules": self.modules / row["source"], "go": self.go}[kind]
                path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
            row["bytes"] = len(data); row["sha256"] = hashlib.sha256(data).hexdigest()
            self.expected["common/" + row["name"]] = data
        names = {row["source"].split("@", 1)[0] + "@" + row["source"].split("@", 1)[1].split("/", 1)[0]
                 for row in self.profile["common"] if row["kind"] == "modules"}
        for name in names:
            (self.modules / name / "fixture.go").write_text("// Copyright Synthetic Authors\n// SPDX-License-Identifier: Apache-2.0\n\npackage fixture\n", encoding="utf-8")
        for row in self.profile["runtime"]:
            data = ("SYNTHETIC " + row["name"] + "\n").encode()
            path = self.runtime / row["source"]; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
            row["bytes"] = len(data); row["sha256"] = hashlib.sha256(data).hexdigest()
            self.expected["runtime/" + row["name"]] = data
        self.profile["runtime_source"]["bytes"] = self.packet.stat().st_size
        self.profile["runtime_source"]["sha256"] = hashlib.sha256(self.packet.read_bytes()).hexdigest()

    def prepare(self, runtime=False, output=None):
        with patch.object(rights, "load_profile", return_value=self.profile):
            return rights.prepare(output or self.output, self.project, self.engine, self.modules, self.go, self.tar,
                                  self.runtime if runtime else None, self.packet if runtime else None)

    def test_exact_common_and_runtime_payloads_without_font_assets(self):
        result = self.prepare(True)
        self.assertEqual(result["font_terms"], "pending user election")
        self.assertEqual(len(result["files"]), 35)
        self.assertEqual(result["module_header_notices"], 6)
        for name, expected in self.expected.items(): self.assertEqual((self.output / name).read_bytes(), expected)
        self.assertEqual((self.output / "runtime/runtime-source-r1.tar.gz").read_bytes(), b"SYNTHETIC_SOURCE_PACKET")
        self.assertFalse(any(p.suffix in (".golemfnt", ".hex") for p in self.output.rglob("*")))
        notices = json.loads((self.output / "common/module-source-notices.json").read_text())
        self.assertEqual(len(notices["notices"]), 6)
        for row in notices["notices"]:
            self.assertEqual(row["notice"], "// Copyright Synthetic Authors\n// SPDX-License-Identifier: Apache-2.0")
            self.assertNotIn("package fixture", row["notice"])

    def test_common_without_runtime_and_existing_output_preserved(self):
        result = self.prepare()
        self.assertEqual(len(result["files"]), 21)
        self.assertFalse(result["with_runtime"])
        self.assertFalse((self.output / "runtime").exists())
        before = (self.output / "rights-inputs.json").read_bytes()
        with self.assertRaises(ValueError): self.prepare()
        self.assertEqual((self.output / "rights-inputs.json").read_bytes(), before)

    def test_same_length_license_corruption_and_missing_inputs(self):
        path = self.engine / "LICENSE"; original = path.read_bytes(); path.write_bytes(bytes(len(original)))
        with self.assertRaisesRegex(ValueError, "固定清單不符"): self.prepare()
        self.assertFalse(self.output.exists())
        path.write_bytes(original); self.go.unlink()
        with self.assertRaises(OSError): self.prepare()
        self.assertFalse(self.output.exists())

    def test_source_links_overlap_and_runtime_pair_rejected(self):
        path = self.engine / "LICENSE"; data = path.read_bytes(); path.unlink()
        outside = self.root / "outside"; outside.write_bytes(data); path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "符號連結"): self.prepare()
        path.unlink(); path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "不得重疊"): self.prepare(output=self.project / "output")
        with self.assertRaisesRegex(ValueError, "同時明示"):
            rights.prepare(self.output, self.project, self.engine, self.modules, self.go, self.tar, self.runtime)
        self.assertFalse(self.output.exists())

    def test_wrong_font_source_and_runtime_packet_rejected(self):
        original = self.tar.read_bytes(); self.tar.write_bytes(b"WRONG_SOURCE")
        with self.assertRaisesRegex(ValueError, "來源壓縮檔不符"): self.prepare()
        self.tar.write_bytes(original); self.packet.write_bytes(b"WRONG_PACKET")
        with self.assertRaisesRegex(ValueError, "固定清單不符"): self.prepare(True)
        self.assertFalse(self.output.exists())

    def test_failed_write_removes_only_new_output(self):
        original_open = Path.open
        def fail_index(path, *args, **kwargs):
            if path == self.output / "rights-inputs.json": raise OSError("synthetic write failure")
            return original_open(path, *args, **kwargs)
        with patch.object(Path, "open", fail_index), self.assertRaises(OSError): self.prepare()
        self.assertFalse(self.output.exists())
        self.assertEqual((self.project / "LICENSE").read_bytes(), self.expected["common/LICENSE-project"])

    def test_full_leading_comments_and_no_program_body(self):
        data = b"/* Copyright First\nPermission to redistribute\n*/\n\n// SPDX-License-Identifier: MIT\nint program_body;\n"
        self.assertEqual(rights.leading_notice(data), "/* Copyright First\nPermission to redistribute\n*/\n\n// SPDX-License-Identifier: MIT")
        self.assertEqual(rights.leading_notice(b"package fixture\n// Copyright body\n"), "")
        self.assertEqual(rights.leading_notice(b"/* Copyright First\nLicense synthetic\n*/ int program_body;\n"),
                         "/* Copyright First\nLicense synthetic\n*/")
        self.assertEqual(rights.leading_notice(b"/* Copyright First */ int program_body;\n"),
                         "/* Copyright First */")
        with self.assertRaisesRegex(ValueError, "未結束"): rights.leading_notice(b"/* Copyright unfinished\n")


if __name__ == "__main__": unittest.main()
