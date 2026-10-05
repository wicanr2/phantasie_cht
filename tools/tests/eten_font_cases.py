"""014：自製字模與公開碼點的來源／隔離反例，不讀原版或第三方字型。"""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_eten_font as eten
import package_files as pf


class EtenFontCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="phantasie-eten-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "eten"; self.source.mkdir()
        # 全部圖案自製；中=A4A4，常用區零起算第66槽。
        standard = bytearray(392820)
        standard[66 * 30:67 * 30] = bytes(range(1, 31))
        special = bytearray(12240)
        special[129 * 30:130 * 30] = b"\x55\xaa" * 15  # A1E3（全形波浪號）。
        for name, data in (("STDFONT.15", standard), ("SPCFONT.15", special)):
            (self.source / name).write_bytes(data)
        self.fingerprints = {p.name: (p.stat().st_size, pf.digest(p.read_bytes())) for p in self.source.iterdir()}
        self.base = self.root / "base.golemfnt"
        records = [(cp, 1, bytes([cp]) * 32) for cp in range(32, 127)]
        records += [(0x3000, 0x81, bytes(32)), (0x4E2D, 0x81, bytes(32)), (0xFF5E, 0x81, bytes(32))]
        self.original = b"GOLEMFNT" + struct.pack("<HHI", 16, 16, len(records))
        self.original += b"".join(struct.pack("<IB", cp, flag) + bitmap for cp, flag, bitmap in records)
        self.base.write_bytes(self.original)
        self.output = self.root / "out.golemfnt"

    def build(self):
        with patch.object(eten, "SOURCES", self.fingerprints):
            return eten.build(self.source, self.base, self.output)

    def test_boundary_indices_and_rejected_gaps(self):
        for code, expected in ((0xA140, ("SPCFONT.15", 0)), (0xA3BF, ("SPCFONT.15", 407)),
                               (0xA440, ("STDFONT.15", 0)), (0xC67E, ("STDFONT.15", 5400)),
                               (0xC940, ("STDFONT.15", 5401)), (0xF9D5, ("STDFONT.15", 13052))):
            self.assertEqual(eten.location(code), expected)
        for code in (0xA13F, 0xA17F, 0xA1A0, 0xA1FF, 0xA3C0, 0xA3FE, 0xC6A1, 0xC8FE, 0xF9D6, 0xFA40):
            with self.subTest(code=hex(code)), self.assertRaises(ValueError): eten.location(code)

    def test_literal_bitmap_ascii_blank_and_provenance(self):
        result = self.build()
        data = self.output.read_bytes()
        self.assertEqual(data[:16 + 95 * 37], self.original[:16 + 95 * 37])
        expected = (struct.pack("<IB", 0x3000, 0x82) + bytes(32) +
                    struct.pack("<IB", 0x4E2D, 0x82) + bytes(range(1, 31)) + bytes(2) +
                    struct.pack("<IB", 0xFF5E, 0x82) + b"\x55\xaa" * 15 + bytes(2))
        self.assertEqual(data[16 + 95 * 37:], expected)
        self.assertEqual((result["glyphs"], result["gnu_ascii"], result["eten_fullwidth"]), (98, 95, 3))
        self.assertEqual(result["sha256"], pf.digest(data))
        self.assertEqual(result["base_font_sha256"], pf.digest(self.original))
        self.assertEqual(self.base.read_bytes(), self.original)

    def test_wrong_source_hash_size_and_no_partial_output(self):
        for change in (b"CORRUPT", bytes(392820)):
            path = self.source / "STDFONT.15"; before = path.read_bytes(); path.write_bytes(change)
            with self.assertRaisesRegex(ValueError, "固定來源"): self.build()
            self.assertFalse(self.output.exists()); path.write_bytes(before)
        # 真正正式常數不能接受自製資料，沒有把 patch profile 當成來源驗證。
        with self.assertRaisesRegex(ValueError, "固定來源"): eten.build(self.source, self.base, self.output)
        self.assertFalse(self.output.exists())

    def test_unsupported_unicode_invalid_base_and_existing_output(self):
        self.base.write_bytes(self.original[:-37] + struct.pack("<IB", 0x1F600, 0x81) + bytes(32))
        with self.assertRaisesRegex(ValueError, "無倚天"): self.build()
        self.assertFalse(self.output.exists())
        for data in (self.original[:-1], self.original[:16] + self.original[16:53] + self.original[16:-37],
                     self.original[:16 + 95 * 37 + 4] + b"\x01" + self.original[16 + 95 * 37 + 5:]):
            self.base.write_bytes(data)
            with self.assertRaises(ValueError): self.build()
            self.assertFalse(self.output.exists())
        self.base.write_bytes(self.original); self.output.write_bytes(b"EXISTING")
        with self.assertRaisesRegex(ValueError, "新檔"): self.build()
        self.assertEqual(self.output.read_bytes(), b"EXISTING")

    def test_public_gate_rejects_eten_and_halfwidth_flags(self):
        data = b"GOLEMFNT" + struct.pack("<HHI", 16, 16, 1) + struct.pack("<IB", 0x4E2D, 0x82) + bytes(32)
        self.assertEqual(pf.font_coverage(data, {0x4E2D}, local_eten=True), 1)
        with self.assertRaisesRegex(ValueError, "來源旗標"): pf.font_coverage(data, {0x4E2D})
        for cp, flag in ((0x4E2D, 2), (0x4E2D, 0x83), (0x41, 0x82)):
            bad = data[:16] + struct.pack("<IB", cp, flag) + bytes(32)
            with self.subTest(cp=cp, flag=flag), self.assertRaisesRegex(ValueError, "來源旗標"):
                pf.font_coverage(bad, {cp}, local_eten=True)


if __name__ == "__main__": unittest.main()
