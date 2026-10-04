# 005 遊玩前端與同狀態驗收

狀態：READY（2026-10-04；驗收收據見 §9 至 §13，卷軸已通過，第二條等鍵路徑未接通；MESS 訊息內選項與其他未量到分支見 §9.2，所以維持 READY。城鎮存檔後冷啟動讀回已由 §10 驗收；原契約經四輪獨立審查，存檔擴充另經兩輪唯讀審查與修正確認）。依賴 `001` 至 `004` 與 dosgolem 規格 `250-cga-int10-scroll-and-palette`（CGA 圖形模式的 INT 10h 與 `oracle.CGAPalette()`）。證據來源：`apps/phantasie/input.go`（`KeyGate`）、`oracle`（`Run`、`SendKeys`、`TypeKeys`、`Scratch`）、dosgolem 規格 `237`（scratch 層）。

## 1. 範圍

兩個命令：互動前端 `cmd/phantasie-play`（Ebitengine 視窗，只用鍵盤），無頭收據工具 `cmd/phantasie-receipt`（路線重播、A/B 比對、稽核、畫面輸出）。路線檔格式、驗收收據格式。打包發行在另一規格。

## 2. 依據

| 事實 | 證據 | 等級 |
|---|---|---|
| 原版每次讀鍵前會先清空 BIOS 鍵盤佇列；`INT 16h AH=00h` 在 dosgolem 佇列空時回 0 不阻塞；按鍵必須在「讀鍵包裝函式入口 `img:37C2`」放進佇列才不會被清空動作吃掉 | `apps/phantasie/input.go` 註解與 `006` | 已證實 |
| 路線 `Return Return Up Return`（`KeyGate` 送鍵）在 60M 步內可重現「新成員、加入、離開城鎮」等流程；同一路線同一步數畫面雜湊相同，與 `Frame` 呼叫節奏無關 | `006`、本輪 `textlog -route` | 已證實（已測路線） |
| 單一字元鍵（字母與數字）以 `oracle.TypeKeys` 進 BIOS 佇列；有名字的鍵（`Return`、`Esc`、方向鍵、`Space`、功能鍵）以 `SendKeys` | `oracle/input.go` | 已證實 |
| 寫檔：DOS 檔案層有 `Scratch` 目錄，建立與寫入都落在該目錄，原始目錄不被修改；城鎮存檔與冷啟動角色讀回已量到 | `internal/dos/files.go` 的 `create`；規格 `237`；[013](../re/013-save-roundtrip.md) | 已證實，限城鎮路線 |
| `oracle` 的 `CGA4()` 回 320×200 色號；CGA 色彩選擇暫存器與 RGB 表目前不由 `oracle` 提供，dosgolem 規格 `250-cga-int10-scroll-and-palette` 補 `oracle.CGAPalette()` | `oracle/oracle.go`；規格 `250` | 已證實（現況） |
| 遊戲動態量到的 INT 10h 是 `AH=00h`、`AH=06h`、`AH=07h` | `002` §2 | 已證實（已測路線） |
| `KeyGate.fire` 沒有去重（`input.go:46-62`）；IRQ0 造成同一讀鍵入口二次觸發時會送兩個鍵，讀鍵計數也重複。`KeyGate.Press(after, name)` 的 `after` 是步數，不是讀鍵次數 | `apps/phantasie/input.go`；第二輪審查 N-22 | 已證實（讀碼） |
| 解壓後映像雜湊與 hook 簽章結果要寫進收據（`AGENTS.md` §5） | `AGENTS.md`；`001` §3.1 | 規則 |

## 3. 互動前端 `cmd/phantasie-play`

旗標：`-root`（原版目錄，唯讀）、`-state`（可寫狀態目錄，預設 `$XDG_DATA_HOME/phantasie-cht`，`Scratch` 指向其下；存檔留在這裡，不寫原版目錄）、`-lang`（預設 zh-TW）、`-text`（`text/` 目錄）、`-font`（字型目錄）、`-zoom`（1 或 2，視窗為 640×400 的倍數）、`-ips`（每秒執行的指令數，預設值由實測決定）。

執行迴圈（Ebitengine 的 `Update`，每秒 60 次）：

1. 執行 `ips / 60` 道指令（可被 `-ips` 調整；呼叫 `RunUntil` 或 `Run`）。步數預算可能在事件的 A 與 B 之間結束，不需要續跑到 B：疊字層在 B 才提交（`001` §7），A 到 B 之間舊疊字繼續遮住，不會閃現英文。
2. `Layer.Frame(indexed, rgb)`，接著 `recolor`（`001` §8）：`indexed = oracle.CGA4()`，`rgb` 依目前調色盤（`002` §6）換算。
3. 組合 640×400 的 RGBA：色號畫面逐點放大 2 倍，`Layer.Draw(dst, 2, missing)`；顯示語言為 `en` 時略過 `Draw`。
4. 交給 Ebitengine 顯示，視窗倍率 `-zoom` 以最近鄰縮放。

輸入：

