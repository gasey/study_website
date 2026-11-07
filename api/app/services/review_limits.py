"""Bound review request bodies before JSON parsing, including chunked uploads."""
from starlette.responses import JSONResponse

class ReviewBodyLimit:
    def __init__(self,app,max_bytes=65536):self.app=app;self.max_bytes=max_bytes
    async def __call__(self,scope,receive,send):
        guarded=scope.get('type')=='http' and scope.get('method') in {'POST','PUT','PATCH'} and scope.get('path','').startswith(('/api/tests','/api/learning-catalog','/api/mocks','/api/contributions','/api/review','/api/admin/bank','/api/auth/mfa/','/api/rewards/','/api/me/exam-checkpoint/','/api/studio/','/api/materials/','/api/creators/','/api/community/','/api/desk/','/api/me/avatar','/api/me/calendar/','/api/admin/calendar/','/api/games/','/api/learning/','/api/study-sessions'))
        guarded=guarded or scope.get('type')=='http' and scope.get('method') in {'POST','PUT','PATCH'} and scope.get('path','').startswith(('/api/editorial/','/api/current-affairs/','/api/paper-workbench/','/api/topic-trail/'))
        if not guarded:return await self.app(scope,receive,send)
        limit=20971520 if scope.get('path')=='/api/paper-workbench/uploads' else 2097152 if scope.get('path','').startswith('/api/paper-workbench/drafts/') and scope.get('path','').endswith('/save') else 524288 if scope.get('path')=='/api/desk/personal' else self.max_bytes
        size=0;messages=[]
        while True:
            message=await receive()
            if message['type']=='http.disconnect':return
            size+=len(message.get('body',b''))
            if size>limit:
                return await JSONResponse({'detail':f'Request exceeds the {limit//1024} KiB size limit'},status_code=413)(scope,receive,send)
            messages.append(message)
            if not message.get('more_body',False):break
        async def replay():
            if messages:return messages.pop(0)
            return await receive()
        await self.app(scope,replay,send)
