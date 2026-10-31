import asyncio
from app.services.public_catalog_cache import PublicCatalogCache

def test_public_cache_coalesces_scopes_expires_and_copies():
    async def run():
        now=[0];cache=PublicCatalogCache(lambda:now[0],limit=2);calls=[]
        async def load():calls.append(1);await asyncio.sleep(.001);return {'count':len(calls)}
        rows=await asyncio.gather(*(cache.get(('taxonomy','all'),load,10)for _ in range(5)))
        assert len(calls)==1 and all(r=={'count':1}for r in rows)
        rows[0]['count']=99
        assert await cache.get(('taxonomy','all'),load,10)=={'count':1}
        assert await cache.get(('taxonomy','mizoram'),load,10)=={'count':2}
        now[0]=11;assert await cache.get(('taxonomy','all'),load,10)=={'count':3}
        cache.clear();assert await cache.get(('taxonomy','all'),load,10)=={'count':4}
        await cache.get(('third',),load,10);await cache.get(('fourth',),load,10);assert len(cache.entries)==2
    asyncio.run(run())

def test_failures_and_invalidation_during_load_do_not_populate_cache():
    async def run():
        cache=PublicCatalogCache();calls=[]
        async def fail():raise RuntimeError('temporary failure')
        try:await cache.get(('key',),fail,10)
        except RuntimeError:pass
        assert not cache.entries
        async def stale():calls.append(1);cache.clear();return 7
        assert await cache.get(('key',),stale,10)==7 and not cache.entries
        await cache.get(('key',),stale,0);assert len(calls)==2
    asyncio.run(run())

def test_only_successful_catalog_mutations_invalidate():
    from app.services.public_catalog_cache import InvalidatePublicCatalog,catalog_cache
    async def run():
        for method,path,status,invalidates in [('POST','/api/admin/review/publish',200,True),('PATCH','/api/collections/ldc',200,True),('POST','/api/admin/review/publish',403,False),('POST','/api/questions/id/answer',200,False),('GET','/api/admin/review',200,False)]:
            async def endpoint(scope,receive,send):
                await send({'type':'http.response.start','status':status,'headers':[]})
                await send({'type':'http.response.body','body':b''})
            before=catalog_cache.generation;messages=[]
            async def send(message):messages.append(message)
            await InvalidatePublicCatalog(endpoint)({'type':'http','method':method,'path':path},None,send)
            assert (catalog_cache.generation>before)==invalidates
            assert messages[0]['status']==status
    asyncio.run(run())
