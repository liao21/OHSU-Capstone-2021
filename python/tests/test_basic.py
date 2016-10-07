# Test MiniVIE/Python Project
#
# Use in conjunction with coverage analyzer as such:
#
# coverage run test_basic.py
# coverage html

import os
import sys
sys.path.insert(0, os.path.abspath('..'))
os.chdir('..')  # change directory so xml files can be found as expected

import RocTableClass
RocTableClass.main()

import UserConfigXml
UserConfigXml.main()

import NfuUdp
NfuUdp.main()
# generates warning for too long parameter name
nfu = NfuUdp.NfuUdp()
nfu.msgUpdateParam('-' *160, 0.0)

import OpenNfuMain
OpenNfuMain.main()

import Plant
Plant.main()

#import sample_main
#sample_main.main()

