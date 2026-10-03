# 001 輸入清冊

日期：2026-10-03。範圍：`Phantasie (1987).zip` 內全部檔案的名稱、大小、SHA-256、格式判定、證據等級與來源權利分類。
逐檔資料在 `001-input-inventory.tsv`（欄位：name、bytes、sha256、category、format、evidence_level、rights）。

## 來源

| 項目 | 值 |
|---|---|
| 壓縮檔 | `Phantasie (1987).zip`，177,126 bytes |
| SHA-256 | `10c5c6c019d694aa3efdb7a6daf3d004f34e83644da7e9e1b68f1136ba3e26b2` |
| 內容 | `phantasi/` 下 70 個檔案，解開共 365,982 bytes（含 1 個 0 bytes 檔） |
| 版本字串 | `VERSION`：「Phantasie (bonus edition) Ver 1.1 11/12/90」「Copyright 1990 Wizardware Group Inc.」 |

壓縮檔與解開的檔案屬使用者本機輸入，不進 Git。解開位置是 `workplace/orig/phantasi/`（已 `.gitignore`）。

## 方法與工具

- 工具：`tools/inventory.py`。只用 Python 標準庫（`zipfile`、`hashlib`、`struct`）讀 bytes 與標頭。
- 環境：Docker 映像 `python:3.13-bookworm`，Python 3.13.15，映像摘要 `sha256:933b46a028fd786c9c3d426ebabc237e29a15912231ea8de576e95f0e4f41a4c`。
- 容器參數：`--rm --network none --memory 512m --cpus 1 --pids-limit 64`，以目前 UID/GID 執行；專案根目錄唯讀掛載，只有 `workplace/` 與 `docs/re/` 可寫。
- 判定只用 bytes 與標頭。內容語意沒有 bytes 層證據的一律標「未知」或「假說」。

### 重跑方法

```bash
cd /home/anr2/cht/phantasie
mkdir -p workplace/orig docs/re
docker run --rm --network none --memory 512m --cpus 1 --pids-limit 64 \
  --log-opt max-size=10m --log-opt max-file=3 -u "$(id -u):$(id -g)" \
  -v "$PWD:/in:ro" -v "$PWD/workplace:/out" -v "$PWD/docs/re:/re" \
  python:3.13-bookworm python -B /in/tools/inventory.py
```

## 與 `AGENTS.md` §2 的核對

| 項目 | 結果 |
|---|---|
| 壓縮檔大小與雜湊 | 一致 |
| 檔案數與解開總量 | 70 個、365,982 bytes，一致 |
| `PHANTASI.EXE` 大小與雜湊 | 21,101 bytes，`0f00a1af62cfcc383b4ca2e4382321f357063ba1457081da6edca4eb9f28e716`，一致 |
| `OUT*.DAT` | 18 個、各 1,024 bytes，缺 `OUT17.DAT`，一致 |
| `DNG1` 至 `DNG10` | 各 1,922 至 1,984 bytes（`DNG6` 最小 1,922，`DNG8` 最大 1,984），一致 |
| `FONT` | 2,032 bytes = 127 × 16，一致 |

## 類別摘要

| 類別 | 檔數 | bytes | 檔案 |
|---|---:|---:|---|
| 主程式 | 1 | 21,101 | `PHANTASI.EXE` |
| overlay | 2 | 58,666 | `OV1.OVR`、`OV2.OVR` |
| 啟動用 COM | 3 | 174 | `R32768.COM`、`M1.COM`、`M2.COM` |
| 啟動腳本 | 1 | 52 | `WIZ.BAT` |
| 版本字串 | 1 | 114 | `VERSION` |
| 字模 | 1 | 2,032 | `FONT` |
| 圖形資料 | 9 | 92,090 | `IBMCOVER`、`CEMEN.IBM`、`PELNOR.IBM`、`ZEUS.IBM`、`MSTR1IBM.PAT`、`MSTR2IBM.PAT`、`PRT1IBM.PAT`、`PRT2IBM.PAT`、`WIZ-MAIN.BSV` |
| 資料檔 | 48 | 176,244 | `MESS1` 至 `MESS10`、`SCROLLS.DTX`、`OUT*.DAT`、`DNG1` 至 `DNG10`、`DNG.SAV`、`DNGX.SAV`、`GUILD.DAT`、`TWNS.DAT`、`TWNS.INT`、`SACK.DAT`、`PHBACKUP`、`PHM`、`PAT` |
| 發行商附檔 | 3 | 15,509 | `GENERAL.DOC`、`LISTING.DOC`、`ORDER.DOC` |
| 空檔 | 1 | 0 | `Phantasie (1987).exo` |

