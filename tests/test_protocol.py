import pytest
from src.protocol import IRCParser, IRCMessage

def test_parse_simple_command():
    msg = IRCParser.parse("PING")
    assert msg.command == "PING"
    assert msg.params == []
    assert msg.prefix is None

def test_parse_with_params():
    msg = IRCParser.parse("NICK Wojtek")
    assert msg.command == "NICK"
    assert msg.params == ["Wojtek"]

def test_parse_with_prefix():
    msg = IRCParser.parse(":server PRIVMSG #channel :Hello!")
    assert msg.prefix == "server"
    assert msg.command == "PRIVMSG"
    assert msg.params == ["#channel", "Hello!"]

def test_parse_trailing_with_spaces():
    msg = IRCParser.parse("PRIVMSG #test :Long message with spaces")
    assert msg.command == "PRIVMSG"
    assert msg.params == ["#test", "Long message with spaces"]

def test_parse_case_insensitivity():
    msg = IRCParser.parse("nick wojtek")
    assert msg.command == "NICK"

def test_parse_empty_raises_error():
    with pytest.raises(ValueError, match="Empty message"):
        IRCParser.parse("   ")

def test_parse_complex_message():
    raw = ":Wojtek!~wojtek@localhost KICK #polska Hubert :Michal Pedziwiatr!"
    msg = IRCParser.parse(raw)
    assert msg.prefix == "Wojtek!~wojtek@localhost"
    assert msg.command == "KICK"
    assert msg.params == ["#polska", "Hubert", "Michal Pedziwiatr!"]

def test_parse_extra_spaces():
    msg = IRCParser.parse("PRIVMSG    #channel   :message")
    assert msg.command == "PRIVMSG"
    assert msg.params == ["#channel", "message"]

def test_parse_empty_trailing():
    msg = IRCParser.parse("QUIT :")
    assert msg.command == "QUIT"
    assert msg.params == [""]

def test_parse_malformed_prefix_only():
    with pytest.raises(Exception):
        IRCParser.parse(":tylko_prefix")
