# 規格索引

狀態依 `AGENTS.md` §4：DRAFT、READY、CONFORMED。規格未 READY 不寫實作。審查報告依各規格列出的 `workplace/` 路徑保存，不進版控；013 的報告在 `workplace/package-prototype/`。

| 編號 | 檔案 | 內容 | 狀態 |
|---|---|---|---|
| 001 | `001-text-overlay-core.md` | `25A5` 繪字事件擷取、分類、版面、疊字產生、字模遮罩定色與診斷 | CONFORMED |
| 002 | `002-screen-op-invalidation.md` | 反白、整頁存取、視窗清除與捲動、調色盤 | CONFORMED（§14 抽樣；BL=1、原有文字跨色盤等仍未量到） |
| 003 | `003-catalog-and-resolve.md` | 譯文檔格式與鍵、`%s` 引數種類、字串解析、格式引擎、lint、靜態列舉、驗收 | CONFORMED |
| 004 | `004-fonts-and-languages.md` | 字型與寬度表、語言通道、即時切換語言的重建流程 | CONFORMED |
| 005 | `005-play-frontend-and-receipts.md` | 互動前端、無頭收據工具、路線檔、稽核與驗收路線 | CONFORMED（§21 十類正常路線抽樣；地城備份等仍未量到） |
| 006 | [006-manual-answer-hints.md](006-manual-answer-hints.md) | 依本機手冊表顯示答案，保留原版選項與輸入 | CONFORMED（物品、法術正常路線抽樣） |
| 007 | [007-scroll-row-layout.md](007-scroll-row-layout.md) | 卷軸整行寬度、空行標記與標題置中 | CONFORMED（正常卷軸 8 抽樣） |
| 008 | [008-discarded-key-wait.md](008-discarded-key-wait.md) | 第二條讀鍵路徑、提示停留與確認返回 | CONFORMED（正常提示與既有路線回歸） |
| 009 | [009-short-message-catalog.md](009-short-message-catalog.md) | 已正常到達的短訊息正文、明示匯出及四語驗收 | CONFORMED（MESS5 索引 61 抽樣） |
| 010 | [010-dim-mask-audit.md](010-dim-mask-audit.md) | 已知變暗格的精確遮罩稽核，保留其他像素檢查 | CONFORMED（正常零魔力樣本） |
| 011 | [011-option-stream-parsing.md](011-option-stream-parsing.md) | MESS 正文後的完整選項字元流及索引消費 | CONFORMED（限資料列舉工具） |
| 012 | [012-recovered-prose-catalog.md](012-recovered-prose-catalog.md) | 16 個已確認缺譯鍵的四語資料與正常畫面驗收 | CONFORMED（完整資料契約及按類別抽樣；15 新鍵未逐鍵量到） |
| 013 | [013-cross-platform-packaging.md](013-cross-platform-packaging.md) | 三平台封包、授權、啟動與實際封包驗證 | READY（版號及 OFL 1.1 已定；原契約兩輪複核通過，新增本機倚天變體及正式封包待驗） |
| 014 | [014-local-eten-font.md](014-local-eten-font.md) | 本機繁中倚天字形、OFL 字型與三平台封包隔離 | READY（實際三平台布局、109 組正常狀態及 34 項測試通過；獨立像素遮罩與正式交付待驗） |
| 015 | [015-presentation-themes.md](015-presentation-themes.md) | 色盤主題、手繪城鎮圖像、原版視窗遮蔽與本機資產隔離 | READY（兩輪唯讀審查通過，實作與正式交付待驗） |
| 016 | [016-gameplay-video-capture.md](016-gameplay-video-capture.md) | 實際遊玩逐格擷取、主題與語言展示及本機推廣影片 | READY（兩輪審查通過，錄影與影片待驗） |
| 017 | [017-original-promo-score.md](017-original-promo-score.md) | 原創影片配樂、MIDI／音色庫來源與音訊驗收 | CONFORMED（第二版技術審查與使用者試聽確認；影片待驗） |
| 018 | [018-all-recognizable-hd-images.md](018-all-recognizable-hd-images.md) | 可辨識場景、80×2 怪物圖像及本機封包資產身份 | READY（契約與證據兩輪複核閉合；完整組整合中） |

各規格結尾的「驗收收據」記錄每個驗收項的證據、結果與未量到的項目。

dosgolem 分支 `phantasie-cht-overlay` 的 `docs/spec/250-cga-int10-scroll-and-palette.md`（CGA 的 INT 10h 捲動、清除與色彩選擇）是 `002`、`005` 的前置規格，已 CONFORMED。

各規格結尾的「實作會改變的既有程式」（`001` §11、`005` §8）列出實作要更動的既有檔案與測試。
