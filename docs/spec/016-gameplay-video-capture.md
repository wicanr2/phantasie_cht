# 016 實際遊玩逐格擷取

狀態：CONFORMED（正式本機交付抽樣，平台限制見末節）。兩輪唯讀審查無阻擋或應改。前置 005 CONFORMED、015 CONFORMED。使用者要求本機推廣影片包含實際遊玩與主題切換；不建立公開影片或 Release。聲音來源另記本機收據；使用者已授權製作原創配樂，並要求先查其他平台版本的音樂。

## 擷取契約

互動前端增加可選自動模式：`-record-route <路線>`、`-frame-dir <新目錄>`、`-frame-every <整數>`、`-hold-frames <整數>`、`-showcase`。沒有 record-route 時保持正常互動；其他擷取旗標不能單獨啟用。空 frame-dir 可用來作同路線無擷取基準。frame-every 為正整數，預設 2，hold-frames 預設 60，介於 1 至 600。自動模式跑完正常退出。

自動模式必須明示 `-state <新目錄>`，父目錄已存在，拒絕使用既有目錄或互動模式的預設玩家存檔位置。每次三模式 A/B 都由同一唯讀 root 加全新 state 啟動，保存初始狀態摘要；失敗時只保留本次研究輸出，不刪除玩家資料。自動分支在啟動 Session 後直接執行擷取，不進 Ebiten RunGame，固定自行 Frame 及合成，不依賴 Draw／Update 排程。

原版啟動、字型、譯文、語言、主題與圖像沿用正常前端；用既有 ParseRoute 與 KeyGate 重播，不注入角色、座標、存檔或記憶體。每個執行切片固定為 ips/60 原版指令預算，稱為虛擬顯示格，並非已證實的原版硬體幀。原版等鍵處可提早結束切片；收據記錄實際步數，不能宣稱 60 Hz 原版時鐘一致。

RouteKey 依原路線排入 Gate，保留 Wait；RouteCheck 等待 Pending 為零且 Reads 大於 LastSent，RouteSnap 等 Pending 為零後再跑路線指定步數。兩者用 RunUntil 逐指令檢查條件，不整塊多跑；Snap 的步數起點為 Pending 第一次達零的精確停止位置，後者預算在末切片裁至剩餘步數，不能多跑。InputWaitError 只有目標條件已成立才算成功，其他等待及錯誤失敗。ips 必須至少 60，切片預算用 ips/60 的整數商。每個切片及停點照常呼叫 Session.Frame。RouteLang 只切顯示；RouteAssert 驗證原有可見格／畫面摘要，失敗不能作成功錄影。以同初始輸入的既有 receipt 核對每停點 steps、reads、完整 memory 與 VRAM，三個新模式互相一致不能單獨取代舊路線語意。

到達停點後保持 hold-frames 個虛擬顯示格。保持期間不再 Run 原版，沒有送鍵、推進 RNG 或增加讀鍵；每格仍以當前原始畫面維護覆繪並使用 015 合成。這是回合制介面的明示停留，不能把保持段說成角色動畫。

showcase 只在第一個名稱為 town 的正常停點發生：先保持 original、amber、hd 各 90 格，沒有 HD 時略過 hd；再在目前主題上保持五個已啟用語言各 60 格，使用正常 NextDisplay，循環後恢復原語言與主題。與真實 Shift+F12／F12 的玩家按鍵分支分開驗收，影片字幕照實標示顯示切換。展示只改顯示，不改 Gate 或遊戲。

每格都執行同一合成與 Frame 維護；frame-every 只控制是否寫 PNG，不能控制執行或 Frame。frame-dir 必須為新目錄、父目錄存在，拒絕符號連結與覆寫。檔名為連續虛擬格號；一定寫最後一格，間隔不同時共有格內容一致。沒有目錄時仍維持同樣渲染，避免無擷取基準省略覆繪維護。

輸出 capture.json 包含 schema、虛擬格率 60、ips、路線 SHA-256、區段與擷取格索引、各停點的原版 steps／reads／完整記憶體 SHA-256／VRAM／overlay content、檔案 SHA-256及目前語言／主題。只留本機，不印按鍵、手冊答案或原版 bytes。沒有已核對的本機答案時，不替玩家作答或猜補，正常路線受阻即失敗。

