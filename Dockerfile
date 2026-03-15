# 1. Asosiy til va versiya (Python 3.11 masalan)
FROM python:3.11-slim

# 2. Konteyner ichidagi ishchi papka nomi
WORKDIR /app

# 3. Muhit o'zgaruvchilari (Python xatolarini tezroq ko'rsatishi uchun)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. Kutubxonalar ro'yxatini konteynerga nusxalash
COPY requirements.txt .

# 5. Kutubxonalarni o'rnatish
RUN pip install --no-cache-dir -r requirements.txt

# 6. Loyihaning qolgan barcha fayllarini nusxalash
COPY . .

# 7. Loyihani ishga tushirish (masalan Django bo'lsa)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]