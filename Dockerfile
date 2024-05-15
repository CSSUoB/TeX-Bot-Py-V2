FROM python:3.12 as builder

ENV PYTHONUNBUFFERED=true \
    PYTHONDONTWRITEBYTECODE=true \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_NO_INTERACTION=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    POETRY_VIRTUALENVS_OPTIONS_ALWAYS_COPY=true \
    POETRY_VIRTUALENVS_OPTIONS_NO_PIP=true \
    POETRY_HOME=/opt/poetry


RUN apt-get update && apt-get install --no-install-recommends -y curl build-essential
RUN python3 -m venv $POETRY_HOME
RUN $POETRY_HOME/bin/pip install poetry==1.8.3


WORKDIR /app

COPY poetry.lock pyproject.toml README.md ./

RUN --mount=type=cache,target=$POETRY_CACHE_DIR $POETRY_HOME/bin/poetry install --without dev --no-root --no-interaction

FROM python:3.12-slim as runtime

ENV LANG=C.UTF-8 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

WORKDIR /app

COPY LICENSE .en[v] config.py exceptions.py main.py messages.json ./
RUN chmod +x main.py

COPY cogs/ ./cogs/
COPY db/ ./db/
COPY utils/ ./utils/

ENTRYPOINT ["python", "-m", "main"]
