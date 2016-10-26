# OpenNfuMain.py
# Designed to be the main startup target for a prosthetic system
#
# Usage: 
#   python OpenNfuMain.py
#   python OpenNfuMain.py --log DEBUG
# Help: 
#   python OpenNfuMain.py -h
#
# Requirements:
#   bluepy
#   numpy
#   scipy
#   sklearn
#   

import logging
import time
from mpl.nfu import NfuUdp
from utilities import user_config


def main():
    """ 
    Run OpenNFU interface
    """

    h = setup_limb_connection()
    setup_signal_source()

    wait_for_limb_connection()
    wait_for_signals()
    test_limb_connection(h)

    run_algorithm()
    close(h)


def setup_logging():
    user_config.setup_file_logging('OpenNFU_')


def setup_limb_connection():
    # Establish network inferface to MPL at address below
    # h = NfuUdp(Hostname="192.168.1.111")
    h = NfuUdp(hostname="localhost")
    h.connect()
    return h


def setup_signal_source():
    pass


def wait_for_limb_connection():
    pass


def wait_for_signals():
    pass


def test_limb_connection(h):
    # Run a quick motion test to verify joints are working
    num_arm_joints = 7
    num_hand_joints = 20
    arm_position = [0.0] * num_arm_joints
    hand_position = [0.0] * num_hand_joints

    # goto zero position
    h.send_joint_angles(arm_position + hand_position)
    time.sleep(3)

    # goto elbow bent position
    arm_position[3] = 0.3
    h.send_joint_angles(arm_position + hand_position)
    time.sleep(3)


def run_algorithm():
    pass


def close(h):
    h.close()
    logging.info('Ending OpenNFU')
    logging.info('-----------------------------------------------')
    # Add short delay to view any final messages at console
    time.sleep(1.0)


if __name__ == "__main__":
    setup_logging()
    main()
