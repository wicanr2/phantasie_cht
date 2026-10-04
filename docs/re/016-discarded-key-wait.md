# 第二條等鍵路徑

日期：2026-10-04。等級：下列原版位元組與正常路線已證實；主機停留採決定性排程，不宣稱真機時鐘一致。

## 輸入與工具

- 原版主程式 SHA-256：`0f00a1af62cfcc383b4ca2e4382321f357063ba1457081da6edca4eb9f28e716`。
- dosgolem `7b18f5c`，Go 1.24.13，Docker `psychicwar-go-ebiten:latest`。
- IDA Pro 9.4，映像基底線性 `1100`；資料庫與工具雜湊沿用 [008](008-text-and-screen-supplement.md) §10。
- IBM《Personal System/2 and Personal Computer BIOS Interface Technical Reference》，1988 年第二版，INT 16h：[原始手冊掃描](https://bitsavers.org/pdf/ibm/pc/ps2/15F0306_PS2_and_PC_BIOS_Interface_Technical_Reference_May88.pdf)。網頁搜尋可核對 AH=00h 必須等有鍵才返回；PDF 直接下載回 403，未核對掃描頁碼。採用平台契約，不追 BIOS 硬體迴圈。

## 位址與資料流

| IDA 線性位址 | dosgolem 映像偏移 | 原始定位與作用 |
|---|---|---|
| `48A0` | `37A0` | `55 8B EC`，進入；SP 記為 S |
| `48A3` | `37A3` | `E8 8D 01`，呼叫 `sub_4A33` 清空鍵盤 |
| `48A6` | `37A6` | `C7 06 CE B8 00 00`，AH=00h 輸入結構 |
| `48AC` 至 `48B7` | `37AC` 至 `37B7` | 推入三個參數；加上 BP，SP=S-8 |
| `48B8` | `37B8` | `E8 A5 16`，即將呼叫 `sub_5F60`，INT 16h |
| `48C1` | `37C1` | `C3`，丟棄讀鍵結果後返回 |

完整函式簽章：`558bece88d01c706ceb80000b8deb850b8ceb850b8160050e8a51683c4068be55dc3`。此處保留原始名稱，不用新名稱取代定位。

既有 `37C2` 會讀鍵並回傳結果；`37A0` 只等一個鍵。兩者不可混作同一入口。現有 BIOS 空佇列回 0，造成 `37A0` 約 150 步就返回。

## 可丟棄驗證

工具 `workplace/explore-main/wait_prototype.go` 重播版控正常路線，到 `map-top` 或 `second-name` 後繼續原版，在 `37B8` 停下。沒有改座標、原版記憶體或程式。重複 120 次停點檢查與 Frame 後，1 MiB 記憶體、VRAM、指令數、ticks、讀鍵次數完全不變。透過 BIOS 佇列送 Return，再執行原版直到 `37C1` 與下一次 `37C2`。

| 路線 | `37B8` 步數 | 入口 SP | 停點 SP | `37C1` 步數 | 下一次讀鍵步數 |
|---|---:|---:|---:|---:|---:|
| 道路描述 | 4,406,639 | 65,462 | 65,454 | 4,406,701 | 4,406,932 |
| 公會重名 | 3,486,930 | 65,442 | 65,434 | 3,486,992 | 3,517,436 |

收據 `wait-road.json`、`wait-duplicate.json` 與 PNG 在同一忽略目錄。畫面已人工核對：道路描述兩行與重名提示完整停留。此實驗證明暫停與原版返回可行，正式閘門仍依 [008 規格](../spec/008-discarded-key-wait.md) 驗收。

| 本機驗證檔 | SHA-256 |
|---|---|
| `wait_prototype.go` | `51e1254de8d73bc0e0839a972826739f617aa3a9c1578dea56d01aa2ae1422e5` |
| `wait-road.json` | `3bc1f54e26e982f73c95c91052297f50e9894518a7194c743a479ff46d8e0057` |
| `wait-duplicate.json` | `af616e20f5b6c0bfd2054d1e3564dbe43d0b7cf6efbbcf342d0ddab549a3ca6c` |

## 正式實作與驗收

引擎 `60b76b3` 以完整簽章與 SP 核對清鍵後的確認停點；前置通用 guard 提交為 `dcc1b9d`。兩條正常提示各四語四模式共 192 點、120 次重複停留、語言切換、正常鍵盤確認及負對照通過。前端 Xvfb 實際按鍵驗證重名提示與重試。其他正常路線、卷軸、存讀檔及手冊長路線回歸的範圍與結果見 [008 驗收收據](../spec/008-discarded-key-wait.md#驗收收據)。

精確工具與收據雜湊在 `workplace/explore-main/wait-verification-manifest.json`。正式原版輸入 70 檔不變；沒有修改原版程式或記憶體來延長畫面。
