#!/usr/bin/env python3
"""This module is the main entry point for the Python Virtual Integration Environment Web App and classifier.

The module supplies one function, main()
Typically this module is started from the command line or auto-run on linux using the systemctl module

Command line arguments allow the specification for a user config parameter file as well as the log level

Example usage:

Windows (using python launcher):
> py -3.6 run_www.py -x my_user_config.xml -l DEBUG

Linux (using python shebang statement):
> ./run_www.py -x my_user_config.xml -l DEBUG
or
> sudo systemctl start mpl_run_www

Revisions:
2016OCT05 Armiger: Created
2017SEP29 Armiger: Added input arguments so that a user config file can be added for different setups
2019JAN19 Armiger: Added asyncio event loop
"""

import asyncio
import logging
import argparse
from utilities import user_config
import scenarios
import sys
MIN_PYTHON = (3, 6)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python %s.%s or later is required.\n" % MIN_PYTHON)


def main():
    """Parse command line arguments into argparse model.

    Command-line arguments:
    -h or --help -- output help text describing command-line arguments.

    """

    # Parse main function input parameters to get user_config xml file
    parser = argparse.ArgumentParser(description='run_www: Configure and run a full user VIE with web training.')
    parser.add_argument('-x', '--XML', help='Specify path for user config file', default='user_config_default.xml')
    parser.add_argument("-l", "--log", dest="logLevel", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        default=logging.INFO, help="Set the logging level")
    args = parser.parse_args()

    # read the user parameter (xml) file
    user_config.read_user_config_file(file=args.XML)

    # Setup logging.  This will create a log file like: USER_2016-02-11_11-28-21.log to which all 'logging' calls go
    user_config.setup_file_logging(log_level=args.logLevel)

    # Setup Default MPL scenario
    # A Scenario is the fundamental building blocks of the VIE: Inputs, Signal Analysis, System Plant, and Output Sink
    vie = scenarios.MplScenario()

    # Perform setup operations based on settings above
    vie.setup()
    vie.setup_interfaces()  # setup web-app and user assessment functions
    vie.setup_load_cell()   # setup interface

    # Run the VIE system
    loop = asyncio.get_event_loop()
    loop.create_task(vie.run())
    if vie.futures is not None:
        loop.run_until_complete(vie.futures())
    loop.run_forever()


if __name__ == '__main__':
    main()
