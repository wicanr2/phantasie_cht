# 015 顯示主題與手繪城鎮

狀態：CONFORMED（正式本機交付抽樣，平台限制見末節）。兩輪唯讀審查最終阻擋、應改、建議皆為零。前置：001、002、004、005 CONFORMED；013、014 CONFORMED。使用者已確認新增色盤主題切換，HD 圖像選彩色手繪、保留原版構圖。此規格只改顯示端，不改原版程式、輸入語意、規則、記憶體、顯示記憶體或存檔。

## 1. 圖像證據與資產

原版城鎮為 320×200 CGA；中央 `(0,8,320,184)` 的像素與 PELNOR.IBM 原始資料逐點相同，證據見 [RE028](../re/028-town-art-and-hd-preview.md)。頂、底各 8 像素是原版選單與城名，不在圖像替換區內。

使用者選定 `workplace/package-prototype/hd-town-preview-r1/pelnor-painted-r1.png` 的手繪方向。製作城鎮獨立圖像時去除兩條 UI、保留原版 BANK、INN、GUILD 與 M 字樣。原版既有招牌的勘誤見 RE028，不把它們刪掉。所有中文、游標、視窗框、角色與數字仍由原版加覆繪繪製。

本機資產：`workplace/package-prototype/hd-town-assets-r1/town-painted.png`，1653×952，2524255 bytes，SHA-256 `f520bd1e2fdb112e630ac05c5ac6006f0ae23607d95f1c7c4deaf5a0e03cec06`。來源與矩形在同目錄 asset-proof.json；生成提示也保存同目錄。資產為原作參考衍生圖，只留本機，不加入 Git、可散布 patch 或公開 Release。選定樣圖保存本機並在版控文件記錄其位置與指紋；專案素材邊界優先於技能一般性的圖像入版控建議。

其餘八個候選圖像來源的解碼與數量仍未知，不能聲稱全部圖像 HD 完成。本規格先接入已證實的城鎮圖像，其他場景安全回退原版；後續圖像須獨立證據與資產，不用城鎮圖覆蓋。

## 2. 主題與按鍵

新增顯示狀態：original、amber、hd。original 不改像素，是既有同狀態驗收基準。amber 是琥珀單色顯示，對原版加覆繪後的 RGB 使用整數亮度 `(77R + 150G + 29B) >> 8`，映為 `(L, 3L/4, L/4)`，透明度不變。hd 只用已驗證的城鎮圖像，其他畫面不改原版。

Shift+F12 切換已載入的主題，普通 F12 保持語言切換，F11 保持全螢幕。F2 至 F10 繼續傳給原版；F1 依 [019](019-frontend-help.md) 保留給操作說明。主題切換不排入原版 Gate、不改語言或停止原版。沒有有效 HD 資產時循環只有 original、amber；資產整組先驗證、載入，再一次切換，不中途讀半份圖。

後端命令列新增 `-art <目錄>`、`-theme auto|original|amber|hd`。auto 在有效資產存在時選 hd，否則 original；直接執行後端時，明示 hd 而可選資產無效會診斷並回原版，不中止基本遊玩。完整封包先走 §5 的必要資產預檢，不能用後端回退放行損毀的包。視窗標題顯示目前語言與主題，產品畫面不寫解析器或權利檢查細節。

## 3. 唯讀載入

art 目錄只有 profile.json 與圖像。profile schema 1 列 source_file 的 basename、固定 source bytes／SHA-256、source_rect、image 的 basename、image bytes／SHA-256。原版 source_file 從 Session 啟動時已指定的唯讀 root 讀取，不從工作目錄猜檔，也不將原版圖像另包入 art 目錄。

拒絕絕對資產名稱、斜線、反斜線、dot／dotdot、符號連結、額外欄位、壞 hash、非 PNG、PNG 超過 16 MiB、任一邊超過 4096 或總像素超過四百萬。source 應為固定 16384 bytes 的 CGA 原始頁；矩形合法且足以留四邊各 4 像素的識別條。圖像寬高比與矩形相對誤差不得超過 0.5%。全部驗證後才對外提供 HD 狀態。

原作 basename 與來源 SHA 放在 Phantasie 專案 profile，dosgolem 通用化的顯示程式不硬編來源檔名或存入原作 bytes。字型或手冊資料不參與圖像辨識。

## 4. 視窗保護與合成

每次 Draw 使用 Session.Frame 的原始 indexed／RGB，照常維護覆繪；不將換色或圖像結果餵回 Frame、事件分類或 Audit。original 的 Compose 行為與既有前端相同。

HD 圖像辨識以原始 indexed 做精確比較，不以譯文、場景名、模糊分數或可修改的遊戲記憶體作判定：

1. 原版 source 以 RE028 的 CGA 位址公式解出中央區域的色碼。
2. 當前矩形四邊各 4 像素的所有色碼必須完全與 source 相同。任一差異即本幀不用 HD。這是保守的圖像邊界辨識，不宣稱其他場景的語意已知。
3. 矩形內所有不同像素的最小包圍矩形作為保護區；沒有差異則沒有保護區。整個包圍矩形保持原版 RGB，包含其中恰好與背景同色的視窗空白處；不逐像素穿透視窗。多個視窗會保護其聯集包圍範圍，允許多保留原版。
4. 只在 source_rect 內、保護區外繪 HD；這些原版像素已逐點與原始城鎮相同。圖像以固定尺寸取樣到 2 倍畫布，不改源圖或原始像素。
5. 最後繪現有覆繪 Layer，保持繁中、其他語言、反白與數字在圖像上方。琥珀換色在 original 加覆繪後做；HD 與琥珀不疊加。

