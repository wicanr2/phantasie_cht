# 020 戰鬥隊員手繪圖像

狀態：CONFORMED（Linux 原始碼建置、資產契約及正常戰鬥抽樣；未重打包）。使用者要求戰鬥畫面底部隊員改用新版 sprite，延續彩色手繪與原版構圖。前置為 [018](018-all-recognizable-hd-images.md) 及 [RE029](../re/029-all-image-formats.md)。本規格只擴充輸出合成，不改輸入、原版資料、角色外觀值、規則或存檔。

兩輪唯讀規格審查及兩輪實作審查已通過，阻擋、應改與建議皆為 0。契約與證據報告為 `workplace/party-hd-r1/contract-review.txt`、`evidence-review.txt`、`implementation-contract-review.txt`、`implementation-evidence-review.txt`。實作提交為引擎 `9f1c720af6aa72dc5b7c7bea5a1ed3a574a2a855`。

## 原版證據

原版 `PRT1IBM.PAT`、`PRT2IBM.PAT` 各 4096 bytes，SHA-256 分別為 `001775cde8d7a3e6902b2bd189568951efef6364d20a4ca4816e741b723b0632`、`be4f143ca1541b774733b4e3d91e510ec13f4358ab80c4a91a8a937c62e6b623`。兩檔為未壓縮 row-major CGA 2bpp，每列 8 bytes，高位先畫。每個 bank 有 16 個 32×32 圖像，索引 i 的 byte 範圍為 `[256i,256i+256)`。

IDA Pro 9.4 靜態 consumer 為 `sub_41AC`，原靜態位址 `0110:30AC`。来源選擇為 DS:3B96 或 DS:4B96，加上 `256 * low byte of DS:[5CB0+0x11A*party_slot]`。以上格式與 consumer 為已證實；索引的種族／職業名稱及 bank 的遊戲語意未知，不命名為攻擊或受擊。

本機證據入口為 `workplace/package-prototype/hd-all-image-review-r1/portrait-geometry-confirmed-r1.json`，工具與位址基準沿用 RE029。12 張正常戰鬥圖像曾完整命中索引 0／bank 1，native y=156、高 32，x 包含 84、144、200。其餘 31 變體未正常到達。PRT 索引 9 與 MSTR 索引 56 同 bank 的 bitmap 相同，必須以位置與類別分開，不以相同 bitmap 宣稱同一遊戲身份。

本次本機參考圖由 Docker Python 3.13 標準庫直接解原版 bytes，輸入唯讀。`workplace/party-hd-r1/party-reference-square-r1.png` 為 2048×2048 黑底圖，8 欄 4 列的 256×256 格置於 y=512 至 1535；每格原圖以最近鄰放大 7 倍至 224×224 置中。順序為索引 0 bank1、索引 0 bank2、索引 1 bank1，依此至索引 15 bank2。矩形、逐圖雜湊與工具收據保存在同目錄的 JSON；圖與原版 bytes 不入 Git。

## schema 3 契約

schema 1、2 的欄位、上限及輸出保持 015、018 行為。schema 3 根欄位仍為 `schema`、`sources`、`images`、`pages`、`sprites`，每筆 sprite 另有必要欄位 `kind`，僅接受 `monster` 或 `party`。schema 2 不接受 `kind`。未知、缺少、重複欄位、null、尾隨 JSON 皆拒絕。

schema 3 的來源仍最多 8、圖像最多 32、場景最多 4、每頁 preserve 最多 16，sprite 合計最多 192。既有 PNG、裁切、完整大小／SHA-256、basename、symlink、完整載入後才曝光的限制不變。新增 `raw-linear` encoding，必須原始與解碼 bytes 都等於宣告的 decoded_bytes，上限 65536。它不能當頁來源。

- monster：僅使用 `zero-rle-linear`，索引 0 至 79、state 1 或 2。寬高及來源范围沿用 018，完整匹配矩形只能位於 `(0,0,320,151)`。
- party：僅使用 `raw-linear`，來源長度 4096、寬高固定 32×32、索引 0 至 15、state 1 或 2，source_offset 必須等於 index×256。完整匹配矩形的 y 必須等於 156，x 為 4 像素對齊且完整落於畫面內。

身份唯一鍵為 kind、index、state。相同完整 bitmap 只在相同 kind 內判定重複並拒絕；跨 kind 允許，以處理已證實的 PRT9／MSTR56。來源 id 與檔案身份仍唯一，引用及來源 encoding 要逐筆核對。profile 不含原版 bytes。

## 純顯示辨識

場景優先與多場景歧義回退沿用 018。沒有場景命中才辨識 sprite。怪物搜尋區保持底線 151；隊員只搜尋 y156 的完整 32×32 圖像，不擴大怪物範圍，也不依列表順序消除歧義。

完整畫面的 packed 暫存只供輸出辨識。4-byte anchor 不能跨列；每個通過 anchor 且落在所屬 kind 允許區、即將完整比對的候選共用 10000 比較上限，超限整幀回退。完整 bitmap 必須逐 byte 相同；相交候選皆拒絕。空圖拒絕載入；全白來源不進候選；後續文字遮擋、白化、清除、部分重繪或位置不符時保留原版。

僅在已命中的完整矩形內清除舊圖及合成手繪圖，色盤 index0、純黑透明與 PNG alpha 行為沿用 018，然後才畫語言覆繪。新圖不得超出原 32×32 矩形，不改隊员名稱、選取框、狀態文字或相鄰圖像。original、amber 輸出不變。每次繪圖都重新辨識，不保留跨幀身份，不寫記憶體、VRAM、鍵盤、亂數或存檔。

## 資產與工具接線

