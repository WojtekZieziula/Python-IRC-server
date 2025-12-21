import logging

from src.session import ClientSession


class UserManager:
    _instance = None

    def __new__(cls) -> "UserManager":
        if cls._instance is None:
            cls._instance = super(UserManager, cls).__new__(cls)
            cls._instance.users = {}
            cls._instance.logger = logging.getLogger(cls.__name__)
        return cls._instance

    def __init__(self) -> None:
        self.users: dict[str, "ClientSession"]
        self.logger: logging.Logger

    def add_user(self, nickname: str, session: "ClientSession") -> None:
        self.users[nickname] = session
        self.logger.info(f"User added: {nickname}")

    def remove_user(self, nickname: str) -> None:
        if nickname in self.users:
            del self.users[nickname]
            self.logger.info(f"User removed: {nickname}")

    def is_nick_taken(self, nickname: str) -> bool:
        return nickname in self.users

    def change_nick(self, old_nick: str, new_nick: str) -> None:
        session = self.users[old_nick]
        del self.users[old_nick]
        self.users[new_nick] = session
        self.logger.info(f"Nick changed: {old_nick} -> {new_nick}")
