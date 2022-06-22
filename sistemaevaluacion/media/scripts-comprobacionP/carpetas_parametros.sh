#!/bin/bash

scripts_estudiante=$1

/bin/bash "$scripts_estudiante" 'prueba1'
var1=$?

/bin/bash "$scripts_estudiante" 'prueba1' 'prueba2' 'prueba3'
var2=$?


if [ "$var1" -eq 0 ]; then
  rm -r /tmp/carpeta_ini/prueba1
  exit 1
else
  if [ "$var2" -eq 0 ]; then
    rm -r /tmp/carpeta_ini/prueba1 | rm -r /tmp/carpeta_ini/prueba2 | rm -r /tmp/carpeta_ini/prueba3
    exit 1
    fi
fi

exit 0