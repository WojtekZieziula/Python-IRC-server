# PyIRC Server

A from-scratch implementation of an IRC server in Python, built with asynchronous I/O and zero runtime dependencies beyond the standard library. Compatible with real IRC clients (HexChat, WeeChat, irssi) - just point them at port 6667.

---

## Team

| Name | Contributions |
|---|---|
| **Hubert Potera** | Project setup (pyproject.toml, Makefile, Docker), async TCP networking layer, signal handling, logging |
| **Kacper Siemionek** | IRC message parser, registration commands (PASS, NICK, USER, QUIT), UserManager |
| **Wojciech Zieziula** | Channel logic (JOIN, PART, KICK, PRIVMSG), ChannelManager, integration tests |

---

## Features

- **Full registration flow** - PASS, NICK, USER with nick collision detection
- **Private messaging** - PRIVMSG between users
- **Channel management** - JOIN, PART, multi-channel support
- **Moderation** - KICK with operator privilege enforcement
- **RFC 1459 numeric replies** - RPL_WELCOME, ERR_NICKNAMEINUSE, ERR_CHANOPRIVSNEEDED, and more
- **Graceful disconnection** - detects dropped clients, releases resources
- **Configurable** via YAML (host, port, server name, password, log level)

---

## Tech Stack

| Area | Choice |
|---|---|
| Language | Python 3.11+ |
| Concurrency | `asyncio` (event loop, no threads) |
| Runtime deps | Standard library + PyYAML |
| Type checking | `mypy` (strict mode) |
| Linting/formatting | `ruff` |
| Testing | `pytest` + `pytest-asyncio` + `pytest-cov` |
| Packaging | `uv` + `hatchling` |
| Containerization | Docker + docker-compose |

---

## Quick Start

**Prerequisites:** Python 3.11+, [`uv`](https://github.com/astral-sh/uv)

```bash
git clone https://github.com/WojtekZieziula/Python-IRC-server.git
cd Python-IRC-server

# Install dependencies
make install

# Run the server (default: port 6667)
make run
```

Connect with any IRC client or test manually:
```bash
telnet localhost 6667
```

Then type:
```
PASS password
NICK alice
USER alice 0 * :Alice
```

### Docker

```bash
make docker-build
make docker-up
```

The server is exposed on port **6667**.

---

## Configuration

Edit `config.yaml` before starting:

```yaml
server:
  name: "pyirc.server"
  host: "0.0.0.0"
  port: 6667
  password: "password"

logging:
  level: "INFO"
```

---

## Architecture

The server is built around an asyncio event loop. Each client connection gets its own `ClientSession` coroutine - no threads, no blocking.

```
IRC Client
    │
    ▼
 Server ──── creates ────► ClientSession
                                │
                                ├──► Parser          (raw bytes → Command objects)
                                │
                                └──► CommandHandler  (business logic)
                                          │
                                          ├──► UserManager    (nick → session map)
                                          └──► ChannelManager (channel state)
```

**Modules:**

| Module | Responsibility |
|---|---|
| `server.py` | Accepts TCP connections, spawns client sessions |
| `session.py` | Per-client read/write loop |
| `protocol.py` | RFC 1459 message parser |
| `commands.py` | Command handlers (NICK, JOIN, PRIVMSG, …) |
| `user_manager.py` | Singleton: active nick → session registry |
| `channel_manager.py` | Singleton: channel membership and operator state |
| `config.py` | YAML config loader |

---

## Testing

```bash
make test
```

Runs the full suite with coverage report.

**Test strategy:**
- **Unit tests** - parser correctness, UserManager/ChannelManager state in isolation
- **Integration tests** - full server spun up via `pytest-asyncio` fixture, real TCP clients simulate registration, messaging, kicks, and abrupt disconnects
- **Robustness tests** - malformed input, oversized lines, sudden disconnections

---

## Makefile Reference

| Command | Description |
|---|---|
| `make install` | Install all dependencies |
| `make run` | Start the server |
| `make test` | Run tests with coverage |
| `make lint` | Run ruff + mypy |
| `make format` | Auto-format with ruff |
| `make docker-build` | Build Docker image |
| `make docker-up` | Start server in container |
| `make clean` | Remove build artifacts and caches |
