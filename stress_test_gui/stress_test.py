import asyncio
from collections.abc import Callable
from concurrent.futures import Future
import aiohttp

class StressTest:
    def __init__(self,
                 loop: asyncio.AbstractEventLoop,
                 url: str,
                 total_requests: int,
                 callback: Callable[[int, int], None]):
        self._completed_request = 0
        self._load_test_future: Future | None = None
        self._loop = loop
        self._url = url
        self._total_requests = total_requests
        self._callback = callback
        self._refresh_rate = total_requests // 100

    def start(self):
        future = asyncio.run_coroutine_threadsafe(self._make_requests(), self._loop)
        self._load_test_future = future

    def cancel(self):
        if self._load_test_future:
            self._loop.call_soon_threadsafe(self._load_test_future.cancel)

    async def _get_url(self, session: aiohttp.ClientSession, url: str) -> None:
        try:
            await session.get(url)
        except Exception as e:
            print(e)

        self._completed_request += 1

        if self._completed_request % self._refresh_rate == 0 or self._completed_request == self._total_requests:
            self._callback(self._completed_request, self._total_requests)

    async def _make_requests(self):
        async with aiohttp.ClientSession() as session:
            reqs = [
                self._get_url(session, self._url)
                for _ in range(self._total_requests)
            ]
            await asyncio.gather(*reqs)


