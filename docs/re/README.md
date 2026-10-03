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

產生清冊的工具是 `tools/inventory.py`，IDA 盤點與 overlay 疊合是 `tools/ida/`，都在 Docker 內執行。研究工作區 `workplace/` 不進版控。
