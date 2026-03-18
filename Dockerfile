FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p static staticfiles

RUN python manage.py collectstatic --noinput

# Portni qidirishda xatolik bo'lmasligi uchun va xatolarni ko'rish uchun:
CMD gunicorn Ecolife.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 2 --threads 4 --log-level debug