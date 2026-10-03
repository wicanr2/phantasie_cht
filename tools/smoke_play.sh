#!/usr/bin/env bash
# 前端實機冒煙（docs/spec/005 §3）：在 Docker 內的虛擬顯示器（Xvfb）啟動 phantasie-play，
# 每個語言各截一張啟動後的畫面，輸出到 workplace/play-shots/<語言>.png。
#
#   tools/smoke_play.sh [語言...]        預設 zh-TW zh-CN en ja ko
#
# 先跑 tools/build_play.sh 與 tools/build_fonts.sh。原版目錄唯讀掛載；存檔狀態目錄是 workplace/play-state。
# 截圖需要用眼睛看：同狀態收據抓不到缺字、機器誤譯這類一眼可見的錯。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ORIG="${PHANTASIE_ORIG:-$ROOT/workplace/orig}"
FONTS="${PHANTASIE_FONTS:-$ROOT/workplace/fonts}"
IMAGE="${PHANTASIE_IMAGE:-psychicwar-go-ebiten:latest}"
WAIT="${PHANTASIE_SMOKE_WAIT:-20}"
for p in "$ORIG/phantasi" "$FONTS" "$ROOT/text" "$ROOT/workplace/bin/phantasie-play"; do test -e "$p" || { echo "找不到 $p" >&2; exit 1; }; done
mkdir -p "$ROOT/workplace/play-state" "$ROOT/workplace/play-shots"
langs=("$@"); [[ ${#langs[@]} -gt 0 ]] || langs=(zh-TW zh-CN en ja ko)
for lang in "${langs[@]}"; do
  timeout 120 docker run --rm --name "phantasie-smoke-$$-$lang" --network none -u "$(id -u):$(id -g)" \
    --memory 2g --cpus 2 --pids-limit 256 --log-opt max-size=10m --log-opt max-file=3 -e HOME=/tmp \
    -v "$ROOT/workplace/bin:/bin-play:ro" -v "$ORIG/phantasi:/orig:ro" -v "$ROOT/text:/text:ro" -v "$FONTS:/fonts:ro" \
    -v "$ROOT/workplace/play-state:/state" -v "$ROOT/workplace/play-shots:/shots" \
    --entrypoint sh "$IMAGE" -c "
      Xvfb :77 -screen 0 1280x800x24 -nolisten tcp >/shots/xvfb.log 2>&1 & sleep 3
      export DISPLAY=:77
      /bin-play/phantasie-play -root /orig -state /state -text /text -font /fonts -zoom 2 -lang $lang >/shots/play-$lang.log 2>&1 &
      sleep $WAIT; import -window root /shots/$lang.png; kill %2 2>/dev/null; true"
  test -s "$ROOT/workplace/play-shots/$lang.png" && echo "截圖：workplace/play-shots/$lang.png" || { echo "沒有截圖：$lang" >&2; exit 1; }
done
