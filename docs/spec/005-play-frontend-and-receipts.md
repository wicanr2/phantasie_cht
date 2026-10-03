# 005 遊玩前端與同狀態驗收

狀態：DRAFT 第二版（2026-10-03）。依賴 `001` 至 `004` 與 dosgolem 規格 243（CGA 圖形模式的 INT 10h 與 `oracle.CGAPalette()`）。證據來源：`apps/phantasie/input.go`（`KeyGate`）、`oracle`（`Run`、`SendKeys`、`TypeKeys`、`Scratch`）、dosgolem 規格 237（scratch 層）。

## 1. 範圍

兩個命令：互動前端 `cmd/phantasie-play`（Ebitengine 視窗，只用鍵盤），無頭收據工具 `cmd/phantasie-receipt`（路線重播、A/B 比對、畫面輸出）。路線檔格式、驗收收據格式。打包發行在另一規格。

## 2. 依據

| 事實 | 證據 | 等級 |
|---|---|---|
| 原版每次讀鍵前會先清空 BIOS 鍵盤佇列；`INT 16h AH=00h` 在 dosgolem 佇列空時回 0 不阻塞；按鍵必須在「讀鍵包裝函式入口 `img:37C2`」放進佇列才不會被清空動作吃掉 | `apps/phantasie/input.go` 註解與 `006` | 已證實 |
| 路線 `Return Return Up Return`（`KeyGate` 送鍵）在 60M 步內可重現「新成員、加入、離開城鎮」等流程；同一路線同一步數畫面雜湊相同，與 `Frame` 呼叫節奏無關 | `006`、本輪 `textlog -route` | 已證實（已測路線） |
| 單一字元鍵（字母與數字）以 `oracle.TypeKeys` 進 BIOS 佇列；有名字的鍵（`Return`、`Esc`、方向鍵、`Space`、功能鍵）以 `SendKeys` | `oracle/input.go` | 已證實 |
| 寫檔：DOS 檔案層有 `Scratch` 目錄，建立與寫入都落在該目錄，原始目錄不被修改 | `internal/dos/files.go` 的 `create`；規格 237 | 已證實（讀碼）；與本遊戲存檔流程的對應待量測 |
| `oracle` 的 `CGA4()` 回 320×200 色號；CGA 色彩選擇暫存器與 RGB 表目前不由 `oracle` 提供，dosgolem 規格 243 補 `oracle.CGAPalette()` | `oracle/oracle.go`；規格 243 | 已證實（現況） |
| 遊戲動態量到的 INT 10h 只有 `AH=00h` 與 `AH=06h` | `002` §2 | 已證實（已測路線） |

## 3. 互動前端 `cmd/phantasie-play`

旗標：`-root`（原版目錄，唯讀）、`-state`（可寫狀態目錄，預設 `$XDG_DATA_HOME/phantasie-cht`，`Scratch` 指向其下；存檔留在這裡，不寫原版目錄）、`-lang`（預設 zh-TW）、`-text`（`text/` 目錄）、`-font`（字型目錄）、`-zoom`（1 或 2，視窗為 640×400 的倍數）、`-ips`（每秒執行的指令數，預設值由實測決定）。

執行迴圈（Ebitengine 的 `Update`，每秒 60 次）：

1. 執行 `ips / 60` 道指令（可被 `-ips` 調整；呼叫 `RunUntil` 或 `Run`）。
2. `Layer.Frame(indexed, rgb)`：`indexed = oracle.CGA4()`，`rgb` 依目前調色盤（`002` §6）換算。
3. 組合 640×400 的 RGBA：色號畫面逐點放大 2 倍，`Layer.Draw(dst, 2, missing)`；顯示語言為 `en` 時略過 `Draw`。
4. 交給 Ebitengine 顯示，視窗倍率 `-zoom` 以最近鄰縮放。

輸入：

- 鍵盤事件轉成原版按鍵：有名字的鍵（Enter 為 `Return`、`Esc`、方向鍵、`Space`、`Backspace`、`Tab`）與功能鍵送 `SendKeys` 同名；可列印字元（`ebiten.AppendInputChars`）送 `TypeKeys`。
- 一律經 `KeyGate.Press`：按鍵排入佇列，於原版下一次讀鍵入口放進 BIOS 佇列（與無頭路線同一路徑）。佇列最多 16 筆，滿了丟棄最新的，避免長按累積。
- 保留鍵（不送原版）：`F11` 全螢幕切換、`F12` 依序切換語言（zh-TW、zh-CN、en、ja、ko 中已啟用者）。本遊戲是否使用 `F11`、`F12`：待靜態確認（掃描碼 `57h`、`58h` 不應出現在程式碼的鍵盤判斷）。

