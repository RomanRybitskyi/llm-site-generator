# Використовуємо офіційний Python образ
FROM python:3.11-slim

# Встановлюємо робочу директорію
WORKDIR /app

# Встановлюємо системні залежності для PIL/Pillow
RUN apt-get update && apt-get install -y \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо файл залежностей
COPY requirements.txt .

# Встановлюємо Python залежності
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код додатку
COPY . .

# Створюємо директорію для згенерованих сайтів
RUN mkdir -p /app/sites

# Відкриваємо порт для FastAPI
EXPOSE 8000

# Встановлюємо змінні середовища
ENV PYTHONUNBUFFERED=1
ENV SITES_DIR=/app/sites

# Команда для запуску додатку
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]