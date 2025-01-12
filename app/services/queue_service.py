import asyncio
from collections import defaultdict
from typing import Dict, List, Optional, Callable, Awaitable
from datetime import datetime

class QueueService:
    def __init__(self, max_concurrent: int = 3):
        self.queues: Dict[int, asyncio.Queue] = defaultdict(asyncio.Queue)
        self.max_concurrent = max_concurrent
        self.processing: Dict[int, int] = defaultdict(int)
        self.tasks: List[asyncio.Task] = []

    async def add_task(self, channel_id: int, task: Callable[..., Awaitable], *args, **kwargs):
        await self.queues[channel_id].put((task, args, kwargs))
        if self.processing[channel_id] < self.max_concurrent:
            self.tasks.append(asyncio.create_task(self._process_queue(channel_id)))

    async def _process_queue(self, channel_id: int):
        self.processing[channel_id] += 1
        try:
            while not self.queues[channel_id].empty():
                task, args, kwargs = await self.queues[channel_id].get()
                await task(*args, **kwargs)
                self.queues[channel_id].task_done()
        finally:
            self.processing[channel_id] -= 1
