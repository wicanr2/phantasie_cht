# 目前狀態

日期：2026-10-04

總目標：用 dosgolem 完成《幽靈戰士》繁體中文化（使用者 2026-10-03 設定）。語言範圍：zh-TW（基準）、zh-CN、英文原版（關閉覆繪）、ja、ko。使用者 2026-10-04 授權下載手冊並直接顯示答案，已取得與題目頁碼相符的合訂手冊。專案規則在 `AGENTS.md`，分期目標在 `docs/goals/001-phases.md`。

| 本輪範圍 | 目前程式與資料 | 最近驗證 | 交付狀態 |
|---|---|---|---|
| 手冊答案提示 | dosgolem `phantasie-cht-overlay`，引擎提交 `e90336d`；四語本機答案表與字型；`workplace/bin/phantasie-play` | 物品、法術、四語及英文、答題返回的 68 個 A/B 檢查點；完整 1 MiB 記憶體相同；城鎮 36 點回歸通過 | 規格 006 CONFORMED；本輪提交與推送已授權 |

## 已有

- 證據：`docs/re/001` 至 `012`（輸入清冊、probe 收據、IDA 靜態盤點、overlay 格式、視訊與文字路徑、動態收據、MESS 與 SCROLLS 格式、補充證據、`%s` 引數指標種類、位置描述文字 `OUT*.DAT`、地城位置列 `OV2:C400`、手冊來源與提示事件）。索引在 `docs/re/README.md`。
- 規格（`docs/spec/`）：001 繪字事件與疊字核心、002 畫面操作與失效、003 catalog 與解析、004 字型與語言、005 前端與驗收、006 手冊答案提示。001、003、004、006 已 CONFORMED；002（`load2`、`invert2`、`AH=0Bh` 未量到）與 005（必備路線尚缺地牢訊息視窗、卷軸閱讀、存檔後讀回）維持 READY。各規格結尾的「驗收收據」列出每個驗收項的證據與結果與未量到的原因。狀態表在 `docs/spec/README.md`。
- dosgolem 分支 `phantasie-cht-overlay`（worktree `workplace/dosgolem-fw`，基底為疊字框架分支，追蹤 `origin/phantasie-cht-overlay`，已推送）：規格 197（`int 27h`）與 `250-cga-int10-scroll-and-palette` 已 CONFORMED；`apps/phantasie/` 有格式引擎、catalog、擷取鉤子、解析、版面、疊字核心（含逐格反白狀態與依狀態切開疊字）、畫面操作與影子、語言切換、稽核、互動前端 `cmd/phantasie-play`、無頭收據工具 `cmd/phantasie-receipt`（路線 `@check`、`@snap`、`@lang`、`@assert-*`，診斷旗標 `-dump-keys`、`-dump-stamps`、`-audit-debug`，故障注入 `-fault`）。
- 譯文：`text/ui.<語言>.tsv` 678 筆、`text/prose.<語言>.tsv` 1027 筆（MESS、SCROLLS 與 `OUT*.DAT` 的地圖描述），語言 zh-TW、zh-CN、ja、ko，四個語言 lint 0 錯誤；`text/glossary*.tsv`、`text/phrases.zh-CN.tsv`、`text/STYLE.md`、`text/protected.tsv`。ja、ko 為機器輔助，未經母語者校對；zh-CN 由 OpenCC 加詞組取代產生。
- 本機手冊提示：`text/manual.<語言>.tsv` 各 156 筆，100 個物品、54 個法術與兩個標題；由 `tools/build_manual_catalog.py` 產生。版控只保存不含答案的 `manual-labels.<語言>.tsv`、工具與合成測試。手冊在 `workplace/manual/`，核對表及收據在 `workplace/manual-derived/`。
- 路線（`tests/routes/`，16 條）：`title`、`title-items`、`town`、`town-timed`、`guild`、`shops`、`messages`、`inn-distribute`、`save-load`、`map`、`dungeon`、`combat`（含整個戰鬥回合）、`weapon-list-scroll`、`lang-switch`、`lang-name`、`lang-options`。zh-TW 全部 PASS，非語言切換路線在 zh-CN、ja、ko 也全部 PASS，同狀態 A/B 全部通過。
- 工具（Docker 內執行）：`tools/run_receipt.sh`、`tools/ab_receipt.sh`、`tools/build_fonts.sh`、`tools/build_play.sh`、`tools/smoke_play.sh`；譯文工具 `gamedata.py`、`enumerate_text.py`、`harvest_events.py`、`ui_*.py`、`prose_*.py`、`out_text*.py`、`lint_catalog.py`、`catalog_lib.py`、`build_font.py`、`derive_zhcn.py`、`ida/`；測試 `tools/tests/`（lint 反例 24 項、共用格式向量 61 項）。

## 已知事實（摘要，等級與證據見 `docs/re/`）

- 文字全經 `0110:25A5`（`printf` 風格）；視窗框線是單字元事件；組句先走 `sprintf`（`3E35`）進 `DS:638E`，可再以 `strcat`（`4DEF`）追加。
- 字模 `FONT` 是粗體，`xlate.Colors` 的多數色規則會判反，顏色由字模遮罩與逐格反白狀態決定（規格 001 §8）。反白矩形可以只涵蓋事件的一部分。
- 畫面操作：反白（`0672`）、頁面緩衝區（`0D30`、`0CF0`、`0D10`、`0D50`）、視窗清除與捲動（BIOS `AH=06h`、`07h`）、`AH=0Bh`。
- 城鎮名來自 `TWNS.DAT`／`TWNS.INT`（12 個）；怪物記錄 3 筆；大地圖位置描述來自 `OUT*.DAT`（`DS:C6FA`）；地城位置列的格式字串指標是 `OV2:C400`。
- 戰鬥回合結算沒有讀鍵入口，用 `@snap` 擷取；沒有隊員時進店只有約 101 萬步的停頓，沒有訊息文字；神祕客有逐行打出的訊息。
- 遊戲含物品與法術兩種手冊題，共 4 個提示事件。物品題與重試時的法術題已從正常玩家路線觀察到。提示顯示手冊答案，保留原版三個選項與判定，不自動送鍵。來源與位址見 `docs/re/012-manual-prompts.md`，顯示契約見 `docs/spec/006-manual-answer-hints.md`。手冊、答案表與作答路線只留本機。

## 阻擋與待決

- 未量到：地牢訊息視窗（MESS）與大地圖位置描述（`OUT*.DAT`）的觸發格；卷軸閱讀（拿不到卷軸物品）；存檔後讀回（收據工具沒有 `SetScratch`）；公會重名輸入訊息；`load2`、`invert2`、INT 10h `AH=0Bh`。
- 已知限制：被原版逐格重畫的數字是粗體，其餘疊字數字是細體，字重不一致；ja、ko 的數字欄位右緣有少數 lint 警告。
- 發行字型授權文字（OFL 1.1 或 GPLv2+ 字型例外）待核對。
- 玩家名音譯（ja、ko）、同一英文在不同畫面需不同譯文：見規格未決段。
- 遠端入口：中文化 `origin/main`；dosgolem `origin/phantasie-cht-overlay`。本輪提交與推送已授權，Issue 寫入、轉公開與 Release 仍逐項授權。

## 下一步

1. 找到地牢訊息視窗與大地圖描述的觸發格，補路線。
2. 發行階段：打包、外洩掃描、發行前實機冒煙、Release 說明。
3. 轉公開前做公開稽核；影片與推廣視使用者決定。
