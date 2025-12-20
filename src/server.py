import asyncio
import logging

from src.config import ServerConfig


class Server:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.server: asyncio.Server | None = None
        self.logger = logging.getLogger(self.__class__.__name__)

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
        addr = writer.get_extra_info("peername")
        self.logger.info(f"Connected from {addr}")

        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break

                message = data.decode().strip()
                self.logger.info(f"[{addr}] {message}")

                # Echo
                writer.write(data)
                await writer.drain()
        except Exception as e:
            self.logger.error(f"Client error {addr}: {e}")
        finally:
            self.logger.info(f"Disconnected {addr}")
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
