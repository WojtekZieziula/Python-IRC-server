import asyncio
import logging

from src.commands import CommandHandler
from src.config import ServerConfig
from src.protocol import IRCParser
from src.session import ClientSession
from src.user_manager import UserManager


class Server:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.server: asyncio.Server | None = None
        self.logger = logging.getLogger(self.__class__.__name__)

        self.command_handler = CommandHandler(self.config)

    async def start(self) -> None:
        self.server = await asyncio.start_server(
            self.handle_client, self.config.host, self.config.port
        )

        if self.server.sockets:
            addr = self.server.sockets[0].getsockname()
            self.logger.info(f"Server is listening at {addr}")

        async with self.server:
            await self.server.serve_forever()

    async def stop(self) -> None:
        if self.server:
            self.logger.info("Shutting down server...")
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("Server stopped.")

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        session = ClientSession(reader, writer)
        self.logger.info(f"Connected from {session.host}")

        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break

                decoded_data = data.decode("utf-8", errors="ignore")

                for line in decoded_data.split("\r\n"):
                    if not line.strip():
                        continue

                    try:
                        self.logger.debug(f"Received: {line}")
                        message = IRCParser.parse(line)
                        await self.command_handler.handle(session, message)
                    except ValueError:
                        pass
                    except Exception as e:
                        self.logger.error(f"Command processing error: {e}")

        except Exception as e:
            self.logger.error(f"Client error {session.host}: {e}")
        finally:
            self.logger.info(f"Disconnected {session.host}")
            if session.nickname:
                UserManager().remove_user(session.nickname)

            await session.quit()
