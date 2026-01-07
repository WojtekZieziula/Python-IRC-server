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

    @staticmethod
    def _irc_lower(nick: str) -> str:
        return nick.lower().replace("[", "{").replace("]", "}").replace("\\", "|")

    def add_user(self, nickname: str, session: "ClientSession") -> None:
        low_nickname = self._irc_lower(nickname)

        if self.is_nick_taken(nickname):
            raise ValueError(f"Nickname '{low_nickname}' is already in use!")

        self.users[low_nickname] = session
        self.logger.info(f"User added: {low_nickname}")

    def get_session(self, nickname: str) -> "ClientSession | None":
        return self.users.get(self._irc_lower(nickname))

    def remove_user(self, nickname: str) -> None:
        low_nickname = self._irc_lower(nickname)
        if low_nickname in self.users:
            del self.users[low_nickname]
            self.logger.info(f"User removed: {nickname}")

    def is_nick_taken(self, nickname: str) -> bool:
        return self._irc_lower(nickname) in self.users

    def change_nick(self, old_nick: str, new_nick: str) -> None:
        session = self.get_session(old_nick)
        if session:
            low_new = self._irc_lower(new_nick)
            if low_new in self.users and low_new != self._irc_lower(old_nick):
                raise ValueError(f"Nickname '{low_new}' is already in use!")

            self.remove_user(old_nick)
            self.add_user(new_nick, session)
            self.logger.info(f"Nick changed: {self._irc_lower(old_nick)} -> {low_new}")
