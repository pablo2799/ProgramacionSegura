#!/bin/bash

mkdir /home/pablo/tmp
cd /home/pablo/tmp
for i in {0..9}
do
    touch "archivo$i.txt"
done
for i in {0..4}
do
    touch "archivo$i.py"
done