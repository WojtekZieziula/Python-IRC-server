import asyncio
import sys


class IRCClient:
    def __init__(self, port: int, nick: str) -> None:
        self.port = port
        self.nick = nick
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        self.reader, self.writer = await asyncio.open_connection("127.0.0.1", self.port)

        self.writer.write(b"PASS password\r\n")
        self.writer.write(f"NICK {self.nick}\r\n".encode())
        self.writer.write(f"USER {self.nick} 0 * :Test User\r\n".encode())
        await self.writer.drain()

        await self.wait_for_message("001")

    async def send(self, command: str) -> None:
        if self.writer:
            self.writer.write(f"{command}\r\n".encode())
            await self.writer.drain()

    async def wait_for_message(
        self, expected_substring: str, timeout: float = 2.0
    ) -> str:
        end_time = asyncio.get_running_loop().time() + timeout

        while True:
            time_left = end_time - asyncio.get_running_loop().time()
            if time_left <= 0:
                raise TimeoutError(
                    f"[{self.nick}] Timeout - oczekiwano '{expected_substring}'"
                )

            if not self.reader:
                raise ConnectionResetError("Reader is not initialized")

            try:
                line = await asyncio.wait_for(self.reader.readline(), timeout=time_left)

                if not line:
                    raise ConnectionResetError(
                        f"[{self.nick}] Serwer zamknął połączenie"
                    )

                decoded = line.decode("utf-8", errors="ignore").strip()

                print(f"Server -> {self.nick}: {decoded}", file=sys.stderr)

                if expected_substring in decoded:
                    return decoded

            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"[{self.nick}] Timeout - oczekiwano '{expected_substring}'"
                )

    async def close(self) -> None:
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass
