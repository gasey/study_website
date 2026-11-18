"""Private billing rehearsal, reached through an SSH tunnel only.

The public Caddy site forwards only the signed webhook endpoint. This app uses
an empty, separate database and test keys; it never imports app.main or workers.
"""
import hashlib
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.config import settings
from app.db import close_pool, cursor, open_pool
from app.routers.billing import router
from app.services.account_boundary import AccountBoundary

if not settings.razorpay_key_id.startswith('rzp_test_'):
    raise RuntimeError('This service requires Razorpay test keys')
if 'finna_paytest' not in settings.database_url:
    raise RuntimeError('This service requires its separate test database')
if settings.public_origin != 'http://127.0.0.1:8011':
    raise RuntimeError('Checkout must stay on the private SSH tunnel')


@asynccontextmanager
async def lifespan(app):
    await open_pool()
    try:
        yield
    finally:
        await close_pool()


app = FastAPI(title='Finna Razorpay test only', lifespan=lifespan,
              docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(AccountBoundary)
app.include_router(router)


@app.get('/api/health')
async def health():
    async with cursor() as cur:
        await cur.execute('SELECT current_database() AS db')
        row = await cur.fetchone()
    return {'status': 'ok', 'test_mode': True, 'isolated_database': row['db'] == 'finna_paytest'}


@app.get('/', response_class=HTMLResponse)
async def checkout_page():
    token = os.environ['FINNA_TEST_SESSION']
    csrf = hashlib.sha256(('bank-review:' + token).encode()).hexdigest()
    html = Path(__file__).with_name('razorpay-test.html').read_text().replace('__CSRF__', csrf)
    response = HTMLResponse(html, headers={'Cache-Control': 'no-store'})
    response.set_cookie('ism_session', token, httponly=True, samesite='strict', max_age=3600)
    return response
