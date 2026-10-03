#!/usr/bin/env bash
# 同狀態 A/B（docs/spec/005 §5.1）：同一路線以 -hooks none、-overlay off、-overlay on 各跑一次，
# 並以兩種 -frame-every 重跑 on，比對每個檢查點的 steps、reads、vram_hash、mem_hash（必須全同）
# 與 layer_hash（Frame 節奏不同時必須相同，否則失敗）。
#
#   tools/ab_receipt.sh <路線檔> [語言，預設 zh-TW]
#
# 收據輸出到 $PHANTASIE_OUT（預設 workplace/receipts/ab/<路線名>）。缺原版檔時 SKIP。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROUTE="${1:?用法：tools/ab_receipt.sh <路線檔> [語言]}"
LANG_="${2:-zh-TW}"
NAME="$(basename "$ROUTE" .route)"
OUT="${PHANTASIE_OUT:-$ROOT/workplace/receipts/ab/$NAME}"
rm -rf "$OUT" && mkdir -p "$OUT"
export PHANTASIE_OUT="$OUT"

run() { # 標籤 旗標...
  local tag="$1"; shift
  local d="$OUT/$tag"
  PHANTASIE_OUT="$d" "$ROOT/tools/run_receipt.sh" "$ROUTE" -lang "$LANG_" "$@" >"$OUT/$tag.log" 2>&1 || true
  ls "$d"/*.tsv >/dev/null 2>&1 || { echo "SKIP 或失敗：$tag（見 $OUT/$tag.log）"; cat "$OUT/$tag.log" | tail -3; exit 0; }
}

run none -hooks none
run off -overlay off
run on
run on-f1 -frame-every 7777

tsv() { ls "$OUT/$1"/*.tsv | head -1; }
# 欄：lang mode check image_hash img_seg hook_sig font_hash steps reads vram_hash mem_hash stamps layer_hash ...
col() { awk -F'\t' -v c="$2" 'NR>1 {print $3 "\t" $c}' "$(tsv "$1")"; }

fail=0
cmp_cols() { # 說明 欄號 A B
  if ! diff <(col "$3" "$2") <(col "$4" "$2") >/dev/null; then
    echo "FAIL：$1 在 $3 與 $4 不同"; diff <(col "$3" "$2") <(col "$4" "$2") | head -5; fail=1
  fi
}
for c in 8 9 10 11; do
  case $c in 8) n=steps;; 9) n=reads;; 10) n=vram_hash;; 11) n=mem_hash;; esac
  cmp_cols "$n" $c none off
  cmp_cols "$n" $c none on
  cmp_cols "$n" $c on on-f1
done
cmp_cols layer_hash 13 on on-f1
if [[ $fail -eq 0 ]]; then
  echo "PASS：$NAME（$(awk 'END{print NR-1}' "$(tsv on)") 個檢查點；hooks none、overlay off、overlay on 的 steps/reads/vram_hash/mem_hash 相同；兩種 frame-every 的 layer_hash 相同）"
else
  exit 1
fi
