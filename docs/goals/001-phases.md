# 分期目標

範圍與退出條件。逐項工作在 GitHub Issue，不在這裡重複。證據閘門與「已中文化」的定義見 `AGENTS.md` §4、§11。

## 第一期：zh-TW 輸出覆繪

範圍：`PHANTASI.EXE` 的玩家可見文字（經 `0110:25A5` 繪出者）以繁體中文覆繪，原版程式、資料與存檔不變。涵蓋 `docs/spec/001` 至 `011` 與 dosgolem 規格 `250-cga-int10-scroll-and-palette`、`251-oracle-step-guard`。

退出條件：

1. 規格 001 至 011 為 CONFORMED：玩家輸出規格有同狀態收據；011 的資料列舉工具有獨立原版 bytes 核對。各規格的必要測試與負對照通過，不能以工具完成替代正常 UI 驗收。
2. `docs/spec/005` §6 的必備路線都有收據（`@check` 加 `@expect`），`stale_cells`、`exposed_events` 為 0 或在已知清單內；到不了的畫面記錄原因與條件。
3. 靜態字串 `ui` 全部有譯文（`lint --sources --harvest` 無缺譯）；MESS 與 SCROLLS 的 `prose` 全部有譯文；已知缺口（位置描述文字等）在 Issue 與 `docs/spec/003` §12 列明。
4. 手冊提示依使用者授權與 [規格 006](../spec/006-manual-answer-hints.md) 顯示答案，保留原版選項、玩家輸入與判定。物品題、法術題、語言切換與返回清除須有正常玩家路線及同狀態收據。手冊、答案表與作答路線只留本機，不加入版控或公開發行包。

## 第二期：多語言

範圍：zh-CN、ja、ko 與英文原版（關閉覆繪）的即時切換。

退出條件：各語言的 catalog 通過 lint；字型與寬度表通過驗收；切換收據（`docs/spec/004` §7）；zh-CN 以 OpenCC 加詞組與逐鍵覆寫產生；ja、ko 為機器輔助，說明未經母語者校對。

## 第三期：發行

範圍：遊玩前端 `cmd/phantasie-play`、無頭收據工具、打包。

退出條件：發行包不含原版檔案、不可散布字型與手冊摘錄（外洩掃描）；`LICENSE`（RRSAL-1.0）隨包；每個語言用發行包實機看標題畫面與主選單；Release 說明照實寫已知限制。轉公開與公開 Release 需要使用者額外授權。
