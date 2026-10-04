# 字型

疊字用字型由 GNU Unifont 17.0.05 的 hex 檔建置成 GOLEMFNT 子集（格式與寬度表見 `docs/spec/004-fonts-and-languages.md` §3）。字型檔不進版控，只提交本說明與各語言的補字清單 `font/<lang>.extra.txt`（目前沒有需要補的字）。

## 來源

| 項目 | 值 |
|---|---|
| 壓縮檔 | `unifont-17.0.05.tar.gz`，SHA-256 `f287cffb26e22723aa36e6684869b0f3ff3bfb822c4b01008bd847911ec1b631` |
| 授權 | 已核對壓縮檔的 `COPYING` 與 `OFL-1.1.txt`，字型可採 SIL OFL 1.1 或 GPLv2+ 含字型例外。發行所採條款待使用者選定，見規格 004 §8 第 3 項 |
| `COPYING` SHA-256 | `cd2785c2b8e0a01d203560265b2d2d47cdb1401d2707d25918ac5531bcdba947` |
| `OFL-1.1.txt` SHA-256 | `869692af094c57fb7258c57fe26820c759319603321d0ffeb278de3651763ded` |
| 作者聲明來源 | 壓縮檔的 `font/Makefile`，SHA-256 `57d63f76a91dda451ae1592e6ba0f4222f4cf2bf2719504b52bf4ce49957e332`；`COPYRIGHT` 變數列完整作者及雙授權聲明 |

核對以固定壓縮檔為準；[上游授權說明](https://unifoundry.com/unifont/index.html)也列明雙授權。非字型工具程式的 GPL 條款與字型條款分開，不將字型子集改成專案的 RRSAL-1.0。發行包須保留所選字型條款及作者聲明；目前尚未建立發行包。

## 各語言對應

| 語言 | hex 成員 | hex 的 SHA-256 |
|---|---|---|
| zh-TW | `font/precompiled/unifont_t-17.0.05.hex` | `169634258e4037b507beaafad5d72edc2e44b3faeaa856d9669e4657d1eee454` |
| zh-CN | `font/precompiled/unifont-17.0.05.hex` | `fd79af3613ec1b984a98d33428fdd43fcf06018d18059960d78edeb63d958622` |
| ja | `font/precompiled/unifont_jp-17.0.05.hex` | `3e88e5e98470e7547555202cebb13bcd4c393d417e2296a0f0f8adade7d37f43` |
| ko | `font/precompiled/unifont-17.0.05.hex` | `fd79af3613ec1b984a98d33428fdd43fcf06018d18059960d78edeb63d958622` |

字元來源：該語言的 `text/ui.<lang>.tsv` 與 `text/prose.<lang>.tsv` 的譯文欄，加 ASCII `20h` 至 `7Eh`；存在時也納入 `text/manual-labels.<lang>.tsv`、本機 `text/manual.<lang>.tsv` 與 `font/<lang>.extra.txt`。缺任何一個要求的字就建置失敗，不為遷就缺字而改譯文。手冊答案表只留本機。

## 重建

```sh
tools/build_fonts.sh <unifont-17.0.05.tar.gz> <輸出目錄>
```

腳本在 Docker 內執行 `tools/build_font.py`，輸出 `<輸出目錄>/<lang>.golemfnt` 並列出 SHA-256。字型檔的雜湊隨譯文內容改變，由驗收收據記錄。

## 已知事項

- zh-TW 採 `unifont_t` 的字形對應臺灣用字：依 `U+9AA8`、`U+76F4` 兩字的字形比對（規格 004 §2），屬強推論，發行前以樣本確認。
- zh-CN、ko 都用預設 `unifont`；zh-CN 的簡體字形區域是否符合慣用待樣本確認。
- ja 以 `unifont_jp`。
