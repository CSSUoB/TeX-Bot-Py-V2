FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-group dev --group deploy

COPY LICENSE /app/
COPY config.py main.py messages.json /app/
COPY exceptions/ /app/exceptions/
COPY utils/ /app/utils/
COPY db/ /app/db/
COPY cogs/ /app/cogs/

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source=https://github.com/CSSUoB/TeX-Bot-Py-V2
LABEL org.opencontainers.image.licenses=Apache-2.0

COPY --from=builder --chown=app:app /app /app

ENV LANG=C.UTF-8 PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["python", "-m", "main"]
