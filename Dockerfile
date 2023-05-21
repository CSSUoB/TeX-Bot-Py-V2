FROM python:3.11.1-alpine as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random

WORKDIR /code

FROM base as builder

ENV PIP_NO_CACHE_DIR=on \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

RUN pip install "poetry"

COPY poetry.lock pyproject.toml README.md ./

COPY . .

RUN . /venv/bin/activate && \
    poetry config virtualenvs.in-project true && \
    poetry install --only=main --no-root && \
    poetry build

FROM base as final

COPY --from=builder /code/.venv ./.venv
COPY --from=builder /code/dist .
COPY docker-entrypoint.sh .

RUN ./.venv/bin/pip install *.whl
CMD ["./main.py"]
