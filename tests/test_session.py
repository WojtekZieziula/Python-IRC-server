import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.session import ClientSession


@pytest.fixture
def server_name() -> str:
    return "pyirc.local"


@pytest.fixture
def mock_streams() -> tuple[AsyncMock, MagicMock]:
    reader = AsyncMock()
    writer = MagicMock()
    writer.drain = AsyncMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()
    return reader, writer


@pytest.mark.asyncio
async def test_session_init(
    mock_streams: tuple[AsyncMock, MagicMock], server_name: str
) -> None:
    mock_reader, mock_writer = mock_streams
    mock_writer.get_extra_info.return_value = ("192.168.1.12", 12345)

    session = ClientSession(mock_reader, mock_writer, server_name)

    assert session.host == "192.168.1.12"
    assert session.port == 12345

    assert session.nickname is None
    assert session.username is None
    assert session.realname is None
    assert session.is_registered is False

    assert session.password_attempt is None
    assert session.closed is False

    expected_logger_name = "Session(192.168.1.12:12345)"
    assert session.logger.name == expected_logger_name
    assert isinstance(session.logger, logging.Logger)

    assert session.reader == mock_reader
    assert session.writer == mock_writer


@pytest.mark.asyncio
async def test_session_init_unknown_address(
    mock_streams: tuple[AsyncMock, MagicMock], server_name: str
) -> None:
    mock_reader, mock_writer = mock_streams
    mock_writer.get_extra_info.return_value = None

    session = ClientSession(mock_reader, mock_writer, server_name)

    assert session.host == "unknown"
    assert session.port == 0
    assert session.logger.name == "Session(unknown:0)"


@pytest.mark.asyncio
async def tests_session_send_reply_success(
    mock_streams: tuple[AsyncMock, MagicMock], server_name: str
) -> None:
    mock_reader, mock_writer = mock_streams
    mock_writer.get_extra_info.return_value = ("10.0.0.1", 6668)
    session = ClientSession(mock_reader, mock_writer, server_name)

    await session.send_reply("asdasdasdasd")

    mock_writer.write.assert_called_once_with(b"asdasdasdasd\r\n")
    mock_writer.drain.assert_awaited_once()


@pytest.mark.asyncio
async def test_session_send_reply_unicode(
    mock_streams: tuple[AsyncMock, MagicMock], server_name: str
) -> None:
    mock_reader, mock_writer = mock_streams
    session = ClientSession(mock_reader, mock_writer, server_name)

    await session.send_reply("Zażółć gęślą jaźń")

    expected_bytes = "Zażółć gęślą jaźń\r\n".encode("utf-8")
    mock_writer.write.assert_called_once_with(expected_bytes)


@pytest.mark.asyncio
async def test_session_prevents_sending_on_closed_connection(
    mock_streams: tuple[AsyncMock, MagicMock], server_name: str
) -> None:
    reader, writer = mock_streams
    session = ClientSession(reader, writer, server_name)

    await session.quit()
    writer.write.reset_mock()

    await session.send_reply("SHOULD NOT SEND")

    writer.write.assert_not_called()


@pytest.mark.asyncio
async def test_session_send_reply_network_error(
    mock_streams: tuple[AsyncMock, MagicMock],
    server_name: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mock_reader, mock_writer = mock_streams
    session = ClientSession(mock_reader, mock_writer, server_name)

    error_msg = "Lost Connection"
    mock_writer.write.side_effect = ConnectionResetError(error_msg)

    await session.send_reply("PING :test")

    assert len(caplog.records) > 0

    error_logs = [r for r in caplog.records if r.levelname == "ERROR"]
    assert len(error_logs) == 1

    target_log = error_logs[0]

    assert "Send error" in target_log.message
    assert error_msg in target_log.message
    assert target_log.name.startswith("Session")


@pytest.mark.asyncio
async def test_session_send_error_format(
    mock_streams: tuple[AsyncMock, MagicMock], server_name: str
) -> None:
    mock_reader, mock_writer = mock_streams
    mock_writer.get_extra_info.return_value = ("127.0.0.1", 6667)
    session = ClientSession(mock_reader, mock_writer, server_name)
    session.nickname = "Wojtek"

    await session.send_error("421", "JOINN", ":Unknown command")

    expected_msg = f":{server_name} 421 Wojtek JOINN :Unknown command\r\n".encode()
    mock_writer.write.assert_called_with(expected_msg)


@pytest.mark.asyncio
async def test_session_quit_cleans_up(
    mock_streams: tuple[AsyncMock, MagicMock], server_name: str
) -> None:
    mock_reader, mock_writer = mock_streams
    session = ClientSession(mock_reader, mock_writer, server_name)

    assert session.closed is False
    await session.quit()
    assert session.closed is True

    mock_writer.close.assert_called_once()
    mock_writer.wait_closed.assert_awaited_once()


@pytest.mark.asyncio
async def test_session_quit_idempotency(
    mock_streams: tuple[AsyncMock, MagicMock], server_name: str
) -> None:
    mock_reader, mock_writer = mock_streams
    session = ClientSession(mock_reader, mock_writer, server_name)

    await session.quit()
    await session.quit()

    assert mock_writer.close.call_count == 1


@pytest.mark.asyncio
async def test_session_quit_handles_exception(
    mock_streams: tuple[AsyncMock, MagicMock], server_name: str
) -> None:
    mock_reader, mock_writer = mock_streams
    session = ClientSession(mock_reader, mock_writer, server_name)

    mock_writer.wait_closed.side_effect = ConnectionError("Socket already closed")

    await session.quit()

    assert session.closed is True
    mock_writer.close.assert_called_once()
