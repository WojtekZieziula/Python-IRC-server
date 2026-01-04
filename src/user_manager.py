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
        if self.is_nick_taken(nickname):
            raise ValueError(f"Nickname '{nickname.lower()}' is already in use!")

        self.users[nickname.lower()] = session
        self.logger.info(f"User added: {nickname.lower()}")

    def get_session(self, nickname: str) -> "ClientSession | None":
        return self.users.get(nickname.lower())

    def remove_user(self, nickname: str) -> None:
        low_nickname = nickname.lower()
        if low_nickname in self.users:
            del self.users[low_nickname]
            self.logger.info(f"User removed: {nickname}")

    def is_nick_taken(self, nickname: str) -> bool:
        return nickname.lower() in self.users

    def change_nick(self, old_nick: str, new_nick: str) -> None:
        session = self.get_session(old_nick)
        if session:
            self.remove_user(old_nick)
            self.add_user(new_nick, session)
            self.logger.info(f"Nick changed: {old_nick.lower()} -> {new_nick.lower()}")
