#!/usr/bin/env python
# test script for MPL interface
#
# This test function is intended to be operated from the command line to bring up a short menu allow communication
# tests with the MPL.
#
# Revisions:
# 2016OCT05 Armiger: Created

# Python 2 and 3:
import threading
from utilities import user_config
from scenarios import mpl_nfu
from mpl.open_nfu import NfuUdp
from pattern_rec.training import TrainingManagerSpacebrew
import assessment


def main():

    # setup logging
    user_config.setup_file_logging(prefix='MPL_WWW_')

    # Setup MPL scenario
    vie = mpl_nfu.setup()
    vie.DataSink.close() # close default unity sink

    # Replace sink with actual arm
    hSink = NfuUdp(hostname="127.0.0.1", udp_telem_port=9028, udp_command_port=9027)
    hSink.connect()
    #t = threading.Thread(name='MPLNFU', target=connection_manager, args=(hSink,))
    #t.setDaemon(True)
    #t.start()
    vie.DataSink = hSink

    # setup web interface
    vie.TrainingInterface = TrainingManagerSpacebrew()
    vie.TrainingInterface.setup(description="JHU/APL Embedded Controller", server="127.0.0.1", port=9000)
    vie.TrainingInterface.add_message_handler(vie.command_string)

    # Setup Assessment
    tac = assessment.TargetAchievementControl(vie, vie.TrainingInterface)
    motion_test = assessment.MotionTester(vie, vie.TrainingInterface)
    vie.TrainingInterface.add_message_handler(motion_test.command_string)
    vie.TrainingInterface.add_message_handler(tac.command_string)

    mpl_nfu.run(vie)

if __name__ == '__main__':
    main()
