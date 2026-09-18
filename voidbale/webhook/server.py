from aiohttp import web

class WebhookServer:
    def __init__(self, bot, path="/webhook", secret_token=None, max_body_size=1048576):
        self.bot=bot; self.path=path; self.secret_token=secret_token
        self.app=web.Application(client_max_size=max_body_size)
        self.app.router.add_post(path,self.handle)
        self.app.router.add_get("/health",self.health)
    async def health(self,request): return web.json_response({"ok":True,"service":"voidbale"})
    async def handle(self,request):
        if self.secret_token is not None and request.headers.get("X-Bale-Bot-Api-Secret-Token") != self.secret_token:
            return web.Response(status=403,text="Forbidden")
        try: update=await request.json()
        except Exception: return web.Response(status=400,text="Invalid JSON")
        await self.bot.process_update(update)
        return web.json_response({"ok":True})
    async def start_async(self,host="0.0.0.0",port=8080):
        runner=web.AppRunner(self.app)
        await runner.setup()
        site=web.TCPSite(runner,host,port)
        await site.start()
        try:
            while True: await __import__("asyncio").sleep(3600)
        finally: await runner.cleanup()
    def run(self,host="0.0.0.0",port=8080):
        web.run_app(self.app,host=host,port=port)
    def create_app(self): return self.app
