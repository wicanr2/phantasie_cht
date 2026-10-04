# 004 字型與語言通道

狀態：CONFORMED（2026-10-04；驗收收據見 §9；READY 於 2026-10-04；經四輪獨立審查：契約對程式、資料對證據、可實作性、對抗式邊界、一致性、動態證據、確認輪。阻擋項與應改項已修，建議項帶進實作或列入已知限制）。依賴 `001`、`002`、`003`。證據來源：`tools/build_font.py` 與本機 Unifont 17.0.05 的實測。

## 1. 範圍

字型來源與子集建置、語言通道（zh-TW、zh-CN、en、ja、ko）、即時切換語言的重建流程、各語言譯文的產生方式。譯文鍵與格式在 `003`，前端的切換鍵在 `005`。

## 2. 依據

| 事實 | 證據 | 等級 |
|---|---|---|
| 疊字用字型是 `xlate.Font`（檔案格式 GOLEMFNT）：magic、`u16 W`、`u16 H`、`u32` 字數，每字 `u32` 碼點、`u8` 來源、位元圖（每列 `(W+7)/8` bytes，MSB 在左） | `xlate/font.go`，`tools/build_font.py` | 已證實 |
| `xlate.ParseFont` 不保留每字的來源位元組（`xlate/font.go` 註解與實作） | `xlate/font.go:73-100` | 已證實 |
| 繪製時全形字 16×16 佔一個原版格（2 倍畫面），半形字 8×16 佔半格；`Layer.Draw` 對超出格寬的點不畫 | `001` §6、§7；`xlate/layer.go` 的 `drawGlyphs` | 已證實（讀碼） |
| 本機 GNU Unifont 17.0.05（壓縮檔 SHA-256 `f287cffb26e22723aa36e6684869b0f3ff3bfb822c4b01008bd847911ec1b631`）含 `unifont`（預設，57,086 字）、`unifont_t`（57,086 字）、`unifont_jp`（58,925 字）三個 BMP hex 檔，另有 `unifont_upper`。`unifont_t` 與預設在 26,833 個碼點字形不同，`unifont_jp` 與預設在 9,967 個碼點不同；`U+9AA8`、`U+76F4` 兩字的字形在三者之間不同 | 本輪以 Docker 內 Python 比對 hex | 已證實 |
| 授權：壓縮檔內有 `COPYING` 與 `OFL-1.1.txt`；字型以 SIL OFL 1.1 與 GPLv2+ 含字型例外兩種條款之一散布 | 壓縮檔內檔案 | 已證實（檔案存在）；發行時引用的條款文字待核對 |
| Unifont 的 `U+2026`、`U+2460`、`U+2606` 是 16 px 寬（全形），以碼點範圍判定全形不可靠 | `unifont_t` hex 行長（64 個十六進位字元 = 16 px） | 已證實 |

`unifont_t` 對應繁體中文（臺灣）字形的假設：以字形比對（`U+9AA8`、`U+76F4` 的筆畫與慣用的臺灣標準字體一致）為依據，屬強推論；採用前以覆蓋檢查加人工看一組樣本確認。

## 3. 字型

| 語言 | 字型來源（hex 檔） | 備註 |
|---|---|---|
| zh-TW | `unifont_t` | 基準語言 |
| zh-CN | `unifont`（預設） | 預設字形的區域假設待樣本確認；缺字時整個建置失敗 |
| ja | `unifont_jp` | |
| ko | `unifont`（預設，含韓文音節區） | |
| en | 不需要 | 關閉疊字 |

建置：`tools/build_font.py --tar <unifont 壓縮檔> --member <hex> --chars <字元來源>... --out <golemfnt>`（Docker 內執行）。字元來源：該語言所有 catalog 的 `translation` 欄（以 `catalog_lib` 讀取，不用 `csv` 模組，避免引號語意），加 `font/<lang>.extra.txt`（手動補的標點與符號）。ASCII `20h` 至 `7Eh` 一律收入。缺任何要求的字就以非零離開；不為遷就缺字而改譯文（`AGENTS.md` §6）。字型檔不進版控，只提交 `font/<lang>.extra.txt` 與 `font/README.md`（來源、版本、雜湊、重建指令）。

