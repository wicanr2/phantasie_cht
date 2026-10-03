#!/usr/bin/env bash
# 建置 zh-TW、zh-CN、ja、ko 的 GOLEMFNT 字型子集（Docker 內執行 tools/build_font.py）。
#
#   tools/build_fonts.sh <unifont-17.0.05.tar.gz> <輸出目錄>
#
# 輸出 <輸出目錄>/<lang>.golemfnt。字元來源是該語言的 text/ui.<lang>.tsv、text/prose.<lang>.tsv，
# 加上存在時的 font/<lang>.extra.txt。缺任何一個要求的字就以非零離開（docs/spec/004 §3）。
# 字型檔不進版控（docs/spec/004 §3、AGENTS.md §7）。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAR="$(realpath "${1:?用法：tools/build_fonts.sh <unifont tar.gz> <輸出目錄>}")"
OUT="$(realpath -m "${2:?缺輸出目錄}")"
test -f "$TAR" || { echo "找不到 $TAR" >&2; exit 1; }
mkdir -p "$OUT"
test -d "$OUT" || { echo "輸出目錄建立失敗：$OUT" >&2; exit 1; }

VER=17.0.05
# 語言:hex 成員（docs/spec/004 §3）
SPECS=(
  "zh-TW:unifont_t-$VER"
  "zh-CN:unifont-$VER"
  "ja:unifont_jp-$VER"
  "ko:unifont-$VER"
)

for spec in "${SPECS[@]}"; do
  lang="${spec%%:*}"
  hex="${spec##*:}"
  chars=(--chars "text/ui.$lang.tsv" --chars "text/prose.$lang.tsv")
  [[ -f "$ROOT/font/$lang.extra.txt" ]] && chars+=(--chars "font/$lang.extra.txt")
  docker run --rm -u "$(id -u):$(id -g)" --network none --memory 1g --cpus 1 --pids-limit 64 \
    --log-opt max-size=10m --log-opt max-file=3 \
    -v "$ROOT:/w:ro" -v "$TAR:/unifont.tar.gz:ro" -v "$OUT:/out" \
    python:3.13-bookworm sh -c "cd /w && python -B tools/build_font.py --tar /unifont.tar.gz \
      --member unifont-$VER/font/precompiled/$hex.hex ${chars[*]} --out /out/$lang.golemfnt"
done
sha256sum "$OUT"/*.golemfnt
