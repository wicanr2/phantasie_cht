# 025 選項字元流與跨記錄解析缺口

日期：2026-10-05。引擎 `8d9807d`、專案基準 `5fe2e82`。本檔記錄資料列舉工具的缺口，原版遊戲與執行期覆繪不修改。實作契約見 [011](../spec/011-option-stream-parsing.md)。

## 輸入與工具

原版輸入及權利分類沿用 [001](001-input-inventory.md)。本機分析清冊 `workplace/explore-dungeon/pool-options-analysis.json` 保存全部來源雜湊與逐項比較，不保存到版控。

| 輸入 | SHA-256 |
|---|---|
| MESS2 | `4720e50e9a3ba3640565224209a15a0ebfaf490974a042e4eb08ba6f38151952` |
| MESS5 | `2c88e615c9b85d84e8405be398ee6424f6bfc7823f9345118f5bec8a8302822f` |
| MESS6 | `f166ef6dce694f4bd0e1829d46111155639cdaf3f7031dcbc772dfa00e7da325` |
| MESS7 | `a9a5da08cc7a52a115e35cf1c0b18f163dd349d67cb6464892c8ec7717ced6d3` |
| MESS8 | `ac7d9f6b7612d7baaaf6ed1d061fae95539491eeddc692b86eb17813e080b84d` |
| `ov2_composed.bin` | `f461da5fb4e02634ab47dcbd8af3f5b7ae53c49d00ad42f5f56fcae765121422` |
| 正式 `ov2.i64` | `294be0bfbe2cb912f59b84f61e5487ae9041d2647a6f357ba5d9ef7521ca2abb` |

IDA Pro 9.4 使用 `ida-pro-9.4-idapython:locked-v1`，image ID `sha256:6f6d59af49d0008c4109a5295b5f374bdc007e2d1ab28cb9de08779584de2780`。正式資料庫唯讀，查詢使用容器 `/tmp` 副本；輸出核對 UID1000、版本、輸入雜湊及 251 個函式。其他分析使用既有 `psychicwar-go-ebiten:latest` 的 Python 3.11。

## 原版讀取契約

等級：已證實，限 IDA 控制流、bytes 及固定原版資料。以下位址為 IDA 線性位址，dosgolem 映像偏移等於該位址減 `1100h`。

| 原始定位 | 證據 |
|---|---|
| `sub_8F71`，`8FD3` 至 `9002` | `DI` 自 0 計正文已消費字元，以 `DI mod 40` 索引目前 chunk，直到 `DI == L` |
| `sub_8F71` 的正文讀取端與 `sub_88F4` | 每滿 40 字元載入下一個索引；選項數來自第一個後續 chunk 的旗標。短訊息依既有 `90B9` 強制為 3 |
| `90DA` 至 `90F2` | 選項欄寬 11 或 3，總選項字元為 `(N-1)×欄寬` |
| `9133` 至 `917B` | 選項繼續沿用正文的 DI，以 mod40 取字元；`9153` 每字元遞增，`9162`、`9164` 判斷跨界，`916E` 至 `9178` 載入下一索引 |
| `9180` 至 `9198` | 每取得完整欄寬才繪一個選項；chunk 邊界不是選項邊界 |

因此選項起點為正文起始索引加 `floor(L/40)`，chunk 內偏移 `L mod 40`。不能固定從 `idx+ceil(L/40)` 的一個 chunk 取選項。後續 chunk 的旗標不屬文字。

## 既有工具缺口

基準 `5fe2e82` 的 `tools/gamedata.py` 對普通訊息固定取 `idx+ceil(L/40)` 的單一 chunk，再切欄位。10 個來源有 55 個普通訊息選項單位，9 個與原版字元流不符。此缺口已依 011 修正，以下保留原始定位與訂正原因。

| 單位 | L | N | 問題 |
|---|---:|---:|---|
| MESS2:90 | 90 | 7 | 同一正文尾段接選項，且跨下一記錄 |
| MESS5:70 | 56 | 3 | 選項在正文末筆內，舊工具誤收後一個訊息 |
| MESS6:44 | 40 | 5 | 第四欄尾空白跨記錄，續段誤列短訊息 |
| MESS6:50 | 50 | 3 | 選項在正文末筆內，舊工具誤收後一個訊息 |
| MESS7:63 | 40 | 5 | 第四欄尾空白跨記錄，續段誤列短訊息 |
| MESS7:74 | 80 | 5 | 第四欄字詞跨記錄，續段誤列短訊息 |
| MESS7:78 | 80 | 6 | 第四及第五欄跨記錄，最後一欄被列為空白 |
| MESS8:40 | 80 | 6 | 第四及第五欄跨記錄，最後一欄被列為空白 |
| MESS8:64 | 41 | 3 | 選項在正文末筆內，舊工具誤收後一個訊息 |

