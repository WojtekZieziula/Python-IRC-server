from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.channel import Channel

if TYPE_CHECKING:
    from src.session import ClientSession


class ChannelManager:
    _instance: ChannelManager | None = None

    def __new__(cls) -> ChannelManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.channels = {}
            cls._instance.logger = logging.getLogger("ChannelManager")
        return cls._instance

    def __init__(self) -> None:
        self.channels: dict[str, Channel]
        self.logger: logging.Logger

    def _normalize_name(self, name: str) -> str:
        if not name.startswith("#"):
            name = "#" + name
        return name.lower()

    def channel_exists(self, name: str) -> bool:
        return self._normalize_name(name) in self.channels

    def get_channel(self, name: str) -> Channel | None:
        return self.channels.get(self._normalize_name(name))

    def create_channel(self, name: str) -> Channel:
        normalized = self._normalize_name(name)

        if not Channel.is_valid_name(normalized):
            self.logger.warning(
                f"Rejection: normalized name '{normalized}' is still invalid."
            )
            raise ValueError(f"Invalid channel name: {name}")

        if normalized in self.channels:
            raise ValueError(f"Channel {normalized} already exists!")

        display_name = name if name.startswith("#") else "#" + name

        new_channel = Channel(display_name)
        self.channels[normalized] = new_channel
        self.logger.info(f"Created new channel: {normalized}")
        return new_channel

    def get_or_create_channel(self, name: str) -> Channel:
        channel = self.get_channel(name)
        if channel:
            return channel
        return self.create_channel(name)

    def remove_user_from_all_channels(self, session: ClientSession) -> None:
        to_delete: list[str] = []

        for name, channel in self.channels.items():
            channel.remove_user(session)
            if not channel.members:
                to_delete.append(name)

        for name in to_delete:
            del self.channels[name]
            self.logger.info(f"Auto-deleted empty channel: {name}")
