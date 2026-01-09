import logging

from src.channel_manager import ChannelManager
from src.config import ServerConfig
from src.protocol import IRCMessage
from src.session import ClientSession
from src.user_manager import UserManager


class CommandHandler:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.user_manager = UserManager()
        self.channel_manager = ChannelManager()

    async def handle(self, session: ClientSession, msg: IRCMessage) -> None:
        command = msg.command
        handlers = {
            "PASS": self.handle_pass,
            "NICK": self.handle_nick,
            "USER": self.handle_user,
            "QUIT": self.handle_quit,
            "JOIN": self.handle_join,
            "PRIVMSG": self.handle_privmsg,
            "PART": self.handle_part,
        }

        handler = handlers.get(command)
        if handler:
            await handler(session, msg)
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

    async def handle_join(self, session: ClientSession, msg: IRCMessage) -> None:
        if not session.is_registered:
            await session.send_error("451", ":You have not registered")
            return

        if not msg.params:
            await session.send_error("461", "JOIN", ":Not enough parameters")
            return

        # This if is for type narrowing only (due to mypy errors)
        if session.nickname is None or session.username is None:
            return

        channel_name = msg.params[0]

        try:
            channel = self.channel_manager.get_or_create_channel(channel_name)
            channel.add_user(session)

            join_msg = (
                f":{session.nickname}!{session.username}@{session.host} "
                f"JOIN {channel.name}"
            )
            await channel.broadcast(join_msg)

            nicks = " ".join([m.nickname for m in channel.members if m.nickname])

            await session.send_reply(
                "353", session.nickname, "=", channel.name, f":{nicks}"
            )
            await session.send_reply(
                "366", session.nickname, channel.name, ":End of /NAMES list"
            )

        except ValueError:
            await session.send_error("403", channel_name, ":No such channel")

    async def handle_part(self, session: ClientSession, msg: IRCMessage) -> None:
        if not msg.params:
            await session.send_error("461", "PART", ":Not enough parameters")
            return

        channel_name = msg.params[0]
        channel = self.channel_manager.get_channel(channel_name)

        if not channel:
            await session.send_error("403", channel_name, ":No such channel")
            return

        if session not in channel.members:
            await session.send_error("442", channel_name, ":You're not on that channel")
            return

        part_msg = f":{session.nickname} PART {channel.name}"
        await channel.broadcast(part_msg)
        channel.remove_user(session)

    async def handle_privmsg(self, session: ClientSession, msg: IRCMessage) -> None:
        if len(msg.params) < 2:
            await session.send_error("411", ":No recipient given (PRIVMSG)")
            return

        target = msg.params[0]
        content = msg.params[1]

        if target.startswith("#"):
            channel = self.channel_manager.get_channel(target)
            if channel:
                if session not in channel.members:
                    await session.send_error("404", target, ":Cannot send to channel")
                    return
                await channel.broadcast(
                    f":{session.nickname} PRIVMSG {target} :{content}",
                    skip_user=session,
                )
            else:
                await session.send_error("401", target, ":No such nick/channel")
        else:
            target_user = self.user_manager.get_session(target)
            if target_user:
                await target_user.send_reply(
                    f":{session.nickname} PRIVMSG {target} :{content}"
                )
            else:
                await session.send_error("401", target, ":No such nick/channel")

    async def handle_quit(self, session: ClientSession, msg: IRCMessage) -> None:
        reason = msg.params[0] if msg.params else "Client Quit"
        self.logger.info(f"User {session.nickname} quitting: {reason}")
        await session.quit()

    async def check_registration(self, session: ClientSession) -> None:
        if not (session.nickname and session.username and not session.is_registered):
            return

        if self.config.password:
            if session.password_attempt != self.config.password:
                self.logger.warning(f"Bad password from {session.host}")
                await session.send_error("464", ":Password incorrect")
                await session.quit()
                return

        try:
            self.user_manager.add_user(session.nickname, session)

            session.is_registered = True

            await session.send_reply(
                "001",
                session.nickname,
                f":Welcome to the IRC Server {session.nickname}!"
                f"{session.username}@{session.host}",
            )
            self.logger.info(f"Registered: {session.nickname}")

        except ValueError:
            self.logger.warning(f"Registration failed: Nick {session.nickname} taken")
            await session.send_error(
                "433", "*", session.nickname, ":Nickname is already in use"
            )

            session.nickname = None