- 鍵盤事件轉成原版按鍵：有名字的鍵（Enter 為 `Return`、`Esc`、方向鍵、`Space`、`Backspace`、`Tab`）與功能鍵送 `SendKeys` 同名；可列印字元（`ebiten.AppendInputChars`）送 `TypeKeys`。
- 一律經 `KeyGate.Press`：按鍵排入佇列，於原版下一次讀鍵入口放進 BIOS 佇列（與無頭路線同一路徑）。佇列最多 16 筆，滿了丟棄最新的，避免長按累積。
- 保留鍵（不送原版）：`F11` 全螢幕切換、`F12` 依序切換語言（zh-TW、zh-CN、en、ja、ko 中已啟用者）。本遊戲是否使用 `F11`、`F12`：待靜態確認（掃描碼 `57h`、`58h` 不應出現在程式碼的鍵盤判斷）。語言切換依 `004` §5（事件中途延到 B 之後）。

沒有滑鼠與搖桿：忽略。沒有音訊：原版的 PC 喇叭輸出以 dosgolem 目前行為處理（不發聲）。

視窗標題：`幽靈戰士（Phantasie）繁體中文化`；語言切換時顯示語言名稱 1 秒（疊在視窗標題，不畫進遊戲畫面）。

## 4. 路線檔

`tests/routes/<名稱>.route`，UTF-8 文字，一行一個項目，`#` 開頭是註解：

| 項目 | 意義 |
|---|---|
| `Return`、`Esc`、`Up`、…、`A`、`1` | 送出一個按鍵（經 `KeyGate`，每次讀鍵入口送一個） |
| `@wait <N>` | 等原版**再讀鍵 N 次**（讀鍵入口次數，不是步數）後才送下一個鍵（用於需要等動畫的畫面；預設 0）。需要新的閘門機制 `KeyGate.PressAfterReads(n, name)`（§8） |
| `@check <名稱>` | 在原版第 K 次讀鍵入口（K 為該行之前已送出的鍵數加 1）停下，輸出收據（§5） |
| `@snap <名稱> <N>` | 所有排入的鍵都送出後，再執行 **N 步**並擷取，輸出收據（§5）。用於原版沒有讀鍵入口的畫面（戰鬥回合結算：命中、傷害、治療等訊息）。N 相對於目前位置，連續的 `@snap` 逐段累加。不等在途事件結束：步數只由路線決定，`-hooks none`、`-overlay off`、`-overlay on` 的 `steps` 才可比對（§5.1）；擷取點可能落在事件的 A 與 B 之間，稽核對在途事件的矩形略過。名稱與 `@check` 共用同一個名稱空間 |
| `@lang <語言>` | 切換顯示語言（需要 `-extra-lang` 或路線用到的語言自動載入；`004` §5、§7） |
| `@assert-visible-same <A> <B>`、`@assert-same-screen <A> <B>` | 兩個先前出現的檢查點的可見格集合（前者）或畫面與疊字內容（後者，`vram_hash` 與 `content_hash`）必須相同（`004` §7 第 3 項） |
| `@expect <key>` | 緊接在 `@check` 或 `@snap` 之後，可多行：該檢查點畫面上**必須已有疊字**的 catalog 鍵（`ui` 的英文鍵或 `prose` 的 `h:` 摘要鍵）。收據比對實際疊字鍵集合，缺少者為失敗 |
| `@known-untranslated <key>` | 緊接在 `@check` 或 `@snap` 之後，可多行：該檢查點允許未譯的鍵（已知缺口，附 Issue 編號作註解）；收據的 `untranslated` 與 `untranslated_args` 鍵集合超出此清單者為失敗 |

`@snap` 的覆蓋門檻（§5）：沒有 `@expect` 的 `@snap` 不要求 `stamps` 至少為 1（擷取點可能落在沒有文字的畫面，例如戰鬥動畫），它的價值在於累計的未譯鍵集合與每個 `Frame` 取樣的稽核涵蓋整個回合；有 `@expect` 者照一般檢查點處理。

可進版控的路線不含手冊答案（`AGENTS.md` §1）。[006-manual-answer-hints.md](006-manual-answer-hints.md) 的手冊作答驗證路線只留本機。`@expect`、`@known-untranslated` 的公開鍵只列 UI 字串與摘要鍵，不列玩家輸入。

## 5. 無頭收據工具 `cmd/phantasie-receipt`

輸入：`-root`、`-route`、`-lang`（可重複）、`-overlay on|off`（`off`：維護 `Layer` 但不呼叫 `Draw`，等同顯示語言 `en`）、`-hooks none`（完全不掛 hook，供唯讀證明）、`-fault <名稱>`（僅測試用的故障注入，§5.1）、`-frame-every <步數>`（無頭模式在 `@check` 以外的 `Frame` 間隔，預設與前端每幀步數相同）、`-out`。

每個 `@check` 輸出一列收據（TSV）：