32 個手繪變體保留各自姿態、武器、轮廓与构圖，不將未知索引推定為種族／職業。正式 PNG 裁切比例誤差最多 0.5%，每格完整落在自身裁切域；最多 4 百萬像素的既有 PNG 限制不變，2048 方形參考圖不能直接宣告為正式 PNG。必要時拆圖或取實際 2048×1024 格區。未可辨識的畫面回原版。

主專案 `tools/package_art_assets.json` 保留 018 的 schema 2 批准 metadata，新增 `tools/package_party_art_assets.json` 固定本規格的 schema 3 metadata。兩個入口分別按 schema 核對批准 JSON 完整等值與逐圖 SHA，不用新版資料覆蓋舊版的批准身份。`package_files.py`、stage／finish、launcher、後端 `ArtAssetNames` 與 `LoadTownArt` 需一併接受 schema 3。原版 PRT 必須來自使用者本機輸入，完整包或本機資產才可帶 HD；patch、Git、公開 Release 不含圖集與原版。既有正式六包、tag、影片不覆寫，本輪不重打包。

## 驗收

先兩輪唯讀審查，分契約／程式與資料／證據，達 READY 後才實作。

必要合成反例為 wrong y、錯 x 對齊、遮擋一像素、白化、空白、跨列 anchor、類別重複身份／bitmap、PRT9 與 MSTR56 在上下區的分流、源長度／offset／geometry／kind／state 錯誤、schema 2 帶 kind、超過 192／8 上限、PNG 損毀或錯 SHA。schema 2 既有怪物辨識與 schema 1 回歸。

封包工具另以 018 的真實舊 schema 2 profile 與 13 份資產執行 `art_files`，核對回傳清冊、逐檔 bytes 與舊雜湊不變；新 schema 3 同樣逐檔核對。兩種 schema 任一 profile 或圖像的單點身份破壞都必須失敗。測試不只使用合成 JSON，也不重新包裝或覆寫舊正式包。

正常戰鬥由原版啟動及鍵盤路線抵達，不修改存檔或記憶體跳關。同一狀態 original／HD 比較完整 memory、VRAM、steps、reads 不變，另確認語言覆繪與 original 主題保持既有輸出。本輪四人隊伍的正常戰鬥矩形為 `(36,156,32,32)`、`(104,156,32,32)`、`(172,156,32,32)`、`(240,156,32,32)`，由原始 PRT bytes 對原版 indexed 畫面完整比對確認；前述舊 12 張圖的 x84、144、200 仍是其自身幾何證據，不套入四人路線。獨立腳本依這四個字面矩形限定隊員差異域，不得呼叫被測 renderer 自己的遮罩。實際把域外單像素改動注入 PNG，確認同一完整差異掃描會拒絕。戰鬥返回或被文字遮擋後不得殘留 HD。

各語言至少擷取一張有實際文字的正常畫面，另擷取 original／HD 同一戰鬥狀態作 README 比較。不含手冊提示或答案。正常到達證據只聲明實際抽樣的索引 0／bank 1，其他變體只有資產／合成反例證據，不能宣稱逐圖原版 parity。

## 本機實作驗證

資產組為 `workplace/party-hd-r1/assets-r1/`，包含 profile 與 13 張 PNG，共 14 份檔案。批准 metadata 為 `tools/package_party_art_assets.json`，profile SHA-256 `25fc039ec21162ef57e90c898025edadd5d9dda62f47e3e238d0524bf1964c75`。新隊員圖集 `party-painted-atlas-r1.png` 為 1536×768、8×4 格，SHA-256 `32cbb9aeeafd5c11f6a7541514422f6460988b18528c2558b2aca997e8b1dc98`。32 格由 image_gen 依原版參考圖生成，再逐格無損裁切與透明補邊，未重畫或重取樣。生成原圖、裁切與可見主體範圍見同工作區 `party-painted-proof-r1.json`，素材只留本機。

| 抽樣 | 證據與結果 |
|---|---|
| 完整資產與辨識契約 | `verification-r1.json` 核對 8 來源、192 變體、14 份檔案；190 個非全白候選辨識通過，兩個全白怪物變體回退。錯誤位置、遮擋、白化、身份、長度、裁切、PNG 與上限負例均拒絕 |
| 正常玩家路線 | `normal-r1/normal-route-receipts.json` 記錄五語 165 個原版狀態點，完整記憶體、VRAM、步數、讀鍵與既有正常路線基準相同，original 主題保持既有像素輸出 |
| 獨立像素允許域 | `normal-r1/independent-mask-verification.json` 完整解碼比較 20 對 PNG，差異只落於四個字面隊員矩形；20 張實際域外單像素負例全部拒絕。審查者另行解碼重驗 |
| 舊資產回歸及工具 | schema 1、2 的契約與實際舊 160 怪物組通過；`tools/tests/party_art_cases.py` 對兩套真實 profile 核對原始 bytes、清冊及各自身份破壞負例，實際 PASS，沒有以 SKIP 計驗收。原生啟動器 `go test ./...` 通過 |
| README 截圖 | `round3-<lang>-hd.png` 五語實際訊息及繁中 original 對照保存於 `docs/screenshots/`；來源、逐檔 SHA 與複製核對見 `workplace/public-readme-screenshots-r1.json` |

驗證限制：正常路線只實際觀察隊員索引 0／bank 1；其他 31 個變體完成資產與合成契約驗證，未逐圖正常到達。不宣稱未知種族、職業或 bank 語意。地圖仍為原版。此輪只驗 Linux 原始碼建置，不宣稱 Windows／macOS 真機通過；既有六包、tag 與 72 秒影片保持不變，尚未含新版隊員。
