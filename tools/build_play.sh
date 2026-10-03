#!/usr/bin/env bash
# 在 Docker 內建置互動前端 phantasie-play（Ebitengine），輸出到 workplace/bin/phantasie-play。
#
#   tools/build_play.sh
#
# 環境變數：
#   PHANTASIE_DG     dosgolem 工作樹            預設 workplace/dosgolem-fw
#   PHANTASIE_IMAGE  建置映像（要有 Go 1.24 以上與 X11、OpenGL 開發檔） 預設 psychicwar-go-ebiten:latest
# 模組快取使用 dosgolem 工作樹的 workplace/gocache、gomodcache；容器 --network none。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DG="${PHANTASIE_DG:-$ROOT/workplace/dosgolem-fw}"
IMAGE="${PHANTASIE_IMAGE:-psychicwar-go-ebiten:latest}"
for d in "$DG" "$DG/workplace/gocache" "$DG/workplace/gomodcache"; do test -d "$d" || { echo "找不到 $d" >&2; exit 1; }; done
mkdir -p "$ROOT/workplace/bin"
timeout 1200 docker run --rm --network none -u "$(id -u):$(id -g)" --memory 4g --cpus 4 --pids-limit 256 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -v "$DG:/src:ro" -v "$DG/workplace/gocache:/gocache" -v "$DG/workplace/gomodcache:/gomodcache" \
  -v "$ROOT/workplace/bin:/out" \
  -e GOCACHE=/gocache -e GOMODCACHE=/gomodcache -e HOME=/tmp -e GOFLAGS=-mod=mod -w /src \
  "$IMAGE" go build -o /out/phantasie-play ./apps/phantasie/cmd/phantasie-play
sha256sum "$ROOT/workplace/bin/phantasie-play"