| 欄 | 內容 |
|---|---|
| `check` | 檢查點名稱 |
| `image_hash`、`img_seg` | 解壓後映像雜湊與載入段（`001` §3.1：重定位後的位元組依載入段而變，同載入段的兩次執行才可比較；每次執行一個值，每列重複） |
| `hook_sig` | hook 簽章檢查結果（`ok` 或失敗的掛點名稱）；非 `ok` 時工具以非零離開，不產生其餘欄位 |
| `font_hash` | 快取的 `FONT` 2,032 bytes 雜湊（`001` §8） |
| `steps` | 原版已執行的指令數 |
| `reads` | 原版讀鍵入口累計次數 |
| `vram_hash` | `B800:0000` 起 `4000h` bytes 的 FNV-1a 64 |
| `mem_hash` | 映像段起至 `DGROUP` 末端（`2E4E:FFFF` 範圍）的雜湊 |
| `stamps` | `Layer` 疊字數 |
| `layer_hash` | 疊字集合（`Key`、位置、`Text`、`State`、`FG`、`BG`、`Transparent`）的雜湊（含顏色與透明格，使整列反色與透明格遺失會改變雜湊） |
| `keys` | 實際疊字鍵集合（`@expect` 比對用）：目前 `Layer` 內各事件組的 `hits[ID]`（`Result.Hits`，`001` §5、§7）的聯集，含字面鍵、模板鍵、各 `%s` 引數鍵與 `prose` 摘要鍵 |
| `untranslated`、`untranslated_args` | 該檢查點之前累計的未譯鍵集合（不含玩家輸入；`001` §9） |
| `counters` | `001` §9 的全部計數器（`unpaired` 必須為 0；`composed_miss_*`、`arg_unclassified`、`straddle`、`recolor_fallback`、`rebuild_lost`、`shadow_lost` 列出） |
| `stale_cells`、`exposed_events` | 稽核結果（§5.1），必須為 0 或在已知清單內 |
| `png` | 2 倍畫面的 PNG 檔名（`-out` 下，`<route>.<check>.<lang>.png`） |

### 5.1 同狀態 A/B 與稽核

**hook 唯讀證明**：同一路線、同一 `-frame-every`，三種執行模式各跑一次：`-hooks none`（完全不掛 hook）、`-overlay off`（掛全部 hook、維護 `Layer`，但不呼叫 `Draw`；等同顯示語言 `en`）、`-overlay on`（預設）。每個檢查點的 `steps`、`reads`、`vram_hash`、`mem_hash` 必須相同。這證明 hook 沒有改機器。`on` 與 `off` 的 2 倍畫面在疊字矩形以外逐點相同只是回歸護欄（`Layer.Draw` 只改疊字矩形內像素，所以由構造保證），**不是位置或內容正確的證據**；位置由 `001` §10.3 的位置 oracle 判定，內容與殘字由下列稽核判定。

**獨立稽核**（以原版 `FONT` 位元圖與目前視訊記憶體為基準，不使用疊字層自己的狀態當期望值）。稽核有自己的**事件日誌**：每個 T 類且在提交時 `Resolve` 回 `OK` 的事件，記 `(ID, Col, Row, Text, 提交的 Step)`，上限 4096 筆、與 `records` 的清理無關（`records` 只保留被 `Layer` 或影子引用者；疊字被指紋偵測、`Clear` 移除的事件正是最先被清掉的，稽核不能依賴它）。遮罩一致檢查共用 `001` §8 的 `maskScan`（像素粒度，只計非透明格範圍內的像素）；全是空白字元的格要求該格同一色號像素不少於 85%（不是恆通過）；其他格用 `cellConsistent`。

1. **殘字稽核**（`stale_cells`）：對每一個 `Shown` 疊字的每個非透明格，取其對應的原版格（事件組的實際列取疊字的 `Y`，不用 `Row×8`，否則捲動後的疊字會被判成殘字），檢查畫面是否仍是該原文的字模畫出的結果：`cellConsistent`（`001` §8：配對率不低於 70%，墨像素保留率不低於 50%；各原版格的反白狀態逐格判定，反白格以對調後的 (底, 墨) 計，所以事件只有一部分被反白時未反白的格不是殘字）。不成立者計為殘字格（疊字蓋在已不是原文的畫面上）。
2. **英文外露稽核**（`exposed_events`）：對事件日誌內的每個事件，若其事件矩形目前仍顯示該原文（同上的遮罩一致檢查，且該矩形沒有被反白以外的操作改動），則 `Layer` 內必須有覆蓋該矩形全部可見像素的疊字；缺少者計為英文外露事件。
3. 兩項稽核每個 `@check` 執行一次，另在無頭模式每個 `Frame` 抽樣。**抽樣略過開啟中事件（A 已觸發、B 未觸發）的矩形**：A 與 B 之間畫面被半寫，舊疊字的字模檢查必然不成立，不是缺陷。結果必須為 0；不為 0 的鍵列入 `@known-untranslated` 同風格的已知清單並附原因，否則失敗。
4. 稽核本身要有負對照，以**故障注入**旗標（`-fault`，僅測試用）達成，不用 `-overlay off`（`off` 仍維護 `Layer`，`exposed_events` 為 0）：`-fault noadd`（提交時不 `Add` 疊字）時 `exposed_events` 必須大於 0；`-fault noclear`（不對未譯事件與 K、N 類 `Clear`）加後續覆寫時 `stale_cells` 必須大於 0；把一個 `Shown` 疊字故意留在被改寫的畫面上，`stale_cells` 必須大於 0。

