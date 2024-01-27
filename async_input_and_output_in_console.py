import asyncio
from asyncio import StreamReader
import sys

async def delay(t):
    print(f'Засыпаю на {t} секунд')
    await asyncio.sleep(t)
    print(f'Просыпаюсь от {t} сукунд')
    return t

async def create_stdin_reader() -> StreamReader:
    stream_reader = StreamReader()
    protocol = asyncio.StreamReaderProtocol(stream_reader)
    loop = asyncio.get_running_loop()
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    return stream_reader

async def main():
    stdin_reader = await create_stdin_reader()
    while True:
        delay_time = await stdin_reader.readline()
        asyncio.create_task(delay(int(delay_time)))

asyncio.run(main())