這也使兩種索引標記錯誤：已消費的選項續段被列成獨立短訊息；未消費的下一個真正訊息被標成 used 而跳過。修正後已重新核對短訊息統計，不能將舊短片段補譯。

兩輪唯讀審查無阻擋或應改。獨立資料審查直接核對原版指令 bytes，再以自己的解碼與逐字元游標確認 55 個單位及表列訂正。修正原型重新列出 MESS5:72、MESS6:52、MESS8:66，短訊息只剩 MESS5:61 與 MESS7:60、61、62。MESS7:88 的正文遇不存在的索引 89，且 N 無效，不屬本次有效選項範圍，不改其既有正文處置。

不可變鍵為 `DOS／OV2／IDA 8F71、9133 至 917B／DI 字元游標`。回填入口為 RE007、RE008、003、009、011、研究及規格索引、CONTEXT。只修資料列舉，不將未到達的原版畫面宣稱已中文化。

## 正常路線限制

正常四人隊伍從 Pelnor 出發，探索第七地牢的路線仍停在 OUT2 `(13,0)` 的游泳畫面。原版阻擋海洋並保留隊員死亡；未修改座標、存檔、記憶體或原版判定。這次探索沒有取得水池或跨記錄選項的正常 UI 收據，不計為新增玩家畫面驗收。私人路線及只讀追蹤入口為 `pool-live.route`、`pool-live-trace.jsonl`、`pool_live.go`。

本次 IDA 原始匯出為 `ida-pool-terrain.json`；資料對照為 `pool-options-analysis.json`。正式 catalog、字型及引擎保持原狀；水池補譯與選項畫面驗收仍待正常路線。

## 工具驗收與現況

011 已 CONFORMED，限資料列舉工具。正式驗證使用 Python 3.13 與 `python:3.13-bookworm`，image ID `sha256:933b46a028fd786c9c3d426ebabc237e29a15912231ea8de576e95f0e4f41a4c`。獨立核對器另行解碼及逐字元讀取，未使用被測 `chunk_at`、`cells` 或 `parse_mess` 建立原版期望。

| 項目 | 結果 |
|---|---|
| 原始欄位 | 55 個普通選項與 4 個短訊息逐一核對；表列 9 個訂正成立，另有 3 個真正訊息恢復 |
| 目前解析分類 | msg 386、short 4、orphan 30、trailer 10；舊工具為 383、9、35、10 |
| 規範化匯出 | 7 個單位改變；MESS6:44、MESS7:63 的訂正只涉及去尾空白前的 bytes |
| 預設匯出 | 404 改為 402，新增 3 個真正訊息，移除 MESS6:53 與 MESS8:67 至 70 的 5 個正文續段 |
| 明示寶箱匯出 | 403 個單位；MESS5:61 的完整原始欄位與既有匯出內容相同 |
| 測試與負對照 | 10 項解析及 5 項既有匯出測試 PASS；舊解析器有 8 項預期失敗 |
| 保護範圍 | 原版 70 檔、受保護檔案 32 個、公開路線 23 條及正式 IDA 不變 |

011 驗收時有 13 個正文或選項鍵及 MESS7:60 至 62 的三個水池正文在四語缺譯。現已依 [026](026-recovered-prose-catalog.md)、[012](../spec/012-recovered-prose-catalog.md) 納入四語資料並重建字型，這 16 個鍵的來源覆蓋缺口為零；正常 UI 仍未量到。`option-parser-missing-keys.json` 保留當時來源 id、摘要鍵及長度。

獨立核對、測試及匯出入口為 `verify_option_parser.py`、`option-parser-verification-summary.json`、`option-parser-tests.log`、`option-prose-regression.log`、`option-parser-negative.log` 與 `option-export-after/`。均位於 `workplace/explore-dungeon/`。正式封存清冊為 `option-parser-verification-manifest.json`；原始資料及全文匯出只留本機。
