#!/usr/bin/env bash
# IDA Pro 9.4 headless 包裝（Docker）。
#
#   tools/ida/ida.sh survey    建庫並匯出盤點資料（workplace/ida/out/）
#
# 輸入：workplace/ida/phantasi_unpacked.bin，是 dosgolem probe 在 LZEXE 解壓完成後
# 傾印的 0110:0000 起 117,232 bytes（見 docs/re/002-probe-receipt.md）。
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
BIN="phantasi_unpacked.bin"
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

cmd="${1:-}"
case "$cmd" in
  survey)
    test -f "$WORK/$BIN" || { echo "找不到 $WORK/$BIN" >&2; exit 1; }
    # 巢狀掛載的目標先由本人建好，否則 dockerd 會以 root 建出空目錄。
    mkdir -p "$WORK/out" "$WORK/tools"
    # 一次性資料庫：每次重建，不在舊庫上試跑。
    rm -f "$WORK"/phantasi.i64 "$WORK"/phantasi.id0 "$WORK"/phantasi.id1 \
          "$WORK"/phantasi.id2 "$WORK"/phantasi.nam "$WORK"/phantasi.til
    rm -f "$WORK"/out/survey.json "$WORK"/out/phantasi.asm
    run idat -A -c -p8086 -Tbinary "-b$LOAD_PARAS" -o/work/phantasi.i64 \
      "-S/work/tools/export_survey.py /work/out /work/$BIN" "/work/$BIN" || true
    ls -l "$WORK/out"
    ;;
  *)
    echo "用法: tools/ida/ida.sh survey" >&2
    exit 2
    ;;
esac
