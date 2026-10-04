# 目前狀態

日期：2026-10-04

總目標：用 dosgolem 完成《幽靈戰士》繁體中文化（使用者 2026-10-03 設定）。語言範圍：zh-TW（基準）、zh-CN、英文原版（關閉覆繪）、ja、ko。使用者 2026-10-04 授權下載手冊並直接顯示答案，已取得與題目頁碼相符的合訂手冊。專案規則在 `AGENTS.md`，分期目標在 `docs/goals/001-phases.md`。

| 本輪範圍 | 目前程式與資料 | 最近驗證 | 交付狀態 |
|---|---|---|---|
| 道路描述與公會重名 | 收據工具及前端基底引擎 `277bb98`；HEAD `7b18f5c` 僅修註解；既有四語 catalog，新增兩條正常路線 | 四語 256 點同狀態；全文、置中、原生與兩倍像素範圍、清除、重試及兩項漏譯負對照通過 | 顯示已驗證；`37A0` 等鍵未接通，互動停留待修復，見 005 §13 |
| 卷軸閱讀與返回 | 引擎 `277bb98`；已重建前端與收據工具，正常路線 `scroll-read` | 四語 480 點同狀態、切換 33 點、13 行全文及原生／2 倍像素範圍、兩項負對照通過 | 007 CONFORMED；卷軸 8 正常抽樣，其他卷未逐頁驗收 |
| 地牢兩行訊息與還原 | 引擎 `f046ec4`；正常路線 `dungeon-message` | 四語、none/off/on/on-f2 共 320 點；完整原版狀態相同，兩種節奏的 Layer 相同，段落顯示與清除通過 | 收據與觸發資料流見 `docs/re/014`；005 保持 READY，其餘未量到分支見 §9.2 |
| 存檔與冷啟動讀回 | dosgolem `phantasie-cht-overlay`，引擎提交 `277bb98`；`workplace/bin/phantasie-receipt`，`-state` 與存檔清冊 | 四語、none/off/on/on-f2 共 240 點；原版狀態與存檔相同，重啟後角色畫面相同；存檔負對照及無存檔層回歸通過 | 規格 005 §10 CONFORMED；整份 005 仍 READY，其餘未量到分支見 §9.2 |
| 手冊答案提示 | 四語本機答案表與字型；互動前端 `workplace/bin/phantasie-play` | 物品、法術、四語及英文、答題返回的 68 個 A/B 檢查點；完整 1 MiB 記憶體相同；城鎮 36 點回歸通過 | 規格 006 CONFORMED；手冊與答案只留本機 |

## 已有

- 證據：`docs/re/001` 至 `015`（輸入清冊、probe 收據、IDA 靜態盤點、overlay 格式、視訊與文字路徑、動態收據、MESS 與 SCROLLS 格式、補充證據、`%s` 引數指標種類、位置描述文字 `OUT*.DAT`、地城位置列 `OV2:C400`、手冊來源與提示事件、存檔與冷啟動讀回、地牢事件格與訊息視窗、卷軸正常閱讀與整行安全範圍）。索引在 `docs/re/README.md`。
- 規格（`docs/spec/`）：001 繪字事件與疊字核心、002 畫面操作與失效、003 catalog 與解析、004 字型與語言、005 前端與驗收、006 手冊答案提示、007 卷軸整行顯示。001、003、004、006、007 已 CONFORMED；002（`load2`、`invert2`、`AH=0Bh` 未量到）與 005（MESS 訊息內選項與其他未量到分支見 §9.2）維持 READY。005 §10 的城鎮存檔與角色冷啟動讀回已 CONFORMED；§11 的地牢兩行訊息與還原已驗收。各規格結尾的「驗收收據」列出每個驗收項的證據與結果與未量到的原因。狀態表在 `docs/spec/README.md`。
- dosgolem 分支 `phantasie-cht-overlay`（worktree `workplace/dosgolem-fw`，基底為疊字框架分支，追蹤 `origin/phantasie-cht-overlay`）：規格 197（`int 27h`）與 `250-cga-int10-scroll-and-palette` 已 CONFORMED；`apps/phantasie/` 有格式引擎、catalog、擷取鉤子、解析、版面、疊字核心（含逐格反白狀態與依狀態切開疊字）、畫面操作與影子、語言切換、稽核、互動前端 `cmd/phantasie-play`、無頭收據工具 `cmd/phantasie-receipt`（路線 `@check`、`@snap`、`@lang`、`@assert-*`，診斷旗標 `-dump-keys`、`-dump-stamps`、`-audit-debug`，故障注入 `-fault`；可選 `-state` 提供各語言獨立存檔與摘要清冊）。
- 譯文：`text/ui.<語言>.tsv` 678 筆、`text/prose.<語言>.tsv` 1027 筆（MESS、SCROLLS 與 `OUT*.DAT` 的地圖描述），語言 zh-TW、zh-CN、ja、ko，四個語言 lint 0 錯誤；`text/glossary*.tsv`、`text/phrases.zh-CN.tsv`、`text/STYLE.md`、`text/protected.tsv`。ja、ko 為機器輔助，未經母語者校對；zh-CN 由 OpenCC 加詞組取代產生。
- 本機手冊提示：`text/manual.<語言>.tsv` 各 156 筆，100 個物品、54 個法術與兩個標題；由 `tools/build_manual_catalog.py` 產生。版控只保存不含答案的 `manual-labels.<語言>.tsv`、工具與合成測試。手冊在 `workplace/manual/`，核對表及收據在 `workplace/manual-derived/`。
- 路線（`tests/routes/`，20 條）：既有 `title`、`title-items`、`town`、`town-timed`、`guild`、`shops`、`messages`、`inn-distribute`、`save-load`、`map`、`dungeon`、`combat`（含整個戰鬥回合）、`weapon-list-scroll`、`lang-switch`、`lang-name`、`lang-options`，zh-TW 全部 PASS，非語言切換路線在 zh-CN、ja、ko 也全部 PASS，同狀態 A/B 全部通過。新增 `save-roundtrip-write`、`save-roundtrip-read` 必須依序使用同一 `-state`，四語與三模式及節奏驗收通過；收據在 `workplace/receipts/save-roundtrip/`。新增 `dungeon-message` 的四語 320 點同狀態通過，收據在 `workplace/explore-dungeon/ab-message-v2/`。新增 `scroll-read` 的四語 480 點與正常返回，收據在 `workplace/explore-main/ab-scroll/`；引擎 277bb98 的四語存讀檔回歸在 `workplace/explore-main/scroll-save-regression/`。
- 新增 `map-description`、`guild-duplicate` 的四語 256 點顯示收據在 `workplace/explore-main/ab-ui-windows/`；獨立全文與像素驗證及兩項漏譯負對照通過。這兩條路線以固定步數擷取，不證明互動等鍵已接通；限制見 005 §13。
- 工具（Docker 內執行）：`tools/run_receipt.sh`、`tools/ab_receipt.sh`、`tools/save_roundtrip.py`、`tools/build_fonts.sh`、`tools/build_play.sh`、`tools/smoke_play.sh`；譯文工具 `gamedata.py`、`enumerate_text.py`、`harvest_events.py`、`ui_*.py`、`prose_*.py`、`out_text*.py`、`lint_catalog.py`、`catalog_lib.py`、`build_font.py`、`derive_zhcn.py`、`ida/`；測試 `tools/tests/`（lint 反例 24 項、共用格式向量 61 項）。

