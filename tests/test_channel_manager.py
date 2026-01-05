import pytest
from unittest.mock import MagicMock
from src.channel_manager import ChannelManager
from src.channel import Channel

@pytest.fixture
def channel_manager():
    manager = ChannelManager()
    manager.channels = {}
    return manager

@pytest.fixture
def mock_session():
    session = MagicMock()
    session.nickname = "Wojtek"
    return session

def test_singleton_behavior():
    manager1 = ChannelManager()
    manager2 = ChannelManager()
    assert manager1 is manager2

def test_normalization(channel_manager):
    assert channel_manager._normalize_name("Polska") == "#polska"
    assert channel_manager._normalize_name("#POLSKA") == "#polska"

def test_create_channel_success(channel_manager):
    channel = channel_manager.create_channel("Programowanie")
    assert channel.name == "#Programowanie"
    assert channel_manager.channel_exists("#programowanie")

def test_create_duplicate_channel_fails(channel_manager):
    channel_manager.create_channel("#test")
    with pytest.raises(ValueError, match="already exists"):
        channel_manager.create_channel("#TEST")

def test_create_invalid_channel_name_fails(channel_manager):
    invalid_names = ["#ka nal", "#kanał,z,przecinkiem", "#extra#hash"]
    for bad_name in invalid_names:
        with pytest.raises(ValueError, match="Invalid channel name"):
            channel_manager.create_channel(bad_name)

def test_get_or_create_behavior(channel_manager):
    channel1 = channel_manager.get_or_create_channel("python")
    channel2 = channel_manager.get_or_create_channel("#PYTHON")

    assert channel1 is channel2
    assert channel1.name == "#python"
    assert len(channel_manager.channels) == 1

def test_remove_user_from_all_channels_and_cleanup(channel_manager, mock_session):
    c1 = channel_manager.get_or_create_channel("#first")
    c2 = channel_manager.get_or_create_channel("#empty")

    other_user = MagicMock()
    c1.add_user(mock_session)
    c1.add_user(other_user)

    c2.add_user(mock_session)

    channel_manager.remove_user_from_all_channels(mock_session)

    assert channel_manager.channel_exists("#first") is True
    assert mock_session not in c1.members

    assert channel_manager.channel_exists("#empty") is False
    assert len(channel_manager.channels) == 1