沒有滑鼠與搖桿：忽略。沒有音訊：原版的 PC 喇叭輸出以 dosgolem 目前行為處理（不發聲）。

視窗標題：`幽靈戰士（Phantasie）繁體中文化`；語言切換時顯示語言名稱 1 秒（疊在視窗標題，不畫進遊戲畫面）。

## 4. 路線檔

`tests/routes/<名稱>.route`，UTF-8 文字，一行一個項目，`#` 開頭是註解：

| 項目 | 意義 |
|---|---|
| `Return`、`Esc`、`Up`、…、`A`、`1` | 送出一個按鍵（經 `KeyGate`，每次讀鍵入口送一個） |
| `@wait <N>` | 等原版再讀鍵 N 次後才送下一個鍵（用於需要等動畫的畫面；預設 0） |
| `@check <名稱>` | 在原版第 K 次讀鍵入口（K 為該行之前已送出的鍵數加 1）停下，輸出收據（§5） |

路線不含任何防拷題或手冊答案（`AGENTS.md` §1）。路線檔不含原版素材，可進版控。

## 5. 無頭收據工具 `cmd/phantasie-receipt`

輸入：`-root`、`-route`、`-lang`（可重複）、`-overlay on|off`、`-frame-every <步數>`（無頭模式在 `@check` 以外的 `Frame` 間隔，預設與前端每幀步數相同）、`-out`。

每個 `@check` 輸出一列收據（TSV）：

| 欄 | 內容 |
|---|---|
| `check` | 檢查點名稱 |
| `steps` | 原版已執行的指令數 |
| `reads` | 原版讀鍵入口累計次數 |
| `vram_hash` | `B800:0000` 起 `4000h` bytes 的 FNV-1a 64 |
| `mem_hash` | 映像段起至 `DGROUP` 末端（`2E4E:FFFF` 範圍）的雜湊 |
| `stamps` | `Layer` 疊字數 |
| `layer_hash` | 疊字集合（`Key`、位置、`Text`）的雜湊 |
| `untranslated` | 該檢查點之前累計的未譯鍵數 |
| `png` | 2 倍畫面的 PNG 檔名（`-out` 下，`<route>.<check>.<lang>.png`） |

同狀態 A/B：同一路線、同一 `-frame-every`，疊字 `on` 與 `off` 各跑一次，每個檢查點的 `steps`、`reads`、`vram_hash`、`mem_hash` 必須相同；`on` 的 2 倍畫面在疊字矩形以外必須與 `off` 逐點相同（以工具內建比較，輸出差異像素數與差異是否全在疊字矩形內）。

換 `-frame-every` 重跑（例如 20,000 步與每次讀鍵入口兩種）：`vram_hash`、`mem_hash` 必須相同；`layer_hash` 與畫面在檢查點若不同，列為「對 `Frame` 節奏敏感」，需說明原因（`001` §11 第 4 項）。

擷取畫面前（PNG 與疊字比較）先呼叫一次 `Layer.Frame`，使 `Pending` 疊字進入 `Shown`（`002` §8）。RGB 依 `oracle.CGAPalette()`。hook 簽章檢查（`001` §3.1）不通過時工具以非零離開並印診斷，不產生收據。

缺原版檔時整個工具 SKIP 並印出原因，不算驗收。

## 6. 驗收路線與覆蓋

必備路線（各自有 `@check`，每個語言各一組收據）：

1. 標題選單（四個項目的畫面）。
2. 城鎮：選單列、`PELNOR` 狀態列、選單反白移動。
3. 公會：選單、反白、`New member`（種族、職業、屬性畫面、`KEEP`／`PURGE`、`INPUT NAME`）、`Add member`、`Inspect`（清單）、關閉選單。
4. 離開城鎮到地圖。
5. 銀行、神祕、武器店、旅店各一個畫面。
6. 地牢：進入、訊息視窗（MESS）、選項視窗、戰鬥的訊息與選單、法術列表。
7. 卷軸閱讀（SCROLLS）。
8. 存檔與讀檔，讀檔後畫面無殘字。

到不了的畫面照實記錄原因與條件，不修改存檔或記憶體跳關（`AGENTS.md` §4）。覆蓋收據列出每條路線經過的文字事件鍵集合與未譯鍵。

## 7. 未決

1. `-ips` 的預設值與原版計時行為（PIT、延遲迴圈）：以實測決定；若原版以指令計數做延遲，需檢查過快是否使動畫無法觀看。
2. `Scratch` 與本遊戲存檔流程（`DNG.SAV` 等以讀寫開啟、`PHBACKUP` 備份）的實際行為。
3. 地牢、戰鬥、商店等路線的按鍵序列與可重現性（隨機數是否固定）。
4. `F11`、`F12` 是否與原版衝突。