字型名稱：`full16-<lang>`（寫入 `Font.Name`，必須非空），`Layer.FontRegistry` 以此名稱換回指標。

**字型寬度表**：`tools/build_font.py` 依 Unifont hex 的行長決定每個字是全形（32 bytes 位元圖，16 px 寬）或半形（16 bytes，8 px 寬），寫入 GOLEMFNT 每字的 `source` 位元組：bit 7 為 1 是全形，低 7 位元是來源編號（Unifont 為 1）。`xlate.ParseFont` 不解讀該位元組，adapter 以自己的檔頭解析（同一份檔案再讀一次）取得 `wide(r)` 表。`001` §6、`003` §7、lint 與 `tools/prose_build.py` 都查同一張表（lint 對來源 hex 以行長建表，與建置出的字型一致）；沒有收入字型的字元視為缺字。驗收：adapter 測試以含半形與全形字的測試字型確認 `wide` 表；`build_font.py` 的輸出以獨立程式（Go 的 `ParseFont` 加 adapter 解析）重讀核對。

缺字的執行期處理：`Layer.Draw` 對缺字的 rune 呼叫 `missing`，字模不畫（計入 `missing_glyph`）。發行前 lint 與建置保證 `missing_glyph = 0`。

## 4. 語言通道

每種語言一個通道：`{lang, catalog, font, enabled}`。

- 啟動時載入所有語言的 `text/{ui,prose}.<lang>.tsv` 與字型。某語言載入失敗（檔案缺、lint 失敗、字型缺）只停用該語言，記錄原因，其他語言不受影響。
- 同一個進程同一時間只有一個啟用中的「顯示語言」。`en`：不畫疊字（`Layer.Draw` 不呼叫），事件與 `Layer` 照常維護（§5），所以切回其他語言時畫面立即正確。
- **影子語言 `shadowLang`**：事件解析與 `Layer` 維護使用的語言。啟動時設為第一個已啟用的非 `en` 語言（以 `-lang en` 啟動也一樣，所以 `Layer` 從一開始就有內容，之後切到 zh-TW 立即顯示）；顯示語言切到非 `en` 時 `shadowLang` 跟著設為該語言；進入 `en` 時維持原值。所有語言都停用時 `shadowLang` 為空，不維護 `Layer`。
- 多語言的 catalog 鍵規則相同（`003` §4）：`ui` 以英文原文為鍵，`prose` 以摘要為鍵；各語言的檔案獨立。
- 新增語言時重跑既有路徑的 A/B（`005`），證明其他語言的輸出不變。

## 5. 即時切換

要求：切換語言後，當下畫面上所有疊字、以及之後被還原的頁面影子（`002` §4）都顯示新語言。

資料結構：

- 每個事件有一筆 `EventRecord`（`001` §3.3）。編號 `g<N>` 作為該事件所有疊字的 `Stamp.Key`；解析只用 `EventRecord`，不再讀原版記憶體，所以語言切換時原版記憶體已變也能重建。P 類修補（`001` §4）複製記錄成新 `ID`，疊字改用新 `ID`，之後的重建使用新記錄。
- `records map[string]*EventRecord`：保留被 `Layer.Stamps` 的 `Key`，或被 `known` 內任一影子的 `ID` 集合引用的記錄（影子登記時存下它的 `ID` 集合，不需要掃描影子內容，`002` §4）。每次切換與每 256 個事件掃描一次，移除沒被引用的記錄；上限 4096 筆，超過時最舊的優先移除（被移除者之後無法重建：`Layer` 中的疊字移除並計入 `rebuild_lost`，影子條目在還原時略過並計入 `shadow_lost`）。
- 影子是**語言無關**的（`002` §4：只存事件編號與已不可見範圍），切換時不需要重建影子，也不需要字型表。P 類修補（`001` §4）建立新記錄（新 `ID`），舊記錄保持原樣給舊影子引用，所以影子還原得到當時的極性；`records` 的引用掃描涵蓋所有影子引用的 `ID`。

