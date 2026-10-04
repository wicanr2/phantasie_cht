#!/usr/bin/env python3
"""009 的明示短訊息匯出檢查。合成輸入不含原版文字；在 Docker 內執行。"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "prose_export.py"


class ExportCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src, self.out = self.root / "src", self.root / "out"
        self.src.mkdir()
        self.out.mkdir()
        (self.out / "batches").mkdir()
        (self.out / "prose-units.jsonl").write_text("sentinel\n")
        (self.out / "batches/batch-000.jsonl").write_text("batch sentinel\n")
        for n in range(1, 11):
            (self.src / f"MESS{n}.msgs.tsv").write_text("")
        (self.src / "MESS1.msgs.tsv").write_text(
            "msg\t1\t40\tlong synthetic line\t\n"
            "short\t2\t5\t abc \t3:  X|  Y\n"
            "short\t3\t5\t     \t3:  X|  Y\n"
            "short\t4\t5\t\\x01abc\t3:  X|  Y\n"
            "short\t5\t5\t\x01abc \t3:  X|  Y\n"
            "short\t6\t5\t def \t3:  X|  Y\n"
        )
        (self.src / "SCROLLS.tsv").write_text("")

    def run_export(self, *flags):
        return subprocess.run([sys.executable, "-B", str(TOOL), str(self.src),
                               str(self.out), "2", *flags], capture_output=True)

    def units(self):
        return [json.loads(line) for line in
                (self.out / "prose-units.jsonl").read_text().splitlines()]

    def snapshot(self):
        return {str(f.relative_to(self.out)): f.read_bytes()
                for f in self.out.rglob("*") if f.is_file()}

    def test_default_retains_skip(self):
        self.assertEqual(self.run_export().returncode, 0)
        self.assertEqual([u["id"] for u in self.units()], ["mess1:1"])

    def test_selected_body_and_normalized_options(self):
        self.assertEqual(self.run_export("--include-short", "mess1:2").returncode, 0)
        u = self.units()[1]
        self.assertEqual((u["id"], u["kind"], u["len"], u["lines"], u["lead"], u["trail"]),
                         ("mess1:2", "short", 5, [" abc"], [1], [1]))
        self.assertEqual(u["opt_cells"], ["  X", "  Y"])

    def test_duplicate_and_flag_order_keep_source_order(self):
        self.assertEqual(self.run_export("--include-short", "mess1:6",
                                        "--include-short", "mess1:2",
                                        "--include-short", "mess1:2").returncode, 0)
        self.assertEqual([u["id"] for u in self.units()],
                         ["mess1:1", "mess1:2", "mess1:6"])

    def test_invalid_requests_leave_all_output_unchanged(self):
        for bad in ("mess1:99", "mess1:1", "mess1:3", "mess1:4", "mess1:5"):
            with self.subTest(bad=bad):
                before = self.snapshot()
                r = self.run_export("--include-short", "mess1:2", "--include-short", bad)
                self.assertNotEqual(r.returncode, 0)
                self.assertEqual(self.snapshot(), before)

    def test_invalid_request_does_not_create_output(self):
        out = self.root / "not-created"
        r = subprocess.run([sys.executable, "-B", str(TOOL), str(self.src),
                            str(out), "--include-short", "mess1:99"], capture_output=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
