import asyncio

import pytest
from ircclient import IRCClient


@pytest.mark.asyncio
async def test_invalid_data_and_long_message(running_server: int) -> None:
    port = running_server
    client = IRCClient(port, "Ziutek")
    try:
        await client.connect()
        await client.send("\x00\xff\xfeINVALID\r\n")
        long_message = "PRIVMSG #general :" + "A" * 10000
        await client.send(long_message)
        await client.send("NICK Ziutek2")
        response = await client.wait_for_message("NICK")
        assert "NICK" in response
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_abrupt_client_disconnect(running_server: int) -> None:
    port = running_server
    client = IRCClient(port, "Ziutek")
    try:
        await client.connect()
        if client.writer:
            client.writer.transport.abort()
        await asyncio.sleep(0.1)
    finally:
        await client.close()
