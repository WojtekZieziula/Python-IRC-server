import argparse
import asyncio
import logging
import signal
import sys

from src.config import load_config
from src.server import Server


def setup_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


async def main() -> None:
    parser = argparse.ArgumentParser(description="PyIRC Server")
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the YAML config file",
    )
    args = parser.parse_args()

    try:
        cfg = load_config(args.config)
    except Exception as e:
        print(f"Couldn't load config file: {e}", file=sys.stderr)
        sys.exit(1)

    setup_logging(cfg.log_level)
    logging.info(f"Loaded config from: {args.config}")

    server_app = Server(cfg.server)

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        logging.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    server_task = asyncio.create_task(server_app.start())

    try:
        await stop_event.wait()
    finally:
        await server_app.stop()
        if not server_task.done():
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
