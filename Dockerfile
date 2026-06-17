FROM python:3.13-slim

RUN pip install uv

WORKDIR /app

COPY app/pyproject.toml app/uv.lock ./
RUN uv sync --frozen

COPY app/ .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
