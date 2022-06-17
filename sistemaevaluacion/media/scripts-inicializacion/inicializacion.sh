#!/bin/bash

mkdir tmp
for i in {0..9}
do
    touch tmp/"archivo$i.txt"
done
for i in {0..4}
do
    touch tmp/"archivo$i.py"
done
for i in {0..2}
do
    touch tmp/"archivo$i.sh"
done