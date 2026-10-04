# 目前狀態

日期：2026-10-04

總目標：用 dosgolem 完成《幽靈戰士》繁體中文化（使用者 2026-10-03 設定）。語言範圍：zh-TW（基準）、zh-CN、英文原版（關閉覆繪）、ja、ko。使用者 2026-10-04 授權下載手冊並直接顯示答案，已取得與題目頁碼相符的合訂手冊。專案規則在 `AGENTS.md`，分期目標在 `docs/goals/001-phases.md`。

| 本輪範圍 | 目前程式與資料 | 最近驗證 | 交付狀態 |
|---|---|---|---|
| 道路描述與公會重名 | 引擎 `60b76b3`，前置 guard `dcc1b9d`；已重建前端與收據工具 | 四語 192 點同狀態、每組 120 次停留、全文及兩種倍率範圍、切換、確認、清除、重試與負對照通過；GUI 真實按鍵通過 | 008 CONFORMED |
| 卷軸閱讀與返回 | 引擎 `60b76b3`；正常路線 `scroll-read` 加明示購買確認 | 四語 496 點同狀態；既有切換 33 點、13 行全文、兩種倍率及負對照有效 | 007 CONFORMED；卷軸 8 正常抽樣，其他卷未逐頁驗收 |
| 地牢兩行訊息與還原 | 引擎 `60b76b3`；正常路線 `dungeon-message` 加確認停點 | zh-TW 21 點回歸 PASS；先前四語 320 點的顯示與還原證據仍有效 | 收據與觸發資料流見 `docs/re/014`、008；005 保持 READY，其餘未量到分支見 §9.2 |
| 存檔與冷啟動讀回 | 引擎 `60b76b3`；`workplace/bin/phantasie-receipt`，`-state` 與存檔清冊 | 四語、四模式 240 點回歸，原版狀態與存檔相同，重啟後角色畫面相同；既有負對照有效 | 規格 005 §10 CONFORMED；整份 005 仍 READY |
| 手冊答案提示 | 引擎 `60b76b3`；四語本機答案表與字型 | 確認等鍵後，物品、法術、四語及英文、返回，三模式各 72 點，共 216 點；完整原版狀態相同 | 006 CONFORMED；手冊與答案只留本機 |
| 地牢訊息選項 | 引擎 `60b76b3`；`dungeon-options` 正常路線 | 四語四模式 512 點同狀態；全文、反白、兩個選擇、重訪、後續段落、戰鬥及色盤後顏色、兩種倍率與負對照通過 | 兩個 11 字元選項已驗證；其餘欄寬仍未量到，見 RE017、005 §14 |
| 寶箱短訊息 | 引擎 `60b76b3`；匯出工具明示納入 `mess5:61`，四語各新增一列正文 | 16 組 2496 個原版狀態點相同；八個短訊息停點共 96 個 UI PASS，40 項全文及倍率檢查、刪除正文負對照與 32 點拉桿回歸通過 | 009 CONFORMED；其他短訊息、3 字元選項仍未量到，見 RE018、005 §15 |
| 第四地牢探索 | 引擎 `60b76b3`；本機正常旅行路線與只讀探針 | 原版入口到 `(14,21)`、九選項目標未到達；死亡顯示另見 020 | 入口與候選資料見 [019](docs/re/019-dungeon-four-reachability.md)；九選項仍未量到 |
| 戰鬥死亡訊息 | 引擎 `60b76b3`；本機正常死亡路線，程式與 catalog 不變 | 四模式 888 個原版狀態點相同；兩個死亡場景四語切換、20 項全文及倍率檢查、英文視圖、回切、返回及負對照通過 | 005 §16 已驗收；全滅仍未量到；勝利見 021，死亡見 [020](docs/re/020-combat-death-messages.md) |
| 戰鬥勝利與獎勵 | 引擎 `60b76b3`；正常 DNG1 戰鬥、本機長路線，公開 `combat` 只修正兩個取樣數字 | 四模式 516 個原版狀態相同、387 個 UI PASS；四語全文、數值、語言往返、返回及負對照通過 | 005 §17 已驗收；全滅仍未量到，見 [021](docs/re/021-combat-victory.md) |

## 已有

