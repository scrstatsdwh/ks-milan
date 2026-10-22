#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py bootstrap_site
python manage.py create_test_user
python manage.py collectstatic --noinput

exec gunicorn ksmilan.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
