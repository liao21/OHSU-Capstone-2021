#!/usr/bin/env python
# test script for MPL interface
#
# This test function is intended to be operated from the command line to bring up a short menu allow communication
# tests with the MPL.
#
# Revisions:
# 2016OCT05 Armiger: Created

# Python 2 and 3:
from utilities import user_config
import scenarios.mpl_nfu
from pattern_rec.training import TrainingManagerSpacebrew
import assessment


def main():

    # setup logging
    user_config.setup_file_logging(prefix='VMPL_')

    # Setup MPL scenario
    vie = scenarios.mpl_nfu.setup()

    # setup web interface
    vie.TrainingInterface = TrainingManagerSpacebrew()
    vie.TrainingInterface.setup(description="JHU/APL Embedded Controller", server="127.0.0.1", port=9000)
    vie.TrainingInterface.add_message_handler(vie.command_string)

    # Setup Assessment
    tac = assessment.TargetAchievementControl(vie, vie.TrainingInterface)
    motion_test = assessment.MotionTester(vie, vie.TrainingInterface)
    vie.TrainingInterface.add_message_handler(motion_test.command_string)
    vie.TrainingInterface.add_message_handler(tac.command_string)

    scenarios.mpl_nfu.run(vie)


if __name__ == '__main__':
    main()