**`Frame` 節奏**：換 `-frame-every` 重跑（例如 20,000 步與每次讀鍵入口兩種）：`vram_hash`、`mem_hash` 必須相同；`layer_hash` 與畫面在檢查點若不同，視為**失敗**，除非該檢查點列在 `tests/routes/known-frame-sensitive.tsv`（附原因與 Issue 編號）。殘字缺陷會呈現為節奏敏感，所以不允許只「說明原因」。

**檢查點在讀鍵入口**：收據只看得到原版等鍵時的穩態；事件中途的暫態（`001` §7 的 A 到 B）由「`Frame` 抽樣稽核」與 `001` §10 的單元測試涵蓋。

**覆蓋門檻**：每個 `@check` 的 `stamps` 必須至少為 1（疊字數為 0 時 A/B 空洞成立，不得算通過），且 `@expect` 鍵集合的每個鍵都在 `keys` 內。

擷取畫面前（PNG 與疊字比較）先呼叫一次 `Layer.Frame` 與 `recolor`，使 `Pending` 疊字進入 `Shown`（`002` §8）。RGB 依 `oracle.CGAPalette()`。hook 簽章檢查（`001` §3.1）不通過時工具以非零離開並印診斷，不產生收據。

缺原版檔時整個工具 SKIP 並印出原因，不算驗收。

## 6. 驗收路線與覆蓋

必備路線（各自有 `@check` 與 `@expect`，每個語言各一組收據）：

1. 標題選單（四個項目的畫面）。
2. 城鎮：選單列（含第 7 項「公會」）、`PELNOR` 狀態列（城鎮名走 `town` 種類查 `ui`，不是英文）、選單反白移動。
3. 公會：選單、反白、`New member`（種族、職業、屬性畫面、`KEEP`／`PURGE`、`INPUT NAME`，含輸入字母的部分覆蓋）、`Add member`、`Inspect`（清單）、關閉選單。
4. 離開城鎮到地圖。
5. 銀行、神祕、武器店、旅店各一個畫面。
6. 地牢：進入、訊息視窗（MESS）、選項視窗、戰鬥的訊息（`%s HITS` 等組句，怪物名走 `monster` 種類）與選單、戰鬥指令列（`sprintf` 加 `strcat` 的組句）、法術列表。
7. 卷軸閱讀（SCROLLS，標題置中）。
8. 存檔與讀檔，讀檔後畫面無殘字。
9. 選項選單：切換音效開關符號兩次（P 類修補）。
10. 語言切換（`004` §7 第 3 項的三例）。

到不了的畫面照實記錄原因與條件，不修改存檔或記憶體跳關（`AGENTS.md` §4）。覆蓋收據列出每條路線經過的文字事件鍵集合與未譯鍵（資料型引數只記 `(呼叫端, 引數序, 種類)`，`003` §5.1）。

## 7. 未決

1. `-ips` 的預設值與原版計時行為（PIT、延遲迴圈）：以實測決定；若原版以指令計數做延遲，需檢查過快是否使動畫無法觀看。
2. 地城存檔與備份還原的實際行為仍待量測；城鎮存檔與角色冷啟動讀回見 §10，已通過。
3. 地牢、戰鬥、商店等路線的按鍵序列與可重現性（隨機數是否固定）。
4. `F11`、`F12` 是否與原版衝突。
5. 稽核的遮罩一致檢查對「被變暗（`invert2`）的列」是否需要放寬（動態未量到變暗，`002` §9）。

## 8. 實作會改變的既有程式

| 位置 | 更動 |
|---|---|
| `apps/phantasie/input.go` `KeyGate.fire`、讀鍵計數 | 重複觸發去重（開啟旗標加 `SP`，同 `001` §3.2）；新增 `PressAfterReads(n, name)`（以讀鍵入口次數為準的閘門），`@wait` 使用 |
| `apps/phantasie/cmd/textlog` | 供收據工具重用的路線重播與計數輸出（見 `001` §11） |
| `oracle` | `CGAPalette()` 與 `CGA4RGB()`（色號畫面換算成 RGB，前端與收據共用，dosgolem 規格 `250-cga-int10-scroll-and-palette` §4） |

## 9. 驗收收據（2026-10-04）

本節的既有收據環境同 `001` §13.1（引擎 commit `e2513a6`、專案 commit `a0704f5（本節加入前的 HEAD）`）。本規格維持 READY：MESS 訊息內選項與其他分支未量到；卷軸見 §12。地牢兩行 MESS 與還原見 §11（見 §9.2 的原因與條件）；其餘分支補上或證明到不了後再升 CONFORMED。既有 16 條路線共 359 個檢查點，zh-TW 全部 PASS；後續存讀檔的兩條路線與收據見 §10。

### 9.1 工具與前端

