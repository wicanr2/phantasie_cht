# 017 原創推廣配樂

狀態：CONFORMED。第二版配樂已通過兩輪唯讀實作審查及使用者試聽確認，供本機推廣影片使用；不為原版增加遊戲內音樂，不建立公開影片。影片畫面仍依 016 驗收。新增配樂須標為本次原創，不能稱為原版原聲帶或未發表原曲。

## 聲音依據與構想

本專案為 DOS 版 Phantasie 執行期中文覆繪，非規則重製。原版開場／城鎮錄音靜音，戰鬥有 PC speaker 音效，來源見 016。第一代的其他平台有主題曲錄音，本次沒有下載、改編或引用旋律。

已驗證的玩家動作為公會組隊、大地圖旅行、回合制戰鬥選擇。聲音構想取城鎮石牆、木造招牌與公會名冊：石材以少量鐵琴音點、木材以尼龍弦撥奏、閱讀停留以長笛及大提琴短句表現。這是新配器構想，不宣稱原作具有這些樂器。

新動機為 D4、F4、E4、A4、G4、D4，MIDI 音高 62、65、64、69、67、62。開頭稀疏陳述，城鎮以撥弦回答，旅行刪去末音，戰鬥縮短節奏，片尾回到 D 並留 A 的空五度。沒有引用既有曲目或請求模仿特定作曲家。

使用者試聽第一版後要求更有戰鬥張力。第二版只調整 48–64.8 秒戰鬥段，增加低音切分、尼龍弦八分音符及低鼓重音，旋律縮短且提高力度。其他分段、動機、留白及總長不變；第一版音訊與量測另留歷史原型，不能當第二版驗收。

## 輸出契約

影片配樂長 72 秒，100 BPM、4/4、30 小節。固定分段：0–7.2 秒片頭、7.2–19.2 城鎮／主題、19.2–33.6 公會／語言／地圖、33.6–45.6 旅行與危險、45.6–48 留白、48–64.8 戰鬥、64.8–72 片尾。進入 45.6 秒留白時，各軌的活動音符與延音踏板必須已關閉，至 48 秒前不發 note-on；只保留自然 release 與 reverb 尾音衰減，不以段落音量包絡遮蔽持續奏音。混入原版音效時另按剪輯表明示。

使用專案編寫的標準 MIDI format 1，ticks-per-quarter 480。保存完整總譜及同步 melody、harmony、bass、percussion 四份 MIDI 與四份音軌；四軌採相同起點、72 秒、48 kHz 雙聲道。note-off 必須與 note-on 配對，不留下掛音；落在最後小節的聲音在 72 秒內淡出。這是線性影片配樂，不宣稱無縫遊戲循環。

