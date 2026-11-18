"""HTTP validators for an explicit, answer-free anonymous browse surface.

This stores no responses. Existing catalog loaders own the bounded data cache;
validators are computed from the actual representation and its generation.
"""
import hashlib
import re
from urllib.parse import parse_qs

from starlette.datastructures import Headers, MutableHeaders

from .public_catalog_cache import catalog_cache
from .browse_allowance import power_filter


_PUBLIC_READS = (
    r'/api/questions',
    r'/api/questions/(?:taxonomy|papers)',
    r'/api/questions/[^/]+',
    r'/api/questions/[^/]+/next',
    r'/api/collections',
    r'/api/collections/[^/]+',
    r'/api/collections/[^/]+/(?:header|study-topics|paper-questions)',
)
_IDENTITY_HEADERS = ('cookie', 'authorization', 'x-device-id')
_MAX_BODY = 4 * 1024 * 1024


def anonymous_browse(request) -> bool:
    """Use the same decision for identity resolution and HTTP caching."""
    headers = Headers(scope=request)
    if any(name in headers for name in _IDENTITY_HEADERS):
        return False
    query = parse_qs(request.get('query_string', b'').decode('latin-1'), keep_blank_values=True)
    # Never share personal history filters or assessment-gated learning entries.
    return (all(value == 'all' for value in query.get('study_status', ['all']))
            and 'learning_entry' not in query and not power_filter(query))


def _matches(value: str, etag: str) -> bool:
    # If-None-Match uses weak comparison for GET; support lists and wildcard.
    return any(tag.strip().removeprefix('W/') in (etag, '*') for tag in value.split(','))


class PublicBrowseCache:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if (scope['type'] != 'http'
                or not any(re.fullmatch(pattern, scope['path']) for pattern in _PUBLIC_READS)):
            return await self.app(scope, receive, send)

        eligible = scope['method'] == 'GET' and anonymous_browse(scope)
        generation = catalog_cache.generation
        start = None
        chunks = []
        size = 0

        async def outgoing(message):
            nonlocal eligible, start, size
            if message['type'] == 'http.response.start':
                headers = MutableHeaders(scope=message)
                for name in _IDENTITY_HEADERS:
                    headers.add_vary_header(name.title())
                eligible = (eligible and message['status'] == 200
                            and 'set-cookie' not in headers
                            and headers.get('content-type', '').startswith('application/json'))
                headers['Cache-Control'] = 'private, no-store'
                if not eligible:
                    if 'etag' in headers:
                        del headers['etag']
                    await send(message)
                else:
                    start = message
            elif message['type'] == 'http.response.body' and eligible:
                chunks.append(message.get('body', b''))
                size += len(message.get('body', b''))
                if size > _MAX_BODY:
                    eligible = False
                    await send(start)
                    await send({**message, 'body': b''.join(chunks)})
                    chunks.clear()
                elif not message.get('more_body', False):
                    body = b''.join(chunks)
                    headers = MutableHeaders(scope=start)
                    if generation == catalog_cache.generation:
                        # Full URL includes exam scope, filters, order and pagination.
                        key = (str(generation).encode() + b'\0' + scope['path'].encode()
                               + b'?' + scope.get('query_string', b'') + b'\0' + body)
                        etag = '"' + hashlib.sha256(key).hexdigest() + '"'
                        headers['ETag'] = etag
                        # Revalidate on reuse so an admin invalidation takes effect
                        # immediately, rather than trusting a browser's fresh copy.
                        headers['Cache-Control'] = 'public, max-age=0, must-revalidate'
                        if _matches(Headers(scope=scope).get('if-none-match', ''), etag):
                            start['status'] = 304
                            if 'content-length' in headers:
                                del headers['content-length']
                            body = b''
                    await send(start)
                    await send({**message, 'body': body})
            else:
                await send(message)

        await self.app(scope, receive, outgoing)
