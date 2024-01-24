import asyncio, signal
import socket
from typing import NoReturn

echo_tasks = []

async def echo(connection: socket,
               loop: asyncio.AbstractEventLoop) -> None:
    try:
        while data := await loop.sock_recv(connection, 1024):
            if data == b'boom\r\n':
                raise Exception('Ошибка сети')
        await loop.sock_sendall(connection, data)
    except Exception:
        print('Error')
    finally:
        connection.close()

class GracefulExit(SystemExit):
    pass

def shutdown():
    raise GracefulExit

async def close_echo_tasks(echo_tasks: list[asyncio.Task]):
    waiters = [asyncio.wait_for(t, timeout=2) for t in echo_tasks]
    for task in waiters:
        try:
            await task
        except TimeoutError:
            pass

async def listen_for_connection(server_socket: socket,
                                loop: asyncio.AbstractEventLoop) -> NoReturn:
    while True:
        connection, address = await loop.sock_accept(server_socket)
        connection.setblocking(False)
        print(f'Запрос на подключение: {address}')
        task = asyncio.create_task(echo(connection, loop))
        echo_tasks.append(task)

async def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_address = ('127.0.0.1', 8000)
    server_socket.setblocking(False)
    server_socket.bind(server_address)
    server_socket.listen()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, shutdown)
    loop.add_signal_handler(signal.SIGTERM, shutdown)
    await listen_for_connection(server_socket, loop)

loop = asyncio.new_event_loop()
try:
    loop.run_until_complete(main())
except GracefulExit:
    loop.run_until_complete(close_echo_tasks(echo_tasks))
finally:
    loop.close()