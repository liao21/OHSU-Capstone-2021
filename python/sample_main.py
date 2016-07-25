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

VERBOSE = 0
dt = 0.02  # seconds per loop.  50Hz update

def setup():
    ''' 
    Create the building blocks of the MiniVIE
    
        SignalSource - source of EMG data
        SignalClassifier - algorithm to classify emg into 'intent'
        Plant - Perform forward integration and apply joint limits
        DataSink - output destination of command signals (e.g. real or virtual arm)
    '''
    
    
    # TODO [Lydia1]: need to include xml file with ROC tables
    filename = "../WrRocDefaults.xml"
    # Create data objects

    # Signal Source get external bio-signal data
    # For MPL, this might be CPC Headstage, External Signal Acquisition, MyoBand, etc.
    #hMyo = MyoUdp()#("192.168.1.3")
    hMyo = MyoUdp(UDP_IP='127.0.0.1',UDP_PORT=10001,numSamples=20)#("192.168.1.3")

    # Training Data holds data labels 
    hTrain = TrainingUdp()

    # Plant maintains current limb state (positions) during velocity control
    #TODO[Lydia2] This can fail if file does not exist, then the UDP objects aren;t cleaned up properly
    hPlant = Plant(dt,filename)

    # Sink is output to outside world (in this case to VIE)
    # For MPL, this might be: real MPL/NFU, Virtual Arm, etc.
    hSink = UnityUdp() #("192.168.1.24")

    # Classifier parameters
    # TODO: generate defaults if these files don't exist, or are corrupt
    # TODO: Perform error checking to ensure number of Classes match matrix sizes
    W = np.genfromtxt("weights.txt", dtype=None)
    C = np.genfromtxt("centers.txt", dtype=None)
    # Classifier class names 
    with open("classes.txt") as f:
        classNames = f.read().splitlines()

    hClassifier = (W,C,classNames)

    #create filefor dumping training data
    #TODO[Lydia2]: store training data more efficiently and explicitly
    file=open('tmp.dat','w')
    
    return {'SignalSource':hMyo, 'SignalClassifier':hClassifier, 'DataSink':hSink, 'Plant':hPlant, 'Trainer':hTrain, 'TmpFile':file }  

def model(SignalSource,SignalClassifier,Plant,DataSink,Trainer):

    # Get data and extract features
    emgData = SignalSource.getData()*0.01
    # feature vector should be [1,nChan*nFeat]
    # data ordering is as follows
    # [ch1f1, ch1f2, ch1f3, ch1f4, ch2f1, ch2f2, ch2f3, ch2f4, ... chNf4]
    f = feature_extract(emgData)
    print('%8.4f %8.4f %8.4f %8.4f' % (f[0,0], f[0,0], f[0,0], f[0,0]))
    # Classify
    W = SignalClassifier[0];
    C = SignalClassifier[1];
    classNames = SignalClassifier[2];
    
    # features[1,nChan*nFeat] * Wg[nChan*numFeat,nClasses] + Cg[1,nClasses]
    v = np.dot(f, W) + C
    classNum = v.argmax()

    # Move joints using classifier
    jointId, jointDir = Plant.class_map(classNames[classNum])

    # Set joint velocities
    # TODO [Lydia1]: Needs ROC implementation
    Plant.velocity[:Plant.NUM_JOINTS] = [0.0] * Plant.NUM_JOINTS # initially set all to zero
    if jointId:
        for i in jointId:
            Plant.velocity[i] = jointDir # set non-zero velocity for joints we care about

    Plant.update()

    # Non-EMG Motion based inputs [Optional]
    # perform joint motion update
    vals = SignalSource.getAngles()
    # Temp: Overwrite Elbow angle based on Myo orientation
    Plant.position[3] = vals[1] + math.pi/2

    # transmit output
    DataSink.sendJointAngles(Plant.position)

    # TODO[Lydia2]: Update training 
    # Training Process begin logging
    # [Lydia2] Efficient way to organize incoming messages, store labeled data on disk
    # [Lydia3] Implement LDA in python to regen training parameters
    cName = str(Trainer.class_name)  # Do I have an external command?
    if cName:
        # If external command, write the data and label to disk
        print(cName)
        #txt = ','.join(map(str, f.tolist()))
        f.tofile(file)
        #file.write(' %d %s\n'%(Trainer.class_id, cName))
    
    # Training Process end


    # DEBUG output display
    if VERBOSE:
        #print(f[:1,:])
        print(("%8.4f" % Plant.position[3], \
        "%8.4f" % Plant.position[4]), \
        'Class: %s' % classNames[classNum])
        
def main():

    ''' Main function that involves setting up devices, 
        looping at a fixed time interval, and performing cleanup
    '''
    h = setup()
    
    # Iteration counter
    cycleMax = 140  # Max iterations (0 for infinite)
    cycleCnt = 0  # Internal Counter
    timeElapsed = -1
    try:
        # setup main loop control
        print("")
        print("Running...")
        print("")
        sys.stdout.flush()

        while ( (cycleMax > 0) and (cycleCnt < cycleMax) ): # main loop
            # Fixed rate loop.  get start time, run model, get end time; delay for duration 
            timeBegin = time.time()
            
            # Increment loop counter
            cycleCnt = cycleCnt + 1
 
            # Run the actual model
            model(h['SignalSource'],h['SignalClassifier'],h['Plant'],h['DataSink'],h['Trainer'])

            timeEnd = time.time()
            timeElapsed = timeEnd - timeBegin
            if dt > timeElapsed:
                time.sleep(dt-timeElapsed)
            else:
                print("Timing Overload")

    finally:        
        print("")
        #print("EMG Buffer:")
        #print(hMyo.getData())
        print("Last timeElapsed was: ", timeElapsed)
        print("")
        print("Cleaning up...")
        print("")

        h['SignalSource'].close()
        h['DataSink'].close()
        h['Trainer'].close()
        h['TmpFile'].close()     #close file  
        # Add short delay to view any final messages
        time.sleep(2.0)

        
if __name__ == "__main__":
    main()
