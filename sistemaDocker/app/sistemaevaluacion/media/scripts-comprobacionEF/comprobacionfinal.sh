#!/bin/bash
let archivostxt=0
let archivospy=0
directorio="/tmp/pruebas/carpeta_ini/"
cd $directorio

for archivo in $(ls *txt); do
    archivostxt=$((archivostxt+1))
done
for archivo in $(ls *py); do
    archivospy=$((archivospy+1))
done
if [ $archivospy -eq 5 ]; then
    if [ $archivostxt -eq 0 ]; then
        echo "exito"
        exit 0
    else
        echo "fallo"
        exit 1
    fi
else
    echo "fallo"
    exit 1
fi