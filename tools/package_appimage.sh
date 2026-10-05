#!/usr/bin/env bash
# 013：只在固定 AppImage 容器內執行，/stage、/runtime 唯讀。
set -euo pipefail
set -C
name=${1:?缺封包名稱}
version=${2:?缺版號}
[[ "$name" =~ ^phantasie-cht-v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}-linux-x86_64-(patch|full-local)$ ]] || exit 2
[[ "$name" == "phantasie-cht-$version-linux-x86_64-"* ]] || exit 2
test -d /stage
test -f /runtime/runtime-x86_64
[[ "$(stat -c %s /runtime/runtime-x86_64)" == 944632 ]] || exit 1
printf '%s  %s\n' 0341f742081a99f00f6c8654d742e470e85c66dafabd17d851ab5b662dc7f511 /runtime/runtime-x86_64 | sha256sum -c -
epoch=$(date -u -d "${version: -8:4}-${version: -4:2}-${version: -2:2}" +%s)
test ! -e "/work/artifacts/$name.AppImage"
test ! -e "/work/$name.squashfs"
mksquashfs /stage "/work/$name.squashfs" -noappend -no-xattrs -all-root -processors 1 -no-progress -comp gzip \
  -mkfs-time "$epoch" -all-time "$epoch" > "/work/$name-build.log"
cat /runtime/runtime-x86_64 "/work/$name.squashfs" > "/work/artifacts/$name.AppImage"
chmod 755 "/work/artifacts/$name.AppImage"
mkdir "/work/extracted/$name"
cd "/work/extracted/$name"
"/work/artifacts/$name.AppImage" --appimage-offset > "/work/$name-offset.txt"
[[ "$(cat "/work/$name-offset.txt")" == 944632 ]] || exit 1
"/work/artifacts/$name.AppImage" --appimage-extract > "/work/$name-extract.log"
test -x squashfs-root/AppRun
printf 'PASS %s AppImage build/extract only\n' "$name"
