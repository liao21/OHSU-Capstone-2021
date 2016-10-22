# Test MiniVIE/Python Project
#
# Use in conjunction with coverage analyzer as such:
#
# coverage run test_basic.py
# coverage html

import os
import sys
import time
import logging
sys.path.insert(0, os.path.abspath('../minivie'))
os.chdir('../minivie')  # change directory so xml files can be found as expected

from Utilities import UserConfig
UserConfig.setupFileLogging('MINIVIE_TEST_')
logging.debug('Running MINIVIE_TEST Script')
UserConfig.main()

from Inputs import Myo
Myo.main()

from Scenarios import MyoUDPTrainer
MyoUDPTrainer

from Controls import Plant
Plant.main()

from MPL import RocTableClass
RocTableClass.main()

from MPL import NfuUdp
NfuUdp.main()
# generates warning for too long parameter name
nfu = NfuUdp.NfuUdp()
nfu.msgUpdateParam('LONG_PARAM' + '*' * 160 + '|', 0.0)

from Scenarios import OpenNfuMain
OpenNfuMain.main()

from Scenarios import sample_main
sample_main.main()

print('-' * 30)
print('All Tests Completed Successfully')
print('-' * 30)

time.sleep(1.0)