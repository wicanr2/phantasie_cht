#!/usr/bin/env python3
"""016/017：Docker 內建立本機影片白名單、重現腳本及驗收。"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex

SCORE_SHA = "fb958dd7a908c0f8b9266c8989bc81706d91a0f0efdcbbf10134098192f0eeb1"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_capture(root, name, version, project):
    path = root / name / "capture.json"
    data = json.loads(path.read_text())

    if data["route_sha256"] != digest(project / "tests/routes" / (name+".route")):
        raise ValueError("擷取不是指定公開玩家路線")
    if data["schema"] != 1 or data["virtual_fps"] != 60 or data["scope"] != "local package gameplay capture":
        raise ValueError("影片只接受正式本機包擷取")
    if data["bundle"]["version"] != version or not data["StateInitiallyEmpty"]:
        raise ValueError("擷取版號或初始狀態不符")
    frames = data["frames"]
    if not frames or any(type(f["frame"]) is not int for f in frames) or any(a["frame"] >= b["frame"] for a,b in zip(frames,frames[1:])):
        raise ValueError("擷取格索引不符")
    for f in frames:
        if not re.fullmatch(r"frame-[0-9]{6}\.png", f["file"]):
            raise ValueError("擷取檔名不符")
        image = path.parent / f["file"]
        if image.is_symlink() or digest(image) != f["sha256"]:
            raise ValueError("擷取畫格指紋不符")
    return {"root": path.parent, "data": data, "sha256": digest(path)}


def plan(captures, score, output, version, project):
    if not re.fullmatch(r"v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}",version) or digest(score) != SCORE_SHA:
        raise ValueError("版號或已確認第二版母帶不符")
    if output.exists():
        raise FileExistsError("影片輸出已存在")
    sources = {name:read_capture(captures,name,version,project) for name in ("town","guild","map","combat")}
    engines = {s["data"]["bundle"]["engine_commit"] for s in sources.values()}
    if len(engines) != 1:
        raise ValueError("擷取不是同一引擎")
    def segment(route,name):
        found = [s for s in sources[route]["data"]["segments"] if s["name"]==name]
        if len(found)!=1:
            raise ValueError("剪輯停止點不是唯一已知區段")
        return found[0]
    def range_of(route,first,last=None):
        a,b=segment(route,first),segment(route,last or first)
        return a["Start"],b["End"]
    shots=[]
    def add(route,first,seconds,title,caption,last=None):
        start,end=range_of(route,first,last)
        segs=[s for s in sources[route]["data"]["segments"] if s["Start"]<end and s["End"]>start]
        allowed={s["name"] for s in segs}
        # No title/manual/private checkpoint may be admitted by a broad range.
        if any(any(token in n.lower() for token in ("manual","answer","title","prompt")) for n in allowed):
            raise ValueError("白名單包含未批准區段")
        fs=[f for f in sources[route]["data"]["frames"] if start<=f["frame"]<end]
        if not fs or any(f["Section"] not in allowed|{"transition"} for f in fs):
            raise ValueError("剪輯範圍含未知畫格")
        start=fs[0]["frame"]
        shots.append(dict(route=route,start=start,end=end,seconds=seconds,title=title,caption=caption,
                          allowed_sections=sorted(allowed),capture_sha256=sources[route]["sha256"],frames=fs))
    add("town","town",7.2,"幽靈戰士 Phantasie","繁體中文・本機倚天字形・彩色手繪")
    for theme,label in (("original","原版"),("amber","琥珀"),("hd","手繪")):
        add("town","show-theme-"+theme,4,"Shift+F12 切換顯示主題",label+"主題")
    for lang,label in (("zh-CN","簡體中文"),("en","英文原版"),("ja","日文"),("ko","韓文"),("zh-TW","繁體中文")):
        add("town","show-language-"+lang,1.08,"F12 切換語言",label)
    add("guild","guild-menu",5.4,"公會與角色建立","實際原版操作錄製",last="stats-wizard")
    add("map","map-top",3.6,"大地圖與隊伍操作","原版規則與存檔保持原樣",last="map-sheet")
    add("combat","combat-step1",12,"地牢探索","正常玩家路線・剪輯節奏經調整",last="combat-step6")
    add("combat","combat-bar",2.4,"回合選擇","片刻留白，準備戰鬥")
    add("combat","combat-bar",16.8,"手繪怪物與回合制戰鬥","原版操作錄製・隊員圖保留原版",last="round3")
    add("town","town",7.2,"三平台本機完整版",version+"｜Windows・Linux・macOS")
    if round(sum(s["seconds"] for s in shots),6)!=72:
        raise ValueError("分鏡總長不符")
    output.mkdir()
    commands=["#!/bin/sh","set -eu"]
    movie_concat=["ffconcat version 1.0"]
    timeline=0
    pauses=[]
    for i,s in enumerate(shots):
        prefix=f"shot-{i:02d}"
        (output/(prefix+"-title.txt")).write_text(s["title"]+"\n")
        (output/(prefix+"-caption.txt")).write_text(s["caption"]+"\n")
        fs=s.pop("frames");concat=["ffconcat version 1.0"]
        factor=s["seconds"]*60/(s["end"]-s["start"])
        runs=[];run_start=fs[0]["frame"];last_hash=fs[0]["sha256"]
        for k,f in enumerate(fs):
            path=sources[s["route"]]["root"]/f["file"]
            if not re.fullmatch(r"/[A-Za-z0-9_./-]+",str(path)):
                raise ValueError("容器擷取路徑不能放入 concat")
            end=fs[k+1]["frame"] if k+1<len(fs) else s["end"]
            concat.extend(["file '"+str(path)+"'",f"duration {(end-f['frame'])/60:.9f}"])
            if f["sha256"]!=last_hash:
                runs.append((run_start,f["frame"],last_hash));run_start=f["frame"];last_hash=f["sha256"]
        runs.append((run_start,s["end"],last_hash))
        concat.append("file '"+str(sources[s["route"]]["root"]/fs[-1]["file"])+"'")
        (output/(prefix+".ffconcat")).write_text("\n".join(concat)+"\n")
        for a,b,h in runs:
            if (b-a)*factor/60>=.75:
                pauses.append(dict(start=timeline+(a-s["start"])*factor/60,end=timeline+(b-s["start"])*factor/60,
                    reason="原版連續相同畫格或明示選單停留",capture_sha256=s["capture_sha256"],frame_sha256=h))
        s.update(output_start=timeline,output_end=timeline+s["seconds"],virtual_time_scale=factor,unique_frames=len({f["sha256"] for f in fs}))
        timeline+=s["seconds"]
        video_filter=(f"setpts={factor:.12f}*(PTS-STARTPTS),fps=30,scale=1024:640:flags=neighbor,"
            "pad=1280:720:128:40:color=0x17191c,"
            f"drawtext=fontfile={FONT}:textfile={output}/{prefix}-title.txt:fontsize=26:fontcolor=0xd1f2ff:x=(w-text_w)/2:y=6,"
            f"drawtext=fontfile={FONT}:textfile={output}/{prefix}-caption.txt:fontsize=20:fontcolor=white:x=(w-text_w)/2:y=689")
        cmd=["ffmpeg","-nostdin","-v","error","-threads","2","-filter_threads","1","-safe","0","-f","concat","-i",str(output/(prefix+".ffconcat")),
             "-vf",video_filter,"-frames:v",str(round(s["seconds"]*30)),"-an","-c:v","libx264","-threads","2","-preset","medium","-crf","19","-pix_fmt","yuv420p",str(output/(prefix+".mp4"))]
        commands.append(shlex.join(cmd));movie_concat.append("file '"+str(output/(prefix+".mp4"))+"'")
    (output/"movie.ffconcat").write_text("\n".join(movie_concat)+"\n")
    movie=output/f"phantasie-cht-{version}-local-promo.mp4"
    commands.append(shlex.join(["ffmpeg","-nostdin","-v","error","-threads","2","-filter_threads","1","-safe","0","-f","concat","-i",str(output/"movie.ffconcat"),
        "-i",str(score),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-t","72","-movflags","+faststart",str(movie)]))
    (output/"render.sh").write_text("\n".join(commands)+"\n")
    manifest=dict(schema=1,version=version,seconds=72,fps=30,width=1280,height=720,engine_commit=engines.pop(),score_sha256=SCORE_SHA,
        rights="local-only game imagery, Eten glyphs and original-derived hand-painted art; approved original score r2",
        captures={n:s["sha256"] for n,s in sources.items()},shots=shots,declared_static=pauses,
        soundtrack_license="GeneralUser GS 2.0 music-production terms; full license retained with source inputs",font=FONT)
    (output/"plan.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(dict(shots=len(shots),seconds=timeline,engine_commit=manifest["engine_commit"])))


def audit(output):
    plan_data=json.loads((output/"plan.json").read_text())
    probe=json.loads((output/"ffprobe.json").read_text())
    streams=probe["streams"];v=next(s for s in streams if s["codec_type"]=="video");a=next(s for s in streams if s["codec_type"]=="audio")
    if v["codec_name"]!="h264" or v["pix_fmt"]!="yuv420p" or (v["width"],v["height"])!=(1280,720) or v["avg_frame_rate"]!="30/1":
        raise ValueError("視訊格式不符")
    if a["codec_name"]!="aac" or a["sample_rate"]!="48000" or a["channels"]!=2 or abs(float(probe["format"]["duration"])-72)>.05:
        raise ValueError("聲音格式或時長不符")
    loud=(output/"loudness.txt").read_text();measured=json.loads(loud[loud.rfind("{"):])
    if abs(float(measured["input_i"])+18)>.5 or float(measured["input_tp"])>-1:
        raise ValueError("成片音量或峰值不符")
    detections=(output/"detect.txt").read_text()
    if "black_start:" in detections:
        raise ValueError("成片遊戲區有未批准黑幀")
    starts=[float(x) for x in re.findall(r"lavfi\.freezedetect\.freeze_start: ([0-9.]+)",detections)]
    ends=[float(x) for x in re.findall(r"lavfi\.freezedetect\.freeze_end: ([0-9.]+)",detections)]
    if len(starts)>len(ends):ends.append(72.)
    intervals=sorted((p["start"],p["end"]) for p in plan_data["declared_static"])
    for start,end in zip(starts,ends):
        cursor=start
        for a,b in intervals:
            if a<=cursor+.15 and b>cursor:cursor=b
        if cursor<end-.15:
            raise ValueError(f"未宣告長靜止區段 {start}..{end}")
    movie=next(output.glob("*-local-promo.mp4"))
    receipt=dict(result="PASS",version=plan_data["version"],file=movie.name,bytes=movie.stat().st_size,sha256=digest(movie),
                 duration=float(probe["format"]["duration"]),lufs=float(measured["input_i"]),true_peak=float(measured["input_tp"]),
                 detected_static=list(zip(starts,ends)),plan_sha256=digest(output/"plan.json"),score_sha256=plan_data["score_sha256"])
    (output/"verification.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(receipt,ensure_ascii=False))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captures",type=Path)
    parser.add_argument("--score",type=Path)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--version")
    parser.add_argument("--project",type=Path)
    parser.add_argument("--audit",action="store_true")
    args=parser.parse_args()
    if args.audit:audit(args.out)
    else:
        if args.captures is None or args.score is None or args.version is None or args.project is None:parser.error("需要captures、score、version、project")
        plan(args.captures,args.score,args.out,args.version,args.project)


if __name__=="__main__":main()
