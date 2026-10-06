# 018 可辨識場景與怪物 HD 圖像

狀態：CONFORMED（正式本機交付抽樣，平台限制見末節）。使用者已選「完成可辨識的場景與怪物圖像」，風格為彩色手繪、保留原版構圖。前置為 015 的純顯示合成及 [RE029](../re/029-all-image-formats.md)。不新增輸入鍵、遊戲規則、存檔欄位或音樂。

## 範圍與資產

本機 HD 組包含城鎮、標題圖、CEMEN、ZEUS 四份場景及 80 個怪物索引各兩種圖像狀態，共 160 變體。怪物名稱及狀態語意未證實時只記索引及 bank，不補故事。隊員 PRT 圖像保留原版。發行商 BSV 的主遊戲 consumer 未知，維持原樣。

手繪圖保留原版位置、輪廓、姿態、武器及空白文字區。場景中文字與選單由原版／覆繪繪製；標題的既有作者、版本及商標文字保留原像素。怪物圖集使用固定格，每格只放該索引的一個狀態；不讓另一個狀態或其他怪物越界。所有生成圖、原版解出圖及提示只留本機，不能進 Git 或 patch。

## schema 2

擴充 015 的 `profile.json`；schema 1 的城鎮行為不變。schema 2 嚴格拒絕未知／重複欄位及尾隨 JSON，根欄位為 `schema`、`sources`、`images`、`pages`、`sprites`。

- sources：id、file、bytes、sha256、encoding、decoded_bytes。encoding 僅 `cga-page`、`zero-rle-page`、`zero-rle-linear`。頁解碼長度必須 16384；線性上限 65536 bytes。游程遇尾端零缺 count、超出預定長度或不足長度均拒絕。
- images：file、bytes、sha256。檔名為安全 basename，數量上限 32，逐份不超過 16 MiB／4096×4096／4 百萬像素，PNG 總檔案 bytes 不超過 64 MiB。必須真正解碼，不能只驗 CRC 或自填 profile。
- pages：source、source_rect、image、image_rect、preserve。所有矩形採 `[x,y,width,height]`，原版矩形以 320×200 native 像素為座標，寬高至少 9；image_rect 採對應 PNG 的像素座標，寬高須為正；preserve 採原版 native 座標且須在 source_rect 內。
- sprites：source、source_offset、width、height、index、state、image、image_rect。來源為線性 bitmap，寬須可除 4、16 至 80，高 1 至 80，完整範圍不可超出解碼資料。image_rect 採 PNG 像素座標，寬高為正；索引與 state 僅作身份，不用推測的遊戲名稱。上限 160；原型與正式 80×2 項逐筆核對來源範圍與圖像裁切。

來源上限 8，場景上限 4，preserve 每頁上限 16。所有矩形須為整數且不越界；source_rect 與 image_rect 的寬高比、sprite native 寬高與 image_rect 的寬高比皆容許 0.5% 誤差，不能用整張 atlas 的比例代替。裁切後以最近鄰取樣到 native 尺寸的兩倍；每個輸出取樣索引明確落在裁切區內，不讀鄰格。

sources／images 身份唯一；引用必須存在，不能使同一 basename 宣告不同指紋。現有無 symlink、唯讀、完整大小及 SHA 檢查沿用 015。全部組載入完成前不曝露部分替换。載入失敗沿用直接後端回退；正式 bundle 已宣告必要 HD 組時拒絕損毀封包。

## 純顯示辨識與合成

不新增原版掛點。所有辨識只讀既有 indexed 畫面；不改原版記憶體、VRAM、鍵盤、亂數、讀檔或 Overlay 的失效流程。

場景沿用 015 四邊完整辨識與內部差異包圍，包含空白視窗。preserve、差異包圍及區域外的像素保留既有原版合成。若多頁同時符合四邊識別，整幀 HD 回退，不以列表順序選頁，也不繼續怪物替換。場景 PNG 的裁切區必須完全不透明。初始來源頁只是辨識基準；後續動畫或 UI 若影響識別邊界就回退，不能強制覆蓋。

沒有場景命中時，怪物用完整原始 row-major bitmap 比對。將目前 indexed 畫面暫存為逐列 CGA packed bytes，每來源選取非零 bytes 最多的連續 4-byte 窗口作候選索引，同分依 row-major 順序選第一個；只有完整矩形逐 byte 相同才可替換。x 按原版已證實的 4 像素對齊搜尋，y 為畫面列；完整矩形須在 `(0,0,320,151)` 內。這是 B005／B309 已證實的怪物底線，可避免與固定 y156、高32 的隊員圖混淆。全零 bitmap 拒絕；相同來源 bitmap 對應不同資產時拒絕載入；同身份同矩形先去重，其餘任何相交候選皆回退。每個通過 anchor 且落在允許區、即將執行完整 byte 比較的候選計一次，上限 10000；超限整幀 HD 回退，避免不可信 profile 造成不受限工作。

4-byte anchor 必須完全位於同一來源列，不能跨兩列交界；目前畫面的 anchor 也只在同一 packed 列內取樣。

每個手繪怪物只畫於命中的原矩形；先以目前色盤 index0 的 RGB 清除原圖，再以 PNG alpha 合成，PNG 的純黑像素視為透明底色。新細節可以畫於該矩形的原空白像素，不能越出矩形。不能塗掉相鄰怪物、隊員、文字、戰鬥結果或選單。完整 bitmap 未匹配、被後續繪圖遮擋、白化或清除狀態皆保留原版。全白來源與白化後圖像可能完全相同；這類來源資產可完整驗證載入，但不進 HD 候選，明示保留原版而不猜狀態。完整載入時逐像素核對，索引 0 的 bank1、bank2 都只有 0／3 兩種像素，因此兩個變體皆保留原版。其後才畫中文 Overlay。original／amber 主題的結果保持 015 行為，Shift+F12 與語言切換不變。

