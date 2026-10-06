#!/usr/bin/env python3
"""021：Docker 內的故事版推廣片，來源、分鏡、合成與獨立媒體驗證。"""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
import struct
import subprocess

from promo_video import SCORE_SHA, digest, read_capture

FONT = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
BOLD = FONT.replace("Regular", "Bold")
VERSION = "v.1.0.1-20261006"
ENGINE = "9f1c720af6aa72dc5b7c7bea5a1ed3a574a2a855"


def run(args, timeout=300):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=timeout)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n")


def safe_path(path):
    if not re.fullmatch(r"/[A-Za-z0-9_./-]+", str(path)):
        raise ValueError("concat 僅接受無跳脫的容器絕對路徑")
    return str(path)


def decode(path, width=640, height=400, seek=None):
    args=["ffmpeg","-nostdin","-v","error","-threads","1"]
    if seek is not None: args += ["-ss",str(seek)]
    args += ["-i",str(path),"-vf",f"scale={width}:{height}","-frames:v","1",
             "-f","rawvideo","-pix_fmt","rgba","-threads","1","-"]
    data=subprocess.check_output(args,timeout=30)
    if len(data)!=width*height*4: raise ValueError("解碼矩形不符")
    return data


def source_theme(capture):
    d=capture["data"]
    s=next(s for s in d["segments"] if s["name"]=="show-theme-hd")
    f=next(f for f in d["frames"] if f["frame"]>=s["Start"])
    pixels=decode(capture["root"]/f["file"],160,100)
    # Exclude menu rows; quantize actual scene colours, not another movie's palette.
    counts=collections.Counter(tuple((v//16)*16+8 for v in pixels[i:i+3])
                               for i in range(160*8*4,160*70*4,4))
    common=counts.most_common(100)
    def nearest(target):
        return min(common,key=lambda item:sum((a-b)**2 for a,b in zip(item[0],target)))[0]
    tokens={k:"0x"+bytes(nearest(t)).hex() for k,t in {
        "deep":(40,24,24),"stone":(120,104,88),"paper":(232,216,184),
        "roof":(168,88,72),"sky":(104,184,248)}.items()}
    return dict(tokens=tokens,source_sha256=f["sha256"],source_frame=f["frame"],
                method="16-level RGB histogram of actual town scene; nearest frequent stone/roof/sky colours",
                histogram=[dict(rgb=list(rgb),count=n) for rgb,n in common[:30]])


def plan(args):
    out=args.out
    if out.exists(): raise FileExistsError("新片輸出已存在，禁止覆寫")
    if digest(args.score)!=SCORE_SHA: raise ValueError("需要已確認的第二版配樂")
    sources={n:read_capture(args.captures,n,VERSION,args.project) for n in ("town","guild","map","combat")}
    bundles={json.dumps(s["data"]["bundle"],sort_keys=True) for s in sources.values()}
    if len(bundles)!=1 or sources["town"]["data"]["bundle"]["engine_commit"]!=ENGINE:
        raise ValueError("需要同一正式封包與引擎")
    bundle=json.loads((args.bundle/"bundle.json").read_text())
    bundle_sha=digest(args.bundle/"bundle.json")
    if bundle_sha!=sources["town"]["data"]["bundle"]["sha256"]:
        raise ValueError("實際封包與擷取不符")
    for a in bundle["assets"]:
        p=args.bundle/a["name"]
        if p.is_symlink() or p.stat().st_size!=a["bytes"] or digest(p)!=a["sha256"]:
            raise ValueError("實際封包資產不符")
    gui=json.loads((args.gui/"capture.json").read_text())
    if gui["schema"]!=1 or gui["version"]!=VERSION or gui["bundle_sha256"]!=bundle_sha or gui["resumed_pixel_difference"]!="0":
        raise ValueError("F1 實際 GUI 收據不符")
    if gui["scope"]!="actual extracted Linux full-local GUI; normal town F1 F12 Esc":
        raise ValueError("未知 GUI 來源")
    if not gui["StateInitiallyEmpty"] or gui["client"]!=[0,0,640,400] or gui["backend_sha256"]!=digest(args.bundle/"phantasie-play") or gui["assets"]!=bundle["assets"]:
        raise ValueError("F1 輸入身份或初始狀態不符")
    if [e["key"] for e in gui["events"]]!=["F1"]+["F12"]*5+["Escape"]:
        raise ValueError("F1 操作時間軸不符")
    for e,lang in zip(gui["events"],["zh-TW","zh-CN","en","ja","ko","zh-TW","zh-TW"]):
        if f"（{lang}・手繪）" not in e["title"]: raise ValueError("GUI 語言或主題不符")
    for i,f in enumerate(gui["frames"]):
        p=args.gui/f["file"]
        if f["file"]!=f"frame-{i:06d}.png" or p.is_symlink() or digest(p)!=f["sha256"]:
            raise ValueError("F1 畫格指紋不符")
        if struct.unpack('>II',p.read_bytes()[16:24])!=(640,400): raise ValueError("F1 client 矩形不符")
        if f["time"]<0 or (i and f["time"]<=gui["frames"][i-1]["time"]):
            raise ValueError("GUI 時間軸不遞增")
    if not gui["frames"] or not 9.5<gui["duration"]<9.7 or gui["frames"][-1]["time"]>=gui["duration"]:
        raise ValueError("F1 錄影長度不符")
    if decode(args.gui/"town-before.png")!=decode(args.gui/"town-after.png"):
        raise ValueError("F1 返回畫面差異不為 0")
    pixelmd5=run(["ffmpeg","-nostdin","-v","error","-threads","1","-framerate","1","-i",str(args.gui/"frame-%06d.png"),
                  "-pix_fmt","rgba","-c:v","rawvideo","-threads","1","-f","framemd5","-"]).stdout
    gh=[line.split(",")[-1].strip() for line in pixelmd5.splitlines() if line and not line.startswith("#")]
    if len(gh)!=len(gui["frames"]): raise ValueError("GUI 解碼格數不符")
    theme=source_theme(sources["town"])
    out.mkdir()
    (out/"gui-framemd5.txt").write_text(pixelmd5)
    save(out/"theme.json",theme)
    c=theme["tokens"]
    fonts={f:digest(Path(f)) for f in (FONT,BOLD)}
    commands=["#!/bin/sh","set -eu"]
    shots=[];source_samples=[];text_bounds=[];timeline=0

    def clip(route,first,last=None):
        cap=sources[route];d=cap["data"];last=last or first
        a=next(s for s in d["segments"] if s["name"]==first)
        b=next(s for s in d["segments"] if s["name"]==last)
        ss=[s for s in d["segments"] if s["Start"]<b["End"] and s["End"]>a["Start"]]
        names=re.findall(r"^@(?:check|snap)\s+(\S+)",(args.project/"tests/routes"/(route+".route")).read_text(),re.M)
        expected=[first] if first.startswith("show-") else names[names.index(first):names.index(last)+1]
        if [s["name"] for s in ss]!=expected or any(any(t in s["name"] for t in ("manual","answer","prompt","title")) for s in ss):
            raise ValueError("來源不是批准的連續玩家區段")
        allowed={s["name"] for s in ss}|{"transition"}
        fs=[f for f in d["frames"] if a["Start"]<=f["frame"]<b["End"]]
        if not fs or any(f["Section"] not in allowed for f in fs): raise ValueError("來源包含未知畫格")
        start=fs[0]["frame"]
        rows=[dict(path=cap["root"]/f["file"],time=(f["frame"]-start)/60,hash=f["sha256"]) for f in fs]
        return dict(route=route,first=first,last=last,rows=rows,duration=(b["End"]-start)/60,
                    capture_sha256=cap["sha256"],allowed_sections=sorted(allowed),start=start,end=b["End"])

    def add(seconds,layout,inputs,labels,bg=None):
        nonlocal timeline
        i=len(shots);prefix=f"shot-{i:02d}";bg=bg or c["deep"]
        rects={"hero":[(600,220,640,400)],"side":[(32,100,896,560)],"full":[(128,40,1024,640)],"closing":[(320,58,640,400)],
               "split":[(24,180,600,375),(656,180,600,375)],
               "grid":[(32,134,384,240),(448,134,384,240),(864,134,384,240),(240,422,384,240),(656,422,384,240)]}[layout]
        if len(inputs)!=len(rects): raise ValueError("版面與來源數量不符")
        count=round(seconds*30);seconds=count/30
        cmd=["ffmpeg","-nostdin","-v","error","-threads","1","-filter_complex_threads","1","-f","lavfi","-i",f"color=c={bg}:s=1280x720:r=30"]
        accent=c["roof"] if bg!=c["stone"] else c["sky"]
        rule_y=38 if layout=="full" else 12
        rule="drawbox=x=48:y=154:w=492:h=3:color="+accent+":t=fill" if layout=="hero" else f"drawbox=x=24:y={rule_y}:w=1232:h=2:color="+accent+":t=fill"
        graph=[f"[0:v]{rule}[bg]"];base="bg";views=[];records=[]
        for j,(src,rect) in enumerate(zip(inputs,rects),1):
            x,y,w,h=rect
            rows=src["rows"];duration=src["duration"];factor=seconds/duration
            concat=["ffconcat version 1.0"]
            for k,row in enumerate(rows):
                end=rows[k+1]["time"] if k+1<len(rows) else duration
                concat += ["file '"+safe_path(row["path"])+"'","option framerate 60",f"duration {end-row['time']:.12f}"]
            concat += ["file '"+safe_path(rows[-1]["path"])+"'","option framerate 60"]
            f=out/f"{prefix}-input-{j}.ffconcat";f.write_text("\n".join(concat)+"\n")
            cmd += ["-threads","1","-safe","0","-f","concat","-i",str(f)]
            graph += [f"[{j}:v]setpts={factor:.12f}*(PTS-STARTPTS),fps=30,scale={w}:{h}:flags=neighbor,tpad=stop_mode=clone:stop_duration={seconds}[g{j}]",
                      f"[{base}][g{j}]overlay={x}:{y}[v{j}]"]
            base=f"v{j}"
            pauses=[];begin=rows[0]["time"];previous=rows[0]["hash"]
            for row in rows[1:]:
                if row["hash"]!=previous:
                    if (row["time"]-begin)*factor>=.75: pauses.append([begin*factor,row["time"]*factor])
                    begin=row["time"];previous=row["hash"]
            if (duration-begin)*factor>=.75: pauses.append([begin*factor,seconds])
            views.append(dict(rect=list(rect),declared_static=pauses,source_pixel_method="decoded RGBA framemd5" if src["route"]=="gui" else "immutable dosgolem PNG SHA-256"))
            records.append({k:v for k,v in src.items() if k!="rows"})
            for k in sorted({0,len(rows)//2,len(rows)-1}):
                source_samples.append(dict(shot=i,viewport=j,file=str(rows[k]["path"]),sha256=digest(rows[k]["path"])))
        text_filters=[]
        for n,(text,x,y,size,color,bold) in enumerate(labels):
            if layout=="full" and y==20: y=6
            if layout=="full" and y==688: y=684
            f=out/f"{prefix}-text-{n}.txt";f.write_text(text+"\n")
            font=BOLD if bold else FONT
            text_filters.append(f"drawtext=fontfile={font}:textfile={f}:fontsize={size}:fontcolor={color}:x={x}:y={y}:alpha='min(1,t/0.25)'")
            metric=run(["ffmpeg","-nostdin","-v","debug","-threads","1","-filter_threads","1","-f","lavfi","-i","color=s=1280x720",
                        "-vf",f"drawtext=fontfile={font}:textfile={f}:fontsize={size}:x={x}:y={y}","-frames:v","1","-f","null","-"])
            m=re.search(r"text_w:(\d+) text_h:(\d+)",metric.stderr)
            if not m: raise ValueError("無字幕量測")
            tw,th=map(int,m.groups())
            if x<24 or y<4 or x+tw>1256 or y+th>712: raise ValueError(f"字幕越界 {f.name}: {tw}x{th}")
            if any(x<rx+rw and x+tw>rx and y<ry+rh and y+th>ry for rx,ry,rw,rh in rects):
                raise ValueError("字幕遮擋遊戲 UI")
            text_bounds.append(dict(file=f.name,x=x,y=y,width=tw,height=th,size=size,sha256=digest(f)))
        graph += [f"[{base}]"+",".join(text_filters)+"[out]"]
        cmd += ["-filter_complex",";".join(graph),"-map","[out]","-frames:v",str(count),"-an","-c:v","libx264","-threads","2",
                "-preset","veryfast","-crf","19","-pix_fmt","yuv420p",str(out/(prefix+".mp4"))]
        commands.append(shlex.join(cmd))
        shots.append(dict(index=i,layout=layout,file=prefix+".mp4",seconds=seconds,output_frames=count,start=timeline,end=timeline+seconds,
                          inputs=records,viewports=views,background=bg,labels=[l[0] for l in labels]))
        timeline+=seconds

    cream=c["paper"];ink=c["deep"]
    add(5.4,"hero",[clip("town","town")],[("格爾諾島・冒險的起點",58,94,24,cream,False),
        ("幽靈戰士",54,210,72,cream,True),("Phantasie",58,310,54,cream,False),
        ("黑騎士的陰影，籠罩格爾諾。",58,410,28,cream,False),("你的冒險，從一支隊伍開始。",58,460,28,cream,False),
        ("經典 DOS 冒險・多語中文化",58,640,25,cream,False)])
    add(5.4,"side",[clip("town","town")],[("受侵擾的島嶼",964,145,36,ink,True),
        ("巫師入侵之後\n黑騎士索取財物\n城鎮籠罩恐懼",964,260,27,ink,False),
        ("尼卡迪穆斯的藏身處仍是謎，你決定召集同伴。",32,674,27,ink,False)],cream)
    add(7.2,"full",[clip("guild","guild-menu","stats-wizard")],[("在公會，組成你的冒險隊伍",260,20,26,cream,True),
        ("招募角色・選擇職業・查看屬性",400,688,23,cream,False)])
    add(7.2,"side",[clip("map","map-top","map-sheet")],[("走出城鎮",966,150,38,ink,True),
        ("穿越荒野\n察看隊伍\n尋找地牢入口",966,260,28,ink,False),("每次探索，都從原版的操作與規則開始。",32,674,27,ink,False)],cream)
    add(7.2,"full",[clip("combat","combat-step1","combat-step6")],[("深入地牢，循著線索前進",286,20,26,cream,True),
        ("實際遊玩錄製・探索與訊息閱讀",380,688,23,cream,False)])
    add(3.6,"split",[clip("town","show-theme-original"),clip("town","show-theme-hd")],[
        ("從四色世界，走進彩色手繪",48,45,43,cream,True),("原版主題",24,135,27,cream,False),
        ("手繪主題",656,135,27,cream,False),("Shift+F12 隨時切換原版、琥珀、手繪",48,622,29,cream,False)],c["stone"])
    add(2.4,"full",[clip("town","show-theme-amber")],[("琥珀主題",535,20,26,cream,True),("保留原版畫面，換一種閱讀色彩",405,688,23,cream,False)])
    langs=[("zh-TW","繁體中文"),("zh-CN","簡體中文"),("en","English"),("ja","日本語"),("ko","한국어")]
    labels=[("用熟悉的文字，讀懂旅程",48,36,43,cream,True)]
    for label,(x,y) in zip([l for _,l in langs],[(152,97),(568,97),(988,97),(375,385),(790,385)]):
        labels.append((label,x,y,24,cream,False))
    labels.append(("F12 切換五語・日韓為機器輔助，未經母語者校對",180,687,20,cream,False))
    add(2.4,"grid",[clip("town","show-language-"+n) for n,_ in langs],labels)
    rows=[dict(path=args.gui/f["file"],time=f["time"],hash=h) for f,h in zip(gui["frames"],gh)]
    add(7.2,"side",[dict(route="gui",rows=rows,duration=gui["duration"],capture_sha256=digest(args.gui/"capture.json"),start=0,end=gui["duration"])],
        [("F1 操作說明",966,150,34,ink,True),("遊戲暫停\n五語即時切換\nEsc 返回旅程",966,260,28,ink,False),
         ("實際開啟、切換語言與返回操作錄製。",32,674,27,ink,False)],cream)
    add(4.2,"full",[clip("combat","combat-bar","combat-cmd-alice-set")],[("迎戰敵人",535,20,26,cream,True),("選擇行動，為每位隊員下達指令",405,688,23,cream,False)])
    add(4.2,"side",[clip("combat","combat-spell-bob","combat-cmd-carol-set")],[("施法與目標",966,150,36,cream,True),
        ("選擇法術\n指定對象\n準備下一回合",966,260,28,cream,False),("手繪怪物與新版隊員，保留原版位置。",32,674,27,cream,False)])
    add(4.2,"full",[clip("combat","combat-cmd-carol-set","round2")],[("回合開始",535,20,26,cream,True),("原版戰鬥運行・訊息與結果呈現",405,688,23,cream,False)])
    add(4.2,"full",[clip("combat","round2","round3")],[("與同伴，一起撐過下一回合",260,20,26,cream,True),("實際遊玩片段，節奏經剪輯調整",405,688,23,cream,False)])
    add(7.2,"closing",[clip("town","town")],[("回到城鎮，準備下一次出發",364,25,23,cream,False),
        ("幽靈戰士",528,494,56,cream,True),("Phantasie",548,579,32,cream,False),
        ("Windows・Linux・macOS 本機完整版",408,630,26,cream,False),
        ("F1 操作說明・F12 語言・Shift+F12 主題",332,680,20,cream,False)])
    if round(timeline,6)!=72 or sum(s["output_frames"] for s in shots)!=2160:
        raise ValueError("分鏡時長不符")
    concat=["ffconcat version 1.0"]
    for s in shots: concat += ["file '"+safe_path(out/s["file"])+"'",f"duration {s['seconds']:.9f}"]
    (out/"movie.ffconcat").write_text("\n".join(concat)+"\n")
    movie=f"phantasie-cht-{VERSION}-story-promo.mp4"
    commands.append(shlex.join(["ffmpeg","-nostdin","-v","error","-threads","1","-safe","0","-f","concat","-i",str(out/"movie.ffconcat"),
                               "-i",str(args.score),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-t","72","-movflags","+faststart",str(out/movie)]))
    (out/"render.sh").write_text("\n".join(commands)+"\n")
    data=dict(schema=1,version=VERSION,file=movie,seconds=72,fps=30,width=1280,height=720,engine_commit=ENGINE,bundle_sha256=bundle_sha,
              backend_sha256=digest(args.bundle/"phantasie-play"),assets=len(bundle["assets"]),score_sha256=SCORE_SHA,fonts=fonts,
              producer_sha256=digest(Path(__file__)),capture_helper_sha256=digest(args.project/"tools/promo_video.py"),
              rights="local-only original/derived game art and ETEN glyphs; approved original score r2",
              story_source="https://www.mocagh.org/ssi/phantasie-manual.pdf#page=3; brief independent summary",
              captures={n:s["sha256"] for n,s in sources.items()},gui_sha256=digest(args.gui/"capture.json"),
              shots=shots,source_samples=source_samples,caption_bounds=text_bounds,theme=theme)
    save(out/"plan.json",data)
    print(json.dumps(dict(shots=len(shots),seconds=timeline,layouts=sorted({s["layout"] for s in shots}),caption_bounds=len(text_bounds))))


def audit(out):
    p=json.loads((out/"plan.json").read_text());movie=out/p["file"];sha=digest(movie)
    probe=run(["ffprobe","-v","error","-count_frames","-show_streams","-show_format","-of","json",str(movie)]).stdout
    (out/"ffprobe.json").write_text(probe);d=json.loads(probe)
    v=next(s for s in d["streams"] if s["codec_type"]=="video");a=next(s for s in d["streams"] if s["codec_type"]=="audio")
    if (v["codec_name"],v["pix_fmt"],v["width"],v["height"],v["avg_frame_rate"],int(v["nb_read_frames"]))!=("h264","yuv420p",1280,720,"30/1",2160):
        raise ValueError("視訊格式不符")
    if (a["codec_name"],a["sample_rate"],a["channels"])!=("aac","48000",2) or any(abs(float(s["duration"])-72)>.05 for s in [a,v,d["format"]]):
        raise ValueError("音訊格式或時長不符")
    loud=run(["ffmpeg","-nostdin","-v","info","-threads","2","-filter_threads","1","-i",str(movie),"-vn","-af","loudnorm=I=-18:TP=-1:LRA=11:print_format=json","-f","null","-"]).stderr
    (out/"loudness.txt").write_text(loud);levels=json.loads(loud[loud.rfind("{"):])
    if any(not math.isfinite(float(levels[k])) for k in ("input_i","input_tp")) or abs(float(levels["input_i"])+18)>.5 or float(levels["input_tp"])>-1:
        raise ValueError("音量或峰值不符")
    checks=[]
    for s in p["shots"]:
        for i,view in enumerate(s["viewports"]):
            x,y,w,h=view["rect"]
            text=run(["ffmpeg","-nostdin","-v","info","-threads","2","-filter_threads","1","-ss",str(s["start"]),"-i",str(movie),
                      "-t",str(s["seconds"]),"-an","-vf",
                      f"crop={w}:{h}:{x}:{y}:exact=1,blackdetect=d=0.2:pix_th=0.01:pic_th=0.9999,freezedetect=n=0.000001:d=1","-f","null","-"]).stderr
            (out/f"shot-{s['index']:02d}-roi-{i}.txt").write_text(text)
            if "black_start:" in text: raise ValueError(f"未批准黑幀 {s['index']} {i}")
            starts=[float(n) for n in re.findall(r"freeze_start: ([0-9.]+)",text)]
            ends=[float(n) for n in re.findall(r"freeze_end: ([0-9.]+)",text)]
            if len(starts)>len(ends): ends.append(s["seconds"])
            for begin,end in zip(starts,ends):
                cursor=begin
                for aa,bb in view["declared_static"]:
                    if aa<=cursor+.15 and bb>cursor: cursor=bb
                if cursor<end-.15: raise ValueError(f"無來源支持的凍結 {s['index']}/{i}: {begin}..{end}")
            checks.append(dict(shot=s["index"],viewport=i,rect=view["rect"],black_intervals=[],static_intervals=list(zip(starts,ends))))
    for sample in p["source_samples"]:
        if digest(Path(sample["file"]))!=sample["sha256"]: raise ValueError("來源樣本已改變")
    if digest(movie)!=sha: raise ValueError("驗證期間成片已改變")
    receipt=dict(result="PASS",file=movie.name,sha256=sha,bytes=movie.stat().st_size,duration=72,frames=2160,
                 lufs=float(levels["input_i"]),true_peak=float(levels["input_tp"]),
                 plan_sha256=digest(out/"plan.json"),score_sha256=p["score_sha256"],roi_checks=checks)
    save(out/"verification.json",receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!="roi_checks"}))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",type=Path,required=True);ap.add_argument("--audit",action="store_true")
    for n in ("captures","gui","bundle","score","project"):ap.add_argument("--"+n,type=Path)
    args=ap.parse_args()
    if args.audit: audit(args.out)
    else:
        if any(getattr(args,n) is None for n in ("captures","gui","bundle","score","project")):ap.error("需要 captures/gui/bundle/score/project")
        plan(args)


if __name__=="__main__":main()
