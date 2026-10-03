# 004 字型與語言通道

狀態：DRAFT（2026-10-03）。依賴 `001`、`002`、`003`。證據來源：`tools/build_font.py` 與本機 Unifont 17.0.05 的實測。

## 1. 範圍

字型來源與子集建置、語言通道（zh-TW、zh-CN、en、ja、ko）、即時切換語言的重建流程、各語言譯文的產生方式。譯文鍵與格式在 `003`，前端的切換鍵在 `005`。

## 2. 依據

| 事實 | 證據 | 等級 |
|---|---|---|
| 疊字用字型是 `xlate.Font`（檔案格式 GOLEMFNT）：magic、`u16 W`、`u16 H`、`u32` 字數，每字 `u32` 碼點、`u8` 來源、位元圖（每列 `(W+7)/8` bytes，MSB 在左） | `xlate/font.go`，`tools/build_font.py` | 已證實 |
| 繪製時全形字 16×16 佔一個原版格（2 倍畫面），半形字 8×16 佔半格；`Layer.Draw` 對超出格寬的點不畫 | `001` §6、§7；`xlate/layer.go` 的 `drawGlyphs` | 已證實（讀碼） |
| 本機 GNU Unifont 17.0.05（壓縮檔 SHA-256 `f287cffb26e22723aa36e6684869b0f3ff3bfb822c4b01008bd847911ec1b631`）含 `unifont`（預設，57,086 字）、`unifont_t`（57,086 字）、`unifont_jp`（58,925 字）三個 BMP hex 檔，另有 `unifont_upper`。`unifont_t` 與預設在 26,833 個碼點字形不同，`unifont_jp` 與預設在 9,967 個碼點不同；`U+9AA8`、`U+76F4` 兩字的字形在三者之間不同 | 本輪以 Docker 內 Python 比對 hex | 已證實 |
| 授權：壓縮檔內有 `COPYING` 與 `OFL-1.1.txt`；字型以 SIL OFL 1.1 與 GPLv2+ 含字型例外兩種條款之一散布 | 壓縮檔內檔案 | 已證實（檔案存在）；發行時引用的條款文字待核對 |

`unifont_t` 對應繁體中文（臺灣）字形的假設：以字形比對（`U+9AA8`、`U+76F4` 的筆畫與慣用的臺灣標準字體一致）為依據，屬強推論；採用前以覆蓋檢查加人工看一組樣本確認。

## 3. 字型

| 語言 | 字型來源（hex 檔） | 備註 |
|---|---|---|
| zh-TW | `unifont_t` | 基準語言 |
| zh-CN | `unifont`（預設） | 預設字形的區域假設待樣本確認；缺字時整個建置失敗 |
| ja | `unifont_jp` | |
| ko | `unifont`（預設，含韓文音節區） | |
| en | 不需要 | 關閉疊字 |

建置：`tools/build_font.py --tar <unifont 壓縮檔> --member <hex> --chars <字元來源>... --out <golemfnt>`（Docker 內執行）。字元來源：該語言所有 catalog 的 `translation` 欄，加 `font/<lang>.extra.txt`（手動補的標點與符號）。ASCII `20h` 至 `7Eh` 一律收入。缺任何要求的字就以非零離開；不為遷就缺字而改譯文（`AGENTS.md` §6）。字型檔不進版控，只提交 `font/<lang>.extra.txt` 與 `font/README.md`（來源、版本、雜湊、重建指令）。

字型名稱：`full16-<lang>`（寫入 `Font.Name`，必須非空），`Layer.FontRegistry` 與 `Layer.Restore` 以此名稱換回指標。

字型寬度表：`tools/build_font.py` 依 Unifont hex 的行長決定每個字是全形（32 bytes 位元圖，16 px 寬）或半形（16 bytes，8 px 寬），寫入 GOLEMFNT 每字的 `source` 位元組（bit 7 為 1 是全形，低 7 位元是來源編號，Unifont 為 1）。`xlate.ParseFont` 不解讀該位元組，adapter 以自己的檔頭解析讀出 `wide(r)` 表。`001` §6、`003` §7 與 lint 都查同一張表；沒有收入字型的字元視為缺字。以碼點範圍判定全形並不可靠：本機 Unifont 的 `U+2026`、`U+2460`、`U+2606` 是 16 px 寬。

缺字的執行期處理：`Layer.Draw` 對缺字的 rune 呼叫 `missing`，字模不畫（計入 `missing_glyph`）。發行前 lint 與建置保證 `missing_glyph = 0`。

## 4. 語言通道

每種語言一個通道：`{lang, catalog, font, enabled}`。