| 項 | 收據 | 結果 |
|---|---|---|
| 無頭收據工具 | `tools/run_receipt.sh` 對 16 條路線、4 個語言（zh-TW 全部；zh-CN、ja、ko 對 13 條非語言切換路線）輸出 TSV 與 PNG；欄位如 §5 表；缺原版時 SKIP | 通過 |
| 同狀態 A/B 與 `Frame` 節奏 | `tools/ab_receipt.sh` 對 16 條路線全部 PASS（`001` §13.2 第 2 項）；沒有節奏敏感的檢查點，不需要 `known-frame-sensitive.tsv` | 通過 |
| 稽核與負對照 | `stale_cells`、`exposed_events`、`mask_strict`、`pos_bad` 全部路線為 0；故障注入四種（`noadd`、`noclear`、`nostrcat`、`verify-early`）各自使稽核或簽章檢查失敗（`001` §13.2 第 5 項） | 通過 |
| 覆蓋門檻 | 每個 `@check` 的 `stamps` 至少為 1、`@expect` 鍵都在 `keys` 內；沒有 `@expect` 的 `@snap` 不要求 `stamps`（§4） | 通過 |
| 互動前端單元與整合測試 | `TestSessionSmoke`、`TestSessionRealFontRecolor`、`TestSessionKeyGate`（需要原版，以 `DOSGOLEM_TEST_ROOT` 與 `/phantasie-data` 掛載實際執行）PASS | 通過 |
| 互動前端實機冒煙 | `tools/build_play.sh` 在 Docker 內建出 `phantasie-play`；`tools/smoke_play.sh` 在 Xvfb 內對 zh-TW、zh-CN、en、ja、ko 各啟動一次並截圖，目視確認標題畫面三個選單項與底部提示為各語言譯文（en 為原版英文），沒有缺字 | 通過 |

### 9.2 §6 驗收路線

| 項 | 路線 | 結果 |
|---|---|---|
| 1 標題選單 | `title`、`title-items`（標題選單、工具選單與提示） | 通過 |
| 2 城鎮 | `town`（36 個檢查點：選單列含公會、`PELNOR` 狀態列、選單反白移動） | 通過 |
| 3 公會 | `guild`（81 個檢查點：選單、反白、`New member` 全流程含輸入名字、`Add member`、`Inspect`、關閉；確認等鍵回歸見 008） | 通過 |
| 4 離開城鎮到地圖 | `map`（17 個檢查點：頂端選單、選項、檢視面板、隊員清單、角色頁、法術列表、施放法術、使用藥水、速度選單、旅店與城鎮進入提示） | 通過 |
| 5 銀行、神祕、武器店、旅店 | `shops`（46）、`messages`（42）、`inn-distribute`（8）、`town-timed`（53，包含神祕客的訊息視窗與現金為 0 的購買；確認等鍵回歸見 008） | 通過 |
| 6 地牢 | `dungeon`（10：進入提示、位置列、選項視窗）；`combat`（33：戰鬥選單列、指令列、法術列表、施法對象，加 14 個 `@snap` 涵蓋整個戰鬥回合的命中與治療等訊息，怪物名走 `monster` 種類） | 部分通過；**未量到**：MESS 訊息內選項與其他事件型別（兩行訊息及還原已由 §11 驗收）、戰鬥勝利與死亡訊息。OUT1 道路格的顯示、停留與確認見 §13 及 008；多回合戰鬥的手冊提示見下 |
| 7 卷軸閱讀 | `scroll-read`（31 點） | 通過；正常提領、購買、使用與返回，確認等鍵後四語 496 點同狀態；標題置中與整行顯示見 007、§12 |
| 8 存檔與讀檔 | `save-load`（讀入原版目錄的全零 `DNG.SAV` 進城鎮、存檔兩次、存檔後開關選單）；`save-roundtrip-write`、`save-roundtrip-read`（存檔落地、冷啟動讀回角色） | 通過，限城鎮正常路線；四語、三模式及 Frame 節奏見 §10 |
| 9 選項選單音效符號 | `lang-options`、`map`（`+音效` 與 `-音效` 往返） | 通過 |
| 10 語言切換 | `lang-switch`、`lang-name`、`lang-options`（`004` §9 第 3 項） | 通過 |

其餘到不了的畫面（原因與條件）：無隊員進旅店、武器店、神祕客、銀行提款按 Return 後約 101 萬步沒有讀鍵，`@snap` 在 3,000 至 300,000 步都只有城鎮選單列，沒有任何訊息文字；現金為 0 的購買在既有停點只有空的訊息視窗，原版（`-overlay off`）同一時刻也是空視窗。這些抽樣不能排除更晚的短暫訊息。公會重名提示的顯示、重試及清除已由 §13 驗證。Options 的「顯示隊伍」「列印」按 Return 後畫面不變；新角色的「裝備、藥水、技能」沒有畫面。

手冊對照提示：依使用者後續授權，已由 [006 手冊答案提示](006-manual-answer-hints.md) 接通物品與法術題，正常路線收據另存本機。`tests/routes/` 的公開路線仍不含答案；缺少本機提示或事件不符時維持原文，收據工具在 `protected` 計數大於 0 時判 FAIL。取得授權前停止該分支的紀錄保留在 `WORKLOG.md`。

