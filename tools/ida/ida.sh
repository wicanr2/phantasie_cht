#!/usr/bin/env bash
# IDA Pro 9.4 headless 包裝（Docker）。
#
#   tools/ida/ida.sh survey          建庫並匯出常駐映像的盤點資料（workplace/ida/out/）
#   tools/ida/ida.sh overlay ov1     建庫並匯出 overlay 的盤點資料（ov1 或 ov2）
#
# 輸入（都在 workplace/ida/，不進版控）：
#   phantasi_unpacked.bin  dosgolem probe 在 LZEXE 解壓後傾印的 0110:0000 起 117,232 bytes
#                          （見 docs/re/002-probe-receipt.md）
#   ov1_composed.bin、ov2_composed.bin  tools/ida/compose_overlay.py 把 overlay 依載入器語意
#                          疊在常駐映像上的結果（見 docs/re/004-overlay-format.md）
#
# 契約（依 ~/ida_94_official/knowledge-base/ida-94-tools.md）：
#   - 一次性容器：--rm、--network none、資源上限、目前 UID/GID、log rotation。
#   - 授權環境由 image 內部提供，不在 log、報告或版控出現。
#   - headless 的 print 不進 stdout，結果一律寫檔到 workplace/ida/out/。
#   - exit code 不是證據；以輸出檔存在、非空、輸入雜湊相符判定。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK="$ROOT/workplace/ida"
IMAGE="${IDA_IMAGE:-ida-pro-9.4-idapython:locked-v1}"
# 載入段 0110：映像在 dosgolem 內的載入段（PSP 0100 + 10h）。-b 的單位是 16 bytes。
LOAD_PARAS="110"

run() {
  docker run --rm --network none \
    --memory "${IDA_MEM:-3g}" --cpus "${IDA_CPUS:-2}" --pids-limit 256 \
    --log-opt max-size=10m --log-opt max-file=3 \
    -u "$(id -u):$(id -g)" \
    -v "$WORK:/work" \
    -v "$ROOT/tools/ida:/work/tools:ro" \
    -w /work \
    "$IMAGE" "$@"
}

# build <標籤> <映像檔名> <腳本參數...>
build() {
  local label="$1" bin="$2"; shift 2
  test -f "$WORK/$bin" || { echo "找不到 $WORK/$bin" >&2; exit 1; }
  # 巢狀掛載的目標先由本人建好，否則 dockerd 會以 root 建出空目錄。
  mkdir -p "$WORK/out" "$WORK/tools"
  # 一次性資料庫：每次重建，不在舊庫上試跑。
  rm -f "$WORK/$label".i64 "$WORK/$label".id0 "$WORK/$label".id1 \
        "$WORK/$label".id2 "$WORK/$label".nam "$WORK/$label".til
  run idat -A -c -p8086 -Tbinary "-b$LOAD_PARAS" "-o/work/$label.i64" \
    "-S/work/tools/export_survey.py /work/out /work/$bin $*" "/work/$bin" || true
  ls -l "$WORK/out"
}

cmd="${1:-}"
case "$cmd" in
  survey)
    rm -f "$WORK"/out/survey.json "$WORK"/out/phantasi.asm
    build phantasi phantasi_unpacked.bin resident 4EE5 0 C9F0
    ;;
  overlay)
    which="${2:-}"
    # 入口偏移與程式碼範圍取自各 overlay 標頭（docs/re/004-overlay-format.md）。
    case "$which" in
      ov1) entry=A591; hi=ACD5 ;;
      ov2) entry=C8CF; hi=C98F ;;
      *) echo "用法: tools/ida/ida.sh overlay ov1|ov2" >&2; exit 2 ;;
    esac
    rm -f "$WORK/out/survey_$which.json" "$WORK/out/$which.asm"
    build "$which" "${which}_composed.bin" "$which" "$entry" 53EA "$hi"
    ;;
  *)
    echo "用法: tools/ida/ida.sh survey | overlay ov1|ov2" >&2
    exit 2
    ;;
esac
