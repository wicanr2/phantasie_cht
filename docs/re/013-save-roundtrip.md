# 013 存檔與冷啟動讀回

日期：2026-10-04。範圍是正常城鎮存檔與重新啟動後讀回角色，不涵蓋地城存檔、備份還原或損壞存檔。

## 輸入與工具

- 原版 `PHANTASI.EXE` SHA-256：`0f00a1af62cfcc383b4ca2e4382321f357063ba1457081da6edca4eb9f28e716`。啟動依原版批次檔順序，壓縮 EXE 未替換。
- dosgolem 分支 `phantasie-cht-overlay`，提交 `e90336d6e3fa9d7e17dcd90e3120b064fe8da10f`。Go 1.24.13 linux/amd64，工具映像 `psychicwar-go-ebiten:latest`，容器關閉網路、原版目錄唯讀。
- 探針 `workplace/explore-main/save_roundtrip.go` SHA-256：`cf5cf44d2142c2322d6f6518de52ac9cdb77bcb175fff9c60283a33c392cd413`。只使用 `Launch`、`SetScratch`、`KeyGate` 與唯讀畫面、記憶體、檔案觀察，沒有寫原版記憶體或修改存檔。
- 位址空間為 dosgolem 實模式；讀鍵沿用映像段偏移 `37C2` 的入口與 `37FA` 的結尾。完整記憶體 SHA-256 取線性位址 `00000h` 起 1 MiB。
- 各次執行使用獨立空存檔目錄與相同預設虛擬時鐘。沒有重擲角色或挑選亂數結果。相同流程的狀態由逐點雜湊核對，不以 seed 數字相同代替證據。
- 原版與產生的存檔均屬本機研究輸入，不加入版控或發行包。

## 正常玩家路線

1. 以 `tests/routes/save-load.route` 進城鎮，在公會建立 Alice、加入隊伍，從選項選單存檔兩次，再開關銀行。
2. 返回公會，選檢視，觀察名單及 Alice 的屬性。
3. 關閉執行器，以同一存檔目錄重新啟動完整批次鏈，從標題選單選繼續。
4. 再進公會，選檢視，觀察名單及同一角色屬性。

公會記得先前的游標。存檔側從「加入成員」向下四次到「檢視」；冷啟動側從「新成員」向下三次。第一版探針誤移到「離開」，該版不作角色讀回驗收；有效證據皆為 `*-v2`。

## 結果

| 觀察 | 證據 | 等級 |
|---|---|---|
| 原版城鎮存檔寫入 `guild.dat` 6,204 bytes、`sack.dat` 120 bytes、`twns.dat` 3,492 bytes；建立角色到第一次按存檔之前，存檔層仍空白 | `save-roundtrip-on-v2.log` 各檢查點的 `files`；原版目錄唯讀 | 已證實 |
| 第二次存檔與重新啟動後，三個檔案的 SHA-256 不變 | 各組 `after-save`、`after-save-2`、`reloaded-inspect-stats` 的 `files` | 已證實 |
| 冷啟動實際讀入已落地名冊與背包 | `phase=read` 的 `FileOps`：`guild.dat` 讀 6,204 bytes、`sack.dat` 讀 120 bytes | 已證實 |
| 原版記憶體及存檔不受覆繪影響 | none、off、on 與 zh-CN、ja、ko 各 15 點；steps、reads、VRAM、映像範圍與完整 1 MiB 雜湊、存檔檔案雜湊逐點相同 | 已證實，限本路線 |
| 重啟讀回前後角色資料與覆繪畫面相同 | `saved-inspect-stats` 與 `reloaded-inspect-stats` 的 VRAM、顯示文字、存檔雜湊相同；名單亦顯示 Alice；人工檢視讀回 PNG。兩點皆在按存檔之後 | 已證實 |
| 四語沒有殘字、外露或遮罩不符 | 全部 15 點的 stale、exposed、strict 為 0；累計未譯僅既有選項分隔線 | 已證實，限檢查點；尚未作正式工具的逐幀累計稽核 |

有效產物在 `workplace/explore-main/save-roundtrip-{none,off,on,zh-CN,ja,ko}-v2.log` 與同名目錄。精確輸入及收據雜湊見同目錄的 `save-roundtrip-verification.json`。`FileOps` 目前不列出成功寫入，不能用沒有 write 紀錄推論沒有存檔；落地檔案與冷啟動讀入是本輪依據。

## 正式收據

互動前端原已有存檔層。無頭收據工具於 `f046ec4` 接通可選 `-state`，新增目錄摘要與實際檔案清冊；[005 §10](../spec/005-play-frontend-and-receipts.md#10-存檔層收據擴充) 已 CONFORMED。四語 × none/off/on/on-f2 共 240 點通過正式逐幀稽核、落地存檔及冷啟動角色讀回。原 `save-load` 路線沒有設定存檔層，仍只用於存檔選單畫面回歸。

正式產物在 `workplace/receipts/save-roundtrip/`，來源與產物雜湊在 `workplace/receipts/save-roundtrip-verification.json`。獨立審查核對實際檔案、原始名冊沒有該角色、讀回前後角色畫面以及停用 `SetScratch` 的負對照。地城存檔、備份還原與平台實機驗收不在這份城鎮收據的完成聲明內。
