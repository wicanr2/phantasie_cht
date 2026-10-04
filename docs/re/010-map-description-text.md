# 010 地圖位置描述文字的來源（OUT*.DAT）

日期：2026-10-04。目的：確認 `docs/spec/003` §12 第 6 項「第三種文字來源」（大地圖上踩到特殊地點時畫出的描述，`%s` 指標落在 `C99D`、`C9C5`、`CA3D`）的資料從哪來。

## 證據

| 項目 | 內容 | 等級 |
|---|---|---|
| 來源檔 | 18 個 `OUT*.DAT`（`OUT17.DAT` 不存在），各 1024 bytes。前段是地圖資料，偏移 595 起是 40 bytes 一筆的描述行：39 個可印字元加 NUL，內容以空白置中或靠左（例 `OUT1.DAT` 偏移 675 是 `         YOU ARE ON A PATH,            `）。共 58 行，相異原文行 44 種（去頭尾空白後 43 種）。有描述行的偏移是 595、635、675、715、755、795、835（7 個槽，每檔只用其中幾個） | 已證實（讀檔位元組） |
| 讀入 | 動態：進入大地圖後，`OUT1.DAT` 以 DOS 讀檔（`int 21h AH=3Fh`，步 1812182 前後，要求與實得 1024 bytes）一次讀進 DGROUP。對描述區位址的第一次寫入就是這次讀檔（寫入者是 dosgolem 的 `int 21h` 處理，不是遊戲程式碼） | 已證實（`oracle.OnWrite` 與 `FileOps`） |
| 位址 | 事件的 `%s` 指標 `C99D`、`C9C5`、`CA3D` 的內容分別是 `OUT1.DAT` 偏移 675、715、835 的描述行；三者與偏移的差都是 `C6FA`。所以讀入緩衝區起點是 `DS:C6FA`，描述區 `[C6FA + 595, C6FA + 875) = [C94D, CA65)` | 已證實（`OUT1.DAT`）；其餘 17 個檔案讀進同一緩衝區是強推論 |
| 不在其他來源 | 描述行不在 MESS、SCROLLS、靜態字串列舉（`tools/enumerate_text.py` 的 `strings.tsv`）；`docs/spec/003` 原先寫「原檔內沒有明文」是只掃了這幾類 | 已證實 |

## 處理

- 區間表 `apps/phantasie/regions.tsv` 加一列 `buffer C94D 0 118`：描述區的 `%s` 引數與格式字串指標歸 `buffer` 種類，查 `prose`。
- `tools/out_text.py` 擷取全部描述行；`tools/out_text_merge.py` 把譯文（以去頭尾空白的英文為鍵的對照檔，工作區檔案，含原版英文故不進版控）併進 `text/prose.<lang>.tsv`。鍵是原文行 rstrip 的 sha256 前 12 位元；原文行開頭有空白（資料已置中）者譯文加 `\c` 由版面置中。同一句話在不同檔案以不同置中位置出現時是不同鍵，各自一列。
- 描述行跨 2 至 3 行連續顯示，每行各自一個事件；譯文逐行對應，語序以能分行接續為準。
- 原版資料瑕疵：`OUT6` 至 `OUT16` 的偏移 755 槽（共 11 個檔案）內容是 `ENDING SEQUENCE` 加 `GE BUBBLING POOL`（前後是 0Dh 等空白控制字元，另有 `1Ah`），像是 `YOU ARE NEAR A STRANGE BUBBLING POOL`（`OUT5` 偏移 755）被其他字串覆寫一半。`OUT19` 的偏移 835 槽是 ` MIST.`（上一行 `...A DENSE MIST` 已含 MIST）。`tools/out_text.py` 不收含 `ENDING SEQUENCE` 的槽，並列在 stderr 的略過清單，保持原文、不譯；這些槽能否在遊戲中被顯示尚未量到（等級：未知）。` MIST.` 與 `A SMALL DOOR SET INTO THE`（`OUT2`、`OUT3`，下一行是 `HILLSIDE`）是正常描述行，已有譯文。

## 正常觸發與顯示驗收

2026-10-04 補充。引擎 `277bb98`，Go 1.24.13、Python 3.13，IDA Pro 9.4。正式資料庫唯讀，查詢容器內副本。

| 原始定位 | 資料流與結果 | 等級 |
|---|---|---|
| `OUT1.DAT` SHA-256 `1ad68c2c67dcb2c94b4260007adedc23a8fa5fe4676897ad8622e2f976357532` | 前 520 bytes 為 26×20 格；偏移 520 起有五位元組特殊格記錄。`(13,15)` 的記錄為 `0D 0F 0C 00 00`，地形格值 66 | 已證實，原始 bytes 與讀取端 |
| IDA 線性 `sub_B867`，`B877: 8A 87 FA C6` | 保留 operand `[bx-3906h]`；16 位元位址等價於 `DS:C6FA + y*26 + x` | 已證實，IDA bytes |
| IDA 線性 `sub_C37E`、`sub_C6F0` | 格值的個位數為 6 時查特殊格表；第三位元組 12 導向兩行分支。描述槽起點為 `DS:C6FA + 595 + 40*(12-10)`，即 `C99D`；下一行在 `C9C5`。其他格及其他事件型別未逐一驗證 | 已證實，靜態資料流與道路格動態事件 |
| IDA 線性 `sub_3FAD`；dosgolem 映像偏移 `2EEE`、`2F10` | 分別畫在第 10、11 列、欄 0；格式 `%s`，引數 `C99D`、`C9C5`。譯文鍵 `h:4832331d8418`、`h:44a7f3d335d4` | 已證實，正常玩家探針與收據 |
| `tests/routes/map-description.route` | 正常建立四人隊伍、離城，從 `(14,15)` 向西一步到 `(13,15)`。繪字完成點為 4,387,641 與 4,406,543 步；4,406,544 步擷取完整覆繪，隨後清除返回 | 已證實，限目前 dosgolem 執行及固定輸入 |

IDA OV2 輸入為 `ov2_composed.bin`，SHA-256 `f461da5fb4e02634ab47dcbd8af3f5b7ae53c49d00ad42f5f56fcae765121422`。輸出 `workplace/explore-main/ida-windows-ov2.json` 核對 251 個函式與輸入雜湊。IDA 線性位址減 `1100h` 才是 dosgolem 映像偏移。

四語、none/off/on/on-f2 共 112 點：84 個覆繪 UI PASS，28 個 none UI SKIP 只作原版狀態基準。完整記憶體、VRAM、步數、讀鍵次數相同；兩種 Frame 節奏的 Layer 相同。獨立排版核對兩行全文與置中，原生與兩倍像素差異只落在原版文字矩形，沒有缺字。刪除第二行譯文的本機副本使目標點 FAIL。

收據在 `workplace/explore-main/ab-ui-windows/map-description/`，清冊在同批 `summary.json`，排版與像素結果在 `ui-window-visual.log`。這些證明顯示與清除；互動等鍵尚未接通，見 [005 §13](../spec/005-play-frontend-and-receipts.md#13-道路描述與公會重名提示)。不能把此收據稱為互動停留驗收，也不以此宣稱所有地圖描述已驗收。
