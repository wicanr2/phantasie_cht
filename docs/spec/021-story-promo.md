# 021：故事與實際遊玩推廣影片

狀態：CONFORMED（本機故事版成片、正常路線與 GUI 抽樣）

兩輪唯讀審查已通過，阻擋、應改與建議皆為 0，報告見本規格末段。四版面可丟棄樣張已在本機檢視，正式實作依本次使用者授權的影片重錄範圍進行。

## 範圍與來源

使用者 2026-10-06 指示依 retro remake 推廣影片技巧重新錄製，並將 README 的故事放在最前面。入口為 Codex `reverse-engineer-retro-game-remake` 技能路由的 `game-promo-video-ffmpeg.md`。配樂沿用使用者已試聽確認的第二版，來源契約見 [017](017-original-promo-score.md)。

故事只摘要 [SSI 原版手冊〈Tholie’s Tale〉](https://www.mocagh.org/ssi/phantasie-manual.pdf#page=3)：格爾諾島遭尼卡迪穆斯與黑騎士侵擾，冒險者在公會召集同伴。這是故事來源，不能作遊戲規則或通關證據。手冊本體與答案不進 Git 或影片。

沿用正式 Linux 完整包 `v.1.0.1-20261006`，引擎 `9f1c720af6aa72dc5b7c7bea5a1ed3a574a2a855`。不更動引擎、遊戲、三平台封包或既有 tag。新片獨立保存，舊片及其收據不覆寫。

## 與舊片的差異

1. 改為故事開場、公會招募、地圖與地牢、戰鬥及返回的冒險敘事。
2. 色票從本次城鎮手繪圖取樣，以石牆、紅屋頂及原版青色為來源，標題使用襯線字體。
3. 輪用標題、故事側欄、完整遊戲大畫面、原版／手繪並列、多語格網與結尾六種版面。遊戲區保持 8:5、完整 UI 與原色，不裁切或調色。
4. 戰鬥段對齊已確認配樂的 48–64.8 秒；新錄 F1 實際 GUI 操作納入影片。

## 擷取與實作契約

- 四條路線從空白本機狀態重錄。依 [016](016-gameplay-video-capture.md) 檢查實際封包、路線、畫格及 bundle 雜湊。逐點 Memory、VRAM、Steps、Reads 與既有正式驗收收據相同，才可剪輯。
- 玩家內容只選既有公會、地圖、地牢、戰鬥與城鎮白名單，以及 016 已批准的相鄰正常 transition。拒絕 title、manual、answer、prompt 區段與未知畫格，不把手冊答案畫面放進故事開場。
- F1 另從實際封包啟動 GUI，使用全新獨立狀態與輸出目錄，正常進入城鎮後錄下 F1 開啟、語言切換與 Esc 返回。逐項核對實際 backend、bundle、text/font/art 指紋，記錄輸入、擷取時間軸、窗口、640×400 client 矩形及來源 PNG 雜湊。關閉後與開啟前畫面獨立比較，解碼像素差須為 0。記錄區間外的啟動畫面不納入影片。
- 先在 `workplace/story-promo-r1/` 做可丟棄樣張。正式程式 `tools/promo_story.py` 保存色票、分鏡及可重現命令，來源畫格與影片留本機。
- Docker 工具使用固定映像、1000:1000、資源上限、外層逾時與清理；FFmpeg 至多兩線程，圖片不使用會使幀數倍增的 zoompan。
- 成片為 72 秒、1280×720、30 fps、2160 格、H.264 yuv420p、AAC 48 kHz 雙聲道。音樂母帶 SHA-256 為 `fb958dd7a908c0f8b9266c8989bc81706d91a0f0efdcbbf10134098192f0eeb1`，不以 `-shortest` 截斷結尾。

## 交付與驗收

交付留在 `dist-all/v.1.0.1-20261006/promo/`，新檔名為 `phantasie-cht-v.1.0.1-20261006-story-promo.mp4`。新片附獨立故事版 plan、來源、工具、雜湊、FFprobe、音量、黑幀／凍結與樣張收據，不覆寫舊片同名 sidecar。影片含原版與衍生美術、倚天字形，只供本機使用，不上傳。

抽樣驗收：逐段抽來源及成片畫格，量測字幕字框不越界；抽新舊影片各四格並列確認差異；驗證完整 UI、五語、三主題、F1 與新版隊員可見。音訊應為非靜音，約 -18 LUFS、true peak 不高於 -1 dBTP。任何長靜止區間必須由來源相同畫格或明示字卡停留獨立支持，不以全片白名單迴避凍結檢查。逐段依實際遊戲 viewport 或字卡區域檢測黑幀／凍結，不沿用舊片固定 crop。黑幀不得超過明示轉場；來源與成片各自的實檔雜湊須符合各自收據。

凍結檢查的 noise 固定為 `0.000001`，持續 1 秒。預設 `0.001` 會把少數像素的戰鬥文字變化歸為雜訊；先獨立解碼核實變化，再對所有視窗使用同一較嚴格門檻，不為個別鏡頭加例外。人工把戰鬥鏡頭停在單一畫格的負對照必須被判為凍結。

審查先由唯讀代理分契約與證據兩個角度執行，報告存 `workplace/story-promo-r1/contract-review.txt`、`evidence-review.txt`。通過後才改 READY 與正式實作。完成後更新 README、唯一目前狀態表 CONTEXT 與 WORKLOG。沒有擴張 Windows／macOS 真機驗收或原版逐瞬間中文化聲明。

## 產製入口

兩支工具都在 Docker 內執行。`tools/record_story_gui.py --bundle <實際完整版 usr/bin> --out <全新 GUI 目錄>` 使用既有 SDK 映像的 Xvfb、xdotool 與 import；輸出目錄不能存在，父目錄須存在。它驗證 bundle 資產、640×400 client、空白狀態、輸入時間軸與獨立返回像素。

`tools/promo_story.py --captures <四路擷取根> --gui <GUI 擷取> --bundle <實際 usr/bin> --score <第二版 master.wav> --project <專案根> --out <全新合成目錄>` 產生 `plan.json`、色票、字幕字框及 `render.sh`。相同掛載路徑執行 `sh <合成目錄>/render.sh`，再以 `tools/promo_story.py --out <合成目錄> --audit` 直接解碼最終影片。固定映像與完整重建指令保存在交付的 `story-provenance.json`。程式只接受本次固定正式包，沒有把單獨 GUI 或未知來源當作原版對拍。

## 驗收收據

最終工作區為 `workplace/story-promo-r1/render-r4/`，目視收據為 `visual-final/verification.json`。兩輪實作與最終唯讀覆核均通過，最終報告為工作區的 `final-contract-review.txt` 與 `implementation-evidence-review.txt`。交付使用獨立 `story-` 前綴，`story-SHA256SUMS.json` 與 `story-provenance.json` 保存新片及重現材料；舊封包清冊保持原樣。

| 抽樣 | 結果與證據 |
|---|---|
| 重新錄製 | 四路共 167 個原版停點、4380 張 PNG。Memory、VRAM、Steps、Reads 與既有正式基準逐點相同，`formal-capture-state-verification.json` PASS |
| F1 GUI | 正式包資產逐項核對，88 格、七個按鍵事件。五語實際說明頁及 Esc 返回，前後解碼像素差 0；`gui-final/capture.json` |
| 視訊與音訊 | 72 秒、2160 格、1280×720、30 fps、H.264／AAC，-18.01 LUFS、-2.41 dBTP；`render-r4/verification.json` PASS |
| 黑幀與凍結 | 直接檢查最終成片的 19 個完整視窗，沒有黑幀，六個長靜止區間有來源畫格支持。人工凍結戰鬥鏡頭的負對照被抓到，`negative/verification.json` PASS |
| 版面 | 14 鏡、六版面、46 份字幕字框，不越界、不覆蓋遊戲 UI。57 份來源樣本、21 份成片與新舊各四格並列目視；五語、三主題、F1 與新版隊員可見 |
| 成片身份 | 4,489,220 bytes，SHA-256 `542c0e673de3645b44eb700d6e840391097027c4e3df0994cae0b76dd6685f9e`，正式 producer 指紋與 plan 相符 |
| 既有交付 | 兩版本共 12 個封包及兩支舊影片重核不變，本機 tag 不移動。本輪沒有新增平台真機聲明或公開 Release |

實作期間的處置：襯線字實際高度超過保守估值，字幕經量測上移；裝飾線移離標題字。凍結檢查改讀最終影片，並依稀疏文字的獨立解碼證據使用統一嚴格門檻。中間版本只留工作區，正式片由最終腳本重新產製，不回填舊 generation 指紋。中途英文戰鬥訊息與正常隊員索引抽樣限制仍沿用 016、020。
