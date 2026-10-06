# 019 F1 操作說明頁

狀態：CONFORMED（原始碼及新版正式封包抽樣；Windows Wine 輔助、macOS 靜態驗證）。前置：005、015 CONFORMED。使用者 2026-10-06 要求 F1 說明頁；本規格只改前端顯示與保留鍵，不改原版程式、記憶體、規則或存檔。

兩輪唯讀規格審查及兩輪實作審查已通過，阻擋、應改與建議皆為 0。契約與證據報告為 `workplace/help-r1/contract-review.txt`、`evidence-review.txt`、`implementation-contract-review.txt`、`implementation-evidence-review.txt`。實作提交為引擎 `9f1c720af6aa72dc5b7c7bea5a1ed3a574a2a855`，驗收範圍見 §6。

## 1. 證據與變更範圍

| 事實 | 等級與來源 |
|---|---|
| 前端目前將 F1 排進 KeyGate，F11 全螢幕、F12 切語言、Shift+F12 切主題 | 已證實；引擎 `8467682` 的 `apps/phantasie/cmd/phantasie-play/main.go`，SHA-256 `a3b14e2a04218e4366c0f66c5bcb23fb1fcb2258a0cc081313cb0a61a6f4fd0a` |
| 原版按鍵透過 KeyGate 送入讀鍵入口 | 已證實；005 §2、§3，映像偏移 `img:37C2`、`img:37FA` 與第二等鍵 `img:37A0`、`img:37B8`、`img:37C1`；原版輸入雜湊沿用 001 |
| 方向鍵與 Enter 可操作原版選單，字母與數字按畫面提示輸入 | 已證實；005 正常 title-items、town、guild、map 路線及公開 `tests/routes/` |
| F1 原版用途沒有獨立語意結論 | 未知；不宣稱原版未使用 F1。使用者本次指定將它保留給前端說明 |

本規格覆蓋 005 §3、015 §2 的 F1 傳送規則。F2 至 F10 維持原版鍵。頁面只列已證實快捷鍵與畫面提示的操作方式，不提供推測規則、手冊答案、存檔快捷鍵或自動作答。

## 2. 狀態與輸入

前端有關閉、開啟兩態。F1 開啟；開啟時 F1 或 Esc 關閉。每次開閉所在的 Update 都不排原版鍵、不呼叫 `Oracle.Run`。開啟期間所有其他原版按鍵與文字輸入丟棄，不累積到關閉後；原有 Gate 佇列保留，不清空也不改寫。F11、F12、Shift+F12 繼續只作用於前端。

Help 開啟期間 Draw 不呼叫 Session.Frame，也不改覆繪 Layer。先畫獨立的 640×400 說明畫布。F12 改目前語言，畫布以目前語言即時重繪；Shift+F12 切前端主題，說明畫布色彩使用琥珀或一般配色。關閉後從相同原版位置繼續，不送 F1/Esc。

## 3. 文字、字型與邊界

唯一正式來源為 `text/help.<lang>.tsv`，五語 zh-TW、zh-CN、en、ja、ko，key、translation、source 三欄。固定 12 個 key：title、pause、open、close、language、theme、fullscreen、arrows、confirm、letters、context、footer。英語 source 是前端新寫說明，不是原版全文。日韓標為機器輔助、未經母語者校對。

載入時拒絕非 UTF-8、重複或未知 key、缺 key、欄數錯誤、控制碼、空譯文、超過 72 KiB 的檔案。每行量測半形 8、全形 16 像素，限 576 像素；全頁使用 16 像素字高與 26 像素行距，最末列不超過 y=366。左右留 32 像素。使用相應語言已載入的 16×16 GOLEMFNT 與寬度表，逐字驗完整 32 bytes 字模。English 使用全形表以外的 ASCII；英語頁拒絕非 ASCII。

缺檔、壞表或缺字時不畫不完整的當語頁，stderr 明示語言與原因，畫面明示英文回退。回退用已驗證 English TSV 的 ASCII 說明與 Ebitengine 內建 ASCII 字形。English TSV 也無效時顯示固定失敗訊息 `Help unavailable. F1 / Esc: close.`。錯誤只影響說明頁，不停用遊戲語言。原版與公開補丁都需包含五張表；字型工具重建時納入 help 表，不能改說明措辭遷就缺字。

## 4. 驗收

先兩輪唯讀審查契約對程式、資料對證據，無阻擋／應改才 READY。DRAFT 的可丟棄 prototype 只留 `workplace/help-r1/`。

- 表解析與字型完整性測試含缺 key、重複 key、非 UTF-8、超寬、缺字的負例，英文回退須可見。
- 正常 Xvfb GUI 从原版標題及進城開 F1，五語畫面完整，F12、Shift+F12、F11 可用，F1/Esc 返回；開啟時方向鍵、Enter 與字母不流入原版。
- 真實 Session 記錄開閉與至少 120 次模態 Update 前後原版步數、讀鍵、Gate Pending、完整記憶體與 VRAM 摘要相同；關閉後按正常方向鍵可繼續。
- 負對照在乾淨匯出中移除模態阻擋，重跑相同測試必須因步數／輸入改變失敗；原版畫面恢復要以獨立 PNG 比較確認。
- 紀錄實際程式、表、字型、原版雜湊、Docker／Go 版本與輸出。Linux GUI 抽驗不宣稱 Windows/macOS 真機通過。本次不覆寫既有 `v.1.0.0-20261005` 封包或 tag。

