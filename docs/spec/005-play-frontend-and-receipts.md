# 005 遊玩前端與同狀態驗收

狀態：DRAFT 第三版（2026-10-03，依第二輪四份審查意見修訂）。依賴 `001` 至 `004` 與 dosgolem 規格 `250-cga-int10-scroll-and-palette`（CGA 圖形模式的 INT 10h 與 `oracle.CGAPalette()`）。證據來源：`apps/phantasie/input.go`（`KeyGate`）、`oracle`（`Run`、`SendKeys`、`TypeKeys`、`Scratch`）、dosgolem 規格 `237`（scratch 層）。

## 1. 範圍

兩個命令：互動前端 `cmd/phantasie-play`（Ebitengine 視窗，只用鍵盤），無頭收據工具 `cmd/phantasie-receipt`（路線重播、A/B 比對、稽核、畫面輸出）。路線檔格式、驗收收據格式。打包發行在另一規格。

## 2. 依據

| 事實 | 證據 | 等級 |
|---|---|---|
| 原版每次讀鍵前會先清空 BIOS 鍵盤佇列；`INT 16h AH=00h` 在 dosgolem 佇列空時回 0 不阻塞；按鍵必須在「讀鍵包裝函式入口 `img:37C2`」放進佇列才不會被清空動作吃掉 | `apps/phantasie/input.go` 註解與 `006` | 已證實 |
| 路線 `Return Return Up Return`（`KeyGate` 送鍵）在 60M 步內可重現「新成員、加入、離開城鎮」等流程；同一路線同一步數畫面雜湊相同，與 `Frame` 呼叫節奏無關 | `006`、本輪 `textlog -route` | 已證實（已測路線） |
| 單一字元鍵（字母與數字）以 `oracle.TypeKeys` 進 BIOS 佇列；有名字的鍵（`Return`、`Esc`、方向鍵、`Space`、功能鍵）以 `SendKeys` | `oracle/input.go` | 已證實 |
| 寫檔：DOS 檔案層有 `Scratch` 目錄，建立與寫入都落在該目錄，原始目錄不被修改 | `internal/dos/files.go` 的 `create`；規格 `237` | 已證實（讀碼）；與本遊戲存檔流程的對應待量測 |
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
| `@expect <key>` | 緊接在 `@check` 之後，可多行：該檢查點畫面上**必須已有疊字**的 catalog 鍵（`ui` 的英文鍵或 `prose` 的 `h:` 摘要鍵）。收據比對實際疊字鍵集合，缺少者為失敗 |
| `@known-untranslated <key>` | 緊接在 `@check` 之後，可多行：該檢查點允許未譯的鍵（已知缺口，附 Issue 編號作註解）；收據的 `untranslated` 與 `untranslated_args` 鍵集合超出此清單者為失敗 |

路線不含任何防拷題或手冊答案（`AGENTS.md` §1）。路線檔不含原版素材，可進版控。`@expect`、`@known-untranslated` 的鍵只列 UI 字串與摘要鍵，不列玩家輸入。

## 5. 無頭收據工具 `cmd/phantasie-receipt`

輸入：`-root`、`-route`、`-lang`（可重複）、`-overlay on|off`、`-frame-every <步數>`（無頭模式在 `@check` 以外的 `Frame` 間隔，預設與前端每幀步數相同）、`-out`。

每個 `@check` 輸出一列收據（TSV）：

