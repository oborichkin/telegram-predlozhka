FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /bot
COPY main.py uv.lock pyproject.toml .
ENTRYPOINT ["uv", "run", "python", "main.py"]