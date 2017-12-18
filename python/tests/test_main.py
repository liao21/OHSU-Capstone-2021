# Test MiniVIE/Python Project
#
# Use in conjunction with coverage analyzer as such:
#
# coverage run test_main.py
# coverage html

import os
import time
import logging
import sys
import time
# Need both these lines to allow double click in windows
sys.path.insert(0, os.path.abspath('../minivie'))
os.chdir('../minivie')  # change directory so xml files can be found as expected

from utilities import user_config
user_config.setup_file_logging('MINIVIE_TEST_')
logging.debug('Running MINIVIE_TEST Script')
user_config.main()

from scenarios import MyoUDPTrainer

from controls import plant
plant.main()

import pattern_rec
pattern_rec.test_feature_extract()

from mpl import roc
roc.main()


# setup simulator
from mpl.open_nfu import Simulator
import run_www

a = Simulator()
a.start()
try:
    run_www.main()
except KeyboardInterrupt:
    pass

a.stop()

print('-' * 30)
print('All Tests Completed Successfully')
print('-' * 30)

time.sleep(1.0)