## 封包與身份

正式已批准 profile 保存於 `tools/package_art_assets.json`，僅含來源／圖像指紋及矩形，不含原版 bytes 或圖像。封包工具只接受該 JSON 的完整等值內容及所有已固定資產指紋，不能以自行改寫的 profile 通過。所有圖像由前端實際解碼及抽樣渲染後才固定身份。

package_files、package.sh、stage、finish、launcher 與 016 bundle 驗證同步支援完整 art 檔清單；檔名須在批准 profile 中且完整，不能只檢城鎮兩檔。launcher 及擷取先核 bundle 的必要檔名與全部 SHA，再由後端核 profile 與 PNG 真解碼。patch 不含 HD，本機完整三平台包含完整組，來源權利分類仍是 local-only original-derived art。參數 `--hd-dir` 及 `-art` 不變。

## 審查與驗收

兩輪唯讀審查先核對辨識／失效／界限與資料／證據。實作限 schema 2 載入、pure renderer 及必要封包清冊，不引入畫面／記憶體注入。

抽樣涵蓋正常城鎮／公會及戰鬥，原版／琥珀／手繪、繁中及其他語言往返。對照同一狀態的 steps、reads、完整 memory、VRAM；原版主題等於既有合成。手繪差異只能落在已辨識場景保護區外或完整怪物矩形，文字仍清楚。每類資產做完整載入與身份核對；原版所有怪物／場景不要求逐一正常到達，未量到清楚保留，不宣稱逐圖 parity。

必要反例：截斷／超長游程、PNG 真解碼失敗、錯原版／圖像 SHA、缺必要圖、越界來源／裁切、全零／重複／相交 bitmap、不匹配與白化回退、未知／重複 JSON 欄位，以及 patch 混入 HD 拒絕。既有 schema 1、015 原版／UI 保護與三平台封包測試依變更範圍回歸。

原型入口：`workplace/package-prototype/hd-all-prototype-r1/`。原版依據及可重生參考圖入口為 RE029；正式包／GUI／影片驗收依 013、014、016。未完成其他圖像或正式包時，不能把城鎮樣本稱為本規格全部交付。

兩輪唯讀契約及證據審查已閉合，最終皆為阻擋 0、應改 0、建議 0。報告為原型目錄的 `contract-spec-review.txt`、`evidence-spec-review.txt`；保留初查及修訂紀錄。READY 僅允許實作，不表示素材或封包已驗收。

實作資產組為 `workplace/package-prototype/hd-all-assets-r1/`，批准 metadata 為 `tools/package_art_assets.json`，profile SHA-256 `66bcad5436723cd49aa64478ba8d0feab4fcd84377bce8879b5b9d1eb17d8d7a`。12 PNG、四頁及 160 變體已完整真解碼、指紋及裁切核對；158 非全白來源逐 bitmap 辨識通過。所有裁切均在對應格內，保留可見門檻 RGB>30 的主體，最大比例誤差 0.00484155；較暗背景雜點不宣稱逐像素全保留。

兩輪實作唯讀審查報告為 `implementation-contract-review.txt`、`implementation-evidence-review.txt`，最終皆 0／0／0。已補跨來源同名指紋檢查、完整 JSON null 拒絕、必要欄位與矩形長度、Python 型別保留的批准比較，以及無色盤 index0 樣本時怪物回退。原版正常 draw consumer 的只讀矩形作為獨立允許域，`normal-r3/tests.log`、`normal-r3/normal-route-receipts.json` 記錄正常城鎮、公會、戰鬥共 750 組五語抽樣；完整 memory、VRAM、steps、reads 不變，original 等於既有合成，HD 像素差異在批准域內。早期僅四隻怪物的固定座標不能涵蓋九隻排列，前兩次驗證脚本失敗不計 PASS。正式封包、GUI 與影片依 013、016 完成前維持 READY。

## 正式本機交付抽樣驗收

本節描述既有正式包。目前原始碼另依 [020](020-party-hd-images.md) 支援戰鬥隊員手繪圖像，尚未併入本節的封包與影片。

三平台實際完整包核對完整 13 份圖像資產及固定 profile SHA-256 `66bcad5436723cd49aa64478ba8d0feab4fcd84377bce8879b5b9d1eb17d8d7a`，四場景與 160 變體完整打包。原有五語 750 組正常路線與唯讀合成證據仍有效。正式包另以正常城鎮、公會、戰鬥擷取核對 150 個原版狀態點，Linux 前端切換與 Wine 手繪城鎮可見；正式影片含手繪城鎮與正常怪物戰鬥，README 已替換正式包截圖。兩個全白變體、無法確認或遭原版視窗遮擋的部分保留原版，隊員與地圖仍按原版顯示。未正常到達的個別場景與怪物保留資產核對證據，不宣稱全數正常玩家路線都已觀察。平台操作限制見 013。

正式收據入口為 `workplace/package-prototype/formal-acceptance-v.1.0.0-20261005/`；交付入口為 `dist-all/v.1.0.0-20261005/`。`smoke/acceptance.json` 與根層 `SHA256SUMS.json` 列出平台範圍；字型獨立遮罩為 `font-mask/verification.json`，冷讀檔為 `save-r2/verification.json`，影片與字幕抽樣為 `visual-verification.json`。較早研究段落中的待驗狀態只描述當時收據，現況以本節為準。
