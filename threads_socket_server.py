from threading import Thread
import socket

class ClientEchoThread(Thread):
    def __init__(self, client: socket.socket):
        super().__init__()
        self.client = client

    def run(self):
        try:
            while True:
                data = self.client.recv(2048)
                if not data:
                    raise BrokenPipeError('Подключение закрыто')
                print(f'Получено {data}')
                self.client.sendall(data)
        except OSError as e:
            print(f'Поток прерван исключением {e}, остановка')

    def close(self):
        if self.is_alive():
            self.client.sendall((bytes('Останавливаюсь', encoding='utf-8')))
            self.client.shutdown(socket.SHUT_RDWR)


if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', 8000))
        server.listen()
        connection_threads = []

        try:
            while True:
                connection, addr = server.accept()
                print(f'Подключение {addr}')
                thread = ClientEchoThread(connection)
                connection_threads.append(thread)
                thread.start()
        except KeyboardInterrupt:
            print('CTRL + C STOOOOOP')
            [thread.close() for thread in connection_threads]
