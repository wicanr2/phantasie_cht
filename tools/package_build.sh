#!/usr/bin/env bash
# 013：Docker 內的離線建置步驟。/source 只讀；/out、/cache 可寫。
set -euo pipefail
platform=${1:?缺平台}
version=${2:?缺版號}
engine=${3:?缺引擎 commit}
[[ "$platform" == linux || "$platform" == windows || "$platform" == macos ]] || exit 2
[[ "$version" =~ ^v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}$ && "$engine" =~ ^[0-9a-f]{40}$ ]] || exit 2
[[ "$(go version)" == 'go version go1.24.13 linux/amd64' ]] || { echo 'Go 版本不符' >&2; exit 1; }
test -d /source/project/apps/phantasie/launcher
test -d /source/engine/apps/phantasie/cmd/phantasie-play
test -d /mods
test -d /cache
test -d /out
export GOCACHE=/cache GOMODCACHE=/mods GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local GOMAXPROCS=2
export GOFLAGS=-mod=readonly
flags="-s -w -X main.releaseVersion=$version -X main.engineCommit=$engine"
case "$platform" in
  linux) targets=(linux:amd64) ;;
  windows) targets=(windows:amd64) ;;
  macos) targets=(darwin:amd64 darwin:arm64) ;;
esac
cp /usr/local/go/LICENSE /out/LICENSE-Go
go version > /out/go-version.txt
for target in "${targets[@]}"; do
  export GOOS=${target%:*} GOARCH=${target#*:} CGO_ENABLED=0
  suffix=''
  extra="$flags"
  if [[ "$GOOS" == windows ]]; then suffix=.exe; extra="$flags -H=windowsgui"; fi
  cd /source/project/apps/phantasie/launcher
  go build -p 1 -trimpath -ldflags "$extra" -o "/out/launcher-$GOARCH$suffix" .
  cd /source/engine
  go build -p 1 -trimpath -ldflags '-s -w' -o "/out/receipt-$GOARCH$suffix" ./apps/phantasie/cmd/phantasie-receipt
  if [[ "$GOOS" == linux ]]; then
    export CGO_ENABLED=1 CC=gcc
  elif [[ "$GOOS" == darwin ]]; then
    export CGO_ENABLED=1 MACOSX_DEPLOYMENT_TARGET=11.0
    if [[ "$GOARCH" == amd64 ]]; then
      export CC=x86_64-apple-darwin24.5-clang CXX=x86_64-apple-darwin24.5-clang++
    else
      export CC=aarch64-apple-darwin24.5-clang CXX=aarch64-apple-darwin24.5-clang++
    fi
  fi
  backend_flags='-s -w'
  [[ "$GOOS" != windows ]] || backend_flags='-s -w -H=windowsgui'
  go build -p 1 -trimpath -ldflags "$backend_flags" -o "/out/backend-$GOARCH$suffix" ./apps/phantasie/cmd/phantasie-play
  for kind in launcher backend receipt; do
    go version -m "/out/$kind-$GOARCH$suffix" > "/out/modules-$kind-$GOARCH.txt"
  done
done
if [[ "$platform" == macos ]]; then
  /osxcross/bin/lipo -create /out/launcher-amd64 /out/launcher-arm64 -output /out/launcher-universal
  /osxcross/bin/lipo -create /out/backend-amd64 /out/backend-arm64 -output /out/backend-universal
elif [[ "$platform" == linux ]]; then
  readelf -d /out/backend-amd64 > /out/backend-dynamic.txt
  readelf --version-info /out/backend-amd64 > /out/backend-symbol-versions.txt
  /out/launcher-amd64 -version > /out/launcher-version.txt
  /out/launcher-amd64 -h > /out/launcher-help.txt
fi
printf 'PASS %s offline compilation only\n' "$platform"
