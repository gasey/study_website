#!/usr/bin/env python3
"""Produce a local auditable extraction artifact; never writes canonical content."""
import argparse,hashlib,json,subprocess
from pathlib import Path

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('pdf',type=Path);parser.add_argument('--output',required=True,type=Path)
 args=parser.parse_args();pdf=args.pdf.resolve()
 if not pdf.is_file():parser.error('PDF not found')
 result=subprocess.run(['pdftotext','-layout',str(pdf),'-'],capture_output=True,timeout=120,check=True)
 text=result.stdout.decode('utf-8',errors='replace')
 if len(text.strip())<30:parser.error('Too little extracted text. Use OCR or reviewed transcription and check against the PDF.')
 args.output.mkdir(parents=True,exist_ok=True)
 (args.output/'extracted.txt').write_text(text)
 with pdf.open('rb') as file:source=hashlib.file_digest(file,'sha256').hexdigest()
 artifact={'schema_version':1,'source_sha256':source,'text_sha256':hashlib.sha256(result.stdout).hexdigest(),
 'pages':max(1,text.count('\f')),'characters':len(text),'tool':'pdftotext','note':'Local text extraction only. Question segmentation, options, instructions and figures require source review.'}
 (args.output/'artifact.json').write_text(json.dumps(artifact,indent=2)+'\n')
 print(json.dumps(artifact,indent=2))
if __name__=='__main__':main()
