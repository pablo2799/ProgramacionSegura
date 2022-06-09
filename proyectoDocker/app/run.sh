#!/bin/bash

sleep 10

python3 -u manage.py makemigrations
python3 -u manage.py migrate

gunicorn --bind :8000 sistemaevaluacion.wsgi:application --reload