import asyncio
from collections.abc import AsyncGenerator

import pytest

from src.config import ServerConfig
from src.server import Server


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
