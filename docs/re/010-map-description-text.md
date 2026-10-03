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
