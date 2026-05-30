FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

EXPOSE ${PORT:-8000}

# Shell form so $PORT is expanded at runtime (Railway injects PORT).
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
