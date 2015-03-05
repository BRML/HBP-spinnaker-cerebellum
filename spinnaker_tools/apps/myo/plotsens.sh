#!/bin/sh
head -n-4 $1 > sens.dat
./plot.py sens.dat
