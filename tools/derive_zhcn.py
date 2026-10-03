#!/usr/bin/env python3
"""由 zh-TW catalog 以 OpenCC（tw2sp）加專案覆寫表產生 zh-CN catalog。只在 Docker 內執行。

  docker run --rm --network none -u "$(id -u):$(id -g)" \
    -v "$PWD/text:/text" -v "$PWD/tools:/t:ro" buck-zhcn-opencc:1.4.2 \
    python3 -B /t/derive_zhcn.py /text

讀 /text/{ui,prose}.zh-TW.tsv，寫 /text/{ui,prose}.zh-CN.tsv。鍵與 source 欄原樣保留；translation 欄逐筆轉換，
格式規格（%s、%d…）與 \\c、<blank> 標記不受影響。兩層覆寫（docs/spec/004 §6）：
  1. /text/phrases.zh-CN.tsv（欄：from、to、note）：OpenCC 轉換後的全域詞組取代（簡體側字串），
     用於 OpenCC 轉出來不合地區或遊戲用語的詞（例：傳送被轉成發送）；依檔案順序逐條套用。
  2. /text/overrides.zh-CN.tsv（欄：key、translation）：逐鍵覆寫整句譯文，取代前面的結果。
映像與版本記錄在 font/README.md 與收據（OpenCC 1.4.2、設定 tw2sp）。
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


def load_phrases(path):
    out = []
    if not os.path.exists(path):
        return out
    for i, line in enumerate(open(path, encoding="utf-8")):
        if i == 0 or not line.strip() or line.startswith("#"):
            continue
        c = line.rstrip("\n").split("\t")
        if len(c) < 2:
            sys.exit(f"{path}:{i + 1}: 欄數不足")
        out.append((c[0], c[1]))
    return out


def main():
    d = sys.argv[1]
    conv = opencc.OpenCC("tw2sp")
    ov = load_overrides(f"{d}/overrides.zh-CN.tsv")
    phrases = load_phrases(f"{d}/phrases.zh-CN.tsv")
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
                if body.startswith(cl.CENTER):
                    flag, body = cl.CENTER, body[1:]
                body = conv.convert(body)
                for a, b in phrases:
                    body = body.replace(a, b)
                out = flag + body
            rows.append((key, out, source))
        cl.write_tsv(f"{d}/{fam}.zh-CN.tsv", rows)
        print(fam, len(rows), "筆")


if __name__ == "__main__":
    main()
