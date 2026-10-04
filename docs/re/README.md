# docs/re 索引

原版證據、位址、雜湊、實驗與推論等級。保留原始位址與 operand，不以推測名稱覆蓋定位資訊。
證據等級：已證實、強推論、假說、未知。

| 編號 | 檔案 | 內容 |
|---|---|---|
| 001 | `001-input-inventory.md`、`001-input-inventory.tsv` | 輸入清冊：70 個檔案的大小、SHA-256、格式判定、證據等級、來源權利分類 |
| 002 | `002-probe-receipt.md` | dosgolem probe 盤點：三個 `.COM` 與 `PHANTASI.EXE` 的執行結果、LZEXE 解壓後映像、串跑診斷、dosgolem 缺口（`INT 27h`） |
| 003 | `003-ida-static-survey.md` | 常駐映像的 IDA 靜態盤點：INT 60h 檢查、視訊模式 04h、`INT 10h` 包裝、overlay 載入器、與 `AGENTS.md` §2 未知項的對照 |
| 004 | `004-overlay-format.md` | overlay 的檔案格式、常駐載入器語意（程式碼載入 `0110:53EA`、資料載入 `DGROUP:B8F0`）、兩個 overlay 的靜態盤點 |
| 005 | `005-video-and-text-paths.md` | 視訊與文字繪製路徑（靜態）：螢幕幾何、字模格式、繪字函式 `0110:25A5`、螢幕緩衝區函式 |
| 006 | `006-dynamic-receipts.md` | `INT 27h` 補上後的動態證據：啟動鏈、overlay 載入、鍵盤路徑、標題與城鎮與公會的畫面時序、決定性 |
| 007 | `007-message-and-scroll-formats.md` | MESSn 與 SCROLLS.DTX 的解碼、記錄結構、讀取函式與未決事項 |
| 008 | `008-text-and-screen-supplement.md` | 補充證據：組句 sprintf、卷軸與 MESS、頁面操作、變暗、BIOS、格式核心、手冊位置、直接視訊寫入；§10 公會重名及第二條等鍵路徑 |
| 009 | `009-arg-regions-and-composition.md` | `%s` 引數的指標落點與種類（怪物、城鎮、玩家、名冊、緩衝區、位置描述）、`strcat` 追加組句、字模遮罩與粗體字模、單字元事件覆寫靜態字串 |
| 010 | `010-map-description-text.md` | 大地圖描述來源、`DS:C6FA`、特殊格表到描述槽的資料流；OUT1 道路兩行顯示與等鍵限制 |
| 011 | `011-dungeon-location-line.md` | 地城位置列的格式字串指標 `OV2:C400`：區間表的 `buffer@ov2` 列、`-dump-keys` 診斷 |
| 012 | [012 手冊來源與提示事件](012-manual-prompts.md) | 掃描手冊來源、物品及法術提示的原始定位與正常玩家路線 |
| 013 | [013 存檔與冷啟動讀回](013-save-roundtrip.md) | 正常城鎮存檔、冷啟動讀回角色、四語與三種覆繪模式的記憶體及存檔核對 |
| 014 | [014 地牢事件格與訊息視窗](014-dungeon-message-trigger.md) | DNG 事件格到 MESS 索引的資料流、兩行段落及整頁還原、四語 320 點同狀態驗收 |
| 015 | [015 卷軸閱讀](015-scroll-reading.md) | 正常購買與閱讀、卷軸逐行消費端與整行安全範圍 |

產生清冊的工具是 `tools/inventory.py`，IDA 盤點與 overlay 疊合是 `tools/ida/`，都在 Docker 內執行。研究工作區 `workplace/` 不進版控。