frame-dir 非空時把 capture.json 排他寫進該新目錄；空時把同樣 JSON 寫至 stdout，由容器編排重導至新研究檔案。三模式的每個停點都記錄當前合成 RGBA SHA-256，與 PNG 寫入無關；另外記錄路線 SHA、初始完整 memory／VRAM 及全新 state 的空目錄身份，證明比較條件一致。輸入指紋與輸出 SHA 分開：必須記錄實際後端執行檔、text／font／art 檔案及原版 root 的 SHA-256；正式錄影另提供 `-record-bundle <清冊>`，記錄版本、engine_commit、bundle SHA 與必要資產，逐檔驗證並核對必要 backend 正是目前執行檔，不能以標籤或其他 stage 冒充正式包。研究基準可不指定 bundle，此時清楚標為 research。

到達停點還須核對 @expect、@known-untranslated、Hooks 的失敗／簽章、Gate.Err、protected 與 unpaired 診斷；原路線累積排入的鍵數須與 Gate.Gated 相同，不能把未知鍵被丟棄當成功送鍵。非 Busy 時稽核殘字及事件遮罩。英文模式不要求中文疊字，但仍檢查原版與鉤子完整性。不通過即失敗退出，不寫成功 capture.json，保留已產生的本機診斷畫格。錯誤只輸出固定的階段分類，共用 parser 與 KeyGate 的原始 error 可能含按鍵或 bytes，不能直接印出。

## 影片與聲音

從正式完整版的實際後端及 text、font、art 錄製。公開 route 可入 Git；私人作答 route、畫格與音訊只放 workplace。剪輯表以區段及格範圍選實際遊玩，包含城鎮、公會、地圖或戰鬥的正常輸入與切換。手冊題區段及其相鄰不穩定格不得入片；用區段白名單，未辨識區段不自動收錄。

剪輯白名單固定 capture.json SHA-256、允許的區段名稱與半開格範圍；換錄製收據就重新核對，不讓舊白名單套入新捕捉。範圍前、內、後各抽格檢查，手冊區段的排除有負對照。

ffmpeg 在既有影片容器以兩核、threads 2、filter_threads 1、有界執行合成 1280×720、30 fps、H.264 yuv420p。維持遊戲 8:5 比例與整個 UI，字幕另在畫面外。字卡只作片頭、轉場與片尾，不能代替真正執行畫格。配色取自城鎮石牆、赤陶屋頂及 CGA 青色，配樂不沿用其他專案。

影片時間以虛擬格索引／60 建立，再重採樣至 30 fps；稀疏 PNG 不能當連續 60 fps 圖片編號。相鄰擷取格依原索引差保留時長，末格補足至總虛擬格數／60 的尾端；步幅不整除的最後一格仍以其真實索引計時。分鏡的剪輯範圍與語言／主題字幕以同一索引來源計算，不用檔案張數猜秒數。

