import pytest
from unittest.mock import AsyncMock, MagicMock
from src.channel import Channel

@pytest.fixture
def channel():
    return Channel("#test")

@pytest.fixture
def mock_session():
    session = MagicMock()
    session.nickname = "Wojtek"
    session.send_reply = AsyncMock()
    return session

def test_channel_validation_logic():
    assert Channel.is_valid_name("#polska") is True
    assert Channel.is_valid_name("#channel123") is True

    assert Channel.is_valid_name("without_hash") is False
    assert Channel.is_valid_name("#with space") is False
    assert Channel.is_valid_name("#with,comma") is False
    assert Channel.is_valid_name("#toolong" + "a"*50) is False
    assert Channel.is_valid_name("#double#hash") is False

def test_channel_creation_fails_on_invalid_name():
    with pytest.raises(ValueError, match="Invalid channel name"):
        Channel("#invalid,name")

    with pytest.raises(ValueError):
        Channel("no_hash")

def test_channel_initialization(channel):
    assert channel.name == "#test"
    assert isinstance(channel.members, set)
    assert len(channel.members) == 0

def test_add_user(channel, mock_session):
    channel.add_user(mock_session)
    assert mock_session in channel.members
    assert len(channel.members) == 1

def test_add_user_duplicate(channel, mock_session):
    channel.add_user(mock_session)
    channel.add_user(mock_session)
    assert len(channel.members) == 1

def test_remove_user(channel, mock_session):
    channel.add_user(mock_session)
    channel.remove_user(mock_session)
    assert mock_session not in channel.members
    assert len(channel.members) == 0

def test_remove_user_not_in_channel(channel, mock_session):
    channel.remove_user(mock_session)
    assert len(channel.members) == 0

@pytest.mark.asyncio
async def test_broadcast_to_all(channel):
    user1 = MagicMock()
    user1.send_reply = AsyncMock()
    user2 = MagicMock()
    user2.send_reply = AsyncMock()

    channel.add_user(user1)
    channel.add_user(user2)

    await channel.broadcast("Hello all!")

    user1.send_reply.assert_called_once_with("Hello all!")
    user2.send_reply.assert_called_once_with("Hello all!")

@pytest.mark.asyncio
async def test_broadcast_with_skip_user(channel, mock_session):
    recipient = MagicMock()
    recipient.send_reply = AsyncMock()

    channel.add_user(mock_session)
    channel.add_user(recipient)

    await channel.broadcast("Secret message", skip_user=mock_session)

    recipient.send_reply.assert_called_once_with("Secret message")
    mock_session.send_reply.assert_not_called()
