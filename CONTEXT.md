# 目前狀態

日期：2026-10-03

- repo 建立（private），尚未寫任何規格或實作程式。專案規則在 `AGENTS.md`。
- 證據文件：`docs/re/001-input-inventory.md`（輸入清冊）、`002-probe-receipt.md`（dosgolem probe 盤點）、`003-ida-static-survey.md`（常駐映像的 IDA 靜態盤點）。索引在 `docs/re/README.md`。
- 原版壓縮檔解開在 `workplace/orig/`，LZEXE 解壓後映像傾印在 `workplace/probe-out/`，IDA 資料庫與輸出在 `workplace/ida/`，都不進版控。
- dosgolem 開發分支 `phantasie-cht-output-overlay` 已建立（本機，無上游，未推送），worktree 在 `workplace/dosgolem`，基底 `2f44a68`（`origin/fix/stubseg-font-collision-program-path`）。沒有任何程式修改。
- 語言範圍：zh-TW、zh-CN、英文原版、ja、ko。沒有手冊。

## 已知事實（摘要，等級與證據見 `docs/re/`）

- `PHANTASI.EXE` 啟動時取 INT 60h 向量，不等於 `49A6:49A6` 就以離開碼 1 結束。三個 `.COM` 是必要的前置步驟。
- 初始視訊模式是 CGA 模式 04h（320×200、四色）。
- 常駐映像沒有 `INT 10h` 字元輸出；文字繪製路徑的假說是程式直接寫 `B800`。
- overlay 由 `0110:3D0F` 的載入器以名稱 `ov1`、`ov2` 加 `.ovr` 載入，載入位址未知。
- 常駐映像的資料段內嵌英文字串。`MESS*` 的讀取者與編碼未知。

## 阻擋

dosgolem 沒有實作 `INT 27h`（舊式常駐結束）。三個 `.COM` 無法常駐，`WIZ.BAT` 的序列無法等價重現，overlay 位址、畫面內容與 `B800` 寫入都量不到。需要在 dosgolem 分支內先寫規格（通用層），經兩輪獨立審查成為 READY 才能實作。語意參考 DOSBox-X `src/dos/dos.cpp:3293`（`DOS_27Handler`）。

## 下一步

1. 寫 `INT 27h` 規格（DRAFT），送審。
2. 規格 READY 並實作、CONFORMED 後，重跑 `-queue` 序列，量 overlay 載入位址、`B800` 寫入與畫面。
3. 擴大 IDA 覆蓋：對 `OV1.OVR`、`OV2.OVR` 建庫，補程式碼區未分析的部分。
