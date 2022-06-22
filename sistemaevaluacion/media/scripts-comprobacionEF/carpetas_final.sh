#!/bin/bash

bandera=0


if [ -d '/tmp/carpeta_ini/prueba1' ]; then
   if [ -d '/tmp/carpeta_ini/prueba2' ]; then
       exit 0
    else
       bandera=bandera1;
    fi
else
   bandera=bandera1;
fi

if [ bandera != 0 ]; then
  exit 2
fi