切換流程（單執行緒；不得在事件中途執行）：

1. 設顯示語言為 `L2`，`shadowLang` 依 §4 更新。若此時有開啟中的事件（A 已觸發、B 未觸發），標記 `pendingSwitch`，在該事件的 B 提交完成之後立即執行步驟 2 至 4；否則立即執行。
2. 對 `Layer` 的每個事件組（同 `Key` 的疊字，依該組第一筆疊字在 `Layer.Stamps` 中的出現順序），以 `shadowLang` 重新 `Resolve`（`003`）與排版（`001` §6）：
   - `records[Key]` 不存在：移除該組疊字，計入 `rebuild_lost`（獨立計數，不併入 `untranslated`）。
   - `Resolve` 回 `OK=false`（新語言缺該鍵）：移除該組疊字，原文顯示；計入 `switch_untranslated`。
   - 成功：先以 `hiddenOf(舊記錄, 舊疊字組)` 算出**已不可見範圍** `Hidden`（事件矩形減去現存可見範圍的補集，同 `002` §4，與影子共用同一函式；不由透明格直接換算，否則整段已被移除的疊字範圍遺失而復活）；新疊字每一格若與任一 `Hidden` 範圍相交則設 `Transparent`（全部格都透明的新疊字不加入）；新疊字的 `Y` 沿用舊組的（`Row×8 + DY`，`002` §4；舊組各疊字的 `Y` 不一致就移除該組並計 `rebuild_lost`）；把舊疊字組從 `Layer.Stamps` 移除，新疊字**插在舊組第一筆疊字原本的位置**（保留疊序），`State = Pending`。**不使用 `Layer.Replace`**（它以同原點移除舊疊字且不看 `Key`，會誤刪同原點的另一個事件的仍可見疊字）。
3. 下一個 `Frame` 依當下畫面 `recolor`（`001` §8）並重算指紋。
4. 之後新事件一律以 `shadowLang` 解析。

已知限制：`Resolve` 回 `OK=false` 的事件在舊語言沒有疊字（原文顯示，也不在影子內），切到譯文更完整的語言時畫面上的英文行不會自動補上，影子還原出的畫面也不會有，要等畫面重繪。ja、ko 與 zh-CN 由 zh-TW 的同一組鍵產生，覆蓋範圍相同，實際影響限於缺譯鍵的差異。

切換不修改原版狀態；切換本身不得改變任何步數時點的記憶體與視訊緩衝區雜湊。

## 6. 譯文的產生

| 語言 | 來源 | 流程 |
|---|---|---|
| zh-TW | 人工與子代理依英文原文翻譯，經 lint | 先寫 `text/glossary.tsv` 的譯名，再批次翻譯（`~/.claude/knowledge-base/workflows/batch-subagent-localization.md`），子代理回收後以檢查工具驗欄數 |
| zh-CN | zh-TW 以 OpenCC `tw2sp` 轉換（`tools/derive_zhcn.py`，Docker 映像記錄版本），兩層覆寫：`text/phrases.zh-CN.tsv`（欄：from、to、note；轉換後的全域詞組取代，例：「傳送」被轉成「发送」）與 `text/overrides.zh-CN.tsv`（欄：key、translation；逐鍵覆寫整句） | 轉換後 lint；轉換結果與 `t2s` 的差異抽樣人工檢視 |
| ja、ko | 以英文原文為源的機器翻譯 | 先定各語言詞表再批次進行；README、讀我與發行說明寫明「機器輔助、未經母語者校對」 |

