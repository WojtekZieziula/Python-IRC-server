from dataclasses import dataclass, field


@dataclass
class IRCMessage:
    command: str
    params: list[str] = field(default_factory=list)
    prefix: str | None = None


class IRCParser:
    @staticmethod
    def parse(data: str) -> IRCMessage:
        data = data.strip()
        if not data:
            raise ValueError("Empty message")

        prefix = None
        if data.startswith(":"):
            prefix, data = data[1:].split(" ", 1)

        if " :" in data:
            part1, part2 = data.split(" :", 1)
            args = part1.split()
            args.append(part2)
        else:
            args = data.split()

        command = args.pop(0).upper()
        return IRCMessage(command=command, params=args, prefix=prefix)
