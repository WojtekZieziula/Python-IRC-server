import logging

from src.config import ServerConfig
from src.protocol import IRCMessage
from src.session import ClientSession
from src.user_manager import UserManager


class CommandHandler:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.user_manager = UserManager()

    async def handle(self, session: ClientSession, msg: IRCMessage) -> None:
        command = msg.command

        if command == "PASS":
            await self.handle_pass(session, msg)
        elif command == "NICK":
            await self.handle_nick(session, msg)
        elif command == "USER":
            await self.handle_user(session, msg)
        elif command == "QUIT":
            await self.handle_quit(session, msg)
        else:
            self.logger.debug(f"Unknown command: {command}")
            await session.send_error("421", command, ":Unknown command")

    async def handle_pass(self, session: ClientSession, msg: IRCMessage) -> None:
        if session.is_registered:
            await session.send_error("462", ":You may not reregister")
            return

        if not msg.params:
            await session.send_error("461", "PASS", ":Not enough parameters")
            return

        session.password_attempt = msg.params[0]
        self.logger.debug(f"Password attempt received from {session.host}")

    async def handle_nick(self, session: ClientSession, msg: IRCMessage) -> None:
        if not msg.params:
            await session.send_error("431", ":No nickname given")
            return

        new_nick = msg.params[0]

        if len(new_nick) > 9 or not new_nick.isalnum():
            await session.send_error("432", new_nick, ":Erroneus nickname")
            return

        if self.user_manager.is_nick_taken(new_nick):
            await session.send_error(
                "433", "*", new_nick, ":Nickname is already in use"
            )
            return

        old_nick = session.nickname
        session.nickname = new_nick

        if session.is_registered:
            if old_nick:
                self.user_manager.change_nick(old_nick, new_nick)
            await session.send_reply(f":{old_nick}", "NICK", new_nick)
        else:
            await self.check_registration(session)

    async def handle_user(self, session: ClientSession, msg: IRCMessage) -> None:
        if session.is_registered:
            await session.send_error("462", ":You may not reregister")
            return

        if len(msg.params) < 4:
            await session.send_error("461", "USER", ":Not enough parameters")
            return

        session.username = msg.params[0]
        session.realname = msg.params[3]
        await self.check_registration(session)

    async def handle_quit(self, session: ClientSession, msg: IRCMessage) -> None:
        reason = msg.params[0] if msg.params else "Client Quit"
        self.logger.info(f"User {session.nickname} quitting: {reason}")
        await session.quit()

    async def check_registration(self, session: ClientSession) -> None:
        if session.nickname and session.username and not session.is_registered:
            if self.config.password:
                if session.password_attempt != self.config.password:
                    self.logger.warning(f"Bad password from {session.host}")
                    await session.send_error("464", ":Password incorrect")
                    await session.quit()
                    return

            session.is_registered = True
            self.user_manager.add_user(session.nickname, session)

            await session.send_reply(
                "001",
                session.nickname,
                f":Welcome to the IRC Server {session.nickname}!"
                f"{session.username}@{session.host}",
            )
            self.logger.info(f"Registered: {session.nickname}")