原版聲音只用正確模擬器實際錄音。[DOSBox 0.74-3 官方手冊](https://www.dosbox.com/DOSBoxManual.html) 列 Ctrl+F6 為 WAV 錄音；原版開場及城鎮第一次錄音是 16.848980 秒靜音，不當有效音源。正常戰鬥的 dosgolem 窄探針有 PIT2 及喇叭寫入；DOSBox 原版戰鬥錄音已取得，45.026984 秒、PCM s16le 44100 Hz 雙聲道，平均 -21.1 dB、最大 -16.3 dB，沒有削波。入口為 `workplace/package-prototype/original-audio-combat-r1/`，保存原始 WAV、設定與正常到達戰鬥的 PNG；擷取腳本在 `original-audio-r1/capture-combat.sh`。影片可使用這份本機原版錄音作背景音效，並明示未與 dosgolem 格時間同步。DOSBox 只作音源與輔助研究，不作視覺或玩法對拍權威。沒有可用配樂時依使用者聲音選擇處理，不能以自製方波、TTS 或不相關原曲頂替。

## 驗收與入口

其他平台音樂的查證入口為 [Xeen Music 自有曲目表](https://www.xeenmusic.com/) 與[錄音版本清單](https://www.patreon.com/xeenmusic/posts/soundtracks-for-33330003)。第一代的 Atari 8-bit、Atari ST、Amiga 各列一首，錄音長度分別為 1:34、0:59、1:04；PC、Apple II、C64 及數個日本平台列為無音樂。這是錄音者的版本分類，尚未由本專案執行其他平台的原版確認。不能由一首錄音推論全程都有背景音樂。[Amiga 第一代與第三代合輯](https://www.youtube.com/watch?v=N3DKeBpEyA8) 的 0:00 標為第一代 Main Theme；第三代曲目不充作第一代配樂。查證日 2026-10-05，這次只查閱曲目資料，未下載或整合其他平台音訊。

兩輪唯讀規格審查為 `workplace/package-prototype/promo-contract-review-r1.txt` 與 `promo-evidence-review-r1.txt`；通過才 READY。實作為引擎 `apps/phantasie/cmd/phantasie-play/auto.go` 與 main 的可選自動分支，影片腳本及字幕表在專案 tools，沒有原版時明示受阻。

實作抽樣收據入口為 `workplace/package-prototype/auto-capture-r1/`。各模式使用同一後端與唯讀原版、譯文、倚天字型、城鎮手繪資產；每次 state 與 PNG 目錄皆新建。r2 的無擷取、間隔 1、間隔 2 與間隔 2 重跑，城鎮 36 個停點一致；公會 81、戰鬥 33 點的無擷取與間隔 2 也一致。全部 150 點的原版 steps、reads、完整 memory 與 VRAM 皆與既有正常路線收據相同。共有 PNG、重跑 JSON、末格的獨立解碼 RGBA、主題及五語展示持續時間通過，摘要見 `verification-r2.json`。

契約審查找到 parser／KeyGate error 可能含輸入原文，已改為固定階段分類；普通選單靜默丟鍵另以成功送鍵數核對拒絕。r4 三種虛構錯誤路線皆 exit 1，未印出 marker，也未寫成功收據；三條正常路線與 r2 的停點及畫格摘要相同，實際 backend hash 分開記錄。入口為 `negative-and-regression-r4.json`。兩輪實作審查在同目錄 `implementation-contract-review.txt` 與 `implementation-evidence-review.txt`。正式包錄製與成片尚待驗證，規格維持 READY。

- 同 route、ips、字型、語言及主題，frame-dir 關閉／間隔 1／間隔 2 三次執行，各停點 steps、reads、完整 memory、VRAM、overlay 相同；間隔 1 與 2 的共有 PNG 相同，兩次同設定重跑 bytes 相同，末格等於該狀態的 015 合成。
- 至少一條正常城鎮／公會及一條地圖／戰鬥，確實進行原版輸入並抵達正常停點；showcase 各語言及主題持續時間、前後 Gate 不變。
- 視訊、音訊、時長與 SHA-256；音源非靜音與無削波。黑格與凍結檢測要對照明示菜單停留區段，超出宣告區段的長凍結失敗。字幕不得裁切；抽片頭、片中切換、戰鬥、片尾人工看圖，聲音的人耳確認另列限制。
- 封包與影片路徑沿用 dist-all/<版本>/full-local、promo、smoke；所有原版、倚天、衍生圖與錄音只留本機。影片存在不等於上述檢查完成。

本規格的擷取完成不代表三平台真機均已驗證，也不代表全部圖像已 HD 化。

正式成片編排為 [tools/promo_video.py](../../tools/promo_video.py)，在 Docker 指定 `--captures`、`--score`、`--out`、`--version`、`--project`。以四條固定公開路線、正式 bundle 與已確認第二版母帶 SHA 建 72 秒白名單、逐段 concat、字幕及 `render.sh`；FFmpeg 腳本仍在既有影片容器執行。字幕在 1024×640 遊戲區外，成片 1280×720／30fps。虛擬格索引保留來源時長，剪輯另明示時間伸縮比例；手冊／答案／標題／prompt 區段拒絕，未知非 transition 格不能入片。`plan.json` 固定 capture.json 指紋，記錄重複原版畫格及明示選單停留，凍結檢測須與這些區段核對。`--audit` 讀 FFprobe、loudnorm 及黑格／凍結檢測，符合契約才寫 `verification.json`；人工畫面與字幕抽看另記本機收據。
## 成片工具的固定執行環境

`tools/promo/Dockerfile.audit` 在既有固定影片映像內加入固定 Python runtime。`tools/promo_video.py --audit` 直接對唯一成片重跑 ffprobe 與 FFmpeg，核對 2160 格、兩軌 72 秒、音量及遊戲區黑幀／凍結。舊的檢測檔不作通過依據。各鏡頭依累積時間邊界分配 30 fps 格數，五語展示依序為 32、33、32、33、32 格。

固定本機映像為 `phantasie-promo:audit-r1`，manifest SHA-256 `26debd16e86d3d8aa6b2420c2a7e7462b479cbba0458a3726d901989ee7f7c87`，含 Python 3.13 與 FFmpeg／ffprobe 5.1.9。建置只使用 Dockerfile 指定的兩份本機基底，執行一律無網路、UID/GID 1000、有限 CPU／記憶體／程序數；影片輸入唯讀，只有本次輸出可寫。

成片編排的契約與資料審查入口為 `workplace/package-prototype/promo-music-prototype-r1/video-contract-review.txt` 與 `video-evidence-review.txt`。報告只驗編排及必要合成反例，正式成片另依本規格的實際錄影、工具解碼與人工抽看閘門驗收。

## 正式本機交付抽樣驗收

正式 Linux 完整版後端以本機倚天、完整圖像組及已驗證 bundle 擷取城鎮、公會、地圖與戰鬥。城鎮 36、公會 81、戰鬥 33 個原版狀態點與既有原版收據一致；地圖使用正常玩家路線，但未另宣稱原版同狀態對拍。15 段各抽看前、首、中、末、後共 75 個來源樣本，選定範圍沒有手冊題或答案。成片另抽看 17 格，完整遊戲區與字幕可見，30 份字幕使用 FFmpeg 實際 drawtext 字框核對無裁切。72.000 秒、2160 格、1280×720、H.264／30 fps，AAC／48 kHz／雙聲道，-18.01 LUFS、-2.41 dBTP。直接重新解碼最終檔案，黑幀為零；偵測到的靜止皆由相同來源 bitmap 的已宣告區間覆蓋，不放寬既有門檻。成片 SHA-256 `060a84c74845b1c1c37f121df55a3fe04ca76cd855287a06856e1ab8353e4a31`。已採用第二版原創配樂，完整音色庫條款及來源封存於 promo。影片僅本機保留。60 秒抽樣含原版戰鬥的中途英文訊息，不宣稱所有執行期瞬間逐格中文化。

正式收據入口為 `workplace/package-prototype/formal-acceptance-v.1.0.0-20261005/`；交付入口為 `dist-all/v.1.0.0-20261005/`。`smoke/acceptance.json` 與根層 `SHA256SUMS.json` 列出平台範圍；字型獨立遮罩為 `font-mask/verification.json`，冷讀檔為 `save-r2/verification.json`，影片與字幕抽樣為 `visual-verification.json`。較早研究段落中的待驗狀態只描述當時收據，現況以本節為準。

## v.1.0.1-20261006 新版成片

影片重新擷取自新版正式 Linux 完整包，使用實際 bundle、繁中倚天及 schema 3 完整手繪組。四條公開玩家路線共 167 個停點的完整記憶體、VRAM、步數與讀鍵，均和既有已驗收基準一致。15 鏡沿用固定區段及正常輸入 transition 白名單，戰鬥字幕改為新版隊員手繪圖像；沒有改動原版操作或手冊區段的排除規則。

新版成片 72 秒、2160 格、1280×720、H.264／30 fps，AAC／48 kHz／雙聲道，-18.01 LUFS、-2.41 dBTP。直接重新解碼 audit 通過，無黑幀，所有偵測靜止均在來源可證明的區間內。SHA-256 `e373d452ec9aa531aaaad12cf5f57b6467bf44e2ca98ec41fb09661679f6d08c`。主代理目視 17 格成片及 75 個來源樣本，新版隊員與主題／五語展示可見，選定區段無手冊答案，30 個實際字幕字框無裁切。配樂仍為使用者確認的第二版，沒有重新製作或替換音源。

影片保存在 `dist-all/v.1.0.1-20261006/promo/`，包括成片、母帶、GeneralUser-GS 完整條款、`plan.json`、`render.sh`、`verification.json` 與 `provenance.json`。正式擷取及目視收據在新版驗收工作區的 `formal-capture-state-verification.json`、`visual-samples.json`、`visual-verification.json`。兩輪最終覆核皆為 0／0／0。F1 開關另由實際 Linux／Wine GUI 驗收，沒有插入影片；中途戰鬥仍可能短暫出現英文，不宣稱逐格全部中文化。舊版成片保持原雜湊，新版僅留本機。
