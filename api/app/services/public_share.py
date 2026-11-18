"""Public source-only previews. Never read answers, attempts or learner identity."""
from html import escape
from urllib.parse import quote, urlencode
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from ..config import settings
from ..exam_scope import scope_condition
from .source_identity import identities_for, display_identity


async def question_preview(cur, question_id, paper=None, exam_scope='mizoram-recruitment'):
    # The appearance and canonical record must still be live in the same read.
    await cur.execute(f'''SELECT q.question, a.paper_id, a.qnum, p.exam_name AS exam,
        p.year FROM canonical_questions q JOIN appearances a ON a.canonical_id=q.id
        JOIN papers p ON p.id=a.paper_id WHERE q.id=%s AND q.status='live'
        AND (%s::text IS NULL OR a.paper_id=%s) AND {scope_condition('p', exam_scope)}
        ORDER BY p.year DESC NULLS LAST,a.is_primary DESC,a.paper_id,a.id LIMIT 1''',
        (question_id, paper, paper))
    row = await cur.fetchone()
    if not row:
        raise HTTPException(404, 'This question source is not available')
    row.update(display_identity(row['paper_id'], row['qnum'], await identities_for(cur, [row['paper_id']])))
    badge = ' · '.join(str(x) for x in (row['exam'], row['year'], 'Q'+str(row['qnum']) if row['qnum'] else None) if x)
    query = urlencode({'paper': row['paper_id'], 'exam_scope': exam_scope})
    encoded = quote(question_id, safe='')
    return {'title': row['question'], 'description': 'Practice this question on Finna.',
            'badge': badge, 'target_path': '/bank/'+encoded+'?'+query,
            'share_path': '/api/questions/'+encoded+'/share?'+query}


def share_page(*, title, description, badge, target_path, share_path, action):
    # Only our configured origin and server-authored paths enter links. No Host,
    # return URL, private collection context, answer snapshot or raw HTML reader.
    origin = settings.public_origin.rstrip('/')
    target = escape(origin+target_path, quote=True)
    url = escape(origin+share_path, quote=True)
    image = escape(origin+'/og-finna.png', quote=True)
    preview_title = escape(title[:320])
    preview_description = escape(' · '.join((badge, description))[:600])
    title, description, badge, action = map(escape, (title, description, badge, action))
    # Keep crawlers on the metadata document; an explicit link opens the app.
    return HTMLResponse(f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · Finna</title><meta name="description" content="{description}">
<meta property="og:type" content="website"><meta property="og:title" content="{preview_title}">
<meta property="og:description" content="{preview_description}"><meta property="og:url" content="{url}">
<meta property="og:site_name" content="Finna"><meta property="og:image" content="{image}">
<meta property="og:image:type" content="image/png"><meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630"><meta property="og:image:alt" content="Finna · Study. Practice. Revise.">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{preview_title}">
<meta name="twitter:description" content="{preview_description}"><meta name="twitter:image" content="{image}">
<link rel="canonical" href="{target}"><meta name="color-scheme" content="light dark">
<style>
:root{{--paper:#F3F5FA;--card:#FFFFFF;--ink:#0E1330;--muted:#4A5170;--line:#DDE3F3;--pri:#1F4BE0;--on-pri:#FFFFFF}}
@media(prefers-color-scheme:dark){{:root{{--paper:#0B0F24;--card:#151B3A;--ink:#F1F3FF;--muted:#A9B0D0;--line:#28315D;--pri:#6C8DFF;--on-pri:#0B0F24}}}}
*{{box-sizing:border-box}}body{{margin:0;padding:24px;background:var(--paper);color:var(--ink);font:16px/1.5 system-ui,sans-serif}}
main{{max-width:760px;margin:8vh auto;background:var(--card);border:1px solid var(--line);border-radius:24px;padding:clamp(20px,5vw,40px);overflow-wrap:anywhere}}
.brand{{font-size:28px;font-weight:900;letter-spacing:-.03em}}.dot{{color:#FFC83D}}
.badge{{color:var(--muted);font-size:14px}}h1{{font-size:clamp(22px,4vw,32px);line-height:1.35;white-space:pre-wrap}}
.description{{color:var(--muted);white-space:pre-wrap}}a{{display:inline-flex;align-items:center;min-height:48px;padding:12px 20px;border-radius:14px;background:var(--pri);color:var(--on-pri);font-weight:700;text-decoration:none}}
a:focus-visible{{outline:3px solid #FFC83D;outline-offset:4px}}
</style></head><body><main><div class="brand">Finna<span class="dot">.</span></div>
<p class="badge">{badge}</p><h1>{title}</h1><p class="description">{description}</p>
<a href="{target}">{action} →</a></main></body></html>''', headers={
        'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer',
        'X-Content-Type-Options': 'nosniff',
        'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"})
