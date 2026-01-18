import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.channel_manager import ChannelManager
from src.config import ServerConfig
from src.server import Server
from src.user_manager import UserManager


@pytest.fixture
def server_config() -> ServerConfig:
    return ServerConfig(name="test.irc", host="127.0.0.1", port=6667, password="pass")


@pytest.mark.asyncio
async def test_server_cleanup_on_disconnect(server_config: ServerConfig) -> None:
    UserManager().users.clear()
    ChannelManager().channels.clear()

    server = Server(server_config)

    mock_reader = AsyncMock(spec=asyncio.StreamReader)
    mock_writer = MagicMock(spec=asyncio.StreamWriter)
    
    mock_reader.readline.return_value = b""

    nickname = "TestUser"
    user_manager = UserManager()
    channel_manager = ChannelManager()

    with patch("src.server.ClientSession") as mock_session:
        instance = mock_session.return_value
        instance.nickname = nickname
        instance.host = "127.0.0.1"
        instance.quit = AsyncMock()

        user_manager.add_user(nickname, instance)

        channel_manager.get_or_create_channel("#test")
        channel = channel_manager.get_channel("#test")

        assert channel is not None
        channel.add_user(instance)

        await server.handle_client(mock_reader, mock_writer)

    assert not user_manager.is_nick_taken(nickname)
    assert len(channel_manager.channels) == 0
