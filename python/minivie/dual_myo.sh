#!/bin/bash

cd /home/pi/git/minivie/python/minivie/inputs/

sudo ./myo.py -tx --ADDR //127.0.0.1:15001 --MAC C3:0A:EA:14:14:D9 --IFACE 0 &
sudo ./myo.py -tx --ADDR //127.0.0.1:15002 --MAC F0:1C:CD:A7:2C:85 --IFACE 1 &
