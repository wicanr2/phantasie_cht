# 012 手冊來源與提示事件

日期：2026-10-04。使用者授權下載手冊並在題目畫面顯示答案。答案與原始掃描只留本機。

## 手冊

下載來源為 Museum of Computer Adventure Game History 保存的發行商掃描。工具：Python 3.13、Poppler 25.12.0，皆在 Docker 內執行。檔案在 `workplace/manual/`；擷取文字與核對頁圖在 `workplace/manual-derived/`。

| 檔案與來源 | SHA-256 | 用途 |
|---|---|---|
| [phant2-manual.pdf](https://www.mocagh.org/ssi/phant2-manual.pdf) | `7c5999dd099c1c72e7b91673e478d2133c37b49a932c51599fe38eb85163f9ed` | Phantasie I and II 合訂手冊。PDF 第 10 頁為印刷頁 15、16 的物品表，第 17 頁為封底法術表；符合遊戲提示 |
| [phantasie-manual.pdf](https://www.mocagh.org/ssi/phantasie-manual.pdf) | `ddc192cc105b8073ffe5bb016b14902e184cd0e6140460e1c58c29f50194abe8` | 初版手冊，物品表印刷頁 17、18；用來交叉核對表格 |
| [phantasiebonus-alt-phantasie-manual.pdf](https://www.mocagh.org/ssi/phantasiebonus-alt-phantasie-manual.pdf) | `f8e128b3790a616643a9dff91b45d40e7bb726139da4f30e1235ea11935fcabf` | Wizardware 重發版 IBM 操作說明；編排不同，不能只按題目頁碼套用 |

權利分類：第三方原版掃描，本機研究輸入，未取得再散布授權。頁碼與表格位置經人工檢視，等級為已證實。

## 原版程式

- 原版壓縮 EXE SHA-256：`0f00a1af62cfcc383b4ca2e4382321f357063ba1457081da6edca4eb9f28e716`。
- IDA 9.4，輸入 `ov2_composed.bin` SHA-256：`f461da5fb4e02634ab47dcbd8af3f5b7ae53c49d00ad42f5f56fcae765121422`。
- 正式 `ov2.i64` 唯讀，複製到容器 `/tmp` 後匯出。最小探針驗證版本、251 個函式與輸入雜湊。證據：`workplace/manual-derived/ida-prompt.json`。
- IDA 線性位址以 `1100h` 為載入基址；下表的執行期欄是 image segment 內的偏移，不是 IDA 線性位址。

| 用途 | IDA call 與 bytes | 執行期返回偏移 | DGROUP 格式字串偏移 | 欄、列 |
|---|---|---|---|---|
| 物品題首行 | `C892: E8 10 6E` | `B795` | `C1BC` | 0、10 |
| 物品題次行 | `C8B1: E8 F1 6D` | `B7B4` | `C1DB` | 0、11 |
| 法術題首行 | `C945: E8 5D 6D` | `B848` | `C1F3` | 0、10 |
| 法術題次行 | `C95E: E8 44 6D` | `B861` | `C204` | 0、11 |

等級：已證實的靜態控制流。`sub_C7C4` 的四個呼叫都走既有 `sub_36A5` 繪字路徑。選項由另外兩個呼叫輸出在欄 5、列 13／15／17。作答端 `C9C5`、`C9D0` 比較 ASCII `1` 至 `3`，因此畫面需要保留三個選項。提示只顯示手冊答案，玩家依選項按鍵。

本機資料表依手冊編號核對，原版名稱表僅作畫面縮寫、羅馬數字與 catalog 鍵的對照，不以程式內正解索引取代手冊。`manual-name-review.tsv` 的 `ptr` 是 DGROUP 內的近指標偏移。未量到的動態分支不宣稱驗收通過。

## 動態證據

Claude 已有收據：`workplace/receipts/cb5/cb5.zh-TW.on-all.tsv`，路線 `workplace/explore-main/cb5.route` 的 `r7s1` 首次顯示物品題，`protected=2`。

本次以 dosgolem `e2513a6`、Go 1.24 容器重跑相同路線至 `r7s1`，原始路線只截短末段，未修改原版狀態。`workplace/manual-derived/probe-item.log` 的兩筆完整 `EventRecord` 確認 overlay 恰為 `ov2`，物品兩列的 Caller、FmtPtr、座標、KindStatic 與上表相符。首行事件步數 `1898957055`，次行 `1898968448`，檢查點 `1909652292`。

從同一路線輸入錯誤選項後，原版重試顯示法術題。`probe-retry.log` 記錄首行事件步數 `1909662019`、次行 `1909674464`，兩個事件的完整辨識條件與上表相符。物品與法術路徑均為動態已證實；這只覆蓋本次抽樣題目，不代表 154 題皆已逐題執行。

已人工檢視 `items.png`、`spells.png`，核對 100 個物品與 54 個法術的名稱／編號。兩輪獨立審查確認表格完整性；法術名稱的數字等級與畫面羅馬數字、兩筆拼寫或縮寫差異記在 `manual-name-review.tsv`。`answers.tsv` 是供 builder 使用的本機三欄輸入。

後續規格：[006 手冊答案提示](../spec/006-manual-answer-hints.md)。
