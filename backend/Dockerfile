# ---- build stage ----
FROM python:3.14-slim-bookworm AS build

COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    # Keep the venv outside /app so the compose bind mount doesn't hide it
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_COMPILE_BYTECODE=1 uv sync --locked --no-install-project

COPY . .

# settings.py reads these at import time. collectstatic only copies files to
# STATIC_ROOT, so placeholders are enough; the real values come at runtime.
RUN DJANGO_SECRET_KEY=collectstatic \
    POSTGRES_DB=x POSTGRES_USER=x POSTGRES_PASSWORD=x POSTGRES_HOST=x POSTGRES_PORT=5432 \
    REDIS_URL=redis://x:6379/0 \
    AWS_ACCESS_KEY_ID=x AWS_SECRET_ACCESS_KEY=x AWS_STORAGE_BUCKET_NAME=x \
    AWS_S3_REGION_NAME=x AWS_S3_ENDPOINT_URL=http://x \
    python src/manage.py collectstatic --noinput

COPY --chmod=755 entrypoint.sh /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "src/manage.py", "runserver", "0.0.0.0:8000"]

# ---- hosting stage ----
FROM python:3.14-slim-bookworm AS hosting

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY --from=build /opt/venv /opt/venv
COPY --from=build /app /app

EXPOSE 8000

COPY --chmod=755 entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "--chdir", "src", "--bind", "0.0.0.0:8000", "saiddit.wsgi:application"]
