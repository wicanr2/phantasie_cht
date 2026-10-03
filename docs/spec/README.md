# 規格索引

狀態依 `AGENTS.md` §4：DRAFT、READY、CONFORMED。規格未 READY 不寫實作。審查報告在 `workplace/review/`（不進版控）。

| 編號 | 檔案 | 內容 | 狀態 |
|---|---|---|---|
| 001 | `001-text-overlay-core.md` | `25A5` 繪字事件擷取、分類、版面、疊字產生、字模遮罩定色與診斷 | READY |
| 002 | `002-screen-op-invalidation.md` | 反白、整頁存取（內容定址、語言無關的影子）、視窗清除與捲動、調色盤 | READY |
| 003 | `003-catalog-and-resolve.md` | 譯文檔格式與鍵、`%s` 引數種類、字串解析、格式引擎、lint、靜態列舉、驗收 | READY |
| 004 | `004-fonts-and-languages.md` | 字型與寬度表、語言通道、即時切換語言的重建流程 | READY |
| 005 | `005-play-frontend-and-receipts.md` | 互動前端、無頭收據工具、路線檔、稽核與驗收路線 | READY |

dosgolem 分支 `phantasie-cht-overlay` 的 `docs/spec/250-cga-int10-scroll-and-palette.md`（CGA 的 INT 10h 捲動、清除與色彩選擇）是 `002`、`005` 的前置規格，在該分支審查與實作。

各規格結尾的「實作會改變的既有程式」（`001` §11、`005` §8）列出實作要更動的既有檔案與測試。
