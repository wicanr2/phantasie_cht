# 目前狀態

日期：2026-10-03

- repo 建立（private），尚未寫任何規格或實作程式。專案規則在 `AGENTS.md`。
- 輸入清冊已建立：`docs/re/001-input-inventory.md`（70 個檔案、365,982 bytes，與 `AGENTS.md` §2 一致）。原版壓縮檔解開在 `workplace/orig/`，不進版控。
- `AGENTS.md` §2 的七個未知項尚未回答。
- 語言範圍：zh-TW、zh-CN、英文原版、ja、ko。沒有手冊。
- dosgolem 開發分支 `phantasie-cht-output-overlay` 尚未建立。使用者定案（2026-10-03）從 `origin/fix/stubseg-font-collision-program-path`（`2f44a68`）開，worktree 放 `workplace/dosgolem`。

下一步：以 `cmd/probe` 盤點 dosgolem 對 `.COM` 啟動序列、LZEXE 壓縮檔、overlay 與視訊模式的支援，再以 IDA 對解壓後映像做靜態反組譯。
