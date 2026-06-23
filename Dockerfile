FROM python:3.13-slim

RUN pip install uv

WORKDIR /app

COPY app/pyproject.toml app/uv.lock ./
RUN uv sync --frozen

COPY app/ .

RUN uv run manage.py collectstatic --noinput && \
    chmod -R a+rX /app

ENV PYTHONUNBUFFERED=1
EXPOSE 8055

RUN groupadd -r django && \
    useradd -m -r -g django django && \
    mkdir -p /home/django/.cache /app/logs /app/media /app/staticfiles && \
    chown -R django:django /home/django/.cache /app/logs /app/media
USER django

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD uv run python -c "import urllib.request; urllib.request.urlopen('http://localhost:8055/api/plans/')" || exit 1

CMD uv run manage.py migrate --noinput && uv run gunicorn config.wsgi:application --bind 0.0.0.0:8055
