"""手冊 builder 的合成反例，沒有原版答案。Docker 內執行。"""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import build_manual_catalog as manual


class ManualCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.rows = [(f"item:TEST {i}", str(i), "fixture") for i in range(1, 101)]
        self.rows += [(f"spell:{i}", "TEST MAGIC", "fixture") for i in range(1, 55)]

    def write(self, rows):
        f = self.root / "reference.tsv"
        f.write_text("key\ttranslation\tsource\n" + "".join("\t".join(row)+"\n" for row in rows))
        return f

    def test_complete_and_localized(self):
        rows = manual.reference(self.write(self.rows))
        (self.root / "manual-labels.test.tsv").write_text("key\ttranslation\tsource\nprompt:item\tITEM\tfixture\nprompt:spell\tSPELL\tfixture\nanswer\tAnswer: %s\tfixture\n")
        (self.root / "ui.test.tsv").write_text("key\ttranslation\tsource\nTEST MAGIC\tMAGIC TEST\tfixture\n")
        result = manual.build(rows, self.root, "test")
        self.assertEqual(len(result.splitlines()), 157)
        self.assertIn("spell:17\tAnswer: MAGIC TEST\tfixture", result)

    def test_missing_duplicate_and_source(self):
        for rows in [self.rows[:-1], self.rows+[self.rows[0]], [("item:TEST 1", "2", "fixture")]+self.rows[1:], [("item:TEST 1", "1", "")]+self.rows[1:]]:
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                manual.reference(self.write(rows))

    def test_range(self):
        for row in [("spell:55", "TEST", "fixture"), ("item:TEST", "0", "fixture")]:
            with self.subTest(key=row[0]), self.assertRaises(ValueError):
                manual.reference(self.write(self.rows+[row]))

    def test_missing_translation_and_title_placeholder(self):
        rows = manual.reference(self.write(self.rows))
        for title, translation in [("ITEM %s", "MAGIC"), ("ITEM", ""), ("ITEM", "<blank>")]:
            (self.root / "manual-labels.test.tsv").write_text(f"key\ttranslation\tsource\nprompt:item\t{title}\tfixture\nprompt:spell\tSPELL\tfixture\nanswer\tAnswer: %s\tfixture\n")
            (self.root / "ui.test.tsv").write_text(f"key\ttranslation\tsource\nTEST MAGIC\t{translation}\tfixture\n")
            with self.subTest(title=title, translation=translation), self.assertRaises(ValueError):
                manual.build(rows, self.root, "test")

    def test_width_and_controls(self):
        for value in ["字"*20, "A\nB"]:
            with self.assertRaises(ValueError):
                manual.bounded(value, 10)


if __name__ == "__main__":
    unittest.main()