## 格式觀察

| 檔案 | 觀察 | 等級 |
|---|---|---|
| `PHANTASI.EXE` | MZ 標頭：映像 21,101 bytes、標頭 2 paragraphs、重定位項 0、minalloc 6411、maxalloc 61581、SS:SP `087E:0080`、CS:IP `0509:0012`；偏移 `0x1C` 為 `LZ09` | 標頭已證實；LZEXE 0.90 為強推論 |
| `R32768.COM`、`M1.COM`、`M2.COM` | 無 MZ 簽章。三檔開頭同為 `FA 2B C0 8E C0 26 A1`，手工解讀為 `CLI`、`SUB AX,AX`、`MOV ES,AX`、`MOV AX,ES:[disp16]`。後續依檔案不同：`R32768` 為 `[0180]`、`CMP AX,49A6`、`JNZ +0C`；`M1` 為 `[0188]`、`CMP AX,49A7`、`JZ +0C`；`M2` 為 `[018C]`、`CMP AX,49A8`、`JZ +0C` | 簽章已證實；指令為強推論（手工解讀，只讀前 16 bytes） |
| `OV1.OVR`、`OV2.OVR` | 開頭同為 `F2 00 EA 53`，不是 `FBOV` | bytes 已證實；載入機制未知 |
| `WIZ-MAIN.BSV` | BSAVE 標頭：魔數 `FD`、段 `B800`、偏移 `0000`、長度 `0FA0`（4,000）。檔案大小 4,007 = 7 + 4,000。資料開頭是 `B2 40` 重複的位元組對 | 標頭已證實；內容為 80×25 文字模式畫面影像，屬強推論 |
| `FONT` | 2,032 bytes = 127 × 16。是否為 CGA 模式 4 的 8×8 字模未驗證 | 大小已證實；用途為假說 |
| `MESS1` 至 `MESS10`、`SCROLLS.DTX` | 可列印位元組比例 0.38 至 0.52，不是明文 | 編碼或壓縮未知 |
| 其餘資料檔 | 內容與用途未知 | 未知 |

`WIZ-MAIN.BSV` 指向文字模式（`B800`、80×25 × 2 bytes）。這是目前唯一能由檔案 bytes 推到顯示模式的線索，
只涉及這個檔案，遊戲主畫面的模式仍待 `AGENTS.md` §2 未知項 1 以執行期證據回答。

## 來源權利分類

| 分類 | 檔案 | 處置 |
|---|---|---|
| 原版遊戲檔，權利人待查 | 除下列兩類以外的 66 個檔案 | 使用者本機輸入，不入 Git、公開發行包或可散布測試語料 |
| 發行商附檔（WizardWorks） | `GENERAL.DOC`、`LISTING.DOC`、`ORDER.DOC` | 說明、產品目錄與訂購單，不是遊戲文字，不翻譯，不入 Git |
| 空檔 | `Phantasie (1987).exo` | 無內容 |

`WIZ.BAT`、`VERSION`、三個 `.COM` 出自原始發行還是 1990 年重發版，沒有證據可分，暫歸「原版遊戲檔」。權利人與原始發行者的查證列在 `AGENTS.md` §12 待決定第 1 項。

## 未回答的項目

`AGENTS.md` §2 的七個未知項本清冊都沒有回答。下一步是以 `cmd/probe` 盤點 dosgolem 對 `.COM` 序列、LZEXE 壓縮檔與 overlay 的支援。
