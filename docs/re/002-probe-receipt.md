# 002 dosgolem probe 盤點收據

日期：2026-10-03。範圍：用 dosgolem `cmd/probe` 單獨與串接執行三個 `.COM` 與 `PHANTASI.EXE`，盤點不支援的服務、視訊模式、檔案存取，並取得 LZEXE 解壓後的映像。
輸入檔雜湊見 `001-input-inventory.md`。證據等級：已證實、強推論、假說、未知。

## 環境

| 項目 | 值 |
|---|---|
| dosgolem 分支 | `phantasie-cht-output-overlay`（本機，無上游），worktree `workplace/dosgolem` |
| 基底 commit | `2f44a68`（`origin/fix/stubseg-font-collision-program-path`，含 spec `194` 至 `196`）；使用者 2026-10-03 定案 |
| 建置 | `tools/go.sh`，映像 `golang:1.24-bookworm`，`DOSGOLEM_CPUS=2`、`DOSGOLEM_MEM=2g`，`--network none` |
| 原版掛載 | `workplace/orig` 唯讀掛到 `/orig`；傾印輸出掛到 `/out`（`workplace/probe-out`） |
| 程式修改 | 無。本次只執行 probe，沒有改動 dosgolem 任何檔案 |

共同命令形式（工作目錄 `workplace/dosgolem`）：

```bash
export DOSGOLEM_ORIG=$PWD/../orig DOSGOLEM_CPUS=2 DOSGOLEM_MEM=2g \
       DOSGOLEM_EXTRA_MOUNT=$PWD/../probe-out:/out
tools/go.sh run ./cmd/probe -exe /orig/phantasi/<檔名> -root /orig/phantasi <旗標>
```

## 三個 `.COM` 的完整手工解讀

三個檔案各 86、44、44 bytes，全部位元組手工解讀（未經反組譯器；`R32768.COM` 的流程另與單跑軌跡逐道核對）。三支都只含 `int 20h` 與 `int 27h`，沒有 `int 21h`。等級：強推論。

`R32768.COM`（進入點 `0100h`）：

```text
0100 cli ; sub ax,ax ; mov es,ax
0105 mov ax,es:[0180] ; cmp ax,49A6 ; jnz 011A
010E mov ax,es:[0182] ; cmp ax,49A6 ; jnz 011A
0117 sti ; int 20h                      ; 兩個字組都是標記：已安裝，結束
011A mov es:[0180],49A6 ; mov es:[0182],49A6     ; INT 60h = 49A6:49A6
     mov es:[0188],49A7 ; mov es:[018A],49A7     ; INT 62h = 49A7:49A7（佔位值）
     mov es:[018C],49A8 ; mov es:[018E],49A8     ; INT 63h = 49A8:49A8（佔位值）
     mov es:[0184],0000 ; mov es:[0186],cs       ; INT 61h = CS:0000
0150 sti ; mov dx,8000 ; int 27h
```

`M1.COM`（`M2.COM` 相同，位址換成 `[018C]`、`[018E]`，標記換成 `49A8`）：

```text
0100 cli ; sub ax,ax ; mov es,ax
0105 mov ax,es:[0188] ; cmp ax,49A7 ; jz 011A
010E mov ax,es:[018A] ; cmp ax,49A7 ; jz 011A
0117 sti ; int 20h                      ; 兩個字組都不是佔位值：結束
011A mov es:[0188],0000 ; mov es:[018A],cs       ; INT 62h = CS:0000
0126 sti ; mov dx,84D8 ; int 27h
```

`M1.COM`、`M2.COM` 在任一個字組仍是 `R32768.COM` 放的佔位值時安裝，把該向量改成自己的 `CS:0000`；`DX` 為 `84D8h`。`M2.COM` 的 `DX` 同為 `84D8h`。

## 單獨執行

