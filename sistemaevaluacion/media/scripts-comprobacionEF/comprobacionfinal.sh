#!/bin/bash
let archivostxt=0
directorio="$1"
cd $directorio
comprobacion(){
    for archivo in $(ls *txt); do
        archivostxt=$((archivostxt+1))
    done
    if [ $archivostxt -eq 0 ]
    then
        echo "exito"
        return 0
    else
        echo "fallo"
        return 1
    fi
}

comprobacion