所有譯文檔以 UTF-8 TSV 為唯一正式來源（`003` §3）。專名沿用譯名表一致處理：`text/glossary.tsv` 與 lint（`003` §10）保證整個 catalog 同詞同譯。

## 7. 驗收

1. 單元測試（純 Go，字面期望值）：字型缺字偵測；字型寬度表（含 `U+2026` 的全形判定）；語言載入失敗只停用該語言；`records` 的建立、引用掃描（`Layer` 與影子）、淘汰；`shadowLang` 的啟動值（`-lang en` 啟動後切到 zh-TW）；切換流程在以假 `Layer` 與假 catalog 的組合下的結果：
   - 透明格保留：舊疊字有部分透明格，重建後新疊字覆蓋同一像素範圍的格仍為透明；
   - 疊序保留：兩個事件組，較新的組部分蓋在較舊的組上，重建後順序不變，且較舊組被蓋到的格仍為透明；
   - 同原點兩個事件（較長者被較短者部分覆蓋後仍有可見尾端）：重建其中任一個不會刪掉另一個；
   - `records` 缺失：移除並計入 `rebuild_lost`；`Resolve` 失敗：移除並計入 `switch_untranslated`；
   - 事件中途切換：`pendingSwitch` 在 B 提交之後才執行。
2. 同狀態收據：同一路線，對每個語言輸出一組畫面與疊字集合，各語言的原版記憶體與 `B800` 雜湊相同；在 zh-TW 與 zh-CN 之間切換前後，疊字數與位置相同，字面依各自 catalog。
3. 切換收據（至少三例，且前兩例是部分覆蓋事件，第二輪審查 B-03）：
   - 城鎮選單列顯示時切換語言，下一個 `Frame` 後城鎮選單列為新語言；開啟公會選單再關閉（影子還原）後，選單列仍為新語言。
   - 建立角色的輸入名字畫面，輸入數個字母（單字元事件部分覆蓋輸入列的疊字）後切換語言：切換前後「可見格集合」（各疊字的非透明格換算成像素範圍的聯集）不變，玩家剛輸入的字母不被蓋住。「可見格集合不變」只對切段相同的語言（zh-TW 與 zh-CN）成立；跨 ja、ko 重建時，新格與 `Hidden` 部分相交即整格透明，範圍可能擴大（已知限制），收據改以「玩家剛輸入的字母格仍不被疊字蓋住」為判準。
   - 選項選單切換音效開關符號後再切換語言：標籤為新語言且符號正確。
4. 負對照：把重建改回 `Layer.Replace`，第 1 項同原點測試與第 3 項輸入名字收據應失敗；把 `Hidden` 換算關掉（新疊字不帶 `Transparent`），透明格保留測試應失敗；把 `Hidden` 改回「由現存疊字的透明格換算」，整段已被清除的疊字不復活的測試應失敗（單元測試加：同一事件兩段，`Clear` 把第二段整筆移除後切換語言，第二段的範圍仍不可見）。

## 8. 未決

1. zh-CN 的字形區域：預設 `unifont` 的字形是否符合簡體慣用。2026-10-04 目視抽樣 `lang-options`、`guild`、`map` 的 zh-CN 收據畫面（選項、銀行、神祕客、離開、角色屬性、法術列表）未發現明顯的區域字形差異；未經母語者校對，仍列為待確認。
2. 日韓專名的處理（音譯、保留英文）與玩家名音譯（`AGENTS.md` §12 待決第 2 項）。
3. 發行授權文字：固定 Unifont 17.0.05 的 `COPYING`、`OFL-1.1.txt` 及 `font/Makefile` 作者聲明已核對，雜湊見 [字型來源](../../font/README.md)。字型可採 OFL 1.1 或 GPLv2+ 含字型例外，非字型工具仍依其 GPL 條款；發行所採字型條款待使用者選定，尚未建立發行包。

