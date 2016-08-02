
"""
Created on Tue Jul 19 11:16:36 2016

Initial creation of the training methods for LDA classification in Python

--VERBOSE  set to 2 or higher
Output timing information 

Most of the functionality is controlled by command line flags
e.g. if you want to do a demo (plus timing info), you can run: 
'python MyoUDPTrainer.py --EXECUTE demo --VERBOSE 2 --TRAIN 20  --PREDICT 1000'
Training builds on whatever saved training data is in the directory, so if you 
want to train from scratch, delete all of the files in the 'python\training_data\'
folder, and then rerun the script with the train flag (alternatively run delete() function).

WIP add delete flag to run delete method instead of manually deleting saved data
WIP change path behavior so that all paths use self.path
WIP add UDP communication to/from unity for training cues and other functionality

@author: D. Samson
"""


#perhaps import only into necessary scripts
import sys
import time
import math
import numpy as np
from MyoUdp import MyoUdp
from Plant import Plant
from UnityUdp import UnityUdp
#from TrainingUdp import TrainingUdp
from feature_extract import feature_extract
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
import os
from os.path import isfile
import argparse
from sklearn.externals import joblib
import socket
import errno
import random


def UnityTrainer(args):
    #Run Myo trainer in Unity. Then control vMPL using training data
    STATES = enum(waitingHandshake=0, waitingStart=1, setupRecord=2, waitingRecord=3, recording=4, cooldown=5, inactive=6, off=7, none=8)
    
    #message = ''    # most recent message from Unity
    
    state = STATES.waitingHandshake
    # Machine learning Myo UDP trainer controller
    trainer = MyoUDPTrainer(args)

    #handshake between unity and python
    trainer.handshake()
    
    state = STATES.waitingStart
    
    #get possible classes to train
    #send to unity for UI possible
    #wait for requests from unity to add individual classes to training set, then add in python class.
    #wait for signal to begin training
    #run training regime, while telling unity UI what to display
    #control vMPL with newly trained data. (allow for more training)
    
    #communication protocal between unity and python
    # e.g. Unity -> '<command code><data>' -> Python
    # Python -> '<Acknowledgement>' -> Unity
    
    # Set arm to demonstration position
    trainer.hPlant.position[0] = 1
    trainer.hPlant.position[3] = 1.3
    trainer.hSink.sendJointAngles(trainer.hPlant.position)
    
    
    while state == STATES.waitingStart:
        # wait for signal to begin 'b'
        data, addr = trainer.receiveBlock()
        data = bytearray(data)
        if data[0] == ord('b'):
            state = STATES.setupRecord
            print('Beginning training session.\n')
    
    
    #adjust in future to read in classes based on unity settings/take all from ROC file
    trainer.TrainingName = ['No Movement', 'Wrist Rotate In', 'Wrist Rotate Out', 'Wrist Adduction',
            'Wrist Abduction', 'Wrist Flex In', 'Wrist Extend Out', 'Hand Open', 'Spherical Grasp']
    
    for pose in trainer.TrainingName:
        # Set arm to demonstration position
        trainer.hPlant.position[0] = 1
        trainer.hPlant.position[3] = 1.3
        trainer.hSink.sendJointAngles(trainer.hPlant.position)
        
        #train each pose while communicating with unity UI
        #tell unity pose name to be trained
        print('waiting for acknowledgement that unity received pose: ' + pose + '.')
        while data == None or data[0] != ord('a'):
            trainer.send(pose)
            data, addr = trainer.receiveBlock()
            print('received packet: ' + str(data))
            if data != None:
                data = bytearray(data)
        
        start = time.time()
        while time.time() - start < 1:
            trainer.output(pose)
        
        state = STATES.waitingRecord
        print('waiting for training signal.')
        #wait for unity to signal recording of pose
        while data == None or data[0] != ord('r'):
            trainer.output(pose)
            data, addr = trainer.receiveBlock()
            print('received packet: ' + str(data))
            if data != None:
                data = bytearray(data)
        trainer.send('a')
        trainer.trainSingle(trainer.TrainingName.index(pose), pause=1)
        trainer.send('d')
        
        #zero out hand joints
        for i in list(range(len(trainer.hPlant.position))):
            trainer.hPlant.position[i] = 0
        #trainer.hPlant.position[0] = 0
        #trainer.hPlant.position[3] = 1.3
        trainer.hSink.sendJointAngles(trainer.hPlant.position)
    
    trainer.save()
    trainer.fit()
    
    print('')
    print(str(trainer))
	
    print('Running prediction model:')
    trainer.predictMult(-1)
    
    
    trainer.close()
    print('\nEnding program in 5 seconds...')
    time.sleep(5)
  
    
