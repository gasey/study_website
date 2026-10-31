#!/usr/bin/env bash
# Mirror canonical-bank source PDFs to the study host for static Range serving.
set -euo pipefail

HOST=${ISM_HOST:-ubuntu@152.67.31.231}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BANK_ROOT=${ISM_BANK_ROOT:-"$ROOT/../mpsc-question-bankv2"}
BANK=${ISM_BANK:-"$BANK_ROOT/bank/mpsc_bank_v2.json"}
DRY_RUN=${1:-}
FIGURES_ONLY=${2:-}
[ -f "$BANK" ] || { echo "bank not found: $BANK" >&2; exit 1; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
python3 - "$BANK" "$BANK_ROOT/pdfs" "$TMP/files.txt" "$BANK_ROOT" "$TMP/figures.txt" <<'PY'
import json, os, sys
bank, root, output, bank_root, figures_output = sys.argv[1:]
data = json.load(open(bank, encoding="utf-8"))
paths, missing = [], []
for paper in data.get("papers", []):
    if paper.get("examType") == "Community": continue
    source = (paper.get("sourceFile") or "").replace("\\", "/").strip("/")
    if not source.startswith("Old_Questions/") or not source.lower().endswith(".pdf"):
        missing.append((paper.get("id"), "not a relative source PDF path")); continue
    if any(part in {"", ".", ".."} for part in source.split("/")):
        missing.append((paper.get("id"), "unsafe source path")); continue
    if not os.path.isfile(os.path.join(root, source)):
        missing.append((paper.get("id"), source)); continue
    paths.append(source)
if missing:
    for paper_id, path in missing[:20]: print(f"missing source PDF: {paper_id}: {path}", file=sys.stderr)
    raise SystemExit(f"refusing incomplete sync: {len(missing)} of {len(data.get('papers', []))} papers lack a PDF")
if len(paths) != len(set(paths)): raise SystemExit("duplicate source paths in bank")
open(output, "w", encoding="utf-8").write("\n".join(paths) + "\n")
print(f"Source PDFs ready: {len(paths)} papers")
figures = set()
for question in data.get("questions", []):
    image = (question.get("figureImage") or "").replace("\\", "/").strip("/")
    if not image:
        continue
    parts = image.split("/")
    if len(parts) != 3 or parts[:2] != ["images", "page-renders"] or not parts[2].endswith(".png"):
        raise SystemExit(f"unsafe or unsupported figure path: {image}")
    if not os.path.isfile(os.path.join(bank_root, image)):
        raise SystemExit(f"missing source figure image: {image}")
    figures.add(parts[2])
open(figures_output, "w", encoding="utf-8").write("\n".join(sorted(figures)) + ("\n" if figures else ""))
print(f"Question figure scans ready: {len(figures)} files")
PY

if [ "$DRY_RUN" = "--dry-run" ]; then
  rsync -a --dry-run --itemize-changes --files-from="$TMP/files.txt" -e ssh \
    "$BANK_ROOT/pdfs/" "$HOST:/tmp/ism-source-pdfs/"
  rsync -a --dry-run --itemize-changes --files-from="$TMP/figures.txt" -e ssh \
    "$BANK_ROOT/images/page-renders/" "$HOST:/tmp/ism-figures/"
  exit 0
fi
if [ "$FIGURES_ONLY" != "--figures-only" ]; then
  ssh "$HOST" 'rm -rf /tmp/ism-source-pdfs && mkdir -p /tmp/ism-source-pdfs'
  rsync -a --info=progress2 --files-from="$TMP/files.txt" -e ssh \
    "$BANK_ROOT/pdfs/" "$HOST:/tmp/ism-source-pdfs/"
fi
ssh "$HOST" 'rm -rf /tmp/ism-figures && mkdir -p /tmp/ism-figures'
rsync -a --info=progress2 --files-from="$TMP/figures.txt" -e ssh \
  "$BANK_ROOT/images/page-renders/" "$HOST:/tmp/ism-figures/"
if [ "$FIGURES_ONLY" != "--figures-only" ]; then
  ssh "$HOST" 'sudo mkdir -p /srv/study/papers/source && sudo rsync -a --delete /tmp/ism-source-pdfs/ /srv/study/papers/source/ && sudo chown -R caddy:caddy /srv/study/papers'
fi
ssh "$HOST" 'sudo mkdir -p /srv/study/papers/figures && sudo rsync -a --delete /tmp/ism-figures/ /srv/study/papers/figures/ && sudo chown -R caddy:caddy /srv/study/papers/figures'
ssh "$HOST" 'sudo python3 -' <<'PY'
from pathlib import Path
p = Path("/etc/caddy/sites/study.hawayu.in.caddy")
s = p.read_text()
route = "\thandle_path /papers/source/* {\n\t\troot * /srv/study/papers/source\n\t\theader Cache-Control \"public, max-age=86400\"\n\t\tfile_server\n\t}\n\n"
if "handle_path /papers/source/*" not in s:
    needle = "\thandle {\n\t\troot * /srv/study/public"
    if needle not in s:
        raise SystemExit("expected study site handler not found; Caddy config left unchanged")
    p.write_text(s.replace(needle, route + needle, 1))
figure_route = "\thandle_path /papers/figures/* {\n\t\troot * /srv/study/papers/figures\n\t\theader Cache-Control \"public, max-age=31536000, immutable\"\n\t\tfile_server\n\t}\n\n"
s = p.read_text()
if "handle_path /papers/figures/*" not in s:
    needle = "\thandle {\n\t\troot * /srv/study/public"
    if needle not in s:
        raise SystemExit("expected study site handler not found; Caddy config left unchanged")
    p.write_text(s.replace(needle, figure_route + needle, 1))
PY
ssh "$HOST" 'sudo caddy validate --config /etc/caddy/Caddyfile && sudo systemctl reload caddy'
echo "Source scans synced to $HOST:/srv/study/papers"
