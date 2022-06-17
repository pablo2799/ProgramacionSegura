#!/bin/bash
directorio="$1"
script(){
    if [ -d "$directorio" ]
    then
        cd "$directorio"
        rm *.txt
        echo "exito"
        return 0
    else
        echo "Se debe recibir un directorio"
        return 1
    fi
}
script