import pytest
from IRCClient import IRCClient

from src.channel_manager import ChannelManager
from src.user_manager import UserManager


@pytest.fixture(autouse=True)
def reset_state() -> None:
    UserManager().users.clear()
    ChannelManager().channels.clear()


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
