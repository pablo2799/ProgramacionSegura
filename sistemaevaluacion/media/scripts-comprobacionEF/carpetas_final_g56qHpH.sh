#!/bin/bash

if [ -d '/tmp/pruebas/carpeta_ini/prueba1' ]; then
   if [ -d '/tmp/pruebas/carpeta_ini/prueba2' ]; then
       exit 0
    else
       exit 1
    fi
else
   exit 1
fi