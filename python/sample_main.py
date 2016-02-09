# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 10:17:58 2016

Initial pass at simulating MiniVIE processing using python so that this runs on an embedded device

@author: R. Armiger
"""

import sys
import math
import time
import numpy as np
from MyoUdp import MyoUdp
from Plant import Plant
from UnityUdp import UnityUdp
from TrainingUdp import TrainingUdp
from feature_extract import feature_extract

VERBOSE = 1

dt = 0.02  # seconds per loop.  50Hz update

# Create data objects

# Singal Source get external bio-signal data
hMyo = MyoUdp()#("192.168.1.3")

# Training Data holds data labels 
hTrain = TrainingUdp()

# Plant maintains current limb state (positions) during velocity control
hPlant = Plant(dt)

# Sink is output to ouside world (in this case to VIE)
hSink = UnityUdp() #("192.168.1.24")

# Classifier parameters
W = np.genfromtxt("weights.txt", dtype=None)
C = np.genfromtxt("centers.txt", dtype=None)
# Classifier class names 
with open("classes.txt") as f:
    classNames = f.read().splitlines()

trainCurrentClass = []

#create filefor dumping training data
file=open('tmp.dat','w')
     
# Iteration counter
cycleMax = 1000  # Max iterations (0 for infinite)
cycleCnt = 0  # Internal Counter
timeElapsed = -1
try:
    # setup main loop control
    print("Running...")
    sys.stdout.flush()

    while True: # main loop

        # LOOP CONTROL        
        # Terminate after certain muber of steps
        cycleCnt = cycleCnt + 1
        if (cycleMax > 0) and cycleCnt > cycleMax:
            break
        # LOOP CONTROL        

        # LOOP TIMING (to achieve fixed rate)
        timeBegin = time.time()


        # Get data and extract features
        # feature vector should be [1,nChan*nFeat]
        # data ordering is as follows
        # [ch1f1, ch1f2, ch1f3, ch1f4, ch2f1, ch2f2, ch2f3, ch2f4, ... chNf4]
        f = feature_extract(hMyo.getData()*0.01)
        
        # Classify
        # features[1,nChan*nFeat] * Wg[nChan*numFeat,nClasses] + Cg[1,nClasses]
        v = np.dot(f, W) + C
        classNum = v.argmax()

        # Move joints using classifier
        jointId, jointDir = hPlant.class_map(classNames[classNum])

        # Set joint velocities
        hPlant.velocity[:hPlant.NUM_JOINTS] = [0.0] * hPlant.NUM_JOINTS
        if jointId:
            for i in jointId:
                hPlant.velocity[i] = jointDir

        hPlant.update()

        # perform joint motion update
        vals = hMyo.getAngles()
        hPlant.position[3] = vals[1] + math.pi/2

        # transmit output
        hSink.sendJointAngles(hPlant.position)


        # Training Process begin logging
        cName = str(hTrain.class_name)
        if cName:
            print(cName)
            #txt = ','.join(map(str, f.tolist()))
            f.tofile(file)
            #file.write(' %d %s\n'%(hTrain.class_id, cName))
        
        # Training Process end


        # DEBUG output display
        if VERBOSE:
            #print(f[:1,:])
            print(("%8.4f" % hPlant.position[3], \
            "%8.4f" % hPlant.position[4]), \
            'Class: %s' % classNames[classNum])

        # LOOP TIMING (to achieve fixed rate)
        timeEnd = time.time()
        timeElapsed = timeEnd - timeBegin
        if dt > timeElapsed:
            time.sleep(dt-timeElapsed)
        else:
            print("Timing Overload")

finally:
    print(hMyo.getData())
    print("Last timeElapsed was: ", timeElapsed)
    hSink.close()
    hMyo.close()
    hTrain.close()
    file.close()     #close file  
