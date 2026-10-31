"""Small process-local cache ONLY for public catalog counts, never learner data."""
import asyncio,copy,time
from collections import OrderedDict
from ..config import settings
class PublicCatalogCache:
    def __init__(self,clock=time.monotonic,limit=32):
        self.clock=clock;self.limit=limit;self.entries=OrderedDict();self.locks={};self.generation=0
    def clear(self):self.generation+=1;self.entries.clear()
    async def get(self,key,load,ttl):
        if ttl<=0:return await load()
        lock=self.locks.setdefault(key,asyncio.Lock())
        async with lock:
            hit=self.entries.get(key)
            if hit and hit[0]>self.clock():return copy.deepcopy(hit[1])
            generation=self.generation;data=await load()
            if generation==self.generation:
                self.entries[key]=(self.clock()+min(ttl,60),copy.deepcopy(data));self.entries.move_to_end(key)
                while len(self.entries)>self.limit:self.entries.popitem(last=False)
            return data
catalog_cache=PublicCatalogCache()
async def public_catalog(key,load):return await catalog_cache.get(key,load,settings.public_catalog_cache_seconds)
class InvalidatePublicCatalog:
    def __init__(self,app):self.app=app
    async def __call__(self,scope,receive,send):
        mutating=scope.get('type')=='http' and scope.get('method')not in ('GET','HEAD','OPTIONS') and scope.get('path','').startswith(('/api/admin/','/api/collections'))
        async def outgoing(message):
            if mutating and message['type']=='http.response.start' and message['status']<400:catalog_cache.clear()
            await send(message)
        await self.app(scope,receive,outgoing)
