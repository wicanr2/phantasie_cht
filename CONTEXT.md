# 目前狀態

日期：2026-10-06

《幽靈戰士》以 dosgolem 執行期輸出攔截與覆繪中文化，原版程式、資料與存檔規則不修改。語言為繁中、簡中、英文原版、日文與韓文。日韓為機器輔助，未經母語者校對。使用者已授權下載手冊、顯示本機答案、commit／push，並指定抽樣驗收。

目前引擎 `9f1c720af6aa72dc5b7c7bea5a1ed3a574a2a855` 已推送至 `phantasie-cht-overlay`，F1 五語說明與隊員手繪合成已納入三平台本機完整版。本機正式包與新版影片固定於專案 `5518f9947973911d8fe57140a42d542af9adffd5`、上述引擎及本機 tag `v.1.0.1-20261006`。來源、工具與雜湊記在交付清冊及 `promo/provenance.json`；後續文件提交不移動 tag。舊 `v.1.0.0-20261005` 六包與影片保持不變。

| 項目 | 現況 | 證據入口 |
|---|---|---|
| 中文化 | 001 至 012 CONFORMED，限資料契約與正常 UI 代表樣本 | [分期驗收矩陣](docs/goals/001-phases.md#抽樣驗收範圍)、[規格索引](docs/spec/README.md) |
| 三平台交付 | 六包乾淨重建，包含三個本機完整版與三個 OFL 補丁包，版號一致 | [013](docs/spec/013-cross-platform-packaging.md)、交付根層 `SHA256SUMS.json` |
| 倚天字形 | 1277 全形與 95 GNU ASCII；1364 個舊字的字模與寬度逐字不變，新增 8 個說明用字已在 F1 抽驗 | [014](docs/spec/014-local-eten-font.md)、[019](docs/spec/019-frontend-help.md)、新版契約審查 |
| 主題與 HD | Shift+F12 切原版、琥珀、手繪；四場景、160 怪物變體已打包，正常城鎮與戰鬥抽驗 | [015](docs/spec/015-presentation-themes.md)、[018](docs/spec/018-all-recognizable-hd-images.md) |
| F1 說明頁 | 已入三平台包；Linux 與 Wine 五語 F1／Esc 返回畫面差為 0，macOS 核對全部表與字型 | [019](docs/spec/019-frontend-help.md)、新版 `gui/verification.json`、`windows/verification.json` |
| 新版隊員圖像 | 32 變體已入三平台包及影片；正常索引 0／bank 1，原有五語 165 狀態及獨立像素允許域仍有效 | [020](docs/spec/020-party-hd-images.md)、`workplace/party-hd-r1/`、新版正式錄影 |
| 推廣影片 | 72 秒實際遊玩與主題／五語展示，2160 格、30 fps，第二版原創配樂 | [016](docs/spec/016-gameplay-video-capture.md)、[017](docs/spec/017-original-promo-score.md)、`promo/verification.json` |
| README 截圖 | 七張主要繁中圖與新版正式包實際擷取的解碼像素及 PNG 完全相同；五語與原版主題對比保留，無手冊答案 | 新版正式收據 `readme-formal-screenshots.json`、`workplace/public-readme-screenshots-r1.json` |
| GitHub Issue | #1 至 #4 已補結案證據並關閉，目前未關閉數為 0 | [遠端 Issue](https://github.com/wicanr2/phantasie_cht/issues) |

唯一現行交付根目錄為 `dist-all/v.1.0.1-20261006/`。`full-local/` 含 Linux x86_64 AppImage、Windows amd64 ZIP、macOS universal ZIP，附遊戲、手冊提示、繁中倚天與完整圖像。`patch/` 不含遊戲、答案、倚天或 HD，採 GNU Unifont 17.0.05 的 OFL 1.1。`promo/` 保存成片、第二版母帶、產製工具及完整音色庫條款；`smoke/` 保存抽樣驗收與重播腳本。全部產物留本機，沒有公開 Release。repo 已依使用者授權轉為 public，GitHub 狀態核對為 PUBLIC；公開範圍為程式、譯文、文件與批准的展示截圖。專案程式授權為 RRSAL-1.0，不涵蓋原版素材。

正式驗收工作區為 `workplace/package-prototype/formal-acceptance-v.1.0.1-20261006/`。Linux 實際完整版已抽測五語標題與 F1、三主題、公會返回、繁中 15 點存檔／冷讀檔。Windows 實際包在 Wine 抽測五語標題與 F1、手繪城鎮；輸入擷取程序 exit 0，窗口關閉後以本次擁有的 wineserver 收尾，正常關閉及 Windows 真機未驗證。macOS 核對兩種架構、plist、全部資產，未真機操作。補丁包完成內容、字型、授權與外洩核對，沒有另行 GUI 抽測。

正式擷取的城鎮 36、公會 81、地圖 17、戰鬥 33 點共 167 點與既有已驗收狀態相同。新版影片直接解碼審核通過，72 秒、2160 格、-18.01 LUFS、-2.41 dBTP，沒有黑幀；靜止區間由相同來源畫面核對。15 段共 75 個來源樣本、17 格成片與 30 份字幕字框抽驗通過，底部新版隊員可見。成片 SHA-256 `e373d452ec9aa531aaaad12cf5f57b6467bf44e2ca98ec41fb09661679f6d08c`。配樂第二版已獲使用者試聽確認，不使用其他版本原版音樂。F1 另作 GUI 驗收，沒有插入影片。成片含中途原版英文戰鬥訊息，不宣稱每個執行期瞬間已逐格中文化。

## 文字、資料與證據

- 四語各有 `ui` 678 筆、`prose` 1044 筆，合計 1722 筆，lint 零錯誤。四語的 16 個來源資料缺口已補齊；MESS6:52 已正常抽驗，其餘 15 新鍵未逐鍵量到，見 [026](docs/re/026-recovered-prose-catalog.md)、[027](docs/re/027-dungeon-six-recovered-message.md)。
- 本機 `manual` 各 156 筆。物品及法術提示保留原版選項，由玩家作答。手冊、答案與作答路線只留本機；版控只有無答案標題、工具與合成測試。入口見 [006](docs/spec/006-manual-answer-hints.md)、[手冊來源](docs/re/012-manual-prompts.md)。
- 原始文字掛點、操作、完整記憶體及正常玩家路線證據見 [研究索引](docs/re/README.md)，不以 GUI 圖片取代原版對拍。最新 HD 實作基準見 [029](docs/re/029-all-image-formats.md)。

## 已知限制

- 未逐項驗證：其他地圖描述格、部分 MESS 欄寬與事件、地城備份還原、INT 10h `AH=0Bh BL=1` 與原有文字跨色盤。具體範圍見 002、005、012，抽樣以外不計 UI PASS。
- 中文停用項目不重現原版變暗；數字有原版粗體與疊字細體混用；日韓數字欄位仍有少量 lint 警告。
- HD 的兩個全白變體、未知或遮擋部分保留原版。地圖保留原版。隊員新功能只有索引 0／bank 1 正常路線證據，其餘 31 變體只完成資產與合成契約；個別未正常到達的場景與怪物不宣稱已實機觀察。
- 新版隊員戰鬥只實際抽驗 Linux；Wine 只抽驗城鎮及五語 F1，macOS 只有靜態驗證。
- 玩家名音譯、公開 Release 與影片公開方式尚未定案。相關 Issue 已依使用者 2026-10-06 授權結案。

舊版本機交付保留，新版使用獨立目錄與 tag。公開儲存庫不散布原版遊戲、手冊答案、倚天字模或手繪圖集。
