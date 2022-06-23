#!/bin/bash

mkdir /tmp/pruebas/carpeta_ini/
cd /tmp/pruebas/carpeta_ini/
for i in {0..9}
do
    touch "archivo$i.txt"
done
for i in {0..4}
do
    touch "archivo$i.py"
done