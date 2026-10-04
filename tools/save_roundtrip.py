#!/usr/bin/env python3
"""在 Docker 內執行四語存讀檔 A/B；存檔和完整收據只寫本機輸出目錄。"""
import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path


def digest(files):
    payload = "".join(f'{f["name"]}\t{f["size"]}\t{f["sha256"]}\n' for f in files)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def disk_files(directory):
    files = []
    for path in sorted(directory.iterdir(), key=lambda p: p.name.encode("utf-8")):
        assert path.is_file() and not path.is_symlink(), path
        data = path.read_bytes()
        files.append(dict(name=path.name, size=len(data), sha256=hashlib.sha256(data).hexdigest()))
    return files


def verify(args):
    if not args.root.is_dir():
        print("SKIP：缺少原版目錄，不算驗收")
        return
    if args.out.exists() and any(args.out.iterdir()):
        raise ValueError("輸出目錄非空，請使用新的驗收目錄")
    args.out.mkdir(parents=True, exist_ok=True)
    profiles = {"none": ["-hooks", "none"], "off": ["-overlay", "off"],
                "on": [], "on-f2": ["-frame-every", "40000"]}
    baseline = {}
    summary = []
    for lang in ("zh-TW", "zh-CN", "ja", "ko"):
        on_rows = {}
        for mode, flags in profiles.items():
            base = args.out / lang / mode
            state = base / "state"
            phases = {}
            for phase, count in (("write", 11), ("read", 4)):
                route = "save-roundtrip-" + phase
                dest = base / phase
                dest.mkdir(parents=True)
                command = [str(args.receipt), "-root", str(args.root), "-route", str(args.routes / (route + ".route")),
                           "-text", str(args.text), "-font", str(args.font), "-lang", lang,
                           "-state", str(state), "-out", str(dest), *flags]
                with (base / (phase + ".log")).open("w") as log:
                    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=240)
                assert result.returncode == 0, (lang, mode, phase, "詳見執行紀錄")
                tsv = list(dest.glob("*.tsv"))
                manifests = list(dest.glob("*.state.json"))
                assert len(tsv) == len(manifests) == 1, (lang, mode, phase)
                with tsv[0].open() as file:
                    rows = list(csv.DictReader(file, delimiter="\t"))
                assert len(rows) == count, (lang, mode, phase, len(rows))
                manifest = json.loads(manifests[0].read_text())
                assert len(manifest["checks"]) == count
                assert manifest["initial"]["hash"] == digest(manifest["initial"]["files"])
                for row, point in zip(rows, manifest["checks"]):
                    assert row["check"] == point["check"]
                    assert row["state_hash"] == point["hash"] == digest(point["files"])
                    assert row["state_in_hash"] == manifest["initial"]["hash"]
                    if mode == "none":
                        assert row["verdict"].startswith("SKIP（-hooks none")
                    else:
                        assert row["verdict"] == "PASS", (lang, mode, phase, row["check"], row["verdict"])
                    key = phase, row["check"]
                    machine = tuple(row[k] for k in ("steps", "reads", "vram_hash", "mem_hash", "full_mem_hash", "state_in_hash", "state_hash"))
                    if key not in baseline:
                        baseline[key] = machine
                    assert machine == baseline[key], (lang, mode, phase, row["check"], "同狀態不符")
                    if mode == "on":
                        on_rows[key] = row
                    if mode == "on-f2":
                        assert row["layer_hash"] == on_rows[key]["layer_hash"], (lang, phase, row["check"], "節奏敏感")
                actual = disk_files(state / lang)
                assert actual == manifest["checks"][-1]["files"], (lang, mode, phase, "落地檔案與清冊不符")
                phases[phase] = rows, manifest, dest
            written, wm, wd = phases["write"]
            loaded, rm, rd = phases["read"]
            assert wm["initial"]["files"] == []
            assert wm["checks"][-1]["files"] != [], (lang, mode, "沒有落地存檔")
            assert wm["checks"][-1]["files"] == rm["initial"]["files"]
            saved = next(row for row in written if row["check"] == "saved-inspect-stats")
            restored = next(row for row in loaded if row["check"] == "reloaded-inspect-stats")
            assert saved["vram_hash"] == restored["vram_hash"]
            if mode != "none":
                assert saved["content_hash"] == restored["content_hash"], (lang, mode, "角色覆繪內容不符")
                assert (wd / saved["png"]).read_bytes() == (rd / restored["png"]).read_bytes(), (lang, mode, "角色畫面不符")
            summary.append(dict(lang=lang, mode=mode, checkpoints=15, verdict="PASS"))
            print(f"PASS：{lang} {mode}，15 個檢查點、存檔及角色讀回", flush=True)
    (args.out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("receipt", "root", "routes", "text", "font", "out"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    verify(args)


if __name__ == "__main__":
    main()
