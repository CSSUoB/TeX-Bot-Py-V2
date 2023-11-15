FROM python:3.11.3 as builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install poetry

WORKDIR /app

COPY poetry.lock pyproject.toml README.md ./

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --no-root --no-interaction

FROM python:3.11.3-slim as runtime

ENV LANG=C.UTF-8

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

WORKDIR /app

COPY . ./

ENTRYPOINT ["python", "-m", "main"]