## 9. 驗收收據（2026-10-04）

環境同 `001` §13.1（引擎 commit `e2513a6`、專案 commit `a0704f5（本節加入前的 HEAD）`）。字型以 `tools/build_fonts.sh` 從 GNU Unifont 17.0.05（zh-TW 用 `unifont_t`、ja 用 `unifont_jp`、zh-CN 與 ko 用 `unifont`）建置，四個語言的字型子集由各自正式譯文重建，缺字即建置失敗。

| 項 | 收據 | 結果 |
|---|---|---|
| 1 單元測試 | `fontwide_test.go`（6 個）、`catalog_test.go`（7 個）、`overlay_test.go` 的語言與切換部分全部 PASS：字型缺字偵測、寬度表（含 `U+2026`）、語言載入失敗只停用該語言、`records` 建立與引用掃描與淘汰、`shadowLang` 啟動值、切換流程（透明格保留、疊序保留、同原點兩個事件、`rebuild_lost`、`switch_untranslated`、`pendingSwitch` 在 B 之後執行） | 通過 |
| 2 同狀態收據 | 13 條路線（`title`、`weapon-list-scroll`、`guild`、`town`、`shops`、`messages`、`town-timed`、`save-load`、`title-items`、`inn-distribute`、`map`、`dungeon`、`combat`）在 zh-TW、zh-CN、ja、ko 各跑一次，同一檢查點的 `steps`、`reads`、`vram_hash`、`mem_hash` 在四個語言之間全部相同；各語言路線全部 PASS。zh-TW 與 zh-CN 之間切換前後可見格集合相同由第 3 項收據判定 | 通過 |
| 3 切換收據 | (a) `lang-switch`：城鎮選單列顯示時切換語言，下一個 `Frame` 後為新語言；開啟再關閉公會選單（影子還原）後選單列仍為新語言，`@assert-visible-same`（可見格集合）與 `@assert-same-screen`（`vram_hash` 與疊字內容）通過；(b) `lang-name`：輸入名字畫面輸入兩個字母後切換 zh-TW、zh-CN、ja、ko，zh-TW 與 zh-CN 的可見格集合不變，ja、ko 以截圖確認玩家輸入的字母格不被疊字蓋住；(c) `lang-options`：音效符號切成 `-` 後切換語言，標籤為新語言、符號正確（`-`、`+`），再切回 zh-TW 後再切符號，8 個檢查點全部 PASS | 通過（三例） |
| 4 負對照 | 突變驗證：語言切換重建改回 `Layer.Replace`（D1a、D1b）、`Hidden` 換算關掉（D2）、`Hidden` 改由透明格換算（D3、D3shared），全部被既有測試抓到；測試名稱含 `TestOverlaySwitchKeepsTransparentCellsAndStackOrder`、`TestOverlaySwitchSameOriginKeepsOtherEvent`、`TestOverlaySwitchHiddenIsNotRevivedByTransparentFlags` | 通過 |

語言範圍：zh-TW（基準）、zh-CN（OpenCC 1.4.2 `tw2sp` 加 `text/phrases.zh-CN.tsv` 與逐鍵覆寫產生）、ja、ko（機器輔助，未經母語者校對）、en（關閉覆繪）。互動前端實機冒煙見 `005` §8。

## 10. 恢復訊息資料的字型重建

[012](012-recovered-prose-catalog.md) 的四語各 16 列資料納入後，按本規格從同一來源重建正式本機字型。繁中、簡中、日文各新增兩個字模，韓文不變；所有舊字模 bytes 相同。四語 lint 錯誤零，既有 UI 警告不變。既有正常寶箱回歸四語畫面與原版狀態相同，詳見 [026](../re/026-recovered-prose-catalog.md)。本規格原有字型契約與發行條款待決保持不變，不能由這次資料測試宣稱新訊息的正常 UI 已完成。
