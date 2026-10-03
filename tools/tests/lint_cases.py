#!/usr/bin/env python3
"""lint_catalog.py 的反例測試（docs/spec/003 §13 第 6 項）。只在 Docker 內執行。

  docker run --rm --network none -u "$(id -u):$(id -g)" -v "$PWD:/p:ro" \
    [-v <unifont.tar.gz 所在目錄>:/f:ro] python:3.13-bookworm python -B /p/tools/tests/lint_cases.py [/f/unifont.tar.gz]

每個反例建在暫存目錄內的最小 TSV，必須被擋下（非零離開且輸出含預期訊息）；另有一個正對照必須通過。
有給字型壓縮檔時才跑需要字型寬度表的反例（U+2026 全形寬度），否則該項 SKIP 並說明不算驗收。
"""
import hashlib
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LINT = os.path.join(HERE, "..", "lint_catalog.py")
FONT_MEMBER = "unifont-17.0.05/font/precompiled/unifont_t-17.0.05.hex"
HEAD = "key\ttranslation\tsource\n"

fails = ran = skipped = 0


def run(name, files, expect_fail, expect_text, extra=None):
    global fails, ran
    ran += 1
    with tempfile.TemporaryDirectory() as d:
        paths = []
        for fname, content in files.items():
            p = os.path.join(d, fname)
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(content)
            if fname.startswith(("ui.", "prose.")):
                paths.append(p)
        cmd = [sys.executable, "-B", LINT] + [a.replace("{d}", d) for a in (extra or [])] + paths
        r = subprocess.run(cmd, capture_output=True, text=True)
        out = r.stdout + r.stderr
    ok = (r.returncode != 0) == expect_fail and all(t in out for t in expect_text)
    if not ok:
        fails += 1
        print(f"失敗 {name}: 離開碼 {r.returncode}，輸出：\n{out}")


def main():
    font = sys.argv[1] if len(sys.argv) > 1 else None
    fx = ["--font-tar", font, "--font-member", FONT_MEMBER] if font else []
    # 正對照
    run("正對照", {"ui.t.tsv": HEAD + "EXIT\t離開\tres:0000\nHP:%-4.3d\t生命:%-4.3d\tres:0001\n"}, False, ["錯誤 0"], fx)
    # 結構
    run("鍵尾端空白", {"ui.t.tsv": HEAD + "EXIT \t離開\tx\n"}, True, ["鍵有尾端空白"], fx)
    run("譯文尾端空白", {"ui.t.tsv": HEAD + "EXIT\t離開 \tx\n"}, True, ["譯文有尾端空白"], fx)
    run("規範化後重複", {"ui.t.tsv": HEAD + "DUP\t甲\tx\nDUP \t乙\tx\n"}, True, ["鍵重複"], fx)
    run("壞跳脫與另一列超寬（兩個都要報）",
        {"ui.t.tsv": HEAD + "A\\xZZ\tx\tx\nOK\t非常非常非常長\tx\n"}, True, ["不認得的跳脫", "寬度超出"], fx)
    run("欄數錯誤", {"ui.t.tsv": HEAD + "A\tB\n"}, True, ["欄數是 2"], fx)
    # 保護清單、衝突
    run("保護清單的鍵進 catalog",
        {"ui.t.tsv": HEAD + "What is the name\t名字\tx\n", "protected.tsv": "key\tnote\nWhat is the name\tx\n"},
        True, ["保護清單"], fx + ["--protected", "{d}/protected.tsv"])
    h = "h:" + hashlib.sha256(b"HELLO THERE").hexdigest()[:12]
    run("ui 與 prose 同文不同譯",
        {"ui.t.tsv": HEAD + "HELLO THERE\t你好\tx\n", "prose.t.tsv": HEAD + h + "\t哈囉\tx\n"}, True, ["譯文不同"], fx)
    # 孤兒與缺譯
    run("--sources 孤兒與缺譯",
        {"ui.t.tsv": HEAD + "ORPHAN\t孤兒\tx\n", "cand.tsv": "key\tkind\tregions\tdyn_seen\tnote\nMISSING\ttext\tres\tN\t\n"},
        False, ["孤兒鍵", "缺譯"], fx + ["--sources", "{d}/cand.tsv"])
    run("--harvest 動態缺譯",
        {"ui.t.tsv": HEAD + "EXIT\t離開\tx\n", "texts.tsv": "count\tcls\tin_static\ttext\n3\tfmtonly\tY\t'Inspect'\n"},
        True, ["動態缺譯"], fx + ["--harvest", "{d}/texts.tsv"])
    # 格式規格
    run("%x", {"ui.t.tsv": HEAD + "VAL %x\t值 %x\tx\n"}, True, ["不支援的轉換規格"], fx)
    run("%2$s", {"ui.t.tsv": HEAD + "A %s\tB %2$s\tx\n"}, True, ["不支援的轉換規格"], fx)
    run("%05d", {"ui.t.tsv": HEAD + "N %d\tN %05d\tx\n"}, True, ["不支援的轉換規格"], fx)
    run("轉換序不一致", {"ui.t.tsv": HEAD + "%s HITS %d\t%d 命中 %s\tx\n"}, True, ["轉換序"], fx)
    run("精度改動", {"ui.t.tsv": HEAD + "%-5s\t%-5.1s\tx\n"}, True, ["精度"], fx)
    # 置中與留白
    run("<blank> 在模板內", {"ui.t.tsv": HEAD + "A %s\t<blank> %s\tx\n"}, True, ["<blank>"], fx)
    run("\\c 不在開頭", {"ui.t.tsv": HEAD + "A\t甲\\c乙\tx\n"}, True, ["不認得的跳脫"], fx)
    run("控制字元", {"ui.t.tsv": HEAD + "A\t甲\x01乙\tx\n"}, True, ["控制字元"], fx)
    run("BOM", {"ui.t.tsv": "﻿" + HEAD + "A\t甲\tx\n"}, True, ["BOM"], fx)
    # 需要字型寬度表
    global skipped
    if font:
        run("U+2026 三個對鍵 OK（真實寬度 6h）", {"ui.t.tsv": HEAD + "OK\t…………\tx\n"[:0] + "OK\t………\tx\n"}, True,
            ["寬度超出"], fx)
        run("缺字（U+E001）", {"ui.t.tsv": HEAD + "A\t\tx\n"}, True, ["字型缺字"], fx)
    else:
        skipped += 2
        print("SKIP: 沒有給字型壓縮檔，U+2026 寬度與缺字兩項反例未執行，不算驗收")
    print(f"{ran} 項，失敗 {fails}，略過 {skipped}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
