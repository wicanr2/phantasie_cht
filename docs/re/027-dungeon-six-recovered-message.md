# 027 第六地牢已恢復正文的正常驗收

日期：2026-10-05。專案基準 `4e8f04c`，引擎 `8d9807d`。沿 [012](../spec/012-recovered-prose-catalog.md) 的 READY 契約驗收 MESS6:52，含新增首行與既有後行。未改引擎、正式譯文、字型、原版資料或判定。其他 15 個新增鍵仍待正常 UI 驗收。

## 輸入與工具

| 輸入 | SHA-256 |
|---|---|
| `PHANTASI.EXE` | `0f00a1af62cfcc383b4ca2e4382321f357063ba1457081da6edca4eb9f28e716` |
| `DNG6` | `c9ea0bf9d055a2a122b6168a304c1d9dbc5eee129436ac625056302a4e0c98ec` |
| `MESS6` | `f166ef6dce694f4bd0e1829d46111155639cdaf3f7031dcbc772dfa00e7da325` |
| `OUT15.DAT` | `8313d18f3d33c53b7aa03859234ffe9833455f200dc5bfdac58e4de1d181ca0d` |
| IDA 輸入 `ov2_composed.bin` | `f461da5fb4e02634ab47dcbd8af3f5b7ae53c49d00ad42f5f56fcae765121422` |
| 正式 `ov2.i64` | `294be0bfbe2cb912f59b84f61e5487ae9041d2647a6f357ba5d9ef7521ca2abb` |

原始輸入與正式 IDA 資料庫唯讀。IDA 9.4 在 `/tmp` 的副本查詢，251 個函式、輸入雜湊及 UID 1000 均核對。image 為 `ida-pro-9.4-idapython:locked-v1`，ID `sha256:6f6d59af49d0008c4109a5295b5f374bdc007e2d1ab28cb9de08779584de2780`。

重播與像素工具沿用 Go 1.24.13、Python 3.11 的 `psychicwar-go-ebiten:latest`，ID `sha256:083e45e6bc0f01ca46ba0774581572c80a607120431b530de72cdd6ffb36f2f7`；準備工具為 Python 3.13。所有工作皆在有界、非 root、無網路的一次性 Docker 容器執行。原版全文、影像及長路線只留本機，不新增可散布原版語料。

## 大地圖路線的必要證據

不可變鍵：`DOS／OV2／IDA B881、C37E、C6AA／大地圖探索`。以下位址皆為 IDA 線性位址，映像偏移另減 `1100h`，不混作同一基準。

| 原始定位 | 已證實的作用 |
|---|---|
| `sub_B7E9` 的 `B7EF` 至 `B813`；`sub_B82F` | 區域編號進檔名格式化，1024 bytes 讀入 `DGROUP:C6FA`；正常離城的該記憶體與原始 OUT1 逐 byte 相同 |
| `sub_B881`，`B891: 80 BF FA C6 78`、`B898: 80 AF FA C6 78` | 格值至少 `78h` 時減去 `78h`，由 `sub_B8A1`、`sub_BB47` 呼叫。不是對格值取餘數 |
| `sub_C37E`，`C411` 至 `C425` | 讀取目的格值，值為 100 時轉入阻擋分支 |
| `sub_C37E:C3C0` 至 `C3D4`；`sub_C6AA:C6AE` 至 `C6EB` | 按呼叫端參數，左跨區加 4、右減 4、上減 1、下加 1；另一座標保持，跨界座標回到 0 或對邊 |

本機候選規劃排除值 100、101、非目標入口及特殊遭遇地形，保留正常文字格與原版隨機遭遇。實際按鍵逐點比對座標，遇到新文字或選單即停下確認。舊水池候選對地形取餘數，不能作可達性證據；第七地牢在本輪保守候選政策下未找到陸路，不表示遊戲中不可達。

原始 bytes 與交叉參照在 `gap2-terrain-{load,io,reveal,normalize}.json`，正常離城資料為 `gap3-world-runtime.bin`。正式規劃工具為 `gap3_plan_world.py`，結果為 `gap3-world-planning.json`，均位於 `workplace/explore-dungeon/`。這些只服務正常輸入探索，不進執行期程式。

## 正常到達與顯示

等級：已證實，限這條固定時鐘、正常輸入路線。

