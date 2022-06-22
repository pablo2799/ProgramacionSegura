#!/bin/bash

mkdir prueba/
cd prueba/
for i in {0..9}
do
    touch "archivo$i.txt"
done
for i in {0..4}
do
    touch "archivo$i.py"
done