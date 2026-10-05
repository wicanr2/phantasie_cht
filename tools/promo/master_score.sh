#!/bin/sh
# 017：依第一遍實测計畫產生母帶；在 music-r1 容器內執行。
set -eu
[ "$#" -eq 1 ] || { echo '用法：master_score.sh 音軌目錄' >&2; exit 2; }
score_out=$1
[ -f "$score_out/master-filter.txt" ] && [ ! -e "$score_out/master.wav" ]
read -r score_mix_sha score_filter_sha score_plan_sha score_extra < "$score_out/master-checks.txt"
[ -z "$score_extra" ]
for score_sha in "$score_mix_sha" "$score_filter_sha" "$score_plan_sha"; do
    [ "${#score_sha}" -eq 64 ]
    case "$score_sha" in *[!0-9a-f]*) echo '不合法的輸入雜湊' >&2; exit 2;; esac
done
[ "$(sha256sum "$score_out/mix.wav" | cut -d ' ' -f 1)" = "$score_mix_sha" ]
[ "$(sha256sum "$score_out/master-filter.txt" | cut -d ' ' -f 1)" = "$score_filter_sha" ]
[ "$(sha256sum "$score_out/master-plan.json" | cut -d ' ' -f 1)" = "$score_plan_sha" ]
score_filter=$(cat "$score_out/master-filter.txt")
case "$score_filter" in *[!0-9a-zA-Z=_:.-]*) echo '不合法的合成參數' >&2; exit 2;; esac
ffmpeg -nostdin -hide_banner -i "$score_out/mix.wav" -af "$score_filter" \
    -ar 48000 -ac 2 -c:a pcm_s24le "$score_out/master.wav" \
    > "$score_out/loudness-pass2.txt" 2>&1
ffmpeg -nostdin -v error -i "$score_out/master.wav" -c:a libvorbis -q:a 6 "$score_out/master.ogg"
ffmpeg -nostdin -hide_banner -i "$score_out/master.wav" \
    -af 'loudnorm=I=-18:TP=-1:LRA=11:print_format=json' -f null - \
    > "$score_out/master-measurement.txt" 2>&1
ffmpeg -nostdin -hide_banner -ss 45.6 -t 2.4 -i "$score_out/master.wav" \
    -af astats=metadata=0:reset=0 -f null - > "$score_out/void-measurement.txt" 2>&1
ffprobe -v error -show_format -show_streams -of json "$score_out/master.wav" > "$score_out/master-probe.json"
ffprobe -v error -show_format -show_streams -of json "$score_out/master.ogg" > "$score_out/ogg-probe.json"
