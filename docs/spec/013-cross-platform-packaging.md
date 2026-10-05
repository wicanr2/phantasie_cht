# 013 三平台交付與封包驗證

狀態：READY（2026-10-05）。第一、二期已依 [分期目標](../goals/001-phases.md#抽樣驗收範圍)完成抽樣收斂。本規格處理第三期。新版契約與資料兩輪唯讀複核無阻擋或應改；正式封包及平台冒煙尚未完成。

## 1. 依據與邊界

- [AGENTS.md](../../AGENTS.md) §9、§10 與 `/home/anr2/cht/AGENTS_DOSGOLEM_CHT.md` §15 是打包契約。輸出目錄依 `/home/anr2/.codex/knowledge-base/local/retro-remake-dist-all-output.md`，版號依同目錄的 `retro-remake-release-versioning.md`。
- 引擎從已推送 `phantasie-cht-overlay` 的固定 commit 用 `git archive` 匯出。不從其他遊戲包複製素材、字型或啟動參數。
- 可散布包不含原版、手冊、答案或私人路線。本機資料包只在 `full-local/`，不入 Git、不上傳。repo 維持 private；公開 Release、影片與轉公開另需授權。
- 原版啟動鏈、輸入、規則、存檔及覆繪保持原契約，不自動回答手冊題。

## 2. 待決與執行閘門

1. 字型散布條款：雙授權及作者聲明已核對，見 [font](../../font/README.md)。OFL 1.1 或 GPLv2+ 含字型例外待使用者選定。沒有答覆時不得代選、採預設或建立正式字型散布包。兩種選項共用的工具與啟動器可以在規格 READY 後實作；合成測試不代表散布條款已定案。
2. 完整版號與本機 tag：使用者 2026-10-05 定案 `v.1.0.0-20261005`，作首個正式本機交付。格式為 `v.<主版>.<次版>.<修訂版>-YYYYMMDD`，日期採 Asia/Taipei。不以原型名代替版號，不移動已發布 tag。版號由封包工具的必要參數輸入，實作與合成測試不建立 tag。
3. AppImage runtime 附帶程式庫的來源與條款須對應固定二進位核對，不只附 runtime 自身 MIT 文件。正式包採 §9.1 的自行重建輸入，原型預編譯 runtime 僅作歷史對照。缺必要授權、來源或精確雜湊，正式打包失敗。

## 3. 入口與乾淨輸入

入口為 `tools/package.sh [all|linux|windows|macos]`；可另明示本機資料模式，預設只產生不含原版的包。腳本編排 Docker、Git 清潔檢查及固定輸入；分析、建置、資料複製、封裝與掃描全部在容器，精確參數見 §17。

前置檢查：

- 專案與引擎工作樹乾淨、作者信箱 `wicanr2@gmail.com`、tag 精確指向專案 HEAD，引擎 commit 等於已推送指定分支。
- 版號完整 regex 比對，缺版號或不符立即失敗。程式、tag、manifest、封包及 `dist-all/<版本>/` 使用同一完整字串。
- 固定 Unifont tar、hex 成員及授權輸入雜湊；四語 catalog 的欄數、placeholder、保護清單、字型覆蓋與格式檢查通過。
- 原版掃描目錄必須存在，只讀檔名及 SHA-256。輸入缺席不能當作無外洩。
- 掛載來源形態及 UID/GID 逐項核對。原版、匯出來源、模組快取及字型 tar 唯讀；只有明確 stage、編譯快取及輸出可寫。

Go 離線建置採 `GOPROXY=off`、`GOSUMDB=off`、`-mod=readonly`、固定版本與 `-trimpath`。容器有 `--rm`、資源限制、外層逾時、network none 及日誌上限。不清除其他版本、其他專案或既有發布檔。

## 4. 共用內容與字型

- 執行期清單為四語 `ui.<lang>.tsv`、`prose.<lang>.tsv`、`manual.<lang>.tsv`，以及共用 `protected.tsv`；不整批帶入 `text/` 或工作區。
- 不含答案變體以正式 `manual-labels.<lang>.tsv` 的三欄資料產生同內容的執行期 `manual.<lang>.tsv`，只允許兩個標題鍵。現有 loader 不讀 manual-labels，這項轉換在封裝階段完成，不改共用 loader；該變體缺答案時仍依 006 保留原版題目與選項。本機變體才加入完整本機答案表。包內檢查須逐鍵確認兩個標題及禁止答案鍵，不能只檢查語言已啟用。
- 字型由該變體實際附帶的正式譯文重建。不含答案包不用本機答案表當字元來源；GOLEMFNT 格式及每語字元覆蓋須核對。
- 本機變體另加入已確認原版資料及四語答案表，存檔另放可寫狀態目錄。手冊掃描影像不隨包。
- 附專案 RRSAL-1.0、dosgolem 原授權、Go 與第三方全文。依各平台 `go version -m` 取模組聯集，檢查模組頂層及內嵌元件授權。缺文件即失敗。
- Linux 包另附 §9.1 的 runtime 配套來源：完整上游來源壓縮檔、Alpine 修補檔與 APKBUILD、編譯處置及腳本、工具版本與實際連結清單，以及附庫與 GCC 啟動物件的全文條款。來源只附文字與公開程式碼，不帶 SDK 的預編譯 APK。各元件沿用原條款，不能改成專案 RRSAL-1.0；僅附上游網址不算配套來源。
- 附選定字型條款、完整作者聲明及來源版本，不將第三方字型改授權為 RRSAL-1.0。
- 讀我寫明原版放置、F11／F12、五語、存檔目錄、抽樣限制、音訊無輸出、日韓機器輔助未經母語者校對及平台測試邊界。

## 5. 平台形式

| 平台 | 形式 | 架構核對 |
|---|---|---|
| Linux | AppImage，type2 runtime 加 SquashFS | ELF x86-64；runtime 大小及 SHA-256 固定 |
| Windows | ZIP，GUI 子系統可執行檔 | PE32+ AMD64，不依賴主機 Go |
| macOS | ZIP 內未簽章 `.app` | Mach-O universal 含 x86-64、arm64 |

Windows 中文 ZIP 項目須有 UTF-8 旗標，`README.txt` 採 UTF-8 BOM、CRLF；批次檔採 ASCII、CRLF、不加 BOM。macOS 說明未簽章及首次開啟方式，未做真機測試不能宣稱通過。

Linux 原型實查直接依賴 `libX11.so.6`、`libm.so.6`、`libc.so.6`，最高符號需求為 GLIBC 2.34。這些由宿主系統提供，不隨本包複製；另須可用的 X11 與 OpenGL 顯示環境。正式封包仍須重查實際二進位的 DT_NEEDED、glibc 符號及動態載入項，明列最低 ABI。Linux 驗證需另選有 Xvfb／顯示執行期、沒有 Go 與開發套件的既有容器；目前 Go 建置映像的 GUI 原型不能代替這項封包檢查。未驗證的發行版不宣稱已支援。

## 6. 啟動與存檔

現有前端需明示 `-root`、`-text`、`-font`，見 [005](005-play-frontend-and-receipts.md)。Ebiten 初始化早於旗標解析，無 DISPLAY 時連 `-h` 都會先失敗。因此採用專案內不連結 GUI 的原生啟動器，完成版本輸出、路徑與匯入預檢後才啟動原有前端。不改 DOS 核心、遊戲規則或覆繪。

### 6.1 資料定位

| 平台 | 包內資料與後端 | 未匯入時的預設原版來源 | 預設使用者資料根 |
|---|---|---|---|
| Linux AppImage | AppDir 的 `usr/bin/` 下後端、text、font | AppImage 外檔旁 `original/`；本機包用包內 `original/` | 絕對路徑的 XDG_DATA_HOME 下 `phantasie-cht`；未設定則使用者家目錄 `.local/share/phantasie-cht` |
| Windows | 啟動器旁後端、text、font | 啟動器旁 `original/` | LOCALAPPDATA 下 `phantasie-cht` |
| macOS | 後端在 Contents/MacOS，text、font 在 Contents/Resources | `.app` 外檔旁 `original/`；本機包用 Resources/original | 使用者 `Library/Application Support/phantasie-cht` |

預設位置從實際執行檔或 AppImage 的外檔位置取得，不使用呼叫者工作目錄。明示 `-root`、`-data`、`-state` 的相對路徑才按呼叫者工作目錄解析。路徑依原生平台解析，支援空白、中文及 Windows 跨磁碟機。缺少平台資料根、非絕對的 XDG_DATA_HOME 或無效路徑時明確失敗，不默認寫入當前目錄。

資料根下的 `original/` 是已匯入原版，`saves/` 是可寫狀態，匯入清冊及鎖在兩者之外。啟動前端時 `Root=original/`、`Scratch=saves/`；讀檔仍由既有 DOS 層優先 Scratch，再查 Root。Root 永不混入存檔。

明示 `-data` 優先於平台預設資料根；`-root` 優先作來源。已有有效匯入時使用既有副本，不因仍有來源而重新複製。明示 `-state` 可使用既有相容狀態目錄，否則用 saves；狀態根須與來源及匯入根不重疊，不隱性搬移或覆寫舊前端的存檔。資料根若已有舊前端的平面存檔，停止並說明可用另一個 `-data` 配合原位置的 `-state`，不能默默開始空隊伍。

### 6.2 匯入生命週期

1. 支援來源以 [001 輸入清冊](../re/001-input-inventory.md) 的固定版本為基準。封裝產生的來源清單只含檔名、大小、SHA-256，不含原始 bytes 或文字。首次來源需符合已確認清單，包括主程式、overlay 與啟動鏈；版本或資料不符就停止，不猜補。
2. 預檢所有路徑、型態、唯讀來源、可寫狀態與必要譯文／字型後才匯入；拒絕來源與狀態相同、互為祖先、符號連結或檔案硬連結重疊，規則沿 005 §10 的收據隔離契約。
3. 原版只從來源讀取，複製到資料根下本次獨占的暫存目錄。複製後逐檔重驗清單，成功才提交為 original；失敗只移除本次暫存，不更動來源、既有匯入或存檔。
4. 再次啟動先重驗已匯入原版及清冊，通過便使用它，不要求外部來源仍在。不重新複製初始名冊或存檔，不刪除 Scratch。已匯入資料不符時停止，讓使用者提供另一個明示資料根或恢復正確來源，不自動替換。
5. 匯入與遊玩期間同一資料根及狀態根只允許一個實例。以 OS 釋放式檔案鎖隔離；程序正常或異常結束均由 OS 釋放，不以猜測 PID 或任意刪除鎖檔來放行。
6. 所有預檢完成後才啟動前端，明示包內 text、font、Root、Scratch 及原版批次鏈。只有前端接收正常鍵盤，啟動器不送作答、跳頁、座標或測試輸入。

### 6.3 錯誤與版本

版本輸出含完整版號及引擎 commit，成功 exit 0；說明 exit 0；參數不符 exit 2；缺來源、版本不符、目錄不可寫、匯入失敗或鎖衝突 exit 1。以上在 GUI 初始化前完成。Windows 雙擊與 macOS Finder 啟動的失敗須有可見說明，包含可照做的放置位置；stderr 日誌不能作唯一回報。Linux 命令列提供同一原因。

須測不同工作目錄、空白及中文路徑、唯讀來源、不可寫狀態、跨磁碟機、已有匯入而來源缺席、來源改變、匯入中斷、已有存檔保留與冷啟動讀回。版本或說明模式不啟動後端，不開 DOS 原版，不建立匯入及狀態。

以上先經 READY，實作後用既有正常路線確認原版狀態、顯示、輸入及存檔 bytes 不變。

## 7. 封裝後檢查

1. 解出實際 AppImage／ZIP，核對預期檔案、架構、執行權限、版本、語言及第三方文件。
2. 不含原版包以原版檔名及 SHA-256 掃描；另掃手冊、答案、私人路線、不可散布字型及研究輸出。命中即刪除本次失敗產物並退出。加入已知禁止檔的合成副本須被拒絕。
3. 本機包分類並核對原版及提示表，不用它通過可散布包掃描。
4. 用包內 catalog 及 font 載入每語，須明確 PASS、全通道啟用，SKIP 不算。缺必要字型或 catalog 的副本須失敗。
5. 每包記大小、SHA-256、平台、架構、權利分類、兩 repo commit、工具版本及輸入雜湊。manifest 放 `dist-all/<版本>/SHA256SUMS.json`，中間物留 workplace。

## 8. 冒煙與完成界線

Linux 從正式 AppImage 解出，在有界 Xvfb 容器以每語冷啟動，正常按鍵到標題及城鎮主選單。核對畫面、沒有語言停用、存檔位置及原版不變，再抽樣 F12 往返、存檔及冷啟動讀回。trap 清理 GUI 子程序，結果在 `dist-all/<版本>/smoke/`。

Windows 用既有 Wine 測實際 ZIP 內容與路徑，記明 Wine 驗證。macOS universal 靜態檢查不算真機啟動；缺真機時依模板 §15.2 保留已知限制。

封包、掃描、語言載入、Linux GUI、Windows 路徑、授權及 manifest 通過後才可 CONFORMED，範圍限實際平台證據。公開 Release 不屬本機交付閘門。

## 9. 工具鏈原型證據

原型在 `workplace/package-prototype/`，不入版控、不作正式交付：

| 項目 | 值 |
|---|---|
| 專案基準 | `dabb3d62bce0fae2ec461f3da15ef95c12a6fa34` |
| 引擎匯出 | `8d9807df4f191c02eef46a22b6f7bbecb426ef5b` |
| Go | 1.24.13，image `083e45e6bc0f01ca46ba0774581572c80a607120431b530de72cdd6ffb36f2f7`（`psychicwar-go-ebiten:latest`） |
| macOS | image `0f50c77c732087b104b3aadc3aecb352054aa37dee8e1d293523a66dfa02ba61`（`psychicwar-osxcross:latest`）；Darwin 24.5，deployment 11.0 |
| AppImage | image `2b6f78b5cf3d3ce8f1a2756fe81303d469d545091c672ff1fb7923cbd6aa88af`（`psychicwar-appimage:latest`）；SquashFS 4.5.1 |
| runtime | 944632 bytes，SHA-256 `1cc49bcf1e2ccd593c379adb17c9f85a36d619088296504de95b1d06215aebbf`；自身版本輸出 commit `75849dc` |

五份二進位已試編譯：Linux、Windows、兩個 macOS thin binary 及 universal。`inspect.py` 獨立解析 ELF、PE、Mach-O 標頭，核對架構、Windows GUI 子系統及 UID/GID。六個實際 Go 模組聯集、Go、專案、引擎及字型共收集 20 項授權輸入，清冊為 `toolchain-verification.json`。這只證明編譯及架構，不證明正式封包可用。

無頭收據工具另以 CGO_ENABLED=0 試編譯 Linux、Windows、macOS x86-64 及 arm64。五語 Linux 前端原型各冷啟動，以正常按鍵擷取標題及城鎮／公會選單共十張畫面，日誌沒有語言停用。原型使用建置映像及現有本機資料，未驗證正式包、匯入啟動器或存檔生命週期。

runtime 的 MIT 與附帶程式庫清單見 [固定 commit 授權](https://github.com/AppImage/type2-runtime/blob/75849dce7cc37e4319b633df1f116ca895c71a12/LICENSE)。同 commit 的[來源壓縮檔](https://codeload.github.com/AppImage/type2-runtime/tar.gz/75849dce7cc37e4319b633df1f116ca895c71a12)已留存研究目錄，31068 bytes，SHA-256 `b7af4960da4b90364e935a3281d04fad6560da4813c012414fa2f738291ad443`。來源 `src/runtime/Makefile` 還列有 mimalloc，但 LICENSE 的附帶清單沒有列；Docker recipe 只固定 Alpine 3.21，未鎖定 APK 版本。舊預編譯輸入的附庫版本仍未補齊，正式包改用 §9.1 的自行重建版本；字型條款仍待使用者選定。

### 9.1 來源可回查的 runtime 重建

舊預編譯輸入不再作正式包來源。固定 commit 的官方 build 為 [28063784345](https://github.com/AppImage/type2-runtime/actions/runs/28063784345)；API 現存 artifacts 為零，匿名下載日誌回傳 403。這只證明該管道沒有取得來源版本，不宣稱其他憑證或管道也不可用。

自行重建版本仍使用相同 runtime 原始碼，只調整 include／library 搜尋根、加入連結 map，並以完整 commit 作版本輸出。原始 Makefile、處置 patch、版本、ELF、map、APK 實際安裝清單及兩次乾淨重建輸出留在 `workplace/package-prototype/runtime-rebuilt/` 與 `runtime-rebuilt-replay/`。輸出 944632 bytes，SHA-256 `0341f742081a99f00f6c8654d742e470e85c66dafabd17d851ab5b662dc7f511`；兩次逐位元組相同，三份自行建出的靜態庫雜湊也相同。

| 元件 | 實際版本 | 來源 |
|---|---|---|
| runtime | commit `75849dce7cc37e4319b633df1f116ca895c71a12` | 固定上游來源 tar |
| libfuse | 3.15.0 | 上游 tar、runtime 的 mount.c patch；tar SHA-256 `70589cfd5e1cff7ccd6ac91c86c01be340b227285c5e200baa284e401eea2ca0` |
| squashfuse | 0.5.2 | 上游 tar，SHA-256 `db0238c5981dabbd80ee09ae15387f390091668ca060a7bc38047912491443d3` |
| musl | 1.2.5-r11 | 上游 tar、Alpine APKBUILD 及全部修補／附檔 |
| zlib | 1.3.2-r0 | 上游 tar 與 Alpine APKBUILD |
| zstd | 1.5.6-r2 | 上游 tar 與 Alpine APKBUILD |
| mimalloc2 | 2.1.7-r0 | 上游 tar、Alpine APKBUILD 及命名 patch |

Alpine 官方索引已存檔；四個元件共 20 個來源輸入逐一符合不可變 APKBUILD 的 SHA-512，見 `runtime-library-source-inputs.json`、`runtime-rebuild-source-profile.json`。實際連結 map 包含上述六個附庫元件，以及 musl／GCC 的啟動物件；不只依 Makefile 推定。GCC 14.2.0 的 [啟動物件來源](https://raw.githubusercontent.com/gcc-mirror/gcc/releases/gcc-14.2.0/libgcc/crtstuff.c)、GPLv3 與 Runtime Library Exception 3.1 也已存檔。13 項授權／來源輸入在 `runtime-license-inputs.json`。

重建使用既有 Alpine 3.21.7 基底，工具層 image `41af06226661cd56537db9bfaefcbb2d2a88212a30dfa168be98e0b6231de8f8`（`phantasie-runtime-builder:source-r1`），Clang 19.1.4、GCC 14.2.0；程式編譯在 user 1000:1000、network none、3 GiB、2 CPUs、128 程序上限及有界逾時的一次性容器。打包仍沿用既有 AppImage image，將核對後 runtime 唯讀掛到 `/opt/runtime-x86_64`，不另建同功能映像。

gzip／zstd 的合成 AppImage 已確認 offset、解出內容、執行權限、AppRun 及中文／含空白參數。這只驗證 runtime 工具，不算正式遊戲包、GUI 或原版同狀態 PASS。正式 Linux 封包明示使用已抽測的 gzip 壓縮。

## 10. 實作位置與審查

實作位於 `tools/` 的譯文整理、掃描及封裝驗證工具，以及專案 `apps/phantasie/` 的原生啟動器；封裝編排入口 `tools/package.sh` 見 §17。啟動器不連結 GUI，以子程序執行固定引擎後端；引擎保持既有前端與收據工具，不改 main、DOS 核心或其他遊戲。文件沿用本規格、CONTEXT、WORKLOG、README 及字型說明。

無頭收據工具隨各平台包放在 tools 子目錄，是命令列工具；版本、架構、模組及授權也納入封包清單，驗證資料缺席時仍依既有契約 SKIP，不附私人作答路線。其正常 GUI 對拍用途與既有規格不變。

兩輪唯讀審查分契約對程式、資料對證據；只寫 workplace 報告。主代理處理阻擋及應改後才能升 READY。版號已定案；字型條款待決只阻擋正式打包與 tag，不阻擋已授權且兩種選項共用的工具實作；不建立 Release。

本輪契約複查已確認 §4 的執行期資料、§5 的 Linux 依賴、§6 的路徑及匯入生命週期，以及無頭工具交付範圍，阻擋與應改均為零。報告在 `workplace/package-prototype/contract-review.txt`；這只確認草案契約補全，不是實作或正式包 PASS。

資料複查也確認四份收據原型的架構、Windows 命令列子系統及零外部 Go 模組，以及五語 GUI 擷取與 runtime 來源限制，阻擋與應改均為零。報告在同目錄的 `evidence-review.txt`；封存入口為 `prototype-verification-manifest.json`，不覆寫先前抽樣或工具鏈清冊。

§9.1 新版 runtime 與執行閘門另由 `runtime-contract-review.txt`、`runtime-evidence-review.txt` 兩輪唯讀複核，阻擋、應改及建議均為零。資料角度直接比對二進位、來源／授權成員、SDK 靜態庫及兩份合成 AppImage；三份自行建庫只交叉核對兩輪原始雜湊收據，未第三次重建。據此升 READY，不把原型計為正式封包驗收。

## 11. 共用譯文整理工具的驗證

[tools/package_text.py](../../tools/package_text.py) 依 §4 準備 13 份指定執行期檔案。預設從 manual-labels 選出兩個標題，不讀本機 manual；本機變體才明示讀取完整提示表。兩種輸出皆保留正式 ui、prose 與 protected 的原始 bytes，清冊列版號、筆數、雜湊及權利分類。輸出須為新目錄；缺資料、欄數或鍵集合不符、來源為符號連結、路徑重疊與錯誤版號均拒絕，不修改來源或既有輸出。

[合成測試](../../tools/tests/package_text_cases.py) 8 項通過。兩種實際中間輸出各 13 檔，由獨立 CSV 讀取及 bytes 比對核對：每語 ui 678、prose 1044；無答案 manual 僅 2 列，本機版 156 列。乾淨合成匯出僅把答案模板加入篩選清單，突變目標恰好一次，獨立字面期望按預期失敗。輸入與既有輸出保留反例也通過。

收據為 `workplace/package-prototype/package-text-verification.json`、`package-text-tests.log`、`package-text-mutation.log`；該輪封存入口為 `runtime-phase-verification-manifest.json`。原生啟動器的後續實作見 §12；完整封包、發行字型及正式平台冒煙尚未完成，013 維持 READY。

## 12. 原生啟動器與研究抽測

實作入口為 [main.go](../../apps/phantasie/launcher/main.go)，獨立 Go 模組在 [go.mod](../../apps/phantasie/launcher/go.mod)。不連結 GUI，先核對包內檔案、支援原版、匯入及存檔隔離，再以子程序啟動固定引擎前端。70 筆 [來源清單](../../apps/phantasie/launcher/original.tsv) 與 001 清冊逐列相符，只含檔名、大小及 SHA-256，沒有原版 bytes 或答案。

在固定 SDK 容器內以 `GOPROXY=off GOSUMDB=off`、唯讀模組快取與 `go build -mod=readonly -trimpath` 建置。必要注入參數為 `-ldflags '-X main.releaseVersion=<完整版號> -X main.engineCommit=<40字元commit>'`；Windows 另加 `-H=windowsgui`。模組只依賴固定的 `golang.org/x/sys v0.36.0`，其兩筆 go.sum 與固定引擎相同。

封裝工具須產生 `bundle.json`。Linux／Windows 放啟動器旁；macOS 放 `Contents/Resources/bundle.json`，路徑以 `Contents` 為基準。格式如下，省略的資產須由工具按實際 bytes 填齊，不能直接使用這個示意：

```json
{
  "schema": 1,
  "version": "v.1.0.0-20261005",
  "engine_commit": "8d9807df4f191c02eef46a22b6f7bbecb426ef5b",
  "backend": "phantasie-play",
  "text": "text",
  "font": "font",
  "assets": [{"name": "phantasie-play", "bytes": 0, "sha256": "由實際檔案計算"}]
}
```

必要資產為後端、13 份執行期譯文與四份字型，共 18 份。每份都有相對路徑、大小及 SHA-256；錯版、缺檔、雜湊不符、未知欄位、路徑跳脫或重複名稱均拒絕。本機變體可增加 `local_original`，指定包內相對原版目錄；原版仍先經 70 檔核對及複製，不直接作存檔根。

匯入使用本次獨占暫存目錄、逐檔重驗及同資料根的原子 rename。清冊在 `data/import.json`，存檔在 `data/saves` 或明示 `-state`。合法匯入不要求來源內容仍有效，不重置存檔。拒絕存檔／資料根的符號連結、特殊檔案及連結數大於 1 的檔案，也比對實際檔案身分。Windows 的目錄列舉可能沒有檔案 ID，因此重新 `Lstat` 取得身分；沒有 Wine 特判。

Unix 前端繼承兩份 flock 描述，啟動器異常結束而前端仍在時繼續持鎖。Windows 前端先以 CREATE_SUSPENDED 建立，加入設有 KILL_ON_JOB_CLOSE 的 job，再恢復執行。這項 OS 契約見 [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)及[程序建立旗標](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags)。版本、說明及參數檢查均在前端初始化之前完成。

| 驗證 | 結果與範圍 |
|---|---|
| Linux 合成測試 | 16 個頂層測試通過，包含匯入失敗、已匯入讀回、存檔保留、舊目錄、必要資產、硬連結、重複啟動與父程序終止後持鎖；含一個子程序助手入口，不作玩家功能數量 |
| 負對照 | 同長度資料損毀、逐一移除 18 份必要資產均拒絕；乾淨複本只移除一處連結數限制，獨立存檔期望按預期失敗 |
| Windows／Wine | 15 個代表測試通過，含 C:/E: 跨磁碟機讀回、中文／空白 argv、硬連結、冷啟動及 job 終止；最終測試輸入 guard 另核對，版本與說明模式另以 GUI 子系統原型執行 |
| Linux 正常畫面 | 從不同工作目錄、中文／空白資料根冷啟動，以正常按鍵到繁中標題及公會選單，沒有語言停用；腳本最後送 SIGTERM，確認後端被終止及無遺留，不算遊戲正常 exit 0 |
| macOS | 兩種架構及 universal 原型只核對標頭與內容，未做 macOS 真機啟動 |

契約及資料審查報告為 `launcher-contract-review-r3.txt`、`launcher-evidence-review-r3.txt`；較早報告及失敗紀錄保留。封存入口為 `workplace/package-prototype/launcher-phase-verification-manifest.json`。這些是啟動器及研究布局的證據，沒有新增遊戲同狀態 A/B，也不代替正式 AppImage／ZIP、發行字型、五語冒煙及封包存檔驗收。013 維持 READY。

## 13. 封包外洩掃描工具

[package_scan.py](../../tools/package_scan.py) 處理 §7 的外洩邊界。Docker 內指定 `--scan` 與 `--original`，掃描來源須完整符合 001 的 70 檔大小及 SHA-256；缺席或錯版直接失敗。掃描已解出的目錄、ZIP 或 tar，不建立交付包或刪除輸入。封裝編排工具仍須在掃描失敗時清理本次失敗產物。

預設拒絕原版檔名與雜湊、original 目錄、手冊 PDF、作答路線、研究目錄、答案資料列與答案模板來源。無答案 manual 表只接受兩個合法標題。清冊包含一個空檔，SHA-256 也照常比對，因此沒有識別力的空檔同樣不能出現在未核對的封包內容中。

ZIP／tar 逐項檢查名稱、重複項目、符號／硬連結、特殊檔案及路徑跳脫；ZIP 非 ASCII 名稱須有 UTF-8 旗標，加密項目及帶資料的目錄拒絕。改名的壓縮檔按實際格式辨識，未列為固定來源的巢狀 ZIP／tar／gzip 繼續掃描；已辨識而未支援的 7z、RAR、XZ、bzip2、lzip、Zstandard 格式失敗。Zstandard 包含標準 frame 及全部 16 種 skippable frame，不能藉改名放行。本工具不宣稱能辨識任意編碼。AppImage 必須先解出目錄，不能只掃外檔。上限為單檔 128 MiB、累計讀取 512 MiB、50,000 項及五層壓縮檔，超過即失敗，不略過剩餘內容。

兩份固定公開來源壓縮檔以精確 SHA-256 對應既有核對證據：§9.1 的 `runtime-source-r1.tar.gz` 與 [font](../../font/README.md) 的 `unifont-17.0.05.tar.gz`。它們逐位元組符合已核對來源時記入來源清單，不把附帶上游來源中的一般空檔或連結當成原版素材。沒有呼叫者可追加的跳過清單；未知 bytes 仍逐層掃描。這項來源辨識不代選字型條款。

本機模式須同時明示 `--local-original <包內相對目錄>` 及 `--local-manual <正式本機提示來源>`。原版只允許在該目錄逐檔對應清冊，四語完整提示表只允許在 text 目錄與指定來源 bytes 完全相同。缺檔、重複、內容不符或提示來源與掃描範圍重疊均失敗；結果分類為 local-only，不用它證明可散布包安全。

合成反例入口為 [package_scan_cases.py](../../tools/tests/package_scan_cases.py)，11 項測試通過。實際無答案布局 14 檔及本機布局 84 檔通過；改名原版與偽裝答案表皆以 exit 1 拒絕。乾淨複本只移除一處 SHA-256 判斷，兩個獨立字面期望按預期失敗。70 個原版檔案未變。

收據為 `workplace/package-prototype/package-scan-r5-verification.json`、`package-scan-tests-r5.log`、`package-scan-mutation-r5.log`；最終契約及資料報告為 `package-scan-contract-review-r3.txt`、`package-scan-evidence-review-r3.txt`。封存入口為同目錄的 `package-scan-phase-verification-manifest.json`，較早報告與收據保留。掃描結果只證明本工具覆蓋的外洩邊界，不證明授權、必要檔案、字型覆蓋、可啟動性或正式封包完成，013 維持 READY。

## 14. 必要資產清冊與 ZIP 工具

[package_files.py](../../tools/package_files.py) 於 Docker 內接收 `--stage`、`--platform`、`--version`。`bundle`／`verify-bundle` 另需完整 `--engine`；`zip`／`verify-zip` 另需 `--archive`，只處理 Windows／macOS。這些是封裝編排可呼叫的共用步驟，不建置、不選字型條款，也不建立 tag。

| 平台 | 輸入布局及清冊 |
|---|---|
| Linux | stage 的 `usr/bin/` 為相對基準，清冊 `usr/bin/bundle.json` |
| Windows | stage 為相對基準，清冊 `bundle.json`；後端 `phantasie-play.exe` |
| macOS | `Phantasie.app/Contents/` 為相對基準，清冊 `Resources/bundle.json`；後端 `MacOS/phantasie-play`，譯文及字型在 Resources |

清冊逐檔核對 §12 的 18 份必要資產；四語 ui／prose 的鍵集合須相同，無答案 manual 僅允許兩個標題。GOLEMFNT 核對 16×16 標頭、記錄長度、合法且遞增的碼點、來源旗標及 ASCII／實際譯文的字元覆蓋。Unix 後端須有執行權限。這項工具只檢查格式與覆蓋，不證明字形或二進位架構。`--local-manual` 明示本機變體，提示 bytes 須符合該來源，固定 70 檔原版須在平台指定的包內目錄；未明示時不得帶入該目錄。verify-bundle 核對本工具生成的精確 UTF-8／LF 清冊。

ZIP 包含 stage 根目錄，項目依名稱排序，時間固定為版號日期零時，權限整理為一般檔案 0644／可執行檔 0755／目錄 0755。核對實際 ZIP 的項目集合、bytes、SHA-256、權限、UTF-8 旗標及時間；不解出寫入主機。Windows 讀我須 UTF-8 BOM／CRLF，若有批次檔則須 ASCII／CRLF 且不含 BOM。來源與輸出重疊、符號連結、特殊檔案、大小寫重名及超限均拒絕。硬連結來源按一般檔案讀取及雜湊，ZIP 不保留硬連結身分；存檔硬連結的拒絕是 §12 的另一項契約。輸出排他建立，失敗只刪除本次建立的清冊或 ZIP，不刪既有檔或來源。

合成驗證入口為 [package_files_cases.py](../../tools/tests/package_files_cases.py)，10 項測試通過。三平台加本機 Windows 的四組命令均產生及核對 18 項清冊；Windows、macOS 及本機 Windows 的三份 ZIP 往返及 §13 掃描通過。本機提示來源不符反例以 exit 1 拒絕。這些命令使用既有前端與正式譯文，字模是自製 BMP 碼點與全零位元圖，不讀 Unifont，不能作正式字型或可讀畫面證據。

乾淨複本只移除一處覆蓋判斷，合法長度的缺字夾具及意外建立清冊兩項期望按預期失敗。實際 Go 啟動器的 readBundle 另讀取四組生成清冊通過，只驗介面及資產雜湊，不啟動 GUI 或原版。101 個輸入雜湊保持不變。

命令、測試、突變與 Go 介面收據分別為 `workplace/package-prototype/package-files-verification.json`、`package-files-tests.log`、`package-files-mutation.log`、`package-files-native-compatibility.log`。唯讀契約及資料報告為 `package-files-contract-review.txt`、`package-files-evidence-review.txt`；本輪封存入口為 `package-files-phase-verification-manifest.json`。較早清冊保留。封包外洩仍另由 §13 掃描；權利、實際字型、架構、平台依賴及 GUI 依其他閘門驗證，013 維持 READY。

## 15. 授權材料整理

[package_rights.py](../../tools/package_rights.py) 在 Docker 內接收 `--out`、`--project`、`--engine`、`--modules`、`--go-license`、`--unifont`。Linux 所需的 `--runtime`、`--runtime-source` 須成對明示。來源唯讀，輸出為尚不存在的中間目錄；不是正式包，也不選字型條款。

[package_licenses.json](../../tools/package_licenses.json) 保存 §9 既有核對輸入的固定大小與 SHA-256：20 份共用條款／聲明、13 份 runtime 條款／啟動物件來源及一份配套來源壓縮檔。工具重新讀取實際來源逐一核對，不從網址或記憶推定內容。Unifont 只抽出 COPYING、OFL 全文及固定 Makefile 中的完整 COPYRIGHT 宣告，不複製 hex、字模或整份字型壓縮檔。

六個固定 Go 模組另收錄來源檔首的連續註解及來源 SHA-256，保留作者與內嵌元件聲明。全文條款仍另附，不以檔首註解代替。此範圍涵蓋固定模組的來源檔，包含沒有編入執行檔的檔案；不是對全部程式作法律分類。Ebitengine 內嵌 GLFW 的 Apache 2.0 全文由同模組 LICENSE 提供。

`rights-inputs.json` 記錄實際輸出雜湊、固定 profile 雜湊與檔首聲明數量；字型選項明確維持 pending。共用輸出有 21 檔，含 runtime 時有 35 檔，清冊本身另計。任何來源不符或寫入失敗都失敗，只移除本次建立的輸出。

合成測試入口為 [package_rights_cases.py](../../tools/tests/package_rights_cases.py)，最終 7 項通過，收據為 `workplace/package-prototype/package-rights-tests-r2.log`。實際材料整理收據為同目錄的 `package-rights-real.log`，35 檔、1,027 則檔首聲明；最終註解截取修正後，全部實際聲明 bytes 不變。材料已另由 §13 實際掃描通過；單一雜湊 guard 突變使同長度損毀的獨立期望按預期失敗，原碼不變。這只證明固定材料整理，不代選字型條款或宣稱正式包的完整權利驗收。

## 16. 平台組裝

[package_stage.py](../../tools/package_stage.py) 於 Docker 內接收以下必要參數：

- `--out`、`--platform`、`--version`、`--project-commit`、`--engine-commit`。
- `--font-license` 必須是使用者已選定的 OFL-1.1 或 GPL-2.0-or-later-with-font-exception，沒有預設。
- `--text-source`、`--unifont`、`--rights`、`--original`、`--launcher`、`--backend`、`--receipt-amd64`；macOS 另須 `--receipt-arm64`。

工具核對固定原版 70 檔作掃描依據，但預設不複製；`--local` 才複製原版及完整提示表，權利分類為 local-only。先核對 §15 材料及固定 GNU tar／hex 雜湊，再按平台布局寫入選定 catalog、原生啟動器、後端及命令列收據工具。四語字型由該布局的 ui、prose、manual 實際譯文重新建立，接著生成 §14 的 18 項清冊並執行 §13 掃描。來源與輸出不得重疊，輸出須排他建立；失敗只清理本次新目錄。

Linux 加入 AppRun、桌面入口及自製 P 圖示，連同 runtime 的全文條款及完整配套來源；AppRun 保留 argv。Windows 讀我使用 BOM／CRLF。macOS 加入 Info.plist，CFBundleVersion／CFBundleShortVersionString 採 `1.0.0`，依 [Apple 的三段整數格式](https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundleshortversionstring)；自訂 PhantasieReleaseVersion、啟動器、清冊、tag 及封包仍使用完整定案版號。未簽章 App 的讀我連到 [Apple 官方開啟步驟](https://support.apple.com/zh-tw/102445)，不提供全域停用安全檢查的命令。

專案 LICENSE、第三方全文、模組作者聲明與 `LICENSES.json` 同時加入。GPL 字型選項另附精確固定的完整 GNU 來源包；OFL 選項不帶該壓縮檔，仍附全文及作者聲明。`package-stage.json` 記錄版本、兩 repo commit、選定條款、平台、權利分類及布局內全部一般檔案的大小／雜湊／權限；項目含 stage 根目錄名稱，不包含清冊自己。

標頭檢查只證明 ELF x86-64、PE32+ AMD64 的 GUI／console 子系統或 Mach-O 的兩種架構及 universal 邊界，不代表 ABI 或可啟動性。合成測試入口為 [package_stage_cases.py](../../tools/tests/package_stage_cases.py)，最終 8 項通過，字模完全自製且全零，原版、條款及來源包也為合成資料。字型 bytes 用獨立字面期望核對；AppRun 用獨立 shell 助手核對參數，不當作遊戲啟動。收據為 `workplace/package-prototype/package-stage-tests-r3.log`。

根層核對入口為同目錄的 `package-stage-verification.json`，唯讀契約及資料報告為 `package-stage-contract-review.txt`、`package-stage-evidence-review.txt`，封存入口為 `package-stage-phase-verification-manifest.json`。原版 70 檔、受保護檔案 32 份、公開路線 23 條及五份較早封存的研究檔案不變。已選條款下的字型、正式包乾淨建置及平台冒煙仍待完成，013 維持 READY。

## 17. 封包編排與乾淨建置

[package.sh](../../tools/package.sh) 在主機只編排 Git、Docker 與來源形態檢查；實際分析、匯出解開、建置、複製、封裝與驗證都在有界、user 1000:1000、network none 的一次性容器。Git archive 在主機直接產生兩份固定提交匯出，不讀工作樹當程式來源。容器以實際主機 UID/GID 執行；來源匯出、封存 tar、來源清冊、授權材料、本機譯文及模組快取唯讀，stage、建置快取及明確輸出可寫。

必要 `--version` 使用定案完整版號。正式包另須 `--font-license`、`--original`、`--unifont`，以及精確指向專案 HEAD 的既有本機 tag。兩 repo 工作樹須乾淨、作者信箱須符合專案規則；引擎須在 phantasie-cht-overlay 且 HEAD 符合遠端指定分支。工具不建立或推送 tag，不建立 Release。`--local` 在 patch 之外另建 full-local，並保留來源及所有原有交付版本。

| 選項 | 意義或本機預設 |
|---|---|
| `--engine` | 引擎工作樹，預設專案 workplace/dosgolem-fw |
| `--modules` | 唯讀模組快取，預設 /home/anr2/go/pkg/mod |
| `--runtime-dir` | 預設 workplace/package-prototype/runtime-rebuilt，含 §9.1 固定 runtime 及全文條款 |
| `--runtime-source` | 預設 workplace/package-prototype/runtime-source-r1.tar.gz |
| `--build-only` | 只作乾淨來源編譯研究，免正式字型及 tag；不讀原版、字型或提示表，不建立 dist-all |

所有來源位置須為存在且形態正確的絕對路徑；CLI `--help` 提供完整選項。沿用 §9 的 Go、osxcross、AppImage 映像及 python:3.13-bookworm，使用已核對的完整 image ID，缺席時失敗，不下載浮動替代版。研究輸出排他建立在 workplace/package-prototype/package-run-<版本>-<平台>-<程序識別>，不當作現行交付。

Docker 內步驟：

1. [package_work.py](../../tools/package_work.py) 的 export 動作解開兩份 Git archive，保留完整 commit 及壓縮檔雜湊，拒絕跳脫路徑、重複或非一般項目。
2. [package_build.sh](../../tools/package_build.sh) 以 Go 1.24.13、readonly modules、GOTOOLCHAIN=local、trimpath 離線編譯。Windows GUI 與 console 工具區分，macOS 分別編譯兩個 thin 後由既有 lipo 合成 universal；沒有修改源碼或設定 HOME。
3. package_work 的 verify-build 核對架構、程式路徑、實際模組版本、啟動器內嵌的版號／引擎字串及 universal 每片原始 bytes。Linux 另記實際啟動器版本輸出、DT_NEEDED 及最高 glibc 符號；最高符號值不是完整平台相容性證明。Go 1.24.13 在 trimpath 下省略 linker flags，不能以 build info 證明注入的版本；固定 SDK `/usr/local/go/src/cmd/go/internal/load/pkg.go:2410` 為依據，SHA-256 `7080541914db2ac8ec9b0a4926d55efde949786d86816efb138c444037484a6e`。後端及收據工具沒有新增版本介面，以乾淨來源提交及實際二進位 SHA-256 定位。
4. 接上 §15 的材料與 §16 的布局；本機提示僅由 package_work 的 local-text 動作加入，正式 ui／prose／protected 均取乾淨專案匯出。其後 [package_appimage.sh](../../tools/package_appimage.sh) 核對固定 runtime，使用 gzip、固定版號日期建 SquashFS，讀實際 offset 及解出內容；其餘平台由 §14 建 ZIP。
5. [package_finish.py](../../tools/package_finish.py) 重讀實際 AppImage runtime／SquashFS／解出內容或 ZIP，核對全部布局、18 項清冊、編譯程式 bytes、來源版本、權利及封包集合。掃描通過後排他複製至 dist-all/<版本>/patch 或 full-local，寫 SHA256SUMS.json；複製失敗只清理本次新版本。

交付清冊明示 built and inspected; platform smoke pending。編排不將靜態封裝當作 §8 的 GUI、存檔或原版同狀態證據。正式字型條款仍待選定，因此目前只驗證兩種條款共用的程式及合成資料；合成反例入口為 [package_work_cases.py](../../tools/tests/package_work_cases.py)，7 項通過。三平台實際乾淨編譯與正式包冒煙仍待驗證，013 維持 READY。
