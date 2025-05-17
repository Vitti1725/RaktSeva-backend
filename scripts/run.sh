#!/bin/sh
set -e

echo "Waiting for database..."
python manage.py wait_for_db

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

uwsgi \
  --chdir /app \
  --socket :9000 \
  --workers 4 \
  --master \
  --enable-threads \
  --module raktseva.wsgi:application
