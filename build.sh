#!/usr/bin/env bash

set -o errexit

pip install -r requirements.txt
npm --prefix theme/static_src install
python manage.py tailwind build
python manage.py collectstatic --no-input
python manage.py migrate --noinput
