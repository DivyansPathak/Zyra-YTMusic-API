# Use a stable Python base
FROM python:3.11-slim

# Prevent Python writing .pyc files and enable buffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# system deps for some libs (optional - adjust if you need build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# copy requirements first for Docker layer caching
COPY requirements.txt .

RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# copy app
COPY . /app

EXPOSE 80

# Uvicorn for async FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers", "--ws", "websockets"]
