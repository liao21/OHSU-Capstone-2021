import logging
import utilities.user_config as uc
from utilities import FixedRateLoop
import scenarios
from pattern_rec import training
import time
import keyboard
import mouse


class VieOutput(object):
    def __init__(self):
        self.enabled = True
        # Add a bail out key to terminate emulation
        keyboard.add_hotkey('esc', lambda: self.toggle())

    def start(self):
        self.enabled = True

    def stop(self):
        self.enabled = False

    def toggle(self):
        self.enabled = not self.enabled

    def update(self, decision):
        if not self.enabled:
            return

        if decision is 'No Movement':
            pass
        elif decision is 'Left':
            mouse.move(-5, 0, absolute=False)
        elif decision is 'Right':
            mouse.move(+5, 0, absolute=False)
        elif decision is 'Up':
            mouse.move(0, -5, absolute=False)
        elif decision is 'Down':
            mouse.move(0, +5, absolute=False)


def parse_arguments():
    """Parse command line arguments into argparse model.

    Command-line arguments:
    -h or --help -- output help text describing command-line arguments.

    """
    import argparse

    # Parse main function input parameters to get user_config xml file
    parser = argparse.ArgumentParser(description='Configure and run a basic VIE with web training.')
    parser.add_argument('-x', '--XML', help='Specify path for user config file', default='user_config_default.xml')
    parser.add_argument("-l", "--log", dest="logLevel", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default=logging.INFO, help="Set the logging level")

    return parser.parse_args()


def main(args):

    # setup logging.  This will create a log file like: USER_2016-02-11_11-28-21.log to which all 'logging' calls go
    uc.read_user_config(file=args.XML)
    uc.setup_file_logging(log_level=args.logLevel)

    # Setup MPL scenario
    # A Scenario is the fundamental building blocks of the VIE: Inputs, Signal Analysis, System Plant, and Output Sink
    vie = scenarios.MplScenario()

    # setup web interface
    vie.TrainingInterface = training.TrainingManagerWebsocket()
    vie.TrainingInterface.setup(port=uc.get_user_config_var('mpl_app_port', 9090))
    vie.TrainingInterface.add_message_handler(vie.command_string)

    vie.setup()

    vie.TrainingData.motion_names = ('No Movement','Left','Right','Up','Down')
    custom_output = VieOutput()

    looper = FixedRateLoop(vie.Plant.dt)

    def loop_func():
        # Run the actual model
        output = vie.update()

        # send gui updates
        msg = '<br>' + output['status']  # Classifier Status
        for src in vie.SignalSource:
            msg += '<br>MYO:' + src.get_status_msg()
        msg += '<br>' + time.strftime("%c")

        # Forward status message (voltage, temp, etc) to mobile app
        vie.TrainingInterface.send_message("strStatus", msg)
        # Send classifier output to mobile app (e.g. Elbow Flexion)
        vie.TrainingInterface.send_message("strOutputMotion", output['decision'])
        # Send motion training status to mobile app (e.g. No Movement [70]
        msg = '{} [{:.0f}]'.format(vie.training_motion,
                                   round(vie.TrainingData.get_totals(vie.training_id), -1))
        vie.TrainingInterface.send_message("strTrainingMotion", msg)

        custom_output.update(output['decision'])

    looper.loop(loop_func)

    vie.TrainingInterface.send_message("strStatus", 'CLOSED')

    vie.close()


if __name__ == '__main__':
    arguments = parse_arguments()
    main(arguments)