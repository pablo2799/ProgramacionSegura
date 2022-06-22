#!/bin/bash

if [ $# -ne 2 ]; then
  echo El script no recibió 2 parámetros
  exit 1
fi

var1=$1
var2=$2

cd /tmp/pruebas/carpeta_ini

mkdir $var1
mkdir $var2