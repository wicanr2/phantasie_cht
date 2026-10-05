#!/bin/sh
# 017：於固定 music-r1 容器執行，第三方输入與 MIDI 唯讀掛載。
set -eu
[ "$#" -eq 3 ] || { echo '用法：render_score.sh 音色庫 MIDI目錄 新輸出目錄' >&2; exit 2; }
score_sf=$1
score_midi=$2
score_out=$3
[ -f "$score_sf" ] && [ -d "$score_midi" ] && [ ! -e "$score_out" ]
[ "$(sha256sum "$score_sf" | cut -d ' ' -f 1)" = 9575028c7a1f589f5770fccc8cff2734566af40cd26ed836944e9a5152688cfe ]
mkdir "$score_out"
fluidsynth --version > "$score_out/synth-version.txt"
ffmpeg -version > "$score_out/ffmpeg-version.txt"
for stem in score melody harmony bass percussion; do
    fluidsynth -ni -r 48000 -g 0.5 -C 0 -R 1 -T wav -O float \
        -o synth.reverb.room-size=0.25 -o synth.reverb.damp=0.7 \
        -o synth.reverb.width=70 -o synth.reverb.level=0.15 \
        -o synth.cpu-cores=1 -o synth.polyphony=256 \
        -F "$score_out/$stem-full.wav" "$score_sf" "$score_midi/$stem.mid" \
        > "$score_out/$stem-render.txt" 2>&1
    ffmpeg -nostdin -v error -i "$score_out/$stem-full.wav" -t 72 -ar 48000 -ac 2 \
        -af 'afade=t=out:st=71:d=1' -c:a pcm_f32le "$score_out/$stem.wav"
done
ffmpeg -nostdin -v error -i "$score_out/melody.wav" -i "$score_out/harmony.wav" \
    -i "$score_out/bass.wav" -i "$score_out/percussion.wav" \
    -filter_complex 'amix=inputs=4:duration=longest:dropout_transition=0:normalize=0' \
    -ar 48000 -ac 2 -c:a pcm_f32le "$score_out/mix.wav"
ffmpeg -nostdin -hide_banner -i "$score_out/mix.wav" \
    -af 'loudnorm=I=-18:TP=-1:LRA=11:print_format=json' -f null - \
    > "$score_out/loudness-pass1.txt" 2>&1
sha256sum "$score_sf" "$score_midi"/*.mid > "$score_out/inputs.sha256"
