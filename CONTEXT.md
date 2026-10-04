# 目前狀態

日期：2026-10-05

總目標：用 dosgolem 完成《幽靈戰士》繁體中文化（使用者 2026-10-03 設定）。語言範圍：zh-TW（基準）、zh-CN、英文原版（關閉覆繪）、ja、ko。使用者 2026-10-04 授權下載手冊並直接顯示答案，已取得與題目頁碼相符的合訂手冊。專案規則在 `AGENTS.md`，分期目標在 `docs/goals/001-phases.md`。

目前引擎為 `8d9807d`，本機前端與收據工具已重建。表內既有項目的 `60b76b3` 是其正式證據基準。最近一輪只修資料列舉的完整選項字元流，未改執行期覆繪；正常畫面驗收仍以各列收據為準。

| 範圍 | 程式與證據基準 | 最近驗證 | 交付狀態 |
|---|---|---|---|
| 道路描述與公會重名 | 引擎 `60b76b3`，前置 guard `dcc1b9d`；已重建前端與收據工具 | 四語 192 點同狀態、每組 120 次停留、全文及兩種倍率範圍、切換、確認、清除、重試與負對照通過；GUI 真實按鍵通過 | 008 CONFORMED |
| 卷軸閱讀與返回 | 引擎 `60b76b3`；正常路線 `scroll-read` 加明示購買確認 | 四語 496 點同狀態；既有切換 33 點、13 行全文、兩種倍率及負對照有效 | 007 CONFORMED；卷軸 8 正常抽樣，其他卷未逐頁驗收 |
| 地牢兩行訊息與還原 | 引擎 `60b76b3`；正常路線 `dungeon-message` 加確認停點 | zh-TW 21 點回歸 PASS；先前四語 320 點的顯示與還原證據仍有效 | 收據與觸發資料流見 `docs/re/014`、008；005 保持 READY，其餘未量到分支見 §9.2 |
| 存檔與冷啟動讀回 | 引擎 `60b76b3`；`workplace/bin/phantasie-receipt`，`-state` 與存檔清冊 | 四語、四模式 240 點回歸，原版狀態與存檔相同，重啟後角色畫面相同；既有負對照有效 | 規格 005 §10 CONFORMED；整份 005 仍 READY |
| 手冊答案提示 | 引擎 `60b76b3`；四語本機答案表與字型 | 確認等鍵後，物品、法術、四語及英文、返回，三模式各 72 點，共 216 點；完整原版狀態相同 | 006 CONFORMED；手冊與答案只留本機 |
| 地牢訊息選項 | 引擎 `60b76b3`；`dungeon-options` 正常路線 | 四語四模式 512 點同狀態；全文、反白、兩個選擇、重訪、後續段落、戰鬥及色盤後顏色、兩種倍率與負對照通過 | 兩個 11 字元選項已驗證；其餘欄寬仍未量到，見 RE017、005 §14 |
| 寶箱短訊息 | 引擎 `60b76b3`；匯出工具明示納入 `mess5:61`，四語各新增一列正文 | 16 組 2496 個原版狀態點相同；八個短訊息停點共 96 個 UI PASS，40 項全文及倍率檢查、刪除正文負對照與 32 點拉桿回歸通過 | 009 CONFORMED；其他短訊息仍未量到；3 字元選項的後續驗收見 RE022、005 §18 |
| 九選項與神殿全滅 | 引擎 `60b76b3`，本機正常路線；程式、catalog、字型不變 | 四模式 1348 個原版狀態相同；264 個目標 UI PASS、146 項全文與倍率、56 項原版數字字模檢查；語言往返、返回與負對照通過 | 005 §18 的本場景已驗收；入口見 019，正常到達及收據見 [022](docs/re/022-nine-options-and-defeat.md) |
| 戰鬥死亡訊息 | 引擎 `60b76b3`；本機正常死亡路線，程式與 catalog 不變 | 四模式 888 個原版狀態點相同；兩個死亡場景四語切換、20 項全文及倍率檢查、英文視圖、回切、返回及負對照通過 | 005 §16 已驗收；全滅見 022；勝利見 021，死亡見 [020](docs/re/020-combat-death-messages.md) |
| 戰鬥勝利與獎勵 | 引擎 `60b76b3`；正常 DNG1 戰鬥、本機長路線，公開 `combat` 只修正兩個取樣數字 | 四模式 516 個原版狀態相同、387 個 UI PASS；四語全文、數值、語言往返、返回及負對照通過 | 005 §17 已驗收；全滅另見 022，勝利見 [021](docs/re/021-combat-victory.md) |
| 戰鬥直接全滅 | 引擎 `60b76b3`，本機正常 DNG4 戰鬥；原版決定消滅及不死處置 | 四模式 1096 個原版狀態相同；129 個目標 UI PASS、70 項全文與倍率；七次英文與回切、正常返回及刪除模板負對照通過 | 005 §18 的本場景已驗收；神殿分支分開記錄，見 [022](docs/re/022-nine-options-and-defeat.md) |
| 第二頁還原 | 引擎 `60b76b3`；沿用正常勝利路線，正式程式與資料不變 | 正向與只停用第二頁影子的負對照共 258 個原版狀態點相同；16 KiB 雙頁逐位元組核對、32 項獨立像素樣本及 12 項英文核對通過；16 項負對照按預期失敗 | 002 §12 的正常勝利樣本已獨立驗收，整份仍 READY，見 [023](docs/re/023-second-page-restoration.md) |
| 零魔力法術清單 | 引擎 `8d9807d`，前一基準 `60b76b3`；只修精確嚴格遮罩稽核 | 四語四模式 672 個原版狀態相同、504 個 UI PASS；32 項完整像素、20 項英文核對；負對照 12 個預期失敗；清單、切換及第二頁共 139 點回歸相同 | 010 CONFORMED；002 §13、005 §19 的正常零魔力樣本已驗收，見 [024](docs/re/024-disabled-spell-list.md)；中文變暗外觀仍是已知限制 |
| MESS 選項資料列舉 | 專案基準 `5fe2e82`，引擎維持 `8d9807d`；原版 IDA 的 DI 字元流 | 10 項解析、5 項匯出 PASS，舊程式 8 項預期失敗；獨立核對 55 個普通選項及 4 個短訊息；原版、受保護檔及路線不變 | 011 CONFORMED，限工具契約；9 個原始欄位訂正、3 個訊息恢復。另有 13 個正文或選項鍵四語缺譯及 3 個水池正文缺譯；無新增 UI 完成聲明，見 [025](docs/re/025-option-stream-parsing.md) |