def parse():
    #parse command-line arguments
    parser = argparse.ArgumentParser(description='Myo Trainer Command-line Arguments:')
    parser.add_argument('-q', '--QUADRATIC', help='Run quadratic analysis of data instead of linear', action='store_true')
    parser.add_argument('-d', '--DELETE', help='Delete currently saved training data if any.', action='store_true')
    parser.add_argument('-t', '--TRAIN', help='Run training regime at start of program. Specify number of sample per class', default=0, type=int)
    parser.add_argument('-p', '--PREDICT', help='Run prediction sequence. Specify number of cycles to run for (-1 for infinite)', default=0, type=int)
    parser.add_argument('-f', '--FREQUENCY', help='Set frequency to update at (Hz)', default=50, type=int)
    parser.add_argument('-i', '--UDP_IP', help='IP address to send controls to', default='127.0.0.1')
    parser.add_argument('-u', '--UNITY_PORT', help='UDP port to receive unity packets from', default=8051)
    parser.add_argument('-y', '--PYTHON_PORT', help='UDP port to send python controls to', default=8050)
    parser.add_argument('-v', '--VERBOSE', help='How much console information. 0=minimal, 1=some, 2=more, etc.', default=1, type=int)
    parser.add_argument('-e', '--EXECUTE', help='What "Main()" should this script execute: UnityTrainer, demo, main, etc.?', type=str, default='UnityTrainer')
    #other args relating to creating new data/etc.
    
    return parser.parse_args()

    
def main(args):
    # Machine learning Myo UDP trainer controller
    trainer = MyoUDPTrainer(args)
    
    pass
    

def demo(args):
    #console demo of training
    
    trainer = MyoUDPTrainer(args)
    print('')

    if args.DELETE == True:
        trainer.delete()
    #trainer.create()
    
    testClasses = ['Wrist Rotate In', 'Wrist Rotate Out', 'Wrist Flex In', 'Wrist Extend Out', 'Hand Open', 'Spherical Grasp', 'No Movement']
    #import poses example
    for pose in testClasses:
        try:
            trainer.addClass(pose)
        except:
            pass
    
    # trainer.addClass('randomClass')
    
    # trainer.removeClass('randomClass')
    # trainer.removeClass('No Movement')
    # trainer.addClass('No Movement')
    
    if args.DELETE == False:
        trainer.load()
    trainer.trainAll()
    trainer.save()
    trainer.fit()
    
    print('')
    print(str(trainer))
	
    print('Running prediction model:')
    trainer.predictMult()
    pass

    
def enum(**enums):
    return type('Enum', (), enums)

    
