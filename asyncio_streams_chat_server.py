import asyncio


class ChatServer:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients: {str: asyncio.StreamWriter} | {} = {}


    async def start_server(self):
        server = await asyncio.start_server(self._connect_client, self.host, self.port)
        async with server:
            await server.serve_forever()


    async def _connect_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        print(self.clients)
        writer.write('Вы успешно подключились!\nУкажите свое имя с помощью команды: "CONNECT username"\n'.encode())
        command_username = await reader.readline()
        if command_username.startswith(b'CONNECT'):
            username = command_username.split(b' ')[1]
            self.clients[username] = writer
            await self._on_connected(username, reader)

        else:
            writer.write('Недопустимая команда'.encode())
            writer.close()
            await writer.wait_closed()

    async def _listener(self, username, reader: asyncio.StreamReader):
        try:
            while data := await asyncio.wait_for(reader.readline(), timeout=60):
                await self._send_all(f'{username.decode().strip()}: {data.decode()}')

        except Exception as e:
            await self._remove_user(username)

    async def _remove_user(self, username):
        writer: asyncio.StreamWriter = self.clients[username]
        del self.clients[username]
        try:
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            pass
        finally:
            await self._send_all(f'{username.decode().strip()} покинул чат')

    async def _send_all(self, data: str):
        deactivate_users = []
        for username, writer in self.clients.items():
            try:
                if username.decode().strip() not in data:
                    writer.write(data.encode())
                    await writer.drain()
            except ConnectionError:
                deactivate_users.append(username)
        [asyncio.create_task(self._remove_user(username)) for username in deactivate_users]


    async def _on_connected(self, username: bytes, reader: asyncio.StreamReader):
        for user, writer in self.clients.items():
            writer.write(f'Подключился {username.decode()}'.encode())
        asyncio.create_task(self._listener(username, reader))


if __name__ == '__main__':
    chat_server = ChatServer('localhost', 8000)
    asyncio.run(chat_server.start_server())