- 正常建立四人隊伍、離城，由區域 1、5、9、10、11、12 到 15。途中保留原版怪物醒來、夜間遭遇、第一次逃跑失敗的傷害及後續逃離結果。沒有重啟挑選有利 seed，沒有修改座標、角色、物品、存檔、記憶體或 VRAM。
- OUT15 `(5,17)` 確認入口後，原版進入 DNG6 `(20,0)`，132,044,889 步、394 次讀鍵。再按三次 Down，抵達 `(20,3)` 的 MESS6:52。
- 沿 [014](014-dungeon-message-trigger.md) 的資料契約核對，DNG6 檔案偏移 119 的格值為 227，事件偏移 1305 的 bytes 為 `B4 01 3C 00 00`。事件首 byte 的低 7 bits 為 52，與正常正文吻合。
- 正文停點為 132,248,219 步、400 次讀鍵。兩行各 40 個原版字元，欄 0、列 5 與 6。dosgolem 映像返回偏移 `7F2C`、指標 `DGROUP:638E`；這是執行期映像基準，不是 IDA 線性位址。新首行鍵為 `h:94439c234774`，後行為 `h:ea96eddf7f59`。
- 同時核對既有入口位置列：欄 0、列 24、40 個字元，dosgolem 映像返回偏移 `811B`、格式指標 `DGROUP:C400`，鍵 `h:00316a61b853`。
- 按 Return 後，原版移到 `(7,4)`，132,252,746 步、401 次讀鍵。正文及位置列全部清除，英文與四語均無殘留。傳送是原版結果，沒有重新實作該規則。

原始觀察為 `gap3-live.route`、`gap3-live-trace.jsonl`、`gap3-gas-body-original.png`。正式四語路線為 `gap3-gas-<lang>.route`。沿原版 `WIZ.BAT` 啟動鏈，兩側使用既有固定 DOS 時鐘初始條件；不解讀或改寫遊戲內 seed。

## 收據與獨立 oracle

| 驗證 | 結果 |
|---|---|
| 四語、none／off／on／on-f2 | 16 組各 188 點，共 3008 個原版 steps、reads、VRAM、映像及完整 1 MiB 記憶體相同。none 的 752 點只作雜湊基準，UI 為 SKIP |
| 正文與切換 | 80 個目標譯文 UI PASS、8 個英文切換 PASS；兩行全文、鍵與位置列均完整。四次保持檢查及回切畫面逐 byte 相同 |
| 取樣節奏 | on 的 20,000 步與 on-f2 的 40,000 步，四語全部 752 點的 Layer、可見內容、稽核及 PNG 相同 |
| 原版字模 | 從原始 16 KiB CGA 雙 bank 獨立解碼，正文及位置列的 6 行樣本逐像素與原始 FONT 相符 |
| 繁中、簡中、日韓像素 | 固定全文、正式 GOLEMFNT 與獨立排版核對 32 張完整原生／2 倍畫面，另有 8 項英文原始畫面核對。16 張正式 PNG 與另一正常重播的原始 RGBA 相同 |
| 保持及清除 | 每語 120 次保持，共 480 幀，不改原版步數及完整記憶體；返回與回切的 24 個空畫面停點，零疊字、零外露、零殘字，PNG 等於原版 |
| 缺鍵負對照 | 乾淨本機副本只刪除繁中新增首行，兩個正文停點、兩種倍率共四項核對按預期失敗；正負原版完整記憶體、視訊與步數相同，返回畫面仍相同 |

各 on 組有 146 個「疊字數為 0」診斷，含旅行及三個返回停點。它們不計 UI PASS。返回清除由原版影像、空疊字及獨立像素 oracle 證明；未把非零退出改寫成整條路線 PASS。原生倍率只驗邊界，不宣稱 16 點陣字型在 8 像素列中的完整可讀性。

核對入口為 `gap3_verify_receipts.py`、`gap3_verify_visual.py`、`gap3_verify_official.go`。摘要為 `gap3-receipt-verification.json`、`gap3-visual-verification.json`、`gap3-official-png-verification.json`；正式封存入口為 `gap3-verification-manifest.json`，均留在同一本機研究工作區。

契約對程式、資料對證據兩輪唯讀複核無阻擋。唯一文件計數訂正已處理；審查報告為同目錄的 `gap3-contract-review.txt`、`gap3-evidence-review.txt`。

## 完成界線與回填

MESS6:52 的正常四語正文、英文、保持、切換及原版傳送後清除已驗收。只解掉 012 新增 16 鍵中的一鍵所屬正文；其他 15 鍵包含三個水池正文，均不外推，既有 002／005 其餘分支也不外推，012 仍 READY。回填 [026](026-recovered-prose-catalog.md)、012、005、索引及唯一現況表。原版 70 檔、32 個受保護正式輸入與二進位、23 條公開路線及正式 IDA 不變。

實作期間的處置：一次性 IDA 單函式列舉漏寫 tuple 逗號，修正後在新副本重跑。收據核對起初誤認 none 有 PNG、SKIP 為短字串，以及沒有歷史分隔線引數，逐項回查正式工具與路線契約後乾淨重跑。像素工具缺 Pillow，改用容器既有 Go 標準 PNG 解碼器。以上都是探針或驗證工具問題，沒有修改產品或放寬目標正文檢查。
