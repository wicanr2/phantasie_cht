# 目前狀態

日期：2026-10-03

- repo 建立（private），尚未寫實作程式。專案規則在 `AGENTS.md`。總目標：用 dosgolem 完成《幽靈戰士》繁體中文化（使用者 2026-10-03 設定）。
- 證據文件：`docs/re/001-input-inventory.md`（輸入清冊）、`002-probe-receipt.md`（dosgolem probe 盤點）、`003-ida-static-survey.md`（常駐映像的 IDA 靜態盤點）、`004-overlay-format.md`（overlay 格式與載入語意）。索引在 `docs/re/README.md`。
- 工作清單在 GitHub Issue（#1 至 #4）。
- 原版壓縮檔解開在 `workplace/orig/`，LZEXE 解壓後映像傾印在 `workplace/probe-out/`，IDA 資料庫與輸出在 `workplace/ida/`，審查報告在 `workplace/review/`，都不進版控。
- dosgolem 開發分支 `phantasie-cht-output-overlay`（本機，無上游，未推送），worktree 在 `workplace/dosgolem`，基底 `2f44a68`（`origin/fix/stubseg-font-collision-program-path`）。已有一個 commit：spec 197（`int 27h`，DRAFT，審查中）。
- 語言範圍：zh-TW、zh-CN、英文原版、ja、ko。沒有手冊。

## 已知事實（摘要，等級與證據見 `docs/re/`）

- `PHANTASI.EXE` 啟動時取 INT 60h 向量，不等於 `49A6:49A6` 就以離開碼 1 結束。三個 `.COM` 是必要的前置步驟。
- 初始視訊模式是 CGA 模式 04h（320×200、四色）。
- 常駐映像與兩個 overlay 都沒有 `INT 10h` 字元輸出。文字由 `0110:25A5`（`printf` 風格，191 個呼叫點）格式化到 `DGROUP:3A36` 後，從 `FONT` 取 8×8 兩位元字模直接寫 `B800`、`BA00`（`docs/re/005`，靜態）。
- overlay 由 `0110:3D0F` 的載入器載入：程式碼讀到 `0110:53EA`、資料讀到 `DGROUP:B8F0`，`ov1` 與 `ov2` 位址相同、互相覆蓋，每次呼叫都重新載入。
- 玩家可見字串至少分布在常駐 `DGROUP`、`OV1` 資料段落、`OV2` 資料段落。`MESS*` 的讀取者與編碼未知。

## 阻擋

dosgolem 沒有實作 `INT 27h`（舊式常駐結束）。三個 `.COM` 無法常駐，`WIZ.BAT` 的序列無法等價重現，動態量測（載入頻率、`B800` 寫入、畫面）都量不到。規格 197 在審查中；READY 之後才實作。

## 下一步

1. 規格 197 審查通過、READY，實作並 CONFORMED。
2. 重跑 `-queue` 序列，做動態量測（Issue #2）。
3. 讀完其餘視訊函式、逐呼叫點盤點格式字串（Issue #3、#4）；設計繪字函式的攔截規格。
