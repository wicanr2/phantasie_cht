# 008 提示畫面的確認等鍵

狀態：CONFORMED
日期：2026-10-04
證據：[016 第二條等鍵路徑](../re/016-discarded-key-wait.md)。前置：dosgolem `251-oracle-step-guard.md` 必須先 CONFORMED。顯示規則沿用 005 §13；不改譯文或原版判定。

前置實作基準：`dcc1b9d`，251 已 CONFORMED。本規格的 none/off/on 同狀態 A/B 以共同的 KeyGate 與此共用契約為基準。

## 行為契約

1. `37A0` 的完整 34 bytes 簽章須與證據相同。每次入口由 guard 核對並直接回錯，錯誤在執行入口指令及 hook 前終止，不能猜測繼續。入口記 SP，IRQ0 返回同一入口與 SP 時不重開等待。
2. 在 `37B8`、入口已開啟且 SP=入口 SP-8 時讀鍵，減法採 16 位元環繞。未開啟或 SP 不符回普通錯誤。只在這次等待第一次到達此點增加 Reads；重複主機更新不得增加 Reads、Dups 或消耗排隊計數。
3. 沒有可送按鍵時回 `oracle.InputWaitError`。Oracle 不執行該指令、hook、stub 或 tick。畫面照常合成與切換語言，直到玩家確認。
4. 有按鍵時只送一個正常 BIOS 按鍵，成功後 Gated 加一、LastSent=Reads，標記已送。即使 IRQ0 先執行並返回相同停點，也不重送。`37C1` 關閉等待。原版 INT 16h 消耗按鍵，照原版返回與清除。
5. 頭鍵的 after 尚未到達或 skip 非零時，這條阻塞路徑回明確普通錯誤，保留排隊鍵、after、skip、Gated 與 LastSent。Reads 只按第 2 項記第一次抵達。禁止藉空鍵前進或反覆呼叫扣掉 skip。既有 `37C2` 的 `@wait` 與排隊規則不變。
6. 不支援的鍵在此路徑回普通錯誤且保留排隊鍵，不當作成功確認。有效鍵仍走 SendKeys／單字元 TypeKeys。
7. 原版程式、記憶體、VRAM 與存檔只因原版指令或正常鍵盤輸入而改變。停留凍結指令時鐘，不宣稱真機 PIT 或 BIOS 忙碌迴圈一致。

## 前端與收據

- 前端只將 `InputWaitError` 當成可繼續的等待；其他錯誤仍終止執行並保留診斷。F12 可以在停留時切換，下一次一般按鍵可繼續。
- 收據的 `@check` 可接受等待錯誤，但必須在返回當下重新核對「Pending=0 且 Reads>LastSent」。條件不成立仍失敗。`@snap N` 若未跑足 N 指令遇到等待，必須失敗，不能把主機幀當指令數。
- 將 `map-description`、`guild-duplicate` 的瞬間擷取改成 `@check` 加明示 Return，驗證停留、確認、清除與重試。不得自動確認。
- 不新增路線指令。120 次 Session 的 Run／Frame 停留與即時切換，由本機驗證程式重播同一正常路線證明。

## 驗收

| 項目 | 證據要求 |
|---|---|
| 兩個正常提示 | 四語 none/off/on/on-f2 收據，同步數、Reads、1 MiB 記憶體、VRAM、存檔清冊；none 的 UI SKIP 不當成功 |
| 停留 | 120 次 Run／Frame 都得到 InputWaitError；Regs 全暫存器與 Flags、1 MiB 記憶體含 BDA、VRAM、steps、ticks、KeysPending、KeysConsumed、Reads、Gated、LastSent、Dups 不變，全文與圖層不變 |
| 切換 | zh-TW→zh-CN→en→ja→ko→zh-TW，不推進原版；回到同語言圖層相同 |
| 確認 | 各提示一次 Return 被 BIOS 消耗一次，以 KeysConsumed 增量與 KeysPending 歸零獨立核對，返回原版清除；重名可改名為 Bob 並回主選單 |
| 負對照 | 關閉 guard 後停留斷言失敗；錯簽章、未開啟、錯 SP、不合法鍵、future after、skip 都明確失敗；合成 IRQ0 返回同一送鍵停點不重送 |
| 回歸 | 既有正常路線全部 zh-TW；四語手冊、卷軸與存讀檔抽樣；Session 冒煙、既有跳過兩次 `37C2` 的 `@wait` 測試及前端 Xvfb 實際輸入 |

