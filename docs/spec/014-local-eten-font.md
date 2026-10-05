# 014 本機倚天字形

狀態：READY。前置規格：004、006 CONFORMED，013 READY。使用者已要求三平台本機倚天完整版含遊戲；可散布發行字型採 OFL 1.1。此規格只增加字型建置與封包隔離，不改原版程式、語言資料或寬度契約。

## 1. 來源與證據

倚天唯讀來源及三檔 SHA-256 見 [font/README.md](../../font/README.md#本機倚天字形)。正式工具只需 STDFONT.15、SPCFONT.15，不讀 ASCFONT.15。固定原始大小分別 392820、12240 bytes；每字 30 bytes，是 16×15 點陣，逐列 MSB 在左。來源權利分類為本機使用，不假設可散布或 OFL。

索引入口為 Codex 路由 `sources/claude/retro-cht/eten-bitmap-font.md`；實際研究為 `workplace/package-prototype/eten-source-coverage-r1.json`。Big5 碼的線性索引：`(hi - 0xA1) * 157 + (lo - 0x40 if lo < 0x7F else lo - 0x62)`。合法尾碼僅 40h 至 7Eh、A1h 至 FEh。符號 A140 至 A3BF 對應 SPCFONT 的 0 至 407；常用字 A440 至 C67E 對應 STDFONT 的 0 至 5400；次常用字 C940 至 F9D5 對應 STDFONT 的 5401 至 13052。原始 STDFONT 尾端另有 41 筆，對應 F9D6 至 F9FE，屬本工具不使用的擴充槽。所有空隙、擴充碼與超界一律拒絕。Unicode 以 Python 3.13 的 `big5` 編碼；唯一明示例外是 U+FF5E 對應 A1E3。

既有繁中完整本機字型共 1364 字：95 個 ASCII 半形、1269 全形，沒有非 ASCII 半形。研究倚天字型對 1269 個全形字均可取模，95 個 ASCII 保留 GNU Unifont。正常標題及城鎮六筆比較含五個不同狀態，原版記憶體相同；這是原型證據，未完成字形遮罩或封包驗收。入口見 `font/README.md`。

## 2. 正式建置

新增 `tools/build_eten_font.py`，只在既有 Python 容器執行。必要參數：`--eten-dir`、`--base-font`、`--out`。base-font 必須是已按 013 從固定 GNU 來源、實際 catalog 建出的繁中 GOLEMFNT，16×16、ASCII 95 字半形，其餘均全形；格式、順序、碼點及來源旗標無效即拒絕。

先驗證兩份原始字模的型態、大小與固定 SHA-256，再以 base-font 碼點決定需要的字元。ASCII U+0020 至 U+007E 保留來源編號 1 與原始 32 bytes；其他字元從倚天取 30 bytes，尾端補兩個零 bytes，來源旗標 `0x82`。全部碼點、排序、字數及半／全形寬度保持不變。任一字無 Big5 對應或字模越界即整個建置失敗，不以全零字模補缺字，不漏字或改譯文。固定來源原有的空白字模保持原樣，例如 ASCII 空格與 U+3000。

輸出排他建立，不覆寫 base-font、來源或任何既有檔。建置輸出以 JSON stdout 記錄字數、來源分類、兩份來源與 base-font／結果的 SHA-256，不寫出提示內容或字元清單。讀取與建置失敗不留下半份輸出。

## 3. 三平台與權利邊界

`package_stage.py` 新增可選 `--eten-dir`，只能與 `--local` 並用。公開 patch 不接受該參數，字型仍全採固定 GNU。本機變體先按既有規格重建四語 GNU 字型，再以新工具建立繁中倚天字型；zh-CN、ja、ko 保留 GNU，英文維持原版。這樣不因其他語言缺倚天字而改文字或停用語言。既有無倚天的研究布局仍能驗證。

本機有倚天時，README.txt 明示「繁體中文全形採本機倚天；ASCII 與其他語言採 GNU Unifont」。LICENSES.json 與 package-stage.json 增加字型來源紀錄：各語言來源、倚天源檔及繁中字型產物雜湊、原始高度 15、輸出畫布 16×16、local-only。OFL 1.1 只適用 GNU 部分，專案 LICENSE 不涵蓋倚天或原版；不附原始倚天檔。

`package.sh` 新增 `--eten-dir`；正式 `--local` 必須明示此來源，build-only 或無 `--local` 時拒絕。主機只檢查絕對路徑、兩份檔案存在及非符號連結，內容指紋在容器驗證。來源唯讀掛載，只傳入 full-local 的 stage，不傳入 patch。參數不得提前寫入 Git archive 或可散布材料。

`package_files.py` 的 GOLEMFNT 檢查新增可選的本機倚天許可：僅有明示 local-manual 且語言為 zh-TW 時接受 `0x82`，且該旗標只允許非 ASCII 全形。所有其他語言與 patch 仍只接受 1、0x81，拒絕 2、0x02、未知旗標或半形倚天。其他既有布局不強迫改字型。

`package_finish.py` 不更動 bundle schema，按既有本機 reference 重驗清冊；交付紀錄保留各 stage 的字型來源紀錄。含倚天的 variant 必須是 full-local，三平台都按此隔離。公開外洩掃描不單獨證明字型來源，必要資產檢查必須一起執行。

## 4. 受影響程式與測試

| 項目 | 改動 |
|---|---|
| tools/build_eten_font.py | 新建置工具，固定來源、索引、來源旗標、排他輸出 |
| tools/package_stage.py | 本機繁中變體與字型來源紀錄 |
| tools/package_files.py | 來源編號 2 僅本機繁中放行 |
| tools/package.sh | 顯式參數、來源形態檢查與唯讀掛載 |
| tools/package_finish.py | 保留來源紀錄，核對 full-local 分類 |
| tools/tests/ | 合成旗標反例、錯誤來源／碼點／輸出反例、stage 整合 |
| font/README.md、CONTEXT.md、013 | 同輪更新入口與驗收狀態 |

引擎既有 ParseFontWide 讀 bit 7，字模載入忽略低 7 位來源，已可接受 0x82；不需要改 dosgolem。手冊表不變，正式工具不將答案寫進日誌。

## 5. 驗收與狀態閘門

先由兩名唯讀審查者分別核對契約對程式、資料對來源，逐項回「阻擋／應改／建議」；報告保留 `workplace/package-prototype/eten-contract-review-r1.txt` 與 `eten-evidence-review-r1.txt`。沒有未決阻擋或應改才升 READY 並實作。

最小充分驗證：

1. 實際來源雜湊、兩個分界字及符號索引獨立核對；1364 個碼點／字數／寬度不變，1269 字全形來源 2，95 字 ASCII bytes 不變。
2. 錯誤 hash、合法長度錯誤內容、未支援 Unicode、壞來源旗標、排序與既有輸出反例全部拒絕，且不改輸入。
3. 三平台 stage 實際本機字型／來源紀錄及 bundle 驗證；patch 及其他語言誤放 `0x82` 拒絕。既有 013 資產、stage 相關測試回歸。
4. 正常標題、城鎮、公會角色清單及一個地牢訊息使用正式字型抽樣；同狀態完整原版記憶體／顯示記憶體不變，像素差異只在批准覆繪格，檢查語言切換、返回及字形可讀。
5. 真正三平台封包與 GUI／存檔驗證依 013，尚未執行時明確 pending，不用字型單元測試計完成。

單一來源許可突變需使 patch 或錯誤語言的倚天反例失敗。保持原始倚天、GNU 壓縮檔、70 份原版及 catalog 不變，收尾檢查擁有權與容器清理。此規格 CONFORMED 只表示已列出的字型與隔離契約通過，不宣稱 HD 圖像、影片或整體發行完成。

## 6. 審查收據

兩輪唯讀審查最終皆為阻擋 0、應改 0、建議 0，入口為 §5 的兩份報告。共同審查的 DRAFT SHA-256 為 `7c159caec78a9009d2b19626b45e4e826e4dc07fb86143c9da66adc04ad09954`。末索引 13052、尾 41 槽不用與合法空白字模已釐清。READY 後實作；獨立像素差異遮罩與三平台正式封包驗收尚未完成。

正式建置與實際布局已完成研究抽測，入口為 `workplace/package-prototype/eten-stage-r1/`：

| 收據 | 結果與界線 |
|---|---|
| build-font.json | 1364 字、95 GNU ASCII、1269 倚天全形，結果 SHA-256 `94106e338da70ca5bc793413bbb10d21a3ee58ef8070eab35462969541bc8c86`，逐 byte 等於較早原型 |
| actual-stage-proof.json | Linux、Windows、macOS 實際本機布局與 bundle 通過，其他三語逐 byte 等於既有 GNU；程式使用乾淨候選 808f32b、引擎 8d9807d，不是新增 HD 或主題完成包 |
| normal-route-proof.json | 公會 81、地牢訊息 21、四語往返 7，共 109 組，步數、顯示記憶體、記憶體摘要及完整記憶體摘要相同，事件稽核 mask_strict=0；四個額外 assert 均通過，不算額外狀態 |
| tests-r1.log、mutation-r1.log | 34 項合成／回歸通過；在乾淨工具副本只擴來源2的公開許可，來源反例按預期失敗，正式程式不變 |
| input-preservation.json | 原版 70 檔、保護輸入 32 檔、公開路線 23 條及兩個倚天來源不變，沒有 root 擁有檔案或誤建 .md 目錄 |
| readme-screenshots.json | 五張正常倚天畫面及來源指紋，沒有手冊答案或 HD 提案 |

實作複核的入口為 `workplace/package-prototype/eten-contract-implementation-review-r1.txt` 與 `eten-evidence-implementation-review-r1.txt`。獨立像素差異遮罩及正式封包／GUI 還未驗證，014 保持 READY。

本輪來源、研究產物與審查報告的封存入口為 `workplace/package-prototype/eten-phase-verification-manifest.json`；不覆寫較早封存。提交後核對保存在同目錄的 `eten-postcommit-verification.json`，只記提交與遠端狀態，不將提交當作封包驗收。
