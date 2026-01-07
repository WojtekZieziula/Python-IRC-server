import asyncio
import logging


class ClientSession:
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        server_name: str,
    ):
        self.reader = reader
        self.writer = writer
        self.server_name = server_name

        addr = writer.get_extra_info("peername")
        self.host = addr[0] if addr else "unknown"
        self.port = addr[1] if addr else 0

        self.nickname: str | None = None
        self.username: str | None = None
        self.realname: str | None = None
        self.is_registered: bool = False

        self.password_attempt: str | None = None
        self.closed: bool = False

        self.logger = logging.getLogger(f"Session({self.host}:{self.port})")

    async def send_reply(self, *args: str) -> None:
        if self.closed:
            self.logger.debug(
                "Attempted to send message to a closed session. Ignoring."
            )
            return

        response = " ".join(args) + "\r\n"
        try:
            self.writer.write(response.encode("utf-8"))
            await self.writer.drain()
            self.logger.debug(f"Sent: {response.strip()}")
        except Exception as e:
            self.logger.error(f"Send error: {e}")

    async def send_error(self, code: str, *args: str) -> None:
        target_nick = self.nickname if self.nickname else "*"
        server_prefix = f":{self.server_name}"
        params_str = " ".join(args)
        full_msg = f"{server_prefix} {code} {target_nick} {params_str}".strip()

        await self.send_reply(full_msg)

    async def quit(self) -> None:
        if self.closed:
            return

        self.closed = True

        self.logger.info("Closing connection")
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
            pass
