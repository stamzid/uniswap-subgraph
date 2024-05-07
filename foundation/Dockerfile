# Base Image
FROM python:3.11-slim as base
ENV PYTHONUNBUFFERED=true
WORKDIR /foundation

# Builder Stage
FROM base as builder
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN python -c 'from urllib.request import urlopen; print(urlopen("https://install.python-poetry.org").read().decode())' | python -
COPY ./pyproject.toml ./pyproject.toml
RUN poetry install --no-interaction --no-ansi -vvv

# Runtime Stage
FROM base as runtime
COPY --from=builder /foundation/.venv /foundation/.venv
ENV PATH="/foundation/.venv/bin:$PATH"
ENV GRPC_DNS_RESOLVER=native
COPY ./ /foundation

# Use entrypoint.sh
COPY ./entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["python", "-m", "foundation.app"]
EXPOSE 8000

