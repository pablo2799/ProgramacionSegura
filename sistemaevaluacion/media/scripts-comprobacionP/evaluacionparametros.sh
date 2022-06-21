#!/bin/bash
script_estudiante="$1"

./"$script_estudiante"
var1=$?
./"$script_estudiante" hola.txt adsf
var2=$?
./"$script_estudiante" tmpd
var3=$?

if [[ $var1 -eq 1 || $var2 -eq 1 || $var3 -eq 1 ]]; then
    echo "No pasó la prueba"
    exit 1
else
    echo "Pasó la prueba"
    exit 0
fi