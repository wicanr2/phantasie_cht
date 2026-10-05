# 028 城鎮圖像與 HD 樣圖

## 已證實的城鎮格式

輸入：`PELNOR.IBM`，16384 bytes，SHA-256 `68833b5ae2ef2c77317b7a30998aacca1a7edf942c20dd0316df833e4394036c`。來源分類：本機原版，不散布。

工具：Docker 的 Python 3.13 標準函式庫，固定映像 `sha256:933b46a028fd786c9c3d426ebabc237e29a15912231ea8de576e95f0e4f41a4c`；正常遊戲畫面由 dosgolem 引擎 `8d9807df4f191c02eef46a22b6f7bbecb426ef5b`、專案候選 `808f32bdc15cddea990b28aeee34c3fb8c80ea8e` 的 Linux 收據工具產生。此處位址皆為檔案偏移，沒有套用 IDA 位址。

| 項目 | 已驗證值 |
|---|---|
| 尺寸 | 320×200，2 bits／pixel |
| 位元順序 | 每 byte 由高至低，四個像素 |
| 掃描線 | 偶數列起於偏移 0，奇數列起於偏移 8192；每列 80 bytes |
| 像素位址 | `(y % 2) * 8192 + (y // 2) * 80 + x // 4` |
| 色值位移 | `6 - 2 * (x % 4)` |
| 樣本色盤 | 黑、RGB 85/255/255、255/85/255、255/255/255 |
| 中央圖像範圍 | 原始畫布 `(0,8,320,184)`；上下各 8 像素為選單與城名文字 |

正常輸入為公開 `tests/routes/town.route` 的前綴，從標題游標繞回第一項，再按 Return 進城；停止於 `@check town`，沒有注入座標、角色或記憶體。以原始圖檔解出的像素，逐點比對 2 倍正常城鎮畫面的中央區域，共 235520 個輸出像素，差異 0。這證實此檔的 CGA 格式與這個畫面的圖像矩形，不證明其他 IBM 或 PAT 同格式。

本機證據入口：

- `workplace/package-prototype/hd-town-preview-r1/pelnor-cga-geometry-proof-r1.json`
- 同目錄 `pelnor-raw-cga-probe-r1.png`
- `workplace/package-prototype/eten-font-prototype-r1/town-run.json` 與 `town-on/`

原版建築上有 BANK、INN、GUILD 字樣。先前將第一張 HD 樣圖的 BANK、INN 判為新增招牌，已由原始圖檔與逐像素核對更正，歷程見 WORKLOG。

## 其餘圖像輸入

以下僅盤點 bytes 與 SHA-256，格式、圖像數量及使用場景尚未驗證，不依檔名猜定。

| 檔案 | bytes | SHA-256 |
|---|---:|---|
| IBMCOVER | 5273 | `0112b997902c65f70c6ae00616230fdc3aa1eff3a0e93aa26223ed6cbaeca37a` |
| CEMEN.IBM | 10030 | `ca875b6612c05ae5ee16b659f76a5a9d4951df886731238b36b83cef8d7e0122` |
| ZEUS.IBM | 5763 | `87c982d8dbe82053e32d682a2b3c431b5c88c7d90ac4ceefa32ac11d4ab9c113` |
| MSTR1IBM.PAT | 20270 | `f8c074fe22e0385540047bae702fb2947e3e41e0ff877812fa0abe7b762e5320` |
| MSTR2IBM.PAT | 22171 | `9f14246c202659f9791016968b51aab1df596af1b18c10dbc8a6bc5a0a5c1f70` |
| PRT1IBM.PAT | 4096 | `001775cde8d7a3e6902b2bd189568951efef6364d20a4ca4816e741b723b0632` |
| PRT2IBM.PAT | 4096 | `be4f143ca1541b774733b4e3d91e510ec13f4358ab80c4a91a8a937c62e6b623` |
| WIZ-MAIN.BSV | 4007 | `a24f456b439b3522981793b6a224eb94a0a7f1ec1663b095f716661b18139744` |

## 美術提案與城鎮整合

使用者已確認繼續 Phantasie 並新增 HD 圖像。另一專案 Psychic War #34 的素材與完成度不適用此案。

使用內建 `image_gen`，以正常繁中城鎮畫面為參考，製作 CGA 像素與彩色手繪兩個可丟棄提案。入口為 `workplace/package-prototype/hd-town-preview-r1/manifest.json`，逐張提示保存在 `prompts.json`；兩張 PNG 同目錄。使用者已選定彩色手繪、保留原版構圖。提案的文字縮放與細節尚未驗證，手繪樣圖未保留全部原版招牌；不直接當作正式資產。

獨立城鎮資產入口為 `workplace/package-prototype/hd-town-assets-r1/asset-proof.json`，同目錄保存 `town-painted.png`、`profile.json` 與 `prompt.txt`。新圖移除遊戲 UI 並恢復原版招牌；尺寸與指紋見 [015 顯示主題與手繪城鎮](../spec/015-presentation-themes.md)。已接入前端的手繪主題。

所有原版解出圖、樣圖及來源只留本機。兩輪審查通過後依 015 實作，正常路線 145 個停點確認原版記憶體與讀鍵不變，90 個停點使用 HD，其餘回退。收據在 `workplace/package-prototype/hd-normal-r1/normal-route-verification.json`；Linux 實際按鍵與五語主題畫面在 `hd-gui-r2/`，README 採該次實際遊玩截圖。這些不證明其餘八份素材已 HD 化，也不代替正式完整版或影片驗收。
