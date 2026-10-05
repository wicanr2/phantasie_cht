# 029 場景與怪物圖像格式

本機原版來源大小與 SHA-256 見 [028](028-town-art-and-hd-preview.md#其餘圖像輸入)。本次只追圖像消費端，沒有修改原版、存檔或規則。完整唯讀審查為 `workplace/package-prototype/hd-all-image-review-r1/evidence-review-r1.txt`，SHA-256 `f267678a6d476a093a0286f94e6d51c4da19ebcd1ae99749d76d918ca5ed7085`。

## 工具與位址基準

IDA Pro 9.4，固定工具映像 `6f6d59af49d0008c4109a5295b5f374bdc007e2d1ab28cb9de08779584de2780`；原資料解碼及 PNG 比對使用 Docker Python 3.13 標準庫，映像同 028。正式資料庫唯讀，容器內複本才供查詢。

IDA 線性位址為 composed image 檔案偏移加 `1100h`；原靜態程式位址為 `0110:(IDA EA−1100h)`。DGROUP 資料的 IDA 位址為 `DAF0h＋DS offset`。實際 dosgolem 映像段可不同，不能將靜態 `0110` 當作固定執行期段。

| 靜態輸入 | bytes | SHA-256 |
|---|---:|---|
| phantasi_unpacked.bin | 117232 | `044b077aaba8b8dba484f2799d5a4086fbbac87e36bb9e76078977c69c6d0c38` |
| ov1_composed.bin | 117232 | `a2f1e2160e030d5688d8d41cb07177b92c4fba00fa8338c87458f9210709fa6f` |
| ov2_composed.bin | 117232 | `f461da5fb4e02634ab47dcbd8af3f5b7ae53c49d00ad42f5f56fcae765121422` |

## 已證實的原版格式

零值游程：非零 byte 原樣輸出；`0,n` 輸出 `n+1` 個零。IDA `sub_1644`，原靜態 `0110:0544`；IDA EA `165F` 的 LODSB、`1660` 的 STOSB 先寫一個零，再於 `166D` 的 REP STOSB 補 n 個。來源為 `ida-ov1-images-r3.json`。

| 類別 | 格式與消費端 | 等級 |
|---|---|---|
| IBMCOVER、CEMEN.IBM、ZEUS.IBM | 零值游程解出各 16384 bytes CGA 頁；OV1 `sub_64EA`、`sub_678B`、`sub_69B1` 經 `sub_3498` 解碼再用 `sub_1DF0` 顯示 | 已證實，限靜態消費端與 bytes |
| MSTR1IBM.PAT、MSTR2IBM.PAT | 各解出 34008 bytes；80 個索引，各有兩個不同圖像狀態；每張 row-major、2bpp、每 byte 高位先畫。尺寸表 DGROUP `2C3C`，32-bit 編碼偏移表 `BECA`，偏移除 2 為 byte offset | 已證實 |
| PRT1IBM.PAT、PRT2IBM.PAT | 各 4096 bytes，16 張 32×32 隊員图，每圖 256 bytes，row-major 2bpp；角色 appearance 低 byte 選索引 | 已證實，未解各索引的種族／職業名稱 |
| WIZ-MAIN.BSV | 7-byte 標頭 `FD 00 B8 00 00 A0 0F`，其後 4000 bytes，符合 B800:0000 的 BSAVE | bytes 已證實；80×25 文字畫面為強推論，主遊戲 consumer 未知 |

怪物幾何逐槽連續覆蓋 `[0,34008)`，無重疊或空洞；寬 32／48／64／80，高 21 至 80。兩個 bank 的同索引 bitmap 及非零輪廓都不同；160 變體不等於 160 物種。清冊為 `monster-geometry-confirmed.json`，SHA-256 `8c4071d0004a1138479df020a283f8ce1b45c89d07965c110b8eed7a209f4890`。

MSTR1 解碼 SHA-256 為 `c5486ee14164089e1820a6e9d9fbec2bb5249b98a03a057585663959dd22819c`；MSTR2 為 `619a5d47bfb493242f65fb91fecd7e3532ecb127c1d5fb3abbadc1fc1a2c6300`。怪物繪製 `sub_AE40` 的原靜態位址為 `0110:9D40`，near stack 參數依序為 x、y、height、width、source byte offset、mode。mode 0 用第一 bank，其他用第二 bank；mode 2 將非零像素白化，FFFF 清除矩形。各模式的遊戲語意名稱尚未證實，不命名為攻擊或受擊。

## 正常樣本與限制

16 張既有正常戰鬥 off PNG 已獨立解析。8 張有完整怪物圖，共 32 個位置皆命中索引 13／bank 1，原座標為 `(36,120)`、`(104,120)`、`(172,120)`、`(240,120)`，各 32×31，逐像素差異 0。12 張有完整隊員圖，命中索引 0／bank 1。詳見 `monster-normal-frame-matches-r1.json` 與 `portrait-geometry-confirmed-r1.json`；未命中的畫面保留空清單。

其餘怪物索引、第二 bank、其他場景的正常到達尚未量到。場景後續有動畫及 UI 寫入，解出初始頁不能證明整場景可安全覆蓋。圖集只作本機素材參考，不當作正常玩家路徑或正式 HD 驗收。

DRAFT 審查另確認兩個原始圖像歧義：索引 0 的兩個 bank 非零像素都全為 3，白化後與各自來源完全相同；PRT 索引 9 與 MSTR 索引 56 的同 bank bitmap 完全相同。不能只靠完整 bitmap 區分這兩類語意。OV2 `sub_B005` 在 IDA EA `B054–B05A` 以 `151−height` 算第一組 y，後續組向上排列；`sub_B309` 讀回 y／height 不增加底線。正常圖像 exclusive bottom 不超過 151，與隊員 y156、高32 分開。窄核對及原始操作數保存於 `hd-all-prototype-r1/evidence-spec-review.txt`；完整載入的逐像素核對補證第一 bank 也全白。正式顯示契約見 018 的回退及位置限制。

全部原尺寸圖、圖集與審查工具只留 `hd-all-image-review-r1/`。手繪候選及原始參考分組保存在 `workplace/package-prototype/hd-all-prototype-r1/`，`monster-groups.json` 列出 8 組、160 變體及圖像位置，`prompts.json` 保存內建 image_gen 提示。正式合成契約見 [018](../spec/018-all-recognizable-hd-images.md)。