實作會改變：`apps/phantasie/input.go`、新增 `input_test.go`、`apps/phantasie/cmd/phantasie-play/main.go`、`apps/phantasie/cmd/phantasie-receipt/main.go` 及兩條路線。原有測試期望只在新增真正確認鍵所需時改動，逐一記錄原因。其他正常路線若遇到新等待，按原版明示確認追加鍵，不自動跳過。

## 審查與收據

2026-10-04 契約對程式、資料對證據兩種唯讀審查完成，報告 `workplace/review/wait-contract.md`、`wait-evidence.md`。主代理逐項核對，明確化 guard 正常送鍵的 BDA 例外與入口直接回錯，增加暫存器／鍵盤計數、IRQ0、16 位元減法與既有 `@wait` 驗收。唯一阻擋已修正，轉 READY。

### 驗收收據

引擎 `60b76b3`，前置 `dcc1b9d`，Go 1.24.13，Docker `psychicwar-go-ebiten:latest`。前端與收據二進位由本次相同執行邏輯建置；catalog 與字型未變。下列閘門皆通過，轉 CONFORMED；其他規格的未量到分支保持原有狀態。

| 閘門 | 本機收據 | 結果 |
|---|---|---|
| 道路與重名 | `workplace/explore-main/ab-wait-windows/`，四語、四模式，兩條各 6 點 | 192 點中 144 個覆繪 UI PASS、48 個 none UI SKIP；原版完整狀態及兩種節奏相同 |
| 停留、切換、確認 | `wait-runtime/`，兩種提示各四語，每組 120 次 Run／Frame | 所有暫存器、Flags、記憶體、VRAM、步數、ticks、BIOS 與閘門計數不變；切換返回同圖層，確認只消耗一次鍵 |
| 全文及範圍 | `wait_visual.go` | 四語兩種提示完整顯示，置中與補白正確，原生及兩倍差異限安全矩形，沒有缺字 |
| 負對照及合成測試 | `wait_runtime.go`、`wait-app-tests.log` | 關閉 guard 的兩種停留皆失敗；錯簽章、未開啟、錯 SP、future after、skip、無效鍵、環繞 SP 與 IRQ0 測試 PASS |
| 一般正常路線 | `wait-regression/summary.json` | 20 條、438 點 zh-TW 全部 PASS；另外兩條存讀檔路線依序驗收 |
| 四語卷軸 | `wait-scroll-regression/summary.json` | 四模式、31 點，共 496 點，原版狀態與兩種節奏相同；卷軸正常返回 |
| 四語存讀檔 | `wait-save-regression/summary.json` | 四模式共 240 點，實際存檔、冷啟動角色讀回與狀態比較通過 |
| 手冊長路線 | `wait-manual-regression-v2/summary.json` | 正常物品、法術題，路線內四語及英文切換、返回，共三模式 216 點；144 個覆繪 UI PASS、72 個 none UI SKIP，原版完整狀態相同 |
| Session 與資料 | `wait-app-tests.log`、`wait-data-tests.log` | 原版冒煙、字型定色、既有 `@wait` 實際 PASS；資料掛載補正後 catalog 與共用格式向量 PASS |
| GUI 實際按鍵 | `wait-gui.log`、`wait-gui/` | Xvfb 正常建立、重名停留、F12 循環、Return 確認、重新命名與關閉 PASS；未宣稱 Windows 或 macOS 真機驗收 |

上述相對路徑均位於 `workplace/explore-main/`，不進版控。none 的 UI SKIP 只提供原版狀態基準，不算顯示驗收。

完整工具、路線、二進位、catalog、字型及收據雜湊在 `workplace/explore-main/wait-verification-manifest.json`。原始 70 檔雜湊不變。

實作期間的處置：原版新增阻塞點使舊路線的後續按鍵被提示消耗，依實際停點加明示 Return，保留既有期望。道路清除後的無字畫面沿既有固定步數快照驗證，不降低一般 `@check` 的疊字門檻。GUI 角色亂數不可與無頭角色值逐點比對，改核對固定提示區域，停留與切換返回仍比整圖。xdotool 的 Escape 名稱及逾時預算屬驗證環境修正。

手冊長路線另量出四個固定步數區段內的確認停點，再拆成精確快照、明示 Return 及餘下步數。原有檢查點的最終步數保持不變。研究副本的自動確認只用於量測，不作正式收據；正式工具沒有自動確認。三模式正式路線各 72 點，完整比對後才列入本節。初次覆繪模式的 240 秒預算不足，改以已驗證的 40,000 步取樣並延長有界預算乾淨重跑。
