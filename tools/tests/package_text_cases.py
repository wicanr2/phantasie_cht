"""規格 013 的封包譯文邊界反例。只用合成文字，在 Docker 內執行。"""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package_text as package


class PackageTextCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="phantasie-package-text-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / "含 空白 譯文"
        self.source.mkdir()
        self.output = self.base / "含 空白 輸出"
        for language in ("zh-TW", "zh-CN", "ja", "ko"):
            for family in ("ui", "prose"):
                (self.source / f"{family}.{language}.tsv").write_text(
                    "key\ttranslation\tsource\nTEST\t測試\tfixture\n", encoding="utf-8")
            (self.source / f"manual-labels.{language}.tsv").write_text(
                "key\ttranslation\tsource\nprompt:item\tITEM\tfixture\n"
                "prompt:spell\tSPELL\tfixture\nanswer\tTEMPLATE %s\tfixture\n", encoding="utf-8")
            # 即使本機表不是合法 UTF-8，無答案模式也不能讀它。
            (self.source / f"manual.{language}.tsv").write_bytes(b"\xffPRIVATE_FIXTURE")
        (self.source / "protected.tsv").write_text("key\tnote\nTEST\t保護\n", encoding="utf-8")
        (self.source / "original-fixture.bin").write_bytes(b"DO_NOT_COPY")

    def prepare(self, local=False):
        return package.prepare(self.source, self.output, "v.1.0.0-20261005", local)

    def test_no_answers_exact_files_and_input_preservation(self):
        before = {p.name: p.read_bytes() for p in self.source.iterdir()}
        result = self.prepare()
        expected = {f"{family}.{lang}.tsv" for lang in ("zh-TW", "zh-CN", "ja", "ko")
                    for family in ("ui", "prose", "manual")} | {"protected.tsv"}
        self.assertEqual({p.name for p in (self.output / "text").iterdir()}, expected)
        for lang in ("zh-TW", "zh-CN", "ja", "ko"):
            self.assertEqual((self.output / "text" / f"manual.{lang}.tsv").read_text(),
                             "key\ttranslation\tsource\nprompt:item\tITEM\tfixture\n"
                             "prompt:spell\tSPELL\tfixture\n")
        self.assertEqual(result["rights"], "no-original-or-manual-answers")
        self.assertEqual(json.loads((self.output / "runtime-text.json").read_text())["version"],
                         "v.1.0.0-20261005")
        self.assertEqual({p.name: p.read_bytes() for p in self.source.iterdir()}, before)

    def test_missing_input_does_not_leave_output(self):
        (self.source / "protected.tsv").unlink()
        with self.assertRaises(OSError):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_existing_output_preserved(self):
        self.output.mkdir()
        marker = self.output / "KEEP"
        marker.write_bytes(b"existing data")
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertEqual(marker.read_bytes(), b"existing data")

    def test_overlap_rejected(self):
        with self.assertRaises(ValueError):
            package.prepare(self.source, self.source / "out", "v.1.0.0-20261005")
        self.assertFalse((self.source / "out").exists())

    def test_links_rejected(self):
        original = self.source / "ui.zh-TW.tsv"
        original.rename(self.source / "target.tsv")
        original.symlink_to("target.tsv")
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_invalid_catalogs_titles_and_key_sets(self):
        path = self.source / "ui.zh-TW.tsv"
        original = path.read_bytes()
        for data in [b"key\ttranslation\tsource\nTEST\t\tfixture\n",
                     original + b"TEST\tduplicate\tfixture\n",
                     original.replace(b"TEST", b"DIFFERENT"),
                     original.replace(b"\n", b"\r\n")]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                path.write_bytes(data)
                self.prepare()
            self.assertFalse(self.output.exists())
        path.write_bytes(original)
        labels = self.source / "manual-labels.zh-TW.tsv"
        before = labels.read_text()
        for text in [before.replace("ITEM", "ITEM %s"),
                     before.replace("prompt:item", "item:FIXTURE"),
                     before + "item:FIXTURE\tPRIVATE\tfixture\n"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                labels.write_text(text)
                self.prepare()
            self.assertFalse(self.output.exists())

    def test_local_variant_requires_complete_tables_and_marks_rights(self):
        with self.assertRaises(UnicodeError):
            self.prepare(local=True)
        self.assertFalse(self.output.exists())
        rows = ["prompt:item\tITEM\tfixture", "prompt:spell\tSPELL\tfixture"]
        rows += [f"item:FIXTURE {i}\tSYNTHETIC\tfixture" for i in range(1, 101)]
        rows += [f"spell:{i}\tSYNTHETIC\tfixture" for i in range(1, 55)]
        for language in ("zh-TW", "zh-CN", "ja", "ko"):
            (self.source / f"manual.{language}.tsv").write_text(
                "key\ttranslation\tsource\n" + "\n".join(rows) + "\n", encoding="utf-8")
        result = self.prepare(local=True)
        self.assertEqual(result["rights"], "local-only")
        self.assertEqual(result["files"]["manual.zh-TW.tsv"]["rows"], 156)
        self.assertIn("item:FIXTURE 100\tSYNTHETIC\tfixture\n",
                      (self.output / "text/manual.zh-TW.tsv").read_text())
        incomplete = self.source / "manual.zh-TW.tsv"
        incomplete.write_text(incomplete.read_text().replace("spell:54\tSYNTHETIC\tfixture\n", ""))
        missing_output = self.base / "incomplete-output"
        with self.assertRaises(ValueError):
            package.prepare(self.source, missing_output, "v.1.0.0-20261005", local=True)
        self.assertFalse(missing_output.exists())

    def test_versions(self):
        for value in ["v1.0.0-20261005", "v.1.0.0", "v.1.0.0-20260230",
                      "v.1.0.0-20261005\n"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                package.prepare(self.source, self.output, value)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
