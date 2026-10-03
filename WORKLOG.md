# 工作紀錄

## 2026-10-03：建立專案

- 以《拯救地球》的經驗寫成 `AGENTS.md`（模板 `~/cht/AGENTS_DOSGOLEM_CHT.md`）。使用者定案：repo `wicanr2/phantasie_cht`（private）、語言與《拯救地球》相同（zh-TW、zh-CN、英文原版、ja、ko）、沒有手冊。
- 讀原版壓縮檔得到初步觀察（WizardWorks 1990 bonus edition v1.1、`PHANTASI.EXE` 疑似 LZEXE 0.90、`WIZ.BAT` 先跑三個 `.COM`、dosgolem 已有 CGA 模式 4 讀取），記在 `AGENTS.md` §2。

## 2026-10-03：輸入清冊

- 以 `tools/inventory.py`（Docker、`python:3.13-bookworm`）解開並雜湊 70 個檔案，產出 `docs/re/001-input-inventory.md` 與 `.tsv`。大小、雜湊與 `AGENTS.md` §2 一致，無勘誤。
- 新增觀察：`WIZ-MAIN.BSV` 是 BSAVE 影像（段 `B800`、長度 4,000），指向 80×25 文字模式畫面；`M1.COM`、`M2.COM` 的條件跳躍是 JZ，與 `R32768.COM` 的 JNZ 不同。
- 使用者定案：dosgolem 分支從 `origin/fix/stubseg-font-collision-program-path` 開（origin/main 缺 spec 194 至 196，本機 main 有 8 個 commit 尚未進 origin/main，只存在於已推送的該修正分支）；本機每步驟 commit、push 另問；本輪範圍含 IDA 靜態反組譯。
