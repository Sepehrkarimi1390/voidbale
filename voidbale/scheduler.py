import asyncio

class Scheduler:
    def __init__(self):
        self._tasks=set()
        self._closed=False
    def every(self, seconds, callback, *args, **kwargs):
        async def runner():
            while not self._closed:
                await asyncio.sleep(seconds)
                if not self._closed: await callback(*args, **kwargs)
        task=asyncio.create_task(runner()); self._tasks.add(task); task.add_done_callback(self._tasks.discard); return task
    def once(self, delay, callback, *args, **kwargs):
        async def runner():
            await asyncio.sleep(delay)
            if not self._closed: await callback(*args, **kwargs)
        task=asyncio.create_task(runner()); self._tasks.add(task); task.add_done_callback(self._tasks.discard); return task
    async def close(self):
        self._closed=True
        tasks=list(self._tasks)
        for task in tasks: task.cancel()
        if tasks: await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()