## 10. 存檔層收據擴充

擴充狀態：CONFORMED（2026-10-04）。已經契約對程式、資料對證據兩輪唯讀審查、實作審查與正式收據獨立核對，阻擋及應改皆清除。補入硬連結、全部語言預檢、有效 UTF-8、清冊模式名稱與輸出目錄隔離。既有 §1 至 §9 的 READY 契約保持有效。動態依據：[013 存檔與冷啟動讀回](../re/013-save-roundtrip.md)。

### 10.1 輸入與隔離

- 收據工具新增可選 `-state <目錄>`。空字串保持原本不落地寫檔的行為。非空時每個 `-lang` 使用 `<目錄>/<語言>` 作為 `Scratch`，在執行啟動鏈前設定。重複執行使用同一語言目錄即可讀回上一條路線的正常存檔，不自動清空、複製或改寫存檔。
- 初始語言僅接受 zh-TW、zh-CN、ja、ko；不接受帶路徑分隔符的任意名稱。同一次命令重複的語言拒絕，避免第二次消費第一次改動的狀態。`@lang` 只切顯示，不更換存檔目錄。
- 存檔層與原版目錄不得相同、互相包含，包含符號連結解析後的路徑。先解析現有祖先再建立目錄；各語言 Scratch 葉目錄拒絕符號連結、子目錄、非一般檔案及硬連結檔案。基底目錄允許各語言子目錄。全部初始語言先完成路徑與檔案檢查，才啟動第一組；錯誤時非零離開，不啟動原版。
- 使用存檔層時，`-out` 與原版目錄不得相同或互相包含；`-out` 不得位於任何 Scratch 葉目錄內或與其相同。解析符號連結後檢查，避免收據 TSV、JSON 與 PNG 自己進入存檔摘要。`-out` 可為 Scratch 的祖先，例如各模式輸出目錄下另放存檔子目錄。
- `-hooks none`、`-overlay off`、`-overlay on` 都以相同方式設定存檔層。三種模式與各語言的驗收用不同空目錄，各自在自己的目錄執行存檔及重啟，禁止串用其他模式產生的存檔作基準。
- 原版唯讀掛載、dosgolem 規格 237 的檔案層不變。新增的觀察只讀存檔，不修改原版記憶體、VRAM、規則、判定或原始檔案。

### 10.2 收據

- TSV 末端追加 `state_in_hash`、`state_hash`，既有欄位位置不變。不使用存檔層時兩欄為 `-`。前者是啟動前的目錄摘要，每列重複；後者是該檢查點實際落地檔案的摘要。空目錄須有可比對的 SHA-256，不用 `-` 代替。
- 目錄摘要只含一般檔案，依檔名位元組順序排列。摘要輸入為每檔的檔名字串、長度及檔案內容 SHA-256；以三欄 TSV 編碼，檔名含控制字元、反斜線或無效 UTF-8 時拒絕。長度為十進位數字，SHA-256 為小寫十六進位，每筆以換行結尾。忽略主機目錄路徑、mtime、UID、GID。所有檔案讀取錯誤均為失敗。
- `<route>.<lang>.<overlay>-<hooks>.state.json` 保存啟動前與每個檢查點的檔名、長度、SHA-256 清冊。清冊與檔案位元組皆由獨立腳本核對，不只相信工具輸出的摘要。
- 只有檔案落地、重新啟動實際讀回與人物畫面恢復都通過，才算存讀檔驗收。只有按存檔後畫面不變，不算讀回驗收。

### 10.3 驗收與影響

1. 將原本 `save-load` 路線保留，另建 `save-roundtrip-write`、`save-roundtrip-read` 公開路線，皆只有正常按鍵、`@check` 與 `@expect`，不包含原版存檔資料。第一條在存檔後進公會檢視角色；第二條從冷啟動標題選繼續，再檢視同一角色。
2. 四語皆跑 write 後 close、read 冷啟動；兩段各跑 none、off、on 及不同 Frame 節奏。逐點 steps、reads、VRAM、映像範圍、完整 1 MiB 雜湊及存檔摘要相同；on 的節奏改變後 Layer 雜湊相同。同一階段各模式及語言的初始 state 摘要須相同。
3. 重啟讀回前後角色的原版畫面與覆繪內容相同，以 VRAM、`content_hash` 與實際 PNG 比對；不跨兩個生命週期比較含事件 ID 的 `layer_hash`。獨立核對清冊與實際落地存檔，write 結束與 read 開始的檔案摘要相同。正常檢視畫面必須有角色資料，不以相同空城鎮畫面代替。
4. 單元測試：不同絕對路徑的同內容、空目錄、改一位元組、不同檔名、無效 UTF-8、符號連結、硬連結、原版目錄重疊及收據目錄污染。錯誤不啟動原版；缺少原版時仍明確 SKIP。一次停用 SetScratch 的乾淨匯出負對照須使存讀檔驗收失敗。
5. 既有無 `-state` 路線的 A/B 行為與欄位不變；抽測 `title`、`save-load`。變動限 `cmd/phantasie-receipt` 與新路線，不改互動前端或通用 DOS 層。

