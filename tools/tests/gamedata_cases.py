"""合成 MESS 選項字元流測試，不含原版素材。使用 Python 3.13。"""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gamedata as g

def pack(records):
    table, payload = [], bytearray()
    for i in range(1, 112):
        table.append(len(payload))
        if i in records:
            flag, text = records[i]
            assert len(text) <= 40
            payload.extend(bytes([flag]) + text.ljust(40, b' '))
    table.append(len(payload))
    return struct.pack('<112H', *table) + b'\xff' * 6 + payload

class OptionStreams(unittest.TestCase):
    def test_body_tail_and_next_message(self):
        records = {1:(56,b'A'*40),2:(3,b'B'*16+b'   LEAVE   '+b'   STAY    '),3:(40,b'C'*40)}
        rows = g.parse_mess(pack(records))
        self.assertEqual(rows[0],('msg',1,56,[b'A'*40,b'B'*16],3,[b'   LEAVE   ',b'   STAY    ']))
        self.assertEqual(rows[1],('msg',3,40,[b'C'*40],None,None))

    def test_word_across_chunk_and_continuation_flag(self):
        rows = g.parse_mess(pack({1:(40,b'A'*40),2:(5,b'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCD'),3:(6,b'EFGH')}))
        self.assertEqual(rows[0][5],[b'ABCDEFGHIJK',b'LMNOPQRSTUV',b'WXYZ0123456',b'789ABCDEFGH'])
        self.assertEqual(len(rows),1)

    def test_exact_boundary_does_not_consume_prefetch(self):
        rows = g.parse_mess(pack({1:(18,b'B'*18+b'OPTION ONE '+b'OPTION TWO '),2:(40,b'C'*40)}))
        self.assertEqual(rows[0][5],[b'OPTION ONE ',b'OPTION TWO '])
        self.assertEqual(rows[1],('msg',2,40,[b'C'*40],None,None))

    def test_short_preserves_nul_and_spaces(self):
        rows = g.parse_mess(pack({1:(10,b'A'*10+b' X\x00        '+b' Y         ')}))
        self.assertEqual(rows[0][5],[b' X\x00        ',b' Y         '])

    def test_non_multiple_body_length_one(self):
        rows=g.parse_mess(pack({1:(41,b'A'*40),2:(3,b'B'+b'FIRST      '+b'SECOND     '),3:(40,b'C'*40)}))
        self.assertEqual(rows[0][3],[b'A'*40,b'B'])
        self.assertEqual(rows[0][5],[b'FIRST      ',b'SECOND     '])
        self.assertEqual(rows[1][1],3)

    def test_width_boundaries_and_count_limits(self):
        cases=[(2,[b'ONE        ']),(7,[b'ONE        ',b'TWO        ',b'THREE      ',b'FOUR       ',b'FIVE       ',b'SIX        ']),
               (8,[b'001',b'002',b'003',b'004',b'005',b'006',b'007']),
               (20,[b'001',b'002',b'003',b'004',b'005',b'006',b'007',b'008',b'009',b'010',b'011',b'012',b'013',b'014',b'015',b'016',b'017',b'018',b'019'])]
        for n,expected in cases:
            with self.subTest(n=n):
                raw=b''.join(expected)
                records={1:(40,b'A'*40),2:(n,raw[:40])}
                if len(raw)>40:records[3]=(1,raw[40:])
                rows=g.parse_mess(pack(records))
                self.assertEqual(rows[0][4:],(n,expected))
                self.assertEqual(len(rows),1)

    def test_invalid_count_not_used_for_first_message(self):
        for n in (0,1,21,32):
            records={1:(40,b'A'*40),2:(n,b' '*40),3:(0,b' '*40)}
            rows=g.parse_mess(pack(records))
            self.assertEqual(rows[0][4:],(None,None))

    def test_missing_continuation_rejected(self):
        with self.assertRaises(ValueError):
            g.parse_mess(pack({1:(40,b'A'*40),2:(5,b'B'*40)}))

    def test_missing_first_option_record_rejected(self):
        with self.assertRaises(ValueError):
            g.parse_mess(pack({1:(39,b'A'*39)}))

    def test_trailer_cannot_supply_option_bytes(self):
        with self.assertRaises(ValueError):
            g.parse_mess(pack({109:(40,b'A'*40),110:(5,b'B'*40),111:(5,b'C'*40)}))

if __name__=='__main__':
    unittest.main()
