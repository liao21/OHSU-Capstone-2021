#!/usr/bin/env python
# test script for MPL interface
#
# This test function is intended to be operated from the command line to bring up a short menu allow communication
# tests with the MPL.
#
# Revisions:
# 2016OCT05 Armiger: Created

# Python 2 and 3:
import time
import numpy as np
from builtins import input
import logging

import utilities
from mpl.open_nfu import NfuUdp
# from mpl.unity import UnityUdp
import mpl.roc as roc


# Show menu
print(30 * '-')
print("   M P L - T E S T ")
print(30 * '-')
print("1. Ping: Limb system and router using OS")
print("2. MPL Wrist")
print("3. MPL Grasps")
print("4. MPL Heartbeats")
print(30 * '-')
print("0. Exit")
print(30 * '-')
print(30 * '-')
print("NOTE: Ensure no other MPL control processes are running. E.g. sudo systemctl stop mpl_run_www.service")
print(30 * '-')

# Get input
choice = input('Enter selection : ')
assert isinstance(choice, str)  # native str on Py2 and Py3

# Convert string to int type
choice = int(choice)

AA = -0.3
EL = 0
armTestStart = [0, AA, 0, EL, 0, 0, 0]

# Take action as per selected menu-option #
if choice == 0:
    pass
if choice == 1:
    print("Starting ping...")
    print(60 * '-')
    print("NOTE: MPL/NFU and host MAC addresses must be on the approved access list in /etc/iptables/rules.v4")
    print(60 * '-')

    result = 0
    while not result:
        result = utilities.ping('192.168.1.111')
    print(result)

elif choice == 2:
    print("Starting MPL Wrist...")
    # hSink = UnityUdp()  commands on 9027, telem 9028
    hSink = NfuUdp(hostname="127.0.0.1", udp_telem_port=9028, udp_command_port=9027)
    hSink.connect()

    hSink.send_joint_angles([0, AA, 0, EL, -0.7, -0.5, -0.5])
    time.sleep(1.0)
    AA = -0.25
    hSink.send_joint_angles([0, AA, 0, EL + 0.55, -0.7, -0.5, -0.5])
    time.sleep(1.0)
    hSink.send_joint_angles([0, AA, 0, EL, 0.7, 0.5, 0.5])
    time.sleep(1.0)
    hSink.send_joint_angles(armTestStart)
    hSink.close()

elif choice == 3:
    print("Starting MPL Grasps...")
    # hSink = UnityUdp()
    hSink = NfuUdp(hostname="127.0.0.1", udp_telem_port=9028, udp_command_port=9027)
    hSink.connect()

    # Read ROC Table

    filename = "../../WrRocDefaults.xml"
    rocTable = roc.read_roc_table(filename)

    for iRoc in [2, 4, 5, 7, 15]:
        numOpenSteps = 50
        numWaitSteps = 50
        numCloseSteps = 50

        mplAngles = np.zeros(27)
        mplAngles[1] = -0.3
        mplAngles[3] = EL + 0.05

        rocElem = roc.get_roc_id(rocTable, iRoc)

        graspVal = np.concatenate(
            (np.linspace(0, 1, numOpenSteps), np.ones(numWaitSteps), np.linspace(1, 0, numCloseSteps)))
        for iVal in graspVal:
            print('Entry #{}, RocId={}, {} {:6.1f} Pct'.format(iRoc, rocElem.id, rocElem.name, iVal * 100))
            mplAngles[rocElem.joints] = roc.get_roc_values(rocElem, iVal)
            hSink.send_joint_angles(mplAngles)
            time.sleep(0.02)
    hSink.close()
elif choice == 4:
    logging.basicConfig(level=logging.INFO)
    hSink = NfuUdp(hostname="127.0.0.1", udp_telem_port=9028, udp_command_port=9027)
    hSink.connect()
    while True:
        try:
            print(hSink.get_status_msg())
            time.sleep(1)
        except KeyboardInterrupt:
            break

    hSink.close()

else:  # default
    print("Exiting...")