本節的 CONFORMED 只表示城鎮存檔與正常角色讀回。§6 的卷軸已由 §12 獨立驗收，其他未量到項目仍獨立處理；MESS 兩行段落及還原見 §11，不因本節通過而直接提升整份規格。

### 10.4 驗收收據

引擎提交 `f046ec4`，Go 1.24.13 linux/amd64。重播與獨立核對工具為 `tools/save_roundtrip.py`，正式產物在 `workplace/receipts/save-roundtrip/`，精確來源與產物雜湊在 `workplace/receipts/save-roundtrip-verification.json`。

| 閘門 | 證據 | 結果 |
|---|---|---|
| 存檔落地與冷啟動 | 四語各在 none、off、on、on-f2 獨立存檔後重啟，共 16 組、240 點。none 的 UI 明確 SKIP，只提供原版狀態基準；其餘 UI 皆 PASS | 通過 |
| 原版狀態與 Frame 節奏 | 每點 steps、reads、VRAM、映像範圍、完整 1 MiB、初始與當前存檔摘要跨模式及語言相同；20,000 與 40,000 步的 Layer 雜湊相同 | 通過 |
| 實際檔案與角色畫面 | 清冊重新計算摘要並核對磁碟位元組；write 結束與 read 開始相同。原始名冊沒有 Alice，各組落地名冊都有 Alice；重啟前後 VRAM、content_hash、PNG 相同 | 通過 |
| 位置與稽核 | 正式收據的 pos_bad、stale_cells、exposed_events、mask_strict 皆為 0；期望鍵全部存在，未譯僅原選項分隔線 | 通過 |
| 單元與拒絕條件 | `go test -count=1 ./apps/phantasie ./apps/phantasie/cmd/phantasie-receipt`；存檔測試涵蓋檔名、內容、連結、目錄、語言及輸出隔離 | 通過 |
| 存檔負對照 | 乾淨匯出恰好停用一處 `SetScratch`，驗收以「沒有落地存檔」失敗；紀錄 `workplace/receipts/save-roundtrip-negative.log` | 通過 |
| 無存檔層回歸 | `title` 1 點、`save-load` 8 點，各跑 none、off、on、on-f2；原版狀態相同，on 的 Layer 相同，新增兩欄皆為 `-`，沒有清冊檔 | 通過 |
| 平台編譯 | Linux amd64 建置；Windows amd64、macOS arm64 交叉編譯。後兩者尚未實機執行，不作平台驗收 | 通過，限編譯 |

實作期間的處置：實作審查發現未提供 `-state` 時跳過語言預檢，已移至早退之前，補兩個反例並重跑測試。原始 70 個輸入檔雜湊不變；沒有把探針第一版誤選選單的結果當成讀回證據。

## 11. 地牢 MESS 兩行段落與還原收據

日期：2026-10-04。現有 READY 契約的正常路線抽樣，沒有改動正式引擎。觸發資料流、輸入雜湊、工具版本與證據等級見 [014](../re/014-dungeon-message-trigger.md)。

`tests/routes/dungeon-message.route` 從原版啟動及建立角色開始，以正常方向鍵進入 DNG1 的事件格。兩行段落以 `@snap gate-visible 120000` 擷取，逐一要求 `h:2a4079d1ee67` 與 `h:5c119d163b05`。接著 `@check gate-wait` 驗證同兩行在確認停點，送 Return 後以 `@snap gate-cleared 60000` 核對原版整頁還原，沒有段落疊字。路線於手冊題出現前結束，不含作答。確認等鍵後路線為 21 點，zh-TW 回歸 PASS，見 008。

引擎 `f046ec4`、專案基底 `11b82a8`。四語各跑 none、off、on、on-f2，共 320 點。steps、reads、VRAM、映像範圍與完整 1 MiB 記憶體雜湊跨模式及語言相同；20,000 與 40,000 步取樣的 Layer 雜湊相同。none 的 UI 是 SKIP，僅供原版狀態基準；其餘判定全部 PASS。段落鍵存在，還原後 `keys` 空白且 `stamps=0`，殘字、外露、遮罩及位置稽核無錯誤。

正式收據與清冊位於 `workplace/explore-dungeon/ab-message-v2/`。`-fault noadd` 負對照使訊息停點因三個外露事件而失敗。繁中、日文、韓文的 2 倍訊息與還原畫面已目視核對；本次未另驗 1 倍合成。

本次僅證明兩行段落與還原，訊息內選項、短訊息與其他事件型別仍未量到。卷軸閱讀已由 §12 驗收；MESS 訊息內選項與其他未量到分支仍保留，所以整份規格維持 READY。

## 12. 卷軸閱讀與返回