| 程式 | 結果 | 等級 |
|---|---|---|
| `R32768.COM`（`-steps 200000 -log-calls`） | 前 17 道指令（至 `INT 27h`）：寫入 INT 60h 向量字組 `[0180]=[0182]=49A6`、INT 62h `[0188]=[018A]=49A7`、INT 63h `[018C]=[018E]=49A8`、INT 61h `[0184]=0`、`[0186]=CS`，再 `DX=8000`、`INT 27h`。dosgolem 不認得 `INT 27h`（回報 `int 27h AH=01 AL=80 ×1`），程式於是繼續執行 `.COM` 之後的零位元組（`add [bx+si],al`），繞過 64 KB 回到 `0100:0100`，第二輪比對命中，以 `INT 20h` 結束。共 32,754 道指令，離開碼 0 | 已證實（軌跡）；指令解讀與 `001` 的手工解讀一致 |
| `M1.COM`、`M2.COM`（各自單跑） | 11 道指令後以 `INT 20h` 結束。`[0188]`、`[018C]` 不是 `R32768` 放的佔位值，不進入安裝分支 | 已證實（軌跡） |
| `PHANTASI.EXE`（`-steps 20000000 -log-calls -watch-video -program-path 'C:\PHANTASI.EXE'`） | 267,141 道指令後 `INT 21h AH=4Ch`，離開碼 1。服務依序為 `AH=4A`（要 7,343 段）、`AH=44` 三次（代號 0、1、2）、`AH=35 AL=60`（得 `0080:0180`）、`AH=4C`。視訊模式維持 `03h`，視訊記憶體一次都沒寫，主控台沒有輸出，沒有未實作的服務，沒有開任何檔案 | 已證實（軌跡） |

`PHANTASI.EXE` 單跑時以離開碼 1 結束的原因，靜態反組譯給出對應程式碼：`sub_4790`（映像偏移 `0x3690`）取得 INT 60h 向量後與 `49A6h` 比對，不符即 `exit(1)`。見 `003-ida-static-survey.md`。

## LZEXE 解壓後映像

| 項目 | 值 | 等級 |
|---|---|---|
| 壓縮檔載入 | 標頭 CS:IP `0509:0012` 加載入段 `0110` = `0619:0012` 為 stub 入口 | 已證實（軌跡與標頭） |
| stub 段轉移 | `0619:0052` → `0972:0053`（第 1,804 道）、`0972:018E` → `094B:0010`（260,441）、`094B:0031` → `10D4:0032`（260,458） | 已證實（`-seg-log`） |
| 解壓完成 | `10D4:00F8` → `0110:4EE5`（第 266,847 道）；`0110:4EE5` 是解壓後程式的進入點 | 已證實（`-seg-log`） |
| DGROUP | `DS=0DAF`（線性 `0DAF0`）。映像基底 `0110` 到 DGROUP 起點共 `0xC9F0`（51,696）bytes | 已證實（暫存器與算術） |
| 堆疊上的程式碼 | `0110:4EB3` → `0DAF:FFD2`（串跑第 557,571 道，緊接 `AH=35 AL=60` 之前）：`int86` 包裝（映像偏移 `0x4E60`）在堆疊上執行小常式，CS 暫時等於 DS | 已證實（`-seg-log`，早於串跑崩潰）；小常式內容為強推論（`CD nn`） |
| 傾印 | 第 266,900 道指令後，`-dump-mem 1100-1DAF0`，117,232 bytes，涵蓋 `0110:0000` 至 DGROUP 末端 | 已證實 |
| SHA-256 | `044b077aaba8b8dba484f2799d5a4086fbbac87e36bb9e76078977c69c6d0c38` | 已證實 |
| 決定性 | 連跑兩次，兩份傾印雜湊相同 | 已證實 |

傾印存在 `workplace/probe-out/phantasi_unpacked_a.bin`（不進版控）。解壓工具就是 dosgolem 基底 commit `2f44a68` 的 probe，沒有使用外部 `unlzexe`。

## 串接執行（診斷，非等價）

`-queue` 可以依序執行 `R32768.COM`（主程式）、`M1.COM`、`M2.COM`、`PHANTASI.EXE`：

```bash
tools/go.sh run ./cmd/probe -exe /orig/phantasi/R32768.COM -root /orig/phantasi \
  -queue /orig/phantasi/M1.COM,/orig/phantasi/M2.COM,/orig/phantasi/PHANTASI.EXE \
  -steps 30000000 -log-calls -watch-video -seg-log -program-path 'C:\PHANTASI.EXE'
```

這條路徑**不等價**於 `WIZ.BAT`：dosgolem 沒有實作 `INT 27h`，三個 `.COM` 都沒有常駐，`EXEC 紀錄` 顯示 `TSR=false`。後續程式因此落在原本要被保留的區塊上。

