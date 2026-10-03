# 目前狀態

日期：2026-10-03

總目標：用 dosgolem 完成《幽靈戰士》繁體中文化（使用者 2026-10-03 設定）。語言範圍：zh-TW（基準）、zh-CN、英文原版（關閉覆繪）、ja、ko。沒有手冊。專案規則在 `AGENTS.md`。

## 已有

- 證據：`docs/re/001` 至 `008`（輸入清冊、probe 收據、IDA 靜態盤點、overlay 格式、視訊與文字路徑、動態收據、MESS 與 SCROLLS 格式、補充證據）。索引在 `docs/re/README.md`。
- 規格（`docs/spec/`）：001 繪字事件與疊字核心、002 畫面操作與失效、003 catalog 與解析、004 字型與語言、005 前端與驗收。第二版，DRAFT，第二輪審查中。狀態表在 `docs/spec/README.md`。
- dosgolem 分支 `phantasie-cht-overlay`（worktree `workplace/dosgolem-fw`，基底為疊字框架分支，本機無上游、未推送）：規格 197（`int 27h`，CONFORMED）、規格 243（CGA 圖形模式的 INT 10h 捲動、清除與調色盤選擇，DRAFT，審查中）、`apps/phantasie/`（啟動鏈、繪字與 sprintf 擷取、鍵閘、證據探針 `cmd/textlog`、證據原型 `cmd/overlay-prototype`）。
- 譯文：`text/ui.zh-TW.tsv`（632 筆，lint 0 錯誤）、`text/glossary.tsv`、`text/STYLE.md`。prose 家族（MESS 與 SCROLLS，約 404 單位、926 行）翻譯中。
- 工具（Docker 內執行）：`tools/gamedata.py`（MESS、SCROLLS 解碼與列舉）、`enumerate_text.py`、`harvest_events.py`、`ui_candidates.py`、`ui_prune.py`、`ui_build.py`、`prose_export.py`、`prose_build.py`、`lint_catalog.py`、`catalog_lib.py`、`build_font.py`、`ida/`。

## 已知事實（摘要，等級與證據見 `docs/re/`）

- 文字全經 `0110:25A5`（`printf` 風格）；視窗框線是單字元事件；組句先走 `sprintf`（`3E35`）進 `DS:638E`。
- 畫面操作：反白（`0672`）、頁面緩衝區（`0D30` 螢幕到緩衝區 1、`0CF0` 與 `0D10` 回螢幕、`0D50` 緩衝區 1 到 2）、視窗清除與捲動（BIOS `AH=06h`）。dosgolem 目前不執行 `AH=06h`，要先有規格 243。
- 反白需要重取色：證據原型截圖證明（開啟時被反白的項目維持中文，關閉時回到英文）。
- 遊戲含 4 個手冊對照提示字串（OV2 入口函式內，隨機條件）。沒有手冊；依 `AGENTS.md` §1：維持原文、不翻譯、不作答、到達時回報使用者。隨機路線（約 4000 鍵 × 多條）進入地牢與戰鬥，未觸發。

## 阻擋與待決

- 規格 243 與 001 至 005 通過審查（READY）之前不寫實作。
- 發行字型授權文字（OFL 1.1 或 GPLv2+ 字型例外）待核對。
- 玩家名音譯（ja、ko）、同一英文在不同畫面需不同譯文、MESS 選項與短訊息的事件形式：見規格未決段。
- 本機 commit 尚未推送：phantasie 主分支領先 origin；dosgolem 分支無上游。推送逐項授權。

## 下一步

1. 第二輪審查結果修訂規格，升 READY。
2. 規格 243 實作（dosgolem 通用層），再實作 `apps/phantasie` 疊字核心、畫面操作、catalog 載入、格式引擎、語言切換、前端與收據工具。
3. prose 譯文合併、lint；zh-CN 以 OpenCC 轉換；ja、ko 機器翻譯（標註未經母語者校對）。
4. 路線與同狀態收據，覆蓋清單，發行打包。