- 證據：`docs/re/001` 至 `021`（輸入清冊、probe 收據、IDA 靜態盤點、overlay 格式、視訊與文字路徑、動態收據、MESS 與 SCROLLS 格式、補充證據、`%s` 引數指標種類、位置描述文字 `OUT*.DAT`、地城位置列 `OV2:C400`、手冊來源與提示事件、存檔與冷啟動讀回、地牢事件格與訊息視窗、卷軸正常閱讀與整行安全範圍、第二條等鍵、訊息選項及拉桿後續、寶箱短訊息、第四地牢入口與戰鬥事件、死亡全文與四語切換、正常勝利及數值結算）。索引在 `docs/re/README.md`。
- 規格（`docs/spec/`）：001 繪字事件與疊字核心、002 畫面操作與失效、003 catalog 與解析、004 字型與語言、005 前端與驗收、006 手冊答案提示、007 卷軸整行顯示、008 確認等鍵、009 短訊息正文。001、003、004、006、007、008、009 已 CONFORMED。002（`load2` 已觀察，獨立還原未驗收見 §12；`invert2` 及色盤其餘分支未量到，BL=0 見 §11）與 005（兩個訊息選項見 §14，寶箱短訊息見 §15，其餘分支見 §9.2）維持 READY。005 §10 的城鎮存檔與角色冷啟動讀回已 CONFORMED；§11 地牢兩行訊息與還原、§13 提示停留與確認已驗證。狀態表在 `docs/spec/README.md`。
- dosgolem 分支 `phantasie-cht-overlay`（worktree `workplace/dosgolem-fw`，追蹤 `origin/phantasie-cht-overlay`）：規格 197（`int 27h`）、250（CGA 捲動及色盤）與 251（指令前 guard）已 CONFORMED。`apps/phantasie/` 有格式引擎、catalog、擷取鉤子、解析、版面、疊字核心、畫面操作與影子、語言切換及稽核；互動前端在 `apps/phantasie/cmd/phantasie-play`，無頭收據工具在 `apps/phantasie/cmd/phantasie-receipt`。收據路線支援 `@check`、`@snap`、`@lang`、`@assert-*`，診斷旗標 `-dump-keys`、`-dump-stamps`、`-audit-debug`，測試故障注入 `-fault`；可選 `-state` 提供各語言獨立存檔與摘要清冊。
- 譯文：`text/ui.<語言>.tsv` 678 筆、`text/prose.<語言>.tsv` 1028 筆（MESS、SCROLLS 與 `OUT*.DAT` 的地圖描述），每語合計 1706 筆，語言 zh-TW、zh-CN、ja、ko，四個語言 lint 0 錯誤；`text/glossary*.tsv`、`text/phrases.zh-CN.tsv`、`text/STYLE.md`、`text/protected.tsv`。ja、ko 為機器輔助，未經母語者校對；zh-CN 由 OpenCC 加詞組取代產生。
- 本機手冊提示：`text/manual.<語言>.tsv` 各 156 筆，100 個物品、54 個法術與兩個標題；由 `tools/build_manual_catalog.py` 產生。版控只保存不含答案的 `manual-labels.<語言>.tsv`、工具與合成測試。手冊在 `workplace/manual/`，核對表及收據在 `workplace/manual-derived/`。
- 路線（`tests/routes/`，23 條）：確認等鍵後既有 20 條一般路線共 438 點 zh-TW PASS，收據在 `workplace/explore-main/wait-regression/`。新增 `dungeon-options` 32 點，四語四模式共 512 點通過，收據在 `workplace/explore-dungeon/ab-dungeon-options/`。另外 `save-roundtrip-write`、`save-roundtrip-read` 依序使用同一 `-state`，四語四模式 240 點回歸通過，收據在 `wait-save-regression/`。四語卷軸 31 點、四模式共 496 點同狀態與節奏回歸在 `wait-scroll-regression/`。其他非語言切換路線的四語 A/B 為既有版本證據，未宣稱本輪重跑全部語言。
- `map-description`、`guild-duplicate` 改在正常確認點停下，各四語四模式共 192 點，收據在 `workplace/explore-main/ab-wait-windows/`；全文、像素範圍、停留、語言切換、確認返回及 guard 負對照通過。契約與完整回歸入口見 008。
- 寶箱短訊息的正常長路線只留本機，收據在 `workplace/explore-dungeon/ab-dungeon-short-v2/`。156 點中 85 個無文字旅行點只作原版狀態診斷；UI 完成聲明限八個 `short-*` 停點。正式清冊見 `short-verification-manifest.json`，範圍及工具處置見 009。
- 工具（Docker 內執行）：`tools/run_receipt.sh`、`tools/ab_receipt.sh`、`tools/save_roundtrip.py`、`tools/build_fonts.sh`、`tools/build_play.sh`、`tools/smoke_play.sh`；譯文工具 `gamedata.py`、`enumerate_text.py`、`harvest_events.py`、`ui_*.py`、`prose_*.py`、`out_text*.py`、`lint_catalog.py`、`catalog_lib.py`、`build_font.py`、`derive_zhcn.py`、`ida/`；測試 `tools/tests/`（lint 反例 24 項、共用格式向量 61 項）。

