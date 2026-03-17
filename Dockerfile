FROM python:3.11-slim

WORKDIR /app

# Muhit o'zgaruvchilari
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Docker build paytida collectstatic bazaga ulanishga harakat qilmasligi uchun
ENV DJANGO_COLLECTSTATIC=1 

# Kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Loyihani nusxalash
COPY . .

# Static fayllarni build jarayonida yig'ish (Siz xohlagandek)
RUN python manage.py collectstatic --noinput

# Gunicorn orqali ishga tushirish (Railway PORT o'zgaruvchisini o'zi beradi)
CMD ["sh", "-c", "python manage.py migrate --noinput; python manage.py collectstatic --noinput; gunicorn Ecolife.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]