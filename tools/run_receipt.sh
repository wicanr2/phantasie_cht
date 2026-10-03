#!/usr/bin/env bash
# 以 Docker 執行無頭收據工具（docs/spec/005 §5）。
#
#   tools/run_receipt.sh <路線檔> [phantasie-receipt 的旗標...]
#
# 預設值（可用環境變數覆寫）：
#   PHANTASIE_ORIG   原版目錄（含 phantasi/），唯讀掛載      預設 workplace/orig
#   PHANTASIE_FONTS  字型目錄（tools/build_fonts.sh 的輸出） 預設 workplace/fonts
#   PHANTASIE_DG     dosgolem 工作樹                        預設 workplace/dosgolem-fw
#   PHANTASIE_OUT    收據與 PNG 的輸出目錄                   預設 workplace/receipts
# 路線檔、text/、字型複製進暫存的 workplace/run/<pid>/（gitignore）後以 /run-data 掛入容器。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROUTE="$(realpath "${1:?用法：tools/run_receipt.sh <路線檔> [旗標...]}")"
shift
ORIG="${PHANTASIE_ORIG:-$ROOT/workplace/orig}"
FONTS="${PHANTASIE_FONTS:-$ROOT/workplace/fonts}"
DG="${PHANTASIE_DG:-$ROOT/workplace/dosgolem-fw}"
OUT="${PHANTASIE_OUT:-$ROOT/workplace/receipts}"
RUN="$ROOT/workplace/run/$$"   # 每次呼叫一個暫存目錄，可並行執行

test -d "$ORIG/phantasi" || { echo "SKIP：找不到原版目錄 $ORIG/phantasi，不算驗收" >&2; exit 0; }
test -d "$FONTS" || { echo "找不到字型目錄 $FONTS（先跑 tools/build_fonts.sh）" >&2; exit 1; }
test -f "$ROUTE" || { echo "找不到路線檔 $ROUTE" >&2; exit 1; }
mkdir -p "$RUN" "$OUT"
trap 'rm -rf "$RUN"' EXIT
cp -r "$ROOT/text" "$RUN/text"
cp -r "$FONTS" "$RUN/fonts"
RNAME="$(basename "$ROUTE")"
cp "$ROUTE" "$RUN/$RNAME"
# 輸出目錄在容器內是 /run-data/out；結束後同步到 $OUT。
mkdir -p "$RUN/out"

(
  cd "$DG"
  DOSGOLEM_ORIG="$ORIG" DOSGOLEM_EXTRA_MOUNT="$RUN:/run-data" \
    tools/go.sh run ./apps/phantasie/cmd/phantasie-receipt \
      -root /orig/phantasi -route "/run-data/$RNAME" -text /run-data/text -font /run-data/fonts \
      -out /run-data/out "$@"
) && status=0 || status=$?
cp -r "$RUN/out/." "$OUT/"
exit $status
