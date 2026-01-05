from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ServerConfig:
    name: str
    host: str
    port: int
    password: str


@dataclass
class AppConfig:
    server: ServerConfig
    log_level: str


def load_config(config_path: str) -> AppConfig:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Couln't find config file: {config_path}")

    with open(path, "r") as f:
        try:
            data: dict[str, Any] = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing file: {e}")

    try:
        server_data = data["server"]
        return AppConfig(
            server=ServerConfig(
                name=server_data["name"],
                host=server_data["host"],
                port=server_data["port"],
                password=server_data["password"],
            ),
            log_level=data["logging"]["level"],
        )
    except KeyError as e:
        raise ValueError(f"Required config option is missing: {e}")