## 已知事實（摘要，等級與證據見 `docs/re/`）

- 文字全經 `0110:25A5`（`printf` 風格）；視窗框線是單字元事件；組句先走 `sprintf`（`3E35`）進 `DS:638E`，可再以 `strcat`（`4DEF`）追加。
- 字模 `FONT` 是粗體，`xlate.Colors` 的多數色規則會判反，顏色由字模遮罩與逐格反白狀態決定（規格 001 §8）。反白矩形可以只涵蓋事件的一部分。
- 畫面操作：反白（`0672`）、頁面緩衝區（`0D30`、`0CF0`、`0D10`、`0D50`）、視窗清除與捲動（BIOS `AH=06h`、`07h`）、`AH=0Bh`。
- 城鎮名來自 `TWNS.DAT`／`TWNS.INT`（12 個）；怪物記錄 3 筆；大地圖位置描述來自 `OUT*.DAT`（`DS:C6FA`）；地城位置列的格式字串指標是 `OV2:C400`。
- 戰鬥回合結算沒有讀鍵入口，用 `@snap` 擷取；沒有隊員時進店只有約 101 萬步的停頓，沒有訊息文字；神祕客有逐行打出的訊息。
- 遊戲含物品與法術兩種手冊題，共 4 個提示事件。物品題與重試時的法術題已從正常玩家路線觀察到。提示顯示手冊答案，保留原版三個選項與判定，不自動送鍵。來源與位址見 `docs/re/012-manual-prompts.md`，顯示契約見 `docs/spec/006-manual-answer-hints.md`。手冊、答案表與作答路線只留本機。

## 阻擋與待決

- 已定位且待修復：`37A0` 是另一條等鍵路徑，現有按鍵閘門只涵蓋 `37C2`；道路描述及重名提示會立即返回。這兩條路線的顯示與清除已驗證，互動停留未完成。
- 未量到：MESS 訊息內選項與其他事件型別；其他地圖描述格；地城存檔及備份還原；`load2`、`invert2`、INT 10h `AH=0Bh`。
- 已知限制：被原版逐格重畫的數字是粗體，其餘疊字數字是細體，字重不一致；ja、ko 的數字欄位右緣有少數 lint 警告。
- 發行字型授權文字（OFL 1.1 或 GPLv2+ 字型例外）待核對。
- 玩家名音譯（ja、ko）、同一英文在不同畫面需不同譯文：見規格未決段。
- 遠端入口：中文化 `origin/main`；dosgolem `origin/phantasie-cht-overlay`。本輪提交與推送已授權，Issue 寫入、轉公開與 Release 仍逐項授權。

## 下一步

1. 先補 `37A0` 等鍵的證據與規格，讓訊息停留直到玩家確認，再回歸前端、收據工具與既有正常路線。
2. 抽樣 MESS 訊息內選項及其他地圖描述；002 的未量到操作與 005 其餘分支沿原規格驗收。
3. 發行階段：打包、外洩掃描、發行前實機冒煙、Release 說明。
4. 轉公開前做公開稽核；影片與推廣視使用者決定。
