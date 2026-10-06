# 目前狀態

日期：2026-10-06

《幽靈戰士》以 dosgolem 執行期輸出攔截與覆繪中文化，原版程式、資料與存檔規則不修改。語言為繁中、簡中、英文原版、日文與韓文。日韓為機器輔助，未經母語者校對。使用者已授權下載手冊、顯示本機答案、commit／push，並指定抽樣驗收。

目前引擎 `9f1c720af6aa72dc5b7c7bea5a1ed3a574a2a855` 位於 `phantasie-cht-overlay`，加入 F1 五語說明與戰鬥隊員手繪合成。本機正式包固定於專案 `ee22b5fbb1416d663d180cbe0364e1f89bb4bcfd`、引擎 `84676827fea98078d2aad184407703f9648654a2`，本機 tag 為 `v.1.0.0-20261005`。新功能尚未併入既有封包與影片；封包、tag 及六包雜湊保持不變。影片工具的實際版本與雜湊記於本機 `promo/provenance.json`。

| 項目 | 現況 | 證據入口 |
|---|---|---|
| 中文化 | 001 至 012 CONFORMED，限資料契約與正常 UI 代表樣本 | [分期驗收矩陣](docs/goals/001-phases.md#抽樣驗收範圍)、[規格索引](docs/spec/README.md) |
| 三平台交付 | 六包乾淨重建，包含三個本機完整版與三個 OFL 補丁包，版號一致 | [013](docs/spec/013-cross-platform-packaging.md)、交付根層 `SHA256SUMS.json` |
| 倚天字形 | 1269 全形與 95 GNU ASCII；四場景獨立像素遮罩通過，139 個原版狀態點一致 | [014](docs/spec/014-local-eten-font.md)、正式收據 `font-mask/verification.json` |
| 主題與 HD | Shift+F12 切原版、琥珀、手繪；四場景、160 怪物變體已打包，正常城鎮與戰鬥抽驗 | [015](docs/spec/015-presentation-themes.md)、[018](docs/spec/018-all-recognizable-hd-images.md) |
| F1 說明頁 | 五語開關、返回、切語言／主題及全螢幕；Linux 正常 GUI 與原版暫停抽驗通過，未重打包 | [019](docs/spec/019-frontend-help.md)、`workplace/help-r1/` |
| 新版隊員圖像 | 32 個手繪變體完整載入；正常索引 0／bank 1、五語 165 狀態點與獨立像素允許域通過，未重打包 | [020](docs/spec/020-party-hd-images.md)、`workplace/party-hd-r1/` |
| 推廣影片 | 72 秒實際遊玩與主題／五語展示，2160 格、30 fps，第二版原創配樂 | [016](docs/spec/016-gameplay-video-capture.md)、[017](docs/spec/017-original-promo-score.md)、`promo/verification.json` |
| README 截圖 | 標題、城鎮、公會、地牢保留正式包畫面；戰鬥重擷取五語新版隊員、原版主題對照，新增 F1 畫面，無手冊答案 | 正式收據 `readme-formal-screenshots.json`、`workplace/public-readme-screenshots-r1.json` |
| GitHub Issue | #1 至 #4 已補結案證據並關閉，目前未關閉數為 0 | [遠端 Issue](https://github.com/wicanr2/phantasie_cht/issues) |

唯一現行交付根目錄為 `dist-all/v.1.0.0-20261005/`。`full-local/` 含 Linux x86_64 AppImage、Windows amd64 ZIP、macOS universal ZIP，附遊戲、手冊提示、繁中倚天與完整圖像。`patch/` 不含遊戲、答案、倚天或 HD，採 GNU Unifont 17.0.05 的 OFL 1.1。`promo/` 保存成片、第二版母帶、產製工具及完整音色庫條款；`smoke/` 保存抽樣驗收與重播腳本。全部產物留本機，沒有公開 Release。使用者已授權 repo 轉公開；公開範圍為程式、譯文、文件與批准的展示截圖。專案程式授權為 RRSAL-1.0，不涵蓋原版素材。

正式驗收工作區為 `workplace/package-prototype/formal-acceptance-v.1.0.0-20261005/`。Linux 實際完整版已抽測五語標題與城鎮、三主題、公會返回、繁中 15 點存檔／冷讀檔。Windows 實際包已在 Wine 抽測五語標題與手繪城鎮；輸入擷取程序 exit 0，Wine 擁有程序清理達 timeout 124，正常關閉及 Windows 真機未驗證。macOS 核對兩種架構、plist、全部資產，未真機操作。補丁包完成內容與資產核對，沒有另行 GUI 抽測。

正式擷取的城鎮 36、公會 81、戰鬥 33 點與既有原版狀態相同。影片直接解碼審核通過，-18.01 LUFS、-2.41 dBTP，沒有黑幀；靜止區間由相同來源畫面核對。15 段共 75 個來源樣本、17 格成片與 30 份字幕字框抽驗通過。配樂第二版已獲使用者試聽確認，不使用其他版本原版音樂。成片含中途原版英文戰鬥訊息，不宣稱每個執行期瞬間已逐格中文化。

## 文字、資料與證據

- 四語各有 `ui` 678 筆、`prose` 1044 筆，合計 1722 筆，lint 零錯誤。四語的 16 個來源資料缺口已補齊；MESS6:52 已正常抽驗，其餘 15 新鍵未逐鍵量到，見 [026](docs/re/026-recovered-prose-catalog.md)、[027](docs/re/027-dungeon-six-recovered-message.md)。
- 本機 `manual` 各 156 筆。物品及法術提示保留原版選項，由玩家作答。手冊、答案與作答路線只留本機；版控只有無答案標題、工具與合成測試。入口見 [006](docs/spec/006-manual-answer-hints.md)、[手冊來源](docs/re/012-manual-prompts.md)。
- 原始文字掛點、操作、完整記憶體及正常玩家路線證據見 [研究索引](docs/re/README.md)，不以 GUI 圖片取代原版對拍。最新 HD 實作基準見 [029](docs/re/029-all-image-formats.md)。

## 已知限制

- 未逐項驗證：其他地圖描述格、部分 MESS 欄寬與事件、地城備份還原、INT 10h `AH=0Bh BL=1` 與原有文字跨色盤。具體範圍見 002、005、012，抽樣以外不計 UI PASS。
- 中文停用項目不重現原版變暗；數字有原版粗體與疊字細體混用；日韓數字欄位仍有少量 lint 警告。
- HD 的兩個全白變體、未知或遮擋部分保留原版。地圖保留原版。隊員新功能只有索引 0／bank 1 正常路線證據，其餘 31 變體只完成資產與合成契約；個別未正常到達的場景與怪物不宣稱已實機觀察。
- F1 與新版隊員只完成 Linux 原始碼抽驗，不屬既有三平台封包或影片內容。
- 玩家名音譯、公開 Release 與影片公開方式尚未定案。相關 Issue 已依使用者 2026-10-06 授權結案。

本機正式交付保持原版本。公開儲存庫不散布原版遊戲、手冊答案、倚天字模或手繪圖集。
