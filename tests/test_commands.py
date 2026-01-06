import pytest
from unittest.mock import AsyncMock, MagicMock, ANY
from src.commands import CommandHandler
from src.protocol import IRCMessage
from src.config import ServerConfig
from src.user_manager import UserManager
from src.channel_manager import ChannelManager

@pytest.fixture
def command_handler():
    UserManager().users = {}
    ChannelManager().channels = {}

    config = ServerConfig(name="test.server", host="127.0.0.1", port=6667, password="password")
    return CommandHandler(config)

@pytest.fixture
def registered_session():
    session = MagicMock()
    session.nickname = "Michal"
    session.username = "michal"
    session.host = "127.0.0.1"
    session.is_registered = True
    session.send_reply = AsyncMock()
    session.send_error = AsyncMock()
    session.quit = AsyncMock()
    return session

@pytest.mark.asyncio
async def test_registration_fail_bad_password(command_handler):
    session = MagicMock()
    session.nickname = "Michal"
    session.username = "michal"
    session.password_attempt = "wrong_password"
    session.is_registered = False
    session.send_error = AsyncMock()
    session.quit = AsyncMock()

    await command_handler.check_registration(session)

    session.send_error.assert_called_with("464", ":Password incorrect")
    session.quit.assert_called_once()

@pytest.mark.asyncio
async def test_nick_change_when_taken(command_handler, registered_session):
    UserManager().add_user("Hubert", MagicMock())

    msg = IRCMessage("NICK", ["Hubert"])
    await command_handler.handle(registered_session, msg)

    registered_session.send_error.assert_called_with("433", "*", "Hubert", ANY)

@pytest.mark.asyncio
async def test_privmsg_no_such_nick(command_handler, registered_session):
    msg = IRCMessage("PRIVMSG", ["DoesNotExist", "Hi!"])
    await command_handler.handle(registered_session, msg)

    registered_session.send_error.assert_called_with("401", "DoesNotExist", ANY)

@pytest.mark.asyncio
async def test_privmsg_to_channel_not_joined(command_handler, registered_session):
    ChannelManager().get_or_create_channel("#polska")

    msg = IRCMessage("PRIVMSG", ["#polska", "Siema!"])
    await command_handler.handle(registered_session, msg)

    registered_session.send_error.assert_called_with("404", "#polska", ANY)

@pytest.mark.asyncio
async def test_join_invalid_channel_name(command_handler, registered_session):
    msg = IRCMessage("JOIN", ["#invalid channel"])
    await command_handler.handle(registered_session, msg)

    registered_session.send_error.assert_called_with("403", "#invalid channel", ANY)

@pytest.mark.asyncio
async def test_part_not_on_channel(command_handler, registered_session):
    ChannelManager().get_or_create_channel("#test")

    msg = IRCMessage("PART", ["#test"])
    await command_handler.handle(registered_session, msg)

    registered_session.send_error.assert_called_with("442", "#test", ANY)

@pytest.mark.asyncio
async def test_privmsg_broadcast_to_channel_members(command_handler, registered_session):
    channel_name = "#test"
    channel = command_handler.channel_manager.get_or_create_channel(channel_name)

    channel.add_user(registered_session)

    hubert_session = MagicMock()
    hubert_session.nickname = "Hubert"
    hubert_session.send_reply = AsyncMock()
    channel.add_user(hubert_session)

    msg = IRCMessage("PRIVMSG", [channel_name, "Hello!"])
    await command_handler.handle(registered_session, msg)

    hubert_session.send_reply.assert_called_with(":Michal PRIVMSG #test :Hello!")
    registered_session.send_reply.assert_not_called()

@pytest.mark.asyncio
async def test_join_lists_all_current_members(command_handler, registered_session):
    channel_name = "#PSI"
    channel = command_handler.channel_manager.get_or_create_channel(channel_name)

    hubert = MagicMock()
    hubert.nickname = "Hubert"
    hubert.send_reply = AsyncMock()
    channel.add_user(hubert)

    msg = IRCMessage("JOIN", [channel_name])
    await command_handler.handle(registered_session, msg)

    called_args = [call.args for call in registered_session.send_reply.call_args_list]

    names_list_call = next(args for args in called_args if args[0] == "353")
    nicks_string = names_list_call[-1]

    assert "Michal" in nicks_string
    assert "Hubert" in nicks_string

@pytest.mark.asyncio
async def test_not_enough_parameters_error(command_handler, registered_session):
    msg = IRCMessage("JOIN", [])
    await command_handler.handle(registered_session, msg)

    registered_session.send_error.assert_called_with("461", "JOIN", ANY)