依 [007 卷軸整行顯示](007-scroll-row-layout.md) 修復空白標記、短來源截斷與標題置中，該規格已 CONFORMED。引擎 `277bb98`，公開正常路線 `scroll-read`，四語 none/off/on/on-f2 共 480 點；原版完整記憶體、VRAM、步數與讀鍵相同，兩種 Frame 節奏的 Layer 相同，掛鉤模式 UI 全 PASS，原版基準只作狀態比較。

銀行提領後可以正常在武器店購買卷軸 8，再由城鎮「使用物品」閱讀；「拿不到卷軸」的舊結論已由正常路線否定。n 返回後原版 VRAM、可見格與覆繪內容均等於閱讀前；卷軸內四語與英文切換後返回繁中亦相同。獨立核對 13 行全文及 1 倍、2 倍像素範圍，空白行不印標記，標題置中。來源見 [015](../re/015-scroll-reading.md)，完整收據與負對照見 007。

修復後另重跑既有四語城鎮存讀檔的 240 點，全部狀態與存檔比較通過。後續 008 接通確認等鍵，卷軸路線加明示購買確認，四語四模式共 496 點再次通過，同時重跑 240 點存讀檔。範圍限正常卷軸 8、城鎮存檔與既有覆蓋；其餘未量到分支照 §9.2 保留，不因新路線通過而宣稱全遊戲完成。

## 13. 道路描述與公會重名提示

### 13.1 範圍與證據

沿用現有 READY 契約補顯示驗收，未修改引擎、譯文、字型、原版記憶體或資料。引擎 `277bb98`，Go 1.24.13、Python 3.13，四語使用既有 catalog 及發行字型。

- `map-description`：正常建立四人隊伍，離城後從 `(14,15)` 向西一步，觸發 OUT1 `(13,15)` 的兩行道路描述。來源與位址見 [RE010](../re/010-map-description-text.md#正常觸發與顯示驗收)。
- `guild-duplicate`：正常建立 Alice，再輸入同名，擷取重名提示，重試 Bob，返回公會。來源與位址見 [RE008 §10](../re/008-text-and-screen-supplement.md#10-公會重名與第二條等鍵路徑)。

本節先前的引擎 `277bb98` 會使兩種提示立即返回，所以當時以已量到的繪字完成後一步擷取。現行 `60b76b3` 的正常確認停點驗收見 §13.4。公開路線不含手冊答案、原版資料或玩家狀態注入。

### 13.2 同狀態收據

正式輸出在 `workplace/explore-main/ab-ui-windows/`。每條路線各有四語 × none/off/on/on-f2 共 16 組；`summary.json` 保存原版 70 檔、路線、工具、catalog 與字型雜湊。

| 閘門 | 結果 |
|---|---|
| 描述 7 點、重名 9 點 | 共 256 點，192 個覆繪 UI PASS；64 個 none UI SKIP 僅作原版狀態基準 |
| 原版狀態 | 每點 steps、reads、VRAM、映像範圍與完整 1 MiB 記憶體均跨模式及語言相同 |
| Frame 節奏 | 20,000 與 40,000 步的 Layer 雜湊每點相同 |
| 位置與稽核 | 目標期望鍵存在；位置、殘字、外露與遮罩稽核零錯誤 |
| 返回 | 描述清除後沒有段落鍵；重名重試後沒有提示鍵，重新命名後公會 VRAM 與覆繪內容等於第一次建立後 |

### 13.3 獨立內容與負對照

`workplace/explore-main/window_visual.go` 由 catalog 與字型寬度獨立計算全文、置中及補白，不呼叫 `layoutLine`；兩行描述與一行重名提示在四語都為 Shown，原始 Text、Cells 與引數未變。1 倍與 2 倍的目標像素差異皆限制在原版文字矩形，沒有缺字。結果在 `ui-window-visual.log`；1 倍的驗證限合成與範圍，不宣稱閱讀品質。

本機暫存副本分別刪除道路第二行、重名提示譯文，正式路線均在目標點 FAIL。負對照輸出在 `negative-map-description/`、`negative-guild-duplicate/`，未改正式 catalog。

### 13.4 互動停留與確認返回

原版 `37A0` 先清鍵，再以 `INT 16h AH=00h` 讀一鍵並丟棄回傳值。引擎 `60b76b3` 依 [008 確認等鍵](008-discarded-key-wait.md) 在清鍵後的 `37B8` 停下；沒有玩家按鍵就不推進原版指令。完整 bytes、SP 與正常路線見 [RE016](../re/016-discarded-key-wait.md)。先前立即返回的缺陷及短暫顯示驗收歷史保留在 `WORKLOG.md`。

兩條正常路線改成 `@check` 停留並明示 Return，四語四模式共 192 點，原版完整狀態相同，144 個覆繪 UI PASS，48 個 none UI SKIP 僅作基準。兩種提示各四語的 120 次 Run／Frame 保持原版狀態與計數不變；語言切換返回同圖層，確認只消耗一鍵，再走原版清除。獨立全文與兩種倍率的像素範圍通過；Xvfb 實際按鍵完成停留、F12、重新命名及返回。

本節的顯示及互動已驗證；整份 005 仍因 §9.2 的其他未量到分支維持 READY。正式收據及負對照入口見 008。
