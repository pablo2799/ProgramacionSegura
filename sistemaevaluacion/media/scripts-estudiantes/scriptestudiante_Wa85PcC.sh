#!/bin/bash
directorio="$1"

if [ -d "$directorio" ]
then
    cd "$directorio"
    rm *.txt
fi
#cd $directorio
#rm *.txt