## 已知事實（摘要，等級與證據見 `docs/re/`）

- 文字全經 `0110:25A5`（`printf` 風格）；視窗框線是單字元事件；組句先走 `sprintf`（`3E35`）進 `DS:638E`，可再以 `strcat`（`4DEF`）追加。
- 字模 `FONT` 是粗體，`xlate.Colors` 的多數色規則會判反，顏色由字模遮罩與逐格反白狀態決定（規格 001 §8）。反白矩形可以只涵蓋事件的一部分。
- 畫面操作：反白（`0672`）、頁面緩衝區（`0D30`、`0CF0`、`0D10`、`0D50`）、視窗清除與捲動（BIOS `AH=06h`、`07h`）、`AH=0Bh`。
- 城鎮名來自 `TWNS.DAT`／`TWNS.INT`（12 個）；怪物記錄 3 筆；大地圖位置描述來自 `OUT*.DAT`（`DS:C6FA`）；地城位置列的格式字串指標是 `OV2:C400`。
- 戰鬥回合結算沒有讀鍵入口，用 `@snap` 擷取；沒有隊員時進店只有約 101 萬步的停頓，沒有訊息文字；神祕客有逐行打出的訊息。
- 遊戲含物品與法術兩種手冊題，共 4 個提示事件。物品題與重試時的法術題已從正常玩家路線觀察到。提示顯示手冊答案，保留原版三個選項與判定，不自動送鍵。來源與位址見 `docs/re/012-manual-prompts.md`，顯示契約見 `docs/spec/006-manual-answer-hints.md`。手冊、答案表與作答路線只留本機。

## 阻擋與待決

- 未量到：MESS5 索引 61 以外的短訊息、其他選項欄寬與事件型別；戰鬥全滅；其他地圖描述格；地城存檔及備份還原；`invert2`。`load2` 的正常呼叫已量到，獨立還原仍待驗收，見 [021](docs/re/021-combat-victory.md) 與 002 §12。INT 10h `AH=0Bh BL=0` 已由 [017](docs/re/017-dungeon-message-options.md) 量到，`BL=1` 及原有文字跨色盤的失效處理仍未量到。
- 已知限制：被原版逐格重畫的數字是粗體，其餘疊字數字是細體，字重不一致；ja、ko 的數字欄位右緣有少數 lint 警告。
- 發行字型的雙授權條款與作者聲明已核對，來源及雜湊見 `font/README.md`；散布採 OFL 1.1 或 GPLv2+ 含字型例外待使用者選定。
- 玩家名音譯（ja、ko）、同一英文在不同畫面需不同譯文：見規格未決段。
- 遠端入口：中文化 `origin/main`；dosgolem `origin/phantasie-cht-overlay`。本輪提交與推送已授權，Issue 寫入、轉公開與 Release 仍逐項授權。

## 下一步

1. 抽樣其他 MESS 短訊息、3 字元選項欄寬與地圖描述；002 的未驗收操作與 005 其餘分支沿原規格驗收。
2. 發行階段：核對字型授權、打包、外洩掃描、發行前實機冒煙、Release 說明。
3. 轉公開前做公開稽核；影片與推廣視使用者決定。