class MyoUDPTrainer:
    

    def __init__(self, args, path=None):
        self.TrainingData = []                      # List of all feature extracted samples
        self.TrainingClass = []                     # List of class indices that each sample belongs to
        self.TrainingName = []                      # Name of each class
        
        if path == None:                            # path to script location. Saved data will be saved/accessed from here.
            self.path = os.path.dirname(os.path.abspath(__file__))
        else:
            self.path = path
               
        self.quadratic = args.QUADRATIC             # set Quadratic Discriminant Analysis mode. False means LDA mode
        self.tsamples = args.TRAIN                  # how many samples per training each class
        self.dt = 1.0/args.FREQUENCY                # how frequently do training and prediction loops run
        self.verb = args.VERBOSE                    # how much information output to the console
        self.pcycles = args.PREDICT                 # how many cycles to predict for. setting to -1 means infinite cycles
        self.hMyo = MyoUdp()                        # Signal Source get external bio-signal data
        self.ROCFile = open(os.path.join(self.path,'..','WrRocDefaults.xml'), 'r')  # ROC file for possible motion classes
        self.hPlant = Plant(self.dt, self.ROCFile)  # Plant maintains current limb state (positions) during velocity control
        self.hSink = UnityUdp()                     #("192.168.1.24")   # Sink is output to ouside world (in this case to VIE)
        self.clf = None                             # Fit training data model
        
        
        self.UDP_IP = args.UDP_IP                   # IP address to communicate with unity through (directed to localhost).
        self.PYTHON_SEND_PORT = args.PYTHON_PORT    # from python send data to unity using this port
        self.UNITY_RECEIVE_PORT = args.UNITY_PORT   # from unity receive data in python using this port
        
        # UDP communication to and from Unity
        self.UnityReceiverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.UnityReceiverSock.bind((self.UDP_IP, self.UNITY_RECEIVE_PORT))
        self.UnityReceiverSock.setblocking(0)
        #https://docs.python.org/2/library/socket.html consider settimeout(<small number>) instead of disabling blocking
        print('UnityPythonUDP UI IP: ' + str(self.UDP_IP))
        print('UnityUDP UI Port: ' + str(self.UNITY_RECEIVE_PORT))
	
        self.PythonSenderSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #print('PythonUDP UI IP: ' + str(self.UDP_IP))
        print('PythonUDP UI Port: ' + str(self.PYTHON_SEND_PORT))
        print('')


    def trainAll(self, samples=None):
        if samples == None:
            samples = self.tsamples
            
        if samples > 0:
            print('\n\nBeginning training Regime in 5 seconds...')
            print('(Ready for first pose "Wrist Rotate In")')
            time.sleep(5)

            print('')
            for classNum, className in enumerate(self.TrainingName):
                self.trainSingle(classNum, samples)


    def trainSingle(self, classNum, samples=None, pause=3):
        if samples == None:
            samples = self.tsamples
            
        print('pose: ' + self.TrainingName[classNum])
        time.sleep(pause)
        
        if self.verb == 0:
            print('Collecting EMG samples...')
        
        for i in list(range(samples)):
            loopStart = time.time()
            emgData = self.hMyo.getData()*0.01
            f = (feature_extract(emgData)).tolist()[0]
            self.TrainingData.append(f)
            self.TrainingClass.append(classNum)
            
            if self.verb >= 1:
                print('%8.4f %8.4f %8.4f %8.4f' % (f[0], f[8], f[16], f[24]))
            if self.verb >= 2:
                print('Get training data loop extraction time: ' + str(time.time() - loopStart) + 's')
            #if self.verb >= 3:
                #print('Emg Buffer:\n' + str(emgData))
            
            loopTime = time.time() - loopStart
            if loopTime < self.dt:
                time.sleep(self.dt - loopTime)
            else:
                print("Timing Overload")
        
        if self.verb == 0:
            print('Done.')
        
        print('')


    def fit(self):
        
        if self.verb >= 1:
            print('Fitting data to ' + ('QDA' if self.quadratic else 'LDA') + ' model.')
        start = time.time()
        
        if len(self.TrainingData) == 0 or len(self.TrainingClass) == 0:
            raise ValueError('Training Data or Class array(s) is empty. Did you forget to save training data?')
        if len(self.TrainingData) != len(self.TrainingClass):
            raise ValueError('Training Data and Training class arrays are incompatable sizes. Try generating new training data from scratch.')
            
        X = np.array(self.TrainingData)
        y = np.array(self.TrainingClass)
        # if self.verb >= 3
            # print('Training data Numpy arrays')
            # print('shape of X: ' + str(X.shape))
            # print('shape of y: ' + str(y.shape))
        if self.quadratic:
            self.clf = QuadraticDiscriminantAnalysis()
        else:
            self.clf = LinearDiscriminantAnalysis()
        self.clf.fit(X, y)
        
        if self.verb >= 2:
            print('Fit LDA model execution time: ' + str(time.time() - start) + 's')


    def predictMult(self, cycles=None):
        if cycles == None:
            cycles = self.pcycles
            
        i = 0
        while i != cycles:
            loopStart = time.time()
            prediction = self.predictSingle()
            if self.verb >= 1:
                print('prediction: ' + prediction)
            if self.verb >= 2:
                print(('QDA' if self.quadratic else 'LDA') + ' prediction execution time: ' + str(time.time() - loopStart) + 's')
            
            self.output(prediction, True)

            loopTime = time.time() - loopStart
            if loopTime < self.dt:
                time.sleep(self.dt - loopTime)
            else:
                print("Timing Overload")
            
            i += 1


    def predictSingle(self):
        return self.TrainingName[self.clf.predict(feature_extract(self.hMyo.getData()*0.01))]


    def output(self, classDecision, upperAngles=False):
        # Move joints using classifier
        try:
            jointId, jointDir = self.hPlant.class_map(classDecision)

            # Set joint velocities
            self.hPlant.velocity[:self.hPlant.NUM_JOINTS] = [0.0] * self.hPlant.NUM_JOINTS
            if jointId:
                for i in jointId:
                    self.hPlant.velocity[i] = jointDir

            self.hPlant.update()

            if upperAngles:
                # perform joint motion update
                vals = self.hMyo.getAngles()
                self.hPlant.position[3] = vals[1] + math.pi/2

            # transmit output
            self.hSink.sendJointAngles(self.hPlant.position)
    
        except:
            print('Class "' + classDecision + '" not available from ROC table.')
            #jointId, jointDir = [[],0]
            pass    


    def save(self, path=None):
        if path == None:
            path = self.path
            
        start = time.time()
        
        print('\nSaving emg feature data to test file')
        trainFolder = os.path.join(path,'training_data')


        if not os.path.exists(trainFolder):
            os.makedirs(trainFolder)
        
        joblib.dump(np.array(self.TrainingData), trainFolder +  os.sep + 'X.pkl')
        joblib.dump(np.array(self.TrainingClass), trainFolder + os.sep + 'y.pkl')
        joblib.dump(self.TrainingName, trainFolder + os.sep + 'className.pkl')
        
        if self.verb >= 2:
            print('Save training data execution time: ' + str(time.time() - start) + 's')


    def load(self, path=None):
        if path == None:
            path = self.path
        trainFolder = os.path.join(path,'training_data')
        
        # Check if data already exists
        # Manipulate data as python arrays, then convert to numpy arrays when final size reached
        saved = isfile(trainFolder + os.sep + 'X.pkl') and isfile(trainFolder + os.sep + 'y.pkl') and isfile(trainFolder + os.sep + 'className.pkl')
        if saved:
            # load from files
            print('Found saved training data. Loading training data from files.')
            self.TrainingData = joblib.load(trainFolder + os.sep + 'X.pkl').tolist()
            self.TrainingClass = joblib.load(trainFolder + os.sep + 'y.pkl').tolist()
            self.TrainingName = joblib.load(trainFolder + os.sep + 'className.pkl') 
        else:
            print('No training data found.')
            self.create(path)
            
        #perform error checks here:
        #if error: self.create()
        pass


    def delete(self, path=None):
        print('Deleting saved data.')
        
        if path == None:
            path = self.path
        trainFolder = os.path.join(path,'training_data') + os.sep
    
        if isfile(trainFolder + 'X.pkl'):
            os.remove(trainFolder + 'X.pkl')
        if isfile(trainFolder + 'y.pkl'):
            os.remove(trainFolder + 'y.pkl')
        if isfile(trainFolder + 'className.pkl'):
            os.remove(trainFolder + 'className.pkl')


    def create(self, path=None):
        if path == None:
            path = self.path
    
        # create new data from default
        print('Creating new set of training data.')
        self.TrainingData = []
        self.TrainingClass = []
        #TrainingName should be loaded from the current ROC file, or start blank, and then addClass for each class
        self.TrainingName = ['Wrist Rotate In', 'Wrist Rotate Out', 'Wrist Flex In', 'Wrist Extend Out', 'Hand Open', 'Spherical Grasp', 'No Movement']
        
        #save empty arrays to files @ path\\training_data\\<array>
        pass


    def close(self):
        print('')
        print('Cleaning up...')
        print('')
        self.hSink.close()
        self.hMyo.close()


    def addClass(self, newClass):
        if newClass not in self.TrainingName:
            self.TrainingName.append(newClass)
        else:
            raise ValueError('Cannot add class "' + newClass + '" to training set. Class already exists in object.')


    def removeClass(self, toRemove):
        print('Attemptint to remove class "' + toRemove +'."')
        
        newData = []
        newClass = []
        newName = []
        remIndex = None
        
        for i in range(len(self.TrainingName)):
            if self.TrainingName[i] != toRemove:
                newName.append(self.TrainingName[i])
            else:
                if remIndex == None:
                    remIndex = i
                else:
                    raise ValueError('Multiple instances of class "' + toRemove + '" in training class list.')
        
        if remIndex == None:
            raise ValueError('No class named "' + toRemove + '" was found in current training data.')
        else:
            for i in range(len(self.TrainingClass)):
                if self.TrainingClass[i] != remIndex:
                    newClass.append(self.TrainingClass[i])
                    newData.append(self.TrainingData[i])
        
        self.TrainingData = newData
        self.TrainingClass = newClass
        self.TrainingName = newName


    def send(self, message):
        self.PythonSenderSock.sendto(bytearray(message, 'utf-8'), (self.UDP_IP, self.PYTHON_SEND_PORT))


    def receiveNoBlock(self, timeout=0.0):
        #receiver that will return None, None if it doesn't receive immediately
        #self.UnityReceiverSock.setblocking(0)
        self.UnityReceiverSock.settimeout(timeout)
        
        try:
            data, addr = self.UnityReceiverSock.recvfrom(1024) # buffer size is 1024 bytes
        except socket.error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK or errno.ETIMEDOUT:
                return None, None
            else:
                # a "real" error occurred
                print(e)
                sys.exit(1)
        else:
            #do stuff with data from receiver
            return data, addr


    def receiveBlock(self):
        #receiver that will wait until it receives data
        self.UnityReceiverSock.setblocking(1)
        return self.UnityReceiverSock.recvfrom(1024) # buffer size is 1024 bytes


    def handshake(self):
        #take data (A) and return (A+1,B)
        #wait for (B+1)
        #can start sending to unity
        
        #self.UnityReceiverSock.setblocking(1)
        acquainted = False      # has the handshake been successful
        print('Attempting handshake with Unity.')
        
        data, addr = self.receiveBlock()
        data = bytearray(data)
        print('Received handshake request from Unity: ' + str(int(data[0])))
        
        #send response with random byte
        response = random.randint(0,255)
        print('Sending response to Unity: ' + str(data[0]+1) + ' ' + str(response))
        self.send(str(data[0]+1) + ' ' + str(response))
        
        #wait for second response
        while not acquainted:
            data, addr = self.receiveBlock()
            data = bytearray(data)
            print('Received handshake response from Unity: ' + str(int(data[0])))
            if data[0] == response + 1:
                acquainted = True
            
        print('Successful handshake between Unity and Python.\n')
        self.UnityReceiverSock.setblocking(0)


    def __str__(self):
        #perhaps adjust output based on VERBOSE
        sizes = [0]*len(self.TrainingName)
        for i in range(len(self.TrainingClass)):
            sizes[self.TrainingClass[i]] += 1
            
        string = 'Myo Trainer Object\n'
        for i, name in enumerate(self.TrainingName):
            string += 'Class: ' + name + '\tSamples: ' + str(sizes[i]) + '\n'
        
        return string       


if __name__ == "__main__":
    args = parse()
    switch = args.EXECUTE
    if (switch == 'UnityTrainer'):
        UnityTrainer(args)
    elif (switch == 'demo'):
        demo(args)
    elif(switch == 'main'):
        main(args)
    else:
        print('Invalid main method requested. No method mapped to "' + switch + '."')

