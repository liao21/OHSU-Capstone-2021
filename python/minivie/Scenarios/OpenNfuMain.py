## OpenNfuMain.py
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

import argparse
import sys
import logging
import xml.etree.cElementTree as ET
import time
from MPL.NfuUdp import NfuUdp
from Utilities import UserConfig

def main():
    """ 
    Run OpenNFU interface
    """

    setupLogging()
    h = setupLimbConnection()
    setupSignalSource()

    waitForLimbConnection()
    waitForSignals()
    testLimbConnection(h)

    runAlgorithm()
    close(h)
def setupLogging():
    UserConfig.setupFileLogging('OpenNFU_')
    
def setupLimbConnection():
    # Establish network inferface to MPL at address below
    #h = NfuUdp(Hostname="192.168.1.111")
    h = NfuUdp(Hostname="localhost")
    h.connect()
    return h
	
def setupSignalSource():
    pass

def waitForLimbConnection():
    pass
def waitForSignals():
    pass
	
def testLimbConnection(h):
    
    # Run a quick motion test to verify joints are working
    NUM_ARM_JOINTS = 7;
    NUM_HAND_JOINTS = 20;
    armPosition = [0.0]*NUM_ARM_JOINTS
    handPosition = [0.0]*NUM_HAND_JOINTS

    # goto zero position
    h.sendJointAngles(armPosition+handPosition)
    time.sleep(3)

    # goto elbow bent position
    armPosition[3] = 0.3
    h.sendJointAngles(armPosition+handPosition)
    time.sleep(3)
	
def runAlgorithm():
    pass


def close(h):
    h.close()
    logging.info('Ending OpenNFU')
    logging.info('-----------------------------------------------')
    # Add short delay to view any final messages at console
    time.sleep(1.0)

	
if __name__ == "__main__":
    main()