| 欄 | 內容 |
|---|---|
| `check` | 檢查點名稱 |
| `image_hash` | 解壓後映像雜湊（`001` §3.1，每次執行一個值，每列重複） |
| `hook_sig` | hook 簽章檢查結果（`ok` 或失敗的掛點名稱）；非 `ok` 時工具以非零離開，不產生其餘欄位 |
| `font_hash` | 快取的 `FONT` 2,032 bytes 雜湊（`001` §8） |
| `steps` | 原版已執行的指令數 |
| `reads` | 原版讀鍵入口累計次數 |
| `vram_hash` | `B800:0000` 起 `4000h` bytes 的 FNV-1a 64 |
| `mem_hash` | 映像段起至 `DGROUP` 末端（`2E4E:FFFF` 範圍）的雜湊 |
| `stamps` | `Layer` 疊字數 |
| `layer_hash` | 疊字集合（`Key`、位置、`Text`、`State`、`FG`、`BG`、`Transparent`）的雜湊（含顏色與透明格，使整列反色與透明格遺失會改變雜湊） |
| `keys` | 實際疊字鍵集合（`@expect` 比對用） |
| `untranslated`、`untranslated_args` | 該檢查點之前累計的未譯鍵集合（不含玩家輸入；`001` §9） |
| `counters` | `001` §9 的全部計數器（`unpaired` 必須為 0；`composed_miss_*`、`arg_unclassified`、`straddle`、`recolor_fallback`、`rebuild_lost`、`shadow_lost` 列出） |
| `stale_cells`、`exposed_events` | 稽核結果（§5.1），必須為 0 或在已知清單內 |
| `png` | 2 倍畫面的 PNG 檔名（`-out` 下，`<route>.<check>.<lang>.png`） |

### 5.1 同狀態 A/B 與稽核

**hook 唯讀證明**：同一路線、同一 `-frame-every`，疊字 `on`、疊字 `off`、完全不掛 hook 三組各跑一次，每個檢查點的 `steps`、`reads`、`vram_hash`、`mem_hash` 必須相同。這證明 hook 沒有改機器。`on` 與 `off` 的 2 倍畫面在疊字矩形以外逐點相同只是回歸護欄（`Layer.Draw` 只改疊字矩形內像素，所以由構造保證），**不是位置或內容正確的證據**；位置由 `001` §10.3 的位置 oracle 判定，內容與殘字由下列稽核判定。

**獨立稽核**（以原版 `FONT` 位元圖與目前視訊記憶體為基準，不使用疊字層自己的狀態當期望值）：

1. **殘字稽核**（`stale_cells`）：對每一個 `Shown` 疊字的每個非透明格，取其對應的原版格（`records[Key]` 的 `Cells`），檢查畫面是否仍是該原文的字模畫出的結果：字模遮罩為 0 的像素全為同一色號、非 0 的像素全為另一色號（反白後色號互換仍成立）。不成立者計為殘字格（疊字蓋在已不是原文的畫面上）。
2. **英文外露稽核**（`exposed_events`）：對 `records` 內每個在提交時 `Resolve` 回 `OK` 的事件，若其事件矩形目前仍顯示該原文（同上的遮罩一致檢查，且該矩形沒有被反白以外的操作改動），則 `Layer` 內必須有覆蓋該矩形全部非隱藏格的疊字；缺少者計為英文外露事件。
3. 兩項稽核每個 `@check` 執行一次，另在無頭模式每個 `Frame` 抽樣（含事件中途的 `Frame`）。結果必須為 0；不為 0 的鍵列入 `@known-untranslated` 同風格的已知清單並附原因，否則失敗。
4. 稽核本身要有負對照：關閉疊字（`-overlay off` 但稽核仍以 on 的 records 執行）時 `exposed_events` 必須大於 0；把一個 `Shown` 疊字故意留在被改寫的畫面上，`stale_cells` 必須大於 0。

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
2. `Scratch` 與本遊戲存檔流程（`DNG.SAV` 等以讀寫開啟、`PHBACKUP` 備份）的實際行為。
3. 地牢、戰鬥、商店等路線的按鍵序列與可重現性（隨機數是否固定）。
4. `F11`、`F12` 是否與原版衝突。
5. 稽核的遮罩一致檢查對「被變暗（`invert2`）的列」是否需要放寬（動態未量到變暗，`002` §9）。

## 8. 實作會改變的既有程式

| 位置 | 更動 |
|---|---|
| `apps/phantasie/input.go` `KeyGate.fire`、讀鍵計數 | 重複觸發去重（開啟旗標加 `SP`，同 `001` §3.2）；新增 `PressAfterReads(n, name)`（以讀鍵入口次數為準的閘門），`@wait` 使用 |
| `apps/phantasie/cmd/textlog` | 供收據工具重用的路線重播與計數輸出（見 `001` §11） |
| `oracle` | `CGAPalette()`（dosgolem 規格 `250-cga-int10-scroll-and-palette`） |
