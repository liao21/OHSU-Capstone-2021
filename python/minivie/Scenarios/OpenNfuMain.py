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
from datetime import datetime
import time
from MPL.NfuUdp import NfuUdp

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
    ######################
    # setup logging
    ######################

    # Logging info
    # Level 	When it's used
    # ------    ---------------
    # DEBUG 	Detailed information, typically of interest only when diagnosing problems.
    # INFO 	Confirmation that things are working as expected.
    # WARNING 	An indication that something unexpected happened, or indicative of some problem in the near future (e.g. 'disk space low'). The software is still working as expected.
    # ERROR 	Due to a more serious problem, the software has not been able to perform some function.
    # CRITICAL 	A serious error, indicating that the program itself may be unable to continue running.

    
    # start message log
    fileName = "OpenNFU" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
    logPath = '.'
    # assuming loglevel is bound to the string value obtained from the
    # command line argument. Convert to upper case to allow the user to
    # specify --log=DEBUG or --log=debug
    parser = argparse.ArgumentParser(description='Main OpenNFU function')
    parser.add_argument('--log', dest='loglevel',
                        default='INFO',
                        help='Set loglevel as DEBUG INFO WARNING ERROR CRITICAL (default is INFO)')
    args = parser.parse_args()
    
    loglevel = args.loglevel
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    
    #logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(loglevel)

    fileHandler = logging.FileHandler("{0}/{1}".format(logPath, fileName))
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)



    #logging.basicConfig(filename='OpenNFU.log',format='%(asctime)s:%(levelname)s:%(message)s', \
    #                    level=numeric_level, datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.info('-----------------------------------------------')
    logging.info('Starting OpenNFU with log level ' + loglevel)
    logging.info('-----------------------------------------------')
    
def setupLimbConnection():
    # Establish network inferface to MPL at address below
    #h = NfuUdp(Hostname="192.168.1.111")
    h = NfuUdp(Hostname="localhost")
	
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
    armVelocity = [0.0]*NUM_ARM_JOINTS
    handPosition = [0.0]*NUM_HAND_JOINTS
    handVelocity = [0.0]*NUM_HAND_JOINTS

    # goto zero position
    h.sendJointAngles(armPosition+armVelocity+handPosition+handVelocity)
    time.sleep(3)

    # goto elbow bent position
    armPosition[3] = 0.3
    h.sendJointAngles(armPosition+armVelocity+handPosition+handVelocity)
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
