FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project

ENV PATH="/app/.venv/bin:$PATH"

COPY src/ ./src/

CMD ["uv", "run", "python", "src/main.py"]