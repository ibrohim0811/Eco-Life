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

CMD ["sh", "-c", "export PYTHONPATH=$PYTHONPATH:. && python bot/main.py & celery -A Ecolife worker -l info -P solo --logfile=celery_worker.log & python manage.py makemigrations accounts && python manage.py migrate --noinput && gunicorn Ecolife.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]