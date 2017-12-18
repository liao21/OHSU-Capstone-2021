#!/usr/bin/env python3
# test script for MPL interface
#
# This test function is intended to be operated from the command line to bring up a short menu allow communication
# tests with the MPL.
#
# Revisions:
# 2016OCT05 Armiger: Created
# 2017SEP29 Armiger: Added input arguments so that a user config file can be added for different setups
#
#

import logging
import utilities.user_config as uc
import scenarios
import inputs.dcell
from pattern_rec import training, assessment


def main():
    """Parse command line arguments into argparse model.

    Command-line arguments:
    -h or --help -- output help text describing command-line arguments.

    """
    import argparse

    # Parse main function input parameters to get user_config xml file
    parser = argparse.ArgumentParser(description='run_www: Configure and run a full user VIE with web training.')
    parser.add_argument('-x', '--XML', help='Specify path for user config file', default='user_config_default.xml')
    parser.add_argument("-l", "--log", dest="logLevel", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        default=logging.INFO, help="Set the logging level")

    args = parser.parse_args()

    # setup logging.  This will create a log file like: USER_2016-02-11_11-28-21.log to which all 'logging' calls go
    uc.read_user_config(file=args.XML)
    uc.setup_file_logging(log_level=args.logLevel)

    # Setup MPL scenario
    # A Scenario is the fundamental building blocks of the VIE: Inputs, Signal Analysis, System Plant, and Output Sink
    vie = scenarios.MplScenario()
    vie.setup()

    # setup web interface
    vie.TrainingInterface = training.TrainingManagerSpacebrew()
    vie.TrainingInterface.setup(description="JHU/APL Embedded Controller", server="127.0.0.1", port=9000)
    vie.TrainingInterface.add_message_handler(vie.command_string)

    # Setup Assessments
    tac = assessment.TargetAchievementControl(vie, vie.TrainingInterface)
    vie.TrainingInterface.add_message_handler(tac.command_string)
    motion_test = assessment.MotionTester(vie, vie.TrainingInterface)
    vie.TrainingInterface.add_message_handler(motion_test.command_string)

    # Setup Additional Logging
    if uc.get_user_config_var('dcell_enable', 0):
        # Start DCell Streaming
        port = uc.get_user_config_var('dcell_serial_port', '/dev/ttymxc2')
        dc = inputs.dcell.DCellSerial(port)
        # Connect and start streaming
        dc.enable_data_logging = True
        try:
            dc.connect()
            logging.info('DCell streaming started successfully')
        except Exception:
            log = logging.getLogger()
            log.exception('Error from DCELL:')

    try:
        vie.run()
    except KeyboardInterrupt:
        vie.close()
        vie.TrainingInterface.brew.stop()


if __name__ == '__main__':
    main()
