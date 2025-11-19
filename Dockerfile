# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and system deps
RUN apt-get update && apt-get install -y wget libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxss1 libx11-xcb1 libgbm1 libasound2 libxcomposite1 libxrandr2 libgtk-3-0 --no-install-recommends \
  && rm -rf /var/lib/apt/lists/*

# Install playwright browsers
RUN python -m playwright install --with-deps

COPY app ./app
COPY playwright.install.sh .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