驗收收據保存 `workplace/help-r1/`。主代理將本規格掛入規格索引並更新 README／CONTEXT 現況。

## 5. 向後相容與工具鏈

既有表或封包沒有 help family 時仍能啟動；F1 明示英文回退或最小失敗訊息。封装來源只有在五語 help 表全部不存在時接受舊布局；存在任一張時必須五張齊全且正確。`tools/package_text.py` 收錄五張，`tools/package_files.py` 的清冊與必要字元核對依實際 help 是否存在；`tools/package_stage.py` 重建四語字型時加入對應 help。English 表只需 ASCII，使用內建 ASCII 字形，不新增 en 字型。

`tools/build_fonts.sh` 的字元輸入加入存在的 help 表。新建測試輸入包含五張 Help 的 stage 必須全部必要表入清冊；移除一張或缺一個字的負例須失敗。這不改寫舊正式封包的必要資產集合與雜湊。可丟棄查證入口 `workplace/help-r1/prototype.py`，輸出 `prototype.json` 已找到舊字型缺字，正式落地前需重建四語字型。

## 6. 本機實作驗證

實作位於 `apps/phantasie/cmd/phantasie-play/main.go`、`help.go`、`help_test.go`。`Update` 蒐集鍵盤後呼叫共用 `tick`；F1 不再進入 namedKeys。Help 開啟時 `Draw` 直接繪說明畫布，不呼叫 Session.Frame。

`workplace/help-r1/provenance.json` 記錄基底引擎 `8467682`、專案 `dc88016`、本輪未提交的實作檔案雜湊、二進位、原版 70 檔、字型、工具版本與證據。二進位 `workplace/help-r1/phantasie-play` SHA-256 為 `d029ebdc78fc302d522d4184baa927c7d3dabd0d4907b4f1c085e6d77c8606e5`。本輪驗證是 Linux 原始碼建置，未重打包。

| 抽樣 | 證據與結果 |
|---|---|
| 解析與原版唯讀 | `go-tests.log` 五個測試 PASS；`freeze.json` 記錄真實 Session 的 120 次模態 Update。完整 1 MiB 記憶體、VRAM、步數、讀鍵、Gate 佇列及送鍵數不變。開閉所在 Update 同樣不動原版，原先預排的 Down 保留，關閉後正常送出 |
| 負對照 | `negative.py` 在乾淨原始碼匯出將模態 early-return 恰好一處移除；`negative.log` 第 0 次 Update 因步數、輸入、記憶體與 VRAM 改變失敗，`negative-verification.json` 記錄被拒絕 |
| 正常 GUI | `gui.py` 使用 Xvfb 與 xdotool，逐張核對視窗標題的語言／主題。五語 F1、F12、Shift+F12、F11、Esc 與 F1 關閉均通過。Help 內輸入 Down、Enter、x 後，標題與城鎮返回畫面解碼像素差皆 0，見 `gui-verification.json` |
| 字型與缺字回退 | 新 GNU 字型四語完整覆蓋；本機繁中倚天 1277 全形與 95 GNU ASCII，SHA-256 `7fd1f6298d5d906d477380a1f59090e1f52d8309fa400f2a9418049671eaf826`，來源見 `eten-fonts/eten-source.json`。舊正式字型缺 Help 字模時，GUI 顯示英文回退標示及完整英文頁，stderr 診斷，遊戲仍可啟動 |
| 工具鏈 | 既有封裝 28 測試與初版 Help 三測試 PASS；最終定向 `package-help-tests.log` 四測試 PASS，包含 translation/source 的 U+0085 控制碼、五語表必要清冊、缺字拒絕，以及只由 Help 引入的新字確實重烘 |
| 版面 | 實際新字型量測最大寬度繁中 240、簡中 256、英語保守估計 384、日語 384、韓語 400 像素，全部低於 576。五語 GUI、琥珀、全螢幕及英文回退逐張目視，無缺字或裁切。English 內建 ASCII 以較窄字形繪製，8 像素為驗證上界 |

驗證限制：只做 Linux Xvfb 原始碼建置抽樣，未宣稱 Windows 或 macOS 真機通過；舊 `v.1.0.0-20261005` 六包及 tag 保持不變，不含本輪 F1 新功能。日韓說明為機器輔助、未經母語者校對。

## 7. 新版正式封包抽樣

`v.1.0.1-20261006` 的六包已納入五語 Help。實際 Linux 完整版及 Windows ZIP／Wine 均開啟五語 F1，按 Esc 返回標題的像素差為 0；城鎮 F1／F1 返回及 Linux 三主題也通過。五語 Help、標題及手繪城鎮的 Linux／Wine PNG bytes 相同。macOS 實際 ZIP 核對五張表、四語字型及雙架構，不宣稱真機 GUI 通過。完整收據在新版正式驗收工作區的 `gui/verification.json`、`windows/verification.json`，交付與平台限制見 013 新版節。舊版六包保持不變。
