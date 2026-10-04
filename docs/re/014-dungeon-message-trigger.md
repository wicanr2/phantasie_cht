# 014 地牢事件格與訊息視窗

日期：2026-10-04。範圍：從原版入口正常走到一個 MESS 事件，核對兩行譯文及整頁還原。沒有修改原版座標、亂數、存檔或物品。

## 輸入與工具

| 輸入 | SHA-256 |
|---|---|
| `PHANTASI.EXE` | `0f00a1af62cfcc383b4ca2e4382321f357063ba1457081da6edca4eb9f28e716` |
| `DNG1` | `75e1b2ff5620cbfb0b1699427d1b07e385df8cee846806ba2fff076521ea319a` |
| `MESS1` | `15c97d1b3989745dee8cdd76abf6b181cf3dfa40e8b57b08e9d4d9f81db95808` |
| `ov2_composed.bin` | `f461da5fb4e02634ab47dcbd8af3f5b7ae53c49d00ad42f5f56fcae765121422` |
| 正式 `ov2.i64` | `294be0bfbe2cb912f59b84f61e5487ae9041d2647a6f357ba5d9ef7521ca2abb` |

IDA Pro 9.4，image `ida-pro-9.4-idapython:locked-v1`，image ID `sha256:6f6d59af49d0008c4109a5295b5f374bdc007e2d1ab28cb9de08779584de2780`。正式資料庫唯讀掛載，查詢在容器 `/tmp` 副本執行。JSON 核對版本、輸入雜湊、UID 1000 與 251 個函式後才使用。

本節 IDA 位址都是線性位址，映像偏移為 `ea - 1100h`。執行期定位用 dosgolem 的映像段 `img` 加映像偏移，資料定位用 DGROUP 偏移。兩者不混用。查詢保留原始函式名、位址、指令 bytes 與交叉參照，位於 `workplace/explore-dungeon/ida-events.json`、`ida-events-final.json`。

## 資料流

| 原始定位與運算元 | 意義與等級 |
|---|---|
| IDA `sub_83E1`，`83E7h` 至 `8417h` | 已證實：以 `DS:751A`、`DS:751C` 為目前座標，移動後要求 `0 <= x < 33`、`0 <= y < 38`。步入零值格被拒絕。座標只讀探針在 `position-base.jsonl` 核對入口後第一步為 `(20,1)` |
| IDA `sub_859F`，`85A2h` 至 `85B6h`，`shl ax,5`、`add ax,dx`、`add bx,ds:word_13FF4` | 已證實：地牢格值來自 `DS:[DS:6504 + y*33 + x]`。`sub_BC88` 在 `BCA3h` 將 `DS:6504` 設為 `C6FAh`，`sub_8323` 在 `834Eh` 讀入 DNG 檔 |
| IDA `sub_8725`，`87BEh` 至 `87CAh` | 已證實：格值大於 `DCh` 時，將格值與座標傳入 `sub_898E` |
| IDA `sub_898E`，`8996h` 至 `89B6h`；`add ax,0FF24h`、兩次左移再加原值、`add ax,4F6h` | 已證實：事件記錄位址為 `DS:6504 + 4F6h + 5*(格值-220)`，第一個 byte 為訊息索引與旗標。`89D5h` 的 `and ax,7Fh` 取索引，再於 `89DCh` 呼叫 `sub_8F71`。第一 byte 為 `FFh` 的記錄提早返回 |
| DNG1 檔偏移 `00B2h` 的格值 `EBh`；事件記錄偏移 `0541h` | 已證實，限本次事件：座標 `(13,5)` 的格值為 235，對應記錄第一 byte `65h`，選出 MESS1 索引 101。只讀動態探針記錄 `DS:64F6 = 101`，沒有寫入座標 |
| IDA `sub_8F71`，`9029h`、`90CBh`、`90CEh` | 已證實：兩行經 `sub_36A5` 繪出，之後經 `sub_48A0` 與 `sub_1DF0` 還原頁面。正常輸入探針的兩筆事件均為 dosgolem `img:25A5`，返回偏移 `7F2Ch`，格式指標 `DS:638E`，欄 0、列 5 與 6 |

訊息索引到記錄的解碼沿用 [007](007-message-and-scroll-formats.md)。本次關閉的是其 §5 第 3 項的事件格來源未知，以及第 6 項的一個實際訊息樣本。其餘選項、標記、其他地牢與卷軸不因這個樣本通過而稱為完成。

## 正常路線與同狀態收據

公開路線為 [dungeon-message.route](../../tests/routes/dungeon-message.route)。從原版啟動鏈建立四名角色、離城、進入地牢，再以正常方向鍵走到事件格。沿用既有檢查點，不重新挑選亂數結果。原版使用 dosgolem 預設固定時鐘，DOS `AH=2Ch` 為零時刻；沒有寫入遊戲種子，不聲稱與其他模擬器骰序相同。

`gate-visible` 在最後一個方向鍵送出後固定執行 120,000 步，核對兩個段落鍵 `h:2a4079d1ee67`、`h:5c119d163b05`。`gate-cleared` 再執行 60,000 步，核對段落已消失，`keys` 空白且 `stamps=0`。兩個停點都在手冊題出現前，公開路線沒有作答。

引擎為 `f046ec4`；專案基底 `11b82a8`。正式驗收使用 `psychicwar-go-ebiten:latest`，Go 1.24.13 linux/amd64，工具為本機 `workplace/explore-dungeon/verify_message.py`。四語 × none/off/on/on-f2 共 16 組，每組 20 點，共 320 點。

| 驗證 | 結果 |
|---|---|
| 原版狀態 | steps、reads、VRAM、映像範圍記憶體與完整 1 MiB SHA-256，跨模式及四語均相同 |
| UI | off、on、on-f2 全部 PASS；none 的 UI 是 SKIP，只作原版狀態基準 |
| 節奏 | on 的 20,000 與 on-f2 的 40,000 步取樣，逐點 Layer 雜湊相同 |
| 訊息與清除 | 四語皆有兩個段落鍵；清除後沒有段落疊字。stale_cells、exposed_events、mask_strict 皆為 0，位置 oracle 無錯誤 |
| 畫面 | 2 倍合成的繁中、日文、韓文訊息及還原畫面已目視核對；本次未另驗 1 倍合成 |
| 負對照 | 正常路線加 `-fault noadd` 後，`gate-visible` 因三個外露事件而 FAIL；記錄在 `negative-message.log`，證明稽核可偵測訊息覆繪失效 |

正式收據、PNG 與輸入及工具雜湊在 `workplace/explore-dungeon/ab-message-v2/summary.json` 與各語言、模式子目錄。原版、解碼全文、手冊與作答路線只留忽略目錄。

## 限制

- 這是兩行 MESS 段落及還原的一個正常樣本。兩個 11 字元訊息選項已由 [017](017-dungeon-message-options.md) 正常驗收；短訊息、其他欄寬與事件型別仍待抽樣。
- 卷軸閱讀與道路描述已由 RE015、RE016 及對應規格驗收。規格 005 仍因其他未量到分支保持 READY。
- 初次 `@check` 已錯過段落，後續無期望鍵的黑畫面 PASS 不作訊息證據。用原版 printf 呼叫時序選定固定擷取步數；沒有改程式或判定以讓驗收通過。
