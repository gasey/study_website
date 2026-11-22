#!/usr/bin/env python3
"""Inspect saved Chromium PDFs; visual page inspection is additionally required."""
from pathlib import Path
import hashlib,json,sys
import pdfplumber

def main(output,report):
    proof=json.loads((output/'browser-print.json').read_text());results=[]
    for case in proof['cases']:
        path=output/case['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==case['sha256']
        pages=[];texts=[]
        with pdfplumber.open(path) as doc:
            for number,page in enumerate(doc.pages,1):
                assert abs(page.width-595.28)<1 and abs(page.height-841.89)<1,'Expected CSS A4'
                chars=[c for c in page.chars if c['text'].strip()]
                assert chars,'Blank PDF page'
                text=page.extract_text() or '';texts.append(text)
                # 18mm CSS margin is51.02pt. Allow rounding at the boundary.
                bounds=[min(c['x0'] for c in chars),min(c['top'] for c in chars),max(c['x1'] for c in chars),max(c['bottom'] for c in chars)]
                assert bounds[0]>=50 and bounds[1]>=50 and bounds[2]<=page.width-50 and bounds[3]<=page.height-50,(case['case'],number,bounds)
                assert '\ufffd' not in text and '(cid:' not in text,'Unmapped glyph'
                pages.append({'page':number,'width_pt':round(page.width,3),'height_pt':round(page.height,3),'text_bounds_pt':[round(n,3) for n in bounds],'characters':len(chars)})
        text='\n'.join(texts)
        assert 'Use your browser' not in text,'Screen instructions printed'
        assert 'OTHER_MEMBER_SECRET_SENTINEL' not in text and 'ASSESSMENT_SECRET_SENTINEL' not in text
        count={'personal-multipage':8,'room-owned':4}.get(case['case'],0)
        for i in range(1,count+1):
            assert text.count(f'NOTE_{i}_START')==1 and text.count(f'NOTE_{i}_END')==1,'Missing or repeated note content'
        if count:assert all(value in text for value in ('Ṭawng','ṭha','â','ê','î','ô','û','<script> & < >.'))
        if case['case']=='assessment-filtered':assert 'AVAILABLE_NOTE_SENTINEL' in text
        if case['case']=='empty':assert 'No notes are available to print.' in text
        results.append({'case':case['case'],'file':case['file'],'sha256':case['sha256'],'pages':pages,'note_boundaries_complete_once':True,'privacy_markers_absent':True,'all_text_inside_18mm_margins':True,'no_blank_pages_or_unmapped_glyphs':True})
    report.write_text(json.dumps({'cases':results,'total_pages':sum(len(x['pages']) for x in results),'visual_inspection_required':True},indent=2)+'\n')
    print('All four browser-generated PDFs pass text, privacy, A4 and margin checks.')
if __name__=='__main__':
    assert len(sys.argv)==3
    main(Path(sys.argv[1]),Path(sys.argv[2]))
