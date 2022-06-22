#!/bin/bash

if [ $# -ne 2 ]; then
  echo El script no recibió 2 parámetros
  exit 1
fi

re='^[0-9]+$'
if ! [[ $1 =~ $re && $2 =~ $re ]] ; then
   echo "No ingresaste un nuemro entero" >&2; exit 1
fi

num1=$1
num2=$2

resuldato_suma=$(($num1 + $num2))
resuldato_resta=$(($num1 - $num2))
resuldato_multiplicacion=$(($num1 * $num2))
resuldato_division=$(($num1 / $num2))

echo "$resuldato_suma"
echo "$resuldato_resta"
echo "$resuldato_multiplicacion"
echo "$resuldato_division"