| 觀察 | 說明 | 等級 |
|---|---|---|
| `AH=35 AL=60` 得 `49A6:49A6` | 通過 `PHANTASI.EXE` 的檢查 | 已證實（軌跡） |
| 視訊模式 04h，於第 557,941 道指令切換 | 發生在 `main` 開頭，與常駐區塊無關，和靜態反組譯一致 | 已證實（診斷串跑），與靜態結果相符 |
| `FONT` 讀入 `0DAF:3244`，要求 2,032、得 2,032 bytes | 傾印顯示 DGROUP 內位址 | 已證實 |
| `IBMCOVER` 開檔後讀取，要求 16,384、得 5,273 bytes | 讀取的目的段是 INT 61h 向量的段。`R32768.COM` 寫入 `[0184]=0`、`[0186]=CS`，它是第一支程式，PSP 為 `0100`，所以目的位址 `0100:0000` 與程式的設計一致。串跑中 `PHANTASI.EXE` 也載入 `0100`，因此被覆蓋；常駐正確時預期 `PHANTASI.EXE` 落在三個常駐區塊之上，`IBMCOVER` 仍寫入 `0100:0000`，蓋掉 `R32768.COM` 自己的 PSP 與程式碼。這與 `003` 發現 4（保留區不含驅動碼）一致 | 目的段來源已證實（靜態與軌跡）；常駐後的預期為強推論，列為 `INT 27h` 規格的量測目標 |
| 之後 `0110:002C` → `3500:C0AB`，並反覆進入 `3500:xxxx` | `IBMCOVER` 的 5,273 bytes 寫在線性 `01000` 起，覆蓋 `PHANTASI.EXE` 自己的 PSP 與映像開頭（映像從線性 `01100`），執行流進入垃圾位址 | 無效（串跑假象） |
| INT 61h、62h 讀到 `0100:0000` | INT 61h 符合 `R32768.COM` 寫入的值。INT 62h 是 `M1.COM` 安裝後的值（`M1.COM` 也載入 `0100`）；常駐正確時 INT 62h 的段應不同於 INT 61h | 與單程式推演相符；段值重合是串跑假象 |
| INT 63h 讀到 `49A8:49A8` | 依 `M2.COM` 的 bytes，`[018C]` 等於 `49A8` 時應進入安裝分支並改寫向量，這次卻仍是佔位值 | 未解釋 |
| `int 27h` 呼叫次數：`AX=0180` ×1、`AX=49A7` ×2、`AX=49A8` ×12 | 對應 `R32768.COM`、`M1.COM`、`M2.COM`，與各自單次執行的預期次數不符 | 未解釋；`INT 27h` 補上後重跑核對 |
| 視訊記憶體一次都沒寫、`B8000` 全 0 | 發生在上述崩潰之後的路徑，不能推論遊戲不寫 `B8000` | 無效 |

串跑不能用於 A/B，也不能用於推論記憶體配置、overlay 位址或畫面內容。要取得這些必須先補 `INT 27h`。

## dosgolem 缺口

| 缺口 | 影響 | 參考 |
|---|---|---|
| `INT 27h`（舊式常駐結束）未實作 | 三個 `.COM` 無法常駐，`WIZ.BAT` 的序列無法在 dosgolem 內重現；`PHANTASI.EXE` 依賴它們留下的記憶體區塊與向量 | `internal/dos/int21.go` 已有 `AH=31h`（`tsr()`，spec `008-tsr-resident` READY）。DOSBox-X `src/dos/dos.cpp:3293` `DOS_27Handler`：`para = ceil(DX / 16)`，縮減 PSP 區塊為 `para`，再以 TSR 方式結束、離開碼 0（原始碼樹 commit `e0b4287`） |

需要的處置：先寫新規格（通用層、`docs/spec/` 在 dosgolem 分支內），經兩輪獨立審查成為 READY，才實作。本收據不包含任何 dosgolem 程式修改。

## 未量到

- 三個 `.COM` 常駐後的記憶體佈局與 `PHANTASI.EXE` 讀到的 INT 61h、62h、63h 向量值：需要 `INT 27h`。
- overlay 的載入位址與時機：需要 `INT 27h`。
- 畫面內容：需要 `INT 27h`。