音色庫為作者的 [GeneralUser GS](https://github.com/mrbumpy409/GeneralUser-GS)，固定 commit `684543d5e5efaef08d02be50dcda8d552478fa60`，保留完整授權與來源。作者條款允許私人及商業音樂創作，對樣本來源的說明也完整保留，不能自行改稱公有領域或 OFL。合成用 FluidSynth 2.3.1，Debian bookworm 套件及必要附庫由官方來源取得並固定 SHA-256。來源入口為 `workplace/package-prototype/promo-music-inputs-r1/source-lock.json`；所有第三方輸入唯讀。

可版本控制的同份來源鎖為 `tools/promo/sources.json`。GeneralUser SF2 的 SHA-256 為 `9575028c7a1f589f5770fccc8cff2734566af40cd26ed836944e9a5152688cfe`；固定 archive 根目錄抽取 SF2、完整 LICENSE 與 README，不用 basename 搜尋混入 documentation/README。

沿用既有影片映像 `sha256:78e0c88b07ee659bec32611ad16a49b01f5a6d75c67ba524b8258de1339d2ab3`，只有缺少 MIDI 合成器時建立有明確替代關係的工具 revision。Docker recipe、固定來源鎖及重建命令進 Git，音色庫、套件與生成音軌只留本機。不得使用主機 runtime、音色庫或未鎖版 library。

合成保存參數、工具版本、MIDI／音色庫／套件／每份輸出 SHA。master 保留 WAV 與 OGG；影片使用 AAC。四個 stem 各自不做獨立響度正規化，先固定混合比例，再對 master 做有測量值的響度調整，目標 -18 LUFS、true peak 不超過 -1 dBTP。不得把技術音量檢查稱為人耳認可。

## 驗收與入口

原型入口為 `workplace/package-prototype/promo-music-prototype-r1/`。正式來源為 `tools/promo_score.py`、`tools/promo/Dockerfile.music` 與 `tools/promo/render_score.sh`，納入 016 的影片輸入清冊。建置前以 `docker image tag sha256:78e0c88b07ee659bec32611ad16a49b01f5a6d75c67ba524b8258de1339d2ab3 phantasie-promo:video-base-78e0c88b` 建立本機別名；recipe 的 digest 同時固定該基底。只複製並解開四份固定套件，額外套件不進映像。

母帶第二遍由 `tools/promo_score.py --master-plan` 保存第一遍數值與混合輸入雜湊，再由 `tools/promo/master_score.sh` 於相同工具映像產生 WAV／OGG 及獨立量測。依據 [FFmpeg loudnorm 文件](https://ffmpeg.org/ffmpeg-filters.html#loudnorm) 使用實測參數，線性調整須符合峰值與響度範圍條件；最後結果以獨立量測為準，不只查命令目標。

兩輪唯讀 DRAFT 審查已完成：契約審查阻擋 0、應改 1、建議 1；來源審查三項皆 0。此版已補上留白入口關閉音符／延音及完整映像雜湊。報告保存於上述原型目錄的 `contract-review.txt` 與 `evidence-review.txt`。

兩輪唯讀審查須先核對來源／授權與 MIDI 契約，再檢查實際音軌。抽樣驗：MIDI 事件數及配對、分段／留白、四軌時長／格式、重建可追溯、非靜音、無削波、LUFS／true peak、混合後的層次。必須抽聽開頭、城鎮、留白及戰鬥；不能聽時明示未驗收，不把檔案存在當作音樂完成。此配樂不代替三平台封包、正式畫面錄製或影片驗收。

第二版收據為 `midi-r2/`、`audio-r2/`、`implementation-contract-review-r2.txt`、`implementation-evidence-review-r2.txt`，兩輪最終均為阻擋 0、應改 0、建議 0。總譜含 289 組成對音符，全部於 72 秒內结束；留白入口無活動音符。五份合成 WAV、四軌混合及母帶均為 48 kHz 雙聲道、3,456,000 frames。母帶 WAV 為 -18.00 LUFS、-2.50 dBTP；OGG 為 -17.96 LUFS、-2.43 dBTP，未削波。第二遍 WAV 重建的 PCM 與母帶完全相同。

戰鬥以外的 108 個 MIDI 音符保持第一版內容；母帶整體增益隨第二版重新量測，因此不宣稱其他段落的母帶 PCM 相同。使用者要求增加戰鬥張力後，試聽第二版並明確選擇「採用第二版」。技術核對與人耳採用分別完成。

重建依序在 Docker 執行 `promo_score.py --output <新 MIDI 目錄>`、`render_score.sh <固定 SF2> <MIDI 目錄> <新音軌目錄>`、`promo_score.py --master-plan <音軌目錄>`、`master_score.sh <音軌目錄>`。前兩個 Python 步驟用既有 Python 3.13 映像；音訊步驟用 `phantasie-promo:music-r1`。音訊工具 revision 的映像 manifest 為 `sha256:b52e4db0fc23ace94827572165dca1392226f314d2add38e1eb5e3057143482d`，Docker recipe 與四份套件指紋是其重建入口。
