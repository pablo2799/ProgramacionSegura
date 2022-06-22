#!/bin/bash

scripts_estudiante=$1

/bin/bash "$scripts_estudiante" 5.1 4
var1=$?

/bin/bash "$scripts_estudiante" 2 2.1
var2=$?

/bin/bash "$scripts_estudiante" 2
var3=$?

/bin/bash "$scripts_estudiante" 2 2 2
var4=$?

/bin/bash "$scripts_estudiante"
var5=$?

if [ "$var1" -eq 0 ]; then
  exit 1
elif [ "$var2" -eq 0 ]; then
  exit 1
elif [ "$var3" -eq 0 ]; then
  exit 1
elif [ "$var4" -eq 0 ]; then
  exit 1
elif [ "$var5" -eq 0 ]; then
  exit 1
else
  exit 0
fi