## 已有

- 證據：`docs/re/001` 至 `025`（輸入清冊、probe 收據、IDA 靜態盤點、overlay 格式、視訊與文字路徑、動態收據、MESS 與 SCROLLS 格式、補充證據、`%s` 引數指標種類、位置描述文字 `OUT*.DAT`、地城位置列 `OV2:C400`、手冊來源與提示事件、存檔與冷啟動讀回、地牢事件格與訊息視窗、卷軸正常閱讀與整行安全範圍、第二條等鍵、訊息選項及拉桿後續、寶箱短訊息、第四地牢入口與戰鬥事件、死亡全文與四語切換、正常勝利及數值結算、九選項、神殿與戰鬥直接全滅、第二頁獨立還原、零魔力法術清單與精確變暗稽核、完整選項字元流）。索引在 `docs/re/README.md`。
- 規格（`docs/spec/`）：001 繪字事件與疊字核心、002 畫面操作與失效、003 catalog 與解析、004 字型與語言、005 前端與驗收、006 手冊答案提示、007 卷軸整行顯示、008 確認等鍵、009 短訊息正文、010 已知變暗格的精確稽核、011 完整選項字元流。001、003、004、006、007、008、009、010、011 已 CONFORMED，011 限工具契約。002（`load2` 正常勝利樣本已獨立驗收，見 §12；`invert2` 正常零魔力樣本已驗收，見 §13；色盤其餘分支未量到，BL=0 見 §11）與 005（兩個訊息選項見 §14，寶箱短訊息見 §15，九選項與全滅見 §18，零魔力清單見 §19，其餘分支見 §9.2）維持 READY。005 §10 的城鎮存檔與角色冷啟動讀回已 CONFORMED；§11 地牢兩行訊息與還原、§13 提示停留與確認已驗證。狀態表在 `docs/spec/README.md`。
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

- 未量到：MESS5 索引 61 以外的短訊息、其他選項欄寬與事件型別；其他地圖描述格；地城存檔及備份還原。`invert2` 正常零魔力樣本已驗收，見 [024](docs/re/024-disabled-spell-list.md)；其他變暗來源未逐一抽樣。`load2` 正常勝利樣本已獨立驗收，其他第二頁狀態不在本樣本內，見 [023](docs/re/023-second-page-restoration.md) 與 002 §12。INT 10h `AH=0Bh BL=0` 已由 [017](docs/re/017-dungeon-message-options.md) 量到，`BL=1` 及原有文字跨色盤的失效處理仍未量到。
- 已知限制：中文停用項目不重現原版變暗外觀；被原版逐格重畫的數字是粗體，其餘疊字數字是細體，字重不一致；ja、ko 的數字欄位右緣有少數 lint 警告。
- 發行字型的雙授權條款與作者聲明已核對，來源及雜湊見 `font/README.md`；散布採 OFL 1.1 或 GPLv2+ 含字型例外待使用者選定。
- 玩家名音譯（ja、ko）、同一英文在不同畫面需不同譯文：見規格未決段。
- 遠端入口：中文化 `origin/main`；dosgolem `origin/phantasie-cht-overlay`。本輪提交與推送已授權，Issue 寫入、轉公開與 Release 仍逐項授權。

完整字元流修正後，真正短訊息只剩已驗收的寶箱與 MESS7 索引 60 至 62 的三個水池。舊工具多列的五個短片段是已消費的長選項續段，不能各自翻譯。目前另有 13 個正文或選項鍵在四語 prose 缺譯。入口見 [025](docs/re/025-option-stream-parsing.md)，本機清單為 `workplace/explore-dungeon/option-parser-missing-keys.json`。水池與新增缺口尚無正常玩家路線驗收。

## 下一步

1. 沿正常路線量到三個水池及 025 的 13 個正文或選項缺譯鍵，再依規格補譯與驗收；未驗收的事件型別、地圖描述、002 操作與 005 分支沿原規格處理。
2. 發行階段：核對字型授權、打包、外洩掃描、發行前實機冒煙、Release 說明。
3. 轉公開前做公開稽核；影片與推廣視使用者決定。
