# 字型

疊字用字型由 GNU Unifont 17.0.05 的 hex 檔建置成 GOLEMFNT 子集（格式與寬度表見 `docs/spec/004-fonts-and-languages.md` §3）。字型檔不進版控，只提交本說明與各語言的補字清單 `font/<lang>.extra.txt`（目前沒有需要補的字）。

## 來源

| 項目 | 值 |
|---|---|
| 壓縮檔 | `unifont-17.0.05.tar.gz`，SHA-256 `f287cffb26e22723aa36e6684869b0f3ff3bfb822c4b01008bd847911ec1b631` |
| 授權 | 已核對壓縮檔的 `COPYING` 與 `OFL-1.1.txt`；使用者已選定發行字型採 SIL OFL 1.1，見規格 004 §8 第 3 項 |
| `COPYING` SHA-256 | `cd2785c2b8e0a01d203560265b2d2d47cdb1401d2707d25918ac5531bcdba947` |
| `OFL-1.1.txt` SHA-256 | `869692af094c57fb7258c57fe26820c759319603321d0ffeb278de3651763ded` |
| 作者聲明來源 | 壓縮檔的 `font/Makefile`，SHA-256 `57d63f76a91dda451ae1592e6ba0f4222f4cf2bf2719504b52bf4ce49957e332`；`COPYRIGHT` 變數列完整作者及雙授權聲明 |

核對以固定壓縮檔為準；[上游授權說明](https://unifoundry.com/unifont/index.html)也列明雙授權。非字型工具程式的 GPL 條款與字型條款分開，不將字型子集改成專案的 RRSAL-1.0。三平台正式補丁包已保留 OFL 1.1 全文及作者聲明，沒有建立公開 Release。

## 本機倚天字形

使用者要求三平台本機完整版包含遊戲並使用倚天字形。此變體及倚天字模只留本機，不加入 Git 或可散布包。正式交付版 `v.1.0.0-20261005` 已打包，字型、正常文字區及 Linux／Wine GUI 抽樣通過，macOS 僅完成靜態核對；範圍見 [014](../docs/spec/014-local-eten-font.md) 末節。

已找到唯讀來源 `/home/anr2/cht/etan_font/ET353S/FILES/`：

| 檔案 | bytes | SHA-256 |
|---|---:|---|
| STDFONT.15 | 392820 | `39ba9c8519d75fe11d5988a8a27e6daa5794ad2ea215108390b0d7e9e53ff701` |
| SPCFONT.15 | 12240 | `f32049ba2a7a21db908878a488a2c1d93c389d17398cf46db1390ba89e247605` |
| ASCFONT.15 | 3840 | `1d0cf09d0a319a9e7039190688c6a905ba4370bd369fbfcfa43b2078480d6918` |

研究入口為 `workplace/package-prototype/eten-source-coverage-r1.json` 及同名前綴的 `.py`。索引依 Codex 路由的 `sources/claude/retro-cht/eten-bitmap-font.md`，16×15 點陣的每列兩 bytes，符號與漢字分檔；「一、中、猴」及標點已抽看。首次將「一條橫線」誤判為只有一列亮點，實際明體多一點襯線，修正研究假設後通過。

倚天對四語正式譯文加本機提示的字元覆蓋只記統計，不匯出原文或答案：zh-TW 全形 1269 字均可對應；zh-CN 缺 417 字、ja 缺 261 字、ko 缺 677 字。這項統計不證明字形或正常畫面已驗收；其他語言保留 GNU 字型，不用倚天取代。字模整合保留既有 16×16 畫布及 8／16 像素排版寬度，不因原始字模高度 15 改變換行或輸出矩形。

可丟棄的實際字型與正常標題、城鎮畫面在 `workplace/package-prototype/eten-font-prototype-r1/`。`font-prototype.json` 記錄 95 個 GNU ASCII 與 1269 個倚天全形字，倚天來源旗標為 `0x82`。`prototype-state-comparison.json` 的六筆比較含五個不同狀態，步數、顯示記憶體、記憶體摘要及完整記憶體摘要均與關閉覆繪相同；未做嚴格像素遮罩驗收。正式封包整合契約見 [014](../docs/spec/014-local-eten-font.md)。

正式工具 [build_eten_font.py](../tools/build_eten_font.py) 已重建相同字型，SHA-256 `94106e338da70ca5bc793413bbb10d21a3ee58ef8070eab35462969541bc8c86`。實際三平台研究布局、109 組正常公會／地牢／語言切換收據與 34 項測試的入口為 `workplace/package-prototype/eten-stage-r1/`，見 014 §6。這些布局使用既有乾淨編譯的程式，不代表新增主題與 HD 圖像已打包。

## 各語言對應

| 語言 | hex 成員 | hex 的 SHA-256 |
|---|---|---|
| zh-TW | `font/precompiled/unifont_t-17.0.05.hex` | `169634258e4037b507beaafad5d72edc2e44b3faeaa856d9669e4657d1eee454` |
| zh-CN | `font/precompiled/unifont-17.0.05.hex` | `fd79af3613ec1b984a98d33428fdd43fcf06018d18059960d78edeb63d958622` |
| ja | `font/precompiled/unifont_jp-17.0.05.hex` | `3e88e5e98470e7547555202cebb13bcd4c393d417e2296a0f0f8adade7d37f43` |
| ko | `font/precompiled/unifont-17.0.05.hex` | `fd79af3613ec1b984a98d33428fdd43fcf06018d18059960d78edeb63d958622` |

字元來源：該語言的 `text/ui.<lang>.tsv` 與 `text/prose.<lang>.tsv` 的譯文欄，加 ASCII `20h` 至 `7Eh`；存在時也納入 `text/help.<lang>.tsv`、`text/manual-labels.<lang>.tsv`、本機 `text/manual.<lang>.tsv` 與 `font/<lang>.extra.txt`。缺任何一個要求的字就建置失敗，不為遷就缺字而改譯文。手冊答案表只留本機。

F1 說明頁新增用字後，Linux 原始碼抽驗已重新烘製四語 GNU 子集與本機繁中倚天子集。本機繁中為 1277 全形及 95 ASCII，SHA-256 `7fd1f6298d5d906d477380a1f59090e1f52d8309fa400f2a9418049671eaf826`，收據與來源在 `workplace/help-r1/eten-fonts/eten-source.json`，驗收範圍見 [019](../docs/spec/019-frontend-help.md#6-本機實作驗證)。既有正式封包的字型與雜湊保持不變。

## 重建

```sh
tools/build_fonts.sh <unifont-17.0.05.tar.gz> <輸出目錄>
```

腳本在 Docker 內執行 `tools/build_font.py`，輸出 `<輸出目錄>/<lang>.golemfnt` 並列出 SHA-256。字型檔的雜湊隨譯文內容改變，由驗收收據記錄。

## 已知事項

- zh-TW 採 `unifont_t` 的字形對應臺灣用字：依 `U+9AA8`、`U+76F4` 兩字的字形比對（規格 004 §2），屬強推論，發行前以樣本確認。
- zh-CN、ko 都用預設 `unifont`；zh-CN 的簡體字形區域是否符合慣用待樣本確認。
- ja 以 `unifont_jp`。
