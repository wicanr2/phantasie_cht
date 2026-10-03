#!/usr/bin/env python3
"""由 zh-TW catalog 以 OpenCC（tw2sp）加專案覆寫表產生 zh-CN catalog。只在 Docker 內執行。

  docker run --rm --network none -u "$(id -u):$(id -g)" \
    -v "$PWD/text:/text" -v "$PWD/tools:/t:ro" buck-zhcn-opencc:1.4.2 \
    python3 -B /t/derive_zhcn.py /text

讀 /text/{ui,prose}.zh-TW.tsv，寫 /text/{ui,prose}.zh-CN.tsv。鍵與 source 欄原樣保留；translation 欄逐筆轉換，
格式規格（%s、%d…）與 \\c、<blank> 標記不受影響。覆寫表 /text/overrides.zh-CN.tsv（欄：key、translation）的
譯文取代轉換結果（用於 OpenCC 轉出來不合地區用語的條目）。映像與版本記錄在輸出的第一行註解之外，
由 font/README.md 與收據記載（OpenCC 1.4.2、設定 tw2sp）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalog_lib as cl  # noqa: E402
import opencc  # noqa: E402


def load_overrides(path):
    out = {}
    if not os.path.exists(path):
        return out
    for _, key, tr, _ in cl.read_tsv(path):
        out[key] = tr
    return out


def main():
    d = sys.argv[1]
    conv = opencc.OpenCC("tw2sp")
    ov = load_overrides(f"{d}/overrides.zh-CN.tsv")
    for fam in ("ui", "prose"):
        src = f"{d}/{fam}.zh-TW.tsv"
        if not os.path.exists(src):
            continue
        rows = []
        for _, key, tr, source in cl.read_tsv(src):
            if key in ov:
                out = ov[key]
            elif tr in ("", "<blank>"):
                out = tr
            else:
                flag = ""
                body = tr
                if body.startswith("\\c"):
                    flag, body = "\\c", body[2:]
                out = flag + conv.convert(body)
            rows.append((key, out, source))
        cl.write_tsv(f"{d}/{fam}.zh-CN.tsv", rows)
        print(fam, len(rows), "筆")


if __name__ == "__main__":
    main()
