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
from pattern_rec import training, assessment


def main():

    """Parse command line arguments into argparse model.

    Command-line arguments:
    -h or --help -- output help text describing command-line arguments.

    """
    import argparse

    # Parse main function input parameters to get user_config xml file
    parser = argparse.ArgumentParser(description='run_www: Configure and run a full user VIE with web training.')
    parser.add_argument('-x', '--XML', help='Specify path for user config file', default='../../user_config.xml')
    args = parser.parse_args()

    # setup logging.  This will create a log file like: USER_2016-02-11_11-28-21.log to which all 'logging' calls go
    user_config.read_user_config(file=args.XML)
    prefix = user_config.get_user_config_var('userFilePrefix', 'USER_')
    user_config.setup_file_logging(prefix=prefix)

    # Setup MPL scenario
    vie = scenarios.mpl_nfu.setup()

    # setup web interface
    vie.TrainingInterface = training.TrainingManagerSpacebrew()
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
