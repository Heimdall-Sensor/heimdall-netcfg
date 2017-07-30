#!/bin/bash

echo "Running: python manage.py migrate"
python manage.py migrate
echo "Running: python manage.py createsuperuser"
python manage.py createsuperuser
echo "Running: python manage.py runserver"
python manage.py runserver
