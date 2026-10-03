# 目前狀態

日期：2026-10-04

總目標：用 dosgolem 完成《幽靈戰士》繁體中文化（使用者 2026-10-03 設定）。語言範圍：zh-TW（基準）、zh-CN、英文原版（關閉覆繪）、ja、ko。沒有手冊。專案規則在 `AGENTS.md`，分期目標在 `docs/goals/001-phases.md`。

## 已有

- 證據：`docs/re/001` 至 `009`（輸入清冊、probe 收據、IDA 靜態盤點、overlay 格式、視訊與文字路徑、動態收據、MESS 與 SCROLLS 格式、補充證據、`%s` 引數指標種類與 `strcat` 組句與字模遮罩）。索引在 `docs/re/README.md`。
- 規格（`docs/spec/`）：001 繪字事件與疊字核心、002 畫面操作與失效、003 catalog 與解析、004 字型與語言、005 前端與驗收。READY（2026-10-04，經四輪獨立審查）。狀態表在 `docs/spec/README.md`。
- dosgolem 分支 `phantasie-cht-overlay`（worktree `workplace/dosgolem-fw`，基底為疊字框架分支，本機無上游、未推送）：規格 197（`int 27h`，CONFORMED）、規格 `250-cga-int10-scroll-and-palette`（READY，已實作：CGA 圖形模式的 INT 10h 捲動、清除與色彩選擇，`oracle.CGAPalette()` 與 `CGA4RGB()`；22 筆獨立向量加突變測試通過，同狀態收據待做）、`apps/phantasie/`（啟動鏈、繪字與 sprintf 擷取、鍵閘、證據探針 `cmd/textlog`、證據原型 `cmd/overlay-prototype`）。
- 譯文：`text/ui.zh-TW.tsv`（677 筆，lint 0 錯誤，13 筆訊息列置中）、`text/prose.zh-TW.tsv`（981 行鍵）、`text/glossary.tsv`（含 12 個城鎮名）與 ja、ko 詞表、`text/phrases.zh-CN.tsv`、`text/STYLE.md`、`text/protected.tsv`。ja、ko 的 ui 批次翻譯進行中（機器輔助）。
- 工具（Docker 內執行）：`gamedata.py`、`enumerate_text.py`、`harvest_events.py`、`ui_candidates.py`、`ui_prune.py`、`ui_build.py`、`ui_merge.py`、`ui_merge_lang.py`、`ui_center.py`、`ui_align.py`、`prose_export.py`、`prose_build.py`、`lint_catalog.py`、`catalog_lib.py`、`build_font.py`、`derive_zhcn.py`、`ida/`；測試 `tools/tests/`（lint 反例 24 項、共用格式向量 57 項，向量在 `tests/vectors/`）。

## 已知事實（摘要，等級與證據見 `docs/re/`）

- 文字全經 `0110:25A5`（`printf` 風格）；視窗框線是單字元事件；組句先走 `sprintf`（`3E35`）進 `DS:638E`，可再以 `strcat`（`4DEF`）追加。
- 字模 `FONT` 是粗體（10 個字元墨點過半），`xlate.Colors` 的多數色規則會判反，顏色改由字模遮罩決定（規格 001 §8）。
- 畫面操作：反白（`0672`）、頁面緩衝區（`0D30`、`0CF0`、`0D10`、`0D50`）、視窗清除與捲動（BIOS `AH=06h`、`07h`）、`AH=0Bh`。
- 城鎮名來自 `TWNS.DAT`／`TWNS.INT`（12 個，`DS:8071 + 0123h × i`）；怪物記錄 3 筆（`7522 + 39h × i`）。
- 遊戲含 4 個手冊對照提示字串（OV2 入口函式內，隨機條件）。沒有手冊；依 `AGENTS.md` §1：維持原文、不翻譯、不作答、到達時回報使用者。四條隨機路線（約 4000 鍵 × 多條）未觸發。

## 阻擋與待決

- 規格 001 至 005 已 READY，`apps/phantasie` 實作進行中。
- 發行字型授權文字（OFL 1.1 或 GPLv2+ 字型例外）待核對。
- 玩家名音譯（ja、ko）、同一英文在不同畫面需不同譯文、MESS 選項與短訊息的事件形式、位置描述文字的來源（`docs/spec/003` §12）：見規格未決段。
- 本機 commit 尚未推送：phantasie 主分支領先 origin；dosgolem 分支無上游。推送逐項授權。

## 下一步

1. （已完成）規格升 READY。
2. 實作 `apps/phantasie`（格式引擎、catalog、擷取、解析、版面、疊字與 recolor、畫面操作與影子、語言切換、前端與收據工具），同狀態收據。
3. ja、ko 批次翻譯合併與 lint；zh-CN 以 OpenCC 轉換；各語言字型。
4. 路線與覆蓋清單，發行打包。
