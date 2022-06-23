#!/bin/bash

sleep 10
su -c 'python3 -u manage.py makemigrations' usuario1
su -c 'python3 -u manage.py migrate' usuario1
su -c 'python3 -u /home/limitado/servidor.py' limitado &
su -c 'gunicorn --bind :8000 sistemaevaluacion.wsgi:application --reload' usuario1