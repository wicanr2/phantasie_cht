#!/usr/bin/env python3
"""Docker/Xvfb：從正式 Linux 完整包錄下城鎮 F1、五語與返回。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess as sp
import threading
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(bundle, out):
    if out.exists():
        raise FileExistsError("GUI 輸出需要新目錄")
    manifest=json.loads((bundle/"bundle.json").read_text())
    assets=[]
    for entry in manifest["assets"]:
        p=bundle/entry["name"]
        if p.is_symlink() or p.stat().st_size!=entry["bytes"] or digest(p)!=entry["sha256"]:
            raise ValueError("實際封包資產不符")
        assets.append(entry)
    out.mkdir()
    if (out/"data").exists():
        raise FileExistsError("GUI 狀態須為空白")
    os.environ['DISPLAY']=':77'
    os.environ['XDG_CACHE_HOME']='/tmp/phantasie-story-cache'
    def cmd(*a):
        return sp.run(a,check=True,capture_output=True,text=True,timeout=35)
    def key(k):
        cmd('xdotool','keydown','--window',window,k)
        time.sleep(.15)
        cmd('xdotool','keyup','--window',window,k)
    def shot(path):
        cmd('import','-window',window,str(path))
        if struct.unpack('>II',path.read_bytes()[16:24])!=(640,400):
            raise ValueError("GUI client 不是完整 640×400")
    x=sp.Popen(['Xvfb',':77','-screen','0','1280x800x24','-nolisten','tcp'],stdout=(out/'xvfb.log').open('w'),stderr=sp.STDOUT)
    player=None
    try:
        time.sleep(1)
        player=sp.Popen([str(bundle/'phantasie'),'-data',str(out/'data'),'-lang','zh-TW','-theme','auto'],stdout=(out/'launcher.log').open('w'),stderr=sp.STDOUT)
        window=cmd('timeout','30','xdotool','search','--sync','--onlyvisible','--name','Phantasie').stdout.splitlines()[0]
        cmd('xdotool','windowfocus','--sync',window)
        time.sleep(5)
        key('Up');time.sleep(.6);key('Return');time.sleep(3)
        name=cmd('xdotool','getwindowname',window).stdout.strip()
        shot(out/'town-before.png')
        events=[];errors=[];start=time.monotonic()
        def actions():
            try:
                for t,k in [(0.8,'F1'),(2.1,'F12'),(3.3,'F12'),(4.5,'F12'),(5.7,'F12'),(6.9,'F12'),(8.1,'Escape')]:
                    time.sleep(max(0,start+t-time.monotonic()))
                    key(k)
                    events.append({'time':time.monotonic()-start,'key':k,'title':cmd('xdotool','getwindowname',window).stdout.strip()})
            except BaseException as e:
                errors.append(repr(e))
        thread=threading.Thread(target=actions)
        thread.start();frames=[]
        while time.monotonic()-start<9.6:
            t=time.monotonic()-start
            path=out/f'frame-{len(frames):06d}.png'
            shot(path)
            frames.append({'file':path.name,'time':t,'sha256':digest(path)})
            time.sleep(max(0,.1-(time.monotonic()-start-t)))
        thread.join()
        if errors: raise RuntimeError(errors)
        shot(out/'town-after.png')
        compare=cmd('compare','-metric','AE',str(out/'town-before.png'),str(out/'town-after.png'),'/tmp/story-difference.png')
        data={'schema':1,'scope':'actual extracted Linux full-local GUI; normal town F1 F12 Esc',
              'version':manifest['version'],'window':name,'client':[0,0,640,400],
              'StateInitiallyEmpty':True,'duration':9.6,'events':events,'frames':frames,
              'resumed_pixel_difference':compare.stderr.strip(),'bundle_sha256':digest(bundle/'bundle.json'),
              'backend_sha256':digest(bundle/'phantasie-play'),'launcher_sha256':digest(bundle/'phantasie'),
              'assets':assets,'producer_sha256':digest(Path(__file__)),
              'before_sha256':digest(out/'town-before.png'),'after_sha256':digest(out/'town-after.png')}
        (out/'capture.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'result':'PASS','frames':len(frames),'events':events,'resumed_difference':compare.stderr.strip()},ensure_ascii=False))
    finally:
        for proc in [player,x]:
            if proc:
                proc.terminate()
                try: proc.wait(timeout=8)
                except sp.TimeoutExpired: proc.kill();proc.wait()


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    record(args.bundle,args.out)
