#!/bin/bash

[[ -f "$1" ]] || { echo "La entrada debe ser un archivo cifrado con variables de entorno"; exit 1; } #Verifica que el oparametro sea un archivo

for linea in $(ccdecrypt -c "$1"); do
	#echo "$linea"
	export "$linea"
done


python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py runserver
