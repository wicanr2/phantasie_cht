#!/usr/bin/env python3
"""017：產生本次原創影片 MIDI；在 Docker 內執行。"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

TPQ = 480
END = 120 * TPQ
VOID = (76 * TPQ, 80 * TPQ)
MOTIF = (62, 65, 64, 69, 67, 62)
STEMS = ("melody", "harmony", "bass", "percussion")
CHANNELS = {"melody": (0,), "harmony": (1, 3), "bass": (2,), "percussion": (9,)}
PROGRAMS = {0: 73, 1: 24, 2: 42, 3: 11}


def varlen(value):
    assert 0 <= value <= 0x0FFFFFFF
    out = [value & 127]
    value >>= 7
    while value:
        out.insert(0, (value & 127) | 128)
        value >>= 7
    return bytes(out)


def track(events):
    result = bytearray()
    previous = 0
    for tick, order, data in sorted(events):
        result.extend(varlen(tick - previous))
        result.extend(data)
        previous = tick
    result.extend(varlen(END - previous) + b"\xff\x2f\x00")
    return b"MTrk" + struct.pack(">I", len(result)) + result


def compose():
    notes = []

    def add(stem, channel, beat, duration, pitch, velocity):
        begin, end = round(beat * TPQ), round((beat + duration) * TPQ)
        assert stem in STEMS and channel in CHANNELS[stem]
        assert 0 <= begin < end <= END and 0 < velocity <= 127
        assert not (begin < VOID[1] and end > VOID[0])
        notes.append(dict(stem=stem, channel=channel, start=begin, end=end,
                          pitch=pitch, velocity=velocity))

    def phrase(bar, pitches, offsets, durations, velocity=66):
        for index, (pitch, offset, duration) in enumerate(zip(pitches, offsets, durations)):
            add("melody", 0, bar * 4 + offset, duration, pitch, velocity + index % 3)

    # 片頭：先留空間，再陳述六音動機，沒有每拍鼓點。
    add("harmony", 3, 0, 1.5, 62, 42)
    add("harmony", 3, 4, 1.5, 69, 38)
    phrase(1, MOTIF, (0, 1, 1.5, 3, 4.5, 6), (.8, .4, 1.2, 1.2, 1.2, 1.6), 58)
    # 城鎮：木質撥弦往返，長笛每兩小節才回話。
    chords = ((50, 57, 62, 65), (55, 62, 67, 70), (46, 53, 58, 62), (50, 57, 62, 65))
    for bar in range(3, 8):
        chord = chords[(bar - 3) % len(chords)]
        for i, pitch in enumerate(chord):
            add("harmony", 1, bar * 4 + i * .75, .55, pitch, 46 + i * 2)
        add("bass", 2, bar * 4, 2.8, chord[0] - 12, 43)
    phrase(3, MOTIF, (0, 1, 1.5, 3, 4.5, 6), (.75, .4, 1.0, 1.0, 1.0, 1.3))
    phrase(6, (69, 67, 65, 64, 62), (0, 1.5, 3, 4.5, 6), (1.1, 1.0, 1.0, 1.0, 1.2), 61)
    # 名冊與旅行：低音空五度，句與句之間容納畫面閱讀。
    for bar in range(8, 14):
        root = (50, 55, 46, 50, 55, 50)[bar - 8]
        add("bass", 2, bar * 4, 2.3, root - 12, 44)
        for offset, pitch in ((.25, root + 12), (2.25, root + 19)):
            add("harmony", 1, bar * 4 + offset, .7, pitch, 45)
    phrase(8, (62, 65, 64, 69, 67), (0, 1.5, 2.5, 4, 6), (1, .7, 1, 1.5, 1.2), 60)
    phrase(11, (60, 62, 65, 64), (0, 2, 4, 6), (1.4, 1.4, 1.3, 1.2), 57)
    # 危險：末音懸置，加入稀疏低鼓；留白前提早關閉所有音符。
    for bar in range(14, 19):
        root = (50, 48, 46, 45, 45)[bar - 14]
        add("bass", 2, bar * 4, 2.4, root - 12, 50)
        add("harmony", 3, bar * 4 + .25, .8, root + 19, 44)
        for offset in (0, 2.5):
            add("percussion", 9, bar * 4 + offset, .15, 48, 46)
    phrase(14, (62, 65, 64, 69, 67), (0, .75, 1.5, 3, 5), (.5, .5, 1, 1.1, 1.1), 65)
    phrase(17, (62, 65, 64, 69, 67), (0, .5, 1, 2, 3), (.35, .35, .7, .7, .6), 64)
    # 小節 19 完整留白。戰鬥是六音的節奏壓縮，不套史詩弦樂循環。
    for bar in range(20, 27):
        root = (50, 50, 55, 46, 50, 45, 50)[bar - 20]
        for offset, interval in ((0, 0), (.75, 0), (1.5, 7), (2.25, 0), (3, 0), (3.5, 7)):
            add("bass", 2, bar * 4 + offset, .35, root - 12 + interval, 72)
        for offset, interval in ((0, 12), (.5, 19), (1, 15), (1.5, 19),
                                 (2, 12), (2.5, 19), (3, 15)):
            add("harmony", 1, bar * 4 + offset + .125, .25, root + interval, 65)
        for offset, pitch, velocity in ((0, 36, 79), (.75, 48, 62), (1, 45, 57),
                                       (1.75, 48, 64), (2, 36, 76), (2.75, 45, 62),
                                       (3, 37, 53), (3.5, 48, 69)):
            add("percussion", 9, bar * 4 + offset, .1, pitch, velocity)
        if bar in (20, 22, 24):
            phrase(bar, MOTIF, (0, .5, 1, 1.75, 2.5, 3.25), (.3, .3, .4, .4, .4, .35), 82)
        elif bar in (21, 23, 25):
            phrase(bar, (69, 67, 65, 64), (.5, 1.5, 2.5, 3.25), (.35, .4, .35, .35), 76)
        elif bar == 26:
            phrase(bar, (69, 67, 64, 62), (0, 1, 2, 3), (.7, .7, .7, .7), 68)
    # 片尾留 D/A 空五度，最後一秒只讓尾音自然消散。
    phrase(27, (65, 64, 62), (0, 1.5, 3), (1, 1, 3.2), 60)
    add("bass", 2, 108, 6, 38, 45)
    add("harmony", 1, 108.25, 1.7, 62, 47)
    add("harmony", 1, 110.5, 1.7, 69, 43)
    add("harmony", 3, 115, 1.5, 62, 35)
    return sorted(notes, key=lambda n: (n["start"], n["channel"], n["pitch"]))


def midi(notes, stems):
    conductor = track([(0, 0, b"\xff\x51\x03\x09\x27\xc0"),
                       (0, 1, b"\xff\x58\x04\x04\x02\x18\x08")])
    tracks = [conductor]
    for stem in stems:
        label = stem.encode("ascii")
        events = [(0, 0, b"\xff\x03" + varlen(len(label)) + label)]
        for channel in CHANNELS[stem]:
            if channel in PROGRAMS:
                events.append((0, 1, bytes((0xC0 | channel, PROGRAMS[channel]))))
            events.extend([(0, 1, bytes((0xB0 | channel, 64, 0))),
                           (0, 1, bytes((0xB0 | channel, 91, 18))),
                           (0, 1, bytes((0xB0 | channel, 93, 0)))])
        for n in notes:
            if n["stem"] == stem:
                events.append((n["start"], 3, bytes((0x90 | n["channel"], n["pitch"], n["velocity"]))))
                events.append((n["end"], 2, bytes((0x80 | n["channel"], n["pitch"], 0))))
        tracks.append(track(events))
    return b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), TPQ) + b"".join(tracks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--output", type=Path)
    choice.add_argument("--master-plan", type=Path)
    args = parser.parse_args()
    if args.master_plan:
        root = args.master_plan
        log = (root / "loudness-pass1.txt").read_text()
        measured = json.loads(log[log.rfind("{"):])
        fields = {"input_i": "measured_I", "input_tp": "measured_TP",
                  "input_lra": "measured_LRA", "input_thresh": "measured_thresh",
                  "target_offset": "offset"}
        options = []
        for key, name in fields.items():
            value = float(measured[key])
            assert math.isfinite(value) and -100 <= value <= 100
            options.append(f"{name}={value:.2f}")
        audio_filter = "loudnorm=I=-18:TP=-1:LRA=11:" + ":".join(options)
        audio_filter += ":linear=true:print_format=json"
        for name in ("master-filter.txt", "master-plan.json", "master-checks.txt"):
            if (root / name).exists():
                raise FileExistsError(name)
        (root / "master-filter.txt").write_text(audio_filter + "\n")
        (root / "master-plan.json").write_text(json.dumps(dict(schema=1,
            source_sha256=hashlib.sha256((root / "mix.wav").read_bytes()).hexdigest(),
            measured=measured, ffmpeg_filter=audio_filter, target_lufs=-18,
            max_true_peak_dbtp=-1), indent=2) + "\n")
        hashes = [hashlib.sha256((root / name).read_bytes()).hexdigest()
                  for name in ("mix.wav", "master-filter.txt", "master-plan.json")]
        (root / "master-checks.txt").write_text(" ".join(hashes) + "\n")
        print(audio_filter)
        return
    # 同版不覆蓋；先完成所有 bytes 與契約核對再建輸出目錄。
    notes = compose()
    files = {"score.mid": midi(notes, STEMS)}
    files.update({stem + ".mid": midi(notes, (stem,)) for stem in STEMS})
    manifest = dict(schema=1, arrangement_revision=2, original_composition=True, bpm=100, bars=30, seconds=72,
                    ticks_per_quarter=TPQ, end_tick=END, void_ticks=list(VOID),
                    motif=list(MOTIF), gm_programs_zero_based=PROGRAMS,
                    composer="本專案編寫的原創 MIDI", notes=notes,
                    files=[dict(file=f, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
                           for f, data in files.items()])
    args.output.mkdir(parents=False, exist_ok=False)
    for name, data in files.items():
        (args.output / name).write_bytes(data)
    (args.output / "score.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(files=len(files), notes=len(notes), seconds=72)))


if __name__ == "__main__":
    main()
