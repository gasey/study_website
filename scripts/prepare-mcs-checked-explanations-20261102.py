#!/usr/bin/env python3
"""Reuse the guarded source/prerequisite checks for this exact eighteen-item packet."""
import argparse,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('mcs_explanations',ROOT/'scripts/prepare-mcs-completion-explanations.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if not a.output.resolve().is_relative_to(ROOT/'reports'):p.error('Write reports under reports/')
 packet=json.loads((ROOT/'docs/sources/mcs-checked-explanations-20261102.json').read_text());assert len(packet['items'])==18
 request,identical=m.prepare(packet,json.loads((m.BANK_ROOT/'bank/mpsc_bank_v2.json').read_text()),m.BANK_ROOT)
 a.output.write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(items=len(request['items']),identical=len(identical),publication=False)))
if __name__=='__main__':main()
