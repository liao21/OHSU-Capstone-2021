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
from utilities import user_config
from scenarios import mpl_nfu
from mpl.open_nfu import NfuUdp
from pattern_rec import training, assessment
from inputs import dcell


def main():
    """Parse command line arguments into argparse model.

    Command-line arguments:
    -h or --help -- output help text describing command-line arguments.

    """
    import argparse

    # Parse main function input parameters to get user_config xml file
    parser = argparse.ArgumentParser(description='run_www: Configure and run a full user VIE with web training.')
    parser.add_argument('-x', '--XML', help='Specify path for user config file', default='../../user_config.xml')
    parser.add_argument("-l", "--log", dest="logLevel", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        default=logging.INFO, help="Set the logging level")

    args = parser.parse_args()

    # setup logging.  This will create a log file like: USER_2016-02-11_11-28-21.log to which all 'logging' calls go
    user_config.read_user_config(file=args.XML)
    prefix = user_config.get_user_config_var('userFilePrefix', 'USER_')
    user_config.setup_file_logging(prefix=prefix, log_level=args.logLevel)

    # Setup MPL scenario
    # A Scenario is the fundamental building blocks of the VIE: Inputs, Signal Analysis, System Plant, and Output Sink
    vie = mpl_nfu.setup()
    vie.DataSink.close()  # close default unity sink

    # Replace sink with actual arm
    sink = NfuUdp(hostname="127.0.0.1", udp_telem_port=9028, udp_command_port=9027)
    sink.connect()
    sink.wait_for_connection()
    # Synch joint position
    if sink.last_percept_position is not None:
        for i in range(0,len(vie.Plant.JointPosition)):
            vie.Plant.JointPosition[i] = sink.last_percept_position[i]

    vie.DataSink = sink

    # setup web interface
    vie.TrainingInterface = training.TrainingManagerSpacebrew()
    vie.TrainingInterface.setup(description="JHU/APL Embedded Controller", server="127.0.0.1", port=9000)
    vie.TrainingInterface.add_message_handler(vie.command_string)

    # Setup Assessments
    tac = assessment.TargetAchievementControl(vie, vie.TrainingInterface)
    vie.TrainingInterface.add_message_handler(tac.command_string)
    motion_test = assessment.MotionTester(vie, vie.TrainingInterface)
    vie.TrainingInterface.add_message_handler(motion_test.command_string)

    # Start DCell Streaming
    dc = dcell.DCellSerial('/dev/ttymxc2')
    # Connect and start streaming
    dc.enable_data_logging = True
    try:
        dc.connect()
        logging.info('DCell streaming started successfully')
    except Exception as err:
        log = logging.getLogger()
        log.exception('Error from DCELL:')

    mpl_nfu.run(vie)


if __name__ == '__main__':
    main()
