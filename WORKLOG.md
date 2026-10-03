# 工作紀錄

## 2026-10-03：建立專案

- 以《拯救地球》的經驗寫成 `AGENTS.md`（模板 `~/cht/AGENTS_DOSGOLEM_CHT.md`）。使用者定案：repo `wicanr2/phantasie_cht`（private）、語言與《拯救地球》相同（zh-TW、zh-CN、英文原版、ja、ko）、沒有手冊。
- 讀原版壓縮檔得到初步觀察（WizardWorks 1990 bonus edition v1.1、`PHANTASI.EXE` 疑似 LZEXE 0.90、`WIZ.BAT` 先跑三個 `.COM`、dosgolem 已有 CGA 模式 4 讀取），記在 `AGENTS.md` §2。

## 2026-10-03：輸入清冊

- 以 `tools/inventory.py`（Docker、`python:3.13-bookworm`）解開並雜湊 70 個檔案，產出 `docs/re/001-input-inventory.md` 與 `.tsv`。大小、雜湊與 `AGENTS.md` §2 一致，無勘誤。
- 新增觀察：`WIZ-MAIN.BSV` 是 BSAVE 影像（段 `B800`、長度 4,000），指向 80×25 文字模式畫面；`M1.COM`、`M2.COM` 的條件跳躍是 JZ，與 `R32768.COM` 的 JNZ 不同。
- 使用者定案：dosgolem 分支從 `origin/fix/stubseg-font-collision-program-path` 開（origin/main 缺 spec 194 至 196，本機 main 有 8 個 commit 尚未進 origin/main，只存在於已推送的該修正分支）；本機每步驟 commit、push 另問；本輪範圍含 IDA 靜態反組譯。

## 2026-10-03：probe 盤點與 IDA 靜態盤點

- 建立 dosgolem worktree `workplace/dosgolem`，分支 `phantasie-cht-output-overlay`（`--no-track`），基底 `2f44a68`。原 dosgolem checkout 有他人未提交的 `cmd/probe/main.go` 修改，未觸碰。
- 單跑三個 `.COM` 與 `PHANTASI.EXE`：`R32768.COM` 以 `INT 27h` 收尾而 dosgolem 未實作；`PHANTASI.EXE` 在 INT 60h 檢查後以離開碼 1 結束，視訊模式維持 03h。結果見 `docs/re/002-probe-receipt.md`。
- 傾印 LZEXE 解壓後映像（117,232 bytes，兩次執行雜湊相同），以 IDA 9.4 靜態盤點。IDA 的預設 DS 必須設為 DGROUP `0DAF`，否則 `main` 不會被解碼。結果見 `docs/re/003-ida-static-survey.md`。
- `-queue` 串跑可以走到 `PHANTASI.EXE` 並切到模式 04h，但 `.COM` 沒有常駐，`IBMCOVER` 被讀到 `PHANTASI.EXE` 自己的 PSP 上，之後的觀察一律無效，已在 `002` 標明。
- 工具腳本：`tools/ida/ida.sh`（巢狀掛載目標先由本人建立，避免 dockerd 以 root 建出空目錄）、`tools/ida/export_survey.py`。
