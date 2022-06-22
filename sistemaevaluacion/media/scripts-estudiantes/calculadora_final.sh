#!/bin/bash

salida_esperada=$1
resuldado_script=$2

echo "$salida_esperada"
echo "$resuldado_script"

if [ $salida_esperada == $resuldado_script ]; then
  exit 0
else
  exit 1
fi