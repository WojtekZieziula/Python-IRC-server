import asyncio
import sys
from collections.abc import AsyncGenerator

import pytest

from src.channel_manager import ChannelManager
from src.config import ServerConfig
from src.server import Server
from src.user_manager import UserManager


@pytest.fixture(autouse=True)
def reset_state() -> None:
    UserManager().users.clear()
    ChannelManager().channels.clear()


@pytest.fixture
def server_config() -> ServerConfig:
    return ServerConfig(
        name="test.integration",
        host="127.0.0.1",
        port=0,
        password="password",
    )


@pytest.fixture
async def running_server(server_config: ServerConfig) -> AsyncGenerator[int, None]:
    server_app = Server(server_config)
    server_task = asyncio.create_task(server_app.start())

    while not server_app.server or not server_app.server.sockets:
        await asyncio.sleep(0.01)

    port = server_app.server.sockets[0].getsockname()[1]
    yield port

    await server_app.stop()
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass


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


@pytest.mark.asyncio
async def test_integration_chat_between_users(running_server: int) -> None:
    port = running_server
    alice = IRCClient(port, "Alice")
    bob = IRCClient(port, "Bob")

    try:
        await alice.connect()
        await bob.connect()

        await alice.send("JOIN #general")
        await alice.wait_for_message("JOIN #general")

        await bob.send("JOIN #general")
        await bob.wait_for_message("JOIN #general")

        await alice.wait_for_message("Bob!Bob@127.0.0.1 JOIN #general")

        await alice.send("PRIVMSG #general :Cześć Bob!")
        msg = await bob.wait_for_message("PRIVMSG #general :Cześć Bob!")
        assert "Alice" in msg

    finally:
        await alice.close()
        await bob.close()


@pytest.mark.asyncio
async def test_integration_kick_scenario(running_server: int) -> None:
    port = running_server
    admin = IRCClient(port, "Admin")
    intruder = IRCClient(port, "Intruder")

    try:
        await admin.connect()
        await intruder.connect()

        await admin.send("JOIN #secret")
        await admin.wait_for_message("JOIN #secret")

        await intruder.send("JOIN #secret")
        await intruder.wait_for_message("JOIN #secret")

        await admin.send("KICK #secret Intruder :Bye bye")

        kick_msg = await intruder.wait_for_message("KICK #secret Intruder")
        assert "Bye bye" in kick_msg

        await intruder.send("PRIVMSG #secret :I am still here")
        await intruder.wait_for_message("404")

    finally:
        await admin.close()
        await intruder.close()


@pytest.mark.asyncio
async def test_integration_connect_and_quit(running_server: int) -> None:
    port = running_server
    client = IRCClient(port, "Tester")

    try:
        await client.connect()
        await client.send("QUIT :Going sleep")
        if client.reader:
            data = await client.reader.read(1024)
            assert data == b"" or b"ERROR" in data
    finally:
        await client.close()
