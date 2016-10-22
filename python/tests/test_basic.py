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

from utilities import user_config
user_config.setup_file_logging('MINIVIE_TEST_')
logging.debug('Running MINIVIE_TEST Script')
user_config.main()

from inputs import myo
myo.main()

from scenarios import MyoUDPTrainer
MyoUDPTrainer

from controls import plant
plant.main()

from mpl import roc
roc.main()

from mpl import nfu
nfu.main()
# generates warning for too long parameter name
nfu = nfu.NfuUdp()
nfu.msg_update_param('LONG_PARAM' + '*' * 160 + '|', 0.0)

from scenarios import open_nfu
open_nfu.main()

from scenarios import sample_main
sample_main.main()

print('-' * 30)
print('All Tests Completed Successfully')
print('-' * 30)

time.sleep(1.0)