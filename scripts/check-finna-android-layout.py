#!/usr/bin/env python3
"""Capture only focused Finna Dev and check real native action geometry."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
import xml.etree.ElementTree as ET

def adb(*args):return subprocess.check_output(['adb','-d',*args])
def bounds(node):
    values=list(map(int,re.findall(r'\d+',node.get('bounds',''))));assert len(values)==4
    return values

def main(report,label,home=False):
    assert re.fullmatch('[a-z0-9-]+',label)
    focus=adb('shell','dumpsys','window').decode()
    assert any('mCurrentFocus=' in line and 'in.hawayu.finna.dev/' in line for line in focus.splitlines()),'Only capture focused Finna Dev'
    image=report/(label+'.png')
    remote='/data/local/tmp/finna-qa.xml'
    try:
        adb('shell','uiautomator','dump',remote)
        xml=adb('exec-out','cat',remote)
    finally:adb('shell','rm','-f',remote)
    path=report/(label+'.xml');path.write_bytes(xml)
    image.write_bytes(adb('exec-out','screencap','-p'))
    tree=ET.fromstring(xml);nodes=list(tree.iter('node'));height=max(bounds(n)[3] for n in nodes)
    checks=[]
    if home:
        for title in ('Continue','Mock test'):
            matches=[n for n in nodes if n.get('content-desc')==title and n.get('clickable')=='true'];assert len(matches)==1,(title,len(matches))
            node=matches[0];box=bounds(node)
            assert 0<box[3]-box[1]<height/4,(title,'Action consumes a quarter of the screen',box)
            labels=[n for n in node.iter('node') if n.get('text')==title];assert labels,(title,'Missing visible action text')
            for n in labels:
                b=bounds(n);assert box[0]<=b[0]<b[2]<=box[2] and box[1]<=b[1]<b[3]<=box[3]
            checks.append({'action':title,'bounds':box,'label_inside_action':True,'less_than_quarter_screen_height':True})
    result={'label':label,'screen_height_px':height,'focused_package':'in.hawayu.finna.dev','checks':checks,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (image,path)}}
    (report/(label+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':
    assert len(sys.argv) in (3,4)
    main(Path(sys.argv[1]),sys.argv[2],len(sys.argv)==4 and sys.argv[3]=='--home')
