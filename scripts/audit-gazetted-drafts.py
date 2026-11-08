#!/usr/bin/env python3
"""Read-only independent PDF geometry/text checks for staged Gazetted drafts.

Use the bundled Python runtime (PyMuPDF/Pillow). No bank or workflow writes.
Token checks supplement visual inspection; a difference is never auto-corrected.
"""
import argparse
import collections
import hashlib
import json
import re
import unicodedata
from pathlib import Path
import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont


def clean(text):
    return '\n'.join(line for line in text.splitlines()
                     if not re.fullmatch(r'\s*(?:Series\s*-\s*[AB]\s*)?-\s*\d+\s*-\s*', line)
                     and not re.fullmatch(r'\s*(?:\*\s*)+\s*', line)).strip()


def token_list(text):
    text = unicodedata.normalize('NFKC', text).casefold()
    text = re.sub(r'\([a-d]\)', '', text)
    return re.findall(r'[^\W_]+|[₹$%°+*/=<>]|_+', text)


def tokens(text):return collections.Counter(token_list(text))


def difference(source, saved, ordered=False):
    a, b = tokens(source), tokens(saved)
    if a!=b:return {'source_only': dict(a-b), 'draft_only': dict(b-a)}
    if ordered and token_list(source)!=token_list(saved):return {'word_order_differs':True}
    return None


def inspect(draft, pdf):
    questions = draft['payload']['questions']
    starts = []
    for q in questions:
        number = q['number'].lstrip('AB')
        page = pdf[q['page']-1]
        matches = [w for w in page.get_text('words') if w[4] == number+'.' and w[0] < 80]
        if len(matches) != 1:
            raise ValueError(f"Ambiguous printed locator: {draft['source_id']} {q['number']}: {matches}")
        starts.append((q['page'], matches[0][1]))
    result = []
    for i, q in enumerate(questions):
        start_page, top = starts[i]
        next_page, next_top = starts[i+1] if i+1 < len(starts) else (len(pdf), pdf[-1].rect.height-35)
        parts, rectangles, graphical = [], [], []
        for p in range(start_page, next_page+1):
            page = pdf[p-1]
            y0 = top-1 if p == start_page else 50
            y1 = next_top-1 if p == next_page else page.rect.height-35
            if y1 <= y0:
                continue
            # Instructions appearing before the next numbered question belong
            # to that next task. Stop the current transcription at their row.
            words = page.get_text('words')
            cuts = [w[1]-1 for w in words if (w[4]=='UNIT' or w[4] in ('Direction','PART-','PART') and w[0]<220) and y0+2<w[1]<y1]
            if cuts:
                y1 = min(cuts)
            if y1 <= y0:
                continue
            rect = fitz.Rect(25, y0, page.rect.width-20, y1)
            source = clean(page.get_text('text', clip=rect, sort=True))
            if p == start_page:
                source = re.sub(r'^\s*\d+\.\s*', '', source)
            graphics_before = len(graphical)
            for drawing in page.get_drawings():
                r = drawing['rect']
                if r.y0 >= y0 and r.y1 <= y1 and r.x0 >= 25 and max(r.width,r.height) > 5:
                    graphical.append({'page':p,'kind':'drawing','bbox':list(r)})
            for image in page.get_image_info():
                r = fitz.Rect(image['bbox'])
                if r.intersects(rect):graphical.append({'page':p,'kind':'image','bbox':list(r)})
            # A task ending at the preceding page bottom can leave an empty
            # strip above the next page's first question. It is not a second
            # task fragment and must not suppress per-option order checks.
            if source or len(graphical) > graphics_before:
                parts.append(source);rectangles.append((p, rect))
        source = clean('\n'.join(parts))
        saved = '\n'.join([q['question'], *q['options'], q['passage']])
        option_checks = []
        if q['type'] == 'mcq' and len(rectangles) == 1:
            p, rect = rectangles[0];page=pdf[p-1]
            labels = [w for w in page.get_text('words',clip=rect) if re.fullmatch(r'\([a-d]\)',w[4])]
            if sorted(w[4] for w in labels) == ['(a)','(b)','(c)','(d)']:
                for letter, option in zip('abcd',q['options']):
                    w = next(w for w in labels if w[4]=='('+letter+')')
                    right = min([v[0]-2 for v in labels if v[0] > w[0]+25]+[rect.x1])
                    bottom = min([v[1]-1 for v in labels if abs(v[0]-w[0]) < 25 and v[1] > w[1]+2]+[rect.y1])
                    value = clean(page.get_text('text',clip=fitz.Rect(w[2]-0.2,w[1]-0.5,right,bottom),sort=True))
                    option_checks.append({'letter':letter,'difference':difference(value,option,ordered=True),'source':value})
            else:
                option_checks.append({'needs_visual_option_check':True,'labels':[w[4]for w in labels]})
        stem=source.split('(a)',1)[0] if q['type']=='mcq' else source
        result.append({'number':q['number'],'id':q['id'],'page':q['page'],
                       'rectangles':[{'page':p,'bbox':list(r)}for p,r in rectangles],
                       'difference':difference(source,saved),'source_text':source,
                       'stem_order_difference':difference(stem,q['question']+'\n'+q['passage'],ordered=True) if q['type']=='mcq' else None,
                       'option_checks':option_checks,'graphics':graphical,'has_saved_crop':bool(q['figure_job'])})
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',required=True,type=Path)
    parser.add_argument('--sources',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    snapshot=json.loads(args.snapshot.read_text());result={'drafts':[],'visual_sheets':[]}
    for draft in snapshot['drafts']:
        name=Path(draft['source_id']).name if not draft['source_id'].endswith('COMMON.pdf') else 'common-2016-paper-i.pdf'
        path=args.sources/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=draft['source_sha256']:raise ValueError('Source changed: '+name)
        pdf=fitz.open(path);checks=inspect(draft,pdf)
        result['drafts'].append({'id':draft['id'],'filename':name,'questions':checks})
        for first in range(0,len(pdf),2):
            images=[]
            for p in range(first,min(first+2,len(pdf))):
                pix=pdf[p].get_pixmap(matrix=fitz.Matrix(900/pdf[p].rect.width,900/pdf[p].rect.width),alpha=False)
                images.append(Image.frombytes('RGB',(pix.width,pix.height),pix.samples))
            sheet=Image.new('RGB',(sum(im.width for im in images),max(im.height for im in images)+28),'#e8e8e8');draw=ImageDraw.Draw(sheet)
            x=0
            for n,im in enumerate(images):
                sheet.paste(im,(x,28));draw.text((x+8,5),name+' / physical page '+str(first+n+1),fill='black');x+=im.width
            dest=args.output/(path.stem+'-pages-'+str(first+1)+'-'+str(min(first+2,len(pdf)))+'.png');sheet.save(dest)
            result['visual_sheets'].append({'file':str(dest),'source_sha256':draft['source_sha256'],'pages':list(range(first+1,min(first+2,len(pdf))+1))})
    (args.output/'geometry-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps([{'file':d['filename'],'questions':len(d['questions']),
                      'token_differences':[q['number']for q in d['questions']if q['difference']],
                      'stem_order_differences':[q['number']for q in d['questions']if q['stem_order_difference']],
                      'option_differences':[q['number']for q in d['questions']if any(c.get('difference')or c.get('needs_visual_option_check')for c in q['option_checks'])],
                      'graphics_without_crop':[q['number']for q in d['questions']if q['graphics']and not q['has_saved_crop']]}for d in result['drafts']],indent=2))


if __name__=='__main__':main()
