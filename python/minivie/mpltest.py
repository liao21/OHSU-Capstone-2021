#!/usr/bin/python
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
from MPL.UnityUdp import UnityUdp
from MPL.NfuUdp import NfuUdp
import MPL.RocTableClass


def ping(host):
    """
    Returns True if host responds to a ping request
    """
    import os
    import platform

    # Ping parameters as function of OS
    ping_str = "-n 1" if platform.system().lower() == "windows" else "-c 1"

    # Ping
    return os.system("ping " + ping_str + " " + host) == 0


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

    result = 0
    while not result:
        result = ping('192.168.1.111')
        # result = ping('127.0.0.1')
    print(result)
elif choice == 2:
    print("Starting MPL Wrist...")
    # hSink = UnityUdp()
    hSink = NfuUdp()
    hSink.connect()

    hSink.sendJointAngles([0, AA, 0, EL, -0.7, -0.5, -0.5])
    time.sleep(1.0)
    AA = -0.25
    hSink.sendJointAngles([0, AA, 0, EL + 0.05, -0.7, -0.5, -0.5])
    time.sleep(1.0)
    hSink.sendJointAngles([0, AA, 0, EL, 0.7, 0.5, 0.5])
    time.sleep(1.0)
    hSink.sendJointAngles(armTestStart)
    hSink.close()

elif choice == 3:
    print("Starting MPL Grasps...")
    # hSink = UnityUdp()
    hSink = NfuUdp()
    hSink.connect()

    # Read ROC Table

    filename = "../../WrRocDefaults.xml"
    rocTable = MPL.RocTableClass.readRoc(filename)

    for iRoc in [2, 4, 5, 7, 15]:
        numOpenSteps = 50
        numWaitSteps = 50
        numCloseSteps = 50

        mplAngles = np.zeros(27)
        mplAngles[1] = -0.3
        mplAngles[3] = EL + 0.05

        rocElem = MPL.RocTableClass.getRocId(rocTable, iRoc)

        graspVal = np.concatenate(
            (np.linspace(0, 1, numOpenSteps), np.ones(numWaitSteps), np.linspace(1, 0, numCloseSteps)))
        for iVal in graspVal:
            print('Entry #{}, RocId={}, {} {:6.1f} Pct'.format(iRoc, rocElem.id, rocElem.name, iVal * 100))
            mplAngles[rocElem.joints] = MPL.RocTableClass.getRocValues(rocElem, iVal)
            hSink.sendJointAngles(mplAngles)
            time.sleep(0.02)
    hSink.close()
elif choice == 4:
    hSink = NfuUdp()
    hSink.connect()
    time.sleep(5)

    hSink.close()

else:  # default
    print("Exiting...")
