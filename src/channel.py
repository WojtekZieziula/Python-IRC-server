from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.session import ClientSession


class Channel:
    def __init__(self, name: str) -> None:
        if not self.is_valid_name(name):
            raise ValueError(f"Invalid channel name: {name}")

        self.name: str = name
        # Hack for ordered set
        self.members: dict[ClientSession, None] = {}
        self.operators: set[ClientSession] = set()
        self.logger: logging.Logger = logging.getLogger(f"Channel:{name}")

    def add_user(self, session: ClientSession) -> None:
        if not self.members:
            self.operators.add(session)
            self.logger.info(f"User {session.nickname} became operator of {self.name}")

        self.members[session] = None
        self.logger.info(f"User {session.nickname} joined {self.name}")

    def remove_user(self, session: ClientSession) -> None:
        self.members.pop(session, None)
        self.operators.discard(session)
        self.logger.info(f"User {session.nickname} left {self.name}")

        if self.members and not self.operators:
            new_op = next(iter(self.members))

            self.operators.add(new_op)
            self.logger.info(
                f"User {new_op.nickname} (oldest member) automatically \
                became operator of {self.name}"
            )

    def is_operator(self, session: ClientSession) -> bool:
        return session in self.operators

    async def broadcast(
        self, message: str, skip_user: ClientSession | None = None
    ) -> None:
        for member in self.members:
            if member != skip_user:
                await member.send_reply(message)

    @staticmethod
    def is_valid_name(name: str) -> bool:
        if not name or len(name) > 200:
            return False

        if not name.startswith("#"):
            return False

        forbidden = {" ", ",", "\x07"}
        if any(char in forbidden for char in name):
            return False

        if "#" in name[1:]:
            return False

        return True
