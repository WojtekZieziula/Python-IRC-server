FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-cache --no-install-project

COPY . .

RUN uv sync --frozen --no-cache

EXPOSE 6667

CMD ["uv", "run", "python", "-m", "src.main", "--config", "config.yaml"]