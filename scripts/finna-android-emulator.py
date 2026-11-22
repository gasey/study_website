#!/usr/bin/env python3
"""Start/check/stop only Finna's dedicated QA AVD. Never targets a physical phone."""
from pathlib import Path
import argparse,os,socket,subprocess,sys
AVD='finna_qa_api36';SERIAL='emulator-5580';PORT=5580
p=argparse.ArgumentParser(description=__doc__)
g=p.add_mutually_exclusive_group();g.add_argument('--start',action='store_true');g.add_argument('--stop',action='store_true');g.add_argument('--check',action='store_true')
p.add_argument('--visible',action='store_true',help='Show the emulator window when starting')
a=p.parse_args()
candidates=[Path(v) for v in (os.environ.get('ANDROID_HOME'),os.environ.get('ANDROID_SDK_ROOT')) if v]+[Path.home()/'Android/Sdk']
sdk=next((p for p in candidates if (p/'platform-tools/adb').is_file() and (p/'emulator/emulator').is_file()),None)
if sdk is None:sys.exit('Android SDK adb/emulator not found; set ANDROID_HOME.')
adb=sdk/'platform-tools/adb';emulator=sdk/'emulator/emulator'
def cmd(*args):return subprocess.run([str(adb),'-s',SERIAL,*args],capture_output=True,text=True,timeout=20)
state=cmd('get-state');running=state.returncode==0 and state.stdout.strip()=='device'
if running:
 name=cmd('emu','avd','name')
 if name.returncode or name.stdout.splitlines()[0]!=AVD:sys.exit('Refusing: the emulator on port5580 is not the Finna QA AVD.')
 if a.stop:
  q=cmd('emu','kill');q.check_returncode();print('Finna QA emulator stopped; its data is retained.')
 else:
  ready=cmd('shell','getprop','sys.boot_completed').stdout.strip()=='1'
  print(f'{AVD}: {"ready" if ready else "booting"} ({SERIAL}). No phone targeted.')
 sys.exit(0)
if not a.start:sys.exit('Finna QA emulator is not running. Use --start; no phone was targeted.')
avds=subprocess.check_output([str(emulator),'-list-avds'],text=True).splitlines()
if AVD not in avds:sys.exit('Dedicated AVD missing; see docs/FINNA-ANDROID-QA.md. No device was modified.')
with socket.socket() as probe:
 if probe.connect_ex(('127.0.0.1',PORT))==0:sys.exit('Port5580 is occupied or its emulator is still booting; refusing to start another.')
logs=Path.home()/'.local/state/finna/android-qa';logs.mkdir(parents=True,exist_ok=True)
args=[str(emulator),'-avd',AVD,'-no-audio','-no-boot-anim','-no-snapshot','-gpu','swiftshader_indirect','-memory','4096','-cores','4','-port',str(PORT)]
if not a.visible:args.append('-no-window')
with (logs/'emulator.log').open('ab') as out:
 child=subprocess.Popen(args,stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True,env={**os.environ,'ANDROID_HOME':str(sdk),'ANDROID_SDK_ROOT':str(sdk)})
print(f'Started {AVD} (PID{child.pid}); use --check to confirm boot. Log: {logs/"emulator.log"}')