辨識失敗、本機來源缺席、圖像損毀或模態視窗碰到邊界皆回原版。原版清除或重繪每幀重新比較，不保留過時的 HD 背景或視窗遮罩。

## 5. 三平台封包

013 的 bundle schema 1 增加可選 art 目錄欄位，缺席保持舊行為。包內宣告 art 時，profile 與 PNG 是必要資產，啟動器依既有 013 清冊預檢；缺檔或 SHA-256 不符即拒絕該封包，不計啟動成功。通過預檢後只把已驗證的 art 路徑傳給後端，後端的來源或場景辨識失敗仍可回退原版。art 只允許有 local_original 的本機包；patch 不接受 art 欄位或任何倚天／HD 素材。公開包仍有 original、amber 的顯示程式。

package.sh／stage 新增可選 `--hd-dir`，明示時只可與 --local 並用，只唯讀掛入 full-local。stage、bundle、finish 及來源紀錄核對 asset 集合、檔案 hash、圖像／原版來源身份及 local-only；圖像 bytes／SHA 必須等於 §1 已由前端解碼的固定資產，不能以自填 profile 接受其他 PNG。不複製研究日誌或整個研究目錄。原版沒有修改；存檔與資料位置遵守 013。

## 6. 審查、實作與驗收

先兩輪唯讀審查契約對程式、資料對證據，報告在 `workplace/package-prototype/hd-contract-review-r1.txt` 與 `hd-evidence-review-r1.txt`，無阻擋或應改才 READY。實作涉及 dosgolem 指定分支的 `apps/phantasie/presentation.go` 與互動前端；遊戲專屬 profile 及封包工具在 Phantasie 專案。沒有新的 engine 版本解析器、遊戲規則或存檔格式。

最小充分驗收：

- 自製圖像／CGA 資料測單一像素邊界負例、內部視窗包圍、空白保護、邊界回退、三主題原像素、損毀來源／PNG／path 反例。
- 正常城鎮、公會視窗、返回、地圖與地牢路線，原版記憶體及顯示記憶體不變；HD 差異只在 source_rect 內、保護區外，original 的 PNG 與既有前端相同。未辨識場景無 HD 差異。
- Linux GUI 的 Shift+F12 切換主題、F12 切語言、返回後背景與原版視窗／字形仍正確；日韓與英文抽樣。新的 hotkey 不使 Gate 多一次讀鍵。
- 三平台真實包逐項核對 art 必要檔與權利隔離，GUI／存檔冒煙依 013；單元測試或 stage 存在不代替正式包。
- 影片須有真正原版執行、正常輸入與新主題畫面；圖片樣圖不算遊玩影片。逐格擷取、聲音與正式影片驗收另依推廣契約，不將此規格當影片完成。

本規格的 CONFORMED 範圍僅主題與已列城鎮圖像。README 與交付清冊明示其他圖像未 HD 化，不以綠色測試稱原版像素一致。原版、字型與本機衍生圖像不進 Git，收尾驗證 UID/GID、Docker 清理、指定分支與使用者授權的 commit／push。

## 7. 目前驗證

顯示單元測試通過，含內部視窗空白、單像素邊界、原版 baseline、琥珀色值與八種無效素材。封包回歸 53 項通過，啟動器測試包含必要 HD 清冊、同長度損毀與 patch 拒絕；正式包尚未產生。

正常路線 town、guild、dungeon-message、lang-switch 共 145 個停點，90 個可使用 HD。每次合成前後核對完整原版記憶體 SHA-256、顯示記憶體與讀鍵次數相同；original 逐 byte 等於舊 ComposeImage，HD 差異在 source_rect 內及保護區外。可重跑研究程式為 `workplace/package-prototype/hd-town-assets-r1/verify_routes.go`，收據在 `hd-normal-r1/normal-route-verification.json`。程式在 Go 工具容器內以唯讀原版、route、text、font、art 輸入建置，輸出另掛 workplace 目錄。

Linux 真實按鍵證據在 `workplace/package-prototype/hd-gui-r2/`：Shift+F12 依序切原版、琥珀、手繪，語言保持 zh-TW；F12 五語循環保持手繪，公會選單邊界失配時回退 CGA，返回恢復手繪。titles.txt 與 PNG 已核對。早期 gui-r1 短暫 Shift 的自動操作失敗不計驗收；以持續按住 Shift 乾淨重跑通過。早期 scene-probe 廣泛分析外層逾時不計 PASS，資料審查使用另行終端 exit 0 的獨立窄 probe。

實作複核入口：`workplace/package-prototype/hd-implementation-contract-r1.txt`、`hd-implementation-evidence-r1.txt`。本規格仍 READY；正式三平台包及影片驗收尚待完成。

## 正式本機交付抽樣驗收

正式 Linux 完整版經真實前端按鍵切換原版、琥珀與手繪主題，五語城鎮、公會開啟及返回抽樣通過。正式包的圖像身份已核對，手繪城鎮與怪物出現在實際遊玩影片，README 使用正式包截圖。其他場景及怪物的完整資產契約見 018；正常玩家路線未到達的個別場景不宣稱已實機觀察。平台限制見 013。

正式收據入口為 `workplace/package-prototype/formal-acceptance-v.1.0.0-20261005/`；交付入口為 `dist-all/v.1.0.0-20261005/`。`smoke/acceptance.json` 與根層 `SHA256SUMS.json` 列出平台範圍；字型獨立遮罩為 `font-mask/verification.json`，冷讀檔為 `save-r2/verification.json`，影片與字幕抽樣為 `visual-verification.json`。較早研究段落中的待驗狀態只描述當時收據，現況以本節為準。
