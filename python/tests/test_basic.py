# Test MiniVIE/Python Project

import os
import sys
sys.path.insert(0, os.path.abspath('..'))
os.chdir('..')  # change directory so xml files can be found as expected

import RocTableClass
RocTableClass.main()

import UserConfigXml
UserConfigXml.main()

#import sample_main
#sample_main.main()

