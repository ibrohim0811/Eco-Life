FROM python:3.11-slim

WORKDIR /app

# Muhit o'zgaruvchilari
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyihani nusxalash
COPY . .

# Serverni ishga tushirish
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]