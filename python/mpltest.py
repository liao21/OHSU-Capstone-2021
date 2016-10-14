#!/usr/bin/python
# test script for MPL interface
# Revisions:
# 2016OCT05 Armiger: Created

# Python 2 and 3:
import time
import numpy as np
from builtins import input
from UnityUdp import UnityUdp 
from NfuUdp import NfuUdp 
import RocTableClass

def ping(host):
    """
    Returns True if host responds to a ping request
    """
    import os, platform

    # Ping parameters as function of OS
    ping_str = "-n 1" if  platform.system().lower()=="windows" else "-c 1"

    # Ping
    return os.system("ping " + ping_str + " " + host) == 0

## Show menu ##
print (30 * '-')
print ("   M P L - T E S T ")
print (30 * '-')
print ("1. Ping: Limb system and router using OS")
print ("2. MPL Wrist")
print ("3. MPL Grasps")
print (30 * '-')
 
## Get input ###
#choice = raw_input('Enter your choice [1-3] : ')
choice = input('Enter selection : ')
assert isinstance(choice, str)    # native str on Py2 and Py3
 
### Convert string to int type ##
choice = int(choice)

AA = -0.3
EL = 0
armTestStart = [0, AA, 0, EL, 0, 0, 0]


### Take action as per selected menu-option ###
if choice == 1:
        print ("Starting ping...")
        result = ping('192.168.1.111')
        #result = ping('127.0.0.1')
        print(result)
elif choice == 2:
        print ("Starting MPL Wrist...")
        #hSink = UnityUdp()
        hSink = NfuUdp()

        hSink.sendJointAngles([0, AA, 0, EL, -0.7, -0.5, -0.5]);
        time.sleep(1.0)
        AA = -0.25;
        hSink.sendJointAngles([0, AA, 0, EL+0.05, -0.7, -0.5, -0.5]);
        time.sleep(1.0)
        hSink.sendJointAngles([0, AA, 0, EL, 0.7, 0.5, 0.5]);
        time.sleep(1.0)
        hSink.sendJointAngles(armTestStart);
        hSink.close()
        
elif choice == 3:
        print ("Starting MPL Grasps...")
        hSink = UnityUdp()

        # Read ROC Table

        filename = "../WrRocDefaults.xml"
        rocTable = RocTableClass.readRoc(filename)

        for iRoc in [2, 4, 5, 7, 15]:
            numOpenSteps = 50;
            numWaitSteps = 50;
            numCloseSteps = 50;
            
            mplAngles = np.zeros(27);
            mplAngles[1] = -0.3;
            mplAngles[3] = EL+0.05;
            
            rocElem = RocTableClass.getRocId(rocTable, iRoc)
            
            graspVal = np.concatenate((np.linspace(0,1,numOpenSteps),np.ones(numWaitSteps),np.linspace(1,0,numCloseSteps)));
            for iVal in graspVal:
                print('Entry #{}, RocId={}, {} {:6.1f} Pct'.format(iRoc,rocElem.id,rocElem.name,iVal*100))
                
                
                newVals = RocTableClass.getRocValues(rocElem, iVal)
                
                mplAngles[rocElem.joints] = newVals
                
                hSink.sendJointAngles(mplAngles);
                time.sleep(0.02);
        hSink.close()
        
else:    ## default ##
        print ("Invalid number. Try again...")
        