- 啟動時載入所有語言的 `text/{ui,prose}.<lang>.tsv` 與字型。某語言載入失敗（檔案缺、lint 失敗、字型缺）只停用該語言，記錄原因，其他語言不受影響。
- 同一個進程同一時間只有一個啟用中的「顯示語言」。`en`：不畫疊字（`Layer.Draw` 不呼叫），事件與 `Layer` 照常維護（§5），所以切回其他語言時畫面立即正確。
- 多語言的 catalog 鍵規則相同（`003` §4）：`ui` 以英文原文為鍵，`prose` 以摘要為鍵；各語言的檔案獨立。
- 新增語言時重跑既有路徑的 A/B（`005`），證明其他語言的輸出不變。

## 5. 即時切換

要求：切換語言後，當下畫面上所有疊字、以及之後被還原的頁面影子（`002` §4）都顯示新語言。

資料結構：

- 每個事件有一筆 `EventRecord`（`001` §3.3：`Format`、`Text`、`Col`、`Row`、`Args`、已擷取的 `%s` 字串、組句關聯）。編號 `g<N>` 作為該事件所有疊字的 `Stamp.Key`；解析只用 `EventRecord`，不再讀原版記憶體，所以語言切換時原版記憶體已變也能重建。
- `records map[string]*EventRecord`：保留被 `Layer` 或 `known` 中任一疊字引用的記錄；每次切換與每 256 個事件掃描一次，移除沒被引用的記錄；上限 4096 筆，超過時最舊的優先移除（移除後該疊字在下次切換時無法重建，改為移除該疊字並計入 `rebuild_lost`）。

切換流程（單執行緒，在 `RunUntil` 返回之間）：

1. 設顯示語言為 `L2`（`en` 以外則記為 `shadowLang`；進入 `en` 時 `shadowLang` 維持原值）。
2. 對 `Layer`：把每個疊字依 `Key` 分組，對每組以 `L2`（`en` 時用 `shadowLang`）重新 `Resolve`（`003`）與排版（`001` §6），以 `Layer.Replace` 換成新疊字，狀態設 `Pending`。
3. 對 `known` 中每一筆快照：還原到暫時的 `Layer`，同上重建，再 `Snapshot` 存回（字型名稱換成新語言）。
4. 重建失敗（記錄不存在、`Resolve` 回 `ok=false`）的疊字：移除，原文顯示；計入 `rebuild_lost`、`untranslated`。
5. 之後新事件一律以 `shadowLang` 解析。

切換不修改原版狀態；切換本身不得改變任何步數時點的記憶體與視訊緩衝區雜湊。

## 6. 譯文的產生

| 語言 | 來源 | 流程 |
|---|---|---|
| zh-TW | 人工與子代理依英文原文翻譯，經 lint | 先寫 `text/glossary.tsv` 的譯名，再批次翻譯（`~/.claude/knowledge-base/workflows/batch-subagent-localization.md`），子代理回收後以檢查工具驗欄數 |
| zh-CN | zh-TW 以 OpenCC `tw2sp` 轉換，加專案詞表覆寫 | 轉換後 lint；詞表 `text/glossary.zh-CN.tsv` 覆寫地區用語 |
| ja、ko | 以英文原文為源的機器翻譯 | 先定各語言詞表再批次進行；README、讀我與發行說明寫明「機器輔助、未經母語者校對」 |

所有譯文檔以 UTF-8 TSV 為唯一正式來源（`003` §3）。專名沿用譯名表一致處理：`text/glossary.tsv` 與 lint（`003` §9）保證整個 catalog 同詞同譯。

## 7. 驗收

1. 單元測試：字型缺字偵測；語言載入失敗只停用該語言；`records` 的建立、引用掃描、淘汰；切換流程在以假 `Layer` 與假 catalog 的組合下的結果（字面期望值）。
2. 同狀態收據：同一路線，對每個語言輸出一組畫面與疊字集合，各語言的原版記憶體與 `B800` 雜湊相同；在 zh-TW 與 zh-CN 之間切換前後，疊字數與位置相同，字面依各自 catalog。
3. 切換收據：在城鎮選單列顯示時切換語言，下一個 `Frame` 後城鎮選單列為新語言；開啟公會選單再關閉（`known` 還原）後，選單列仍為新語言。

## 8. 未決

1. zh-CN 的字形區域：預設 `unifont` 的字形是否符合簡體慣用，樣本確認前不聲稱完成。
2. 日韓專名的處理（音譯、保留英文）與玩家名音譯（`AGENTS.md` §12 待決第 2 項）。
3. 發行授權文字：採 OFL 1.1 還是 GPLv2+ 字型例外，發行前核對 `COPYING` 與 `OFL-1.1.txt` 的實際條文。
